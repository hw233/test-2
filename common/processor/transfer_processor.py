#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场
"""

from common.data.transfer import TransferInfo
from proto import internal_pb2
from utils.timer import Timer
from utils.ret import Ret
from utils import logger
from datalib.global_data import DataBase
from common.business import transfer as transfer_business
from common.business import console as console_business
from common.transfer_matcher import TransferMatcher
from common import pack

class TransferProcessor(object):

    def query(self, common_id, request):
        """查询换位厌恶场排行榜"""
        timer = Timer(common_id)

        req = internal_pb2.InternalQueryTransferReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        transfer = transfer_business.get_transfer_by_user_id(data, req.user_id)
        if transfer == None:
            transfer = TransferInfo.create(data.id, req.user_id, TransferMatcher.MAX_RANK, False)
            data.transfer_list.add(transfer)

        top20 = TransferMatcher().get_top20(data)
        match = TransferMatcher().match(data, transfer)
        behind5 = TransferMatcher().get_behind5(data, transfer)
        
        res = internal_pb2.InternalQueryTransferRes()
        res.status = 0
        
        pack.pack_transfer_info(transfer, res.self, internal_pb2.InternalTransferInfo.SELF)
        for t in top20:
            pack.pack_transfer_info(t, res.top20.add(), internal_pb2.InternalTransferInfo.TOP)
        for m in match:
            pack.pack_transfer_info(m, res.match.add(), internal_pb2.InternalTransferInfo.MATCH)
        for b in behind5:
            pack.pack_transfer_info(b, res.behind5.add(), internal_pb2.InternalTransferInfo.BEHIND)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer

    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query transfer succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _query_failed(self, err, req, timer):
        logger.fatal("Query transfer failed[reason=%s]" % err)
        res = internal_pb2.InternalQueryTransferRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query transfer failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def exchange(self, common_id, request):
        """交换排名"""
        timer = Timer(common_id)

        req = internal_pb2.InternalExchangeTransferReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_exchange, req, timer)
        defer.addErrback(self._exchange_failed, req, timer)
        return defer

    def _calc_exchange(self, data, req, timer):
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        res = internal_pb2.InternalExchangeTransferRes()
        res.status = 0

        transfer = transfer_business.get_transfer_by_user_id(data, req.user_id)
        assert transfer != None
        target_transfer = transfer_business.get_transfer_by_user_id(data, req.target_user_id)
        assert target_transfer != None

        res.self_rank = transfer.rank
        res.rival_rank = target_transfer.rank

        if target_transfer.rank < transfer.rank and req.exchange:
            #if target_transfer.is_robot:
            #    transfer.rank = target_transfer.rank
            #    data.transfer_list.delete(target_transfer.id)
            #else:
            #    target_transfer.rank, transfer.rank = transfer.rank, target_transfer.rank
            target_transfer.rank, transfer.rank = transfer.rank, target_transfer.rank

        defer = DataBase().commit(data)
        defer.addCallback(self._exchange_succeed, req, res, timer)
        return defer

    def _exchange_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Exchange transfer succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _exchange_failed(self, err, req, timer):
        logger.fatal("Exchange transfer failed[reason=%s]" % err)
        res = internal_pb2.InternalQueryTransferRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Exchange transfer failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response
