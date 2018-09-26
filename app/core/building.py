#coding:utf8
"""
Created on 2015-01-26
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 建筑物相关逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


def calc_consume_resource(building, heroes, technologys):
    """计算建造/升级建筑时需要消耗的资源
    Args:
        building[BuildingInfo]: 建筑物信息
        heroes[list(HeroInfo)]: 参与建造/升级的英雄，英雄的技能可以减少消耗
        technologys[list(TechnologyInfo)]: 起作用的内政科技
    Returns:
        消耗的资源 (money, food)
    """
    next_level = building.level + 1
    key = "%s_%s" % (building.basic_id, next_level)
    money = data_loader.BuildingLevelBasicInfo_dict[key].limitMoney
    food = data_loader.BuildingLevelBasicInfo_dict[key].limitFood

    #暂时没有影响资源消耗的内政科技

    #TODO 暂时还没有设计英雄技能

    return (int(money), int(food))


def calc_consume_time(building, heroes, technologys, user):
    """计算建造/升级建筑时需要消耗的时间
    Args:
        building[BuildingInfo]: 建筑物信息
        heroes[list(HeroInfo)]: 参与建造/升级的英雄，英雄的内务值可以减少消耗
        technologys[list(TechnologyInfo)]: 起作用的非战斗科技
    Returns:
        耗时（秒）
    """
    next_level = building.level + 1
    key = "%s_%s" % (building.basic_id, next_level)
    time = data_loader.BuildingLevelBasicInfo_dict[key].limitTime #秒

    total_reduce_time = 0
    #内政科技的影响
    for tech in technologys:
        attribute = data_loader.InteriorTechnologyBasicInfo_dict[
                tech.basic_id].interiorAttributeIncrease
        ratio = attribute.buildSpeed / 100.0
        total_reduce_time += utils.floor_to_int(time * ratio)

    #驻守英雄的影响
    level = data_loader.BuildingLevelBasicInfo_dict[key].limitMonarchLevel
    for hero in heroes:
        if hero is None:
            continue

        ratio = _calc_time_reduce_by_hero(hero, level)
        total_reduce_time += utils.floor_to_int(time * ratio)

    #vip的影响
    open_flags = get_flags()
    if "is_open_buildinglist" in open_flags:
        #查看是否开启了建造队列（vip减少时间与建造队列一起开发）
        ratio = data_loader.VipBasicInfo_dict[user.vip_level].reduceBuildTimeRate / 100.0
        total_reduce_time += utils.floor_to_int(time * ratio)

    time -= total_reduce_time
    return max(0, utils.floor_to_int(time))


def _calc_time_reduce_by_hero(hero, level):
    """计算英雄参与建造/升级，可以减少多少耗时
    Args:
        hero[HeroInfo]: 英雄的信息
        level[int]: 主公等级限制，参与计算而已
    Returns:
        减少的时间比例: [0-1]
    """
    N = hero.interior_score
    SN = data_loader.MonarchLevelBasicInfo_dict[level].sn
    P = float(data_loader.OtherBasicInfo_dict["P_Building"].value)
    if N <= SN:
        return pow(float(N) / SN, 2) * P
    else:
        return (1 + (0.33 / P - 1) * (1 - float(SN) / N)) * P


def calc_money_capacity(basic_id, level, technologys = []):
    """计算建筑物提供的金钱储量
    """
    key = "%d_%d" % (basic_id, level)
    if key in data_loader.BuildingStorageBasicInfo_dict:
        base = data_loader.BuildingStorageBasicInfo_dict[key].moneyCapacity

        #科技加成
        tech_basic_ids = [info.basic_id for info in technologys]
        addition_of_technology = calc_money_capacity_addition_of_technology(
            base, tech_basic_ids)
        logger.debug("money capacity[tech addition=%d]" % addition_of_technology)

        return base + addition_of_technology

    return 0


def calc_food_capacity(basic_id, level, technologys = []):
    """获取建筑物提供的粮食储量
    """
    key = "%d_%d" % (basic_id, level)
    if key in data_loader.BuildingStorageBasicInfo_dict:
        base = data_loader.BuildingStorageBasicInfo_dict[key].foodCapacity
        
        #科技加成
        tech_basic_ids = [info.basic_id for info in technologys]
        addition_of_technology = calc_food_capacity_addition_of_technology(
            base, tech_basic_ids)
        logger.debug("food capacity[tech addition=%d]" % addition_of_technology)

        return base + addition_of_technology

    return 0


def calc_soldier_capacity(basic_id, level, technologys = []):
    """获取建筑物提供的士兵兵容
    """
    key = "%d_%d" % (basic_id, level)
    if key in data_loader.BuildingStorageBasicInfo_dict:
        base = data_loader.BuildingStorageBasicInfo_dict[key].soldierCapacity

        #科技加成
        tech_basic_ids = [info.basic_id for info in technologys]
        addition_of_technology = calc_soldier_capacity_addition_of_technology(
            base, tech_basic_ids)
        logger.debug("soldier capacity[tech addition=%d]" % addition_of_technology)

        return base + addition_of_technology

    return 0


def calc_unlock_finish_soldier_technology(basic_id, level):
    """计算将军府解锁的已经完成研究的兵种科技
    Args:
        basic_id[int]: 建筑物 basic id
        level[int]: 建筑物等级
    Returns:
        list(id): 兵种科技的 basic id 列表
    """
    unlock = []
    all_tech = data_loader.SoldierTechnologyBasicInfo_dict
    for id in all_tech:
        assert all_tech[id].limitBuildingId == basic_id
        if all_tech[id].limitBuildingLevel == level and all_tech[id].isFinish:
            unlock.append(id)

    return unlock


def calc_money_capacity_addition_of_technology(capacity_base, tech_basic_ids):
    """计算科技对金钱容量的加成"""
    addition = 0
    for id in tech_basic_ids:
        increase = (data_loader.InteriorTechnologyBasicInfo_dict[
            id].interiorAttributeIncrease.moneyCapacity)
        increase = increase/ 100.0
        addition += (int)(increase * capacity_base)

    return addition


def calc_food_capacity_addition_of_technology(capacity_base, tech_basic_ids):
    """计算科技对粮食容量的加成"""
    addition = 0
    for id in tech_basic_ids:
        increase = (data_loader.InteriorTechnologyBasicInfo_dict[
            id].interiorAttributeIncrease.foodCapacity)
        increase = increase/ 100.0
        addition += (int)(increase * capacity_base)

    return addition


def calc_soldier_capacity_addition_of_technology(capacity_base, tech_basic_ids):
    """计算科技对兵营容量的加成"""
    addition = 0
    for id in tech_basic_ids:
        increase = (data_loader.InteriorTechnologyBasicInfo_dict[
            id].interiorAttributeIncrease.soldierCapacity)
        increase = increase/ 100.0
        addition += (int)(increase * capacity_base)

    return addition


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))
    
    return open_flags


