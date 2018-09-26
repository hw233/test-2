#coding:utf8
"""
Created on 2016-03-26
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 用户头像id自动生成逻辑
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from datalib.data_loader import data_loader


class IconGenerator(object):
    __metaclass__ = Singleton

    def __init__(self):
        #头像icon目前先从Init表里拿
        self.user_icons_id = data_loader.InitUserBasicInfo_dict[1].userIconId


    def gen_by_id(self, id):
        index = id % len(self.user_icons_id)
        return self.user_icons_id[index]


    def gen(self):
        random.seed()
        index = random.randint(0, len(self.user_icons_id) - 1)
        return self.user_icons_id[index]


