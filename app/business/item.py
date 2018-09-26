#coding:utf8
"""
Created on 2015-09-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Item 相关业务逻辑
"""

import random
from utils import logger
from utils import utils
from app import log_formater
from datalib.data_loader import data_loader
from app.data.item import ItemInfo
from app.data.hero import HeroInfo
from app.business import user as user_business
from app.core import technology as technology_module

def init_default_items(data, pattern):
    """创建一个新帐号时，初始化赠送的物品
    Args:
        data[UserData]: 用户信息
        pattern[int]: 初始化模式
    """
    basic_ids = data_loader.InitUserBasicInfo_dict[pattern].itembasicId
    nums = data_loader.InitUserBasicInfo_dict[pattern].itemNum
    assert len(basic_ids) == len(nums)

    for index in range(0, len(basic_ids)):
        item = ItemInfo.create(data.id, basic_ids[index], nums[index])
        data.item_list.add(item)

    return True


def gain_item(data, infos, str, use_type):
    """获得新物品
    如果原来已经拥有物品，物品数量增加
    如果原来没有这件物品，添加物品
    Args:
        infos[list(basic_id, num)]: 奖励的物品信息
    Returns:
        True: 成功
        False: 失败
    """
    output_items = [] 
    for (basic_id, num) in infos:
	id = ItemInfo.generate_id(data.id, basic_id)
        item = data.item_list.get(id)
        if item is not None:
            item.acquire(num)
        else:
            item = ItemInfo.create(data.id, basic_id, num)
            data.item_list.add(item)
        item = [basic_id, num, item.num]
        output_items.append("[item=")
        output_items.append(utils.join_to_string(item))
        output_items.append("]")
    item = ''.join(output_items)
    log = log_formater.output_item(data, str, use_type, item)
    logger.notice(log)
    #logger.notice("gain items %s"% ''.join(output_items))
    return True


def use_resource_item(data, resource, item, num):
    """使用资源物品：粮包、钱包、元宝袋、政令符
    更新 resource 信息、item 信息
    Args:
        resource[ResourceInfo out]: 资源信息
        item[ItemInfo out]: 物品信息
        num[int]: 消耗物品个数
    Returns:
        使用物品正确，返回 True
        否则返回 False
    """
    if item.is_money_item():
        money = item.use_money_item(num)
        if money is None:
            return False
        resource.gain_money(money)

    elif item.is_food_item():
        food = item.use_food_item(num)
        if food is None:
            return False
        resource.gain_food(food)

    elif item.is_gold_item():
        original_gold = resource.gold
        gold = item.use_gold_item(num)
        if gold is None:
            return False
        resource.gain_gold(gold)
        log = log_formater.output_gold(data, gold, log_formater.RESOURCE_ITEM_GOLD,
                "Gain gold frome resource item", before_gold = original_gold)
        logger.notice(log)


    elif item.is_energy_item():
        energy_num = item.use_energy_item(num)
        if energy_num is None:
            return False
        
        energy = data.energy.get()
        energy.gain_energy(energy_num)

    elif item.is_soul_item():
        soul = item.use_soul_item(num)
        if soul is None:
            return False
        resource.gain_soul(soul)

    elif item.is_starsoul_item():
        #XXX:因为客户端bug可能导致Num=0,在这里作特殊处理
        if num <= 0:
            return True
        soul = item.resolve_starsoul_item(num)
        if soul is None:
            return False
        resource.gain_soul(soul)

    else:
        logger.warning("Invalid item[basic id=%d]" % item.basic_id)
        return False

    return True

def use_item(data, item, num, resource, now):
    """使用物品
    未来替代use_resource_item use_monarch_exp
    Args:
        item[ItemInfo out]: 物品信息
        num[int]: 消耗物品个数
        resource[ResourceInfo out]: 资源信息
        now[int]:时间
    Returns:
        使用物品正确，返回 True
        否则返回 False
    """
    if item.is_vip_point_item():
        vip_point = item.use_vip_point_item(num)
        if vip_point is None:
            return False
        user = data.user.get()
        #vip点数需要先折算成price
        ratio = float(
            data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value)
        user.gain_vip_points(int(vip_point / ratio))

    elif item.is_package_item():
        package_basic_info = item.use_package_item(num)
        if package_basic_info is None:
            return False
	
        original_gold = resource.gold
        gold = package_basic_info.gold * num
        if gold > 0:
            resource.gain_gold(gold)
        log = log_formater.output_gold(data, gold, log_formater.ITEM_GOLD,
                "Gain gold from item", before_gold = original_gold)
        logger.notice(log)

        gain_items = []
        for i in range(0, len(package_basic_info.itemsBasicId)):
            gain_items.append(
                    (package_basic_info.itemsBasicId[i], package_basic_info.itemsNum[i] * num))
        gain_item(data, gain_items, "resource item award", log_formater.RESOURCE)

        for i in range(0, len(gain_items)):
            id = ItemInfo.generate_id(data.id, gain_items[i][0])
            item = data.item_list.get(id)

    elif item.is_month_card_item():
        month_card_type = item.use_month_card_item(num)
        if month_card_type is None:
            return False
        pay = data.pay.get()
        pay.add_card(month_card_type, now)

    else:
        logger.warning("Invalid item[basic id=%d]" % item.basic_id)
        return False

    return True

