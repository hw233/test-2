#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

import base64
from utils import logger
from utils import utils


class BroadcastInfo(object):
    """一条广播信息
    """

    __slots__ = [
            "id",
            "common_id",
            "create_time",
            "mode_id",
            "priority",
            "life_time",
            "content",
            ]

    def __init__(self):
        self.id = 0
        self.common_id = 0
        self.create_time = 0
        self.mode_id = 0
        self.priority = 0
        self.life_time = 0

        self.content = ''

    @staticmethod
    def create(id, common_id, now, mode_id, priority, life_time, content):
        """新建一条广播信息
        """
        broadcast = BroadcastInfo()
        broadcast.id = id
        broadcast.common_id = common_id
        broadcast.create_time = now
        broadcast.mode_id = mode_id
        broadcast.priority = priority
        broadcast.life_time = life_time

        #base64 编码存储，避免一些非法字符造成的问题
        broadcast.content = base64.b64encode(content)
        return broadcast


    def is_overdue(self, now):
        """广播数据是否过期失效
        """
        if self.create_time + self.life_time < now:
            return True
        else:
            return False


    def get_readable_content(self):
        """获取可读的内容
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.content)
