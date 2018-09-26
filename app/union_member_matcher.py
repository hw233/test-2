#coding:utf8
"""
Created on 2016-06-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟成员信息匹配逻辑
"""

from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy


class UnionMemberMatcher(object):

    def __init__(self):
        self.ids = []
        self.result = {}


    def add_condition(self, user_id):
        self.ids.append(user_id)


    def match(self):
        """查询玩家信息、战力信息
        """
        proxy = DataProxy()
        for user_id in self.ids:
            proxy.search("user", user_id)
            proxy.search("battle_score", user_id)
            proxy.search("union", user_id)

        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        for user_id in self.ids:
            user = proxy.get_result("user", user_id)
            battle_score = proxy.get_result("battle_score", user_id)
            union = proxy.get_result("union", user_id)

            self.result[user_id] = (
                    user.get_readable_name(),
                    user.level,
                    user.icon_id,
                    user.last_login_time,
                    battle_score.score,
                    union.honor)

        return self


class UnionMemberDetailMatcher(object):

    def match(self, user_id, union_id):
        """查询玩家信息、联盟信息、阵容信息
        """
        self.user_id = user_id
        self.union_id = union_id

        proxy = DataProxy()
        proxy.search("user", self.user_id)
        proxy.search("battle_score", self.user_id)
        proxy.search("union", self.user_id)
        proxy.search_by_index("technology", "user_id", self.user_id)    #查战斗科技
        proxy.search_by_index("team", "user_id", self.user_id)    #查战斗科技

        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, pre_proxy):
        self.user = pre_proxy.get_result("user", self.user_id)
        self.battle_score = pre_proxy.get_result("battle_score", self.user_id)
        self.union = pre_proxy.get_result("union", self.user_id)
        self.technologys = pre_proxy.get_all_result("technology")

        #过滤 team
        teams_id = self.battle_score.get_powerful_teams_id()
        self.teams = []
        teams = pre_proxy.get_all_result("team")
        for team in teams:
            if team.id in teams_id:
                self.teams.append(team)

        #查询 heroes
        heroes_id = []
        for team in self.teams:
            heroes_id.extend(team.get_heroes())

        proxy = DataProxy()
        for hero_id in heroes_id:
            proxy.search("hero", hero_id)

        defer = proxy.execute()
        defer.addCallback(self._calc_detail_result)
        return defer


    def _calc_detail_result(self, proxy):
        heroes = proxy.get_all_result("hero")
        self.heroes = {}
        for hero in heroes:
            self.heroes[hero.basic_id] = hero

        return self


class UnionMemberBattleDetailSearcher(object):

    def search(self, unions):
        """查询联盟战争中的玩家信息
        """
        self.unions = unions

        proxy = DataProxy()
        for union_id in self.unions:
            proxy.search_by_index("unionmember", "union_id", union_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, pre_proxy):
        self.members = {}
        for member in pre_proxy.get_all_result("unionmember"):
            if member.is_join_battle:
                self.members[member.user_id] = member

        proxy = DataProxy()
        for user_id in self.members:
            proxy.search("user", user_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_detail_result)
        return defer


    def _calc_detail_result(self, proxy):
        self.users = {}
        for user in proxy.get_all_result("user"):
            self.users[user.id] = user

        return self