def use_monarch_exp(data, item, num, now):
    """使用主公经验丹，提升用户经验，可能会升级
    """
    exp = item.use_monarch_exp_item(num)
    if exp is None:
        return False

    return user_business.level_upgrade(data, exp, now, "monarch exp", log_formater.EXP_MONARCH )


def use_speed_item(item, num, building, tech):
    """使用加速物品,加速科技或者建造
    """
    speed_time = item.use_speed_item(num)
    if speed_time is None:
        return False

    if building is not None:
        building.reduce_upgrade_time(speed_time)
    elif tech is not None:
        tech.reduce_research_time(speed_time)

    return True


def sell(resource, item, num):
    """出售 item，换取金钱
    更新 resource 信息和 item 信息
    Args:
        resource[ResourceInfo out]: 资源信息
        item[ItemInfo out] 出售的物品
        num[int] 出售的数量
    Returns:
        出售成功返回 True
        失败返回 False
    """
    money = item.sell(num)
    if money is None:
        return False

    logger.debug("Sell item[basic id=%d][num=%d][gain money=%d]" %
            (item.basic_id, num, money))
    resource.gain_money(money)
    return True


def use_starsoul_item(data, item, num, soldier):
    """消耗将魂石，生成对应英雄
    Args:
        data[UserData]: 用户信息
        item[ItemInfo out] 出售的物品
        num[int] 消耗的数量
        soldier[SoldierInfo] 生成的英雄所配置的兵种
    Returns:
        成功返回 HeroInfo
        失败返回 None
    """
    info = item.use_starsoul_item(num)
    if info is None:
        return None

    (hero_basic_id, starsoul_num) = info

    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), soldier.basic_id)
            
    return HeroInfo.create_by_starsoul(item.user_id, hero_basic_id, 
            starsoul_num, soldier, battle_technology_basic_id)


def compose(data, src_info, dest_basic_id, now, dest_num = 1):
    """物品合成
    Args:
        src_info[list(basic_id)]: 原材料物品信息
        dest_basic_id[int]: 合成物品的 basic id
        dest_num[int]: 合成的物品的数量，默认是1
    Returns:
        True: 合成成功
        False:合成失败
    """
    src_basic_id = data_loader.ItemComposeBasicInfo_dict[dest_basic_id].srcId
    src_num = data_loader.ItemComposeBasicInfo_dict[dest_basic_id].srcNum
    money_cost = data_loader.ItemComposeBasicInfo_dict[dest_basic_id].moneyCost * dest_num
    assert len(src_basic_id) == len(src_num)

    #花费金钱
    resource = data.resource.get()
    resource.update_current_resource(now)
    if not resource.cost_money(money_cost):
        logger.warning("not enough money[money=%d][need=%d]" % (resource.money, money_cost))
        return False

    if set(src_info) != set(src_basic_id):
        logger.debug("Source item error[expect=%s][source=%s]" %
                (src_basic_id, src_info))
        return False
    output_items = []
    for index in range(0, len(src_basic_id)):
        src_id = ItemInfo.generate_id(data.id, src_basic_id[index])
        src_item = data.item_list.get(src_id)
        consume = src_item.consume(src_num[index] * dest_num)
        if not consume[0]:
            return False
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
    item = ''.join(output_items)
    log = log_formater.output_item(data, "compose consume", log_formater.COMPOSE_CONSUME, item)
    logger.notice(log)

    dest_id = ItemInfo.generate_id(data.id, dest_basic_id)
    dest = data.item_list.get(dest_id)
    if dest is None:
        #新物品
        dest = ItemInfo.create(data.id, dest_basic_id, dest_num)
        data.item_list.add(dest)
    else:
        dest.acquire(dest_num)
    compose_item = "[item="+utils.join_to_string([dest_basic_id, dest_num, dest.num])+"]"
    log = log_formater.output_item(data, "compose gain", log_formater.COMPOSE_GAIN, compose_item)
    logger.notice(log)
    return dest


