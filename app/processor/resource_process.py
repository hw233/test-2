#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 资源相关逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import resource_pb2
from proto import internal_pb2
from datalib.data_proxy4redis import DataProxy
from datalib.global_data import DataBase
from app import pack
from app import log_formater
from app.business import account as account_business
from app.business import resource as resource_business
from datalib.data_dumper import DataDumper
from firefly.server.globalobject import GlobalObject


class ResourceProcessor(object):

    def exchange(self, user_id, request):
        timer = Timer(user_id)
        req = resource_pb2.UseGoldReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_exchange, req, timer)
        defer.addCallback(self._exchange_succeed, req, timer)
        defer.addErrback(self._exchange_failed, req, timer)
        return defer


    def _calc_exchange(self, data, req, timer):
        """
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        resource = data.resource.get()
        original_gold = resource.gold
        resource.update_current_resource(timer.now)

        lack_money = 0
        if req.HasField("lack_money"):
            lack_money = req.lack_money
        lack_food = 0
        if req.HasField("lack_food"):
            lack_food = req.lack_food

        need_gold = resource.gold_exchange_resource(lack_money, lack_food)
        if need_gold < 0:
            raise Exception("Gold exchange resource failed")

        # if req.use_gold != gold:
        #     raise Exception("Exchange with error gold[need gold=%d][use gold=%d]" %
        #             (gold, req.use_gold))

        log = log_formater.output_gold(data, -need_gold, log_formater.EXCHANGE_MONEY_FOOD,
                "Exchange money food by gold", money = lack_money, food = lack_food, before_gold = original_gold)
        logger.notice(log)

        return DataBase().commit(data)


    def _exchange_succeed(self, data, req, timer):
        res = resource_pb2.UseGoldRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Exchange succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _exchange_failed(self, err, req, timer):
        logger.fatal("Exchange failed[reason=%s]" % err)

        res = resource_pb2.UseGoldRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Exchange failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add(self, user_id, request):
        """增加/减少资源，内部测试用接口
        """
        timer = Timer(user_id)
        req = internal_pb2.AddResourceReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add, req, timer)
        defer.addCallback(self._add_succeed, req, timer)
        defer.addErrback(self._add_failed, req, timer)
        return defer


    def _calc_add(self, data, req, timer):
        """强制的添加/减少金钱、粮草、元宝
        """
        resource = data.resource.get()
        resource.update_current_resource(timer.now)
        original_gold = resource.gold

        if req.resource.money > 0:
            resource.gain_money(req.resource.money, True)
        elif req.resource.money < 0:
            resource.cost_money(-req.resource.money)

        if req.resource.food > 0:
            resource.gain_food(req.resource.food, True)
        elif req.resource.food < 0:
            resource.cost_food(-req.resource.food)

        if req.resource.gold > 0:
            resource.gain_gold(req.resource.gold)
            log = log_formater.output_gold(data, req.resource.gold, log_formater.OPERATE_GOLD,
                "Gain gold frome add", before_gold = original_gold)
            logger.notice(log)
        elif req.resource.gold < 0:
            resource.cost_gold(-req.resource.gold)
            log = log_formater.output_gold(data, -req.resource.gold, log_formater.OPERATE_GOLD,
                "Remove gold", before_gold = original_gold)
            logger.notice(log)

        if req.resource.achievement > 0:
            resource.gain_achievement(req.resource.achievement)
        elif req.resource.achievement < 0:
            resource.cost_achievement(-req.resource.achievement)

        if req.resource.soul > 0:
            resource.gain_soul(req.resource.soul)
        elif req.resource.soul < 0:
            resource.cost_soul(-req.resource.soul)

        return DataBase().commit(data)


    def _add_succeed(self, data, req, timer):
        res = internal_pb2.AddResourceRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Add resource succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_failed(self, err, req, timer):
        logger.fatal("Add resource failed[reason=%s]" % err)

        res = internal_pb2.AddResourceRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add resource failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def recalc(self, user_id, request):
        """内部接口,资源数据重算"""
        timer = Timer(user_id)

        req = internal_pb2.ReCalculationResourceReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_recalc, req, timer)
        defer.addCallback(self._recalc_succeed, req, timer)
        defer.addErrback(self._recalc_failed, req, timer)
        return defer

    def _calc_recalc(self, data, req, timer):
        resource = data.resource.get()

        if req.FOOD_OUTPUT in req.op:
            food_output = resource_business.recalc_food_output(data)
            resource.update_food_output(food_output)

        if req.FOOD_CAPACITY in req.op:
            food_capacity = resource_business.recalc_food_capacity(data)
            resource.update_food_capacity(food_capacity)

        if req.MONEY_OUTPUT in req.op:
            money_output = resource_business.recalc_money_output(data)
            resource.update_money_output(money_output)

        if req.MONEY_CAPACITY in req.op:
            money_capacity = resource_business.recalc_money_capacity(data)
            resource.update_money_capacity(money_capacity)

        return DataBase().commit(data)

    def _recalc_succeed(self, data, req, timer):
        resource = data.resource.get()

        res = internal_pb2.ReCalculationResourceRes()
        res.status = 0
        res.food_output = resource.food_output
        res.food_capacity = resource.food_capacity
        res.money_output = resource.money_output
        res.money_capacity = resource.money_capacity

        response = res.SerializeToString()

        log = log_formater.output(data, "Recalculation resource succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response

    def _recalc_failed(self, err, req, timer):
        logger.fatal("Recalculation resource failed[reason=%s]" % err)

        res = internal_pb2.ReCalculationResourceRes()
        res.status = -1
        response = res.SerializeToString()

        logger.notice("Recalculation resource failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def recalc_all(self, user_id, request):
        """内部接口:重算所有用户的资源数据"""
        timer = Timer(user_id)

        req = internal_pb2.ReCalculationResourceAllReq()
        req.ParseFromString(request)

        dumper = DataDumper()
        defer = dumper.get_all("user", "id")
        defer.addCallback(self._calc_recalc_all_dump, req, timer)
        defer.addErrback(self._recalc_all_failed, req, timer)
        return defer

    def _calc_recalc_all_dump(self, ids, req, timer):
        def _recalc(ids, index):
            user_id = ids[index]

            app_req = internal_pb2.ReCalculationResourceReq()
            app_req.user_id = user_id
            for op in req.op:
                app_req.op.append(op)
            
            app_request = app_req.SerializeToString()
            defer = GlobalObject().root.callChild(
                "portal", "forward_recalc_resource", user_id, app_request)
            defer.addCallback(_recalc_result, ids, index + 1)
            return defer

        def _recalc_result(response, ids, index):
            res = internal_pb2.ReCalculationResourceRes()
            res.ParseFromString(response)
            if res.status != 0:
                return False

            if index >= len(ids):
                return True

            defer = _recalc(ids, index)
            return defer

        defer = _recalc(ids, 0)
        defer.addCallback(self._calc_recalc_all_do, req, timer)
        return defer

    def _calc_recalc_all_do(self, result, req, timer):
        if result == False:
            raise Exception("Recalc resource failed")

        return self._recalc_all_succeed(req, timer)

    def _recalc_all_succeed(self, req, timer):
        res = internal_pb2.ReCalculationResourceAllRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Recalc all resource succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _recalc_all_failed(self, err, req, timer):
        logger.fatal("Recalc all resource failed[reason=%s]" % err)
        res = internal_pb2.ReCalculationResourceAllRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Recalc all resource failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
