#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from utils.timer import Timer
from proto import union_pb2
from proto import internal_pb2
from proto import internal_union_pb2
from datalib.global_data import DataBase
from app.union_matcher import UnionMatcher
from app.union_patcher import UnionPatcher
from app.union_ranker import UnionRanker
from app.union_recommender import UnionRecommender
from app.union_allocator import UnionAllocator
from app.business import union as union_business
from app.business import union_donate
from app.business import union_boss as union_boss_business
from app.data.donate_box import UserDonateBox
from app import pack
from app import log_formater
import datetime
import base64


class UnionProcessor(object):

    def query(self, user_id, request, force = False):
        """查询联盟信息
        """
        timer = Timer(user_id)

        req = union_pb2.QueryUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer, force)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer, force):
        union = data.union.get(True)
        if not force and not union.is_belong_to_target_union(req.union_id):
            #已经不属于对应联盟
            res = union_pb2.QueryUnionRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

            defer = DataBase().commit(data)
            defer.addCallback(self._query_succeed, req, res, timer)
            return defer
            
        union.update_daily_info(timer.now)

        union_req = internal_union_pb2.InternalQueryUnionReq()
        union_req.user_id = data.id

        #请求 Union 模块，查询联盟情况
        if not force:
            defer = GlobalObject().remote['gunion'].callRemote(
                    "query_union", union.union_id, union_req.SerializeToString())
        else:
            defer = GlobalObject().remote['gunion'].callRemote(
                    "query_union_force", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._update_query_info, data, req, timer)
        return defer


    def _update_query_info(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union res errro")

        res = union_pb2.QueryUnionRes()
        res.status = 0
        res.ret = union_res.ret

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            logger.warning("User query union unexpected")

            if union_res.ret == union_pb2.UNION_NOT_MATCHED:
                union = data.union.get()
                if not union.leave_union(union.union_id, timer.now, False):
                    raise Exception("Leave union failed")

            defer = DataBase().commit(data)
            defer.addCallback(self._query_succeed, req, res, timer)
            return defer

        else:
            return self._patch_query_info(union_res, data, req, timer)


    def _patch_query_info(self, union_res, data, req, timer):
        """补充联盟信息
        """
        assert union_res.ret == union_pb2.UNION_OK
        res = union_pb2.QueryUnionRes()
        res.status = 0
        res.ret = union_res.ret
       
        #填充 union message
        defer = UnionPatcher().patch(res.union, union_res.union, data, timer.now)
        defer.addCallback(self._do_patch_query_info, data, union_res, req, res, timer)
        return defer


    def _do_patch_force(self, patcher, data, union_res, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _do_patch_query_info(self, patcher, data, union_res, req, res, timer):
        #填充捐献相关信息
        union_donate.syn_donate_boxes(data, union_res.boxes_info)

        for box_info in union_res.boxes_info:
            if box_info.current_state == UserDonateBox.DONATING:
                donate_level = union_donate.query_donate_level(data, box_info.treasurebox_id)
                for is_donate in donate_level:
                    box_info.donate_types.append(is_donate)
            if box_info.current_state != UserDonateBox.NULL and \
                not union_donate.is_donate_box_rewarded(data, box_info.treasurebox_id):
                res.union.boxes_info.add().CopyFrom(box_info)

        res.union.donate_info.coldtime = union_donate.get_true_cold_time(data, timer)
        strings = union_donate.trun_donate_records_to_strings(union_res.donate_records)
        for string in strings:
            res.union.donate_info.donate_records.add().CopyFrom(string)

        
        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer
        
#        #查询联盟boss
#        union_req = internal_union_pb2.InternalQueryUnionBossReq()
#        union_req.user_id = data.id
#
#        union = data.union.get(True)
#        defer = GlobalObject().remote['gunion'].callRemote(
#                "query_unionboss", union.union_id, union_req.SerializeToString())
#        defer.addCallback(self._do_patch_query_info_unionboss, data, req, res, timer)
#        return defer
#
#    def _do_patch_query_info_unionboss(self, union_response, data, req, res, timer):
#        union_res = internal_union_pb2.InternalQueryUnionBossRes()
#        union_res.ParseFromString(union_response)
#
#        if union_res.status != 0:
#            raise Exception("Query union boss failed")
#
#        if union_res.ret != union_pb2.UNION_OK:
#            res.ret = union_res.ret
#            return self._query_succeed(data, req, res, timer)
#
#        union_boss_business.try_update_union_boss(data, union_res.bosses_id, union_res.last_update_time)
#
#        if len(union_res.bosses_id) != 0:
#            self._pack_unionboss(data, union_res, res.union.union_boss, timer.now)
#
#        defer = DataBase().commit(data)
#        defer.addCallback(self._query_succeed, req, res, timer)
#        return defer
#
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
        response = res.SerializeToString()
        logger.notice("Query union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query union failed[reason=%s]" % err)
        res = union_pb2.QueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def create(self, user_id, request):
        """创建联盟
        """
        timer = Timer(user_id)

        req = union_pb2.CreateUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_create, req, timer)
        defer.addErrback(self._create_failed, req, timer)
        return defer


    def _calc_create(self, data, req, timer):
        union = data.union.get(True)
        if union.is_belong_to_union():
            #玩家已经属于一个联盟，无法创建联盟
            logger.debug("User is belong to union[union_id=%d]" % union.union_id)
            res = union_pb2.CreateUnionRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

            defer = DataBase().commit(data)
            defer.addCallback(self._create_succeed, req, res, timer)
            return defer

        if not union_business.is_able_to_create_union(data, req.gold_cost, timer.now):
            raise Exception("Not able to create union")

        #分配联盟 id
        union_id = UnionAllocator().allocate()

        #请求 Union 模块，创建联盟
        union_req = internal_union_pb2.InternalCreateUnionReq()
        union_req.user_id = data.id
        union_req.name = req.name
        union_req.icon_id = req.icon_id

        defer = GlobalObject().remote['gunion'].callRemote(
                "create_union", union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_create_result, data, req, timer)
        return defer


    def _calc_create_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Create union res error")

        res = union_pb2.CreateUnionRes()
        res.status = 0
        res.ret = union_res.ret
        if res.ret != union_pb2.UNION_OK:
            return self._create_succeed(data, req, res, timer)
        
        #创建联盟
        union_business.create_union(
                data, union_res.union.id, req.gold_cost, timer.now)

        res.union.CopyFrom(union_res.union)
        #第一次创建联盟返回时要把union member信息不全
        user = data.user.get(True)
        res.union.members[0].user.name = user.get_readable_name()
        res.union.members[0].user.level = user.level
        res.union.members[0].user.headicon_id = user.icon_id

        #查询联盟boss
        union_req = internal_union_pb2.InternalQueryUnionBossReq()
        union_req.user_id = data.id

        union = data.union.get(True)
        defer = GlobalObject().remote['gunion'].callRemote(
                "query_unionboss", union.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_create_result_unionboss, data, req, res, timer)
        return defer


    def _calc_create_result_unionboss(self, union_response, data, req, res, timer):
        union_res = internal_union_pb2.InternalQueryUnionBossRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union boss failed")

        if union_res.ret != union_pb2.UNION_OK:
            res.ret = union_res.ret
            return self._create_succeed(data, req, res, timer)

        union_boss_business.try_update_union_boss(data, union_res.bosses_id, union_res.last_update_time)

        if len(union_res.bosses_id) != 0:
            self._pack_unionboss(data, union_res, res.union.union_boss, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._create_succeed, req, res, timer)
        return defer


    def _create_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Create union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _create_failed(self, err, req, timer):
        logger.fatal("Create union failed[reason=%s]" % err)
        res = union_pb2.CreateUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Create union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def search(self, user_id, request):
        """查找联盟
        """
        timer = Timer(user_id)

        req = union_pb2.SearchUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_search, req, timer)
        defer.addErrback(self._search_failed, req, timer)
        return defer


    def _calc_search(self, data, req, timer):
        union = data.union.get(True)
        user = data.user.get(True)
        if union.is_locked(timer.now):
            logger.debug("Union is locked")
            res = union_pb2.SearchUnionRes()
            res.status = 0
            res.lock_left_time = union.lock_time - timer.now

            defer = DataBase().commit(data)
            defer.addCallback(self._search_succeed, req, res, timer)
            return defer

        else:
            if req.type == req.SEARCH:
                matcher = UnionMatcher()
                matcher.add_condition(req.union_id, req.name)
                defer = matcher.match()
            elif req.type == req.RECOMMEND:
                matcher = UnionRecommender()
                matcher.add_condition(user)
                defer = matcher.match(timer.now)
            elif req.type == req.RANK:
                matcher = UnionRanker()
                defer = matcher.match(timer.now)

            defer.addCallback(self._calc_search_result, data, req, timer)
            return defer


    def _calc_search_result(self, matcher, data, req, timer):
        res = union_pb2.SearchUnionRes()
        res.status = 0

        available = data.union.get(True).is_able_to_join(timer.now)

        for union in matcher.result:
            message = res.unions.add()
            message.id = union.id
            message.name = union.get_readable_name()
            message.icon_id = union.icon
            message.current_number = union.current_number
            message.max_number = union.max_number
            message.join_status = union.join_status
            message.need_level = union.join_level_limit
            message.announcement = union.get_readable_announcement()
            message.prosperity = union.today_prosperity
            message.recent_prosperity = union.recent_prosperity

            res.available.append(available)

        union = data.union.get(True)
        if union.is_belong_to_union():
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

        defer = DataBase().commit(data)
        defer.addCallback(self._search_succeed, req, res, timer)
        return defer


    def _search_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Search union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _search_failed(self, err, req, timer):
        logger.fatal("Search union failed[reason=%s]" % err)
        res = union_pb2.SearchUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Search union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update(self, user_id, request):
        """设置联盟
        """
        timer = Timer(user_id)

        req = union_pb2.UpdateUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer


    def _calc_update(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #已经不属于对应联盟
            res = union_pb2.QueryUnionRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

        #消耗元宝
        if req.HasField("name") or req.HasField("icon_id"):
            gold = union.calc_update_cost_gold()
            if gold != req.gold_cost:
                raise Exception("Gold not matched[need=%d][cost=%d]" %
                        (gold, req.gold_cost))

            resource = data.resource.get()
            resource.update_current_resource(timer.now)
            if resource.gold < gold:
                raise Exception("Not enough gold[own=%d][cost=%d]" %
                        (resource.gold, gold))

        #请求 Union 模块，设置联盟
        union_req = internal_union_pb2.InternalUpdateUnionReq()
        union_req.user_id = data.id
        if req.HasField("name"):
            union_req.name = req.name
        if req.HasField("icon_id"):
            union_req.icon_id = req.icon_id
        if req.HasField("need_level"):
            union_req.need_level = req.need_level
        if req.HasField("join_status"):
            union_req.join_status = req.join_status
        if req.HasField("announcement"):
            union_req.announcement = req.announcement

        defer = GlobalObject().remote['gunion'].callRemote(
                "update_union", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_update_result, data, req, timer)
        return defer


    def _calc_update_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionRes()
        union_res.ParseFromString(union_response)

        res = union_pb2.UpdateUnionRes()
        res.status = 0
        res.ret = union_res.ret
        if res.ret == union_pb2.UNION_OK:
            #修改成功，消耗元宝
            resource = data.resource.get()
            resource.update_current_resource(timer.now)
            original_gold = resource.gold
            if not resource.cost_gold(req.gold_cost):
                raise Exception("Cost gold failed")
            log = log_formater.output_gold(data, -req.gold_cost, log_formater.UNIONUPDATE,
                "Update union by gold", before_gold = original_gold)
            logger.notice(log)
            res.union.CopyFrom(union_res.union)

        defer = DataBase().commit(data)
        defer.addCallback(self._update_succeed, req, res, timer)
        return defer


    def _update_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Update union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _update_failed(self, err, req, timer):
        logger.fatal("Update union failed[reason=%s]" % err)
        res = union_pb2.UpdateUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete(self, user_id, request):
        """删除联盟数据（内部接口）
        """
        timer = Timer(user_id)

        req = internal_pb2.DeleteUnionReq()
        req.ParseFromString(request)

        defer = Deferred()
        for union_id in req.unions_id:
            defer.addCallback(self._calc_delete, union_id, timer)
        defer.addCallback(self._delete_succeed, req, timer)
        defer.addErrback(self._delete_failed, req, timer)
        defer.callback(0)
        return defer


    def _calc_delete(self, status, union_id, timer):
        """删除联盟
        """
        #请求 Union 模块，删除联盟
        union_req = internal_union_pb2.InternalDeleteUnionReq()

        defer = GlobalObject().remote['gunion'].callRemote(
                "delete_union", union_id, union_req.SerializeToString())
        defer.addCallback(self._check_delete_result, union_id, timer)
        return defer


    def _check_delete_result(self, union_response, union_id, timer):
        union_res = internal_union_pb2.InternalDeleteUnionRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Delete union failed[union_id=%d]" % union_id)

        return union_res.status


    def _delete_succeed(self, data, req, timer):
        res = internal_pb2.DeleteUnionRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_failed(self, err, req, timer):
        logger.fatal("Delete union failed[reason=%s]" % err)
        res = internal_pb2.DeleteUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def try_transfer(self, user_id, request):
        """自动转让盟主(内部接口)"""
        timer = Timer(user_id)
        
        req = internal_pb2.TryTransferUnionLeaderReq()
        req.ParseFromString(request)

        union_req = internal_union_pb2.InternalTryTransferUnionLeaderReq()
        union_req.user_id = user_id

        defer = GlobalObject().remote['gunion'].callRemote(
                "try_transfer_leader", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_transfer, req, timer)
        defer.addErrback(self._transfer_failed, req, timer)
        return defer

    def _calc_transfer(self, union_response, req, timer):
        union_res = internal_union_pb2.InternalTryTransferUnionLeaderRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Try transfer union leader failed[union_id=%d]" % req.union_id)

        res = internal_pb2.TryTransferUnionLeaderRes()
        res.status = 0
        res.ret = union_res.ret

        return self._transfer_succeed(req, res, timer)

    def _transfer_succeed(self, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Try transfer union leader succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _transfer_failed(self, err, req, timer):
        logger.fatal("Try transfer union leader failed[reason=%s]" % err)
        res = internal_pb2.TryTransferUnionLeaderRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Try transfer union leader"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
