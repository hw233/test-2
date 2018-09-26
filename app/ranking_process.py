#coding:utf8
"""
Created on 2015-05-29
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief:  排行榜功能
"""

import time
import random
import math
from utils import logger
from utils import utils
from utils.timer import Timer
from proto import ranking_pb2
from proto import internal_pb2
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy
from datalib.global_data import DataBase
from app import pack
from app.user_matcher import UserMatcherWithBattle
from app import log_formater
from app.business import transfer as transfer_business
from app.data.arena import ArenaInfo
from app.data.melee import MeleeInfo
from app.data.trainer import TrainerInfo
from app.core.rival import PVEEnemyPool
from firefly.server.globalobject import GlobalObject


OFFICIAL_POSITION_COUNT = 45    #每个房间查询的官职个数
MELEE_COUNT = 45          #每个房间查询的乱斗场玩家个数

class RankingProcessor(object):

    def query_ranking(self, user_id, request):
        timer = Timer(user_id)

        req = ranking_pb2.QueryRankingReq()
        req.ParseFromString(request)
        if req.type == ranking_pb2.QueryRankingReq.BATTLE_SCORE:
            return self._query_battle_score_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.KILL_ENEMY:
            return self._query_kill_enemy_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.OFFICIAL_POSITION:
            return self._query_official_position_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.ACTIVITY_HERO:
            return self._query_activity_hero_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.UNION_SEASON_BATTLE:
            return self._query_union_season_battle_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.UNION_SEASON_BATTLE_INDIVIDUALS:
            return self._query_union_season_battle_individual_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.ANNEAL_HARD_MODE:
            return self._query_anneal_hard_mode_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.WORLD_BOSS:
            return self._query_worldboss_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.MELEE_ARENA:
            return self._query_melee_ranking(user_id, req, timer)
        elif req.type == ranking_pb2.QueryRankingReq.TRANSFER_ARENA:
            return self._query_transfer_arena(user_id, req, timer)

    def _query_battle_score_ranking(self, user_id, req, timer):
        if req.start_index < 1 or req.start_index > req.end_index:
            raise Exception("Ranking req error")

        proxy = DataProxy()

        proxy.search("battle_score", user_id)  #先查玩家自己的battle score
        proxy.search_ranking("battle_score", "score", user_id)  #先查玩家自己的排名
        proxy.search_by_rank("battle_score", "score", req.start_index - 1, req.end_index - 1)
        defer = proxy.execute()

        defer.addCallback(self._calc_query_battle_score_ranking, user_id, req, timer)
        defer.addErrback(self._query_battle_score_ranking_failed, req, timer)
        return defer


    def _calc_query_battle_score_ranking(self, proxy, user_id, req, timer):
        self_battlescore = proxy.get_result("battle_score", user_id).score
        self_ranking = proxy.get_ranking("battle_score", "score", user_id) + 1
        results = proxy.get_rank_result(
                "battle_score", "score", req.start_index - 1, req.end_index - 1)

        proxy = DataProxy()
        player_scores = {}
        player_rankings = {}
        for i,value in enumerate(results):
            player_scores[value.user_id] = value
            player_rankings[value.user_id] = i
            proxy.search("user", value.user_id)
        proxy.search("user", user_id)   #再查一下玩家自己

        defer = proxy.execute()
        defer.addCallback(self._query_battle_score_ranking_succeed, user_id, req,
                self_ranking, self_battlescore, player_scores, player_rankings, timer)
        return defer


    def _query_battle_score_ranking_succeed(self, proxy, user_id, req,
            self_ranking, self_battlescore, player_scores, player_rankings, timer):
        users = proxy.get_all_result("user")
        if len(users) != len(player_scores) and len(users) != (len(player_scores) + 1):
            raise Exception("Ranking players num error")
        logger.debug('len users [%d]' % len(users))

        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for i, user in enumerate(users):
            if user.id == user_id:
                pack.pack_ranking_info_of_user(
                        user, self_battlescore, self_ranking, res.rankings.add())
            else:
                pack.pack_ranking_info_of_user(
                        user,
                        player_scores[user.id].score,
                        player_rankings[user.id] + 1,
                        res.rankings.add())

        response = res.SerializeToString()
        log = log_formater.output2(user_id, "Query battle score ranking succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_battle_score_ranking_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query battle score ranking failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query battle score ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def _query_kill_enemy_ranking(self, user_id, req, timer):
        if req.start_index < 1 or req.start_index > req.end_index:
            raise Exception("Ranking req error")

        proxy = DataProxy()

        proxy.search("trainer", user_id)  #先查玩家自己的battle
        proxy.search_ranking("trainer", "kills", user_id)   #先查玩家自己的排名
        proxy.search_by_rank("trainer", "kills", req.start_index - 1, req.end_index - 1)
        defer = proxy.execute()

        defer.addCallback(self._calc_query_kill_enemy_ranking, user_id, req, timer)
        defer.addErrback(self._query_kill_enemy_ranking_failed, user_id, req, timer)
        return defer


    def _calc_query_kill_enemy_ranking(self, proxy, user_id, req, timer):
        self_kills = proxy.get_result("trainer", user_id).kills
        self_ranking = proxy.get_ranking("trainer", "kills", user_id) + 1
        results = proxy.get_rank_result(
                "trainer", "kills", req.start_index - 1, req.end_index - 1)

        proxy = DataProxy()
        player_kill_enemys = {}
        player_rankings = {}
        for i,value in enumerate(results):
            player_kill_enemys[value.user_id] = value
            player_rankings[value.user_id] = i
            proxy.search("user", value.user_id)
        proxy.search("user", user_id)   #再查一下玩家自己

        defer = proxy.execute()
        defer.addCallback(self._query_kill_enemy_ranking_succeed, user_id, req, self_ranking,
                self_kills, player_kill_enemys, player_rankings, timer)
        return defer


    def _query_kill_enemy_ranking_succeed(self, proxy, user_id, req,
            self_ranking, self_kills, player_kill_enemys, player_rankings, timer):
        users = proxy.get_all_result("user")
        if len(users) != len(player_kill_enemys) and len(users) != (len(player_kill_enemys) + 1):
            raise Exception("Ranking players num error")
        logger.debug('len users [%d]' % len(users))

        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for i, user in enumerate(users):
            if user.id == user_id:
                pack.pack_ranking_info_of_user(
                        user, self_kills, self_ranking, res.rankings.add())
            else:
                pack.pack_ranking_info_of_user(
                        user,
                        player_kill_enemys[user.id].kills,
                        player_rankings[user.id] + 1,
                        res.rankings.add())

        response = res.SerializeToString()
        log = log_formater.output2(user_id, "Query kill enemy ranking succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_kill_enemy_ranking_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query kill enemy ranking failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query kill enemy ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def _query_official_position_ranking(self, user_id, req, timer):

        cache_proxy = DataProxy()

        cache_proxy.search("arena", user_id)  #先查玩家自己的arena

        #拿到房间的积分范围
        scores_range = []
        range = ArenaInfo.get_index_score_range(ArenaInfo.ARENA_INDEX)
        scores_range.append(range)

        for range in scores_range:
            cache_proxy.search_by_rank_score(
                    "arena", "score", range[0], range[1], 0, OFFICIAL_POSITION_COUNT)

        defer = cache_proxy.execute()
        defer.addCallback(self._calc_query_official_position_ranking,
                user_id, scores_range, req, timer)
        return defer


    def _calc_query_official_position_ranking(self, proxy, user_id, scores_range, req, timer):
        cache_proxy = DataProxy()

        self_arena = proxy.get_result("arena", user_id)
        cache_proxy.search("user", user_id)

        all_arenas = {}
        all_arenas_rank = {}
        player_rankings = {}
        for range in scores_range:
            arena_list = proxy.get_rank_score_result(
                    "arena", "score", range[0], range[1], 0, OFFICIAL_POSITION_COUNT)

            #按照积分先排序
            arena_list.sort(lambda x,y:cmp(ArenaInfo.get_real_score(x.score),
                ArenaInfo.get_real_score(y.score)), reverse = True)

            arena_rank = 1
            for arena in arena_list:
                all_arenas[arena.user_id] = arena
                all_arenas_rank[arena.user_id] = arena_rank
                arena_rank = arena_rank + 1
                cache_proxy.search("user", arena.user_id)

        defer = cache_proxy.execute()
        defer.addCallback(self._query_official_position_ranking_succeed, user_id,
                self_arena, all_arenas, all_arenas_rank, req, timer)
        return defer


    def _query_official_position_ranking_succeed(self, proxy, user_id,
            self_arena, all_arenas, all_arenas_rank, req, timer):

        users = proxy.get_all_result("user")

        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for i, user in enumerate(users):
            #官职榜不用ranking值
            if user.id == user_id:
                if user.id not in all_arenas_rank:
                    pack.pack_ranking_info_of_user(
                            user,
                            self_arena.calc_arena_title_level(0),
                            0,
                            res.rankings.add())
                else:
                    pack.pack_ranking_info_of_user(
                            user,
                            self_arena.calc_arena_title_level(all_arenas_rank[user.id]),
                            0,
                            res.rankings.add())
            else:
                pack.pack_ranking_info_of_user(
                        user,
                        all_arenas[user.id].calc_arena_title_level(all_arenas_rank[user.id]),
                        0,
                        res.rankings.add())

        response = res.SerializeToString()
        log = log_formater.output2(user_id, "Query official position ranking succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_official_position_ranking_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query official position ranking failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query official position ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def _query_activity_hero_ranking(self, user_id, req, timer):
        if req.start_index < 1 or req.start_index > req.end_index:
            raise Exception("Ranking req error")

        proxy = DataProxy()

        proxy.search("draw", user_id)  #先查玩家自己的draw
        proxy.search_ranking("draw", "activity_scores", user_id)   #先查玩家自己的排名
        proxy.search_by_rank("draw", "activity_scores", req.start_index - 1, req.end_index - 1)
        defer = proxy.execute()

        defer.addCallback(self._calc_query_activity_hero_ranking, user_id, req, timer)
        defer.addErrback(self._query_activity_hero_ranking_failed, req, timer)
        return defer


    def _calc_query_activity_hero_ranking(self, proxy, user_id, req, timer):
        self_score = proxy.get_result("draw", user_id).activity_scores
        self_ranking = proxy.get_ranking("draw", "activity_scores", user_id) + 1
        results = proxy.get_rank_result(
                "draw", "activity_scores", req.start_index - 1, req.end_index - 1)

        proxy = DataProxy()
        players = {}
        players_ranking = {}
        for i,value in enumerate(results):
            players[value.user_id] = value
            players_ranking[value.user_id] = i
            proxy.search("user", value.user_id)
        proxy.search("user", user_id)   #再查一下玩家自己

        #players的积分排名，需要保证积分相同时，后达到积分的人排名在后面
        for (k,v) in players.items():
            k_draw_last_time = v.last_gold_draw_time
            k_score = v.activity_scores
            k_ranking = players_ranking[k]

            for (k1,v1) in players.items():
                if k == k1:
                    continue

                k1_draw_last_time = v1.last_gold_draw_time
                k1_score = v1.activity_scores
                k1_ranking = players_ranking[k1]
                if (k_score == k1_score and k_draw_last_time < k1_draw_last_time
                        and k_ranking > k1_ranking):
                    #互换排名
                    players_ranking[k] = k1_ranking
                    players_ranking[k1] = k_ranking

                    k_ranking = k1_ranking

        if user_id in players_ranking:
            self_ranking = players_ranking[user_id] + 1

        defer = proxy.execute()
        defer.addCallback(self._query_activity_hero_ranking_succeed, user_id, req, self_ranking,
                self_score, players, players_ranking, timer)
        return defer


    def _query_activity_hero_ranking_succeed(self, proxy, user_id, req,
            self_ranking, self_score, players, players_ranking, timer):
        users = proxy.get_all_result("user")
        if len(users) != len(players) and len(users) != (len(players) + 1):
            raise Exception("Ranking players num error")
        logger.debug('len users [%d]' % len(users))

        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for i, user in enumerate(users):
            if user.id == user_id:
                pack.pack_ranking_info_of_user(
                        user, self_score, self_ranking, res.rankings.add())
            else:
                pack.pack_ranking_info_of_user(
                        user,
                        players[user.id].activity_scores,
                        players_ranking[user.id] + 1,
                        res.rankings.add())

        response = res.SerializeToString()
        log = log_formater.output2(user_id, "Query activity hero ranking succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_activity_hero_ranking_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query activity hero ranking failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query activity hero ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def query_ranking_player_powerful_teams(self, user_id, request):
        timer = Timer(user_id)

        req = ranking_pb2.QueryRankingPlayerPowerfulTeamsReq()
        req.ParseFromString(request)

        proxy = DataProxy()

        proxy.search("battle_score", req.target_user_id)    #查询目标玩家的排名信息
        proxy.search_by_index("technology", "user_id", req.target_user_id)    #查战斗科技
        defer = proxy.execute()

        defer.addCallback(self._calc_query_ranking_player_powerful_teams, req, timer)
        defer.addErrback(self._query_ranking_player_powerful_teams_failed, req, timer)
        return defer


    def _calc_query_ranking_player_powerful_teams(self, proxy, req, timer):
        battle_score = proxy.get_result("battle_score", req.target_user_id)
        if battle_score == None:
            #如果为None,则认为它是机器人,尝试在PVE表中查找
            return self._query_ranking_player_from_pve(req, timer)

        teams_id = battle_score.get_powerful_teams_id()[0:3] #取前三队

        technologys = proxy.get_all_result("technology")
        technology_basic_ids = []
        for technology in technologys:
            if not technology.is_upgrade and technology.is_battle_technology():
                technology_basic_ids.append(technology.basic_id)

        proxy = DataProxy()
        for team_id in teams_id:
            proxy.search("team", team_id)

        defer = proxy.execute()
        defer.addCallback(self._query_player_powerful_team_heroes,
                technology_basic_ids, req, timer, teams_id)
        return defer


    def _query_player_powerful_team_heroes(self, proxy, technology_basic_ids,
            req, timer, teams_id):
        teams = proxy.get_all_result("team")

        proxy = DataProxy()
        for team in teams:
            for hero_id in team.get_heroes():
                if hero_id == 0:
                    continue
                else:
                    proxy.search("hero", hero_id)

        defer = proxy.execute()
        defer.addCallback(self._query_ranking_player_powerful_teams_succeed,
                technology_basic_ids, req, timer, teams)
        return defer


    def _query_ranking_player_powerful_teams_succeed(self, proxy, technology_basic_ids,
            req, timer, teams):
        heroes = proxy.get_all_result("hero")

        res = ranking_pb2.QueryRankingPlayerPowerfulTeamsRes()
        res.status = 0

        i = 0
        for team in teams:
            team_res = res.teams.add()
            pack.pack_team_info(team, team_res)
            team_res.index = i
            i += 1
            for team_hero_res in team_res.heroes:
                if team_hero_res.basic_id == 0:
                    continue

                for hero in heroes:
                    if hero.basic_id == team_hero_res.basic_id:
                        pack.pack_hero_info(hero, team_hero_res, timer.now)

        for basic_id in technology_basic_ids:
            res.battle_tech_ids.append(basic_id)

        response = res.SerializeToString()
        log = log_formater.output2(req.user_id, "Query ranking player powerful teams succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_ranking_player_powerful_teams_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query ranking player powerful teams failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingPlayerPowerfulTeamsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query ranking player powerful teams failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def _query_union_season_battle_ranking(self, user_id, req, timer):
        """查询联盟赛季中联盟积分排名
        """

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_union_season_battle, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_union_season_battle(self, data, req, timer):
        if req.start_index < 1 or req.start_index > req.end_index:
            raise Exception("Ranking req error")

        union = data.union.get(True)

        proxy = DataProxy()
        if union.is_belong_to_union():
            proxy.search_ranking("unionseason", "score", union.union_id)
            proxy.search("unionseason", union.union_id)
        proxy.search_by_rank("unionseason", "score", req.start_index - 1, req.end_index - 1)
        defer = proxy.execute()

        defer.addCallback(self._calc_union_season_battle_post, data, req, timer)
        defer.addCallback(self._query_succeed, req, timer)
        return defer


    def _calc_union_season_battle_post(self, pre_proxy, data, req, timer):
        union = data.union.get(True)

        rankings = {}

        #获得己方联盟的排名
        if union.is_belong_to_union():
            own_ranking = pre_proxy.get_ranking("unionseason", "score", union.union_id)
            own_season = pre_proxy.get_result("unionseason", union.union_id)
            rankings[own_ranking] = own_season

        results = pre_proxy.get_rank_result(
                "unionseason", "score", req.start_index - 1, req.end_index - 1)
        for i, season in enumerate(results):
            rankings[i] = season

        #查询联盟信息
        proxy = DataProxy()
        for index in rankings:
            proxy.search("unionunion", rankings[index].union_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_union_season_battle_result, rankings, data, req, timer)
        return defer


    def _calc_union_season_battle_result(self, proxy, rankings, data, req, timer):
        unions = {}
        for union in proxy.get_all_result("unionunion"):
            unions[union.id] = union

        res = ranking_pb2.QueryRankingRes()
        res.status = 0
        for ranking in rankings:
            season = rankings[ranking]
            union = unions[season.union_id]
            pack.pack_ranking_info_of_union(
                    union, season.score, ranking + 1, res.rankings.add())

        return res


    def _query_succeed(self, res, req, timer):
        response = res.SerializeToString()
        logger.notice("Query ranking succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query ranking failed[reason=%s]" % err)
        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_union_season_battle_individual_ranking(self, user_id, req, timer):
        """查询联盟赛季中个人战功排名
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_union_season_battle_individual, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_union_season_battle_individual(self, data, req, timer):
        if req.start_index < 1 or req.start_index > req.end_index:
            raise Exception("Ranking req error")

        req.end_index = 50#TODO 客户端赋值错误，临时方案，待客户端修复
        proxy = DataProxy()
        proxy.search_ranking("union", "season_score", data.id)
        proxy.search_by_rank("union", "season_score", req.start_index - 1, min(20, req.end_index - 1))
        defer = proxy.execute()

        defer.addCallback(self._calc_union_season_battle_individual_post, data, req, timer)
        defer.addCallback(self._query_succeed, req, timer)
        return defer


    def _calc_union_season_battle_individual_post(self, pre_proxy, data, req, timer):
        #获得自己的排名
        own_ranking = pre_proxy.get_ranking("union", "season_score", data.id)

        rankings = {}
        rankings[own_ranking] = data.union.get(True)
        results = pre_proxy.get_rank_result(
                "union", "season_score", req.start_index - 1, min(20, req.end_index - 1))
        for i, union in enumerate(results):
            rankings[i] = union

        #查询玩家信息
        proxy = DataProxy()
        for index in rankings:
            proxy.search("user", rankings[index].user_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_union_season_battle_individual_result,
                rankings, data, req, timer)
        return defer


    def _calc_union_season_battle_individual_result(self, proxy, rankings, data, req, timer):
        users = {}
        for user in proxy.get_all_result("user"):
            users[user.id] = user

        res = ranking_pb2.QueryRankingRes()
        res.status = 0
        for ranking in rankings:
            union = rankings[ranking]
            user = users[union.user_id]
            pack.pack_ranking_info_of_user(
                    user, union.season_score, ranking + 1, res.rankings.add())

        return res


    def _query_anneal_hard_mode_ranking(self, user_id, req, timer):
        if req.start_index < 1 or req.start_index > req.end_index:
            raise Exception("Ranking req error")

        proxy = DataProxy()

        proxy.search("anneal", user_id)  #先查玩家自己的anneal
        proxy.search_ranking("anneal", "hard_floor", user_id)   #先查玩家自己的排名
        proxy.search_by_rank("anneal", "hard_floor", req.start_index - 1, req.end_index - 1)
        defer = proxy.execute()

        defer.addCallback(self._calc_query_anneal_hard_mode_ranking, user_id, req, timer)
        defer.addErrback(self._query_anneal_hard_mode_ranking_failed, req, timer)
        return defer


    def _calc_query_anneal_hard_mode_ranking(self, proxy, user_id, req, timer):
        self_level = proxy.get_result("anneal", user_id).hard_floor
        self_ranking = proxy.get_ranking("anneal", "hard_floor", user_id) + 1
        results = proxy.get_rank_result(
                "anneal", "hard_floor", req.start_index - 1, req.end_index - 1)

        proxy = DataProxy()
        players = {}
        player_rankings = {}
        for i,value in enumerate(results):
            players[value.user_id] = value
            player_rankings[value.user_id] = i
            proxy.search("user", value.user_id)
        proxy.search("user", user_id)   #再查一下玩家自己

        defer = proxy.execute()
        defer.addCallback(self._query_anneal_hard_mode_ranking_succeed, user_id, req, self_ranking,
                self_level, players, player_rankings, timer)
        return defer
        
       
    def _query_anneal_hard_mode_ranking_succeed(self, proxy, user_id, req,
            self_ranking, self_score, players, players_ranking, timer):
        users = proxy.get_all_result("user")
        if len(users) != len(players) and len(users) != (len(players) + 1):
            raise Exception("Ranking players num error")
        logger.debug('len users [%d]' % len(users))

        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for i, user in enumerate(users):
            if user.id == user_id:
                pack.pack_ranking_info_of_user(
                        user, self_score, self_ranking, res.rankings.add())
            else:
                pack.pack_ranking_info_of_user(
                        user,
                        players[user.id].hard_floor,
                        players_ranking[user.id] + 1,
                        res.rankings.add())

        response = res.SerializeToString()
        log = log_formater.output2(user_id, "Query anneal hard mode ranking succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_anneal_hard_mode_ranking_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query anneal hard mode ranking failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query anneal hard mode ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def _query_worldboss_ranking(self, user_id, req, timer):
        if req.start_index < 1 or req.start_index > req.end_index:
            raise Exception("Ranking req error")

        proxy = DataProxy()

        proxy.search("worldboss", user_id)  #先查玩家自己的worldboss
        proxy.search_ranking("worldboss", "merit", user_id)   #先查玩家自己的排名
        proxy.search_by_rank("worldboss", "merit", req.start_index - 1, req.end_index - 1)
        defer = proxy.execute()

        defer.addCallback(self._calc_query_worldboss_ranking, user_id, req, timer)
        defer.addErrback(self._query_worldboss_ranking_failed, req, timer)
        return defer


    def _calc_query_worldboss_ranking(self, proxy, user_id, req, timer):
        self_merit = proxy.get_result("worldboss", user_id).merit
        self_ranking = proxy.get_ranking("worldboss", "merit", user_id) + 1
        results = proxy.get_rank_result(
                "worldboss", "merit", req.start_index - 1, req.end_index - 1)

        proxy = DataProxy()
        players = {}
        player_rankings = {}
        for i,value in enumerate(results):
            players[value.user_id] = value
            player_rankings[value.user_id] = i
            proxy.search("user", value.user_id)
        proxy.search("user", user_id)   #再查一下玩家自己

        defer = proxy.execute()
        defer.addCallback(self._query_worldboss_ranking_succeed, user_id, req, self_ranking,
                self_merit, players, player_rankings, timer)
        return defer
        
       
    def _query_worldboss_ranking_succeed(self, proxy, user_id, req,
            self_ranking, self_score, players, players_ranking, timer):
        users = proxy.get_all_result("user")
        if len(users) != len(players) and len(users) != (len(players) + 1):
            raise Exception("Ranking players num error")
        logger.debug('len users [%d]' % len(users))

        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for i, user in enumerate(users):
            if user.id == user_id:
                pack.pack_ranking_info_of_user(
                        user, self_score, self_ranking, res.rankings.add())
            else:
                pack.pack_ranking_info_of_user(
                        user,
                        players[user.id].merit,
                        players_ranking[user.id] + 1,
                        res.rankings.add())

        response = res.SerializeToString()
        log = log_formater.output2(user_id, "Query worldboss ranking succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_worldboss_ranking_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query worldboss ranking failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query worldboss ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def _query_melee_ranking(self, user_id, req, timer):

        cache_proxy = DataProxy()

        cache_proxy.search("melee", user_id)  #先查玩家自己的melee

        cache_proxy.search_ranking("melee", "score", user_id)   #先查玩家自己的排名
        #拿到房间的积分范围
        scores_range = []
        range = MeleeInfo.get_index_score_range(MeleeInfo.MELEE_INDEX)
        scores_range.append(range)

        for range in scores_range:
            cache_proxy.search_by_rank_score(
                    "melee", "score", range[0], range[1], 0, MELEE_COUNT)

        defer = cache_proxy.execute()
        defer.addCallback(self._calc_query_melee_ranking,
                user_id, scores_range, req, timer)
        return defer


    def _calc_query_melee_ranking(self, proxy, user_id, scores_range, req, timer):
        cache_proxy = DataProxy()
        self_arena = proxy.get_result("melee", user_id)
        self_ranking = proxy.get_ranking("melee", "score", user_id) + 1
        cache_proxy.search("user", user_id)

        all_arenas = {}
        all_arenas_rank = {}
        player_rankings = {}
        for range in scores_range:
            arena_list = proxy.get_rank_score_result(
                    "melee", "score", range[0], range[1], 0, MELEE_COUNT)

            #按照积分先排序
            arena_list.sort(lambda x,y:cmp(ArenaInfo.get_real_score(x.score),
                ArenaInfo.get_real_score(y.score)), reverse = True)

            arena_rank = 1
            for arena in arena_list:
                all_arenas[arena.user_id] = arena
                all_arenas_rank[arena.user_id] = arena_rank
                arena_rank = arena_rank + 1
                cache_proxy.search("user", arena.user_id)

        defer = cache_proxy.execute()
        defer.addCallback(self._query_melee_ranking_succeed, user_id,
                self_arena, self_ranking, all_arenas, all_arenas_rank, req, timer)
        return defer


    def _query_melee_ranking_succeed(self, proxy, user_id,
            self_arena, self_ranking, all_arenas, all_arenas_rank, req, timer):

        users = proxy.get_all_result("user")

        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for i, user in enumerate(users):
            if user.id == user_id:
                pack.pack_ranking_info_of_user(
                        user, MeleeInfo.get_real_score(self_arena.score), 
                        self_ranking, res.rankings.add())


            else:
                pack.pack_ranking_info_of_user(
                        user, MeleeInfo.get_real_score(all_arenas[user.id].score),
                        all_arenas_rank[user.id],
                        res.rankings.add())

        response = res.SerializeToString()
        log = log_formater.output2(user_id, "Query melee ranking succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_melee_ranking_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Query melee ranking failed[reason=%s]" % err)

        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query melee ranking failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def _query_transfer_arena(self, user_id, req, timer):
        """查询换位厌恶场排名"""
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_transfer_arena, req, timer)
        defer.addErrback(self._query_transfer_arena_failed, req, timer)
        return defer

    def _calc_query_transfer_arena(self, data, req, timer):
        req = internal_pb2.InternalQueryTransferReq()
        req.user_id = data.id
        request = req.SerializeToString()

        defer = GlobalObject().remote["common"].callRemote("query_transfer_info", 1, request)
        defer.addCallback(self._calc_query_transfer_arena_result, data, req, timer)
        return defer

    def _calc_query_transfer_arena_result(self, common_response, data, req, timer):
        common_res = internal_pb2.InternalQueryTransferRes()
        common_res.ParseFromString(common_response)

        if common_res.status != 0:
            raise Exception("Query transfer failed")

        transfer_business.update_transfer(data, common_res.match)

        rank_dict = {}
        for t in common_res.top20:
            rank_dict[t.user_id] = t
        for m in common_res.match:
            rank_dict[m.user_id] = m
        for b in common_res.behind5:
            rank_dict[b.user_id] = b
        rank_dict[common_res.self.user_id] = common_res.self

        ranks = rank_dict.values()
        ranks.sort(key=lambda x: x.rank)
        matcher = UserMatcherWithBattle()
        for rank in ranks:
            matcher.add_condition(rank.user_id, rank.is_robot)

        defer = matcher.match()
        defer.addCallback(self._calc_query_transfer_arena_match, data, req, timer, ranks)
        return defer

    def _calc_query_transfer_arena_match(self, results, data, req, timer, ranks):
        res = ranking_pb2.QueryRankingRes()
        res.status = 0

        for rank in ranks:
            rank_info = res.rankings.add()
            rank_info.id = rank.user_id
            rank_info.ranking = rank.rank
            rank_info.name = results[rank.user_id]['name']
            rank_info.level = results[rank.user_id]['level']
            rank_info.value = results[rank.user_id]['battle_score'] if not rank.is_robot else 0
            rank_info.icon_id = results[rank.user_id]['icon_id']
            rank_info.value1 = int(rank.transfer_type)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_transfer_arena_succeed, req, res, timer)
        return defer

    def _query_transfer_arena_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query transfer arena rank succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _query_transfer_arena_failed(self, err, req, timer):
        logger.fatal("Query transfer arena rank failed[reason=%s]" % err)
        res = ranking_pb2.QueryRankingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query transfer arena rank failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _query_ranking_player_from_pve(self, req, timer):
        """从pve中查询机器人"""
        enemy = PVEEnemyPool().get_by_id(req.target_user_id)
        
        res = ranking_pb2.QueryRankingPlayerPowerfulTeamsRes()
        res.status = 0

        index = 0
        for i in xrange(3):
            if enemy.teamInfo[index] == 0:
                continue
            team = res.teams.add()
            team.index = i
            for j in xrange(3):
                if enemy.teamInfo[index] == 0:
                    continue
                hero = team.heroes.add()

                hero.basic_id = enemy.teamInfo[index]
                hero.level = enemy.heroLevel[index] if index < len(enemy.heroLevel) else 1
                hero.star_level = enemy.heroStarLevel[index] if index < len(enemy.heroStarLevel) else 1

                if index < len(enemy.soldierBasicId):
                    hero.soldier_basic_id = enemy.soldierBasicId[index]
                hero.soldier_level = enemy.soldierLevel[index] if index < len(enemy.soldierLevel) else 1

                if index * 3 < len(enemy.heroEquipmentId):
                    hero.equipment_weapon_id = enemy.heroEquipmentId[index * 3]
                if index * 3 + 1 < len(enemy.heroEquipmentId):
                    hero.equipment_armor_id = enemy.heroEquipmentId[index * 3 + 1]
                if index * 3 + 2 < len(enemy.heroEquipmentId):
                    hero.equipment_treasure_id = enemy.heroEquipmentId[index * 3 + 2]

                hero.evolution_level = enemy.heroEvolutionLevel[index] if index < len(enemy.heroEvolutionLevel) else 1
                
                index += 1
        
        response = res.SerializeToString()
        log = log_formater.output2(req.user_id, "Query ranking robot powerful teams succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response
