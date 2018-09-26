#coding:utf8
"""
Created on 2016-05-18
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 资源相关逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import energy_pb2
from datalib.global_data import DataBase
from app import pack
from app import log_formater
from app.business import energy as energy_business
from app import log_formater
from app.business import account as account_business


class EnergyProcessor(object):

    def buy_energy(self, user_id, request):
        timer = Timer(user_id)
        req = energy_pb2.BuyEnergyReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_buy_energy, req, timer)
        defer.addCallback(self._buy_energy_succeed, req, timer)
        defer.addErrback(self._buy_energy_failed, req, timer)
        return defer


    def _calc_buy_energy(self, data, req, timer):
        """
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        energy = data.energy.get()
        energy.update_current_energy(timer.now)

        need_gold, original_gold = energy_business.buy_energy(data, energy, timer.now)
        if need_gold < 0:
            raise Exception("Buy energy failed")

        #记录次数
        trainer = data.trainer.get()
        trainer.add_daily_buy_energy_num(1)

        log = log_formater.output_gold(data, -need_gold, log_formater.BUY_ENERGY,
                "Buy energy by gold", before_gold = original_gold, energy = energy.get_energy_num_of_buy())
        logger.notice(log)

        return DataBase().commit(data)


    def _buy_energy_succeed(self, data, req, timer):
        res = energy_pb2.BuyEnergyRes()
        res.status = 0
        pack.pack_energy_info(data.energy.get(True), res.energy_info, timer.now)
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Buy energy succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _buy_energy_failed(self, err, req, timer):
        logger.fatal("Buy energy failed[reason=%s]" % err)

        res = energy_pb2.BuyEnergyRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Buy energy failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refresh_energy(self, user_id, request):
        timer = Timer(user_id)
        req = energy_pb2.RefreshEnergyInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh_energy, req, timer)
        defer.addCallback(self._refresh_energy_succeed, req, timer)
        defer.addErrback(self._refresh_energy_failed, req, timer)
        return defer


    def _calc_refresh_energy(self, data, req, timer):
        """
        """
        energy = data.energy.get()
        energy.update_current_energy(timer.now)

        if not energy_business.refresh_energy(data, energy, timer.now):
            raise Exception("Refresh energy failed")

        return DataBase().commit(data)


    def _refresh_energy_succeed(self, data, req, timer):
        res = energy_pb2.RefreshEnergyInfoRes()
        res.status = 0
        pack.pack_energy_info(data.energy.get(True), res.energy_info, timer.now)
        response = res.SerializeToString()

        log = log_formater.output(data, "Refresh energy succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _refresh_energy_failed(self, err, req, timer):
        logger.fatal("Refresh energy failed[reason=%s]" % err)

        res = energy_pb2.RefreshEnergyInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh energy failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


