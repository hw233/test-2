#coding:utf8
"""
Created on 2016-09-21
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

import base64
from utils import logger
from utils import utils


class BasicActivityStepInfo(object):
    """
    """

    __slots__ = [
            "id",
            "basic_id",
            "target",
            "default_lock",
            "heroes_basic_id",
            "items_id",
            "items_num",

            "gold",
            "description",
            "value1",
            "value2",
            ]

    def __init__(self):
        self.id = 0
        self.basic_id = 0
        self.target = 0
        self.default_lock = False
        self.heroes_basic_id = ''
        self.items_id = ''
        self.items_num = ''

        self.gold = 0
        self.description = ''
        self.value1 = 0
        self.value2 = 0

    @staticmethod
    def create(id, basic_id):
        """
        """
        activity_step = BasicActivityStepInfo()
        activity_step.id = id
        activity_step.basic_id = basic_id

        #todo

        return activity_step


    def update(self, target, default_lock, heroes_basic_id, items_id, items_num, gold, 
            description, value1, value2):
        """
        """
        self.target = target
        self.default_lock = default_lock
        self.heroes_basic_id = utils.join_to_string(heroes_basic_id)
        self.items_id = utils.join_to_string(items_id)
        self.items_num = utils.join_to_string(items_num)
        self.gold = gold
        #默认已经传的description已经是base64编码过
        self.description = description  #base64.b64encode(description)
        self.value1 = value1
        self.value2 = value2


    def get_heroes_basic_id(self):
        return utils.split_to_int(self.heroes_basic_id)


    def get_items(self):
        items_id = utils.split_to_int(self.items_id)
        items_num = utils.split_to_int(self.items_num)

        assert len(items_id) == len(items_num)
        items = []
        for i in range(len(items_id)):
            items.append((items_id[i], items_num[i]))

        return items





