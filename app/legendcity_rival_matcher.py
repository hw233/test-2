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
from app.data.rival import RivalInfo
from app.data.legendcity import LegendCityInfo
from app.core.rival import PVEEnemyPool
from app.core.name import NameGenerator
from app.core.icon import IconGenerator


class LegendCityRivalMatcher(object):
    """史实城对手信息查询
    根据 city_id, user_id 查询玩家的史实城战斗信息
    """
    def __init__(self):
        self.player = None
        self.now = None
        self.position_level = 0


    def match(self, data, city_id, rival_id, is_robot, position_level, now):
        """进行匹配
        """
        legendcity = data.legendcity_list.get(LegendCityInfo.generate_id(data.id, city_id))
        rival = data.rival_list.get(legendcity.node_id)
        if rival is None:
            logger.debug("Create rival for legendcity[rival_id=%d]" % legendcity.node_id)
            rival = RivalInfo.create(legendcity.node_id, data.id)
            data.rival_list.add(rival)
        self.player = rival
        self.now = now
        self.position_level = position_level

        if is_robot:
            return self._match_robot(city_id, rival_id)
        else:
            return self._match_user(city_id, rival_id)


    def _match_robot(self, city_id, rival_id):
        """查找假玩家（机器人）的信息
        """
        enemy = PVEEnemyPool().get_by_id(rival_id)
        name = NameGenerator().gen_by_id(rival_id)
        icon = IconGenerator().gen_by_id(rival_id)
        self.player.set_pve_enemy(enemy, name, [], rival_id, icon)
        self.player.set_legendcity_detail(rival_id, [], self.position_level)

        defer = Deferred()
        defer.callback(self)
        return defer


    def _match_user(self, city_id, rival_id):
        """查找真实玩家的信息
        """
        #查询 rival 信息
        proxy = DataProxy()
        proxy.search("user", rival_id)
        proxy.search("guard", rival_id)
        proxy.search("legendcity", LegendCityInfo.generate_id(rival_id, city_id))
        proxy.search_by_index("technology", "user_id", rival_id)
        proxy.search_by_index("hero", "user_id", rival_id)

        defer = proxy.execute()
        defer.addCallback(self._calc_result, rival_id, city_id)
        return defer


    def _calc_result(self, proxy, rival_id, city_id):
        guard = proxy.get_result("guard", rival_id)
        user = proxy.get_result("user", rival_id)
        legendcity = proxy.get_result(
                "legendcity", LegendCityInfo.generate_id(rival_id, city_id))
        technology_list = proxy.get_all_result("technology")
        hero_list = proxy.get_all_result("hero")

        #防守阵容
        self.player.set_pvp_enemy_guard(guard)
        rival_heroes = []
        heroes_id = self.player.get_heroes_id()
        for hero_id in heroes_id:
            for hero in hero_list:
                if hero.id == hero_id:
                    rival_heroes.append(hero)
                    break 

        #战斗科技
        tech_basic_ids = []
        for technology in technology_list:
            if not technology.is_upgrade and technology.is_battle_technology():
                tech_basic_ids.append(technology.basic_id)
        self.player.set_pvp_enemy_detail(
                user, rival_heroes, technology_basic_ids = tech_basic_ids)

        #史实城信息
        buffs = legendcity.get_buffs(self.now)
        self.player.set_legendcity_detail(rival_id, buffs, self.position_level)
        return self


