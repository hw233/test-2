#coding:utf8
"""
Created on 2016-07-08
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 定时红包功能
"""

import time
import random
import math
import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.core import reward as reward_module



class ChestInfo(object):
    """红包信息
    """

    CHEST_START_HOUR = 10
    CHEST_END_HOUR = 23
    INTERNAL_TIME = 300 #可抽红包间隔： 例如2点抢红包，2点-2点05分之间都可以抢


    __slots__ = [
           "user_id",
           "next_start_time",
           "next_end_time",
           "level",
           "money",
           "food",
           "gold",
           "items_id",
           "items_num",
           ]

    def __init__(self):
        self.user_id = 0
        self.next_start_time = 0
        self.next_end_time = 0
        self.level = 0
        self.money = 0
        self.food = 0
        self.gold = 0
        self.items_id = ''
        self.items_num = ''

    @staticmethod
    def create(user_id, now):
        """初始的红包信息
        Args:
            user_id[int]: 用户 id
            now[int]: 当前时间戳
        Returns:
            chest[ChestInfo]
        """
        chest = ChestInfo()
        chest.user_id = user_id
        chest.next_start_time = 0
        chest.next_end_time = INTERNAL_TIME = 300 
        chest.level = 0
        chest.money = 0
        chest.food = 0
        chest.gold = 0
        chest.items_id = ''
        chest.items_num = ''

        return chest


    def is_in_duration(self, now):
        """是否在红包可抢的时间范围内
        """
        if (now >= self.next_start_time and now <= self.next_end_time + 900):
            return True
        else:
            return False

    
    def update_info(self, now):
        """更新下次红包信息
        """
        self._calc_next_start_time(now)
        self._calc_next_reward()

        return True


    def get_items_info(self):
        """
        """
        items_id = utils.split_to_int(self.items_id)
        items_num = utils.split_to_int(self.items_num)
        items_info = []
        for i in range(0, len(items_id)):
            items_info.append((items_id[i], items_num[i]))

        return items_info



    def _calc_next_start_time(self, now):
        """生成下次抽红包时间
        """
        date = time.localtime(now)
        today_start = (date.tm_year, date.tm_mon, date.tm_mday, ChestInfo.CHEST_START_HOUR, 0, 0,
            date.tm_wday, date.tm_yday, date.tm_isdst)
        today_end = (date.tm_year, date.tm_mon, date.tm_mday, ChestInfo.CHEST_END_HOUR, 0, 0,
            date.tm_wday, date.tm_yday, date.tm_isdst)
        
        today_start_ts = long(time.mktime(today_start))
        today_end_ts = long(time.mktime(today_end))

        if now < today_start_ts:
            #当天可抽红包的时段还没到
            self.next_start_time = today_start_ts

        elif now >= today_end_ts:
            #当天可抽红包的时段已经结束
            tomorrow = now + utils.SECONDS_OF_DAY
            date_tomorrow = time.localtime(tomorrow)
            tomorrow_start = (date_tomorrow.tm_year, date_tomorrow.tm_mon, 
                    date_tomorrow.tm_mday, ChestInfo.CHEST_START_HOUR, 0, 0, 
                    date_tomorrow.tm_wday, date_tomorrow.tm_yday, date_tomorrow.tm_isdst)


            tomorrow_start_ts = long(time.mktime(tomorrow_start))
            self.next_start_time = tomorrow_start_ts

        else:
            #处于红包活动时间内
            next_start = (date.tm_year, date.tm_mon, date.tm_mday, date.tm_hour + 1, 0, 0,
                    date.tm_wday, date.tm_yday, date.tm_isdst)
            self.next_start_time = long(time.mktime(next_start))

        self.next_end_time = self.next_start_time + ChestInfo.INTERNAL_TIME

        return True



    def _calc_next_reward(self):
        """生成下次抽红包的奖励
        """
        self.level = 0
        self.money = 0
        self.food = 0
        self.gold = 0
        self.items_id = ""
        self.items_num = ""

        pool = getattr(data_loader, "BoxInfo_dict")
        total_weight = 0
        for id in pool:
            total_weight += pool[id].weight

        roll = random.randint(0, total_weight-1)
        sum = 0
        for id in pool:
            sum += pool[id].weight
            if roll < sum:
                self.level = pool[id].level
                self.money = pool[id].reward.money
                self.food = pool[id].reward.food
                self.gold = pool[id].reward.gold
                self.items_id = utils.join_to_string(pool[id].reward.itemBasicIds)
                self.items_num = utils.join_to_string(pool[id].reward.itemNums)
                break

        return True






