#coding:utf8
"""
Created on 2017-03-01
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟boss处理流程
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from utils.timer import Timer
from proto import union_pb2
from proto import union_boss_pb2
from proto import internal_union_pb2
from proto import boss_pb2
from proto import battle_pb2
from datalib.global_data import DataBase
from app import pack
from app.data.team import TeamInfo
from app import log_formater
from app.data.unionboss import UserUnionBossInfo
from app.data.union import UserUnionInfo
from app.data.node import NodeInfo
from app.business import hero as hero_business
from app.business import union_boss as union_boss_business
from app.business import battle as battle_business
from app.business import item as item_business
from app import basic_view
from app import compare
from utils import utils
import datetime

class UnionBossProcessor(object):
    """联盟boss"""

    def query(self, user_id, request):
        """查询联盟boss"""
        timer = Timer(user_id)

        req = union_boss_pb2.QueryUnionBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        res = union_boss_pb2.QueryUnionBossRes()
        res.status = 0

        union = data.union.get(True)
        if union is None or not union.is_belong_to_target_union(req.union_id):
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._query_succeed(data, req, res, timer)

        union_req = internal_union_pb2.InternalQueryUnionBossReq()
        union_req.user_id = data.id

        union = data.union.get(True)
        defer = GlobalObject().remote['gunion'].callRemote(
                "query_unionboss", union.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_query_result, data, req, res, timer)
        return defer

    def _calc_query_result(self, union_response, data, req, res, timer):
        union_res = internal_union_pb2.InternalQueryUnionBossRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union boss failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._query_succeed(data, req, res, timer)

        union_boss_business.try_update_union_boss(data, union_res.bosses_id, union_res.last_update_time)

        if len(union_res.bosses_id) != 0:
            self._pack_unionboss(data, union_res, res.union_boss, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer
    
    def _pack_unionboss(self, data, union_res, message, now):
        """打包unionboss信息"""
        attack_boss = union_boss_business.get_boss_by_id(data, union_res.attack_id, True)
        user = data.user.get(True)
        union = data.union.get(True)

        if union_res.attack_id != 0:
            pack.pack_unionboss_info(attack_boss, user, message.current_boss.IN_BATTLE,
                    union_res.attack_total_soldier_num, union_res.attack_soldier_num, 
                    message.current_boss, now)

        #end_time = union.union_boss_last_update_time + int(datetime.timedelta(days=3).total_seconds())
        end_time = union.union_boss_last_update_time + 3 * utils.SECONDS_OF_DAY
        message.remain_time = end_time - now
        
        bosses_id = [boss_id for boss_id in union_res.bosses_id]
        if union_res.attack_id == 0:
            message.current_boss_step = 10
        else:
            message.current_boss_step = bosses_id.index(union_res.attack_id)
        message.attack_num = union.get_remain_union_boss_attack_num()
        message.refresh_num = union.union_boss_reset_num
        message.score = union.union_boss_score
        
        for boss_id in union_res.bosses_id:
            boss = union_boss_business.get_boss_by_id(data, boss_id, True)
            message.boss_hero_id.append(boss.boss_hero_id())

        for box in union_res.boxes:
            message.boxes.add().CopyFrom(box)

        for step in union.get_union_boss_box_steps():
            message.accepted_box_steps.append(step)

    def _query_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Query union boss succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Query union boss failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _query_failed(self, err, req, timer):
        logger.fatal("Query union boss failed[reason=%s]" % err)
        res = union_boss_pb2.QueryUnionBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union boss failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def start_battle(self, user_id, request):
        """开始联盟boss战斗"""
        timer = Timer(user_id)

        req = union_boss_pb2.StartUnionBossBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_battle, req, timer)
        defer.addErrback(self._start_battle_failed, req, timer)
        return defer

    def _calc_start_battle(self, data, req, timer):
        res = union_boss_pb2.StartUnionBossBattleRes()
        res.status = 0
        
        union = data.union.get(True)
        if union is None or not union.is_belong_to_target_union(req.union_id):
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._start_battle_succeed(data, req, res, timer)

        #请求联盟验证并模块获取boss信息
        union_req = internal_union_pb2.InternalSyncBossReq()
        union_req.user_id = data.id
        union_req.boss_step = req.boss_step

        defer = GlobalObject().remote['gunion'].callRemote(
            "sync_unionboss", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_start_battle_result, data, req, timer)
        return defer


    def _calc_start_battle_result(self, union_response, data, req, timer):
        res = union_boss_pb2.StartUnionBossBattleRes()
        res.status = 0

        union_res = internal_union_pb2.InternalSyncBossRes()
        union_res.ParseFromString(union_response)
        
        if union_res.status != 0:
            raise Exception("Start union boss battle failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._start_battle_succeed(data, req, res, timer)

        if union_res.boss_status != UserUnionBossInfo.BATTLE:
            if union_res.boss_status == UserUnionBossInfo.INACTIVE:
                res.ret = union_pb2.UNION_BOSS_INACTIVE
            else:
                res.ret = union_pb2.UNION_BOSS_KILLED
            return self._start_battle_succeed(data, req, res, timer)

        boss_id = union_res.boss_id
        array_index = req.world_boss_choose_index    #选择boss队伍的index

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

        (ret, battle_ret) = union_boss_business.start_battle(data, boss_id, 
                array_index, teams, heroes, timer.now, req.gold)
        if ret != union_pb2.UNION_OK or battle_ret != battle_pb2.BATTLE_OK:
            res.ret = ret
            res.battle_ret = battle_ret
            return self._start_battle_succeed(data, req, res, timer)

        node_id = NodeInfo.generate_id(data.id, UserUnionInfo.get_union_boss_node_basic_id())
        battle = data.battle_list.get(node_id, True)
        resource = data.resource.get(True)
        pack.pack_battle_reward_info(battle, res.reward)
        pack.pack_resource_info(resource, res.resource)
        conscript_list = data.conscript_list.get_all(True)
        for conscript in conscript_list:
            pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)

        res.ret = union_pb2.UNION_OK
        res.battle_ret = battle_pb2.BATTLE_OK
        defer = DataBase().commit(data)
        defer.addCallback(self._start_battle_succeed, req, res, timer)
        return defer

    def _start_battle_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK and res.battle_ret == battle_pb2.BATTLE_OK:
            logger.notice("Start union boss battle succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Start union boss battle failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _start_battle_failed(self, err, req, timer):
        logger.fatal("Start union boss battle failed[reason=%s]" % err)
        res = union_boss_pb2.StartUnionBossBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start union boss battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_battle(self, user_id, request):
        """结束boss战"""
        timer = Timer(user_id)

        req = union_boss_pb2.FinishUnionBossBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_battle, req, timer)
        defer.addErrback(self._finish_battle_failed, req, timer)
        return defer

    def _calc_finish_battle(self, data, req, timer):
        #兵力信息
        res = union_boss_pb2.FinishUnionBossBattleRes()
        res.status = 0

        own_soldier_info = []
        for result in req.battle.attack_heroes:
            hero_basic_id = result.hero.basic_id
            hero = hero_business.get_hero_by_id(data, hero_basic_id)
            own_soldier_info.append((
                hero.soldier_basic_id,
                hero.soldier_level,
                result.soldier_survival))
        enemy_soldier_info = []
        if req.battle.HasField("relive_times"):
            for i in range(req.battle.relive_times):
                for result in req.battle.defence_heroes:
                    #攻打世界boss时有重生逻辑，实际杀敌会更多
                    enemy_soldier_info.append((
                        result.hero.soldier_basic_id,
                        result.hero.soldier_level,
                        0))
                        
        for result in req.battle.defence_heroes:
            enemy_soldier_info.append((
                result.hero.soldier_basic_id,
                result.hero.soldier_level,
                result.soldier_survival))

        #计算杀敌数
        kill_soldier_num = battle_business._calc_number_of_death(enemy_soldier_info)

        node_id = NodeInfo.generate_id(data.id, UserUnionInfo.get_union_boss_node_basic_id())
        node = data.node_list.get(node_id)
        rival = data.rival_list.get(node_id)
        boss = union_boss_business.get_boss_by_id(data, rival.rival_id)
        
        change_nodes = []
        new_items = []
        new_mails = []
        new_arena_records = []
        if req.battle.result == req.battle.WIN:
            win = True
            if not battle_business.win_battle(
                data, node, enemy_soldier_info, own_soldier_info,
                change_nodes, timer.now, new_arena_records, is_unionboss=True):
                raise Exception("win union boss battle failed")
        else:
            win = False
            if not battle_business.lose_battle(
                data, node, timer.now, enemy_soldier_info, own_soldier_info,
                change_nodes, new_items, new_mails, new_arena_records):
                raise Exception("loss union boss battle failed")

        union_boss_business.finish_battle(data, boss, win, kill_soldier_num)

        if req.battle.result == req.battle.WIN:
            if not compare.check_user_r(data, req.monarch, with_level=True):
                res.battle_ret = union_pb2.BATTLE_MONARCH_ERROR
                return self._finish_battle_succeed(data, req, res, timer)

            for info in req.battle.attack_heroes:
                if not compare.check_hero_r(data, info.hero, with_level=True):
                    res.battle_ret = union_pb2.BATTLE_HERO_ERROR
                    return self._finish_battle_succeed(data, req, res, timer)
            
            for item_info in req.items:
                compare.check_item(data, item_info)

        #请求gunion模块
        user = data.user.get(True)
        union_req = internal_union_pb2.InternalSyncBossReq()
        union_req.user_id = data.id
        union_req.user_name = user.name
        union_req.boss_id = boss.boss_id
        union_req.kill_addition = kill_soldier_num

        defer = GlobalObject().remote['gunion'].callRemote(
            "sync_unionboss", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_finish_battle_result, data, req,
                own_soldier_info, enemy_soldier_info, kill_soldier_num, boss, timer)
        return defer

    def _calc_finish_battle_result(self, union_response, data, req, 
            own_soldier_info, enemy_soldier_info, kill_soldier_num, boss, timer):
        res = union_boss_pb2.FinishUnionBossBattleRes()
        res.status = 0

        union_res = internal_union_pb2.InternalSyncBossRes()
        union_res.ParseFromString(union_response)
        
        if union_res.status != 0:
            raise Exception("finish union boss battle failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._finish_battle_succeed(data, req, res, timer)

        user = data.user.get(True)
        union = data.union.get(True)

        res.ret = union_pb2.UNION_OK
        res.battle_ret = battle_pb2.BATTLE_OK
        pack.pack_unionboss_info(boss, user, union_res.boss_status,
                union_res.total_soldier_num, union_res.current_soldier_num,
                res.boss, timer.now)
        
        conscript_list = data.conscript_list.get_all(True)
        for conscript in conscript_list:
            pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)
        
        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_battle_succeed, req, res, timer)
        return defer

    def _finish_battle_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK and res.battle_ret == battle_pb2.BATTLE_OK:
            logger.notice("Finish union boss battle succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Finish union boss battle failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _finish_battle_failed(self, err, req, timer):
        logger.fatal("Finish union boss battle failed[reason=%s]" % err)
        res = union_boss_pb2.FinishUnionBossBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish union boss battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def score_reward(self, user_id, request):
        """领取个人战功奖励"""
        timer = Timer(user_id)

        req = union_boss_pb2.AcceptUnionBossIndividualsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_score_reward, req, timer)
        defer.addErrback(self._score_reward_succeed, req, timer)
        return defer

    def _calc_score_reward(self, data, req, timer):
        res = union_boss_pb2.AcceptUnionBossIndividualsRes()
        res.status = 0

        union = data.union.get()
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        if not union_boss_business.is_able_to_accept_score_box(data, req.target_step):
            res.ret = union_pb2.UNION_BOSS_SCORE_UNACCEPTABLE
            return self._score_reward_succeed(data, req, res, timer)

        (items_id, items_num, honor) = \
                union_boss_business.get_score_box_reward(data, req.target_step)
        
        item_info = map(None, items_id, items_num)
        item_business.gain_item(data, item_info, "score reward", log_formater.SCORE_REWARD)
        union.accept_boss_score_box(req.target_step, honor)

        res.ret = union_pb2.UNION_OK
        pack.pack_resource_info(resource, res.resource)
        for item_id, item_num in item_info:
            item = res.items.add()
            item.basic_id = item_id
            item.num = item_num

        res.honor = honor

        defer = DataBase().commit(data)
        defer.addCallback(self._score_reward_succeed, req, res, timer)
        return defer

    def _score_reward_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Accept union boss score reward succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Accept union boss score reward failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _score_reward_failed(self, err, req, timer):
        logger.fatal("Accept union boss score reward failed[reason=%s]" % err)
        res = union_boss_pb2.AcceptUnionBossIndividualsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union boss score reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def boss_reward(self, user_id, request):
        """领取boss宝箱奖励"""
        timer = Timer(user_id)

        req = union_boss_pb2.QueryUnionBossBoxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_boss_reward, req, timer)
        defer.addErrback(self._boss_reward_failed, req, timer)
        return defer

    def _calc_boss_reward(self, data, req, timer):
        union = data.union.get(True)
        if union is None or not union.is_belong_to_target_union(req.union_id):
            res = union_boss_pb2.QueryUnionBossBoxRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._boss_reward_succeed(data, req, res, timer)

        user = data.user.get(True)
        union_req = internal_union_pb2.InternalUnionBossBossRewardReq()
        union_req.user_id = data.id
        union_req.user_name = user.name
        union_req.icon_id = user.icon_id
        union_req.boss_step = req.box_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "accept_unionboss_reward", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_boss_reward_result, data, req, timer)
        return defer

    def _calc_boss_reward_result(self, union_response, data, req, timer):
        res = union_boss_pb2.QueryUnionBossBoxRes()
        res.status = 0

        union_res = internal_union_pb2.InternalUnionBossBossRewardRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("accept union boss reward failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._boss_reward_succeed(data, req, res, timer)

        item_id = 0
        item_num = 0
        for member in union_res.box.members:
            if member.user_id == data.id:
                item_id = member.item_id
                item_num = member.item_num

        if item_id != 0:
            item_business.gain_item(data, [(item_id, item_num)], "boss reward", log_formater.BOsS_REWARD)

        res.ret = union_pb2.UNION_OK
        res.box.CopyFrom(union_res.box)

        defer = DataBase().commit(data)
        defer.addCallback(self._boss_reward_succeed, req, res, timer)
        return defer

    def _boss_reward_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Accept union boss box reward succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Accept union boss box reward failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _boss_reward_failed(self, err, req, timer):
        logger.fatal("Accept union boss box reward failed[reason=%s]" % err)
        res = union_boss_pb2.QueryUnionBossBoxRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union boss box reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def query_boss_reward(self, user_id, request):
        """查询boss宝箱领取情况"""
        timer = Timer(user_id)

        req = union_boss_pb2.QueryUnionBossBoxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_boss_reward, req, timer)
        defer.addErrback(self._query_boss_reward_failed, req, timer)
        return defer

    def _calc_query_boss_reward(self, data, req, timer):
        union = data.union.get(True)
        if union is None or not union.is_belong_to_target_union(req.union_id):
            res = union_boss_pb2.QueryUnionBossBoxRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._query_boss_reward_succeed(data, req, res, timer)

        user = data.user.get(True)
        union_req = internal_union_pb2.InternalUnionBossBossRewardReq()
        union_req.user_id = data.id
        union_req.user_name = user.name
        union_req.icon_id = user.icon_id
        union_req.boss_step = req.box_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "query_unionboss_reward", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_query_boss_reward_result, data, req, timer)
        return defer

    def _calc_query_boss_reward_result(self, union_response, data, req, timer):
        res = union_boss_pb2.QueryUnionBossBoxRes()
        res.status = 0

        union_res = internal_union_pb2.InternalUnionBossBossRewardRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("accept union boss reward failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._query_boss_reward_succeed(data, req, res, timer)

        res.ret = union_pb2.UNION_OK
        res.box.CopyFrom(union_res.box)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_boss_reward_succeed, req, res, timer)
        return defer

    def _query_boss_reward_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Query union boss box reward succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Query union boss box reward failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response
    
    def _query_boss_reward_failed(self, err, req, timer):
        logger.fatal("Query union boss box reward failed[reason=%s]" % err)
        res = union_boss_pb2.QueryUnionBossBoxRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union boss box reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def reset(self, user_id, request):
        """花费元宝重置攻击次数"""
        timer = Timer(user_id)

        req = union_boss_pb2.RefreshUnionBossAttackReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reset, req, timer)
        defer.addErrback(self._reset_failed, req, timer)
        return defer

    def _calc_reset(self, data, req, timer):
        res = union_boss_pb2.RefreshUnionBossAttackRes()
        res.status = 0

        union = data.union.get()
        if union is None or not union.is_belong_to_target_union(req.union_id):
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._reset_succeed(data, req, res, timer)

        gold = union_boss_business.get_reset_attack_gold(data)
        if gold != req.gold:
            res.ret = union_pb2.UNION_BOSS_REFRESH_ATTACK_GOLD_ERROR
            return self._reset_succeed(data, req, res, timer)
        
        union.reset_unionboss_attack()

        resource = data.resource.get()
        resource.update_current_resource(timer.now)	
        original_gold = resource.gold
        if not resource.cost_gold(gold):
            res.ret = union_pb2.UNION_BOSS_REFRESH_ATTACK_GOLD_SHORTAGE
            return self._reset_succeed(data, req, res, timer)
        log = log_formater.output_gold(data, -gold, log_formater.UNIONBOSS_RESET,
                "Unionboss reset", before_gold = original_gold)
        logger.notice(log)	

        res.ret = union_pb2.UNION_OK
        defer = DataBase().commit(data)
        defer.addCallback(self._reset_succeed, req, res, timer)
        return defer

    def _reset_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Reset union boss battle num succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Reset union boss battle num failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _reset_failed(self, err, req, timer):
        logger.fatal("Reset union boss battle num failed[reason=%s]" % err)
        res = union_boss_pb2.RefreshUnionBossAttackRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reset union boss battle num failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def add(self, user_id, request):
        """添加联盟boss组基础数据"""
        timer = Timer(user_id)

        req = union_boss_pb2.AddUnionBossGroupBasicDataReq()
        req.ParseFromString(request)
        
        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_add, req, timer)
        defer.addCallback(self._add_succeed, req, timer)
        defer.addErrback(self._add_failed, req, timer)
        return defer

    def _calc_add(self, basic_data, req, timer):
        for group in req.boss_group:
            start_time = 0
            end_time = 0
            if group.HasField("start_date"):
                start_time = utils.get_start_second_by_timestring(group.start_date)
            if group.HasField("end_date"):
                end_time = utils.get_start_second_by_timestring(group.end_date)

            str_bosses_id = utils.join_to_string(group.bosses_id)

            basic_boss_group = basic_data.unionbossgroup_list.get(group.id)
            if basic_boss_group is None:
                basic_boss_group = BasicUnionBossGroupInfo.create(group.id, basic_view.BASIC_ID,
                        start_time, end_time, str_bosses_id)
                basic_data.unionbossgroup_list.add(basic_boss_group)
            else:
                basic_boss_group.update(start_time, end_time, str_bosses_id)

        return DataBase().commit_basic(basic_data)

    def _add_succeed(self, basic_data, req, timer):
        res = union_boss_pb2.AddUnionBossGroupBasicDataRes()
        res.status = 0
        logger.notice("Add union boss group basic data succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _add_failed(self, err, req, timer):
        logger.fatal("Add union boss group basic data failed[reason=%s]" % err)
        res = union_boss_pb2.AddUnionBossGroupBasicDataRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add union boss group basic data failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    '''
    def update(self, user_id, request):
        """更新联盟boss(内部接口)"""
        timer = Timer(user_id)

        req = union_boss_pb2.UpdateUnionBossReq()
        req.ParseFromString(request)

        union_req = internal_union_pb2.InternalUpdateUnionBossReq()
        union_req.user_id = user_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "update_unionboss", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._update_result, req, timer)
        return defer

    def _update_result(self, union_response, req, timer):
        res = union_boss_pb2.UpdateUnionBossRes()
        res.status = 0

        union_res = internal_union_pb2.InternalUpdateUnionBossRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            return self._update_failed(req, timer)

        res.is_update = union_res.is_update
        res.is_reset = union_res.is_reset

        return self._update_succeed(req, res, timer)

    def _update_succeed(self, req, res, timer):
        logger.notice("update union boss succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _update_failed(self, req, timer):
        logger.fatal("update union boss failed")
        res = union_boss_pb2.UpdateUnionBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("update union boss failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
    '''
