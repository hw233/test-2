#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class CountryInfo(object):
    """country的公共信息
    """

    __slots__ = [
            "id",
            "wei_weight",
            "shu_weight",
            "wu_weight",
            ]

    def __init__(self):
        self.id = 0
        self.wei_weight = 0
        self.shu_weight = 0
        self.wu_weight = 0

    @staticmethod
    def create(id):
        """新建信息
        """
        country = CountryInfo()
        country.id = id
        country.wei_weight = 0
        country.shu_weight = 0
        country.wu_weight = 0
        
        return country


    def get_wei_weight(self):
        return self.wei_weight

    def get_shu_weight(self):
        return self.shu_weight

    def get_wu_weight(self):
        return self.wu_weight

    def get_country_of_least_weight(self):
        """返回权重最低的国家势力
           1表示魏，2表示蜀，3表示吴
        """
        if self.wei_weight <= self.shu_weight and self.wei_weight <= self.wu_weight:
            return 1
        elif self.shu_weight <= self.wei_weight and self.shu_weight <= self.wu_weight:
            return 2
        else:
            return 3


    def add_wei_weight(self):
        self.wei_weight += 1

    def add_shu_weight(self):
        self.shu_weight += 1

    def add_wu_weight(self):
        self.wu_weight += 1

    def reduce_wei_weight(self):
        self.wei_weight -= 1
        self.wei_weight = max(0, self.wei_weight)

    def reduce_shu_weight(self):
        self.shu_weight -= 1
        self.shu_weight = max(0, self.shu_weight)

    def reduce_wu_weight(self):
        self.wu_weight -= 1
        self.wu_weight = max(0, self.wu_weight)







