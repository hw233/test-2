#coding:utf8
"""
Created on 2016-09-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

import base64
from utils import logger
from utils import utils


class AnnealRecordInfo(object):
    """一条试炼场记录
    """

    __slots__ = [
            "id",
            "common_id",
            "first_name",
            "first_level",
            "first_icon_id",
            "first_finished_time",

            "fast_name",
            "fast_level",
            "fast_icon_id",
            "fast_finished_time",
            "fast_cost_time",
            ]

    def __init__(self):
        self.id = 0
        self.common_id = 0
        self.first_name = ''
        self.first_level = 0
        self.first_icon_id = 0
        self.first_finished_time = 0

        self.fast_name = ''
        self.fast_level = 0
        self.fast_icon_id = 0
        self.fast_finished_time = 0
        self.fast_cost_time = 0

    @staticmethod
    def create(id, common_id):
        """新建一条广播信息
        """
        record = AnnealRecordInfo()
        record.id = id
        record.common_id = common_id
        record.first_name = ''
        record.first_level = 0
        record.first_icon_id = 0
        record.first_finished_time = 0

        record.fast_name = ''
        record.fast_level = 0
        record.fast_icon_id = 0
        record.fast_finished_time = 0
        record.fast_cost_time = 0

        return record


    def is_need_to_update_first_record(self):
        """
        """
        return self.first_level == 0


    def is_need_to_update_fast_record(self, cost_time):
        """
        """
        if self.fast_level == 0:
            return True

        if cost_time < self.fast_cost_time:
            return True

        return False


    def update_first_record(self, name, level, icon_id, passed_time, now):
        """更新首次通关记录的信息
        """
        self.first_name = name
        self.first_level = level
        self.first_icon_id = icon_id
        self.first_finished_time = now - passed_time


    def update_fast_record(self, name, level, icon_id, passed_time, cost_time, now):
        """更新首次通关记录的信息
        """
        assert cost_time >= 0

        self.fast_name = name
        self.fast_level = level
        self.fast_icon_id = icon_id
        self.fast_finished_time = now - passed_time
        self.fast_cost_time = cost_time


    def get_readable_first_name(self):
        """获取可读的内容
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.first_name)


    def get_readable_fast_name(self):
        """获取可读的内容
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.fast_name)




