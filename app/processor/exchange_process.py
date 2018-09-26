#coding:utf8
"""
Created on 2016-11-22
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 兑换流程
"""

from utils.timer import Timer
from utils import logger
from firefly.server.globalobject import GlobalObject
from datalib.global_data import DataBase
from proto import exchange_pb2
from app.business import exchange as exchange_business
from app import pack

class ExchangeProcessor(object):
    """兑换流程"""

    def query(self, user_id, request):
        """查询兑换信息"""
        timer = Timer(user_id)

        req = exchange_pb2.QueryExchangeInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        comm_req = exchange_pb2.QueryExchangeProportionReq()
        comm_req.user_id = data.id
        defer = GlobalObject().remote["common"].callRemote(
            "query_exchange_info", 1, comm_req.SerializeToString())
        defer.addCallback(self._calc_query_proportion, data, req, timer)
        return defer

    def _calc_query_proportion(self, comm_response, data, req, timer):
        comm_res = exchange_pb2.QueryExchangeProportionRes()
        comm_res.ParseFromString(comm_response)
        if comm_res.status != 0:
            raise Exception("query exchange proportion failed")
        
        exchange_business.reset_exchange_num(data, timer.now)

        user = data.user.get(True)

        res = exchange_pb2.QueryExchangeInfoRes()
        res.status = 0
        res.ret = exchange_pb2.EXCHANGE_OK
        res.exchange_info.food2money_exchange_ratio = comm_res.food2money_exchange_ratio
        res.exchange_info.money2food_exchange_ratio = comm_res.money2food_exchange_ratio
        res.exchange_info.exchange_num = user.exchange_num
        res.exchange_info.next_fresh_ratio_time = comm_res.next_fresh_ratio_time

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer
    
    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query exchange info succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _query_failed(self, err, req, timer):
        logger.fatal("Query exchange info failed[reason=%s]" % err)
        res = exchange_pb2.QueryExchangeInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query exchange info failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def exchange(self, user_id, request):
        """兑换"""
        timer = Timer(user_id)

        req = exchange_pb2.ExchangeReq()
        req.ParseFromString(request)
        
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_exchange, req, timer)
        defer.addErrback(self._exchange_failed, req, timer)
        return defer

    def _calc_exchange(self, data, req, timer):
        comm_req = exchange_pb2.QueryExchangeProportionReq()
        comm_req.user_id = data.id
        defer = GlobalObject().remote["common"].callRemote(
            "query_exchange_info", 1, comm_req.SerializeToString())
        defer.addCallback(self._calc_exchange_proportion, data, req, timer)
        return defer

    def _calc_exchange_proportion(self, comm_response, data, req, timer):
        comm_res = exchange_pb2.QueryExchangeProportionRes()
        comm_res.ParseFromString(comm_response)

        if comm_res.status != 0:
            raise Exception("query exchange proportion failed")

        if not exchange_business.check_exchange_req(data, req, 
            comm_res.food2money_exchange_ratio, comm_res.money2food_exchange_ratio):
            res = exchange_pb2.ExchangeRes()
            res.status = 0
            res.ret = exchange_pb2.EXCHANGE_INVALID

            defer = DataBase().commit(data)
            defer.addCallback(self._exchange_succeed, req, res, timer)
            return defer

        exchange_type = req.type
        exchange_able = exchange_business.is_able_to_exchange(
            data, req.money, req.food, exchange_type, timer.now)
        if exchange_able != True:
            res = exchange_pb2.ExchangeRes()
            res.status = 0
            res.ret = exchange_able

            defer = DataBase().commit(data)
            defer.addCallback(self._exchange_succeed, req, res, timer)
            return defer
        
        if exchange_type == exchange_business.MONEY_TO_FOOD:
            exchange_business.money_exchange(data, req.money, req.food, timer.now)
        else:
            exchange_business.food_exchange(data, req.money, req.food, timer.now)
        
        user = data.user.get(True)
        resource = data.resource.get(True)

        res = exchange_pb2.ExchangeRes()
        res.status = 0
        res.ret = exchange_pb2.EXCHANGE_OK
        pack.pack_resource_info(resource, res.resource)
        res.exchange_num = user.exchange_num

        defer = DataBase().commit(data)
        defer.addCallback(self._exchange_succeed, req, res, timer)
        return defer

    def _exchange_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Exchange succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _exchange_failed(self, err, req, timer):
        logger.fatal("Exchange failed[reason=%s]" % err)
        res = exchange_pb2.ExchangeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Exchange failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response