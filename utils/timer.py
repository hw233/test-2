#coding:utf8
"""
Created on 2015-03-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 时间处理逻辑
"""

import time


class Timer(object):
    """计时器
    """

    def __init__(self, id = 0):
        self.id = id
        self.start = time.time()
        self.now = int(self.start)


    def count_ms(self):
        duration = time.time() - self.start
        return int(duration * 1000)

