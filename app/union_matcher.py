#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟信息匹配逻辑
"""

from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy


class UnionMatcher(object):
    """查询联盟
    """

    def add_condition(self, match_id = None, match_name = None):
        """提供匹配条件
        """
        self.id = match_id
        self.name = match_name
        self.result = []
        self.result_id = set()


    def match(self):
        """进行匹配
        """
        proxy = DataProxy()
        proxy.get_all("unionunion", "id")
        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        """匹配计算
        """
        unions = proxy.get_all_result("unionunion")
        for union in unions:
            if self.id is not None and self.id == union.id:
                self._add_result(union)
            if self.name is not None and self.name == union.get_readable_name():
                self._add_result(union)

        return self


    def _add_result(self, union):
        if union.id in self.result_id:#去重
            return
        self.result.append(union)
        self.result_id.add(union.id)


