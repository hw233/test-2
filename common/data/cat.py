#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 招财猫
"""

class CatInfo(object):

    __slots__ = (
        "id",
        "common_id",
        "user_id",
        "name",
        "gold",
        "index",
    )

    def __init__(self):
        self.id = 0
        self.common_id = 1
        self.user_id = 0
        self.name = ""
        self.gold = 0
        self.index = 1
       

    @staticmethod
    def generate_id(common_id, index):
        return common_id << 32 | index

    @staticmethod
    def create(common_id, user_id, name, gold, index):
        cat = CatInfo()
        cat.id = CatInfo.generate_id(common_id, index)
        cat.common_id = common_id
        cat.user_id = user_id
        cat.name = name
        cat.gold = gold
        cat.index = index
        return cat
