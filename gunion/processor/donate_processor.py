#coding:utf8
"""
Created on 2016-10-27
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟捐献流程
"""

from utils import logger
from utils.timer import Timer
from proto import internal_union_pb2
from proto import union_pb2
from datalib.global_data import DataBase
from gunion.data.donate_box import UnionDonateBox
from gunion.data.donate_record import UnionDonateRecord
from gunion.business import donate as donate_business
from gunion.business import member as member_business
from gunion import pack

class DonateProcess(object):
    """联盟捐献流程"""

    def query(self, union_id, request):
        """查询联盟捐献信息"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionDonateReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        if not data.is_valid():
            res = internal_union_pb2.InternalQueryUnionDonateRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._query_succeed(data, req, res, timer)
        
        member = member_business.find_member(data, req.user_id)
        if member is None:
            res = internal_union_pb2.InternalQueryUnionDonateRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
        else:
            donate_business.auto_refresh_donate_boxes(data, timer)

            res = internal_union_pb2.InternalQueryUnionDonateRes()
            res.status = 0
            res.ret = union_pb2.UNION_OK

            donate_boxes = data.donate_box_list.get_all(True)
            for donate_box in donate_boxes:
                pack.pack_donate_box_info(data, req.user_id, donate_box, res.boxes_info.add(), timer)

            donate_records = donate_business.get_donate_records(data)
            for donate_record in donate_records:
                pack.pack_donate_record_info(donate_record, res.donate_records.add())
        
        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer
    
    def _query_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Query union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Query union donate succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _query_failed(self, err, req, timer):
        logger.fatal("Query union donate failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionDonateRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
    
    def initiate(self, union_id, request):
        """发起捐献"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalInitiateDonateReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_initiate, req, timer)
        defer.addErrback(self._initiate_failed, req, timer)
        return defer

    def _calc_initiate(self, data, req, timer):
        res = internal_union_pb2.InternalInitiateDonateRes()
        res.status = 0
        if not data.is_valid():     
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._initiate_succeed(data, req, res, timer)
        
        member = member_business.find_member(data, req.user_id)
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
        else:
            ret = donate_business.is_able_to_initiate_donate(data, req.user_id, req.box_id, timer)
            if ret != 0:
                res.ret = ret
            else:
                donate_business.initiate_donate(data, req.box_id, timer)
                donate_box = donate_business.get_donate_box(data, req.box_id, True)
                
                res.ret = union_pb2.UNION_OK
                pack.pack_donate_box_info(data, req.user_id, donate_box, res.box_info, timer)
        
        defer = DataBase().commit(data)
        defer.addCallback(self._initiate_succeed, req, res, timer)
        return defer
        
    def _initiate_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Initiate union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Initiate union donate succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _initiate_failed(self, err, req, timer):
        logger.fatal("Initiate union donate failed[reason=%s]" % err)
        res = internal_union_pb2.InternalInitiateDonateRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Initiate union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def start(self, union_id, request):
        """开始捐献"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalStartUnionDonateReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_start, req, timer)
        defer.addErrback(self._start_failed, req, timer)
        return defer

    def _calc_start(self, data, req, timer):
        res = internal_union_pb2.InternalStartUnionDonateRes()
        res.status = 0
        if not data.is_valid():
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._start_succeed(data, req, res, timer)
        
        member = member_business.find_member(data, req.user_id)
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._start_succeed(data, req, res, timer)

        if not donate_business.is_able_to_start_donate(data, req.box_id, timer):
            res.ret = union_pb2.UNION_DONATE_BOX_INVALID
        else:
            (honor, donate_box) = donate_business.start_donate(
                data, req.box_id, req.user_id, req.user_name, req.donate_type, timer)
            
            res.ret = union_pb2.UNION_OK
            res.honor = honor
            pack.pack_donate_box_info(data, req.user_id, donate_box, res.box_info, timer)
            donate_records = donate_business.get_donate_records(data)
            for donate_record in donate_records:
                pack.pack_donate_record_info(donate_record, res.donate_records.add())
        
        defer = DataBase().commit(data)
        defer.addCallback(self._start_succeed, req, res, timer)
        return defer

    def _start_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Start union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Start union donate succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _start_failed(self, err, req, timer):
        logger.fatal("Start union donate failed[reason=%s]" % err)
        res = internal_union_pb2.InternalStartUnionDonateRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def reward(self, union_id, request):
        """领取宝箱"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalGetBoxRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_reward, req, timer)
        defer.addErrback(self._reward_failed, req, timer)
        return defer

    def _calc_reward(self, data, req, timer):
        res = internal_union_pb2.InternalGetBoxRewardRes()
        res.status = 0
        if not data.is_valid():
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._reward_succeed(data, req, res, timer)
        member = member_business.find_member(data, req.user_id)
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._reward_succeed(data, req, res, timer)

        if not donate_business.is_able_to_reward_donate_box(data, req.box_id, timer):
            res.ret = union_pb2.UNION_DONATE_NO_CONDITION
        else:
            res.ret = union_pb2.UNION_OK
            pack.pack_donate_reward_info(
                UnionDonateBox.get_reward_item_list(req.box_id),
                UnionDonateBox.get_reward_resource_list(req.box_id),
                res.reward)
        
        defer = DataBase().commit(data)
        defer.addCallback(self._reward_succeed, req, res, timer)
        return defer

    def _reward_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Reward union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Reward union donate succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _reward_failed(self, err, req, timer):
        logger.fatal("Reward union donate failed[reason=%s]" % err)
        res = internal_union_pb2.InternalGetBoxRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reward union donate failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def refresh(self, union_id, request):
        """刷新宝箱"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalRefreshBoxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_refresh, req, timer)
        defer.addErrback(self._refresh_failed, req, timer)
        return defer

    def _calc_refresh(self, data, req, timer):
        res = internal_union_pb2.InternalRefreshBoxRes()
        res.status = 0
        if not data.is_valid():
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._refresh_succeed(data, req, res, timer)
        member = member_business.find_member(data, req.user_id)
        if member is None:
            res.ret = union_pb2.UNION_NOT_MATCHED
            return self._refresh_succeed(data, req, res, timer)

        ret = donate_business.is_able_to_refresh_donate_box(data, req.box_id, req.user_id, timer)
        if ret != 0:
            res.ret = ret
        else:
            new_donate_box = donate_business.refresh_donate_box(data, req.box_id, timer)

            res.ret = union_pb2.UNION_OK
            pack.pack_donate_box_info(data, req.user_id, new_donate_box, res.box_info, timer)

        defer = DataBase().commit(data)
        defer.addCallback(self._refresh_succeed, req, res, timer)
        return defer

    def _refresh_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Refresh union donate box failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Refresh union donate box succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
                
        response = res.SerializeToString()
        return response
    
    def _refresh_failed(self, err, req, timer):
        logger.fatal("Refresh union donate box failed[reason=%s]" % err)
        res = internal_union_pb2.InternalRefreshBoxRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh union donate box failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
