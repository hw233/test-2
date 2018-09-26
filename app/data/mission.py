#coding:utf8
"""
Created on 2015-05-18
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 每日任务相关逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class MissionInfo(object):
    def __init__(self, id = 0, user_id = 0,
            basic_id = 0, type = 0,
            current_num = 0, target_num = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id
        self.type = type
        self.current_num = current_num
        self.target_num = target_num


    @staticmethod
    def generate_id(user_id, mission_basic_id):
        return user_id << 32 | mission_basic_id


    @staticmethod
    def get_basic_id(mission_id):
        return mission_id & 0xFFFFFFFF


    @staticmethod
    def create(user_id, basic_id):
        """创建任务信息
        """
        mission_id = MissionInfo.generate_id(user_id, basic_id)
        mission_type = data_loader.AllMission_dict[basic_id].type
        target_num = data_loader.AllMission_dict[basic_id].destNum
        mission = MissionInfo(mission_id, user_id, basic_id, mission_type, 0, target_num)
        return mission


    def create_next(self):
        """创建后置任务
        """
        next_id = data_loader.AllMission_dict[self.basic_id].nextId
        if next_id == 0:
            return None
        else:
            return self.create(self.user_id, next_id)

    def reset(self):
        """
        """
        current_num = 0


    def forward(self, num):
        """任务进度前进
        """
        self.current_num += num


    def update(self, num):
        """任务进度更新
        """
        self.current_num = num


    def is_unlocked(self, level):
        """任务是否解锁
        """
        return data_loader.AllMission_dict[self.basic_id].unlockMonarchLevel <= level


    def is_finish(self, level):
        """任务是否完成
        """
        #任务必须已经解锁
        if not self.is_unlocked(level):
            return False

        return self.current_num >= self.target_num


    def is_day7_type(self):
        """是否是开服7天的任务类型
        """
        type = data_loader.AllMission_dict[self.basic_id].type
        return type >= 11 and type <= 17


    def is_activity_type(self):
        """是否是活动类的任务类型
        """
        type = data_loader.AllMission_dict[self.basic_id].type
        return type == 4


    def get_reward_items(self):
        """
        """
        item_list = []

        reward = data_loader.AllMission_dict[self.basic_id].reward

        items_basic_id = reward.itemBasicInfoId
        items_num = reward.itemNum
        assert len(items_basic_id) == len(items_num)
        items_count = len(items_basic_id)

        for i in range(0, items_count):
            item_list.append((items_basic_id[i], items_num[i]))

        return item_list

