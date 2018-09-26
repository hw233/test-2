#coding:utf8
"""
Created on 2016-01-26
@Author: 
@Brief : 
"""

from utils import logger
from datalib.data_loader import data_loader


def calc_defense_value(defense, technologys = []):
    """计算城防的城防值
    """
    base = int(data_loader.CityDefenceBasicInfo_dict[
        defense.building_level].defenseValue)

    #科技加成
    tech_basic_ids = [info.basic_id for info in technologys]
    addition_of_technology = _calc_defense_value_addition_of_technology(
            base, tech_basic_ids)
    logger.debug("defense value[tech addition=%d]" % addition_of_technology)

    return base + addition_of_technology


def _calc_defense_value_addition_of_technology(output_base, tech_basic_ids):
    """计算科技对城防值的加成"""
    addition = 0
    for id in tech_basic_ids:
        increase = (data_loader.InteriorTechnologyBasicInfo_dict[id].
                interiorAttributeIncrease.defense)
        increase = increase/ 100.0
        addition += (int)(increase * output_base)

    return addition


