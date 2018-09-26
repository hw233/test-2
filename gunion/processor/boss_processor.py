#coding:utf8
"""
Created on 2017-03-01
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟boss
"""

from utils import logger
from utils.timer import Timer
from datalib.global_data import DataBase
from proto import internal_union_pb2
from proto import union_pb2
from app import basic_view
from gunion.business import member as member_business
from gunion.business import boss as boss_business
from gunion.data.boss import UnionBossInfo

class BossProcess(object):
    """联盟boss"""
    '''
    def update(self, union_id, request):
        """更新联盟boss信息"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalUpdateUnionBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._update, union_id, req, timer)
        return defer

    def _update(self, basic_data, union_id, req, timer):
        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_update, basic_data, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer

    def _calc_update(self, data, basic_data, req, timer):
        res = internal_union_pb2.InternalUpdateUnionBossRes()
        res.status = 0

        is_update = boss_business.update_unioboss_from_basic_data(data, basic_data, timer.now)
        is_reset = boss_business.reset_unionboss(data, timer.now)

        res.is_update = is_update
        res.is_reset = is_reset

        defer = DataBase().commit(data)
        defer.addCallback(self._update_succeed, req, res, timer)
        return defer

    def _update_succeed(self, data, req, res, timer):
        logger.notice("update union boss succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _update_failed(self, err, req, timer):
        logger.fatal("update union boss failed[reason=%s]" % err)
        res = internal_union_pb2.InternalUpdateUnionBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("update union boss failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
    '''

    def query(self, union_id, request):
        """查询boss信息"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        res = internal_union_pb2.InternalQueryUnionBossRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        member = member_business.find_member(data, req.user_id)
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._query_succeed(data, req, res, timer)

        boss_business.try_change_unionboss(data, timer.now)
        boss_business.try_reset_unionboss(data, timer.now)

        union = data.union.get(True)
        res.last_update_time = union.boss_last_update_time

        bosses_id = union.get_bosses_id()
        for boss_id in bosses_id:
            res.bosses_id.append(boss_id)

        boss_id = union.get_attacking_unionboss()
        if boss_id != 0:
            attack_boss = boss_business.get_union_boss(data, boss_id, True)
            res.attack_id = attack_boss.boss_id
            res.attack_soldier_num = attack_boss.current_soldier_num
            res.attack_total_soldier_num = attack_boss.total_soldier_num

        for step, boss_id in enumerate(bosses_id):
            box = res.boxes.add()
            boss = boss_business.get_union_boss(data, boss_id, True)
            if boss.status != UnionBossInfo.KILLED:
                box.id = -1
                continue
            
            box.id = step
            reward_record = boss.get_reward_record()
            for user_id, user_name, icon_id, item_id, item_num, time in reward_record:
                member = box.members.add()
                member.user_id = user_id
                member.name = user_name
                member.headIconId = icon_id
                member.item_id = item_id
                member.item_num = item_num
                member.passedTime = timer.now - time

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer

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
        res = internal_union_pb2.InternalQueryUnionBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union boss failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def sync(self, union_id, request):
        """同步或获取boss信息"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalSyncBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_sync, req, timer)
        defer.addErrback(self._sync_failed, req, timer)
        return defer

    def _calc_sync(self, data, req, timer):
        res = internal_union_pb2.InternalSyncBossRes()
        res.status = 0

        member = member_business.find_member(data, req.user_id)
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._sync_succeed(data, req, res, timer)

        union = data.union.get()
        bosses_id = union.get_bosses_id()

        status = None
        boss_id = None
        boss_step = None
        now_boss_step = None
        total_soldier_num = None
        current_soldier_num = None

        if req.HasField("boss_step"):
            assert not req.HasField("boss_id")
            if req.boss_step < 0 or req.boss_step > len(bosses_id) - 1:
                res.ret = union_pb2.UNION_BOSS_INACTIVE
                return self._sync_succeed(data, req, res, timer)
                
            boss_id = bosses_id[req.boss_step]
            boss_step = req.boss_step
            boss = boss_business.get_union_boss(data, boss_id)

        if req.HasField("boss_id"):
            assert not req.HasField("boss_step")
            boss_id = req.boss_id
            boss_step = bosses_id.index(boss_id)
            boss = boss_business.get_union_boss(data, boss_id)
        
        if req.HasField("kill_addition"):
            assert req.HasField("user_name")
            assert req.HasField("boss_id") or req.HasField("boss_step")
            assert boss_id is not None

            boss = boss_business.get_union_boss(data, boss_id)

            if boss.is_able_to_attack():
                boss_business.attack_boss(data, boss, req.kill_addition, req.user_id, req.user_name)
        
        now_boss_step = union.boss_step
        status = boss.status
        total_soldier_num = boss.total_soldier_num
        current_soldier_num = boss.current_soldier_num

        res.ret = union_pb2.UNION_OK
        res.boss_step = boss_step
        res.now_boss_step = now_boss_step
        res.boss_id = boss_id
        res.boss_status = status
        res.total_soldier_num = total_soldier_num
        res.current_soldier_num = current_soldier_num
        
        defer = DataBase().commit(data)
        defer.addCallback(self._sync_succeed, req, res, timer)
        return defer

    def _sync_succeed(self, data, req, res, timer):
        if res.ret == union_pb2.UNION_OK:
            logger.notice("Sync union boss succeed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Sync union boss failed"
                    "[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))
        response = res.SerializeToString()
        return response

    def _sync_failed(self, err, req, timer):
        logger.fatal("Sync union boss failed[reason=%s]" % err)
        res = internal_union_pb2.InternalSyncBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Sync union boss failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def boss_reward(self, union_id, request):
        """领取boss公共奖励"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalUnionBossBossRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_boss_reward, req, timer)
        defer.addErrback(self._boss_reward_failed, req, timer)
        return defer

    def _calc_boss_reward(self, data, req, timer):
        res = internal_union_pb2.InternalUnionBossBossRewardRes()
        res.status = 0

        union = data.union.get()
        member = member_business.find_member(data, req.user_id)
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._boss_reward_succeed(data, req, res, timer)

        boss_id = union.get_bosses_id()[req.boss_step]
        boss = boss_business.get_union_boss(data, boss_id)
        if boss is None:
            raise Exception("Boss is None[boss_id=%d]" % boss_id)

        if boss_business.is_able_to_accept_boss_reward(data, member, boss):
            logger.debug("Accept boss box reward[union_id=%d][user_id=%d][boss_id=%d]" % (
                    data.id, member.user_id, boss_id))
            boss_business.accept_boss_reward(data, req.user_id, req.user_name, req.icon_id,
                    boss, timer.now)
        else:
            logger.debug("Query boss box reward[union_id=%d][user_id=%d][boss_id=%d]" % (
                    data.id, member.user_id, boss_id))
        
        reward_record = boss.get_reward_record()
        res.box.id = req.boss_step
        for user_id, user_name, icon_id, item_id, item_num, time in reward_record:
            member = res.box.members.add()
            member.user_id = user_id
            member.name = user_name
            member.headIconId = icon_id
            member.item_id = item_id
            member.item_num = item_num
            member.passedTime = timer.now - time

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
        res = internal_union_pb2.InternalUnionBossBossRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union boss box reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_boss_reward(self, union_id, request):
        """请求boss宝箱领取记录"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalUnionBossBossRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_query_boss_reward, req, timer)
        defer.addErrback(self._query_boss_reward_failed, req, timer)
        return defer

    def _calc_query_boss_reward(self, data, req, timer):
        res = internal_union_pb2.InternalUnionBossBossRewardRes()
        res.status = 0

        member = member_business.find_member(data, req.user_id)
        union = data.union.get()
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._query_boss_reward_succeed(data, req, res, timer)

        boss_id = union.get_bosses_id()[req.boss_step]
        boss = boss_business.get_union_boss(data, boss_id)
        if boss is None:
            raise Exception("Boss is None[boss_id=%d]" % boss_id)

        reward_record = boss.get_reward_record()
        res.box.id = req.boss_step
        for user_id, user_name, icon_id, item_id, item_num, time in reward_record:
            member = res.box.members.add()
            member.user_id = user_id
            member.name = user_name
            member.headIconId = icon_id
            member.item_id = item_id
            member.item_num = item_num
            member.passedTime = timer.now - time

        return self._query_boss_reward_succeed(data, req, res, timer)

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
        res = internal_union_pb2.InternalUnionBossBossRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union boss box reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
