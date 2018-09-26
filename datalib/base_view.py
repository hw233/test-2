#coding:utf8
"""
Created on 2016-05-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 基础视图
"""

import copy
from twisted.internet.defer import Deferred
from utils import logger
from datalib.data_element import UniqueData
from datalib.data_element import DataSet
from datalib.data_proxy4redis import DataProxy


class BaseView(object):
    """基础视图
    """

    __slots__ = [
            "id",
            "_valid",
            ]


    def __init__(self):
        self.id = None
        self._valid = False


    def is_valid(self):
        return self._valid

