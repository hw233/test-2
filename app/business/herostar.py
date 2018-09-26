#coding:utf8
"""
Created on 2015-02-04
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 将星盘处理逻辑
"""

from app.data.herostar import HeroStarInfo
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.business import item as item_business
from app.business import building as building_business
from app.business import hero as hero_business
from app.business import account as account_business
from app.core import technology as technology_module
import copy
from app import log_formater


def init_herostar(data):
    """初始化将星盘"""
    stars_id = []
    for _, v in data_loader.ConstellationBasicInfo_dict.items():
        stars_id.extend(v.starsID)
    for star_id in stars_id:
        herostar = get_herostar_by_id(data, star_id)
        if herostar is None:
            herostar = HeroStarInfo.create(data.id, star_id)
            data.herostar_list.add(herostar)

def get_herostar_by_id(data, star_id):
    """通过id获取将星"""
    id = HeroStarInfo.generate_id(data.id, star_id)
    return data.herostar_list.get(id, True)

def is_micefu_level_ok(data, star_id):
    """秘策府的等级是否满足需求"""
    next_star_id = HeroStarInfo.get_next_level_id(star_id)
    if next_star_id == 0:
        raise Exception("Hero star is full level")
    next_level = HeroStarInfo.get_herostar_level(next_star_id)

    micefu_basic_id = int(float(data_loader.OtherBasicInfo_dict["building_micefu"].value))
    micefu_list = building_business.get_buildings_by_basic_id(data, micefu_basic_id)
    if len(micefu_list) <= 0:
        return False
    micefu_level = building_business.get_buildings_by_basic_id(data, micefu_basic_id)[0].level
    limit_level = data_loader.MicehouseLevelBasicInfo_dict[micefu_level].heroStarLevelLimit

    return next_level <= limit_level

def get_strength_items(data, star_id):
    """获取将星升到下一级所需要的物品列表"""
    next_star_id = HeroStarInfo.get_next_level_id(star_id)
    if next_star_id == 0:
        raise Exception("Hero star is full level")

    items_id = copy.deepcopy(data_loader.HeroStarUpLvBasicInfo_dict[next_star_id].costItemID)
    items_num = copy.deepcopy(data_loader.HeroStarUpLvBasicInfo_dict[next_star_id].costItemNumb)

    real_items_id = []
    real_items_num = []
    
    for i, id in enumerate(items_id):
        level = _get_starsoul_level(id)
        replace_item_id = _get_replace_item_id(next_star_id, level)
        
        if replace_item_id != 0:
            replace_item = item_business.get_item_by_id(data, replace_item_id)
            if replace_item is None:
                replace_item_num = 0
            else:
                if replace_item_id not in real_items_id:
                    replace_item_num = replace_item.num
                else:
                    replace_item_num = replace_item.num - real_items_num[real_items_id.index(replace_item_id)]

            replace_num = min(replace_item_num, items_num[i])
            items_num[i] -= replace_num
        
            if replace_num > 0:
                if replace_item_id not in real_items_id:
                    real_items_id.append(replace_item_id)
                    real_items_num.append(replace_num)
                else:
                    real_items_num[real_items_id.index(replace_item_id)] += replace_num

        if items_num[i] > 0:
            if items_id[i] not in real_items_id:
                real_items_id.append(items_id[i])
                real_items_num.append(items_num[i])
            else:
                real_items_num[real_items_id.index(items_id[i])] += items_num[i]
    
    return (real_items_id, real_items_num)

def get_cost_money(data, star_id):
    next_star_id = HeroStarInfo.get_next_level_id(star_id)
    if next_star_id == 0:
        raise Exception("Hero star is full level")

    return data_loader.HeroStarUpLvBasicInfo_dict[next_star_id].starCost

def validate_items(data, items_id, items_num, items_info):
    """验证消耗的物品是否与请求一致"""
    user_item_set = set([(item_info.basic_id, item_info.num) for item_info in items_info])
    real_item_set = set(zip(items_id, items_num))
    if len(user_item_set.difference(real_item_set)) == \
        len(real_item_set.difference(user_item_set)) == 0:
        return True
    else:
        return False

def strength_herostar(data, star_id, items_id, items_num, cost_money, timer):
    """给将星升级"""
    # 1.消耗物品
    # 2.消耗金币
    # 3.升级将星
    # 4.更新英雄的将星
    # 5.判断是否需要发送广播
    output_items=[]
    for i, id in enumerate(items_id):
        item = item_business.get_item_by_id(data, id)
        if item is None:# or item.num < items_num[i]:
            raise Exception("No enough items")
        consume = item.consume(min(item.num, items_num[i]))
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
    log = log_formater.output_item(data, "herostar", log_formater.STRENGTH_HEROSTAR, ''.join(output_items))
    logger.notice(log)
    #logger.notice("strength herostar %s"%''.join(output_items))

    resource = data.resource.get()
    resource.update_current_resource(timer.now)
    if not resource.cost_money(cost_money):
        raise Exception("No enough money")

    new_star_id = _do_strength_herostar(data, star_id)

    hero_list = data.hero_list.get_all()
    for hero in hero_list:
        if star_id in hero.get_herostars_set():
            battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
                data.technology_list.get_all(True), hero.soldier_basic_id)
            hero.update_herostar(star_id, new_star_id, battle_technology_basic_id)
            assert hero_business.post_upgrade(data, hero, timer.now, battle_technology_basic_id)


def _do_strength_herostar(data, star_id):
    next_star_id = HeroStarInfo.get_next_level_id(star_id)
    assert next_star_id != 0
    new_star = HeroStarInfo.create(data.id, next_star_id)

    old_star_id = HeroStarInfo.generate_id(data.id, star_id)
    data.herostar_list.delete(old_star_id)
    data.herostar_list.add(new_star)
    return next_star_id


