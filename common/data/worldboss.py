#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class CommonWorldBossInfo(object):
    """世界boss的公共信息
    """

    __slots__ = [
            "id",
            "boss_id",
            "arise_time",
            "start_time",
            "end_time",
            "current_soldier_num",
            "total_soldier_num",
            "kill_user_id",
            "kill_user_name",
            "finish_time",
            "broadcast_status",
            ]

    def __init__(self):
        self.id = 0
        self.boss_id = 0
        self.arise_time = 0
        self.start_time = 0
        self.end_time = 0
        self.current_soldier_num = 0
        self.total_soldier_num = 0
        self.kill_user_id = 0
        self.kill_user_name = ''
        self.finish_time = 0
        self.broadcast_status = "0#0#0#0#0#0#0#0#0"

    @staticmethod
    def create(id):
        """新建信息
        """
        world_boss = CommonWorldBossInfo()
        world_boss.id = id
        world_boss.boss_id = 0
        world_boss.arise_time = 0
        world_boss.start_time = 0
        world_boss.end_time = 0
        world_boss.current_soldier_num = 0
        world_boss.total_soldier_num = 0
        world_boss.kill_user_id = 0
        world_boss.kill_user_name = ''
        world_boss.finish_time = 0
        world_boss.broadcast_status = "0#0#0#0#0#0#0#0#0"
        
        return world_boss


    def get_arise_time(self):
        return self.arise_time


    def reset(self, arise_time, start_time, end_time, total_soldier_num, boss_id):
        """boss有变，重置boss信息
        """
        assert arise_time != 0
        assert start_time != 0
        assert end_time != 0

        if self.total_soldier_num == 0:
            #只有第一次使用配置血量
            self.total_soldier_num = total_soldier_num
        else:
            total_time = self.end_time - self.start_time
            if self.finish_time > self.start_time and self.finish_time <= self.end_time:
                duration_time = self.finish_time - self.start_time
            else:
                duration_time = total_time

            time_ratio = 1.0 * duration_time / total_time
            self.total_soldier_num = max(272000, int((self.total_soldier_num - self.current_soldier_num) / time_ratio))

        self.arise_time = arise_time
        self.start_time = start_time
        self.end_time = end_time
        self.boss_id = boss_id
        self.current_soldier_num = self.total_soldier_num
        self.kill_user_id = 0
        self.kill_user_name = ''
        self.finish_time = 0


    def is_dead(self):
        """boss是否被打败
        """
        if self.current_soldier_num == 0:
            return True
        else:
            return False


    def get_total_soldier_num(self):
        return self.total_soldier_num


    def update_total_soldier_num(self, total_soldier_num):
        assert total_soldier_num > 0
        self.total_soldier_num = total_soldier_num


    def get_current_soldier_num(self):
        return self.current_soldier_num


    def update_current_soldier_num(self, kills_addition):
        assert kills_addition >= 0
        self.current_soldier_num = max(0, self.current_soldier_num - kills_addition)


    def update_kill_user(self, user_id, user_name, now):
        self.kill_user_id = user_id
        self.kill_user_name = user_name
        self.finish_time = now


    def update_broadcast_status(self, index):
        """更新世界boss血量下降的广播状态
        """
        status = utils.split_to_int(self.broadcast_status)
        if status[index] == 1:
            return False
        else:
            status[index] = 1
            self.broadcast_status = utils.join_to_string(status)
            return True







