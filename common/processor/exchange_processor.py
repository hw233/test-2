#coding:utf8
"""
Created on 2016-11-22
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 兑换流程
"""
from utils.timer import Timer
from datalib.global_data import DataBase
from proto import exchange_pb2
from common.business import exchange as exchange_business
from common.data.exchange import CommonExchangeInfo
from common.business import console as console_business
from utils import logger

class ExchangeProcessor(object):
    """兑换流程"""
    
    def query(self, common_id, request):
        """查询公共兑换信息"""
        timer = Timer(common_id)
        
        req = exchange_pb2.QueryExchangeProportionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        exchange_business.refresh_exchange(data, timer.now)

        exchange = data.exchange.get()
        res = exchange_pb2.QueryExchangeProportionRes()
        res.status = 0
        res.money2food_exchange_ratio = exchange.money_proportion
        res.food2money_exchange_ratio = exchange.food_proportion
        res.next_fresh_ratio_time = \
            exchange.last_refresh_time + CommonExchangeInfo.refresh_time() - timer.now

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
        res = exchange_pb2.QueryExchangeProportionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response