#coding:utf8
"""
Created on 2016-02-29
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 竞技场对战记录相关
"""

import base64
import time
from utils import logger
from utils import utils
from datalib.data_loader import data_loader

class PlunderRecordInfo(object):
    """仇人记录
    """

    def __init__(self, id = 0, 
            user_id = 0, rival_user_id = 0,
            name = '', level = 0,
            icon_id = 0, country = 0,
            hatred = 0,
            been_attacked_num = 0,
            score = 0, union_id = 0,
            today_attack_money = 0,
            today_attack_food = 0,
            today_robbed_money = 0,
            today_robbed_food = 0):

        self.id = id
        self.user_id = user_id
        self.rival_user_id = rival_user_id
        self.name = name
        self.level = level
        self.icon_id = icon_id
        self.country = country
        self.hatred = hatred
        self.been_attacked_num = been_attacked_num
        self.score = score
        self.union_id = union_id
        self.today_attack_money = today_attack_money
        self.today_attack_food = today_attack_food
        self.today_robbed_money = today_robbed_money
        self.today_robbed_food = today_robbed_food


    @staticmethod
    def generate_id(user_id, rival_user_id):
        id = user_id << 32 | rival_user_id
        return id


    @staticmethod
    def create(user_id, rival_user_id):
        """创建
        """
        id = PlunderRecordInfo.generate_id(user_id, rival_user_id)
        plunder_record = PlunderRecordInfo(id, user_id, rival_user_id)
        return plunder_record


    def set_record(self, name, level, icon_id, country, hatred, been_attacked_num, score):
        """
        """
        self.name = name
        self.level = level
        self.icon_id = icon_id
        self.country = country
        self.hatred = hatred
        self.been_attacked_num = been_attacked_num
        self.score = score


    def get_readable_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.name)


    def modify_hatred(self, diff):
        """diff可正可负
        """

        self.hatred = max(0, self.hatred + diff)


    def reset_daily(self):
        """
        """
        self.been_attacked_num = 0
        self.today_attack_money = 0
        self.today_attack_food = 0
        self.today_robbed_money = 0
        self.today_robbed_food = 0


    def reset_been_attacked_num(self):
        """
        """
        self.been_attacked_num = 0


    def add_been_attacked_num(self):
        """
        """
        self.been_attacked_num = self.been_attacked_num + 1


    def add_today_attack_resource(self, money, food):
        """
        """
        self.today_attack_money += money
        self.today_attack_food += food
        self.today_attack_money = max(0, self.today_attack_money)
        self.today_attack_food = max(0, self.today_attack_food)


    def add_today_robbed_resource(self, money, food):
        """
        """
        self.today_robbed_money += money
        self.today_robbed_food += food
        self.today_robbed_money = max(0, self.today_robbed_money)
        self.today_robbed_food = max(0, self.today_robbed_food)



