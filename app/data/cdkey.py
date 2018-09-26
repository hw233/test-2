#coding:utf8
"""
Created on 2016-05-05
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 兑换码相关
"""

from firefly.utils.singleton import Singleton
from utils import utils
from utils import logger
from utils.redis_agent import RedisAgent


class CDkeyRedisAgent(object):
    """访问CDkey Reids
    """
    __metaclass__ = Singleton

    def connect(self, ip, port, db = '0', password = None, timeout = 1):
        """初始化
        Args:
            timeout : 连接超时事件，单位 s
        """
        self.redis = RedisAgent()
        self.redis.connect(ip, port, db, password, timeout)


    def set(self, key, value):
        """设置 key
        内部测试接口
        """
        return self.redis.client.setnx(key, value)



    def get(self, key):
        """根据 key，获取礼包 id
        Returns:
            如果 cdkey 不合法，返回0
        """
        value = self.redis.client.get(key)
        if value is None:
            return 0
        return int(value)


    def finish(self, key):
        """使用 key
        Return:
            True/False
        """
        if self.redis.client.delete(key) == 0:
            return False
        return True




