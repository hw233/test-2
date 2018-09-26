#coding:utf8
"""
Created on 2017-11-24
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : plunder 敌人匹配逻辑
"""
import time
import random
import base64
from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy
from app.data.rival import RivalInfo
from app.data.node import NodeInfo
from app.data.plunder_record import PlunderRecordInfo
from app.core import reward as reward_module
from app.core import battle as battle_module
from app.core.rival import PVEEnemyPool
from app.core.rival import DungeonEnemyPool
from app.core.name import NameGenerator
from app.core.icon import IconGenerator


class PlunderMatcher(object):
    """为节点匹配敌人 PVE/PVP
    """

    def __init__(self, level, invalid):
        """
        """
        self.players = {}
        self._level = level
        self._invalid = invalid
        self._pve_players = []
        self._pvp_players = []
        self._specify_user_id = []


    def add_condition(self, data, plunder):
        """提供匹配条件，发起一次搜索
        """
        rivals_id = plunder.generate_plunder_rivals_id()
        for rival_id in rivals_id:
            rival = data.rival_list.get(rival_id)
            if rival is None:
                rival = RivalInfo.create(rival_id, data.id)
                data.rival_list.add(rival)

            guard = data.guard_list.get_all()[0]
            (score_min, score_max) = (max(500, int(guard.score * 0.7)), max(2000, int(guard.score * 1.1)))
            rival.set_pvp_matching_condition(NodeInfo.ENEMY_TYPE_PVP_CITY,
                    #node.rival_score_min, node.rival_score_max, True)
                    score_min, score_max, True)
            self._pvp_players.append(rival)
            logger.debug("Add pvp city rival match condition[score_min=%d][score_max=%d]"
                   % (score_min, score_max))

            self.players[rival.id] = rival


    def _pvp_convert_to_pve(self, rival):
        """PVP 退化成 PVE
        """
        #敌人类型退化成 PVE 的资源点
        rival.pvp_convert_to_pve(NodeInfo.ENEMY_TYPE_PVE_RESOURCE, self._level)

        self._pve_players.append(rival)
        self._pvp_players.remove(rival)
        logger.debug("Rival become pve[rival id=%d]"
                "[pvp count=%d][pve count=%d]" %
                (rival.id, len(self._pvp_players), len(self._pve_players)))


    def query_specify_user(self, str_list, rival):
        """字符串查询匹配
        """
        proxy = DataProxy()
        proxy.get_all("user", "id")
        defer = proxy.execute()
        defer.addCallback(self._calc_query_specify_user_result, str_list)
        defer.addCallback(self._query_user_info, rival)
        return defer


    def _calc_query_specify_user_result(self, proxy, str_list):
        """匹配计算
        """
        users = proxy.get_all_result("user")
        for user in users:
            if str(user.id) == str_list or user.name == base64.b64encode(str_list):
                self._specify_user_id.append(user.id)

        return self


    def _query_user_info(self, proxy, rival):
        """
        """
        cache_proxy = DataProxy()
        for user_id in self._specify_user_id:

            #查询 user, technology, hero, resource, defense 表
            cache_proxy.search("user", user_id)
            cache_proxy.search("union", user_id)
            #cache_proxy.search_by_index("guard", "user_id", user_id)
            cache_proxy.search("guard", user_id)

        defer = cache_proxy.execute()
        defer.addCallback(self._calc_query_user_info, rival)
        return defer


    def _calc_query_user_info(self, proxy, rival):
        """得到对手的详情
        """
        for user_id in self._specify_user_id:
            user = proxy.get_result("user", user_id)
            union = proxy.get_result("union", user_id)

            rival.rival_id = user_id
            rival.name = user.name
            rival.level = user.level
            rival.icon_id = user.icon_id
            rival.country = user.country
            rival.score = 0
            rival.union_id = union.union_id
            rival.in_protect = user.in_protect
                    
            guards = proxy.get_all_result("guard")
            for guard in guards:
                if guard.user_id == user_id:
                    rival.score = guard.score
                    break

            self.players[rival.id] = rival

        return True


    def match(self, plunder, country, only_pve = False):
        """匹配对手
        Args:
            only_pve[bool]: 只进行 PVE 匹配
        Returns:
            True: 成功
        """
        #所有的 PVP 退化成 PVE
        if only_pve:
            for rival in self._pvp_players:
                self._pvp_convert_to_pve(rival)

        defer = Deferred()
        defer.addCallback(self._match_pvp, country) #先进行 PVP 敌人匹配
        defer.addCallback(self._match_pve, country)
        defer.addCallback(self._check, plunder)
        defer.callback(True)
        return defer


    def match_specify(self, data, plunder, rival_user_id, country):
        """
        """
        rival_id = plunder.generate_specify_rival_id()

        rival = data.rival_list.get(rival_id)
        self.players[rival.id] = rival
        self._pvp_players.append(rival)
       
        cache_proxy = DataProxy()
        cache_proxy.search("guard", rival_user_id)

        defer = cache_proxy.execute()
        defer.addCallback(self._set_pvp_rival_guard, rival_user_id, rival)
        defer.addCallback(self._calc_pvp_rival_info, country)
        return defer


    def _set_pvp_rival_guard(self, proxy, rival_user_id, rival):
        """
        """
        guards = proxy.get_all_result("guard")
        
        rival_guard = None
        for guard in guards:
            if guard.user_id == rival_user_id:
             #一个玩家目前只对应一个guard
                rival_guard = guard
                break
        
        #if rival_guard is None:
        #    rival.clear()  #该玩家不存在或没有guard信息

        rival.set_pvp_enemy_guard(rival_guard)
        if rival_guard == None:
            rival.rival_id = rival_user_id
        rival.is_rob = True

        cache_proxy = DataProxy()
        #查询 user, technology, hero, resource, defense 表
        cache_proxy.search("user", rival.rival_id)
        cache_proxy.search("union", rival.rival_id)
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


    def _match_pvp(self, status, country):
        """匹配 pvp 对手
        """
        assert status is True
        if len(self._pvp_players) <= 0:
            return True

        cache_proxy = DataProxy()

        #查询战力范围内的玩家数量
        for rival in self._pvp_players:
            logger.debug("Match PVP[rival id=%d]" % rival.id)
            cache_proxy.search_rank_score_count(
                    "guard", "score", rival.score_min, rival.score_max)

        defer = cache_proxy.execute()
        defer.addCallback(self._pre_select_pvp_rival)
        defer.addCallback(self._filter_pvp_rival)
        defer.addCallback(self._calc_pvp_rival_info, country)
        return defer


    def _pre_select_pvp_rival(self, proxy):
        """初步选择对手
        在可选区间内，初步随机选择 X 名对手
        通常情况下，X > 1，为了避免选择到的对手不合适而需要重新请求
        Args:
            proxy[DataProxy]
        """
        cache_proxy = DataProxy()

        exit_rivals = []
        least_count = 3 #初步选择3人
        for rival in self._pvp_players:
            total_count = proxy.get_rank_score_count(
                    "guard", "score", rival.score_min, rival.score_max)

            if total_count <= 0:
                #对应的区间范围内无合适的 PVP 对手，退化为 PVE
                logger.warning("Invalid rival score range[id=%d][%d-%d]" %
                        (rival.id, rival.score_min, rival.score_max))
                exit_rivals.append(rival)

            random.seed()
            count = min(least_count, total_count)
            offset = random.randint(0, total_count - count)
            rival.set_pvp_filter_range(offset, count)
            cache_proxy.search_by_rank_score("guard", "score",
                    rival.score_min, rival.score_max, rival.offset, rival.count)

        #退化成 PVE 对手
        for rival in exit_rivals:
            self._pvp_convert_to_pve(rival)

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
            cache_proxy.search("union", rival.rival_id)
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


    def _calc_pvp_rival_info(self, proxy, country):
        """得到对手的详情
        """
        for rival in self._pvp_players:
            #对手信息
            rival_user = proxy.get_result("user", rival.rival_id)
            rival_user_union = proxy.get_result("union", rival.rival_id)
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

                #获得特殊物品：将军令
                if rival.country != country:
                    items_country = reward_module.random_country_spoils()
                    items.extend(items_country)

                rival.set_pvp_enemy_detail(rival_user, rival_heroes,
                        gain_money, gain_food, items, tech_basic_ids)
            else:
                rival.set_pvp_enemy_detail(rival_user, rival_heroes,
                        technology_basic_ids = tech_basic_ids)

            if rival_user_union is None:
                rival_union_id = 0
            else:
                rival_union_id = rival_user_union.union_id
            rival.set_plunder(rival_union_id, rival_user.in_protect)

        return True


    def _match_pve(self, status, country):
        """匹配 pve 对手
        需要放在匹配 pvp 对手后执行，因为 pvp 匹配可能退化为 pve 匹配
        """
        assert status is True
        if len(self._pve_players) <= 0:
            return True

        rival_id = 1
        for rival in self._pve_players:
            logger.debug("Match PVE[rival id=%d]" % rival.id)
            self._match_one_pve(rival, rival_id, country)
            rival_id += 1
        return True


    def _match_one_pve(self, rival, rival_id, country):
        """根据战力范围，匹配出一个 PVE 敌人
        """
        enemy = PVEEnemyPool().get(rival.score_min, rival.score_max)
        name = NameGenerator().gen() #随机一个名字
        icon = IconGenerator().gen() #随机一个icon
        spoils = reward_module.random_pve_spoils(enemy.level)

        rival_country = rival_id % 3 + 1
        #获得特殊物品：将军令
        if rival_country != country:
            items_country = reward_module.random_country_spoils()
            spoils.extend(items_country)
        rival.set_pve_enemy(enemy, name, spoils, rival_id, icon, rival_country)


    def _check(self, status, plunder):
        assert status is True

        rivals_user_id = []
        for id in self.players:
            rivals_user_id.append(self.players[id].rival_id)
            
        plunder.set_plunder_rivals_user_id(rivals_user_id)

        return self



