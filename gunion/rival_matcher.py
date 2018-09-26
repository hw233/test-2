#coding:utf8
"""
Created on 2016-07-29
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : PVE 敌人匹配逻辑
"""
import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class PVEEnemyPool(object):
    """PVE 敌人池
    """
    __metaclass__ = Singleton

    def __init__(self):
        self._rivals = {}
        for id in data_loader.PVEEnemyBasicInfo_dict:
            enemy = data_loader.PVEEnemyBasicInfo_dict[id]
            if enemy.level not in self._rivals:
                self._rivals[enemy.level] = [enemy]
            else:
                self._rivals[enemy.level].append(enemy)


    def get(self, level):
        random.seed()
        choose = random.sample(self._rivals[level], 1)[0]

        name_index = random.sample(data_loader.UserNameBasicInfo_dict, 1)[0]
        name = data_loader.UserNameBasicInfo_dict[name_index].name.encode("utf-8")
        icon = random.sample(data_loader.InitUserBasicInfo_dict[1].userIconId, 1)[0]

        return (choose, name, icon)


