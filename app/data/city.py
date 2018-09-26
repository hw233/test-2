#coding:utf8
"""
Created on 2015-02-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 城市相关数值计算
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader

EMPTY_SLOT = 0


class CityInfo(object):
    def __init__(self, id = 0, user_id = 0,
            basic_id = 0, is_main = False, name = '',
            building_num = 0, buildings_id = '', mansion_id = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id
        self.is_main = is_main
        self.name = name
        self.building_num = building_num
        self.buildings_id = buildings_id
        self.mansion_id = mansion_id


    @staticmethod
    def generate_id(user_id, basic_id):
        id = user_id << 32 | basic_id
        return id


    @staticmethod
    def get_basic_id(city_id):
        return city_id & 0xFFFFFFFF


    @staticmethod
    def create(user_id, basic_id, is_main = False):
        """创建一个主城
        Args:
            user_id[int]: 用户 id
            pattern[int]: 初始化模式
            is_main[bool]: 是否是主城
        Returns:
            city[CityInfo] 创建的城池信息
        """
        id = CityInfo.generate_id(user_id, basic_id)
        city = CityInfo(id, user_id, basic_id, is_main)

        limit = data_loader.CityBasicInfo_dict[basic_id].slotNum + 1 #第0个位置不使用
        slots = [EMPTY_SLOT] * limit
        city.buildings_id = utils.join_to_string(slots)

        return city


    def get_all_building(self):
        """
        获取当前所有建筑 id 列表
        """
        slots = utils.split_to_int(self.buildings_id)
        return slots


    def place_building(self, building, is_mansion):
        """
        在城池中放置建筑
        """
        #判断对应位置是否是空地
        slots = utils.split_to_int(self.buildings_id)
        if (building.slot_index < 1 or building.slot_index > len(slots) or
                slots[building.slot_index] != EMPTY_SLOT):
            logger.warning("Slot is not available[index=%d][num=%d][build=%s]" %
                    (building.slot_index, len(slots), self.buildings_id))
            return False

        slots[building.slot_index] = building.id
        self.building_num += 1
        self.buildings_id = utils.join_to_string(slots)

        if is_mansion:
            self.mansion_id = building.id

        return True


    def change_name(self, new_name):
        """更改城池名称
        """
        if not isinstance(new_name, str):
            logger.warning("Invalid type")
            return False

        INVALID = "&"
        if new_name.find(INVALID) != -1:
            logger.warning("Name has invalid character[name=%s]" % new_name)
            return False

        self.name = new_name
        return True


    def destroy_building(self, building):
        """
        删除一个建筑物
        """
        slots = utils.split_to_int(self.buildings_id)
        if slots[building.slot_index] != building.id:
            logger.warning("Building not matched"
                    "[slot index=%d][building id in slot=%d][building id=%d]" %
                    (building.slot_index, slots[building.slot_index], building.id))
            return False

        slots[building.slot_index] = 0
        self.building_num -= 1
        self.buildings_id = utils.join_to_string(slots)
        return True


