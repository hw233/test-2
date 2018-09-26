#coding:utf8
"""
Created on 2016-05-18
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 玩家信息匹配逻辑
"""

from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy
from app.data.user import UserInfo
from app.data.legendcity import LegendCityInfo
from app.core.rival import PVEEnemyPool
from app.core.name import NameGenerator
from app.core.icon import IconGenerator


class UserMatcher(object):
    """根据 user id 查询玩家的基本信息
    名称、等级、icon
    """

    def __init__(self):
        self.ids = []
        self.users = {}


    def add_condition(self, id, is_robot = False):
        """提供匹配条件
        """
        if is_robot:
            enemy = PVEEnemyPool().get_by_id(id)
            name = NameGenerator().gen_by_id(id)
            icon = IconGenerator().gen_by_id(id)
            user = UserInfo(id, level = enemy.level)
            user.change_name(name)
            user.change_icon(icon)
            self.users[id] = user
        else:
            self.ids.append(id)


    def match(self):
        """进行匹配
        """
        proxy = DataProxy()

        for user_id in self.ids:
            proxy.search("user", user_id)

        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        for user_id in self.ids:
            user = proxy.get_result("user", user_id)
            self.users[user_id] = user

        return self.users


class UserMatcherWithBattle(object):
    """带战力的"""

    def __init__(self):
        self.ids = []
        self.results = {}
    
    def add_condition(self, id, is_robot = False):
        """提供匹配条件
        """
        if is_robot:
            enemy = PVEEnemyPool().get_by_id(id)
            name = NameGenerator().gen_by_id(id)
            icon = IconGenerator().gen_by_id(id)
            
            result = {}
            result['id'] = id
            result['level'] = enemy.level
            result['name'] = name
            result['icon_id'] = icon
            result['battle_score'] = enemy.score
            self.results[id] = result
        else:
            self.ids.append(id)

    def match(self):
        """进行匹配
        """
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
            result = {}
            result['id'] = user_id
            result['level'] = user.level
            result['name'] = user.get_readable_name()
            result['icon_id'] = user.icon_id
            result['battle_score'] = battle_score.score

            self.results[user_id] = result

        return self.results
