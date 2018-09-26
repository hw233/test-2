#coding:utf8
"""
Created on 2016-03-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 充值相关数据存储结构
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class PayRecordInfo(object):
    """充值记录
    """

    __slots__ = [
            "id",
            "user_id",
            "index",
            "order_id",
            "price",
            "order_number",
            "time",
            "platform",
            "is_finish",
            ]

    def __init__(self):
        self.id = 0
        self.user_id = 0
        self.index = 0
        self.order_id = 0
        self.price = 0.0
        self.order_number = ''
        self.time = 0
        self.platform = 0
        self.is_finish = False

    @staticmethod
    def create(user_id, index, platform, now):
        """创建充值记录
        """
        id = PayRecordInfo.generate_id(user_id, index)

        record = PayRecordInfo()
        record.id = id
        record.user_id = user_id
        record.index = index
        record.platform = platform
        record.time = now
        record.is_finish = False
        return record


    @staticmethod
    def generate_id(user_id, index):
        id = user_id << 32 | index
        return id


    def set_detail(self, order_id, order_number, price):
        self.order_id = order_id
        self.order_number = order_number
        self.price = price


    def finish(self, order = None):
        assert self.is_finish is False

        if order is not None:
            self.order_id = order.id
            self.price = order.truePrice

        self.is_finish = True


