#coding:utf8
"""
Created on 2015-10-22
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 城防相关核心计算逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


def calc_attacker_income(attacker_level, defender_level, defense, resource):
    """计算掠夺成功后，进攻方可以获得的资源（金钱粮草）
    Args:
        attacker_level[int]: 攻方等级
        defender_level[int]: 守方等级
        defense[DefenseInfo]: 守方城防情况
        resource[ResourceInfo]: 守方资源情况
    Returns:
        (gain_money, gain_food) 可以获得的资源数量
    """
    (money, food) = calc_defender_loss(defense, resource, defender_level)

    #考虑攻方和守方的等级差距（战斗难度）
    level_gap = attacker_level - defender_level
    cofficient = _calc_level_gap_cofficient(level_gap)
    gain_money = money * cofficient
    gain_food = food * cofficient

    #缴税给系统
    tax_ratio = float(data_loader.OtherBasicInfo_dict["PVPResourceTaxRatio"].value) / 100.0
    assert tax_ratio >= 0.0 and tax_ratio <= 1.0
    gain_money = int(gain_money * (1.0 - tax_ratio))
    gain_food = int(gain_food * (1.0 - tax_ratio))

    #钱、粮抢夺量不超过当前主公等级对应的最大抢夺量
    max_gain_money = data_loader.MonarchLevelBasicInfo_dict[attacker_level].lostMoneyMax
    max_gain_food = data_loader.MonarchLevelBasicInfo_dict[attacker_level].lostFoodMax
    gain_money = min(gain_money, max_gain_money)
    gain_food = min(gain_food, max_gain_food)

    logger.debug("Attacker rob resource[origin=%d,%d][gain=%d,%d][level_gap=%d]" %
            (money, food, gain_money, gain_food, level_gap))
    return (gain_money, gain_food)


def _calc_level_gap_cofficient(gap):
    """计算等级差距带来的加成数值
    """
    gap_dict = data_loader.MonarchLevelGapBasicInfo_dict
    if gap in gap_dict:
        return gap_dict[gap].coefficient

    max_gap = max(gap_dict.keys())
    min_gap = min(gap_dict.keys())

    if gap > max_gap:
        return gap_dict[max_gap].coefficient
    elif gap < min_gap:
        return gap_dict[min_gap].coefficient


def calc_defender_loss(defense, resource, defender_level):
    """计算收到掠夺，防守方损失的资源（金钱粮草）
    Args:
        defense[DefenseInfo]: 守方城防情况
        resource[ResourceInfo]: 守方资源情况
    Returns:
        (lost_money, lost_food) 损失的资源数量
    """
    if defense is None:
        safe_value = 0
        protect_ratio = 0
    else:
        safe_value = defense.defense_value
        protect_ratio = data_loader.CityDefenceBasicInfo_dict[
                defense.building_level].protectRatio

    assert protect_ratio >= 0 and protect_ratio <= 100
    lost_ratio = (100.0 - protect_ratio) / 100.0

    #由城防值保护一部分资源
    dangerous_money = max(0, resource.money - safe_value)
    dangerous_food = max(0, resource.food - safe_value)

    #由资源保护率再保护一部分资源
    lost_money = int(dangerous_money * lost_ratio)
    lost_food = int(dangerous_food * lost_ratio)

    #钱、粮丢失量不超过当前主公等级对应的最大丢失量
    max_lost_money = data_loader.MonarchLevelBasicInfo_dict[defender_level].lostMoneyMax
    max_lost_food = data_loader.MonarchLevelBasicInfo_dict[defender_level].lostFoodMax
    lost_money = min(lost_money, max_lost_money)
    lost_food = min(lost_food, max_lost_food)

    logger.debug("Defender lost resource[lost=%d,%d][safe=%d][lost ratio=%f]" %
            (lost_money, lost_food, safe_value, lost_ratio))
    return (lost_money, lost_food)


def calc_fight_team_count(generalhouse):
    """计算一次可以出战的队伍数量
    和将军府等级相关
    """
    levels_limit = utils.split_to_int(data_loader.OtherBasicInfo_dict[
                "UnlockFrontMiddleBackTeamGeneralhouseLevel"].value)
    count = len([limit for limit in levels_limit if generalhouse.level >= limit])
    return count


