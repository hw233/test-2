#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟 id 分配逻辑
"""

from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataRedisAgent


class UnionAllocator(object):
    """联盟 id 分配
    """

    def allocate(self):
        """进行 id 分配
        """
        self._agent = DataRedisAgent().redis.client
        union_id = self._agent.incr("IDunion")
        return union_id

