#coding:utf8
"""
Created on 2016-07-29
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争匹配逻辑
"""

import random
from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy


class BattleMatcher(object):
    """联盟战争匹配逻辑
    """

    def add_condition(self, target_score, invalid_union_id, avoid_union_id):
        self.target_score = target_score
        self.invalid_union_id = invalid_union_id
        self.avoid_union_id = avoid_union_id

        self.candidate = []
        self.avoid_candidate = []
        self.result = None


    def match(self):
        """匹配
        1 筛选所有符合参战条件的联盟
        2 优先匹配联盟匹配隐藏积分相同的队伍
        # 3 优先匹配联盟成员人数接近的联盟
        # 4 优先匹配平均等级接近的联盟
        5 尽量不匹配上次的对手
        """
        proxy = DataProxy()
        proxy.get_all("unionunion", "id")
        defer = proxy.execute()
        defer.addCallback(self._collect)
        return defer


    def _collect(self, pre_proxy):
        """收集信息
        """
        proxy = DataProxy()

        for union in pre_proxy.get_all_result("unionunion"):
            proxy.search("unionseason", union.id)
        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        """匹配计算
        """
        seasons = proxy.get_all_result("unionseason")
        for season in seasons:
            if season.union_id in self.invalid_union_id:
                #不能匹配的联盟
                continue
            elif not season.is_able_to_join_battle:
                #不能参战的联盟
                continue
            elif season.union_id in self.avoid_union_id:
                self.avoid_candidate.append(season)
            else:
                self.candidate.append(season)

        self._choose()
        return self


    def _choose(self):
        """进行选择
        """
        if len(self.candidate) > 0:
            #选择隐藏分分差接近的联盟
            min_gap = abs(self.target_score - self.candidate[-1].match_score)
            for season in self.candidate:
                if abs(season.match_score - self.target_score) <= min_gap:
                    self.result = season
                    min_gap = abs(season.match_score - self.target_score)

        elif len(self.avoid_candidate) > 0:
            random.seed()
            self.result = random.sample(self.avoid_candidate, 1)[0]

        if self.result is None:
            logger.warning("Choose rival union failed")
        else:
            logger.debug("Choose rival union[union_id=%d]" % self.result.union_id)

