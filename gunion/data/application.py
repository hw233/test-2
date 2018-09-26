#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟申请相关数据存储结构
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnionApplicationInfo(object):
    """联盟申请信息
    """

    __slots__ = [
            "id",
            "union_id",
            "user_id",
            "user_name",
            "user_icon",
            "user_level",
            "user_battle_score",
            "time",
            ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.user_id = 0
        self.user_name = ''
        self.user_icon = 0
        self.user_level = 0
        self.user_battle_score = 0
        self.time = 0

    @staticmethod
    def generate_id(union_id, user_id):
        id = union_id << 32 | user_id
        return id


    @staticmethod
    def create(union_id, user_id):
        id = UnionApplicationInfo.generate_id(union_id, user_id)

        application = UnionApplicationInfo()
        application.id = id
        application.union_id = union_id
        application.user_id = user_id
        return application


    def set_detail(self, user_name, user_icon, user_level, user_battle_score, now):
        self.user_name = base64.b64encode(user_name)
        self.user_icon = user_icon
        self.user_level = user_level
        self.user_battle_score = user_battle_score
        self.time = now


    def is_available(self, now):
        gap = now - self.time
        return gap <= int(float(data_loader.UnionConfInfo_dict["application_lifetime"].value))


    def get_readable_user_name(self):
        return base64.b64decode(self.user_name)

