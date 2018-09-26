#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟援助处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import union_pb2
from proto import internal_union_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app.union_member_matcher import UnionMemberMatcher
from app import compare
from app import pack
from app.user_matcher import UserMatcher
from app.business import union as union_business
import base64


class UnionAidProcessor(object):


    def query_aid(self, user_id, request):
        """查看联盟援助
        """
        timer = Timer(user_id)

        req = union_pb2.QueryUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_pb2.QueryUnionAidRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._query_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalQueryUnionAidReq()
        union_req.user_id = data.id
        defer = GlobalObject().remote['gunion'].callRemote(
                "query_aid", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_query_result, data, req, timer)
        return defer


    def _calc_query_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionAidRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union aid res error")

        union = data.union.get(True)

        res = union_pb2.QueryUnionAidRes()
        res.status = 0
        res.ret = union_res.ret

        if res.ret == union_pb2.UNION_OK:
            for aid_msg in union_res.aids:
                if aid_msg.sender.user_id == data.id:
                    res.aid_own.CopyFrom(aid_msg)
                else:
                    res.aids.add().CopyFrom(aid_msg)
            res.lock_time_left = union.aid_lock_time - timer.now

        #成员信息，查询数据库
        matcher = UnionMemberMatcher()
        for aid in union_res.aids:
            matcher.add_condition(aid.sender.user_id)
        defer = matcher.match()
        defer.addCallback(self._do_patch_query_info, data, req, res, timer)
        return defer


    def _do_patch_query_info(self, matcher, data, req, res, timer):
        for aid_msg in res.aids:
            (name, level, icon, last_login_time, battle_score, honor) = matcher.result[
                    aid_msg.sender.user_id]
            aid_msg.sender.name = name
            aid_msg.sender.level = level
            aid_msg.sender.headicon_id = icon

        if res.HasField("aid_own"):
            user = data.user.get(True)
            res.aid_own.sender.name = user.get_readable_name()
            res.aid_own.sender.level = user.level
            res.aid_own.sender.headicon_id = user.icon_id

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union aid succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query union aid failed[reason=%s]" % err)
        res = union_pb2.QueryUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union aid failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start_aid(self, user_id, request):
        """启动联盟援助
        """
        timer = Timer(user_id)

        req = union_pb2.StartUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start, req, timer)
        defer.addErrback(self._start_failed, req, timer)
        return defer


    def _calc_start(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #不属于联盟
            res = union_pb2.StartUnionAidRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        if not union.is_able_to_start_aid(timer.now):
            #在锁定期内
            logger.warning("Not able to start aid")
            res = union_pb2.StartUnionAidRes()
            res.status = 0
            res.ret = union_pb2.UNION_AID_LOCKED

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        if not union_business.is_able_to_start_aid(
                data, req.need_item.basic_id, req.need_item.num, timer.now):
            raise Exception("Start union aid failed")

        union_req = internal_union_pb2.InternalStartUnionAidReq()
        union_req.user_id = data.id
        union_req.need_item.CopyFrom(req.need_item)

        defer = GlobalObject().remote['gunion'].callRemote(
                "start_aid", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_start_result, data, req, timer)
        return defer


    def _calc_start_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalStartUnionAidRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union aid res error")

        res = union_pb2.StartUnionAidRes()
        res.status = 0
        res.ret = union_res.ret

        if res.ret == union_pb2.UNION_OK:
            #开始联盟援助
            union_business.start_aid(data, timer.now)

            res.own.CopyFrom(union_res.own)

            trainer = data.trainer.get()
            trainer.add_daily_start_aid(1)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_succeed, req, res, timer)
        return defer


    def _start_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Start union aid succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _start_failed(self, err, req, timer):
        logger.fatal("Start union aid failed[reason=%s]" % err)
        res = union_pb2.StartUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start union aid failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_aid(self, user_id, request):
        """结束联盟援助
        """
        timer = Timer(user_id)

        req = union_pb2.FinishUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish, req, timer)
        defer.addErrback(self._finish_failed, req, timer)
        return defer


    def _calc_finish(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_pb2.FinishUnionAidRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._finish_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalFinishUnionAidReq()
        union_req.user_id = data.id

        defer = GlobalObject().remote['gunion'].callRemote(
                "finish_aid", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_finish_result, data, req, timer)
        return defer


    def _calc_finish_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalFinishUnionAidRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union aid res error")

        res = union_pb2.FinishUnionAidRes()
        res.status = 0
        res.ret = union_res.ret

        if res.ret == union_pb2.UNION_OK:
            #结束联盟援助
            union_business.finish_aid(data,
                    union_res.item.basic_id, union_res.item.num)

            res.item.CopyFrom(union_res.item)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_succeed, req, res, timer)
        return defer


    def _finish_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Finish union aid succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_failed(self, err, req, timer):
        logger.fatal("Finish union aid failed[reason=%s]" % err)
        res = union_pb2.FinishUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish union aid failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def respond_aid(self, user_id, request):
        """响应联盟援助
        """
        timer = Timer(user_id)

        req = union_pb2.RespondUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_respond, req, timer)
        defer.addErrback(self._respond_failed, req, timer)
        return defer


    def _calc_respond(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_pb2.RespondUnionAidRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._respond_succeed, req, res, timer)
            return defer

        if not union_business.is_able_to_respond_aid(data, req.item.basic_id):
            raise Exception("Not able to respond aid")

        union_req = internal_union_pb2.InternalRespondUnionAidReq()
        union_req.user_id = data.id
        union_req.target_user_id = req.target_user_id
        union_req.item_basic_id = req.item.basic_id

        defer = GlobalObject().remote['gunion'].callRemote(
                "respond_aid", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_respond_result, data, req, timer)
        return defer


    def _calc_respond_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalRespondUnionAidRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union aid res error")

        res = union_pb2.RespondUnionAidRes()
        res.status = 0
        res.ret = union_res.ret

        if res.ret != union_pb2.UNION_OK:
            return self._respond_succeed(data, req, res, timer)

        #结束联盟援助
        if not union_business.respond_aid(
                data, req.item.basic_id,
                union_res.honor, union_res.exp, union_res.gold, timer.now):
            raise Exception("Respond aid failed")

        pack.pack_resource_info(data.resource.get(), res.resource)
        res.union_prosperity = union_res.prosperity

        compare.check_item(data, req.item)
        compare.check_user(data, req.monarch, with_level = True)

        #发广播
        defer = self._respond_broadcast(data, req, timer)
        defer.addCallback(self._calc_respond_result_broadcast, data, req, res, timer)
        return defer

    def _calc_respond_result_broadcast(self, result, data, req, res, timer):
        if not result:
            logger.warning("Respond send broadcast failed[user_id=%d]" % data.id)

        trainer = data.trainer.get()
        trainer.add_daily_respond_aid(1)

        defer = DataBase().commit(data)
        defer.addCallback(self._respond_succeed, req, res, timer)
        return defer

    def _respond_broadcast(self, data, req, timer):
        matcher = UserMatcher()
        matcher.add_condition(req.target_user_id)
        defer = matcher.match()
        defer.addCallback(self._respond_broadcast_match, data, req, timer)
        return defer

    def _respond_broadcast_match(self, users, data, req, timer):
        try:
            user_name = data.user.get(True).name
            target_user_name = users[req.target_user_id].name
            item_name_key = data_loader.ItemBasicInfo_dict[req.item.basic_id].nameKey.encode("utf-8")

            broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_respond_unionaid'].value))
            mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
            life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
            template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
            priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

            content = template.replace("#str#", base64.b64decode(user_name), 1)
            content = content.replace("#str#", "@%s@" % item_name_key, 1)
            content = content.replace("#str#", base64.b64decode(target_user_name), 1)

            req = broadcast_pb2.AddBroadcastInfoReq()
            req.user_id = data.id
            req.mode_id = mode_id
            req.priority = priority
            req.life_time = life_time
            req.content = content
            request = req.SerializeToString()

            defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
            defer.addCallback(self._respond_broadcast_result)
            return defer
        except:
            return False

    def _respond_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        return res.status == 0

    def _respond_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Respond union aid succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _respond_failed(self, err, req, timer):
        logger.fatal("Respond union aid failed[reason=%s]" % err)
        res = union_pb2.RespondUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Respond union aid failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

