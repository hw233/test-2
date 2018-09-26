#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 好友信息匹配逻辑
"""

from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy


class FriendMatcher(object):
    """查询好友
    """

    def add_condition(self, match_id = None):
        """提供匹配条件
        """
        self.id = match_id
        self.result = []


    def match(self):
        """进行匹配
        """
        proxy = DataProxy()
        proxy.get_all("user", "id")
        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        """匹配计算
        """
        users = proxy.get_all_result("user")
        for user in users:
            if self.id is not None and self.id == user.id:
                self.result.append(user)

        return self


