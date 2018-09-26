#coding:utf8
"""
Created on 2016-12-29
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 竞技场对战记录相关
"""

import base64
import time
from utils import logger
from utils import utils
from datalib.data_loader import data_loader

class MeleeRecordInfo(object):
    """乱斗场场对战记录
    """

    STATUS_INVALID = 0
    STATUS_ATTACK_WIN = 1     #进攻胜利
    STATUS_ATTACK_LOSE = 2    #进攻失败
    STATUS_DEFEND_WIN = 3     #防御成功
    STATUS_DEFEND_LOSE = 4    #防御失败

    def __init__(self, id = 0, user_id = 0,
            player_id = 0, name = '', level = 0,
            icon_id = 0, status = STATUS_INVALID,
            score_delta = 0):

        self.id = id
        self.user_id = user_id
        self.player_id = player_id
        self.name = name
        self.level = level
        self.icon_id = icon_id
        self.status = status
        self.score_delta = score_delta


    @staticmethod
    def generate_id(user_id, index):
        id = user_id << 32 | index
        return id

    @staticmethod
    def get_index(id):
        index = id & 0xFFFFFFFF
        return index


    @staticmethod
    def create(index, user_id):
        """创建演武场对战记录
        """
        id = MeleeRecordInfo.generate_id(user_id, index)
        arena_record = MeleeRecordInfo(id, user_id)
        return arena_record


    def set_record(self, player_id, name, level,
            icon_id, status, score_delta):
        """
        """
        self.player_id = player_id
        self.name = name
        self.level = level
        self.icon_id = icon_id
        self.status = status
        self.score_delta = score_delta


    def get_readable_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.name)


