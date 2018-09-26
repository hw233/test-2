#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场战斗记录
"""
import base64

class TransferRecordInfo(object):
    ATTACK_WIN = 1
    ATTACK_LOSE = 2
    DEFEND_WIN = 3
    DEFEND_LOSE = 4

    __slots__ = (
        "id",
        "user_id",
        "index",
        "rival_user_id",
        "rival_user_name",
        "rival_level",
        "rival_icon",
        "status",
        "self_rank",
        "rival_rank"
    )

    def __init__(self):
        self.id = 0
        self.user_id = 0
        self.index = 0
        self.rival_user_id = 0
        self.rival_user_name = ''
        self.rival_level = 0
        self.rival_icon = 0
        self.status = self.ATTACK_WIN
        self.self_rank = 0
        self.rival_rank = 0

    @staticmethod
    def create(user_id, index, rival_user_id, rival_user_name, rival_level, rival_icon,
            status, self_rank, rival_rank):
        transfer_record = TransferRecordInfo()
        transfer_record.id = user_id << 32 | index
        transfer_record.user_id = user_id
        transfer_record.index = index
        transfer_record.rival_user_id = rival_user_id
        transfer_record.rival_user_name = base64.b64encode(rival_user_name)
        transfer_record.rival_level = rival_level
        transfer_record.rival_icon = rival_icon
        transfer_record.status = status
        transfer_record.self_rank = self_rank
        transfer_record.rival_rank = rival_rank

        return transfer_record

    def get_rival_user_name(self):
        if self.rival_user_name == "":
            return ""
        else:
            return base64.b64decode(self.rival_user_name)
