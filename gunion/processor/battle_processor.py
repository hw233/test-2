#coding:utf8
"""
Created on 2016-06-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from proto import internal_union_pb2
from proto import internal_pb2
from proto import union_pb2
from proto import union_battle_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from gunion.data.battle import UnionBattleInfo
from gunion.data.battle_node import UnionBattleMapNodeInfo
from gunion.business import aid as aid_business
from gunion.business import member as member_business
from gunion.business import battle as battle_business
from gunion.season_searcher import SeasonRankingSearcher
from gunion.season_allocator import SeasonAllocator
from gunion.battle_matcher import BattleMatcher
from gunion import pack
import base64


class BattleProcessor(object):


    def query(self, union_id, request):
        """查询联盟战争情况
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        member_invalid = False
        user_id = 0
        if req.HasField("user_id"):
            user_id = req.user_id
            member = member_business.find_member(data, user_id)
            if member is None:
                #玩家不在联盟中
                member_invalid = True

        if member_invalid:
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        else:
            #刷新，返回战争信息
            battle_business.update_battle(data, timer.now)
            res = self._pack_query_response(union_pb2.UNION_OK, data, user_id, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _pack_invalid_query_response(self, ret):
        """打包非法查询战争响应
        """
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_query_response(self, ret, data, user_id, now):
        """打包查询战争响应
        """
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = 0
        res.ret = ret

        battle = battle_business.get_current_battle(data, now)
        self._pack_battle_info(data, user_id, res.battle, now)
        return res


    def _pack_battle_info(self, data, user_id, battle_message, now):
        """打包战争详情
        """
        #战争基础信息
        union = data.union.get(True)
        season = data.season.get(True)
        battle = battle_business.get_current_battle(data, now)
        pack.pack_battle_info(union, season, battle, battle_message, now)

        #个人数据
        if user_id != 0:
            member = member_business.find_member(data, user_id)
            if member is not None:
                pack.pack_battle_individual_info(member, battle_message.user)

        #己方防守地图信息
        nodes = battle_business.get_battle_map(data)
        pack.pack_battle_map_info(union, season, battle, nodes, battle_message.own_map, now)

        #战斗记录
        records = data.battle_record_list.get_all(True)
        for record in records:
            pack.pack_battle_record_info(record, battle_message.records.add(), now)


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def launch(self, union_id, request, force = False):
        """发起联盟战争
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_launch, req, timer, force)
        defer.addErrback(self._launch_failed, req, timer)
        return defer


    def _calc_launch(self, data, req, timer, force):
        member = member_business.find_member(data, req.user_id)
        if not force and member is None:
            #玩家已经不在联盟中
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        elif not force and member.is_normal_member():
            #只有盟主和副盟主，有权发起联盟战争
            res = self._pack_invalid_query_response(union_pb2.UNION_NO_AUTH)
        else:
            battle = battle_business.get_current_battle(data, timer.now)
            if battle.is_at_war():
                #在交战中，不能重复发起战争，返回当前战争情况
                res = self._pack_query_response(
                        union_pb2.UNION_BATTLE_LAUNCH_DUP, data, req.user_id, timer.now)
            else:
                season = data.season.get()
                if not season.is_able_to_launch_battle(timer.now):
                    logger.warning("Not able to launch battle")
                    #不能发起战争，返回当前战争情况
                    res = self._pack_query_response(
                            union_pb2.UNION_BATTLE_LAUNCH_INVALID, data, req.user_id, timer.now)
                else:
                    #发起战争
                    max_index = 0
                    recent_rival_id = 0
                    for battle_past in data.battle_list.get_all(True):
                        logger.debug("Candidate rival[index=%d][rival_id=%d]" %
                                (battle_past.index, battle_past.rival_union_id))
                        if battle_past.index > max_index and battle_past.rival_union_id != 0:
                            recent_rival_id = battle_past.rival_union_id
                            max_index = battle_past.index

                    old_rival_id = []
                    if recent_rival_id > 0:
                        logger.debug("Invalid rival[rival_id=%d]" % recent_rival_id)
                        old_rival_id.append(recent_rival_id)

                    matcher = BattleMatcher()
                    matcher.add_condition(season.match_score, [data.id], old_rival_id)
                    defer = matcher.match()
                    defer.addCallback(self._calc_launch_result, data, battle, req, timer)
                    return defer

        defer = DataBase().commit(data)
        defer.addCallback(self._launch_succeed, req, res, timer)
        return defer


    def _calc_launch_result(self, matcher, data, battle, req, timer):
        if matcher.result is None:
            #没有匹配到合适的对手
            res = self._pack_query_response(
                    union_pb2.UNION_BATTLE_LAUNCH_NORIVAL, data, req.user_id, timer.now)
            defer = DataBase().commit(data)
            defer.addCallback(self._launch_succeed, req, res, timer)
            return defer

        rival_union_season = matcher.result
        rival_union_id = rival_union_season.union_id

        #向对方联盟提交发起战争请求
        launch_req = internal_union_pb2.InternalLaunchUnionBattleReq()
        launch_req.rival_union_id = data.id
        launch_req.rival_union_battle_index = battle.index

        defer = GlobalObject().remote['gunion'].callRemote(
                "accept_battle", rival_union_id, launch_req.SerializeToString())
        defer.addCallback(self._post_launch, data, battle, req, timer)
        return defer


    def _post_launch(self, launch_response, data, battle, req, timer):
        """收到对方联盟的响应
        """
        launch_res = internal_union_pb2.InternalLaunchUnionBattleRes()
        launch_res.ParseFromString(launch_response)

        if launch_res.status != 0:
            raise Exception("Launch union battle res error[res=%s]" % launch_res)

        if launch_res.ret != union_pb2.UNION_OK:
            #对方联盟不能参战
            res = self._pack_query_response(
                    union_pb2.UNION_BATTLE_LAUNCH_INVALID, data, req.user_id, timer.now)
        else:
            #对方联盟接受战斗请求，双方进入战斗
            rival_union_id = launch_res.rival_union_id
            rival_battle_id = UnionBattleInfo.generate_id(
                    rival_union_id, launch_res.rival_union_battle_index)
            battle_business.launch_battle(
                    data, battle, rival_union_id, rival_battle_id, timer.now)
            res = self._pack_query_response(
                    union_pb2.UNION_OK, data, req.user_id, timer.now)

            #发广播
            try:
                defer = self._launch_broadcast(data, launch_res.rival_union_name, req, timer)
            except:
                defer = Deferred()
                defer.callback(False)
            defer.addCallback(self._post_launch_broadcast, data, req, res, timer)
            return defer

        defer = DataBase().commit(data)
        defer.addCallback(self._launch_succeed, req, res, timer)
        return defer

    def _post_launch_broadcast(self, result, data, req, res, timer):
        if not result:
            logger.warning("Launch union battle send broadcast failed[union_id=%d]" % timer.id)

        defer = DataBase().commit(data)
        defer.addCallback(self._launch_succeed, req, res, timer)
        return defer

    def _launch_broadcast(self, data, rival_union_name, req, timer):
        union_name = data.union.get(True).name

        broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_launch_unionbattle'].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(union_name), 1)
        content = content.replace("#str#", base64.b64decode(rival_union_name), 1)

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._launch_broadcast_result)
        return defer

    def _launch_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        return res.status == 0


    def _launch_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Launch union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _launch_failed(self, err, req, timer):
        logger.fatal("Launch union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Launch union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def launch_two(self, union_id, request):
        """发起两个指定联盟的战争
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalLaunchUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_launch_new, req, timer)
        defer.addErrback(self._launch_failed, req, timer)
        return defer


    def _calc_launch_new(self, data, req, timer):
        battle = battle_business.get_current_battle(data, timer.now)
        if battle.is_at_war():
            #在交战中，不能重复发起战争，返回当前战争情况
            res = _pack_launch_response(
                    union_pb2.UNION_BATTLE_LAUNCH_DUP, timer.now)
            
            internal_union_pb2.InternalLaunchUnionBattleRes()
            res.status = -1
            res.ret = union_pb2.UNION_BATTLE_LAUNCH_DU
        else:
            season = data.season.get()
            if not season.is_able_to_launch_battle(timer.now):
                logger.warning("Not able to launch battle")
                #不能发起战争，返回当前战争情况
                res = internal_union_pb2.InternalLaunchUnionBattleRes()
                res.status = -1
                res.ret = union_pb2.UNION_BATTLE_LAUNCH_INVALID
            else:
                #发起战争
                rival_union_id = req.rival_union_battle_index
        
                #向对方联盟提交发起战争请求
                launch_req = internal_union_pb2.InternalLaunchUnionBattleReq()
                launch_req.rival_union_id = data.id
                launch_req.rival_union_battle_index = battle.index
        
                defer = GlobalObject().remote['gunion'].callRemote(
                        "accept_battle", rival_union_id, launch_req.SerializeToString())
                defer.addCallback(self._post_launch_new, data, battle, req, timer)
                return defer

        defer = DataBase().commit(data)
        defer.addCallback(self._launch_new_succeed, req, res, timer)
        return defer


    def _post_launch_new(self, launch_response, data, battle, req, timer):
        """收到对方联盟的响应
        """
        launch_res = internal_union_pb2.InternalLaunchUnionBattleRes()
        launch_res.ParseFromString(launch_response)

        if launch_res.status != 0:
            raise Exception("Launch union battle res error[res=%s]" % launch_res)

        if launch_res.ret != union_pb2.UNION_OK:
            #对方联盟不能参战
            res = self._pack_launch_response(
                    union_pb2.UNION_BATTLE_LAUNCH_INVALID)
        else:
            #对方联盟接受战斗请求，双方进入战斗
            rival_union_id = launch_res.rival_union_id
            rival_battle_id = UnionBattleInfo.generate_id(
                    rival_union_id, launch_res.rival_union_battle_index)
            battle_business.launch_battle(
                    data, battle, rival_union_id, rival_battle_id, timer.now)
            res = self._pack_launch_response(
                    union_pb2.UNION_OK)

            #发广播
            try:
                defer = self._launch_broadcast(data, launch_res.rival_union_name, req, timer)
            except:
                defer = Deferred()
                defer.callback(False)
            defer.addCallback(self._post_launch_broadcast, data, req, res, timer)
            return defer

        defer = DataBase().commit(data)
        defer.addCallback(self._launch_new_succeed, req, res, timer)
        return defer


    def _pack_launch_response(self, ret):
        """打包查询战争响应
        """
        res = internal_union_pb2.InternalLaunchUnionBattleRes()
        res.status = 0
        res.ret = ret

        return res


    def _launch_new_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Launch union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _launch_new_failed(self, err, req, timer):
        logger.fatal("Launch union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalLaunchUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Launch union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def accept(self, union_id, request):
        """接受战争请求
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalLaunchUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_accept, req, timer)
        defer.addErrback(self._accept_failed, req, timer)
        return defer


    def _calc_accept(self, data, req, timer):
        """接受战争请求
        """
        season = data.season.get()
        if not season.is_able_to_join_battle:
            logger.debug("Not able to accept battle")
            #不能参战
            res = self._pack_accept_response(data, union_pb2.UNION_BATTLE_LAUNCH_INVALID)
        else:
            #接受战斗
            battle = battle_business.get_current_battle(data, timer.now)
            rival_union_id = req.rival_union_id
            rival_battle_id = UnionBattleInfo.generate_id(
                    rival_union_id, req.rival_union_battle_index)
            battle_business.launch_battle(
                    data, battle, rival_union_id, rival_battle_id, timer.now, False)
            res = self._pack_accept_response(data, union_pb2.UNION_OK, battle)

        defer = DataBase().commit(data)
        defer.addCallback(self._accept_succeed, req, res, timer)
        return defer


    def _pack_accept_response(self, data, ret, battle = None):
        res = internal_union_pb2.InternalLaunchUnionBattleRes()
        res.status = 0
        res.ret = ret

        if battle is not None:
            res.rival_union_id = battle.union_id
            res.rival_union_battle_index = battle.index
            res.rival_union_name = data.union.get(True).name
        return res


    def _accept_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Accept union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _accept_failed(self, err, req, timer):
        logger.fatal("Accept union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalLaunchUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def deploy(self, union_id, request):
        """部署联盟战争节点防御
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalDeployUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_deploy, req, timer)
        defer.addErrback(self._deploy_failed, req, timer)
        return defer


    def _calc_deploy(self, data, req, timer):
        member = member_business.find_member(data, req.user_id)
        battle = battle_business.update_battle(data, timer.now)
        node_id = UnionBattleMapNodeInfo.generate_id(data.id, req.node_index)
        node = data.battle_node_list.get(node_id)
        city_level = 0

        if member is None:
            #玩家已经不在联盟中
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        elif not member.is_join_battle:
            #玩家未参战
            res = self._pack_invalid_query_response(union_pb2.UNION_BATTLE_LOCKED)
        elif not battle.is_able_to_deploy():
            #战争不是准备阶段，无法布防
            res = self._pack_query_response(
                    union_pb2.UNION_BATTLE_DEPLOY_INVALID, data, req.user_id, timer.now)
        else:
            team = []#阵容
            heroes = []#英雄信息
            techs = []#科技信息
            TEAM_HERO_COUNT = 3
            if member.is_normal_member():
                city_level = UnionBattleMapNodeInfo.CITY_LEVEL_MEMBER
            elif member.is_vice_leader():
                city_level = UnionBattleMapNodeInfo.CITY_LEVEL_VICE
            elif member.is_leader():
                city_level = UnionBattleMapNodeInfo.CITY_LEVEL_LEADER

            for team_info in req.teams:
                hero_num = 0
                for hero_info in team_info.heroes:
                    hero_num += 1
                    team.append(hero_info.basic_id)
                    if hero_info.basic_id == 0:
                        continue
                    heroes.append(hero_info)
                for i in range(TEAM_HERO_COUNT - hero_num):
                    team.append(0)    #若该team不满3人，客户端并没有传id为0的hero，所以此处补全
            for tech_basic_id in req.battle_tech_ids:
                techs.append(tech_basic_id)

            if len(team) == 0 and node.is_able_to_cancel_deploy(req.user_id):
                #取消防御部署
                battle_business.cancel_deploy_node(data, node)
                res = self._pack_query_response(
                        union_pb2.UNION_OK, data, req.user_id, timer.now)
            elif len(team) > 0 and node.is_able_to_deploy():
                #部署防御
                battle_business.deploy_node(data, node,
                        req.defender_user_id, req.defender_user_name,
                        req.defender_user_icon, req.defender_user_level,
                        team, heroes, techs, city_level)
                res = self._pack_query_response(
                        union_pb2.UNION_OK, data, req.user_id, timer.now)
            elif len(team) > 0 and node.is_able_to_cancel_deploy(req.user_id):
                #更新防御部署
                battle_business.cancel_deploy_node(data, node)
                battle_business.deploy_node(data, node,
                        req.defender_user_id, req.defender_user_name,
                        req.defender_user_icon, req.defender_user_level,
                        team, heroes, techs, city_level)
                res = self._pack_query_response(
                        union_pb2.UNION_OK, data, req.user_id, timer.now)
            else:
                #已经无法布防/取消布防
                res = self._pack_query_response(
                        union_pb2.UNION_BATTLE_DEPLOY_INVALID, data, req.user_id, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._deploy_succeed, req, res, timer)
        return defer


    def _deploy_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Deploy union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _deploy_failed(self, err, req, timer):
        logger.fatal("Deploy union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Deploy union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def cancel_deploy(self, union_id, request):
        """取消节点的防御部署
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalDeployUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_cancel_deploy, req, timer)
        defer.addErrback(self._cancel_deploy_failed, req, timer)
        return defer


    def _calc_cancel_deploy(self, data, req, timer):
        member = member_business.find_member(data, req.user_id)
        defender = member_business.find_member(data, req.defender_user_id)
        if member is None:
            #玩家已经不在联盟中
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        elif not member.is_join_battle:
            #玩家未参战
            res = self._pack_invalid_query_response(union_pb2.UNION_BATTLE_LOCKED)
        elif member.is_normal_member():
            #只有盟主和副盟主，有权取消部署
            res = self._pack_invalid_query_response(union_pb2.UNION_NO_AUTH)
        else:
            battle = battle_business.update_battle(data, timer.now)
            node_id = UnionBattleMapNodeInfo.generate_id(data.id, req.node_index)
            node = data.battle_node_list.get(node_id)
            if not battle.is_able_to_deploy() or not node.is_deployed(req.defender_user_id):
                #已经无法取消
                res = self._pack_query_response(
                        union_pb2.UNION_BATTLE_DEPLOY_INVALID, data, req.user_id, timer.now)
            elif defender is None:
                #驻防玩家已经不在联盟中，直接取消部署
                battle_business.cancel_deploy_node(data, node)
                res = self._pack_query_response(
                        union_pb2.UNION_OK, data, req.user_id, timer.now)
            else:
                #通知驻防玩家，取消防御部署
                defer = self._cancel_deploy_notice(data, req, timer)
                return defer

        defer = DataBase().commit(data)
        defer.addCallback(self._cancel_deploy_succeed, req, res, timer)
        return defer


    def _cancel_deploy_notice(self, data, req, timer):
        app_req = union_battle_pb2.DeployUnionBattleReq()
        app_req.user_id = req.defender_user_id
        app_req.union_id = data.id
        app_req.node_index = req.node_index

        defer = GlobalObject().remote['app'].callRemote(
                "deploy_union_battle", req.defender_user_id, app_req.SerializeToString())
        defer.addCallback(self._cancel_deploy_notice_post, data, req, timer)
        return defer


    def _cancel_deploy_notice_post(self, app_response, data, req, timer):
        app_res = union_battle_pb2.DeployUnionBattleRes()
        app_res.ParseFromString(app_response)

        if app_res.status != 0:
            raise Exception("Cancel deploy notice res error")

        if app_res.ret == union_pb2.UNION_OK:
            res = self._pack_query_response(
                    union_pb2.UNION_OK, data, req.user_id, timer.now)
        else:
            res = self._pack_query_response(
                    union_pb2.UNION_BATTLE_DEPLOY_INVALID, data, req.user_id, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._cancel_deploy_succeed, req, res, timer)
        return defer


    def _cancel_deploy_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Cancel deploy union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _cancel_deploy_failed(self, err, req, timer):
        logger.fatal("Cancel deploy union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Cancel deploy union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start(self, union_id, request):
        """开始一场战斗
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalStartUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_start, req, timer)
        defer.addErrback(self._start_failed, req, timer)
        return defer


    def _calc_start(self, data, req, timer):
        """开始一场战斗
        """
        if req.is_attack_side:
            #进攻方联盟收到开战信息
            member = member_business.find_member(data, req.attacker_user_id)
            if member is None:
                #玩家已经不在联盟中
                res = self._pack_start_response(union_pb2.UNION_NOT_MATCHED, data, timer.now)
            elif not member.is_join_battle:
                #玩家未参战
                res = self._pack_start_response(union_pb2.UNION_BATTLE_LOCKED, data, timer.now)
            else:
                res = self._pack_start_response(
                        union_pb2.UNION_OK, data, timer.now, True, req.attacker_user_id)

        else:
            #防守方联盟收到开战信息
            battle = battle_business.update_battle(data, timer.now)
            if not battle_business.start_node_battle_as_defender(data, battle,
                    req.attacker_user_id, req.attacker_user_name, req.attacker_user_icon,
                    req.attacker_soldier_num,
                    req.node_index, req.node_level, timer.now):
                #开战失败，返回正确的战争信息
                res = self._pack_start_response(
                        union_pb2.UNION_BATTLE_START_INVALID, data, timer.now, True)
            else:
                res = self._pack_start_response(union_pb2.UNION_OK, data, timer.now)
            
            #获取防守阵容信息
            node_id = UnionBattleMapNodeInfo.generate_id(data.id, req.node_index)
            node = data.battle_node_list.get(node_id)
            pack.pack_union_battle_rival(node, res.rival)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_succeed, req, res, timer)
        return defer


    def _pack_start_response(self, ret, data, now, include_battle_info = False, user_id = 0):
        res = internal_union_pb2.InternalStartUnionBattleRes()
        res.status = 0
        res.ret = ret

        if include_battle_info:
            self._pack_battle_info(data, user_id, res.battle, now)

        return res


    def _start_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Start union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _start_failed(self, err, req, timer):
        logger.fatal("Start union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalStartUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish(self, union_id, request):
        """结束一场战斗
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalFinishUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_finish, req, timer)
        defer.addErrback(self._finish_failed, req, timer)
        return defer


    def _calc_finish(self, data, req, timer):
        """结束一场战斗
        """
        battle = battle_business.update_battle(data, timer.now)
        score_add = []

        if req.is_attack_side:
            #作为进攻方
            member = member_business.find_member(data, req.attacker_user_id)
            if member is None:
                #玩家已经不在联盟中
                res = self._pack_finish_response(union_pb2.UNION_NOT_MATCHED, data, timer.now)
            elif not member.is_join_battle:
                #玩家未参战
                res = self._pack_finish_response(union_pb2.UNION_BATTLE_LOCKED, data, timer.now)
            elif not battle_business.finish_node_battle_as_attacker(
                    data, battle, req.node_index, req.battle_stage, req.is_attacker_win,
                    member, req.attacker_user_level, req.attacker_kills, score_add,
                    req.node_level_after_battle, req.is_node_broken_after_battle):
                #结束战斗失败
                res = self._pack_finish_response(
                        union_pb2.UNION_BATTLE_FINISH_INVALID, data, timer.now,
                        True, req.attacker_user_id, score_add[0])
            else:
                res = self._pack_finish_response(union_pb2.UNION_OK, data, timer.now,
                        True, req.attacker_user_id, score_add[0])
        else:
            member = member_business.find_member(data, req.defender_user_id)
            node_id = UnionBattleMapNodeInfo.generate_id(data.id, req.node_index)
            node = data.battle_node_list.get(node_id)
            soldier_num_before_battle = node.current_soldier_num
            #作为防守方
            if battle_business.finish_node_battle_as_defender(data, battle,
                    req.node_index, req.node_level,
                    req.is_attacker_win, req.attacker_user_id,
                    member, req.attacker_kills, req.defender_kills, timer.now):
                res = self._pack_finish_response(
                        union_pb2.UNION_OK, data, timer.now, True)

                #需要把当前节点的信息传回去,有可能这个节点血量已经被打光
                node_id = UnionBattleMapNodeInfo.generate_id(data.id, req.node_index)
                node = data.battle_node_list.get(node_id)
                soldier_num_after_battle = node.current_soldier_num

                res.node_level = node.level
                if (soldier_num_before_battle != soldier_num_after_battle and 
                        soldier_num_after_battle == 0):
                    res.is_node_broken_after_battle = True
                else:
                    res.is_node_broken_after_battle = False
                res.battle_stage = battle.stage

                #如果防守方在联盟中，通知
                # if member is not None:
                #     self._notice_defender(member, req.defender_kills, timer)
            else:
                #结束战斗失败
                res = self._pack_finish_response(
                        union_pb2.UNION_BATTLE_FINISH_INVALID, data, timer.now, True)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_succeed, req, res, timer)
        return defer


    def _notice_defender(self, defender, defender_kills, timer):
        """通知防守方，增加战功
        """
        score = defender.calc_battle_score_by_kills(defender_kills)

        app_req = internal_pb2.GainUnionBattleScoreReq()
        app_req.score = score

        defer = GlobalObject().remote['app'].callRemote(
                "gain_union_battle_individual_score",
                defender.user_id, app_req.SerializeToString())
        defer.addCallback(self._notice_defender_post, timer)
        return defer


    def _notice_defender_post(self, app_response, timer):
        app_res = internal_pb2.GainUnionBattleScoreRes()
        app_res.ParseFromString(app_response)

        if app_res.status != 0:
            raise Exception("Notice defender res error")


    def _pack_finish_response(self, ret, data, now,
            include_battle_info = False, user_id = 0, score = 0):
        res = internal_union_pb2.InternalFinishUnionBattleRes()
        res.status = 0
        res.ret = ret

        if include_battle_info:
            self._pack_battle_info(data, user_id, res.battle, now)
            res.individual_battle_score_add = score

        return res


    def _finish_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Finish union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_failed(self, err, req, timer):
        logger.fatal("Finish union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalFinishUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def drum(self, union_id, request):
        """擂鼓
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalDrumForUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_drum, req, timer)
        defer.addErrback(self._drum_failed, req, timer)
        return defer


    def _calc_drum(self, data, req, timer):
        member = member_business.find_member(data, req.user_id)
        if member is None:
            #玩家不在联盟中
            res = self._pack_invalid_drum_response(union_pb2.UNION_NOT_MATCHED)
        elif not member.is_join_battle:
            #玩家未参战
            res = self._pack_invalid_drum_response(union_pb2.UNION_BATTLE_LOCKED)
        else:
            #刷新，返回战争信息
            battle = battle_business.update_battle(data, timer.now)
            if battle.is_able_to_drum():
                score = battle_business.drum(data, battle, member, req.user_level)
                res = self._pack_drum_response(
                        union_pb2.UNION_OK, data, req.user_id, timer.now, score)
            else:
                res = self._pack_drum_response(
                        union_pb2.UNION_BATTLE_DRUM_INVALID, data, req.user_id, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._drum_succeed, req, res, timer)
        return defer


    def _pack_invalid_drum_response(self, ret):
        res = internal_union_pb2.InternalDrumForUnionBattleRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_drum_response(self, ret, data, user_id, now, score = 0):
        """
        """
        res = internal_union_pb2.InternalDrumForUnionBattleRes()
        res.status = 0
        res.ret = ret

        battle = battle_business.get_current_battle(data, now)
        self._pack_battle_info(data, user_id, res.battle, now)

        res.individual_battle_score_add = score
        return res


    def _drum_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Drum for union battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _drum_failed(self, err, req, timer):
        logger.fatal("Drum for union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Drum for union battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def accept_individual_step_award(self, union_id, request):
        """领取战功阶段奖励
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalAcceptUnionBattleIndividualStepReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_accept_individual_step, req, timer)
        defer.addErrback(self._accept_individual_step_failed, req, timer)
        return defer


    def _calc_accept_individual_step(self, data, req, timer):
        member = member_business.find_member(data, req.user_id)
        if member is None:
            #玩家不在联盟中
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        elif not member.is_join_battle:
            #玩家未参战
            res = self._pack_invalid_query_response(union_pb2.UNION_BATTLE_LOCKED)
        else:
            if not member.accept_battle_score_step_award(req.user_level, req.target_step):
                raise Exception("Accept battle score step award failed")

            res = self._pack_invalid_query_response(union_pb2.UNION_OK)

        defer = DataBase().commit(data)
        defer.addCallback(self._accept_individual_step_succeed, req, res, timer)
        return defer


    def _accept_individual_step_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Accept union battle individual step award succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _accept_individual_step_failed(self, err, req, timer):
        logger.fatal("Accept union battle individual step award failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union battle individual step award failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def gain_battle_score(self, union_id, request):
        """增加胜场积分/战功
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalGainUnionBattleScoreReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_gain_battle_score, req, timer)
        defer.addErrback(self._gain_battle_score_failed, req, timer)
        return defer


    def _calc_gain_battle_score(self, data, req, timer):
        #增加联盟胜场积分
        if req.HasField("union_score"):
            season = data.season.get()
            season.gain_union_score(req.union_score)

        #增加成员战功
        if req.HasField("user_id") and req.HasField("individual_score"):
            member = member_business.find_member(data, req.user_id)
            if member is not None:
                member.gain_battle_score_immediate(req.individual_score)

        defer = DataBase().commit(data)
        defer.addCallback(self._gain_battle_score_succeed, req, timer)
        return defer


    def _gain_battle_score_succeed(self, data, req, timer):
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK
        response = res.SerializeToString()
        logger.notice("Gain battle score succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _gain_battle_score_failed(self, err, req, timer):
        logger.fatal("Gain battle score failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Gain battle score failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def force_update(self, union_id, request):
        """强制更新联盟战争状态
        """
        timer = Timer(union_id)

        req = internal_pb2.ForceUpdateUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_force_update, req, timer)
        defer.addCallback(self._force_update_succeed, req, timer)
        defer.addErrback(self._force_update_failed, req, timer)
        return defer


    def _calc_force_update(self, data, req, timer):
        if req.op == req.SEASON_FORWARD:
            #通知所有成员，进入下一个赛季
            for member in data.member_list.get_all(True):
                self._notice_forward_season(member.user_id, timer)

            #进入下一个赛季
            season = data.season.get()
            next_season_index = season.index + 1
            next_season_start_time = SeasonAllocator().calc(next_season_index)
            battle_business.forward_season(data, next_season_index, next_season_start_time)

        elif req.op == req.SEASON_RESET:
            #重置赛季
            season = data.season.get()
            battle_business.forward_season(data, season.index, season.start_time)

            #通知所有成员，进入下一个赛季
            for member in data.member_list.get_all(True):
                self._notice_forward_season(member.user_id, timer)

        elif req.op == req.SEASON_SYNC:
            #重置赛季
            (season_index, season_start_time) = SeasonAllocator().calc_now(timer.now)
            battle_business.forward_season(data, season_index, season_start_time)

            #通知所有成员，进入下一个赛季
            for member in data.member_list.get_all(True):
                self._notice_forward_season(member.user_id, timer)

        elif req.op == req.SEASON_FINISH:
            #赛季结束
            season = data.season.get()
            season.force_finish(timer.now)

        elif req.op == req.BATTLE_FORWARD:
            #通知所有成员，进入下一场战斗
            for member in data.member_list.get_all(True):
                if member.is_join_battle:
                    logger.debug("Notice forward battle[user_id=%d]" % member.user_id)
                    self._notice_forward_battle(member.user_id, timer)

            #进入下一场战争
            battle_business.forward_battle(data, timer.now)
            battle_business.update_battle(data, timer.now)

        elif req.op == req.BATTLE_FIGHT:
            #战争进入战斗阶段，改变战争开战时间
            battle = battle_business.get_current_battle(data, timer.now)
            battle.force_update_fight_time(timer.now)
            battle_business.update_battle(data, timer.now)

        elif req.op == req.BATTLE_CLOSE:
            #战争进入结束阶段，改变结束战斗时间
            battle = battle_business.get_current_battle(data, timer.now)
            battle.force_update_close_time(timer.now)
            battle_business.update_battle(data, timer.now)

        elif req.op == req.BATTLE_FINISH:
            #战争结束，改变战争结束时间
            battle = battle_business.get_current_battle(data, timer.now)
            battle.force_update_finish_time(timer.now)

        return DataBase().commit(data)


    def _force_update_succeed(self, data, req, timer):
        res = internal_pb2.ForceUpdateUnionBattleRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Force update battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _force_update_failed(self, err, req, timer):
        logger.fatal("Force update battle failed[reason=%s]" % err)
        res = internal_pb2.ForceUpdateUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Force update battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def try_forward_battle(self, union_id, request):
        """尝试进入下一场战争
        """
        timer = Timer(union_id)

        req = union_battle_pb2.TryForwardUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_try_forward_battle, req, timer)
        defer.addErrback(self._try_forward_battle_failed, req, timer)
        return defer


    def _calc_try_forward_battle(self, data, req, timer):
        res = union_battle_pb2.TryForwardUnionBattleRes()
        res.status = 0

        battle = battle_business.update_battle(data, timer.now, True)
        if battle.is_finished(timer.now):
            #战斗已结束
            res.enable = True
            if battle.is_initiator:
                res.attack_union_id = data.id
                res.defence_union_id = battle.rival_union_id
            else:
                res.attack_union_id = battle.rival_union_id
                res.defence_union_id = data.id

            union = data.union.get(True)
            season = data.season.get(True)
            pack.pack_battle_map_info(union, season, battle, [], res.unions.add(), timer)
            for member in data.member_list.get_all(True):
                pack.pack_battle_individual_info(member, res.users.add())

            #通知所有成员，进入下一场战斗
            for member in data.member_list.get_all(True):
                if member.is_join_battle:
                    self._notice_forward_battle(member.user_id, timer)

            #进入下一场战斗
            battle_business.forward_battle(data, timer.now)
        else:
            res.enable = False

        defer = DataBase().commit(data)
        defer.addCallback(self._try_forward_battle_succeed, req, res, timer)
        return defer


    def _notice_forward_battle(self, user_id, timer):
        app_req = internal_pb2.UnionBattleForwardReq()
        defer = GlobalObject().remote['app'].callRemote(
                "forward_union_battle", user_id, app_req.SerializeToString())
        defer.addCallback(self._notice_forward_battle_post, timer)
        return defer


    def _notice_forward_battle_post(self, app_response, timer):
        app_res = internal_pb2.UnionBattleForwardRes()
        app_res.ParseFromString(app_response)
        if app_res.status != 0:
            raise Exception("Notice forward battle res error")


    def _try_forward_battle_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Try forward battle succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _try_forward_battle_failed(self, err, req, timer):
        logger.fatal("Try forward battle failed[reason=%s]" % err)
        res = union_battle_pb2.TryForwardUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Try forward battle failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def try_forward_season(self, union_id, request):
        """尝试进入下一个赛季
        """
        timer = Timer(union_id)

        req = union_battle_pb2.TryForwardUnionBattleSeasonReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_try_forward_season, req, timer)
        defer.addErrback(self._try_forward_season_failed, req, timer)
        return defer


    def _calc_try_forward_season(self, data, req, timer):
        res = union_battle_pb2.TryForwardUnionBattleSeasonRes()
        res.status = 0

        season = data.season.get(True)
        battle = battle_business.update_battle(data, timer.now)
        if ((battle.stage == battle.BATTLE_STAGE_IDLE or
                battle.stage == battle.BATTLE_STAGE_INVALID or
                battle.is_finished(timer.now)) and
                timer.now >= season.get_finish_time()):
            #战斗结束，且赛季结束
            res.enable = True

            #通知所有成员，进入下一个赛季
            for member in data.member_list.get_all(True):
                self._notice_forward_season(member.user_id, timer)

            #进入下一个赛季
            season = data.season.get()
            next_season_index = season.index + 1
            next_season_start_time = SeasonAllocator().calc(next_season_index)
            battle_business.forward_season(data, next_season_index, next_season_start_time)

        else:
            res.enable = False

        defer = DataBase().commit(data)
        defer.addCallback(self._try_forward_season_succeed, req, res, timer)
        return defer


    def _notice_forward_season(self, user_id, timer):
        app_req = internal_pb2.UnionBattleForwardReq()
        defer = GlobalObject().remote['app'].callRemote(
                "forward_union_battle_season", user_id, app_req.SerializeToString())
        defer.addCallback(self._notice_forward_season_post, timer)
        return defer


    def _notice_forward_season_post(self, app_response, timer):
        app_res = internal_pb2.UnionBattleForwardRes()
        app_res.ParseFromString(app_response)
        if app_res.status != 0:
            raise Exception("Notice forward season res error")


    def _try_forward_season_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Try forward season succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _try_forward_season_failed(self, err, req, timer):
        logger.fatal("Try forward season failed[reason=%s]" % err)
        res = union_battle_pb2.TryForwardUnionBattleSeasonRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Try forward season failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def node_reward(self, union_id, request):
        """领取node公共奖励"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalUnionBattleNodeRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_node_reward, req, timer)
        defer.addErrback(self._node_reward_failed, req, timer)
        return defer

    def _calc_node_reward(self, data, req, timer):
        res = internal_union_pb2.InternalUnionBattleNodeRewardRes()
        res.status = 0
 
        node_id = UnionBattleMapNodeInfo.generate_id(data.id, req.node_index)
        node = data.battle_node_list.get(node_id)
        if battle_business.is_able_to_accept_node_reward(data, req.user_id, node):
            logger.debug("Accept battle box reward[union_id=%d][user_id=%d][node_index=%d]" % (
                    data.id, req.user_id, req.node_index))
            battle_business.accept_node_reward(data, req.user_id, req.user_name, req.icon_id,
                    node, timer.now)
        else:
            logger.debug("Query battle box reward[union_id=%d][user_id=%d][node_index=%d]" % (
                    data.id, req.user_id, req.node_index))
       
        reward_record = node.get_reward_record()
        res.box.id = req.node_index
        for user_id, user_name, icon_id, item_id, item_num, time in reward_record:
            member = res.box.members.add()
            member.user_id = user_id
            member.name = user_name
            member.headIconId = icon_id
            member.item_id = item_id
            member.item_num = item_num
            member.passedTime = timer.now - time

        defer = DataBase().commit(data)
        defer.addCallback(self._node_reward_succeed, req, res, timer)
        return defer

    def _node_reward_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Accept union battle box reward succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Accept union battle box reward failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _node_reward_failed(self, err, req, timer):
        logger.fatal("Accept union battle box reward failed[reason=%s]" % err)
        res = internal_union_pb2.InternalUnionBattleNodeRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union battle box reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def battle_box_reward(self, union_id, request):
        """领取大宝箱公共奖励"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalUnionBattleBoxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_battle_box_reward, req, timer)
        defer.addErrback(self._battle_box_reward_failed, req, timer)
        return defer

    def _calc_battle_box_reward(self, data, req, timer):
        res = internal_union_pb2.InternalUnionBattleBoxRes()
        res.status = 0

        battle = battle_business.get_current_battle(data, timer.now)
        if battle_business.is_able_to_accept_battle_box_reward(data, req.user_id, battle):
            logger.debug("Accept battle box reward[union_id=%d][user_id=%d]" % (
                    data.id, req.user_id))
            battle_business.accept_battle_box_reward(data, battle, req.user_id, req.user_name,
                    req.icon_id, timer.now)
        else:
            logger.debug("Query battle box reward[union_id=%d][user_id=%d]" % (
                    data.id, req.user_id))
        
        reward_record = battle.get_reward_record()
        res.box.id = 100 
        for user_id, user_name, icon_id, item_id, item_num, time in reward_record:
            member = res.box.members.add()
            member.user_id = user_id
            member.name = user_name
            member.headIconId = icon_id
            member.item_id = item_id
            member.item_num = item_num
            member.passedTime = timer.now - time

        defer = DataBase().commit(data)
        defer.addCallback(self._battle_box_reward_succeed, req, res, timer)
        return defer


    def _battle_box_reward_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Accept union battle box reward succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Accept union battle box reward failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response


    def _battle_box_reward_failed(self, err, req, timer):
        logger.fatal("Accept union battle box reward failed[reason=%s]" % err)
        res = internal_union_pb2.InternalUnionBattleBoxRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union battle box reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



