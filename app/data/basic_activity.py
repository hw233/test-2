#coding:utf8
"""
Created on 2016-09-21
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

import time
import base64
from utils import logger
from utils import utils


class BasicActivityInfo(object):
    """
    """

    __slots__ = [
            "id",
            "basic_id",
            "style_id",
            "type_id",
            "start_time",
            "end_time",
            "start_day",
            "end_day",

            "steps_id",
            "icon_name",
            "name",
            "description",
            "hero_basic_id",
            "weight"
            ]

    STYLE_ALL = 0
    STYLE_SEVEN_DAY = 1       #开服七天活动
    STYLE_FIRST_PAY = 2       #首冲活动
    STYLE_DAILY = 3           #日常活动
    STYLE_SHOP = 4            #神秘商店活动
    STYLE_NORMAL = 5          #普通活动
    STYLE_FESTIVAL = 6        #节日活动


    def __init__(self):
        self.id = 0
        self.basic_id = 0
        self.style_id = 0     #活动大分类的id
        self.type_id = 0      #活动类型的id
        self.start_time = 0
        self.end_time = 0
        self.start_day = 0
        self.end_day = 0

        self.steps_id = ''
        self.icon_name = ''
        self.name = ''
        self.description = ''
        self.hero_basic_id = 0
        self.weight = 0

    @staticmethod
    def create(id, basic_id):
        """
        """
        activity = BasicActivityInfo()
        activity.id = id
        activity.basic_id = basic_id

        #todo

        return activity


    def update(self, style_id, type_id, start_time, end_time, start_day, end_day, 
            icon_name, name, description, hero_basic_id, steps_id, weight):
        """
        """
        self.style_id = style_id
        self.type_id = type_id
        self.start_time = start_time
        self.end_time = end_time
        self.start_day = start_day
        self.end_day = end_day

        #用 base64 编码存储，避免一些非法字符造成的问题
        #默认已经传的description已经是base64编码过
        self.icon_name = icon_name       #base64.b64encode(icon_name)
        self.name = name                #base64.b64encode(name)
        self.description = description  #base64.b64encode(description)
        self.hero_basic_id = hero_basic_id

        self.steps_id = utils.join_to_string(steps_id)
        self.weight = weight


    def get_steps(self):
        return utils.split_to_int(self.steps_id)


    def is_invalid(self, now):
        """活动基础数据配置的结束时间是否已经过期
        """
        if self.end_time == '':
            return False

        end_time = utils.get_end_second_by_timestring(self.end_time)

        logger.debug("basic activity[id=%d][end_time=%s][end_timestamp=%d][now=%d]" % 
                 (self.id, self.end_time, end_time, now))
        WEEK_SECONDS = 86400 * 7
        if end_time + WEEK_SECONDS >= now:    #超过1周算过期
            return False
        else:
            return True


    def is_living(self, now):
        """当前是否处于活动时间中
        """
        if self.end_time == '' or self.start_time == '':
            return False

        start_time = utils.get_start_second_by_timestring(self.start_time)
        end_time = utils.get_end_second_by_timestring(self.end_time)


        if self.style_id == BasicActivityInfo.STYLE_FESTIVAL:
            return now + 86400 * 8 >= start_time and now <= end_time
        else:
            return now >= start_time and now <= end_time


