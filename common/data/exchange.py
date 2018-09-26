#coding:utf8
"""
Created on 2016-07-03
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 兑换信息
"""

from datalib.data_loader import data_loader
import random

class CommonExchangeInfo(object):
    """兑换信息"""

    MONEY_TO_FOOD = "money_to_food_proportion"
    FOOD_TO_MONEY = "food_to_money_proportion"

    __slots__ = [
        "id",
        "last_refresh_time",
        "money_proportion",
        "food_proportion",
    ]

    def __init__(self):
        self.id = 0
        self.last_refresh_time = 0
        self.money_proportion = 0.0
        self.food_proportion = 0.0

    @staticmethod
    def create(id):
        exchange = CommonExchangeInfo()
        exchange.id = id
        exchange.last_refresh_time = 0
        exchange.money_proportion = CommonExchangeInfo.make_proportion(
            CommonExchangeInfo.MONEY_TO_FOOD)
        exchange.food_proportion = CommonExchangeInfo.make_proportion(
            CommonExchangeInfo.FOOD_TO_MONEY)

        return exchange

    @staticmethod
    def make_proportion(t):
        """生成兑换比例"""
        range_string = data_loader.ExchangeBasicInfo_dict[t].value
        max_proportion = float(range_string.split("-")[0])
        min_proportion = float(range_string.split("-")[1])
        return random.uniform(max_proportion, min_proportion)

    @staticmethod
    def refresh_time():
        """获取刷新间隔时间"""
        return int(float(data_loader.ExchangeBasicInfo_dict["refresh_time"].value))

    def refresh(self):
        self.money_proportion = self.make_proportion(self.MONEY_TO_FOOD)
        self.food_proportion = self.make_proportion(self.FOOD_TO_MONEY)