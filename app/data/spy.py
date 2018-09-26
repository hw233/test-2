#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 谍报随机事件
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class SpyPool(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._levels = {}

        for id in data_loader.EventSpyBasicInfo_dict:
            weight = data_loader.EventSpyBasicInfo_dict[id].weight
            level = data_loader.EventSpyBasicInfo_dict[id].level
            if level not in self._levels:
                self._levels[level] = [(id, weight)]
            else:
                info = self._levels[level]
                weight += info[-1][1]
                info.append((id, weight))


    def choose(self, level):
        """随机选择
        """
        assert level in self._levels

        info = self._levels[level]
        random.seed()
        c = random.uniform(0, info[-1][1])
        for index, (id, weight) in enumerate(info):
            if c < weight:
                return id


