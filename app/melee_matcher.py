#coding:utf8
"""
Created on 2016-12-20
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 乱斗场匹配
"""

import math
import random
from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy
from datalib.data_loader import data_loader
from app.data.melee import MeleeInfo
from app.data.rival import RivalInfo
from app.data.node import NodeInfo
from app.data.hero import HeroInfo
from app.data.technology import TechnologyInfo
from app.business import melee as melee_business
from app.core import reward as reward_module
from app.core.rival import PVEEnemyPool
from app.core.name import NameGenerator
from app.core.icon import IconGenerator
import copy


class MeleeMatcher(object):
    """乱斗场查询器(与演武场类似)
    """
    def __init__(self):
        """
        """
        self.rank_base = 0 #本房间演武场第一名在全局数据中的排名
        self.rank = 0
        self.users_count = 0 #本房间的人数


    def query_ranking(self, data, melee):
        """查询自己的排名
        """
        defer = Deferred()
        defer.addCallback(self._get_melee_rank, data, melee)
        defer.addCallback(self._check)
        defer.callback(True)
        return defer


    def match(self, data, melee):
        """匹配对手
        """
        defer = Deferred()
        defer.addCallback(self._get_melee_rank, data, melee)
        defer.addCallback(self._match_melee, data, melee)
        defer.addCallback(self._check)
        defer.callback(True)
        return defer


    def query_melee_users_by_ranking(self, data, melee, count, users):
        """按照排名查询乱斗场，获取对应用户信息
        args:
            users(out: 元组（userid, name, level, icon_id, title_level, score, ranking_index）)
        """
        defer = Deferred()
        defer.addCallback(self._get_melee_rank, data, melee)  #先查自己的排名
        defer.addCallback(self._query_melees_by_ranking, melee, count, users)
        defer.addCallback(self._check)
        defer.callback(True)
        return defer


    def _get_melee_rank(self, status, data, melee):
        """获得玩家乱斗场的排名
        """
        assert status is True

        cache_proxy = DataProxy()
        #查询玩家所在房间的第一名
        (min_score, max_score) = MeleeInfo.get_index_score_range(melee.index)
        cache_proxy.search_by_rank_score(
                "melee", "score", min_score, max_score, 0, 1)
        #查询玩家所在房间人数
        cache_proxy.search_rank_score_count(
                "melee", "score", min_score, max_score)
        defer = cache_proxy.execute()
        defer.addCallback(self._select_melee_rank, data, min_score, max_score)
        return defer


    def _select_melee_rank(self, proxy, data, min_score, max_score):
        #获得本房间第一名的user_id
        arena_list = proxy.get_rank_score_result("melee", "score",
                min_score, max_score, 0, 1)
        assert len(arena_list) == 1
        first_user_id = arena_list[0].user_id
        #房间人数
        self.users_count = proxy.get_rank_score_count("melee", "score",
                min_score, max_score)

        cache_proxy = DataProxy()

        #查询本房间第一名在总榜中的排名
        cache_proxy.search_ranking("melee", "score", first_user_id)
        #查询自己在总榜中的排名
        cache_proxy.search_ranking("melee", "score", data.id)

        defer = cache_proxy.execute()
        defer.addCallback(self._calc_melee_rank, data, first_user_id)
        return defer


    def _calc_melee_rank(self, proxy, data, first_user_id):
        self.rank_base = proxy.get_ranking("melee", "score", first_user_id)
        self_rank = proxy.get_ranking("melee", "score", data.id)
        self.rank = self_rank - self.rank_base + 1
        logger.debug("melee self rank=%d, rank_base=%d" % (self.rank, self.rank_base))
        return True


    def _match_melee(self, status, data, melee):
        """匹配副本对手
        """
        assert status is True

        x = self.rank
        players_rank = []
        #根据规则，挑选出要选作对手的玩家排名
        if x <= 10:
            if x == 1:
                players_rank += random.sample(range(2, x+50), 3)
            elif x == 2:
                players_rank.append(1)
                players_rank += random.sample(range(3, x+50), 2)
            else:
                players_rank += random.sample(range(1, x), 1)
                players_rank += random.sample(range(x, x+50), 2)
        elif x > 10 and x <= 100:
            players_rank += random.sample(range(int(math.ceil(0.5 * x - 5)), x), 1)
            players_rank += random.sample(range(x, x+100), 2)
        elif x > 100 and x <= 1000:
            #players_rank += random.sample(range(int(math.ceil(0.5 * x - 10)), int(math.ceil(0.5 * x + 10))), 1)
            players_rank += random.sample(range(int(math.ceil(0.5 * x - 10)), x), 1)
            #players_rank += random.sample(range(x-30, x), 1)
            players_rank += random.sample(range(x, x+100), 2)
        elif x > 1000:
            #players_rank += random.sample(range(int(math.ceil(0.5 * x - 50)), int(math.ceil(0.5 * x + 50))), 1)
            players_rank += random.sample(range(int(math.ceil(0.5 * x - 50)), x), 1)
            #players_rank += random.sample(range(int(math.ceil(0.9 * x - 100)), x), 1)
            players_rank += random.sample(range(x, x+100), 2)
        assert len(players_rank) == 3
        logger.debug("match players by rank[self_rank=%d][match rank=[%d, %d, %d]" %\
                (x, players_rank[0], players_rank[1], players_rank[2]))

        cache_proxy = DataProxy()
        for rank in players_rank:
            if rank > self.users_count:  #超过本房间人数则跳过
                continue
            cache_proxy.search_by_rank("melee", "score", self.rank_base + rank - 1, self.rank_base + rank - 1)
        defer = cache_proxy.execute()
        defer.addCallback(self._select_players_info, data, melee, players_rank)
        return defer


    def _select_players_info(self, proxy, data, melee, players_rank):
        """查询玩家的主公信息、阵容和战斗科技
        """
        users_id = []
        users_arena = {}
        users_arena_ranking = {}
        for rank in players_rank:
            if rank > self.users_count:  #超过本房间人数则跳过
                continue

            results = proxy.get_rank_result(
                    "melee", "score", self.rank_base + rank - 1, self.rank_base + rank - 1)
            if len(results) == 0:
                continue

            #匹配到玩家自己，舍弃
            if results[0].user_id == data.user.get(True).id:
                continue

            #匹配到积分为0的玩家，舍弃
            if MeleeInfo.get_real_score(results[0].score) == 0:
                continue

            #如果乱斗场阵容不足9个，舍弃
            if len(utils.split_to_int(results[0].heroes_basic_id)) != 9:
                logger.warning("melee heroes_id not correct.[user_id=%d]" % results[0].user_id)
                continue

            #assert len(results) == 1
            user_id = results[0].user_id
            users_id.append(user_id)
            users_arena[user_id] = results[0]
            users_arena_ranking[user_id] = rank

        cache_proxy = DataProxy()
        for user_id in users_id:
            cache_proxy.search("user", user_id)    #查询主公信息
            cache_proxy.search("guard", user_id)    #查阵容
            cache_proxy.search_by_index("technology", "user_id", user_id)    #查战斗科技

        defer = cache_proxy.execute()
        defer.addCallback(self._select_teams, data, melee,
                users_id, users_arena, users_arena_ranking)
        return defer


    def _select_teams(self, proxy, data, melee, users_id, users_arena, users_arena_ranking):
        """查team信息
        """
        cache_proxy = DataProxy()
        users = {}
        users_id_usable = []
        guards = {}
        tech_basic_ids = {}
        heroes_id = {}
        for user_id in users_id:
            user_result = proxy.get_result("user", user_id)
            if not user_result.allow_pvp_arena:
                #若恰好匹配到演武场还未开启的玩家，则跳过
                continue

            guard_result = proxy.get_result("guard", user_id)
            if guard_result is None:
                continue

            users[user_id] = user_result
            users_id_usable.append(user_id)
            guards[user_id] = guard_result    #目前只有一个防守阵容

            results = proxy.get_all_result("technology")
            battle_technologys = []
            for result in results:
                if (result.user_id == user_id and not result.is_upgrade
                        and result.is_battle_technology()):
                    battle_technologys.append(result.basic_id)
            tech_basic_ids[user_id] = battle_technologys

            #heroes_id[user_id] = utils.split_to_int(guards[user_id].teams_hero)
            #for hero_id in heroes_id[user_id]:
            #    if hero_id != 0:
            #        cache_proxy.search("hero", hero_id)

        #设置rival的演武场信息
        rivals = {}
        rivals_id = melee.generate_arena_rivals_id()
        for i in range(len(users_id_usable)):
            user_id = users_id_usable[i]
            rival_id = rivals_id[i]
            rival = data.rival_list.get(rival_id)
            if rival is None:
                rival = RivalInfo.create(rival_id, data.id)
                data.rival_list.add(rival)
            rivals[rival_id] = rival

            user_arena = users_arena[user_id]
            heroes_basic_id = utils.split_to_int(user_arena.heroes_basic_id)
            heroes_id = []
            for basic_id in heroes_basic_id:
                hero_id = HeroInfo.generate_id(user_id, basic_id)
                heroes_id.append(hero_id)
                if hero_id != 0:
                    cache_proxy.search("hero", hero_id)

            battle_score = guards[user_id].get_team_score()
            heroes = utils.join_to_string(heroes_id)
            #计算积分变化
            (self_win_score, self_lose_score) = melee_business.calc_battle_score(
                    melee, MeleeInfo.get_real_score(user_arena.score))
            (rival_win_score, rival_lose_score) = melee_business.calc_battle_score(
                    user_arena, MeleeInfo.get_real_score(melee.score))

            arena_buff_id = user_arena.calc_arena_buff_id(users_arena_ranking[user_id])
            rival.set_melee(user_id, battle_score, heroes,
                    MeleeInfo.get_real_score(user_arena.score),
                    users_arena_ranking[user_id], arena_buff_id,
                    self_win_score, self_lose_score, user_arena.heroes_position)
            logger.debug("melee rival:[user_id=%d][battle_score=%d][heroes=%s][arena_score=%d]"
                    "[arena_ranking=%d][arena_buff_id=%d][self_win_score=%d][self_lose_score=%d]"
                    "[rival_win_score=%d][rival_lose_score=%d]" % (user_id, battle_score, heroes,
                        MeleeInfo.get_real_score(user_arena.score), users_arena_ranking[user_id], arena_buff_id,
                        self_win_score, self_lose_score, rival_win_score, rival_lose_score))

        defer = cache_proxy.execute()
        defer.addCallback(self._set_rivals_info, data, melee, rivals, users,
                heroes_id, tech_basic_ids)
        return defer


    def _set_rivals_info(self, proxy, data, melee, rivals, users, heroes_id, tech_basic_ids):

        rivals_user_id = []
        rivals_battle_score = []
        rivals_score = []
        rivals_info = []
        for i in rivals:
            rival = rivals[i]
            #对手阵容中英雄信息
            rival_heroes = []
            heroes_id = rival.get_heroes_id()
            for hero_id in heroes_id:
                if hero_id == 0:
                    rival_heroes.append(None)
                else:
                    hero = proxy.get_result("hero", hero_id)
                    rival_heroes.append(hero)

            spoils = reward_module.random_pve_spoils(users[rival.rival_id].level)
            rival.set_pvp_enemy_detail(users[rival.rival_id], rival_heroes,
                    items = spoils,
                    technology_basic_ids = tech_basic_ids[rival.rival_id])
            rivals_user_id.append(rival.rival_id)
            rivals_battle_score.append(rival.score)
            rivals_score.append(rival.win_score)
            rivals_info.append(rival)

        #演武场搜出来的对手不足3人，pve补上
        rivals_id = melee.generate_arena_rivals_id()
        pve_user_id = 0    #rival为pve类型的user_id
        for i in range(3 - len(rivals)):
            rival_id = rivals_id[i + len(rivals)]
            rival = data.rival_list.get(rival_id)
            if rival is None:
                rival = RivalInfo.create(rival_id, data.id)
                data.rival_list.add(rival)

            #pve匹配的战力范围
            key = data.user.get(True).level - 4 #演武场需主公17级才开启
            match_info = data_loader.KeyNodeMatchBasicInfo_dict[key]

            rival.set_pve_matching_condition(NodeInfo.ENEMY_TYPE_MELEE,
                    match_info.enemyScoreMin, match_info.enemyScoreMax)

            #创建pve melee数据
            self_score = MeleeInfo.get_real_score(melee.score)
            pve_rival_score = random.randint(int(0.8 * self_score), int(1.2 * self_score)) #pve对手随机积分
            pve_arena = MeleeInfo()
            pve_arena.add_score(pve_rival_score)
            pve_arena.update_index(data.user.get(True).level)
            pve_arena_ranking = 9999 #pve的rival排名随意给个很大的名次
            arena_buff_id = pve_arena.calc_arena_buff_id(pve_arena_ranking)

            #只计算我方积分变化
            (self_win_score, self_lose_score) = melee_business.calc_battle_score(melee, pve_rival_score)
            rival.set_melee(pve_user_id, 0, '', pve_rival_score,
                    pve_arena_ranking, arena_buff_id,
                    self_win_score, self_lose_score, '')
            logger.debug("melee rival(pve):[user_id=%d][arena_score=%d][arena_ranking=%d]"
                    "[arena_buff_id=%d][self_win_score=%d][self_lose_score=%d]"
                    % (pve_user_id, pve_rival_score,
                        pve_arena_ranking, arena_buff_id,
                        self_win_score, self_lose_score))

            self._match_one_pve(rival, pve_user_id)

            rivals_user_id.append(pve_user_id)
            rivals_battle_score.append(rival.score)
            rivals_score.append(rival.win_score)
            rivals_info.append(rival)
            pve_user_id += 1    #若pve有多个，保证user_id不重

        rivals_user_id_origin = copy.copy(rivals_user_id)

        #rivals_user_id按照rivals_score的高低排序
        for i in range(len(rivals_score)):
            for j in range(i + 1, len(rivals_score)):
                if rivals_score[i] < rivals_score[j]:
                    #互换积分
                    tmp1 = rivals_score[j]
                    rivals_score[j] = rivals_score[i]
                    rivals_score[i] = tmp1
                    #互换rival user id
                    tmp2 = rivals_user_id[j]
                    rivals_user_id[j] = rivals_user_id[i]
                    rivals_user_id[i] = tmp2
                    #互换rival battle_score
                    tmp3 = rivals_battle_score[j]
                    rivals_battle_score[j] = rivals_battle_score[i]
                    rivals_battle_score[i] = tmp3

        melee.set_arena_rivals_user_id(rivals_user_id_origin)

        return True


    def _match_one_pve(self, rival, rival_id):
        """根据战力范围，匹配出一个 PVE 敌人
        """
        enemy = PVEEnemyPool().get(rival.score_min, rival.score_max)
        name = NameGenerator().gen() #随机一个名字
        spoils = reward_module.random_pve_spoils(enemy.level)

        icon_id = IconGenerator().gen() #随机生成一个头像
        rival.set_pve_enemy(enemy, name, spoils, rival_id, icon_id)


    def _query_melees_by_ranking(self, status, melee, count, users):
        """按照排名查询乱斗场信息
        """
        assert status is True

        cache_proxy = DataProxy()

         #查询玩家所在房间的前count名
        (min_score, max_score) = MeleeInfo.get_index_score_range(melee.index)
        cache_proxy.search_by_rank_score(
                "melee", "score", min_score, max_score, 0, count)

        defer = cache_proxy.execute()
        defer.addCallback(self._query_users, min_score, max_score, count, users)
        return defer


    def _query_users(self, proxy, min_score, max_score, count, users):
        """
        """
        results = proxy.get_rank_score_result(
                "melee", "score", min_score, max_score, 0, count)

        cache_proxy = DataProxy()
        arena_rankings = {}
        arenas = {}
        for i,value in enumerate(results):
            arena_rankings[value.user_id] = i + 1 #排名
            arenas[value.user_id] = value
            cache_proxy.search("user", value.user_id)

        defer = cache_proxy.execute()
        defer.addCallback(self._get_users, min_score, max_score,
                arenas, arena_rankings, users)
        return defer


    def _get_users(self, proxy, min_score, max_score, arenas, arena_rankings, users):
        """
            users(out: 元组（userid, name, level, icon_id, title_level, score, ranking_index）)
        """
        results = proxy.get_all_result("user")

        for user in results:
            users.append(
                    (user.id, user.get_readable_name(), user.level, user.icon_id,
                        arenas[user.id].title_level,
                        MeleeInfo.get_real_score(arenas[user.id].score),
                        arena_rankings[user.id]))
        return True


    def _check(self, status):
        assert status is True
        return self


