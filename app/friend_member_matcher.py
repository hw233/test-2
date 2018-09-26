#coding:utf8
"""
Created on 2016-06-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 好友成员信息匹配逻辑
"""

from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy


class FriendMemberMatcher(object):

    def __init__(self):
        self.ids = []
        self.result = {}
        #self.user_id = 0


    def add_condition(self, user_id):
        self.ids.append(user_id)


    def match(self):
        """查询玩家信息、战力信息
        """
        #self.user_id = user_id
        proxy = DataProxy()
        for user_id in self.ids:
            proxy.search("user", user_id)
            proxy.search("battle_score", user_id)

        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        for user_id in self.ids:
            user = proxy.get_result("user", user_id)
            battle_score = proxy.get_result("battle_score", user_id)
            user_apply = utils.split_to_int(user.friends_apply)
          #  if self.user_id in user_apply:
          #      continue
            self.result[user_id] = (
                    user.id,
                    user.get_readable_name(),
                    user.icon_id,
                    user.level,
                    battle_score.score)

        return self


#