def casting(data, src_info, dest_basic_id, dest_num, building_level):
    """物品熔铸
    Args:
        src_info[list((basic_id, casting_num))]: 原材料物品信息
        dest_basic_id[int]: 熔铸物品的 basic id
        building_level[int]:铁匠铺等级
    Returns:
        True: 合成成功
        False:合成失败
    """
    if not data_loader.BlackSmithBasicInfo_dict.has_key(building_level):
        logger.warning("BlackSmith building level is error[building_level=%d]" % building_level)
        return (False, None)

    #dest
    dest_item_basic = data_loader.ItemBasicInfo_dict[dest_basic_id]
    dest_casting_value = dest_item_basic.value
    if (dest_item_basic.type != int(float(data_loader.OtherBasicInfo_dict["item_equipment_upgrade"].value))
            or dest_casting_value == 0):
        logger.warning("Casting dest item error[basic_id=%d]" % dest_basic_id)
        return (False, None)
    if dest_basic_id not in data_loader.BlackSmithBasicInfo_dict[building_level].itemIds:
        logger.warning("BlackSmith building level is not reached[building_level=%d][dest_basic_id=%d]" 
                % (building_level, dest_basic_id))
        return (False, None)

    #p
    p = float(data_loader.OtherBasicInfo_dict["P_BlackSmith"].value)

    #src
    src_casting_value = 0
    output_items = []
    for info in src_info:
        src_id = ItemInfo.generate_id(data.id, info[0])
        src_item = data.item_list.get(src_id)
        if not src_item.is_equipment_upgrade_item():
            logger.warning("Casting source item type error[basic_id=%d]" % info[0])
            return (False, None)
        
        #消耗熔铸的原材料
        consume = src_item.consume(info[1])
        if not consume[0]:
            logger.warning("Casting source item num error[basic_id=%d][num=%d]"
                    % (src_item.basic_id, src_item.num))
            return (False, None)
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        src_casting_value += min(data_loader.ItemBasicInfo_dict[info[0]].value * p, dest_casting_value) * info[1]
    item = ''.join(output_items)
    log = log_formater.output_item(data, "casting consume", log_formater.CASTING_CONSUME, item)
    logger.notice(log)
    #logger.notice("casting %s"%''.join(output_items))
    #熔铸成功率
    p_casting = 1.0 * src_casting_value / (dest_casting_value * dest_num)

    random.seed()
    p_random = random.random()
    dest_item = None
    if p_random < p_casting:
        #熔铸成功
        dest_id = ItemInfo.generate_id(data.id, dest_basic_id)
        dest_item = data.item_list.get(dest_id)
        if dest_item is None:
            #新物品
            dest_item = ItemInfo.create(data.id, dest_basic_id, dest_num)
            data.item_list.add(dest_item)
        else:
            dest_item.acquire(dest_num)
        casting_item ="[item="+utils.join_to_string([dest_basic_id, dest_num, dest_item.num])+"]"
        log = log_formater.output_item(data, "casting gain", log_formater.CASTING_GAIN, casting_item)
        logger.notice(log)
	#logger.notice("gain item[item=%d#%d#%d]"%(dest_basic_id, dest_num, dest_item.num))

    logger.debug("Casting result[src_value=%d][dest_value=%d][p_casting=%f][p_random=%f]"
            % (src_casting_value, dest_casting_value, p_casting, p_random))
    return (True, dest_item)

def get_item_by_id(data, item_id, readonly = False):
    """通过物品id获取物品"""
    id = ItemInfo.generate_id(data.id, item_id)
    return data.item_list.get(id, readonly)


def create_broadcast_of_compose(data, item):
    """创建宝珠合成的广播"""
    broadcast_id = \
            int(float(data_loader.OtherBasicInfo_dict["broadcast_id_stone_compose"].value))

    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    user = data.user.get(True)
    content = template.replace("#str#", user.get_readable_name(), 1)
    content = content.replace("#str#", ("@%s@" %
        data_loader.ItemBasicInfo_dict[item.basic_id].nameKey.encode("utf-8")), 1)
    
    return (mode_id, priority, life_time, content)


