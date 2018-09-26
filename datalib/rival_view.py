#coding:utf8
"""
Created on 2016-05-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 视图：玩家数据
"""

from utils import logger
from datalib.base_view import BaseView
from datalib.data_element import UniqueData
from datalib.data_element import DataSet
from datalib.data_proxy4redis import DataProxy


class RivalView(BaseView):
    """对手信息
    匹配时使用
    """

    __slots__ = [
            "user",             #玩家信息
            "resource",         #玩家资源信息

            "defense",          #城防信息
            "guard_list",       #阵容信息
            "hero_list",        #阵容中的英雄信息
            "technology_list",  #相关科技信息
            ]



class BatchRivalView(BaseView):


    def __init__(self):
        """
        """
        self.rivals = {}


    def get(self, ids):
        """从 cache 中读入对手信息
        Args:
            id[int]: 玩家 id
        """
        self.id = id
        cache_proxy = DataProxy()

        #查询 user, technology, hero, resource, defense 表
        for rival in self._pvp_players:
            cache_proxy.search("user", rival.rival_id)
            cache_proxy.search_by_index("technology", "user_id", rival.rival_id)
            heroes_id = rival.get_heroes_id()
            for hero_id in heroes_id:
                if hero_id != 0:
                    cache_proxy.search("hero", hero_id)
            if rival.is_rob:
                cache_proxy.search("resource", rival.rival_id)
                cache_proxy.search("defense", rival.defense_id)

        defer = cache_proxy.execute()
        return defer


    def _filter_pvp_rival(self, proxy):
        """筛选出合适的对手
        筛选掉不合法的对手（比如重复的对手）
        """
        exit_rivals = []
        for rival in self._pvp_players:
            candidate = []
            guard_list = proxy.get_rank_score_result("guard", "score",
                    rival.score_min, rival.score_max, rival.offset, rival.count)
            for guard in guard_list:
                if guard.user_id not in self._invalid:
                    logger.debug("Candidate[user id=%d]" % guard.user_id)
                    candidate.append(guard)

            #如果可选对手为空，退化为 PVE
            if len(candidate) == 0:
                logger.warning("Bad luck for no candidate[id=%d][%d-%d][%d,%d]" %
                        (rival.id, rival.score_min, rival.score_max,
                            rival.offset, rival.count))
                exit_rivals.append(rival)
                continue

            #随机选择
            random.seed()
            rival_guard = random.sample(candidate, 1)[0]
            rival.set_pvp_enemy_guard(rival_guard)

            self._invalid.append(rival.rival_id) #不能匹配到重复的敌人
            logger.debug("Add invalid user[user id=%d]" % rival.rival_id)

        #退化成 PVE 对手
        for rival in exit_rivals:
            self._pvp_convert_to_pve(rival)

        cache_proxy = DataProxy()

        #查询 user, technology, hero, resource, defense 表
        for rival in self._pvp_players:
            cache_proxy.search("user", rival.rival_id)
            cache_proxy.search_by_index("technology", "user_id", rival.rival_id)
            heroes_id = rival.get_heroes_id()
            for hero_id in heroes_id:
                if hero_id != 0:
                    cache_proxy.search("hero", hero_id)
            if rival.is_rob:
                cache_proxy.search("resource", rival.rival_id)
                cache_proxy.search("defense", rival.defense_id)

        defer = cache_proxy.execute()
        return defer


    def _calc_pvp_rival_info(self, proxy):
        """得到对手的详情
        """
        for rival in self._pvp_players:
            #对手信息
            rival_user = proxy.get_result("user", rival.rival_id)
            technologys = proxy.get_all_result("technology")
            tech_basic_ids = []
            for technology in technologys:
                if (technology.user_id == rival.rival_id and
                        not technology.is_upgrade and technology.is_battle_technology()):
                    tech_basic_ids.append(technology.basic_id)

            #对手阵容中英雄信息
            rival_heroes = []
            heroes_id = rival.get_heroes_id()
            for hero_id in heroes_id:
                if hero_id == 0:
                    rival_heroes.append(None)
                else:
                    hero = proxy.get_result("hero", hero_id)
                    rival_heroes.append(hero)

            if rival.is_rob:
                #计算可以从对手抢夺的资源
                resource = proxy.get_result("resource", rival.rival_id)
                defense = proxy.get_result("defense", rival.defense_id)
                (gain_money, gain_food) = battle_module.calc_attacker_income(
                        self._level, rival_user.level, defense, resource)
                #有可能可能获得一个将魂石
                items = reward_module.random_starsoul_spoils()

                rival.set_pvp_enemy_detail(rival_user, rival_heroes,
                        gain_money, gain_food, items, tech_basic_ids)
            else:
                rival.set_pvp_enemy_detail(rival_user, rival_heroes,
                        technology_basic_ids = tech_basic_ids)

        return True

