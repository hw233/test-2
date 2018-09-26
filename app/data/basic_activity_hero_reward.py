#coding:utf8
"""
Created on 2016-09-21
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

import base64
from utils import logger
from utils import utils


class BasicActivityHeroRewardInfo(object):
    """
    """

    __slots__ = [
            "id",      #original_id和level拼成的id作为存储的key
            "basic_id",
            "original_id",
            "level",
            "items_id",
            "items_num",
            "weight",
            ]

    def __init__(self):
        self.id = 0
        self.basic_id = 0
        self.original_id = 0
        self.level = 0
        self.items_id = 0
        self.items_num = 0
        self.weight = 0 

    @staticmethod
    def generate_id(original_id, level):
        id = original_id << 32 | level
        return id


    @staticmethod
    def generate_all_ids(original_id):
        ids = []
        MAX_LEVEL = 14
        for i in range(MAX_LEVEL):
            id = original_id << 32 | i
            ids.append(id)
        return ids


    @staticmethod
    def get_original_id(id):
        original_id = id & 0xFFFFFFFF
        return original_id


    @staticmethod
    def create(original_id, basic_id, level, weight):
        """
        """
        id = BasicActivityHeroRewardInfo.generate_id(original_id, level)

        activity_reward = BasicActivityHeroRewardInfo()
        activity_reward.id = id
        activity_reward.basic_id = basic_id
        activity_reward.original_id = original_id
        activity_reward.weight = weight


        return activity_reward


    def update(self, level, items_id, items_num, weight):
        """
        """
        self.level = level
        self.items_id = items_id
        self.items_num = items_num
        self.weight = weight


    def get_items(self):
        #items_id = utils.split_to_int(self.items_id)
        #items_num = utils.split_to_int(self.items_num)

        #assert len(items_id) == len(items_num)
        #items = []
        #for i in range(len(items_id)):
        #    items.append((items_id[i], items_num[i]))
        items = []
        items.append((int(self.items_id), int(self.items_num)))
        return items


