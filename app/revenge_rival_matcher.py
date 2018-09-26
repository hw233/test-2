#coding:utf8
"""
Created on 2015-10-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 复仇敌人匹配逻辑
"""
from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy
from app.data.node import NodeInfo
from app.data.rival import RivalInfo
from app.core import reward as reward_module
from app.core import battle as battle_module


class RevengeRivalMatcher(object):
    """查询复仇的敌人信息
    根据 user id，查询敌人最新的情况
    """
    def __init__(self):
        self.player = None


    def search(self, data, rival_user_id):
        """查询对手信息
        Args:
            rival_user_id[int]: 对手 user id
        """
        user = data.user.get(True)
        self._level = user.level

        rival_id = RivalInfo.generate_revenge_id(data.id)
        rival = data.rival_list.get(rival_id)
        if rival is None:
            rival = RivalInfo.create(rival_id, data.id)
            data.rival_list.add(rival)

        rival.set_pvp_matching_condition(NodeInfo.ENEMY_TYPE_PVP_CITY, 0, 0, True)
        self.player = rival

        defer = Deferred()
        defer.addCallback(self._search_rival, self.player)
        defer.addCallback(self._check)
        defer.callback(rival_user_id)
        return defer


    def _search_rival(self, rival_user_id, rival):
        """查询 pvp 对手
        """
        cache_proxy = DataProxy()
        cache_proxy.search("guard", rival_user_id)

        defer = cache_proxy.execute()
        defer.addCallback(self._search_rival_detail, rival_user_id, rival)
        defer.addCallback(self._parse_rival, rival_user_id, rival)
        return defer


    def _search_rival_detail(self, proxy, rival_user_id, rival):
        """查询 pvp 对手详细信息
        """
        rival_guard = proxy.get_result("guard", rival_user_id)
        rival.set_pvp_enemy_guard(rival_guard)

        #查询 user, hero, resource, defense 表
        cache_proxy = DataProxy()
        cache_proxy.search("user", rival.rival_id)
        cache_proxy.search_by_index("technology", "user_id", rival.rival_id)
        heroes_id = rival.get_heroes_id()
        for hero_id in heroes_id:
            if hero_id != 0:
                cache_proxy.search("hero", hero_id)
        cache_proxy.search("resource", rival.rival_id)
        cache_proxy.search("defense", rival.defense_id)

        defer = cache_proxy.execute()
        return defer


    def _parse_rival(self, proxy, rival_user_id, rival):
        """得到对手的阵容
        """
        rival_user = proxy.get_result("user", rival.rival_id)
        technologys = proxy.get_all_result("technology")
        tech_basic_ids = []
        for technology in technologys:
            if not technology.is_upgrade and technology.is_battle_technology():
                tech_basic_ids.append(technology.basic_id)
        rival_heroes = []
        heroes_id = rival.get_heroes_id()
        for hero_id in heroes_id:
            if hero_id == 0:
                rival_heroes.append(None)
            else:
                hero = proxy.get_result("hero", hero_id)
                rival_heroes.append(hero)

        #计算可以从对手抢夺的资源
        resource = proxy.get_result("resource", rival.rival_id)
        defense = proxy.get_result("defense", rival.defense_id)
        (gain_money, gain_food) = battle_module.calc_attacker_income(
                self._level, rival_user.level, defense, resource)

        #有可能可能获得一个将魂石
        items = reward_module.random_starsoul_spoils()

        rival.set_pvp_enemy_detail(rival_user, rival_heroes, gain_money, gain_food,
                items, tech_basic_ids)
        return True


    def _check(self, status):
        assert status is True
        return self

