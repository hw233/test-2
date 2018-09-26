#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟排名逻辑
"""

from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy


class UnionRanker(object):
    """联盟推荐
    """
    RANK_START = 0
    RANK_STOP = 19

    def match(self, now):
        proxy = DataProxy()
        proxy.search_by_rank(
                "unionunion", "recent_prosperity", self.RANK_START, self.RANK_STOP)
        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        self.result = proxy.get_rank_result(
                "unionunion", "recent_prosperity", self.RANK_START, self.RANK_STOP)
        return self


