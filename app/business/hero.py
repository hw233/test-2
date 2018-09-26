#coding:utf8
"""
Created on 2015-09-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Hero 相关业务逻辑
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.hero import HeroInfo
from app.data.item import ItemInfo
from app.data.soldier import SoldierInfo
from app.core import resource as resource_module
from app.core import technology as technology_module
from app.business import team as team_business
from app.business import item as item_business
from app import log_formater
from proto import hero_pb2

def gain_hero(data, basic_id, num = 1):
    """获得新英雄
    如果原来没有这个英雄，增加英雄
    如果原来已经拥有，分解成将魂石
    Args:
        basic_id[int]: 英雄 basic id
        num[int]: 英雄数量
    """
    assert num >= 1

    soldier_basic_id = HeroInfo.get_default_soldier_basic_id(basic_id)
    soldier_id = SoldierInfo.generate_id(data.id, soldier_basic_id)
    soldier = data.soldier_list.get(soldier_id, True)
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), soldier_basic_id)
    new_hero = HeroInfo.create(data.id, basic_id, soldier, battle_technology_basic_id)

    id = HeroInfo.generate_id(data.id, basic_id)
    hero = data.hero_list.get(id)
    if hero is None:
        data.hero_list.add(new_hero)
        num -= 1

        if not post_gain_hero(data, new_hero):
            return False

    if num > 0:
        #对于已经拥有的英雄，分解成将魂石
        (item_basic_id, item_num) = new_hero.split()
        item_num *= num
        item_business.gain_item(data, [(item_basic_id, item_num)], "hero split", log_formater.HERO_SPLIT)

    return True


def post_gain_hero(data, hero):
    """获得英雄的后续处理
    1 可能需要更新 top 阵容
    """
    user = data.user.get(True)
    guard_list = data.guard_list.get_all()
    for guard in guard_list:
        #更新 top 阵容
        if not guard.try_update_top_score([hero], user.team_count):
            return False

    return True


def level_upgrade_by_item(data, hero, item, consume_num, now):
    """英雄使用经验丹进行升级
    Returns:
        True: 成功
        False: 失败
    """
    #使用经验丹
    exp, output_item = item.use_exp_item(consume_num)
    if not exp:
        logger.warning("Use exp item failed")
        return False

    logger.debug("use hero exp item[num=%d][exp=%d]" % (consume_num, exp))

    user = data.user.get(True)

    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)

    #英雄获得经验
    diff_level = hero.level_up(exp, user.level, battle_technology_basic_id)
    if diff_level < 0:
        return False
    elif diff_level > 0:
        return post_upgrade(data, hero, now, battle_technology_basic_id)

    return True, output_item


def level_upgrade(data, hero, exp, now):
    """英雄增加经验
    Returns:
        True: 成功
        False: 失败
    """
    user = data.user.get(True)
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)

    diff_level = hero.level_up(exp, user.level, battle_technology_basic_id)
    if diff_level < 0:
        return False
    elif diff_level > 0:
        return post_upgrade(data, hero, now, battle_technology_basic_id)

    return True


def level_upgrade_by_working(data, hero, exp_per_hour, end_time, now):
    """英雄因为工作，增加经验
    Returns:
        True: 成功
        False: 失败
    """
    user = data.user.get(True)
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)

    diff_level = hero.update_working_exp(exp_per_hour, end_time, 
            user.level, battle_technology_basic_id)
    if diff_level < 0:
        return False
    elif diff_level > 0:
        post_upgrade(data, hero, now, battle_technology_basic_id)

    return True


def star_upgrade(data, hero, item, consume_num, soul_num, now):
    """
    英雄使用将魂石升星
    """
    info = item.use_starsoul_item(consume_num)
    if not info:
        logger.warning("Use starsoul item failed")
        return hero_pb2.STARSOUL_NOT_ENOUGH

    resource = data.resource.get()
    if not resource.cost_soul(soul_num):
        logger.warning("Cost soul failed")
        return hero_pb2.SOUL_NOT_ENOUGH

    hero_basic_id = info[0]
    if hero.basic_id != hero_basic_id:
        logger.warning("Hero basic id not match starsoul item")
        raise Exception("Hero star upgrade failed")

    starsoul_num = info[1]
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    #英雄获得将魂
    if not hero.star_level_up(starsoul_num, battle_technology_basic_id):
        raise Exception("Hero star upgrade failed")

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        raise Exception("Hero star upgrade failed")
        
    return hero_pb2.HERO_OK


def evolution_level_upgrade(data, hero, item, consume_num, now):
    """
    英雄使用突破石升进化等级
    """
    if not item.use_evolution_item(consume_num):
        logger.warning("Use evolution item failed")
        return False

    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    #英雄进化
    if not hero.evolution_level_up(item.basic_id, consume_num, battle_technology_basic_id):
        return False

    return post_upgrade(data, hero, now, battle_technology_basic_id)


def skill_upgrade(data, hero, index, now):
    """英雄技能升级
    消耗金钱和一个技能点数
    Args:
        hero[HeroInfo out]: 英雄的信息
        index[int]: 指定升级第几个技能，[0, 3]
        resource[ResourceInfo out]: 资源信息
    Returns:
        是否升级技能成功
    """
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    (ret, cost_money) = hero.upgrade_skill(index, battle_technology_basic_id)
    if not ret:
        return False

    #代币(技能书替换)
    skillbook_items = []
    for item_info in data_loader.ItemBasicInfo_dict.values():
        if item_info.type == 41:
            skillbook_items.append(item_info)
    
    #XXX:目前认为只有一种代币,即type＝41的物品只有一个
    skillbook = item_business.get_item_by_id(data, skillbook_items[0].id)
    times = 0
    if skillbook is not None and skillbook.num > 0:
        while skillbook.num > 0 and cost_money > 0:
            cost_money -= skillbook_items[0].value
            skillbook.num -= 1
            times += 1
        items ="[item="+utils.join_to_string([skillbook_items[0].id, -times, skillbook.num])+"]"
        log = log_formater.output_item(data, "skill item", log_formater.SKILL_ITEM, items)
        logger.notice(log)
	    
    if cost_money < 0:
        cost_money = 0

    resource = data.resource.get()
    resource.update_current_resource(now)
    if not resource.cost_money(cost_money):
        return False

    # if not resource.cost_skill_point():
    #     return False

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False

    #记录升级次数
    trainer = data.trainer.get()
    trainer.add_skill_upgrade_num(1)

    return True


def soldier_update(data, hero, soldier, now):
    """英雄更新兵种
    Args:
        data[UserData]
        hero[HeroInfo]: 英雄信息
        soldier[SoldierInfo]: 兵种信息
        now[int]: 当前时间戳
    Returns:
        True: 成功
        False: 失败
    """
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), soldier.basic_id)

    if not hero.update_soldier(soldier, battle_technology_basic_id):
        return False

    return post_upgrade(data, hero, now, battle_technology_basic_id)


def equipment_upgrade(data, hero_basic_id, equipment_type, cost_gold, now):
    """英雄装备进阶
    E1 + source_items + money = E2 + return_items
    装备 + 材料 + 金钱 = 进阶后的装备 + 返还材料
    金钱不足，可以使用元宝
    Args:
        data[UserData]
        hero_basic_id[int]: 英雄 basic id
        equipment_typ[int]: 进阶的装备类型
        cost_gold[int]: 花费的元宝数量（金钱不够的情况下，可以使用元宝）
        now[int]: 当前时间戳
    Returns:
        True: 成功
        False: 失败
    """
    hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
    hero = data.hero_list.get(hero_id)

    origin_equipment_id = hero.get_equipment(equipment_type)
    upgrade_info = data_loader.EquipmentUpgradeBasicInfo_dict[origin_equipment_id]

    #花费金钱
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    cost_money = upgrade_info.moneyCost

    #金钱不够，使用元宝
    gold = 0
    money_gap = 0
    if resource.money < cost_money:
        money_gap = cost_money - resource.money
        gold = resource.gold_exchange_resource(money = money_gap)
        if gold < 0 or gold != cost_gold:
            logger.warning("Gold exchange resource failed"
                    "[money gap=%d][expect cost=%d][input cost=%d]" %
                    (money_gap, gold, cost_gold))
            return False

    if not resource.cost_money(cost_money):
        return False

    #消耗进阶材料
    output_items = []
    assert len(upgrade_info.needMaterialId) == len(upgrade_info.needMaterialNum)
    for index in range(0, len(upgrade_info.needMaterialId)):
        item_id = ItemInfo.generate_id(data.id, upgrade_info.needMaterialId[index])
        item = data.item_list.get(item_id)
        if not item.is_equipment_scroll_item() and not item.is_equipment_upgrade_item():
            logger.warning("Invalid equipment item for upgrade[item basic id=%d]" %
                    item.basic_id)
            return False
        consume = item.consume(upgrade_info.needMaterialNum[index])
        if not consume[0]:
            return False
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
    log = log_formater.output_item(data, "equipt", log_formater.EQUIPT, ''.join(output_items))
    logger.notice(log)
    #logger.notice("equipment upgrade %s"%''.join(output_items))

    #可能返还部分材料
    assert len(upgrade_info.returnMaterialId) == len(upgrade_info.returnMaterialNum)
    for index in range(0, len(upgrade_info.returnMaterialId)):
        item_business.gain_item(data,
                [(upgrade_info.returnMaterialId[index], upgrade_info.returnMaterialNum[index])],
		 "return material", log_formater.RETURN_MATERIAL)

    #英雄更新装备
    dest_equipment_id = upgrade_info.nextEquipmentId
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    if not hero.update_equipment(equipment_type, dest_equipment_id, 
            battle_technology_basic_id):
        return False

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False

    #记录装备进阶次数
    trainer = data.trainer.get()
    trainer.add_equipment_upgrade_num(1)

    if gold > 0:
        log = log_formater.output_gold(data, -gold, log_formater.UPGRADE_EQUIPMENT,
                "Upgrade equipment by gold", money = money_gap, before_gold = original_gold)
        logger.notice(log)

    return True


def equipment_upgrade_max(data, hero_basic_id, equipment_type, target_id, cost_gold, now):
    """英雄装备一键进阶
    E1 + source_items + money = E2 + return_items
    装备 + 材料 + 金钱 = 进阶后的装备 + 返还材料
    金钱不足，可以使用元宝
    Args:
        data[UserData]
        hero_basic_id[int]: 英雄 basic id
        equipment_typ[int]: 进阶的装备类型
        cost_gold[int]: 花费的元宝数量（金钱不够的情况下，可以使用元宝）
        now[int]: 当前时间戳
    Returns:
        True: 成功
        False: 失败
    """
    hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
    hero = data.hero_list.get(hero_id)

    origin_equipment_id = hero.get_equipment(equipment_type)

    if not data_loader.EquipmentUpgradeBasicInfo_dict.has_key(target_id):
        logger.warning("Target equipment not exist [target_id=%d]" % target_id)
        return False
    upgrade_infos = []
    while origin_equipment_id != 0 and origin_equipment_id != target_id:
        upgrade_info = data_loader.EquipmentUpgradeBasicInfo_dict[origin_equipment_id]
        upgrade_infos.append(upgrade_info)
        origin_equipment_id = upgrade_info.nextEquipmentId 

    #花费金钱
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    cost_money = 0
    for i in range(len(upgrade_infos)):
        cost_money += upgrade_infos[i].moneyCost

    #金钱不够，使用元宝
    gold = 0
    money_gap = 0
    need_resource_gold = 0
    if resource.money < cost_money:
        money_gap = cost_money - resource.money
        gold = resource.gold_exchange_resource(money = money_gap)
        if gold < 0:
            logger.warning("Gold exchange resource failed"
                    "[money gap=%d][expect cost=%d]" %
                    (money_gap, gold))
            return False
        need_resource_gold = gold

    if not resource.cost_money(cost_money):
        return False

    need_material_ids = []
    need_material_nums = []
    need_gold = 0
    for i in range(len(upgrade_infos)):
        #消耗进阶材料
        assert len(upgrade_infos[i].needMaterialId) == len(upgrade_infos[i].needMaterialNum)
        for index in range(0, len(upgrade_infos[i].needMaterialId)):
            need_material_ids.append(upgrade_infos[i].needMaterialId[index])
            need_material_nums.append(upgrade_infos[i].needMaterialNum[index])

        #可能返还部分材料
        assert len(upgrade_infos[i].returnMaterialId) == len(upgrade_infos[i].returnMaterialNum)
        for index in range(0, len(upgrade_infos[i].returnMaterialId)):
            item_business.gain_item(data,
                    [(upgrade_infos[i].returnMaterialId[index], upgrade_infos[i].returnMaterialNum[index])], 
		    "return material", log_formater.RETURN_MATERIAL)
    output_items = []
    for index in range(0, len(need_material_ids)):
        item_id = ItemInfo.generate_id(data.id, need_material_ids[index])
        item = data.item_list.get(item_id)
        if item is None:
            item_num = 0
        else:
            if not item.is_equipment_scroll_item() and not item.is_equipment_upgrade_item():
                logger.warning("Invalid equipment item for upgrade[item basic id=%d]" %
                        item.basic_id)
                return False
            item_num = item.num

        if item_num < need_material_nums[index]:
            need_gold += ((need_material_nums[index] - item_num) * 
                    data_loader.ItemBasicInfo_dict[need_material_ids[index]].buy_gold_price)
        consume =item.consume(min(item_num, need_material_nums[index]))
        if item_num != 0:
            if not consume[0]:
                return False
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
    log = log_formater.output_item(data, "equipt", log_formater.EQUIPT, ''.join(output_items))
    logger.notice(log)
    if need_resource_gold + need_gold != cost_gold:
        logger.warning("Gold calc error[resource_gold=%d][gold=%d][cost_gold=%d]"
                % (need_resource_gold, need_gold, cost_gold))
        #return False

    #英雄更新装备
    dest_equipment_id = target_id
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    if not hero.update_equipment(equipment_type, dest_equipment_id, 
            battle_technology_basic_id):
        return False

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False

    #记录装备进阶次数
    trainer = data.trainer.get()
    trainer.add_equipment_upgrade_num(1)

    if gold > 0:
        log = log_formater.output_gold(data, -gold, log_formater.UPGRADE_EQUIPMENT,
                "Upgrade equipment by gold", money = money_gap, before_gold = original_gold)
        logger.notice(log)

    return True


def equipment_enchant(data,
        hero_basic_id, equipment_type, dest_equipment_id,
        cost_item, cost_gold, now):
    """英雄装备精炼
    E1 + items + money = E2
    装备 + 材料 + 金钱 = 精炼后的装备
    金钱不足，可以使用元宝兑换
    材料不足(材料提供精炼值，精炼值不足)，可以使用元宝兑换
    Args:
        data[UserData]
        hero_basic_id[int]: 英雄 basic id
        equipment_typ[int]: 精炼的装备类型
        dest_equipment_id[int]: 精炼的装备 id
        cost_item[list((item_id, item_num))]: 消耗的材料信息
        cost_gold[int]: 花费的元宝数量（金钱/材料不够的情况下，可以使用元宝）
        now[int]: 当前时间戳
    Returns:
        True: 成功
        False: 失败
    """
    hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
    hero = data.hero_list.get(hero_id)

    origin_equipment_id = hero.get_equipment(equipment_type)
    enchant_info = data_loader.EquipmentEnchantBasicInfo_dict[origin_equipment_id]
    enchant_branch_count = len(enchant_info.nextEquipmentIds)
    assert enchant_branch_count == len(enchant_info.moneyCost)
    assert enchant_branch_count == len(enchant_info.needPoints)
    assert enchant_branch_count == len(enchant_info.type)

    #非法的精炼
    if not dest_equipment_id in enchant_info.nextEquipmentIds:
        logger.warning("Invalid enchant branch[origin id=%d][dest id=%d]" %
                (origin_equipment_id, dest_equipment_id))
        return False

    enchant_branch_index = enchant_info.nextEquipmentIds.index(dest_equipment_id)

    #花费金钱
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    cost_money = enchant_info.moneyCost[enchant_branch_index]

    #金钱不够，使用元宝
    enchant_gold = 0
    money_gap = 0
    point_gap = 0
    if resource.money < cost_money:
        money_gap = cost_money - resource.money
        gold = resource.gold_exchange_resource(money = money_gap)
        if gold < 0:
            return False
        enchant_gold += gold

    if not resource.cost_money(cost_money):
        return False

    #消耗精炼材料，获得精炼 point 值
    cost_point = enchant_info.needPoints[enchant_branch_index]
    enchant_type = enchant_info.type[enchant_branch_index]
    enchant_point = 0
    output_items = []
    for (item_id, item_num) in cost_item:
        item = data.item_list.get(item_id)
        point, item = item.use_equipment_enchant_item(item_num, enchant_type)
        if point < 0:
            return False
        enchant_point += point
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(item)))
        output_items.append("]")
    log = log_formater.output_item(data, "enchant", log_formater.ENCHANT, ''.join(output_items))
    logger.notice(log)
    if enchant_point < cost_point:
        point_gap = cost_point - enchant_point
        gold = resource.gold_exchange_enchant_point(point_gap)
        if gold < 0:
            return False
        enchant_gold += gold

    if enchant_gold != cost_gold:
        logger.warning("Cost gold failed[real cost=%d][input cost=%d]" %
                (enchant_gold, cost_gold))
        return False

    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    #英雄更新装备
    if not hero.update_equipment(equipment_type, dest_equipment_id,
            battle_technology_basic_id):
        return False

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False

    #记录装备进阶次数
    trainer = data.trainer.get()
    trainer.add_equipment_enchant_num(1)

    if enchant_gold > 0:
        log = log_formater.output_gold(data, -enchant_gold, log_formater.EXCHANGE_ENCHANT_VALUE,
                "Enchant equipment by gold", money = money_gap, before_gold = original_gold,  enchant = point_gap)
        logger.notice(log)

    return True


def equipment_enchant_max(data,
        hero_basic_id, equipment_type, dest_equipment_id,
        cost_item, cost_gold, now):
    """英雄装备一键精炼
    E1 + items + money = E2
    装备 + 材料 + 金钱 = 精炼后的装备
    金钱不足，可以使用元宝兑换
    材料不足(材料提供精炼值，精炼值不足)，可以使用元宝兑换
    Args:
        data[UserData]
        hero_basic_id[int]: 英雄 basic id
        equipment_typ[int]: 精炼的装备类型
        dest_equipment_id[int]: 精炼的装备 id
        cost_item[list((item_id, item_num))]: 消耗的材料信息
        cost_gold[int]: 花费的元宝数量（金钱/材料不够的情况下，可以使用元宝）
        now[int]: 当前时间戳
    Returns:
        True: 成功
        False: 失败
    """
    hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
    hero = data.hero_list.get(hero_id)

    origin_equipment_id = hero.get_equipment(equipment_type)
    
    if not data_loader.EquipmentEnchantBasicInfo_dict.has_key(dest_equipment_id):
        logger.warning("Target equipment not exist")
        return False

    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    enchant_infos = []
    cost_money = 0
    cost_point = 0
    enchant_type = 0
    while origin_equipment_id != 0 and origin_equipment_id != dest_equipment_id:
        enchant_info = data_loader.EquipmentEnchantBasicInfo_dict[origin_equipment_id]
        enchant_branch_count = len(enchant_info.nextEquipmentIds)
        assert enchant_branch_count == len(enchant_info.moneyCost)
        assert enchant_branch_count == len(enchant_info.needPoints)
        assert enchant_branch_count == len(enchant_info.type)
        enchant_infos.append(enchant_info)
 
        if not dest_equipment_id in enchant_info.nextEquipmentIds:
            if origin_equipment_id in data_loader.EquipmentEnchantBasicInfo_dict[enchant_info.nextEquipmentIds[0]].nextEquipmentIds:
                logger.warning("Error equipment enchant id =%d" % dest_equipment_id)
                return False

            #默认先选第一个，然后往精炼的下一层递进
            origin_equipment_id = enchant_info.nextEquipmentIds[0]
            enchant_branch_index = 0
        else:
            origin_equipment_id = dest_equipment_id
            enchant_branch_index = enchant_info.nextEquipmentIds.index(dest_equipment_id)

        #金钱
        cost_money += enchant_info.moneyCost[enchant_branch_index]
 
        #精炼 point 值
        cost_point += enchant_info.needPoints[enchant_branch_index]
        enchant_type = enchant_info.type[enchant_branch_index]

    #花费金钱
    #金钱不够，使用元宝
    enchant_gold = 0
    money_gap = 0
    point_gap = 0
    if resource.money < cost_money:
        money_gap = cost_money - resource.money
        gold = resource.gold_exchange_resource(money = money_gap)
        if gold < 0:
            return False
        enchant_gold += gold

    if not resource.cost_money(cost_money):
        return False

    #消耗精炼材料，获得精炼 point 值
    enchant_point = 0
    output_items = []
    for (item_id, item_num) in cost_item:
        item = data.item_list.get(item_id)
        point, item = item.use_equipment_enchant_item(item_num, enchant_type)
        if point < 0:
            return False
        enchant_point += point
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(item)))
        output_items.append("]")
    log = log_formater.output_item(data, "enchant", log_formater.ENCHANT, ''.join(output_items))
    logger.notice(log)

    if enchant_point < cost_point:
        point_gap = cost_point - enchant_point
        gold = resource.gold_exchange_enchant_point(point_gap)
        if gold < 0:
            return False
        enchant_gold += gold

    if enchant_gold != cost_gold:
        logger.warning("Cost gold failed[enchant_point=%d][real cost=%d][input cost=%d]" %
                (cost_point, enchant_gold, cost_gold))
        return False

    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    #英雄更新装备
    if not hero.update_equipment(equipment_type, dest_equipment_id,
            battle_technology_basic_id):
        return False

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False

    #记录装备进阶次数
    trainer = data.trainer.get()
    trainer.add_equipment_enchant_num(1)

    if enchant_gold > 0:
        log = log_formater.output_gold(data, -enchant_gold, log_formater.EXCHANGE_ENCHANT_VALUE,
                "Enchant equipment by gold", money = money_gap, before_gold = original_gold, enchant = point_gap)
        logger.notice(log)

    return True


def mount_equipment_stone(data, hero_basic_id, item_basic_id, equipment_type, stones_id, now):
    """装备镶嵌宝石
    """
    if equipment_type == HeroInfo.EQUIPMENT_INVALID_ID:
        return False

    if len(stones_id) != HeroInfo.EQUIPMENT_STONE_NUM:
        return False

    hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
    hero = data.hero_list.get(hero_id)

    #拿出已镶嵌的宝石
    stones_list = hero.get_equipment_stones(equipment_type)
    stones_type = []
    for stone_id in stones_list:
        if stone_id == 0:
            continue
        stones_type.append(data_loader.ItemBasicInfo_dict[stone_id].type)

    #要镶嵌的宝石
    item_id = ItemInfo.generate_id(data.id, item_basic_id)
    item = data.item_list.get(item_id)
    item.use_equipment_stone_item()
    mount_stone_type = data_loader.ItemBasicInfo_dict[item_basic_id].type
    if mount_stone_type in stones_type:
        logger.warning("Cannot mount the same type stone[stone_type=%d]" % mount_stone_type)
        return False
    
    #找出要镶嵌的宝石位置
    index = 0
    for i in range(len(stones_list)):
        if stones_list[i] != stones_id[i]:
            break
        index += 1

    if index >= HeroInfo.EQUIPMENT_STONE_NUM:
        logger.warning("Equipment stone not changed")
        return False

    stones_list[index] = item_basic_id

    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    #英雄更新镶嵌的宝石
    if not hero.update_equipment_stones(equipment_type, stones_list, battle_technology_basic_id):
        logger.warning("update equipment stones error[type=%d]" % equipment_type)

        return False

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False

    return True


def demount_equipment_stone(data, heroes_basic_id, equipments_type, equipments_stones_id, item_basic_id, now):
    """装备卸下宝石（多个英雄的多个装备可以同时卸下）
    """
    stones_num = len(heroes_basic_id)
    #花费元宝
    need_gold = stones_num * int(float(
        data_loader.OtherBasicInfo_dict["demount_gold_cost"].value))
    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold
    if need_gold != 0 and not resource.cost_gold(need_gold):
        logger.warning("Not enough gold[gold=%d][need=%d]" % (resource.gold, need_gold))
        return False 
    log = log_formater.output_gold(data, -need_gold, log_formater.DUMOUT_EQUIP_STONE,
                "Demount equitpement stone by gold", before_gold = original_gold)
    logger.notice(log)

    for i in range(len(heroes_basic_id)):
        if equipments_type[i] == HeroInfo.EQUIPMENT_INVALID_ID:
            return False
        
        hero_id = HeroInfo.generate_id(data.id, heroes_basic_id[i])
        hero = data.hero_list.get(hero_id)


        stones_list = hero.get_equipment_stones(equipments_type[i])
        diff_index = -1
        for j in range(len(stones_list)):
            if stones_list[j] != equipments_stones_id[i][j]:
                diff_index = j
                break

        if diff_index == -1 or diff_index >=HeroInfo.EQUIPMENT_STONE_NUM:
            logger.warning("Not stone demount")
            return False

        stones_list[diff_index] = equipments_stones_id[i][diff_index]
        if cmp(stones_list, equipments_stones_id[i]) != 0:
            logger.warning("Only demount one stone at one time")
            return False

        #影响英雄所带兵种战力的科技
        battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
                data.technology_list.get_all(True), hero.soldier_basic_id)
        #英雄更新镶嵌的宝石
        if not hero.update_equipment_stones(equipments_type[i], stones_list, battle_technology_basic_id):
            logger.warning("update equipment stones error[type=%d]" % equipments_type)
            return False

        if not post_upgrade(data, hero, now, battle_technology_basic_id):
            return False

    if not item_business.gain_item(data, [(item_basic_id, stones_num)], "demount stone", log_formater.DEMOUNT_STONE):
        raise Exception("Gain item failed")

    return True


def upgrade_equipment_stone(data, hero_basic_id, item_basic_id, equipment_type, stones_id, now):
    """装备上的宝石升级 (装备上原有宝石 + 宝石物品， 生成高级宝石，并继续镶嵌在装备上）
    """
    if equipment_type == HeroInfo.EQUIPMENT_INVALID_ID:
        return False

    if len(stones_id) != HeroInfo.EQUIPMENT_STONE_NUM:
        return False

    hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
    hero = data.hero_list.get(hero_id)

    #拿出已镶嵌的宝石
    stones_list = hero.get_equipment_stones(equipment_type)
    old_stone_id = 0
    new_stone_id = 0
    #找出升级前和升级后的宝石
    for i in range(len(stones_id)):
        if stones_list[i] != 0 and stones_list[i] != stones_id[i]:
            old_stone_id = stones_list[i]
            new_stone_id = stones_id[i]
            break

    if old_stone_id == 0 or new_stone_id == 0:
        logger.warning("stone error[before=%d][after=%d]" % (old_stone_id, new_stone_id))
        return False

    src_basic_id = data_loader.ItemComposeBasicInfo_dict[new_stone_id].srcId[0]
    src_num = data_loader.ItemComposeBasicInfo_dict[new_stone_id].srcNum[0]
    money_cost = data_loader.ItemComposeBasicInfo_dict[new_stone_id].moneyCost

    if src_basic_id != old_stone_id:
        logger.warning("stone cannot upgrade[before=%d][after=%d]" % (old_stone_id, new_stone_id))
        return False

    #花费金钱
    resource = data.resource.get()
    resource.update_current_resource(now)
    if not resource.cost_money(money_cost):
        logger.warning("not enough money[money=%d][need=%d]" % (resource.money, money_cost))
        return False

    #消耗掉低级宝石
    item_id = ItemInfo.generate_id(data.id, old_stone_id)
    item = data.item_list.get(item_id)
    consume = item.consume(src_num - 1)
    if not consume[0]:
        return False
    output_items = []
    output_items.append("[item=")
    output_items.append(utils.join_to_string(list(consume[1])))
    output_items.append("]")
    log = log_formater.output_item(data, "upgrade equipment stone", log_formater.COMPOSE_CONSUME, ''.join(output_items))
    logger.notice(log)
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    #英雄更新镶嵌的宝石
    if not hero.update_equipment_stones(equipment_type, stones_id, battle_technology_basic_id):
        logger.warning("update equipment stones error[type=%d]" % equipment_type)
        return False
    
    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False

    return True


def post_upgrade(data, hero, now, battle_technology_basic_id):
    """英雄升级、升星等会导致一些东西改变：
    1 自身配置的兵种可能升级
    2 驻守在市场、农田里，导致产速改变
    3 可能更新防守阵容中的历史最高战力
    4 可能更新队伍（更新队伍战力）
    Args:
        data[UserInfo]: 玩家数据
        hero[HeroInfo]: 英雄信息
        now[int]: 时间戳
        battle_technology_basic_id[]:影响英雄所带兵种战力的科技
    Returns:
        True: 成功
        False: 失败
    """
    #如果英雄升级，可能会提升兵种等级
    soldier_id = SoldierInfo.generate_id(data.id, hero.soldier_basic_id)
    soldier = data.soldier_list.get(soldier_id)
    if not hero.update_soldier(soldier, battle_technology_basic_id):
        return False

    #如果英雄驻守在建筑中
    if hero.is_working_in_building():
        building = data.building_list.get(hero.place_id)
        if building.is_able_to_garrison() and not building.is_upgrade:
            if not _post_upgrade_in_building(data, building, now):
                return False

    #更新 top 阵容
    user = data.user.get(True)
    guard_list = data.guard_list.get_all()
    for guard in guard_list:
        if not guard.try_update_top_score([hero], user.team_count):
            logger.warning("Try to update guard top score failed")
            return False

    #如果英雄在队伍中，更新队伍信息
    for team in data.team_list.get_all():
        if team.is_hero_in_team(hero.id):
            if team_business.refresh_team(data, team):
                break
            else:
                return False

    return True


def _post_upgrade_in_building(data, building, now):
    """
    """
    heroes = []#驻守武将
    heroes_id = building.get_working_hero()
    for hero_id in heroes_id:
        if hero_id == 0:
            heroes.append(None)
        else:
            hero = data.hero_list.get(hero_id, True)
            heroes.append(hero)

    if building.is_farmland():
        resource = data.resource.get()
        resource.update_current_resource(now)
        #所有生效的内政科技
        technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]
        return _post_upgrade_in_farmland(building, heroes, resource, technologys, now)

    elif building.is_market():
        resource = data.resource.get()
        resource.update_current_resource(now)
        #所有生效的内政科技
        technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]
        return _post_upgrade_in_market(building, heroes, resource, technologys, now)

    logger.warning("Invalid building for garrison[building basic id=%d]" % building.basic_id)
    return False


def _post_upgrade_in_farmland(building, heroes, resource, technologys, now):
    """
    由于英雄升级，导致其驻守的农田的粮食产量变化，重新计算粮食产量
    """
    output = resource_module.calc_food_output(building, heroes, technologys)
    output_delta = output - building.value

    resource.update_food_output(resource.food_output + output_delta)
    building.update_value(output)
    return True


def _post_upgrade_in_market(building, heroes, resource, technologys, now):
    """
    由于英雄升级，导致其驻守的市场的金钱产量变化，重新计算之
    """
    output = resource_module.calc_money_output(building, heroes, technologys)
    output_delta = output - building.value

    resource.update_money_output(resource.money_output + output_delta)
    building.update_value(output)
    return True


def is_need_broadcast(hero_basic_id):
    """突破到高等级时触发广播
    """
    broadcast_level = 5
    try:
        broadcast_level = int(float(data_loader.OtherBasicInfo_dict["broadcast_star_level_limit"].value))
    except:
        logger.warning("get broadcast_star_level_limit config error")

    if data_loader.HeroBasicInfo_dict[hero_basic_id].potentialLevel >= broadcast_level:
        return True
    else:
        return False


def create_broadcast_content(user, hero_basic_id, type):
    """创建广播信息
        args: type = 1:draw   2:herolist   3:vist
    """
    if type == 2:
        broadcast_id = int(float(
            data_loader.OtherBasicInfo_dict["broadcast_id_get_hero_herolist"].value))
    elif type == 3:
        broadcast_id = int(float(
            data_loader.OtherBasicInfo_dict["broadcast_id_get_hero_visit"].value))
    else:
        broadcast_id = int(float(
            data_loader.OtherBasicInfo_dict["broadcast_id_get_hero_draw"].value))

    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(user.name), 1)
    content = content.replace("#str#",
            ("@%s@" % data_loader.HeroBasicInfo_dict[hero_basic_id].nameKey.encode("utf-8")), 1)

    return (mode_id, priority, life_time, content)

def is_able_to_perfect_reborn_hero(data, now):
    """是否能够完美重生武将"""
    resource = data.resource.get()
    resource.update_current_resource(now)
    user = data.user.get(True)
    if user.vip_level < 2:
        return hero_pb2.RebornHeroRes.REBORN_NEED_VIP
    elif resource.gold < int(float(data_loader.OtherBasicInfo_dict["reborn_hero_cost_gold"].value)):
        return hero_pb2.RebornHeroRes.REBORN_NEED_GOLD
    else:
        return True

def resolve_hero(data, hero_basic_id, is_perfect, now):
    """分解武将"""
    #1.返还资源
    #2.删除武将
    #3.更新信息
    hero = get_hero_by_id(data, hero_basic_id)
    if hero is None:
        logger.warning("No such hero[hero_basic_id=%d]" % hero_basic_id)
        return False

    (items_id, items_num, soul_num) = _get_resolve_hero_item(hero)
    item_dict = {}
    for i in range(len(items_id)):
        if items_id[i] in item_dict:
            item_dict[items_id[i]] += items_num[i]
        else:
            item_dict[items_id[i]] = items_num[i]

    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold

    if is_perfect:
        cost_gold = int(float(data_loader.OtherBasicInfo_dict["reborn_hero_cost_gold"].value))
        resource.cost_gold(cost_gold)
        log = log_formater.output_gold(data, -cost_gold, log_formater.RESOLVE_HERO,
                "Resolve hero by gold", before_gold = original_gold)
        logger.notice(log)

    else:
        ratio = float(data_loader.OtherBasicInfo_dict["reborn_hero_item_return"].value) / 100
        for item_id in item_dict.keys():
            item_dict[item_id] = utils.ceil_to_int(item_dict[item_id] * ratio)
        soul_num = utils.ceil_to_int(soul_num * ratio)
    
    # 镶嵌宝石特殊处理
    (stones_id, stones_num) = _get_return_equipment_stones(hero)
    for i in range(len(stones_id)):
        if stones_id[i] in item_dict:
            item_dict[stones_id[i]] += stones_num[i]
        else:
            item_dict[stones_id[i]] = stones_num[i]

    logger.debug("Resolve hero return items and souls[item_dict=%s][soul_num=%d]" %
            (item_dict, soul_num))

    item_business.gain_item(data, item_dict.items(), "resolve hero", log_formater.RESOLVE_HERO)
    resource.gain_soul(soul_num)

    #data.hero_list.delete(hero.id)
    delete_hero(data, hero)
    return True

def _get_resolve_hero_item(hero):
    """获取分解武将返还的物品"""
    ret_items_id = []
    ret_items_num = []
    ret_soul_num = 0

    ret_soul_num += _get_return_soul(hero)
    (items_id, items_num) = _get_return_expitem(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_money(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_evolution(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_equipment(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_awaken(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)

    return (ret_items_id, ret_items_num, ret_soul_num)

def reborn_hero(data, hero_basic_id, is_perfect, now):
    """重生武将"""
    #1.返还资源
    #2.武将降级
    #3.更新信息
    hero = get_hero_by_id(data, hero_basic_id)
    if hero is None:
        logger.warning("No such hero[hero_basic_id=%d]" % hero_basic_id)
        return False

    (items_id, items_num) = _get_reborn_hero_items(hero)
    item_dict = {}
    for i in range(len(items_id)):
        if items_id[i] in item_dict:
            item_dict[items_id[i]] += items_num[i]
        else:
            item_dict[items_id[i]] = items_num[i]

    if is_perfect:
        cost_gold = int(float(data_loader.OtherBasicInfo_dict["reborn_hero_cost_gold"].value))
        resource = data.resource.get()
        resource.update_current_resource(now)
        original_gold = resource.gold
        resource.cost_gold(cost_gold)
        log = log_formater.output_gold(data, -cost_gold, log_formater.REBORN_HERO,
                "Reborn hero by gold", before_gold = original_gold)
        logger.notice(log)
    else:
        ratio = float(data_loader.OtherBasicInfo_dict["reborn_hero_item_return"].value) / 100
        for item_id in item_dict.keys():
            item_dict[item_id] = utils.ceil_to_int(item_dict[item_id] * ratio)
    
    # 镶嵌宝石特殊处理
    (stones_id, stones_num) = _get_return_equipment_stones(hero)
    for i in range(len(stones_id)):
        if stones_id[i] in item_dict:
            item_dict[stones_id[i]] += stones_num[i]
        else:
            item_dict[stones_id[i]] = stones_num[i]

    logger.debug("Reborn hero return items:[item_dict=%s]" % item_dict)

    item_business.gain_item(data, item_dict.items(), "reborn hero", log_formater.REBORN_HERO)

    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    hero.reborn(battle_technology_basic_id)

    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return False
    return True

def _get_reborn_hero_items(hero):
    """获取重生武将返还的物品"""
    ret_items_id = []
    ret_items_num = []
    
    (items_id, items_num) = _get_return_starsoul(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_expitem(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_money(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_evolution(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    (items_id, items_num) = _get_return_equipment(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    # 镶嵌宝石特殊处理
    '''
    (items_id, items_num) = _get_return_equipment_stones(hero)
    ret_items_id.extend(items_id)
    ret_items_num.extend(items_num)
    '''

    return (ret_items_id, ret_items_num)

def _get_return_starsoul(hero):
    """星级降低返还将魂石"""
    items_id = []
    items_num = []
    star_level = hero.star
    num_starsoul = 0

    initial_star_level = HeroInfo.get_initial_star_level(hero.basic_id)
    while star_level > initial_star_level:
        num_starsoul += data_loader.HeroStarLevelBasicInfo_dict[star_level].perceptivity
        star_level -= 1

    items_id.append(data_loader.HeroBasicInfo_dict[hero.basic_id].starSoulBasicId)
    items_num.append(num_starsoul)

    return (items_id, items_num)

def _get_return_soul(hero):
    """分解武将返还精魄"""
    star_level = hero.star
    num_starsoul = 0    #将魂石数量
    num_soul = 0        #精魄

    while star_level >= HeroInfo.get_min_star_level():
        num_starsoul += data_loader.HeroStarLevelBasicInfo_dict[star_level].perceptivity
        num_soul += data_loader.HeroStarLevelBasicInfo_dict[star_level].soul
        star_level -= 1

    item_id = data_loader.HeroBasicInfo_dict[hero.basic_id].starSoulBasicId
    num_soul += ItemInfo.get_soul_num(item_id) * num_starsoul
    return num_soul

def _get_return_awaken(hero):
    """分解武将返还觉醒材料"""
    if hero.is_awaken == 0:
        return ([], [])
    
    items_id = data_loader.HeroAwakeningBasicInfo_dict[hero.basic_id].itemBasicIDs
    items_num = data_loader.HeroAwakeningBasicInfo_dict[hero.basic_id].itemCost
    assert len(items_id) == len(items_num)

    return (items_id, items_num)

def _get_return_expitem(hero):
    """等级降低返还经验丹"""
    level = hero.level
    exp = hero.exp
    while level > 1:
        exp += data_loader.HeroLevelBasicInfo_dict[level].exp
        level -= 1

    exp_items = []
    for item_info in data_loader.ItemBasicInfo_dict.values():
        if item_info.type == 2:
            exp_items.append(item_info)

    exp_items.sort(key = lambda x : x.value, reverse = True)

    items_id = []
    items_num = []
    remainder = exp
    for exp_item in exp_items:
        items_id.append(exp_item.id)
        items_num.append(remainder // exp_item.value)
        remainder = remainder % exp_item.value

    return (items_id, items_num)

def _get_return_money(hero):
    """技能降级返还钱袋"""
    skills_id = utils.split_to_int(hero.skills_id)
    all_money = 0
    for i, skill_id in enumerate(skills_id):
        if skill_id == 0:
            continue
        level = data_loader.SkillBasicInfo_dict[skill_id].level
        money = 0
        while level > HeroInfo._get_skill_unlock_level(i):
            money += data_loader.SkillLevelBasicInfo_dict[level].money
            level -= 1
        all_money += money
    
    money_items = []
    for item_info in data_loader.ItemBasicInfo_dict.values():
        if item_info.type == 1:
            money_items.append(item_info)

    money_items.sort(key = lambda x : x.value, reverse = True)

    items_id = []
    items_num = []
    remainder = all_money
    for money_item in money_items:
        items_id.append(money_item.id)
        items_num.append(remainder // money_item.value)
        remainder = remainder % money_item.value

    return (items_id, items_num)

def _get_return_evolution(hero):
    """返还突破石"""
    evolution_level = hero.evolution_level
    if evolution_level < 2:
        return ([], [])

    evolution_ids = data_loader.HeroBasicInfo_dict[hero.basic_id].evolutionIds
    evolution_ids = evolution_ids[:evolution_level - 1]

    items_id = []
    items_num = []
    for evolution_id in evolution_ids:
        evolution_basic = data_loader.HeroEvolutionLevelBasicInfo_dict[evolution_id]
        evolution_item_num = int(evolution_basic.evolvePoints)
        soldier_type = hero.get_soldier_type()
        if soldier_type == hero.SOLDIER_TYPE_FOOTMAN:
            evolution_item_id = int(evolution_basic.evolutionItemBasicIds[0])
        elif soldier_type == hero.SOLDIER_TYPE_CAVALRY:
            evolution_item_id = int(evolution_basic.evolutionItemBasicIds[1])
        elif soldier_type == hero.SOLDIER_TYPE_ARCHER:
            evolution_item_id = int(evolution_basic.evolutionItemBasicIds[2])
        
        items_id.append(evolution_item_id)
        items_num.append(evolution_item_num)

    return (items_id, items_num)

def _get_return_equipment(hero):
    """返还装备材料"""
    items_id = []
    items_num = []
    equipments_id = utils.split_to_int(hero.equipments_id)
    for equipment_id in equipments_id:
        #1.返还精炼材料
        #2.返还升级材料
        items_id.extend(data_loader.EquipmentUpgradeBasicInfo_dict[equipment_id].returnMaterialId)
        items_num.extend(data_loader.EquipmentUpgradeBasicInfo_dict[equipment_id].returnMaterialNum)

        #诡异的等级设定
        if data_loader.EquipmentBasicInfo_dict[equipment_id].upgradeLevel == 1:
            level = 1
        else:
            level = (data_loader.EquipmentBasicInfo_dict[equipment_id].upgradeLevel - 1) * 5
        if level <= 0:
            continue
        items_id.append(data_loader.EquipmentToItemBasicInfo_dict[level].itemBasicId)
        items_num.append(data_loader.EquipmentToItemBasicInfo_dict[level].num)

    return (items_id, items_num)

def _get_return_equipment_stones(hero):
    """返还镶嵌的宝石"""
    items_id = []
    items_id.extend(hero.get_equipment_stones(hero.EQUIPMENT_TYPE_WEAPON))
    items_id.extend(hero.get_equipment_stones(hero.EQUIPMENT_TYPE_ARMOR))
    items_id.extend(hero.get_equipment_stones(hero.EQUIPMENT_TYPE_TREASURE))
    items_id = [item_id for item_id in items_id if item_id != 0]
    items_num = [1] * len(items_id)

    return (items_id, items_num)

def awaken_hero(data, hero, now):
    """觉醒英雄
        1. 判断是否可以觉醒
        2. 扣除相应的物品
        3. 觉醒
    """
    if hero.basic_id not in data_loader.HeroAwakeningBasicInfo_dict.keys():
        return hero_pb2.AwakeningHeroRes.ERROR_HERO

    item_list = data_loader.HeroAwakeningBasicInfo_dict[hero.basic_id].itemBasicIDs
    item_num = data_loader.HeroAwakeningBasicInfo_dict[hero.basic_id].itemCost
    skill_id = data_loader.HeroAwakeningBasicInfo_dict[hero.basic_id].skillID
    assert len(item_list) == len(item_num)
    output_items = []
    for i in range(len(item_list)):
        item = item_business.get_item_by_id(data, item_list[i])
        if item is None:
            return hero_pb2.AwakeningHeroRes.NEED_ITEM
        consume =  item.consume(item_num[i])
        if not consume[0]:
            return hero_pb2.AwakeningHeroRes.NEED_ITEM
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
    log = log_formater.output_item(data, "awaken hero", log_formater.AWAKEN_HERO, ''.join(output_items))
    logger.notice(log)
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    hero.awaken_hero(battle_technology_basic_id)
    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return hero_pb2.AwakeningHeroRes.ERROR_HERO

    return hero_pb2.AwakeningHeroRes.SUCCESS

def hero_refine(data, hero):
    """英雄洗髓
    """
    unlock_level = hero.refine_unlock_level()
    if hero.level < unlock_level:
        logger.warning("hero level too low cannot refine[user_id=%d][hero_id=%d]" %
                (data.id, hero.id))
        return hero_pb2.RefineHeroRes.Refine_ERROR_HERO

    (item_id, item_num) = hero.refine_item()
    item = item_business.get_item_by_id(data, item_id)
    if item is None or item.num < item_num:
        logger.warning("no enough refine item[user_id=%d][item_num=%d][need_num=%d]" %
                (data.id, 0 if item is None else item.num, item_num))
        return hero_pb2.RefineHeroRes.Refine_NEED_ITEM
    output_items = []
    consume = item.consume(item_num)
    if not consume[0]:
        logger.warning("no enough refine item[user_id=%d][item_num=%d][need_num=%d]" %
                (data.id, item.num, item_num))
        return hero_pb2.RefineHeroRes.Refine_NEED_ITEM
    output_items.append("[item=")
    output_items.append(utils.join_to_string(list(consume[1])))
    output_items.append("]")
    log = log_formater.output_item(data, "refine", log_formater.REFINE, ''.join(output_items))
    logger.notice(log)

    hero.refine()
    
    return hero_pb2.RefineHeroRes.Refine_SUCCESS

def hero_refine_upgrade(data, hero, now):
    """英雄洗髓进阶"""
    if hero.refine_full_attribute_num() < len(hero.REFINE_TYPES):
        return hero_pb2.RefineHeroRes.Refine_CONNT_UPGRADE

    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
                data.technology_list.get_all(True), hero.soldier_basic_id)
    hero.refine_upgrade(battle_technology_basic_id)
    if not post_upgrade(data, hero, now, battle_technology_basic_id):
        return hero_pb2.RefineHeroRes.Refine_ERROR_HERO

    return hero_pb2.RefineHeroRes.Refine_SUCCESS

def delete_hero(data, hero):
    """删除武将,并解除相关依赖"""
    #解除Team的依赖
    teams = data.team_list.get_all()
    for team in teams:
        if team.is_hero_in_team(hero.id):
            heroes_basic_id = [
                HeroInfo.get_basic_id(id)
                for id in team.get_heroes()
                if id != hero.id
            ]
            team_business.update_team(data, team.index, heroes_basic_id)

    #解除melee的依赖
    melee = data.melee.get()
    (heroes_list, positions_list) = melee.get_heroes_position()
    if hero.basic_id in heroes_list:
        melee.set_heroes_position([], [])

    data.hero_list.delete(hero.id)


def get_hero_by_id(data, hero_basic_id, readonly = False):
    id = HeroInfo.generate_id(data.id, hero_basic_id)
    return data.hero_list.get(id, readonly)
