#coding:utf8
"""
Created on 2016-03-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 充值相关处理逻辑
"""

from utils import logger
from utils import utils
from utils.timer import Timer
from proto import pay_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.business import pay as pay_business
from app.business import mission as mission_business


class PayProcessor(object):
    """充值相关逻辑
    """

    def query_pay(self, user_id, request):
        """查询充值商店信息
        """
        timer = Timer(user_id)

        req = pay_pb2.QueryPayShopReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_pay, req, timer)
        defer.addErrback(self._query_pay_failed, req, timer)
        return defer


    def _calc_query_pay(self, data, req, timer):
        """查询充值商店信息，如果到了刷新时间，则刷新
        """
        pay_ids = pay_business.query_pay(data, timer.now)
        if pay_ids is None:
            raise Exception("Query pay failed")

        res = self._pack_query_pay_response(data, pay_ids, timer.now)
        defer = DataBase().commit(data)
        defer.addCallback(self._query_pay_succeed, req, res, timer)
        return defer


    def _pack_query_pay_response(self, data, ids, now):
        """封装查询商店信息的响应
        """
        res = pay_pb2.QueryPayShopRes()
        res.status = 0

        for id in ids:
            res.orders.append(id)

        pay = data.pay.get(True)
        res.refresh_gap = pay.refresh_time - now
        return res


    def _query_pay_succeed(self, data, req, res, timer):
        """查询充值商店成功
        """
        response = res.SerializeToString()
        log = log_formater.output(data, "Query pay succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_pay_failed(self, err, req, timer):
        """查询充值商店失败
        """
        logger.fatal("Query pay failed[reason=%s]" % err)

        res = pay_pb2.QueryPayShopRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query pay failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start_pay(self, user_id, request):
        """开始进行购买
        """
        timer = Timer(user_id)

        req = pay_pb2.StartPayReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_pay, req, timer)
        defer.addErrback(self._start_pay_failed, req, timer)
        return defer


    def _calc_start_pay(self, data, req, timer):
        """开始购买，获得订单信息
        """
        value = None
        if req.HasField("value"):
            value = req.value

        (order_info, order_number) = pay_business.get_order(
                data, req.platform, req.order_id, timer.now, value)

        res = self._pack_start_pay_response(order_info, order_number)
        defer = DataBase().commit(data)
        defer.addCallback(self._start_pay_succeed, req, res, timer)
        return defer


    def _pack_start_pay_response(self, order_info, order_number):
        """封装开始购买的响应
        """
        res = pay_pb2.StartPayRes()
        res.status = 0
        res.order_info = order_info
        res.order_number = order_number
        return res


    def _start_pay_succeed(self, data, req, res, timer):
        """开始购买成功
        """
        response = res.SerializeToString()
        log = log_formater.output(data, "Start pay succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_pay_failed(self, err, req, timer):
        """开始购买失败
        """
        logger.fatal("Start pay failed[reason=%s]" % err)

        res = pay_pb2.StartPayRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start pay failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_pay(self, user_id, request):
        """完成购买
        """
        timer = Timer(user_id)

        req = pay_pb2.FinishPayReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_pay, req, timer)
        defer.addErrback(self._finish_pay_failed, req, timer)
        return defer


    def _calc_finish_pay(self, data, req, timer):
        """结束购买，验证，发放获得
        """
        (ret, update_paycard, items) = pay_business.pay_for_order(
                data, req.platform, req.order_number, req.pay_reply, timer.now)
        if not ret:
            raise Exception("Finish pay failed")

        #更新对应的月卡任务
        card_missions = []
        if update_paycard:
            mission_business.update_all_missions(data, timer.now)
            card_missions = mission_business.get_mission(
                    data, mission_business.MISSION_PAYCARD)

        res = self._pack_finish_pay_response(data, card_missions, items, req.order_number)
        defer = DataBase().commit(data)
        defer.addCallback(self._finish_pay_succeed, req, res, timer)
        return defer


    def _pack_finish_pay_response(self, data, missions, items, order_number):
        """封装结束购买的响应
        """
        res = pay_pb2.FinishPayRes()
        res.status = 0

        pack.pack_resource_info(data.resource.get(), res.resource)
        for mission in missions:
            pack.pack_mission_info(mission, res.missions.add())
        for (item_basic_id, item_num) in items:
            info = res.items.add()
            info.basic_id = item_basic_id
            info.num = item_num
        pack.pack_monarch_info(data.user.get(), res.monarchInfo)
        res.order_number = order_number
        return res


    def _finish_pay_succeed(self, data, req, res, timer):
        """结束购买成功
        """
        response = res.SerializeToString()
        logger.notice("Finish pay succeed[id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_pay_failed(self, err, req, timer):
        """结束购买失败
        """
        logger.fatal("Finish pay failed[reason=%s]" % err)

        res = pay_pb2.FinishPayRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish pay failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def patch_pay(self, user_id, request):
        """强行完成某种商品购买（不检查是否有支付回调）
        """
        timer = Timer(user_id)

        req = pay_pb2.FinishPayReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_patch_pay, req, timer)
        defer.addErrback(self._patch_pay_failed, req, timer)
        return defer


    def _calc_patch_pay(self, data, req, timer):
        """结束购买，验证，发放获得
        """
        order_id = int(req.pay_reply)
        (ret, update_paycard) = pay_business.patch_order(
                data, req.platform, order_id, req.order_number, timer.now)
        if not ret:
            raise Exception("Patch pay failed")

        #更新对应的月卡任务
        card_missions = []
        if update_paycard:
            mission_business.update_all_missions(data, timer.now)
            card_missions = mission_business.get_mission(
                    data, mission_business.MISSION_PAYCARD)

        defer = DataBase().commit(data)
        defer.addCallback(self._patch_pay_succeed, req, timer)
        return defer


    def _patch_pay_succeed(self, data, req, timer):
        """结束购买成功
        """
        res = pay_pb2.FinishPayRes()
        res.status = 0
        pack.pack_monarch_info(data.user.get(), res.monarchInfo)

        response = res.SerializeToString()
        logger.notice("Patch pay succeed[id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _patch_pay_failed(self, err, req, timer):
        """结束购买失败
        """
        logger.fatal("Patch pay failed[reason=%s]" % err)

        res = pay_pb2.FinishPayRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Patch pay failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def try_finish_pay_outside(self, user_id, request):
        """尝试完成在游戏外的支付，目前只支持soha
        """
        timer = Timer(user_id)

        req = pay_pb2.TryFinishPayOutsideReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_try_finish_pay_outside, req, timer)
        defer.addErrback(self._try_finish_pay_outside_failed, req, timer)
        return defer


    def _calc_try_finish_pay_outside(self, data, req, timer):
        """结束购买，验证，发放获得
        """
        (ret, update_paycard, items) = pay_business.try_finish_order_outside(
                data, req.platform, timer.now)
        if not ret:
            raise Exception("Try finish pay outside failed")

        #更新对应的月卡任务
        card_missions = []
        if update_paycard:
            mission_business.update_all_missions(data, timer.now)
            card_missions = mission_business.get_mission(
                    data, mission_business.MISSION_PAYCARD)

        res = self._pack_try_finish_pay_outside_response(data, card_missions, items)
        defer = DataBase().commit(data)
        defer.addCallback(self._try_finish_pay_outside_succeed, req, res, timer)
        return defer


    def _pack_try_finish_pay_outside_response(self, data, missions, items):
        """封装结束购买的响应
        """
        res = pay_pb2.TryFinishPayOutsideRes()
        res.status = 0

        pack.pack_resource_info(data.resource.get(), res.resource)
        for mission in missions:
            pack.pack_mission_info(mission, res.missions.add())
        for (item_basic_id, item_num) in items:
            info = res.items.add()
            info.basic_id = item_basic_id
            info.num = item_num
        pack.pack_monarch_info(data.user.get(), res.monarchInfo)
        #res.order_number = order_number
        return res


    def _try_finish_pay_outside_succeed(self, data, req, res, timer):
        """
        """
        response = res.SerializeToString()
        logger.notice("Try finish pay outside succeed[id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _try_finish_pay_outside_failed(self, err, req, timer):
        """
        """
        logger.fatal("Try finish pay outside failed[reason=%s]" % err)

        res = pay_pb2.TryFinishPayOutsideRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Try finish pay outside failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


