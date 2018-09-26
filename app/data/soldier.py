#coding:utf8
"""
Created on 2015-01-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Soldier 数值相关计算
"""

import math
from utils import logger
from datalib.data_loader import data_loader


class SoldierInfo(object):
    def __init__(self, id = 0, user_id = 0, basic_id = 0, level = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id
        self.level = level


    @staticmethod
    def generate_id(user_id, basic_id):
        id = user_id << 32 | basic_id
        return id


    @staticmethod
    def get_root_ids(user_id):
        ids = []
        basic_id = int(float(data_loader.OtherBasicInfo_dict["footman_base_id"].value))
        ids.append(generate_id(user_id, basic_id))
        basic_id = int(float(data_loader.OtherBasicInfo_dict["cavalry_base_id"].value))
        ids.append(generate_id(user_id, basic_id))
        basic_id = int(float(data_loader.OtherBasicInfo_dict["archer_base_id"].value))
        ids.append(generate_id(user_id, basic_id))

        return ids


    @staticmethod
    def create(user_id, basic_id, level = 1):
        """创建一个新的兵种
        初始等级默认为1
        """
        id = SoldierInfo.generate_id(user_id, basic_id)
        soldier = SoldierInfo(id, user_id, basic_id, level)
        return soldier


    def upgrade(self):
        """升级兵种
        只升一级
        """
        next_level = self.level + 1

        key = "%s_%s" % (self.basic_id, next_level)
        if key not in data_loader.SoldierBasicInfo_dict:
            logger.warning("Soldier level up failed[basic_id=%d][level=%d]" %
                    (self.basic_id, next_level))
            return False

        self.level = next_level
        logger.debug("Soldier upgrade[basic id=%d][level=%d]" % (self.basic_id, self.level))
        return True


