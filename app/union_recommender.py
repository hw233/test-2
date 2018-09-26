#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟推荐匹配逻辑
"""

import random
from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy


class UnionRecommender(object):
    """联盟推荐
    """

    def add_condition(self, user):
        self.user = user
        self.result = []


    def match(self, now):
        """进行推荐
        """
        proxy = DataProxy()
        proxy.get_all("unionunion", "id")
        defer = proxy.execute()
        defer.addCallback(self._calc_result, now)
        return defer


    def _calc_result(self, proxy, now):
        """推荐计算
        1 推荐新创建的联盟
        2 推荐活跃度较高的联盟
        3 过滤无法加入的联盟（当前人数，加入状态，加入等级限制）
        """
        pre_match = []

        unions = proxy.get_all_result("unionunion")
        for union in unions:
            if union.join_status == union.JOIN_STATUS_DISABLE:
                continue
            elif union.current_number >= union.max_number:
                continue
            elif union.join_level_limit > self.user.level:
                continue

            pre_match.append(union)

        if len(pre_match) <= 20:
            self.result = pre_match
        else:
            self._filter(pre_match, now)

        return self


    def _filter(self, pre_match, now):
        """进行筛选
        """
        #从近期繁荣度排名靠前的联盟中选择
        active_unions = sorted(pre_match, key = lambda u:u.recent_prosperity, reverse = True)
        active_unions = active_unions[:30]
        num = min(len(active_unions), 10)
        self.result = random.sample(active_unions, num)

        #从最近创建的联盟中选择
        new_unions = []
        for union in pre_match:
            if union in self.result:
                continue
            if now - union.create_time < 604800:#一周
                new_unions.append(union)
        num = min(len(new_unions), 10)
        self.result.extend(random.sample(new_unions, num))

