#coding:utf8
"""
Created on 2015-11-05
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 姓名自动生成逻辑
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from datalib.data_loader import data_loader


class NameGenerator(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.candidates = []
        for id in data_loader.UserNameBasicInfo_dict:
            self.candidates.append(id)
        self.length = len(self.candidates)


    def gen_by_id(self, id):
        index = id % self.length
        name_id = self.candidates[index]
        name = data_loader.UserNameBasicInfo_dict[name_id].name.encode("utf-8")
        return name


    def gen(self):
        random.seed()
        name_id = random.sample(self.candidates, 1)[0]
        name = data_loader.UserNameBasicInfo_dict[name_id].name.encode("utf-8")
        return name


