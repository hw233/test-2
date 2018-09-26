#coding:utf8
"""
Created on 2015-04-14
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 资源相关数值计算
         包括：金钱、粮草、兵力、技能点
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class DefenseInfo(object):
    def __init__(self, building_id = 0, user_id = 0, building_level = 0, defense_value = 0):
        self.building_id = building_id
        self.user_id = user_id
        self.building_level = building_level

        if self.building_level == 0:
            self.defense_value = defense_value
        else:
            self.defense_value = int(data_loader.CityDefenceBasicInfo_dict[building_level].defenseValue)


    @staticmethod
    def create(building):
        """创建新的城防信息，新建一个城防建筑后发生
        """
        defense = DefenseInfo(building.id, building.user_id, building.level)
        return defense


    def update(self, building):
        """更新城防信息
        """
        self.building_level = building.level
        return True


    def update_defense_value(self, value):
        """更新城防值
        """
        assert value >= 0
        self.defense_value = value

