#coding:utf8
"""
Created on 2016-07-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争相关处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from proto import union_pb2
from proto import union_battle_pb2
from proto import internal_pb2
from proto import internal_union_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.team import TeamInfo
from app.data.item import ItemInfo
from app.data.hero import HeroInfo
from app.data.node import NodeInfo
from app.union_matcher import UnionMatcher
from app.union_patcher import UnionBattlePatcher
from app.union_member_matcher import UnionMemberMatcher
from app.union_ranker import UnionRanker
from app.union_recommender import UnionRecommender
from app.union_allocator import UnionAllocator
from app.business import account as account_business
from app.business import union_battle as union_battle_business
from app.business import appoint as appoint_business
from app.business import hero as hero_business
from app.business import item as item_business


class UnionBattleProcessor(object):

    def query(self, user_id, request):
        """查询战争情况
        """
        timer = Timer(user_id)

        req = union_battle_pb2.QueryUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_battle_pb2.QueryUnionBattleRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._query_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalQueryUnionBattleReq()
        union_req.user_id = data.id
        defer = GlobalObject().remote['gunion'].callRemote(
                "query_battle", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_query_result, data, req, timer)
        return defer


    def _calc_query_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union battle res error")

        res = union_battle_pb2.QueryUnionBattleRes()
        res.status = 0
        res.ret = union_res.ret
        if union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch(res.battle, union_res.battle, data, timer.now)
            defer.addCallback(self._calc_query_post, data, req, res, timer)
            return defer

        return self._calc_query_post(None, data, req, res, timer)


    def _calc_query_post(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query union battle failed[reason=%s]" % err)
        res = union_battle_pb2.QueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def drum(self, user_id, request):
        """擂鼓
        """
        timer = Timer(user_id)

        req = union_battle_pb2.DrumForUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_drum, req, timer)
        defer.addErrback(self._drum_failed, req, timer)
        return defer


    def _calc_drum(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_battle_pb2.DrumForUnionBattleRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._drum_succeed, req, res, timer)
            return defer

        cost_gold = 0
        if req.HasField("gold"):
            cost_gold = req.gold
        item = None
        if req.HasField("item"):
            item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
            item = data.item_list.get(item_id)

        if not union_battle_business.is_able_to_drum(data, item, cost_gold):
            raise Exception("Not able to drum")

        union_req = internal_union_pb2.InternalDrumForUnionBattleReq()
        union_req.user_id = data.id
        union_req.user_level = data.user.get(True).level
        defer = GlobalObject().remote['gunion'].callRemote(
                "drum_for_battle", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_drum_result, data, item, cost_gold, req, timer)
        return defer


    def _calc_drum_result(self, union_response, data, item, cost_gold, req, timer):
        union_res = internal_union_pb2.InternalDrumForUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union battle res error")

        res = union_battle_pb2.QueryUnionBattleRes()
        res.status = 0
        res.ret = union_res.ret

        if union_res.ret == union_pb2.UNION_OK:
            score = union_res.individual_battle_score_add
            union_battle_business.drum(data, item, cost_gold, score, timer.now)
            if req.HasField("item"):
                compare.check_item(data, req.item)

        if union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch(res.battle, union_res.battle, data, timer.now)
            defer.addCallback(self._calc_drum_post, data, req, res, timer)
            return defer

        return self._calc_drum_post(None, data, req, res, timer)


    def _calc_drum_post(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._drum_succeed, req, res, timer)
        return defer


    def _drum_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Drum for union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _drum_failed(self, err, req, timer):
        logger.fatal("Drum for union battle failed[reason=%s]" % err)
        res = union_battle_pb2.DrumForUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Drum for union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def launch(self, user_id, request, force = False):
        """发起联盟战争
        """
        timer = Timer(user_id)

        req = union_battle_pb2.QueryUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_launch, req, timer, force)
        defer.addErrback(self._launch_failed, req, timer)
        return defer


    def _calc_launch(self, data, req, timer, force):
        if not force:
            union = data.union.get(True)
            if not union.is_belong_to_target_union(req.union_id):
                res = union_battle_pb2.QueryUnionBattleRes()
                res.status = 0
                res.ret = union_pb2.UNION_NOT_MATCHED
                
                defer = DataBase().commit(data)
                defer.addCallback(self._launch_succeed, req, res, timer)
                return defer

        #发起战争
        union_req = internal_union_pb2.InternalQueryUnionBattleReq()
        union_req.user_id = data.id
        if not force:
            defer = GlobalObject().remote['gunion'].callRemote(
                    "launch_battle", req.union_id, union_req.SerializeToString())
        else:
            defer = GlobalObject().remote['gunion'].callRemote(
                    "launch_battle_force", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_launch_result, data, req, timer)
        return defer


    def _calc_launch_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union battle res error")

        res = union_battle_pb2.QueryUnionBattleRes()
        res.status = 0
        res.ret = union_res.ret

        if union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch(res.battle, union_res.battle, data, timer.now)
            defer.addCallback(self._calc_launch_post, data, req, res, timer)
            return defer

        return self._calc_launch_post(None, data, req, res, timer)


    def _calc_launch_post(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._launch_succeed, req, res, timer)
        return defer


    def _launch_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Launch union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _launch_failed(self, err, req, timer):
        logger.fatal("Launch union battle failed[reason=%s]" % err)
        res = union_battle_pb2.QueryUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Launch union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def launch_two(self, user_id, request):
        """发起两个指定联盟的战争
        """
        timer = Timer(user_id)

        req = internal_union_pb2.InternalLaunchUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_launch_new, req, timer)
        defer.addErrback(self._launch_new_failed, req, timer)
        return defer


    def _calc_launch_new(self, data, req, timer):
        #发起战争
        defer = GlobalObject().remote['gunion'].callRemote(
                "launch_battle_two", req.rival_union_id, req.SerializeToString())
        defer.addCallback(self._calc_launch_new_result, data, req, timer)
        return defer


    def _calc_launch_new_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalLaunchUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Launch two union battle res error")

        #return self._calc_launch_post_new(None, data, req, union_res, timer)
        return self._launch_new_succeed(data, req, union_res, timer)


    def _calc_launch_post_new(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._launch_new_succeed, req, res, timer)
        return defer


    def _launch_new_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Launch two union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _launch_new_failed(self, err, req, timer):
        logger.fatal("Launch two union battle failed[reason=%s]" % err)
        res = internal_union_pb2.InternalLaunchUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Launch two union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def deploy(self, user_id, request):
        """部署联盟战争节点防御
        """
        timer = Timer(user_id)

        req = union_battle_pb2.DeployUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_deploy, req, timer)
        defer.addErrback(self._deploy_failed, req, timer)
        return defer


    def _calc_deploy(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #玩家不属于联盟
            res = union_battle_pb2.DeployUnionBattleRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._deploy_succeed, req, res, timer)
            return defer

        #检查队伍是否合法
        teams = []
        for team_info in req.teams:
            team_id = TeamInfo.generate_id(data.id, team_info.index)
            team = data.team_list.get(team_id, True)
            teams.append(team)
        if not union_battle_business.is_able_to_deploy(data, req.node_index, teams):
            raise Exception("Team deploy invalid")

        #部署防御
        union_req = internal_union_pb2.InternalDeployUnionBattleReq()
        user = data.user.get(True)
        union_req.user_id = data.id
        union_req.defender_user_id = data.id
        union_req.defender_user_name = user.get_readable_name()
        union_req.defender_user_icon = user.icon_id
        union_req.defender_user_level = user.level
        union_req.node_index = req.node_index
        for team in teams:
            team_msg = union_req.teams.add()
            team_msg.index = team.index
            for hero_id in team.get_heroes():
                if hero_id != 0:
                    hero = data.hero_list.get(hero_id, True)
                    pack.pack_hero_info(hero, team_msg.heroes.add(), timer.now)
        for tech in data.technology_list.get_all(True):
            if tech.is_battle_technology() and not tech.is_upgrade:
                union_req.battle_tech_ids.append(tech.basic_id)

        defer = GlobalObject().remote['gunion'].callRemote(
                "deploy_battle", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_deploy_result, data, req, timer)
        return defer


    def _calc_deploy_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union battle res error")

        if union_res.ret == union_pb2.UNION_OK:
            #锁定所有派出的队伍
            teams = []
            for team_info in req.teams:
                team_id = TeamInfo.generate_id(data.id, team_info.index)
                team = data.team_list.get(team_id)
                teams.append(team)
            union_battle_business.deploy_for_union_battle(data, req.node_index, teams)

        res = union_battle_pb2.DeployUnionBattleRes()
        res.status = 0
        res.ret = union_res.ret
        if union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch(res.battle, union_res.battle, data, timer.now)
            defer.addCallback(self._calc_deploy_post, data, req, res, timer)
            return defer

        return self._calc_deploy_post(None, data, req, res, timer)


    def _calc_deploy_post(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._deploy_succeed, req, res, timer)
        return defer


    def _deploy_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Deploy union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _deploy_failed(self, err, req, timer):
        logger.fatal("Deploy union battle failed[reason=%s]" % err)
        res = union_battle_pb2.DeployUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Deploy union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def deploy_force(self, user_id, request):
        """部署联盟战争节点防御
        """
        timer = Timer(user_id)

        req = union_battle_pb2.DeployUnionBattleForceReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_deploy_force, request, req, timer)
        defer.addErrback(self._deploy_force_failed, req, timer)
        return defer


    def _calc_deploy_force(self, data, request, req, timer):
        defer = GlobalObject().root.callChild("portal", "forward_union_battle_deploy_force", req.user_id, request)
        defer.addCallback(self._calc_deploy_force_result, data, req, timer)
        return defer


    def _calc_deploy_force_result(self, response, data, req, timer):
        union_res = union_battle_pb2.DeployUnionBattleForceRes()
        union_res.ParseFromString(response)

        if union_res.status != 0:
            raise Exception("Deploy force union battle res error")

        res = union_battle_pb2.DeployUnionBattleForceRes()
        res.status = 0
        res.ret = union_res.ret 
        defer = DataBase().commit(data)
        defer.addCallback(self._deploy_force_succeed, req, res, timer)
        return defer


    def _deploy_force_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Deploy force union battle force succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _deploy_force_failed(self, err, req, timer):
        logger.fatal("Deploy force union battle failed[reason=%s]" % err)
        res = union_battle_pb2.DeployUnionBattleForceRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Deploy force union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_deploy_force(self, user_id, request):
        """部署联盟战争节点防御,不需要由玩家选择
        """
        timer = Timer(user_id)

        req = union_battle_pb2.DeployUnionBattleForceReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_deploy_force, req, timer)
        defer.addErrback(self._receive_deploy_failed, req, timer)
        return defer


    def _calc_receive_deploy_force(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #玩家不属于联盟
            res = union_battle_pb2.DeployUnionBattleForceRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._receive_deploy_succeed, req, res, timer)
            return defer

        battle_score = data.battle_score.get()
        teams_index = battle_score.get_powerful_teams_id()[0:3] #取前三队
        teams = []
        for team_index in teams_index:
            team_id = TeamInfo.generate_id(data.id, team_index)
            team = data.team_list.get(team_id, True)
            teams.append(team)
        if not union_battle_business.is_able_to_deploy(data, req.node_index, teams, True):
            raise Exception("Team deploy invalid")

        union_req = internal_union_pb2.InternalDeployUnionBattleReq()
        user = data.user.get(True)
        union_req.user_id = data.id
        union_req.defender_user_id = data.id
        union_req.defender_user_name = user.get_readable_name()
        union_req.defender_user_icon = user.icon_id
        union_req.defender_user_level = user.level
        union_req.node_index = req.node_index
        for team in teams:
            team_msg = union_req.teams.add()
            team_msg.index = team.index
            for hero_id in team.get_heroes():
                if hero_id != 0:
                    hero = data.hero_list.get(hero_id, True)
                    pack.pack_hero_info(hero, team_msg.heroes.add(), timer.now)
        for tech in data.technology_list.get_all(True):
            if tech.is_battle_technology() and not tech.is_upgrade:
                union_req.battle_tech_ids.append(tech.basic_id)

        defer = GlobalObject().remote['gunion'].callRemote(
                "deploy_battle", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_receive_deploy_result, data, req, timer)
        return defer


    def _calc_receive_deploy_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Receive deploy union battle res error")

        #不锁定所有派出的队伍

        res = union_battle_pb2.DeployUnionBattleForceRes()
        res.status = 0
        res.ret = union_res.ret
        if union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch(res.battle, union_res.battle, data, timer.now)
            defer.addCallback(self._calc_deploy_post, data, req, res, timer)
            return defer

        return self._calc_deploy_post(None, data, req, res, timer)


    def _calc_receive_deploy_post(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._receive_deploy_succeed, req, res, timer)
        return defer


    def _receive_deploy_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Receive deploy union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        DataBase().clear_data(data)
        return response


    def _receive_deploy_failed(self, err, req, timer):
        logger.fatal("Receive deploy union battle failed[reason=%s]" % err)
        res = union_battle_pb2.DeployUnionBattleForceRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive deploy union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def cancel_deploy(self, user_id, request):
        """取消部署
        盟主和副盟主可以取消其他成员的部署
        """
        timer = Timer(user_id)

        req = union_battle_pb2.DeployUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_cancel_deploy, req, timer)
        defer.addErrback(self._cancel_deploy_failed, req, timer)
        return defer


    def _calc_cancel_deploy(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #玩家不属于联盟
            res = union_battle_pb2.DeployUnionBattleRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._cancel_deploy_succeed, req, res, timer)
            return defer

        #部署防御
        union_req = internal_union_pb2.InternalDeployUnionBattleReq()
        user = data.user.get(True)
        union_req.user_id = data.id
        union_req.node_index = req.node_index
        union_req.defender_user_id = req.user_id
        defer = GlobalObject().remote['gunion'].callRemote(
                "cancel_deploy_battle", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_cancel_deploy_result, data, req, timer)
        return defer


    def _calc_cancel_deploy_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union battle res error")

        res = union_battle_pb2.DeployUnionBattleRes()
        res.status = 0
        res.ret = union_res.ret
        if union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch(res.battle, union_res.battle, data, timer.now)
            defer.addCallback(self._calc_cancel_deploy_post, data, req, res, timer)
            return defer

        return self._calc_cancel_deploy_post(None, data, req, res, timer)


    def _calc_cancel_deploy_post(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._cancel_deploy_succeed, req, res, timer)
        return defer


    def _cancel_deploy_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Cancel deploy union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _cancel_deploy_failed(self, err, req, timer):
        logger.fatal("Cancel deploy union battle failed[reason=%s]" % err)
        res = union_battle_pb2.DeployUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Cancel deploy union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start(self, user_id, request):
        """开始战斗
        """
        timer = Timer(user_id)

        req = union_battle_pb2.StartUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start, req, timer)
        defer.addErrback(self._start_failed, req, timer)
        return defer


    def _calc_start(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #玩家不属于联盟
            res = union_battle_pb2.StartUnionBattleRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        #参战队伍 & 英雄
        teams = []
        heroes = []
        for team_info in req.battle.attack_teams:
            team_id = TeamInfo.generate_id(data.id, team_info.index)
            team = data.team_list.get(team_id)
            if team is None:
                continue
            teams.append(team)

            for hero_id in team.get_heroes():
                if hero_id != 0:
                    hero = data.hero_list.get(hero_id)
                    heroes.append(hero)

        #检查是否可以开战
        if not union_battle_business.is_able_to_start_battle(
                data, teams, heroes, timer.now, req.cost_gold):
            raise Exception("Not able to start battle")

        #开战，请求本方联盟核实信息
        user = data.user.get(True)
        union_req = internal_union_pb2.InternalStartUnionBattleReq()
        union_req.is_attack_side = True
        union_req.attacker_user_id = data.id

        defer = GlobalObject().remote['gunion'].callRemote(
                "start_battle", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_start_result, data, teams, heroes,req, timer)
        return defer


    def _calc_start_result(self, union_response, data, teams, heroes,req, timer):
        union_res = internal_union_pb2.InternalStartUnionBattleRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Query union battle res error")

        if union_res.ret != union_pb2.UNION_OK:
            res = union_battle_pb2.StartUnionBattleRes()
            res.status = 0
            res.ret = union_res.ret
            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        #开战，进攻防守方的联盟地图
        user = data.user.get(True)
        rival_union_req = internal_union_pb2.InternalStartUnionBattleReq()
        rival_union_req.is_attack_side = False
        rival_union_req.node_index = req.node_index
        rival_union_req.node_level = req.node_level
        rival_union_req.attacker_user_id = data.id
        rival_union_req.attacker_user_name = user.get_readable_name()
        rival_union_req.attacker_user_icon = user.icon_id
        total_soldier_num = union_battle_business.calc_soldier_consume(heroes)
        rival_union_req.attacker_soldier_num = total_soldier_num
        rival_union_req.defender_user_id = req.rival_user_id

        defer = GlobalObject().remote['gunion'].callRemote(
                "start_battle", req.rival_union_id, rival_union_req.SerializeToString())
        defer.addCallback(self._calc_rival_start_result,
                union_res, data, teams, heroes, req, timer)
        return defer


    def _calc_rival_start_result(self, union_response,
            union_res, data, teams, heroes, req, timer):
        rival_union_res = internal_union_pb2.InternalStartUnionBattleRes()
        rival_union_res.ParseFromString(union_response)
        if rival_union_res.status != 0:
            raise Exception("Query rival union battle res error")

        res = union_battle_pb2.StartUnionBattleRes()
        res.status = 0
        res.ret = rival_union_res.ret

        if res.ret == union_pb2.UNION_OK:
            #开战逻辑
            if not union_battle_business.start_battle(
                    data, teams, heroes, req.rival_user_id, rival_union_res.rival,
                    timer.now, req.cost_gold > 0):
                raise Exception("Start battle failed")

            #补充响应
            res.unlock_time = union_res.unlock_time
            union = data.union.get(True)
            node_id = NodeInfo.generate_id(data.id, union.get_battle_mapping_node_basic_id())
            battle = data.battle_list.get(node_id, True)
            pack.pack_battle_reward_info(battle, res.reward)
            pack.pack_resource_info(data.resource.get(True), res.resource)
            conscript_list = data.conscript_list.get_all(True)
            for conscript in conscript_list:
                pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)

        if rival_union_res.HasField("battle") and union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch_by_both_message(
                    res.battle, union_res.battle, rival_union_res.battle, data, timer.now)
            defer.addCallback(self._calc_start_post, data, req, res, timer)
            return defer

        return self._calc_start_post(None, data, req, res, timer)


    def _calc_start_post(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._start_succeed, req, res, timer)
        return defer


    def _start_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Start union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _start_failed(self, err, req, timer):
        logger.fatal("Start union battle failed[reason=%s]" % err)
        res = union_battle_pb2.StartUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish(self, user_id, request):
        """结束战斗
        """
        timer = Timer(user_id)

        req = union_battle_pb2.FinishUnionBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish, req, timer)
        defer.addErrback(self._finish_failed, req, timer)
        return defer


    def _calc_finish(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #玩家不属于联盟
            res = union_battle_pb2.FinishUnionBattleRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._finish_succeed, req, res, timer)
            return defer

        skip = False
        if req.HasField("is_skip") and req.is_skip == True:
            #跳过战斗
            skip = True
        
        union = data.union.get()
        node_id = NodeInfo.generate_id(data.id, union.get_battle_mapping_node_basic_id())
        battle = data.battle_list.get(node_id)
        rival = data.rival_list.get(battle.rival_id, True)
        teams = []
        for team_index in battle.get_battle_team():
            team_id = TeamInfo.generate_id(data.id, team_index)
            teams.append(data.team_list.get(team_id))

        heroes = []
        for hero_id in battle.get_battle_hero():
            hero = hero_business.get_hero_by_id(data, hero_id)
            heroes.append(hero)

        #存活兵力信息
        if skip:
            (win, own_soldier_info, enemy_soldier_info) = \
                appoint_business.calc_battle_result(data, battle, rival, teams, heroes)
        else:
            own_soldier_info = []
            for result in req.battle.attack_heroes:
                hero_basic_id = result.hero.basic_id
                hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
                hero = data.hero_list.get(hero_id, True)
                own_soldier_info.append((
                    hero.soldier_basic_id,
                    hero.soldier_level,
                    result.soldier_survival))
            enemy_soldier_info = []
            for result in req.battle.defence_heroes:
                enemy_soldier_info.append((
                    result.hero.soldier_basic_id,
                    result.hero.soldier_level,
                    result.soldier_survival))

            if req.battle.result == req.battle.WIN:
                win = True
            else:
                win = False

        #检查是否可以结束战斗
        if not union_battle_business.is_able_to_finish_battle(data, timer.now):
            raise Exception("Not able to finish battle")

        #结束战斗，向防守方联盟发送结束请求
        user = data.user.get(True)
        union_req = internal_union_pb2.InternalFinishUnionBattleReq()
        union_req.is_attack_side = False
        union_req.node_index = req.node_index
        union_req.node_level = req.node_level
        union_req.is_attacker_win = win
        union_req.attacker_user_id = data.id
        union_req.attacker_user_level = user.level
        union_req.defender_user_id = req.rival_user_id
        union_req.attacker_kills = union_battle_business.calc_kills(enemy_soldier_info)
        union_req.defender_kills = union_battle_business.calc_kills(own_soldier_info)

        defer = GlobalObject().remote['gunion'].callRemote(
                "finish_battle", req.rival_union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_rival_finish_result, union_req,
                win, own_soldier_info, enemy_soldier_info, data, skip, heroes, req, timer)
        return defer


    def _calc_rival_finish_result(self, union_response, union_req,
            win, own_soldier_info, enemy_soldier_info, data, skip, heroes, req, timer):
        union_res = internal_union_pb2.InternalFinishUnionBattleRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Query union battle res error")

        if union_res.ret != union_pb2.UNION_OK:
            #联盟校验错误，算战斗失败
            win = False

        #结束战斗，向己方联盟发送结束请求
        union_req.is_attack_side = True
        union_req.is_attacker_win = win
        union_req.node_level_after_battle = union_res.node_level
        union_req.is_node_broken_after_battle = union_res.is_node_broken_after_battle
        union_req.battle_stage = union_res.battle_stage
        defer = GlobalObject().remote['gunion'].callRemote(
                "finish_battle", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_own_finish_result, union_res,
                win, own_soldier_info, enemy_soldier_info, data, skip, heroes, req, timer)
        return defer


    def _calc_own_finish_result(self, union_response, rival_union_res,
            win, own_soldier_info, enemy_soldier_info, data, skip, heroes, req, timer):
        union_res = internal_union_pb2.InternalFinishUnionBattleRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Query union battle res error")

        score = 0
        if union_res.HasField("individual_battle_score_add"):
            score = union_res.individual_battle_score_add

        #结束战斗
        if win:
            if not union_battle_business.win_battle(
                    data, enemy_soldier_info, own_soldier_info, score, timer.now):
                raise Exception("Win battle failed")
        else:
            if not union_battle_business.lose_battle(
                    data, enemy_soldier_info, own_soldier_info, score, timer.now):
                raise Exception("Lose battle failed")

        #检查请求
        if win:
            compare.check_user(data, req.monarch, with_level = True)
            for info in req.battle.attack_heroes:
                compare.check_hero(data, info.hero, with_level = True)
            for item_info in req.items:
                compare.check_item(data, item_info)

        res = union_battle_pb2.FinishUnionBattleRes()
        res.status = 0
        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
        else:
            res.ret = rival_union_res.ret

        if skip:
            pack.pack_monarch_info(data.user.get(True), res.monarch)
            if win:
                res.battle_output.result = battle_pb2.BattleOutputInfo.WIN
            else:
                res.battle_output.result = battle_pb2.BattleOutputInfo.LOSE

            for i, hero in enumerate(heroes):
                attack_hero = res.battle_output.attack_heroes.add()
                pack.pack_hero_info(hero, attack_hero.hero, timer.now)
                attack_hero.soldier_survival = own_soldier_info[i][2]

        if union_res.HasField("battle") and rival_union_res.HasField("battle"):
            defer = UnionBattlePatcher().patch_by_both_message(res.battle,
                    union_res.battle, rival_union_res.battle, data, timer.now)
            defer.addCallback(self._calc_finish_post, data, req, res, timer)
            return defer

        return self._calc_finish_post(None, data, req, res, timer)


    def _calc_finish_post(self, patcher, data, req, res, timer):
        pack.pack_resource_info(data.resource.get(True), res.resource)
        for conscript in data.conscript_list.get_all(True):
            pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_succeed, req, res, timer)
        return defer


    def _finish_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Finish union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_failed(self, err, req, timer):
        logger.fatal("Finish union battle failed[reason=%s]" % err)
        res = union_battle_pb2.FinishUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def battle_node_reward(self, user_id, request):
        """领取node宝箱奖励"""
        timer = Timer(user_id)

        req = union_battle_pb2.QueryUnionBattleBoxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_battle_node_reward, req, timer)
        defer.addErrback(self._battle_node_reward_failed, req, timer)
        return defer


    def _calc_battle_node_reward(self, data, req, timer):
        union = data.union.get(True)
        if union is None or not union.is_belong_to_target_union(req.union_id):
            res = union_battle_pb2.QueryUnionBattleBoxRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._battle_node_reward_succeed(data, req, res, timer)

        user = data.user.get(True)
        union_req = internal_union_pb2.InternalUnionBattleNodeRewardReq()
        union_req.user_id = data.id
        union_req.user_name = user.name
        union_req.icon_id = user.icon_id
        union_req.node_index = req.box_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "accept_battle_node_reward", req.rival_union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_battle_node_reward_result, data, req, timer)
        return defer

    def _calc_battle_node_reward_result(self, union_response, data, req, timer):
        res = union_battle_pb2.QueryUnionBattleBoxRes()
        res.status = 0

        union_res = internal_union_pb2.InternalUnionBattleNodeRewardRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("accept union battle node reward failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._battle_node_reward_succeed(data, req, res, timer)

        item_id = 0
        item_num = 0
        for member in union_res.box.members:
            if member.user_id == data.id:
                item_id = member.item_id
                item_num = member.item_num

        if item_id != 0:
            item_business.gain_item(data, [(item_id, item_num)], "node reward", log_formater.UNION_BATTLE)

        res.ret = union_pb2.UNION_OK
        res.box.CopyFrom(union_res.box)

        defer = DataBase().commit(data)
        defer.addCallback(self._battle_node_reward_succeed, req, res, timer)
        return defer


    def _battle_node_reward_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Accept union battle node box reward succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Accept union battle node box reward failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response


    def _battle_node_reward_failed(self, err, req, timer):
        logger.fatal("Accept union battle node box reward failed[reason=%s]" % err)
        res = union_battle_pb2.QueryUnionBattleBoxRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union battle node box reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def accept_union_battle_box(self, user_id, request):
        """领取联盟战大宝箱奖励"""
        timer = Timer(user_id)

        req = union_battle_pb2.QueryUnionBattleBoxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_accept_union_battle_box, req, timer)
        defer.addErrback(self._accept_union_battle_box_failed, req, timer)
        return defer


    def _calc_accept_union_battle_box(self, data, req, timer):
        union = data.union.get(True)
        if union is None or not union.is_belong_to_target_union(req.union_id):
            res = union_battle_pb2.QueryUnionBattleBoxRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._accept_union_battle_box_succeed(data, req, res, timer)

        user = data.user.get(True)
        union_req = internal_union_pb2.InternalUnionBattleBoxReq()
        union_req.user_id = data.id
        union_req.user_name = user.name
        union_req.icon_id = user.icon_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "accept_union_battle_box_succeed", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_accept_union_battle_box_result, data, req, timer)
        return defer

    def _calc_accept_union_battle_box_result(self, union_response, data, req, timer):
        res = union_battle_pb2.QueryUnionBattleBoxRes()
        res.status = 0

        union_res = internal_union_pb2.InternalUnionBattleBoxRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("accept union battle box failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._accept_union_battle_box_succeed(data, req, res, timer)

        item_id = 0
        item_num = 0
        for member in union_res.box.members:
            if member.user_id == data.id:
                item_id = member.item_id
                item_num = member.item_num

        if item_id != 0:
            item_business.gain_item(data, [(item_id, item_num)], "union battle", log_formater.UNION_BATTLE)

        res.ret = union_pb2.UNION_OK
        res.box.CopyFrom(union_res.box)

        defer = DataBase().commit(data)
        defer.addCallback(self._accept_union_battle_box_succeed, req, res, timer)
        return defer


    def _accept_union_battle_box_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Accept union battle box succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Accept union battle box failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response


    def _accept_union_battle_box_failed(self, err, req, timer):
        logger.fatal("Accept union battle box failed[reason=%s]" % err)
        res = union_battle_pb2.QueryUnionBattleBoxRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union battle box failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


