#coding:utf8
"""
Created on 2016-07-30
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟赛季排名查询
"""

from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy
from datalib.data_loader import data_loader


class SeasonRankingSearcher(object):
    """联盟赛季积分排名查询
    """
    def __init__(self):
        self.union_id = 0
        self.user_id = 0
        self.union_ranking = 0
        self.individual_ranking = 0


    def get_ranking(self, union_id, user_id):
        """查询联盟赛季排名
        """
        self.union_id = union_id
        self.user_id = user_id

        proxy = DataProxy()
        proxy.search_ranking("unionseason", "score", union_id)
        proxy.search_ranking("union", "season_score", user_id)
        proxy.execute(asyn = False)
        self.union_ranking = proxy.get_ranking("unionseason", "score", union_id)
        self.individual_ranking = proxy.get_ranking(
                "union", "season_score", user_id)

        print self.union_ranking
        print self.individual_ranking
        return (self.union_ranking, self.individual_ranking)


