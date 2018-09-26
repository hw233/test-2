#coding:utf8
"""
Created on 2016-03-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 处理竞技场请求
"""

import base64
from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import map_pb2
from proto import internal_pb2
from proto import broadcast_pb2
from proto import internal_union_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.plunder import PlunderInfo
from app.data.rival import RivalInfo
from app.plunder_matcher import PlunderMatcher
from app.business import plunder as plunder_business
from app.business import account as account_business


class PlunderProcessor(object):
    """处理pvp掠夺相关逻辑
    """

    def query_pvp_players(self, user_id, request):
        """查询掠夺对手
        """
        timer = Timer(user_id)

        req = map_pb2.QueryPlayersReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_pvp_players, req, timer)
        defer.addErrback(self._query_pvp_players_failed, req, timer)
        return defer


    def _calc_query_pvp_players(self, data, req, timer):
        user = data.user.get()
        if not user.allow_pvp:
            raise Exception("PVP is not unlock[user_level=%d]" % user.level)

        if not account_business.update_across_day_info(data, timer.now, True):
            logger.warning("Update across day info failed")
            return False

        user = data.user.get(True)
        resource = data.resource.get()
        invalid_rival = [data.id]
        plunder_matcher = PlunderMatcher(user.level, invalid_rival)
        plunder = data.plunder.get()

        #刷新扣除金钱
        if req.HasField("cost_money"):
            resource.cost_money(req.cost_money)

        if req.type == 1: #掠夺
            plunder_matcher.add_condition(data, plunder)
            #匹配对手
            defer = plunder_matcher.match(plunder, user.country)
            defer.addCallback(self._pack_pvp_players_response,
                data, plunder, plunder_matcher, req, timer)
            return defer

        elif req.type == 2:  #仇家
            res = map_pb2.QueryPlayersRes()
            res.status = 0

            plunder_business.update_plunder_enemy(data) 
            plunder_enemy_list = data.plunder_record_list.get_all()
            for plunder_enemy in plunder_enemy_list:
                pack.pack_plunder_record(plunder_enemy, res.players.add())

            res.attack_num = plunder.attack_num
            res.left_reset_num = plunder.get_left_reset_num()

            defer = DataBase().commit(data)
            defer.addCallback(self._query_pvp_players_succeed, req, res, timer)
            return defer


        elif req.type == 3: #指定查询
            rival_id = plunder.generate_specify_rival_id()
            rival = data.rival_list.get(rival_id)
            if rival is None:
                rival = RivalInfo.create(rival_id, data.id)
                data.rival_list.add(rival)

            #查询对手
            defer = plunder_matcher.query_specify_user(req.str, rival)
            defer.addCallback(self._pack_pvp_players_response,
                data, plunder, plunder_matcher, req, timer)

            return defer


    def _pack_pvp_players_response(self, proxy, data, plunder, plunder_matcher, req, timer):
        """构造返回
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = map_pb2.QueryPlayersRes()
        res.status = 0

        for id in plunder_matcher.players:
            rival = data.rival_list.get(id, True)
            player_msg = res.players.add()
            pack.pack_plunder_player(rival, player_msg)
            #如果已经是仇人了，加上仇恨值
            enemy = plunder_business.get_plunder_enemy(data, rival.rival_id)
            if enemy is not None:
                player_msg.hatred = enemy.hatred

        res.attack_num = plunder.attack_num
        res.left_reset_num = plunder.get_left_reset_num()

        resource = data.resource.get()
        resource.update_current_resource(timer.now)
        pack.pack_resource_info(resource, res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_pvp_players_succeed, req, res, timer)
        return defer


    def _pack_specify_user_response(self, proxy, data, plunder, plunder_matcher, req, timer):
        """构造返回
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = map_pb2.QueryPlayersRes()
        res.status = 0

        for enemy in plunder_matcher._pvp_players:
            pack.pack_plunder_enemy(enemey, res.players.add())


        res.attack_num = plunder.attack_num
        res.left_reset_num = plunder.get_left_reset_num()

        defer = DataBase().commit(data)
        defer.addCallback(self._query_pvp_players_succeed, req, res, timer)
        return defer


    def _query_pvp_players_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Query pvp players succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_pvp_players_failed(self, err, req, timer):
        logger.fatal("Query pvp players failed[reason=%s]" % err)

        res = map_pb2.QueryPlayersRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query pvp players failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_player_info(self, user_id, request):
        """查询指定对手详情
        """
        timer = Timer(user_id)

        req = map_pb2.QueryPlayerInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_player_info, req, timer)
        defer.addErrback(self._query_player_failed, req, timer)
        return defer


    def _calc_query_player_info(self, data, req, timer):
        #
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")
        
        plunder = data.plunder.get()
        rival_id = plunder.get_plunder_rival_id(req.user_id)
        if rival_id != 0:
            #在之前匹配的4个rival中，直接打包返回
            rival = data.rival_list.get(rival_id)
            defer = Deferred()
            if rival.union_id != 0:
                defer.addCallback(self._query_union_info, data, plunder, rival, req, timer)
            else:
                defer.addCallback(self._pack_query_player_response, data, plunder, rival, req, timer)

            defer.addErrback(self._query_player_failed, req, timer)
            defer.callback(0)
        else:

            rival_id = plunder.generate_specify_rival_id()
            rival = data.rival_list.get(rival_id)
            if rival is None:
                rival = RivalInfo.create(rival_id, data.id)
                data.rival_list.add(rival)

            #去新匹配
            user = data.user.get(True)
            plunder = data.plunder.get()
            invalid_rival = [data.id]
            plunder_matcher = PlunderMatcher(user.level, invalid_rival)
            defer = plunder_matcher.match_specify(data, plunder, req.user_id, user.country)
            defer.addCallback(self._query_union_info, data, plunder, rival, req, timer)

        return defer

    
    def _query_union_info(self, proxy, data, plunder, rival, req, timer):
        """"""
        union_req = internal_union_pb2.InternalQueryUnionReq()
        union_req.user_id = data.id
        
        defer = GlobalObject().remote['gunion'].callRemote(
                "query_union_summary", rival.union_id, union_req.SerializeToString())
        defer.addCallback(self._pack_query_player_response, data, plunder, rival, req, timer)
        return defer


    def _pack_query_player_response(self, union_response, data, plunder, rival, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        if rival.union_id != 0:
            union_res = internal_union_pb2.InternalQueryUnionRes()
            union_res.ParseFromString(union_response)
            if union_res.status != 0:
                logger.warning("Query union res errro")
                union_info = None
            else:
                union_info = []
                union_info.append(union_res.union.id)
                union_info.append(union_res.union.name)
                union_info.append(union_res.union.icon_id)
        else:
            union_info = None

        res = map_pb2.QueryPlayerInfoRes()
        res.status = 0
        res.attack_num = plunder.attack_num
        res.left_reset_num = plunder.get_left_reset_num()

        enemy = plunder_business.get_plunder_enemy(data, rival.rival_id)

        if enemy is not None:
            hatred = enemy.hatred
            been_attacked_num = enemy.been_attacked_num
            today_attack_money = enemy.today_attack_money
            today_attack_food = enemy.today_attack_food
            today_robbed_money = enemy.today_robbed_money
            today_robbed_food = enemy.today_robbed_food
        else:
            hatred = 0
            been_attacked_num = 0
            today_attack_money = 0
            today_attack_food = 0
            today_robbed_money = 0
            today_robbed_food = 0

        pack.pack_plunder_player_with_detail(rival, res.player, union_info, hatred, 
                been_attacked_num, today_attack_money, today_attack_food,
                today_robbed_money, today_robbed_food)

        #resource = data.resource.get()
        #resource.update_current_resource(timer.now)
        #pack.pack_resource_info(resource, res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_player_succeed, req, res, timer)
        return defer


    def _query_player_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Query player succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_player_failed(self, err, req, timer):
        logger.fatal("Query player failed[reason=%s]" % err)

        res = map_pb2.QueryPlayerInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query player failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def reset_attack_num(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = map_pb2.ResetAttackNumReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reset_attack_num, req, timer)
        defer.addCallback(self._reset_attack_num_succeed, req, timer) 
        defer.addErrback(self._reset_attack_num_failed, req, timer)
        return defer


    def _calc_reset_attack_num(self, data, req, timer):
        plunder = data.plunder.get()
        
        plunder_business.reset_attack_num(data, plunder)
        return DataBase().commit(data)


    def _reset_attack_num_succeed(self, data, req, timer):
        plunder = data.plunder.get(True)
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        res = map_pb2.ResetAttackNumRes()
        res.status = 0
        res.attack_num = plunder.attack_num
        res.left_reset_num = plunder.get_left_reset_num()
        pack.pack_resource_info(resource, res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Reset attack num succeed",
                req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _reset_attack_num_failed(self, err, req, timer):
        logger.fatal("Reset attack num failed[reason=%s]" % err)
        plunder = data.plunder.get(True)
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        res = map_pb2.ResetAttackNumRes()
        res.status = 0 #-1
        res.attack_num = plunder.attack_num
        res.left_reset_num = plunder.get_left_reset_num()
        pack.pack_resource_info(resource, res.resource)

        response = res.SerializeToString()
        logger.notice("Reset attack num failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


  
