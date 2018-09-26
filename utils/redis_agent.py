#coding:utf8
"""
Created on 2015-07-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Redis 代理类
"""

import redis
from firefly.server.globalobject import GlobalObject
from utils import logger


class RedisAgent(object):
    """访问 redis
    """

    def __init__(self):
        pass


    def connect(self, ip, port, db, password, timeout):
        self.client = redis.StrictRedis(host = ip, port = port, db = db,
                password = password, socket_timeout = timeout)


    def pipeline(self):
        return self.client.pipeline()


