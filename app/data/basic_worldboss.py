#coding:utf8
"""
Created on 2016-09-21
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

import time
import base64
from utils import logger
from utils import utils


class BasicWorldBossInfo(object):
    """
    """

    __slots__ = [
            "id",
            "basic_id",
            "boss_id",
            "date",
            "start_time",
            "end_time",
            "description",

            "total_soldier_num",
            ]

    def __init__(self):
        self.id = 0
        self.basic_id = 0
        self.boss_id = 0
        self.date = ''
        self.start_time = ''
        self.end_time = ''
        self.description = ''
        self.total_soldier_num = 0

    @staticmethod
    def create(id, basic_id):
        """
        """
        world_boss = BasicWorldBossInfo()
        world_boss.id = id
        world_boss.basic_id = basic_id
        #todo
        return world_boss


    def update(self, boss_id, date, start_time, end_time, 
            description, total_soldier_num):
        """
        """
        self.boss_id = boss_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time

        #用 base64 编码存储，避免一些非法字符造成的问题
        #默认已经传的description已经是base64编码过
        self.description = description  #base64.b64encode(description)

        self.total_soldier_num = total_soldier_num


    def get_arise_time(self):
        """
        """
        return utils.get_start_second_by_timestring(self.date)


    def is_invalid(self, now):
        """世界boss基础数据配置的结束时间是否已经过期
        """
        if self.date == '':
            return False

        end_time = utils.get_end_second_by_timestring(self.date)

        WEEK_SECONDS = 86400 * 7
        if end_time + WEEK_SECONDS >= now:    #超过1周算过期
            return False
        else:
            return True


