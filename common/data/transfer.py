#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场公共数据
"""

class TransferInfo(object):

    __slots__ = (
        "id",
        "common_id",
        "user_id",
        "rank",
        "is_robot",
    )

    def __init__(self):
        self.id = 0
        self.common_id = 1
        self.user_id = 0
        self.rank = 2000
        self.is_robot = False

    @staticmethod
    def generate_id(common_id, user_id):
        return common_id << 32 | user_id

    @staticmethod
    def create(common_id, user_id, rank=2000, is_robot=False):
        transfer = TransferInfo()
        transfer.id = TransferInfo.generate_id(common_id, user_id)
        transfer.common_id = common_id
        transfer.user_id = user_id
        transfer.rank = rank
        transfer.is_robot = is_robot

        return transfer