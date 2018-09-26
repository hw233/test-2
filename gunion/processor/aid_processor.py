#coding:utf8
"""
Created on 2016-06-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟援助处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import internal_union_pb2
from proto import union_pb2
from datalib.global_data import DataBase
from gunion.business import aid as aid_business
from gunion.business import member as member_business
from gunion import pack



class AidProcessor(object):


    def start(self, union_id, request):
        """发起联盟援助
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalStartUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_start, req, timer)
        defer.addErrback(self._start_failed, req, timer)
        return defer


    def _calc_start(self, data, req, timer):
        """发起
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_start_response_invalid(union_pb2.UNION_NOT_MATCHED)
            return self._start_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        if member is None:
            res = self._pack_start_response_invalid(union_pb2.UNION_MEMBER_INVALID)
        else:
            aid = aid_business.start_aid(data, req.user_id,
                    req.need_item.basic_id, req.need_item.num, timer.now)
            if aid is None:
                raise Exception("Start union aid failed")
            res = self._pack_start_response(aid, req.user_id, timer)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_succeed, req, res, timer)
        return defer


    def _pack_start_response_invalid(self, ret):
        res = internal_union_pb2.InternalStartUnionAidRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_start_response(self, aid, user_id, timer):
        res = internal_union_pb2.InternalStartUnionAidRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK
        pack.pack_aid_info(aid, res.own, user_id, timer.now)
        return res


    def _start_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Start union aid succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _start_failed(self, err, req, timer):
        logger.fatal("Start union aid failed[reason=%s]" % err)
        res = internal_union_pb2.InternalStartUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start union aid failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish(self, union_id, request):
        """结束联盟援助
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalFinishUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_finish, req, timer)
        defer.addErrback(self._finish_failed, req, timer)
        return defer


    def _calc_finish(self, data, req, timer):
        """结束
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_finish_response_invalid(union_pb2.UNION_NOT_MATCHED)
            return self._finish_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        if member is None:
            res = self._pack_finish_response_invalid(union_pb2.UNION_MEMBER_INVALID)
        else:
            aid = aid_business.finish_aid(data, req.user_id, timer.now)
            if aid is None:
                raise Exception("Finish union aid failed")
            res = self._pack_finish_response(aid, req.user_id)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_succeed, req, res, timer)
        return defer


    def _pack_finish_response_invalid(self, ret):
        res = internal_union_pb2.InternalFinishUnionAidRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_finish_response(self, aid, user_id):
        res = internal_union_pb2.InternalFinishUnionAidRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK
        res.item.basic_id = aid.item_basic_id
        res.item.num = aid.item_current_num
        return res


    def _finish_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Finish union aid succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_failed(self, err, req, timer):
        logger.fatal("Finish union aid failed[reason=%s]" % err)
        res = internal_union_pb2.InternalFinishUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish union aid failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query(self, union_id, request):
        """查询所有联盟援助信息
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        """查询
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_query_response_invalid(union_pb2.UNION_NOT_MATCHED)
            return self._query_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        if member is None:
            res = self._pack_query_response_invalid(union_pb2.UNION_MEMBER_INVALID)
        else:
            res = self._pack_query_response(data, req.user_id, timer)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _pack_query_response_invalid(self, ret):
        res = internal_union_pb2.InternalQueryUnionAidRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_query_response(self, data, user_id, timer):
        res = internal_union_pb2.InternalQueryUnionAidRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        for aid in data.aid_list.get_all(True):
            if aid.is_active_for(user_id, timer.now):
                pack.pack_aid_info(aid, res.aids.add(), user_id, timer.now)

        return res


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union aid succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query union aid failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union aid failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def respond(self, union_id, request):
        """响应，进行援助
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalRespondUnionAidReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_respond, req, timer)
        defer.addErrback(self._respond_failed, req, timer)
        return defer


    def _calc_respond(self, data, req, timer):
        """援助
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_respond_response_invalid(union_pb2.UNION_NOT_MATCHED)
            return self._respond_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        target_member = member_business.find_member(data, req.target_user_id)
        if member is None:
            res = self._pack_respond_response_invalid(union_pb2.UNION_MEMBER_INVALID)
        elif target_member is None:
            res = self._pack_respond_response_invalid(union_pb2.UNION_AID_INVALID)
        else:
            aid = aid_business.respond_aid(
                    data, member, target_member, req.item_basic_id, timer.now)
            if aid is None:
                res = self._pack_respond_response_invalid(union_pb2.UNION_AID_INVALID)
            else:
                res = self._pack_respond_response(aid, req.user_id)

        defer = DataBase().commit(data)
        defer.addCallback(self._respond_succeed, req, res, timer)
        return defer


    def _pack_respond_response_invalid(self, ret):
        res = internal_union_pb2.InternalRespondUnionAidRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_respond_response(self, aid, user_id):
        res = internal_union_pb2.InternalRespondUnionAidRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        (honor, exp, gold) = aid.calc_user_benefit()
        res.honor = honor
        res.exp = exp
        res.gold = gold

        res.prosperity = aid.calc_union_benefit()
        return res


    def _respond_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Respond union aid succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _respond_failed(self, err, req, timer):
        logger.fatal("Respond union aid failed[reason=%s]" % err)
        res = internal_union_pb2.InternalRespondUnionAidRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Respond union aid failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


