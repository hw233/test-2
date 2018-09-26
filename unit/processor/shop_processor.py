#coding:utf8
"""
Created on 2016-05-20
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城商店处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import unit_pb2
from proto import legendcity_pb2
from datalib.global_data import DataBase
from unit.data.position import UnitPositionInfo


class ShopProcessor(object):

    def buy_goods(self, city_id, request):
        """购买商品，需要缴税给太守
        """
        timer = Timer(city_id)

        req = unit_pb2.UnitBuyGoodsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_buy_goods, req, timer)
        defer.addErrback(self._buy_goods_failed, req, timer)
        return defer


    def _calc_buy_goods(self, data, req, timer):
        """缴税给太守
        """
        position = data.position_list.get(UnitPositionInfo.generate_id(data.id, req.user_id))
        if not position.cost_reputation(req.pay + req.extra_pay):
            raise Exception("Cost reputation failed")

        city = data.city.get()
        if req.tax != city.tax:
            return self._buy_goods_succeed(data, False, city.tax, req, timer)

        city.gain_tax_income(req.extra_pay)
        defer = DataBase().commit(data)
        defer.addCallback(self._buy_goods_succeed, True, city.tax, req, timer)
        return defer


    def _buy_goods_succeed(self, data, valid, tax, req, timer):
        res = unit_pb2.UnitBuyGoodsRes()
        res.status = 0
        if valid:
            res.ret = legendcity_pb2.OK
        else:
            res.ret = legendcity_pb2.TAX_CHANGED
        res.tax = tax
        position = data.position_list.get(
                UnitPositionInfo.generate_id(data.id, req.user_id), True)
        res.reputation = position.reputation
        response = res.SerializeToString()
        logger.notice("Buy goods succeed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _buy_goods_failed(self, err, req, timer):
        logger.fatal("Buy goods failed[reason=%s]" % err)
        res = unit_pb2.UnitBuyGoodsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Buy goods failed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