def _get_starsoul_level(item_id):
    """蓝,紫,橙对应0,1,2"""
    level = data_loader.ItemBasicInfo_dict[item_id].level - 3
    assert level >= 0
    return level

def _get_replace_item_id(star_id, level):
    consId = data_loader.HeroStarBasicInfo_dict[star_id].constellationID
    return data_loader.ConstellationBasicInfo_dict[consId].replaceItemID[level]

def is_hero_star_ok(data, hero, index):
    """英雄的星级是否满足条件"""
    hero_star_unlock_1 = int(float(data_loader.OtherBasicInfo_dict['hero_star_unlock_1'].value)) - 1
    hero_star_unlock_2 = int(float(data_loader.OtherBasicInfo_dict['hero_star_unlock_2'].value)) - 1
    hero_star_unlock_3 = int(float(data_loader.OtherBasicInfo_dict['hero_star_unlock_3'].value)) - 1
    hero_star_unlock_4 = int(float(data_loader.OtherBasicInfo_dict['hero_star_unlock_4'].value)) - 1
    hero_star_unlock_5 = int(float(data_loader.OtherBasicInfo_dict['hero_star_unlock_5'].value)) - 1
    hero_star_unlock_6 = int(float(data_loader.OtherBasicInfo_dict['hero_star_unlock_6'].value)) - 1

    flags = account_business.get_flags()
    if 'star_level_disassemble' in flags:
        if hero.star < 20:
            return 0 <= index <= hero_star_unlock_1
        elif hero.star < 30:
            return 0 <= index <= hero_star_unlock_2
        elif hero.star < 40:
            return 0 <= index <= hero_star_unlock_3
        elif hero.star < 50:
            return 0 <= index <= hero_star_unlock_4
        elif hero.star < 60:
            return 0 <= index <= hero_star_unlock_5
        elif hero.star == 60:
            return 0 <= index <= hero_star_unlock_6
    else:
        if hero.star == 1:
            return 0 <= index <= hero_star_unlock_1
        elif hero.star == 2:
            return 0 <= index <= hero_star_unlock_2
        elif hero.star == 3:
            return 0 <= index <= hero_star_unlock_3
        elif hero.star == 4:
            return 0 <= index <= hero_star_unlock_4
        elif hero.star == 5:
            return 0 <= index <= hero_star_unlock_5
        
    return False

def wear_herostar(data, hero, star_id, index, timer):
    """英雄装备将星"""
    assert star_id not in hero.get_herostars_set()
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    hero.wear_herostar(star_id, index, battle_technology_basic_id)
    assert hero_business.post_upgrade(data, hero, timer.now, battle_technology_basic_id)

def validate_hero_herostar(data, hero, hero_info):
    """验证将星是否与请求一致"""
    return cmp(hero_info.hero_star, hero.get_herostars()) == 0

def unload_herostar(data, hero, star_id, timer):
    """英雄卸下将星"""
    assert star_id in hero.get_herostars_set()
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)
    hero.unload_herostar(star_id, battle_technology_basic_id)
    assert hero_business.post_upgrade(data, hero, timer.now, battle_technology_basic_id)


def calc_herostar_constellations_num(data, star_id):
    """计算同种将星的收集数量
    """
    constellations_num = {}
    for constellation in data_loader.ConstellationBasicInfo_dict.values():
        constellations_num[constellation.constellationID] = 0

    herostar_list = data.herostar_list.get_all(True)
    
    for herostar in herostar_list:
        if herostar.herostar_level() > 0:
            constellations_num[herostar.constellation_id()] += 1
    
    for constellation_id, constellation_num in constellations_num.items():
        if constellation_id == HeroStarInfo.get_constellation_id(star_id):
            return constellation_num

    return 0


def is_need_broadcast(data, star_id):
    """是否需要发广播"""
    if HeroStarInfo.get_herostar_level(star_id) != 0:
        return False
    
    constellation_num = calc_herostar_constellations_num(data, star_id)

    if constellation_num == 4 or constellation_num >= 6:
        return True

    return False


def create_broadcast(data, constellation_id, constellation_num):
    """创建广播"""
    if constellation_num == 4:
        broadcast_id = \
                int(float(data_loader.OtherBasicInfo_dict["broadcast_id_get_four_herostar"].value))
    elif constellation_num >= 6:
        broadcast_id = \
                int(float(data_loader.OtherBasicInfo_dict["broadcast_id_get_herostar"].value))

    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    user = data.user.get(True)
    content = template.replace("#str#", user.get_readable_name(), 1)
    content = content.replace("#str#", ("@%s@" %
        data_loader.ConstellationBasicInfo_dict[constellation_id].name.encode("utf-8")), 1)
    
    return (mode_id, priority, life_time, content)


def is_need_broadcast_of_upgrade(data, star_id):
    """是否需要发升级的广播"""
    if HeroStarInfo.get_herostar_level(star_id) >= 3:
        return True
    
    return False


def create_broadcast_of_upgrade(data, star_id):
    """创建升级的广播"""
    broadcast_id = \
            int(float(data_loader.OtherBasicInfo_dict["broadcast_id_upgrade_herostar"].value))

    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    user = data.user.get(True)
    content = template.replace("#str#", user.get_readable_name(), 1)
    content = content.replace("#str#", ("@%s@" %
        data_loader.HeroStarBasicInfo_dict[star_id].starName.encode("utf-8")), 1)
    content = content.replace("#str#", str(data_loader.HeroStarBasicInfo_dict[star_id].starLv), 1)
    
    return (mode_id, priority, life_time, content)




