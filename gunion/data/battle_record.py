#coding:utf8
"""
Created on 2016-07-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争中的战斗记录
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnionBattleRecordInfo(object):
    """联盟战争战斗记录
    """

    __slots__ = [
            "id",
            "union_id",
            "index",
            "time",
            "node_index",
            "node_level",       #联盟战争节点等级
            "is_attacker_win",  #是否攻击方胜利

            "attacker_user_id",
            "attacker_user_name",
            "attacker_user_icon",
            "attacker_union_id",
            "defender_user_id",
            "defender_user_name",
            "defender_user_icon",
            "defender_union_id",
            ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.index = 0
        self.time = 0

        self.node_index = 0
        self.node_level = 0
        self.is_attacker_win = False
        self.attacker_user_id = 0
        self.attacker_user_name = ""
        self.attacker_user_icon = 0
        self.attacker_union_id = 0
        self.defender_user_id = 0
        self.defender_user_name = ""
        self.defender_user_icon = 0
        self.defender_union_id = 0

    @staticmethod
    def generate_id(union_id, index):
        id = union_id << 32 | index
        return id


    @staticmethod
    def create(union_id, index, now):
        record_id = UnionBattleRecordInfo.generate_id(union_id, index)
        record = UnionBattleRecordInfo()
        record.id = record_id
        record.union_id = union_id
        record.index = index
        record.time = now

        record.node_index = 0
        record.node_level = 0
        record.is_attacker_win = False
        record.attacker_user_id = 0
        record.attacker_user_name = ""
        record.attacker_user_icon = 0
        record.attacker_union_id = 0
        record.defender_user_id = 0
        record.defender_user_name = ""
        record.defender_user_icon = 0
        record.defender_union_id = 0

        return record


    def attach_result(self, node_index, node_level, is_attacker_win):
        self.node_index = node_index
        self.node_level = node_level
        self.is_attacker_win = is_attacker_win


    def attach_attacker_info(self, user_id, name, icon, union_id):
        self.attacker_user_id = user_id
        self.attacker_user_name = base64.b64encode(name)
        self.attacker_user_icon = icon
        self.attacker_union_id = union_id


    def attach_defender_info(self, user_id, name, icon, union_id):
        self.defender_user_id = user_id
        self.defender_user_name = base64.b64encode(name)
        self.defender_user_icon = icon
        self.defender_union_id = union_id


    def get_readable_attacker_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.attacker_user_name)


    def get_readable_defender_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.defender_user_name)

