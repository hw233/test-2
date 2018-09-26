#coding:utf8
"""
Created on 2015-05-25
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 用户统计相关
"""

from utils import logger


class StatisticsInfo(object):
    def __init__(self, user_id = 0):
        self.user_id = user_id


    @staticmethod
    def create(user_id):
        statistics = StatisticsInfo(user_id)
        return statistics



