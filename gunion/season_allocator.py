#coding:utf8
"""
Created on 2016-07-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟 id 分配逻辑
"""

from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataRedisAgent
from datalib.data_loader import data_loader


class SeasonAllocator(object):
    """联盟赛季分配
    """

    def allocate(self, now):
        """根据时间戳计算是第几个赛季，返回赛季编号和赛季开始时间
        Args:
            now[int]: 当前时间戳
        Returns:
            (index, start_time): (赛季编号，赛季开始时间戳)
        """
        self._agent = DataRedisAgent().redis.client
        beginning = self._agent.get("TIMEunionseason")#第一个赛季开始的时间戳
        if beginning is None:
            #如果服务器还没有赛季信息，初始化第一个赛季开始的时间
            beginning = utils.get_start_second_of_week(now)
            self._agent.set("TIMEunionseason", beginning)
        else:
            beginning = int(beginning)

        duration = utils.count_days_diff(beginning, now)
        period = int(float(data_loader.UnionConfInfo_dict["battle_season_last_day"].value))
        index = duration // period + 1
        start_time = beginning + (index - 1) * period * utils.SECONDS_OF_DAY
        return (index, start_time)


    def calc(self, index):
        """根据赛季编号，计算赛季开始时间
        Args:
            index[int]: [1, +)
        Returns:
            start_time
        """
        self._agent = DataRedisAgent().redis.client
        beginning = self._agent.get("TIMEunionseason")#第一个赛季开始的时间戳
        # if beginning is None:
            #如果服务器还没有赛季信息，初始化第一个赛季开始的时间
            # beginning = utils.get_start_second_of_week(now)
            # self._agent.set("TIMEunionseason", beginning)
        # else:
        beginning = int(beginning)

        period = int(float(data_loader.UnionConfInfo_dict["battle_season_last_day"].value))
        start_time = beginning + (index - 1) * period * utils.SECONDS_OF_DAY
        return start_time


    def calc_now(self, now):
        """计算当前时间是第几赛季，以及赛季开始时间
        Returns:
            (index, start_time)
        """
        self._agent = DataRedisAgent().redis.client
        beginning = self._agent.get("TIMEunionseason")#第一个赛季开始的时间戳
        if beginning is None:
            #如果服务器还没有赛季信息，初始化第一个赛季开始的时间
            beginning = utils.get_start_second_of_week(now)
            self._agent.set("TIMEunionseason", beginning)
        else:
            beginning = int(beginning)

        period = int(float(data_loader.UnionConfInfo_dict["battle_season_last_day"].value))
        index = (now - beginning) // (period * utils.SECONDS_OF_DAY) + 1
        start_time = beginning + (index - 1) * period * utils.SECONDS_OF_DAY
        return (index, start_time)


