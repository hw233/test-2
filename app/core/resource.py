#coding:utf8
"""
Created on 2015-10-22
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 资源相关核心计算逻辑
"""

from utils import logger
from datalib.data_loader import data_loader


def calc_money_output(building, heroes, technologys):
    """更新金钱产量
    step 1 资源产量 = 建筑提供的基础产量 + 武将提供的额外产量 + 科技提供的额外产量
    step 2 再结算武将技能加成
    """
    if building.is_upgrade:
        return 0

    #基础产量
    base = calc_output_base(building.basic_id, building.level)
    logger.debug("money output[base=%d]" % base)
    if base == 0:
        return 0

    #英雄 产量加成
    addition_of_hero = 0
    for hero in heroes:
        if hero is None:
            continue
        addition_of_hero += calc_money_output_addition_of_hero(
                base, building.level, hero.interior_score)
        logger.debug("money output[hero addition=%d][hero basic id=%d]" %
                (addition_of_hero, hero.basic_id))

    #科技加成
    tech_basic_ids = [info.basic_id for info in technologys]
    addition_of_technology = _calc_money_output_addition_of_technology(
            base, tech_basic_ids)
    logger.debug("money output[tech addition=%d]" % addition_of_technology)

    #TODO
    #还需要考虑武将技能加成

    output = base + addition_of_hero + addition_of_technology
    logger.debug("money output[total=%d]" % int(output))
    return int(output)


def calc_food_output(building, heroes, technologys):
    """更新粮食产量
    """
    if building.is_upgrade:
        return 0

    #基础产量
    base = calc_output_base(building.basic_id, building.level)
    logger.debug("food output[base=%d]" % base)
    if base == 0:
        return 0

    #英雄 产量加成
    addition_of_hero = 0
    for hero in heroes:
        if hero is None:
            continue
        addition_of_hero += calc_food_output_addition_of_hero(
                base, building.level, hero.interior_score)
        logger.debug("food output[hero addition=%d][hero basic id=%d]" %
                (addition_of_hero, hero.basic_id))

    #科技加成
    tech_basic_ids = [info.basic_id for info in technologys]
    addition_of_technology = _calc_food_output_addition_of_technology(
            base, tech_basic_ids)
    logger.debug("food output[tech addition=%d]" % addition_of_technology)

    #TODO
    #还需要考虑武将技能加成

    output = base + addition_of_hero + addition_of_technology
    logger.debug("food output[total=%d]" % int(output))
    return int(output)


def calc_soldier_output(building, heroes, technologys):
    """更新士兵产量
    """
    #基础产量
    base = calc_output_base(building.basic_id, building.level)
    logger.debug("soldier output[base=%d]" % base)
    if base == 0:
        return 0

    #英雄 产量加成
    addition_of_hero = 0
    for hero in heroes:
        if hero is None:
            continue
        addition_of_hero += calc_soldier_output_addition_of_hero(
                base, building.level, hero.interior_score)
        logger.debug("soldier output[hero addition=%d][hero basic id=%d]" %
                (addition_of_hero, hero.basic_id))

    #科技加成
    tech_basic_ids = [info.basic_id for info in technologys]
    addition_of_technology = _calc_soldier_output_addition_of_technology(
            base, tech_basic_ids)
    logger.debug("soldier output[tech addition=%d]" % addition_of_technology)

    #TODO
    #还需要考虑武将技能加成

    output = base + addition_of_hero + addition_of_technology 
    logger.debug("soldier output[total=%d]" % int(output))
    return int(output)


def calc_output_base(building_basic_id, building_level):
    """计算基础产量，和建筑物相关
    """
    key = "%d_%d" % (building_basic_id, building_level)
    if key in data_loader.BuildingOutputBasicInfo_dict:
        return int(data_loader.BuildingOutputBasicInfo_dict[key].value)

    return 0


def calc_money_output_addition_of_hero(
        output_base, building_level, hero_interior_score):
    """计算英雄带来的金钱产量增加值
    """
    FL = data_loader.BuildingLevelCoefficientInfo_dict[building_level].F_Level_Money
    P = output_base
    N = hero_interior_score
    return _calc_output_addition_of_hero(FL, P, N)


def calc_food_output_addition_of_hero(
        output_base, building_level, hero_interior_score):
    """计算英雄带来的粮食产量增加值
    """
    FL = data_loader.BuildingLevelCoefficientInfo_dict[building_level].F_Level_Food
    P = output_base
    N = hero_interior_score
    return _calc_output_addition_of_hero(FL, P, N)


def calc_soldier_output_addition_of_hero(
        output_base, building_level, hero_interior_score):
    """计算英雄带来的粮食产量增加值
    """
    FL = data_loader.BuildingLevelCoefficientInfo_dict[building_level].F_Level_Soldier
    P = output_base
    N = hero_interior_score
    return _calc_output_addition_of_hero(FL, P, N)


def _calc_output_addition_of_hero(FL, P, N):
    addition = 0
    if N <= 2 * P:
        addition += int(round(N * FL, 4))
    else:
        addition += int(round(2 * P * FL, 4))
    return addition


def _calc_money_output_addition_of_technology(output_base, tech_basic_ids):
    """计算科技对金钱产量的加成"""
    addition = 0
    for id in tech_basic_ids:
        increase = (data_loader.InteriorTechnologyBasicInfo_dict[id].
                interiorAttributeIncrease.moneyOutput)
        increase = increase/ 100.0
        addition += (int)(increase * output_base)

    return addition


def _calc_food_output_addition_of_technology(output_base, tech_basic_ids):
    """计算科技对粮草产量的加成"""
    addition = 0
    for id in tech_basic_ids:
        increase = (data_loader.InteriorTechnologyBasicInfo_dict[id].
                interiorAttributeIncrease.foodOutput)
        increase = increase/ 100.0
        addition += (int)(increase * output_base)

    return addition


def _calc_soldier_output_addition_of_technology(output_base, tech_basic_ids):
    """计算科技对士兵产量的加成"""
    addition = 0
    for id in tech_basic_ids:
        increase = (data_loader.InteriorTechnologyBasicInfo_dict[id].
                interiorAttributeIncrease.soldierOutput)
        increase = increase/ 100.0
        addition += (int)(increase * output_base)

    return addition

