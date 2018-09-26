#coding:utf8
"""
Created on 2015-12-26
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 世界地图随机事件公共方法入口
"""

import random
from utils import logger
from firefly.utils.singleton import Singleton
from datalib.data_loader import data_loader


class EventCommonLogic(object):

    def __init__(self, type,
            arise = None, clear = None, timeout = None, stop = None):
        self._type = type
        self._arise = arise
        self._clear = clear
        self._stop = stop
        self._timeout = timeout


    def arise(self, data, node, now, **kwargs):
        """出现时的方法
        """
        if self._arise is None:
            raise Exception("Arise lucky event invalid[type=%d]" % self._type)
        return self._arise(data, node, now, **kwargs)


    def clear(self, data, node, now, **kwargs):
        """清除时的方法
        1 出现未启动，超过 idletime
        2 出现未启动，节点控制权发生变动
        """
        if self._clear is None:
            raise Exception("Clear lucky event invalid[type=%d]" % self._type)
        return self._clear(data, node, now, **kwargs)


    def timeout(self, data, node, now, **kwargs):
        """超时时的方法
        1 启动未结束，超过 lifetime
        """
        if self._timeout is None:
            raise Exception("Timeout lucky event invalid[type=%d]" % self._type)
        return self._timeout(data, node, now, **kwargs)


    def stop(self, data, node, now, **kwargs):
        """中止时的方法
        1 启动未结束，节点控制权发生变动
        """
        if self._stop is None:
            raise Exception("Stop lucky event invalid[type=%d]" % self._type)
        return self._stop(data, node, now, **kwargs)



class EventHandler(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._e = {}


    def register(self, type,
            arise = None, clear = None, timeout = None, stop = None):
        """注册随机事件的不同方法
        """
        assert type not in self._e
        self._e[type] = EventCommonLogic(type, arise, clear, timeout, stop)


    def arise(self, data, node, now, **kwargs):
        """出现时的方法
        """
        event_type = kwargs["event_type"]
        return self._e[event_type].arise(data, node, now, **kwargs)


    def clear(self, data, node, now, **kwargs):
        """清除时的方法
        1 出现未启动，超过 idletime
        2 出现未启动，节点控制权发生变动
        """
        return self._e[node.event_type].clear(data, node, now, **kwargs)


    def timeout(self, data, node, now, **kwargs):
        """超时时的方法
        1 启动未结束，超过 lifetime
        """
        return self._e[node.event_type].timeout(data, node, now, **kwargs)


    def stop(self, data, node, now, **kwargs):
        """中止时的方法
        1 启动未结束，节点控制权发生变动
        """
        return self._e[node.event_type].stop(data, node, now, **kwargs)

