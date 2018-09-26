#coding:utf8
"""
Created on 2015-10-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 科技相关逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.technology import TechnologyInfo


def calc_consume_time(basic_id, type, heroes, technologys, user):
    """计算研究科技需要消耗的时间
    基础时间 * 科技加成 * 武将加成
    Args:
        basic_id[int]: 需要研究的科技的 basic id
        heroes[HeroInfo[]]: 参与研究的英雄，英雄的内务值可以减少消耗
        technologys[TechnologyInfo[]]: 起作用的非战斗科技
    Returns:
        耗时（秒）
    """
    if type == TechnologyInfo.BATTLE_TECH_TYPE:
        all_techs = data_loader.BattleTechnologyBasicInfo_dict
    elif type == TechnologyInfo.INTERIOR_TECH_TYPE:
        all_techs = data_loader.InteriorTechnologyBasicInfo_dict
    elif type == TechnologyInfo.SOLDIER_TECH_TYPE:
        all_techs = data_loader.SoldierTechnologyBasicInfo_dict

    base_time = all_techs[basic_id].limitTime #秒
    building_basic_id = all_techs[basic_id].limitBuildingId
    building_level = all_techs[basic_id].limitBuildingLevel
    key = "%s_%s" % (building_basic_id, building_level)
    monarch_level = data_loader.BuildingLevelBasicInfo_dict[key].limitMonarchLevel

    total_reduce_time = 0
    #科技加成减少时间
    for info in technologys:
        attribute = (data_loader.InteriorTechnologyBasicInfo_dict[info.basic_id].
                interiorAttributeIncrease)
        ratio =  attribute.researchSpeed / 100.0
        reduce_time = utils.floor_to_int(ratio * base_time)
        total_reduce_time += reduce_time
        logger.debug("technology reduce time[basic_id=%d][ratio=%d][reduce_time=%d]" 
                % (info.basic_id, ratio, reduce_time))

    #英雄减少时间
    for hero in heroes:
        if hero is not None:
            ratio = _calc_time_reduce_by_hero(hero, monarch_level)
            reduce_time = utils.floor_to_int(ratio * base_time)
            total_reduce_time += reduce_time
            logger.debug("hero reduce time[basic_id=%d][hero_level=%d][hero_star=%d][hero_research_score=%d][ratio=%f][reduce_time=%d]"
                    % (hero.basic_id, hero.level, hero.star, hero.research_score, ratio, reduce_time))

    #vip的影响
    open_flags = get_flags()
    if "is_open_buildinglist" in open_flags:
        #查看是否开启了建造队列（vip减少时间与建造队列一起开发）
        ratio = data_loader.VipBasicInfo_dict[user.vip_level].reduceStudyTimeRate / 100.0
        total_reduce_time += utils.floor_to_int(base_time * ratio)

    return max(0, utils.floor_to_int(base_time - total_reduce_time))


def _calc_time_reduce_by_hero(hero, user_level):
    """计算英雄参与研究，可以减少多少耗时
    Args:
        hero[HeroInfo]: 英雄的信息
        level[int]: 主公等级限制，参与计算而已
    Returns:
        减少的时间比例: [0-1]
    """
    Y = hero.research_score
    SY = data_loader.MonarchLevelBasicInfo_dict[user_level].sy
    P = float(data_loader.OtherBasicInfo_dict["P_Tech"].value)
    if Y <= SY:
        return pow(float(Y) / SY, 2) * P
    else:
        return (1 + (0.33 / P - 1) * (1 - SY / float(Y))) * P


def calc_consume_resource(basic_id, type, heroes, technologys):
    """计算研究科技时需要消耗的资源
    基础消耗 * 科技加成 * 武将技能加成
    Args:
        basic_id[int]: 需要研究的科技的 basic id
        heroes[HeroInfo[]]: 参与建造/升级的英雄，英雄的技能可以减少消耗
        technologys[TechnologyInfo[]]: 起作用的内政科技
    Returns:
        消耗的资源 (money, food)
    """
    if type == TechnologyInfo.BATTLE_TECH_TYPE:
        all_techs = data_loader.BattleTechnologyBasicInfo_dict
    elif type == TechnologyInfo.INTERIOR_TECH_TYPE:
        all_techs = data_loader.InteriorTechnologyBasicInfo_dict
    elif type == TechnologyInfo.SOLDIER_TECH_TYPE:
        all_techs = data_loader.SoldierTechnologyBasicInfo_dict

    #基础消耗
    money = all_techs[basic_id].limitMoney
    food = all_techs[basic_id].limitFood

    #暂时没有减少研究时资源消耗的科技

    #TODO 暂时还没有设计英雄技能

    return (money, food)


def generate_soldier(technology):
    """兵种科技可以解锁兵种
    """
    assert technology.is_soldier_technology()

    basic_id = data_loader.SoldierTechnologyBasicInfo_dict[
            technology.basic_id].soldierBasicInfoId
    level = data_loader.SoldierTechnologyBasicInfo_dict[
            technology.basic_id].level
    return (basic_id, level)


def get_battle_technology_for_soldier(technologys, soldier_basic_id):
    """获得跟兵种有关的战斗科技
    Args:
        technologys[TechnologyInfo[]]: 起作用的内政科技
        soldier_basic_id[int]: 指定的兵种的 basic id
    Returns:
        battle_technology_basic_id[int[]]
    """

    technology_basic_id = []
    
    #所有生效的战斗科技
    battle_technologys = [tech for tech in technologys
            if tech.is_battle_technology() and not tech.is_upgrade]
    
    for tech in battle_technologys:
        if soldier_basic_id in data_loader.BattleTechnologyBasicInfo_dict[
                tech.basic_id].soldierBasicInfoId:
            technology_basic_id.append(tech.basic_id)

    return technology_basic_id


def get_battle_technology_for_soldier_by_ids(technology_ids, soldier_basic_id):
    """获得跟兵种有关的战斗科技id
    Args:
        technologys_ids[int[]]: 起作用的内政科技
        soldier_basic_id[int]: 指定的兵种的 basic id
    Returns:
        battle_technology_basic_id[int[]]
    """

    technology_basic_id = []
    
    for basic_id in technology_ids:
        if soldier_basic_id in data_loader.BattleTechnologyBasicInfo_dict[
                basic_id].soldierBasicInfoId:
            technology_basic_id.append(basic_id)

    return technology_basic_id


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))
    
    return open_flags


