#coding:utf8
"""
Created on 2016-07-11
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 中央控制
"""

from utils import logger
from utils import utils


class ConsoleInfo(object):
    """控制数据
    """

    __slots__ = [
            "id",
            "broadcast_num",
            "mail_num",
            ]

    def __init__(self):
        self.id = 0

        self.broadcast_num = 0
        self.mail_num = 0

    @staticmethod
    def create(common_id):
        """创建
        """
        console = ConsoleInfo()
        console.id = common_id

        console.broadcast_num = 0
        console.mail_num = 0
        return console


    def generate_broadcast_id(self):
        self.broadcast_num += 1
        return self.broadcast_num

