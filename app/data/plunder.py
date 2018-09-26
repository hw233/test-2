#coding:utf8
"""
Created on 2017-11-21
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : pvp掠夺功能相关
"""

import time
import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class PlunderInfo(object):
    """掠夺相关信息
    """


    def __init__(self, user_id = 0, 
            attack_num = 0,
            reset_num = 0,
            rivals_user_id = '',
            daily_win_num = 0,
            total_win_num = 0,
            total_lose_num = 0):

        self.user_id = user_id
        self.attack_num = attack_num
        self.reset_num = reset_num
        self.rivals_user_id = rivals_user_id
        self.daily_win_num = daily_win_num
        self.total_win_num = total_win_num
        self.total_lose_num = total_lose_num


    @staticmethod
    def create(user_id):
        """创建掠夺信息
        """
        plunder = PlunderInfo(user_id)
        return plunder


    def reset(self):
        """
        """
        self.attack_num = 0
        self.reset_num = 0
        self.daily_win_num = 0


    def consume_attack_num(self):
        """
        """
        self.attack_num += 1


    def reset_attack_num(self):
        """
        """
        self.attack_num = 0
        self.reset_num += 1


    def get_left_reset_num(self):
        """
        """
        max_reset_num = int(float(
            data_loader.OtherBasicInfo_dict["max_prey_reset_num"].value))
        
        return max(0, max_reset_num - self.reset_num)


    def generate_plunder_rivals_id(self):
        """掠夺匹配4个对手的rival_id
        """
        RIVAL_BASE_ID = int(float(data_loader.MapConfInfo_dict['plunder_node_basic_id'].value))
        
        return [self.user_id << 32 | RIVAL_BASE_ID,
                self.user_id << 32 | (RIVAL_BASE_ID + 1),
                self.user_id << 32 | (RIVAL_BASE_ID + 2),
                self.user_id << 32 | (RIVAL_BASE_ID + 3)]


    def generate_specify_rival_id(self):
        """指定查询对手的rival_id
        """
        RIVAL_BASE_ID = int(float(data_loader.MapConfInfo_dict['plunder_node_basic_id'].value))
        
        return self.user_id << 32 | RIVAL_BASE_ID + 4


    def get_plunder_rival_id(self, rival_user_id):
        """返回匹配对手的rival id
        """
        RIVAL_BASE_ID = int(float(data_loader.MapConfInfo_dict['plunder_node_basic_id'].value))
        
        rivals_user_id = utils.split_to_int(self.rivals_user_id)
        index = 0
        if_exist = False
        for user_id in rivals_user_id:
            if rival_user_id == user_id:
                if_exist = True
                break
            index += 1

        if not if_exist:
            return 0

        return self.user_id << 32 | (RIVAL_BASE_ID + index)


    def set_plunder_rivals_user_id(self, rivals_user_id):
        """设置匹配对手的id
        """
        self.rivals_user_id = utils.join_to_string(rivals_user_id)


