#coding:utf8
"""
Created on 2016-05-24
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 祈福相关逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from utils import utils
from proto import pray_pb2
from proto import broadcast_pb2
from app import pack
from app import compare
from app import log_formater
from datalib.global_data import DataBase
from app.data.pray import PrayInfo
from app.business import pray as pray_business
from app import log_formater
from app.business import account as account_business


class PrayProcessor(object):

    def pray(self, user_id, request):
        timer = Timer(user_id)
        req = pray_pb2.PrayReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_pray, req, timer)
        defer.addCallback(self._pray_succeed, req, timer)
        defer.addErrback(self._pray_failed, req, timer)
        return defer


    def _calc_pray(self, data, req, timer):
        """
        """
        #更新资源
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        building_level = 0
        #找出寺庙
        for building in data.building_list.get_all(True):
            if building.is_temple():
                building_level = building.level
                break
        if building_level == 0:
            raise Exception("Pray failed, no temple")

        cost_gold = req.cost_gold if req.HasField("cost_gold") else 0
        if not pray_business.start_pray(data, req.pray_type, building_level, cost_gold):
            raise Exception("Pray failed")

        #记录次数
        trainer = data.trainer.get()
        trainer.add_daily_pray_num(1)

        return DataBase().commit(data)


    def _pray_succeed(self, data, req, timer):
        res = pray_pb2.PrayRes()
        res.status = 0
        pack.pack_pray_info(data.pray.get(True), res.pray_info, timer.now)
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Pray succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _pray_failed(self, err, req, timer):
        logger.fatal("Pray failed[reason=%s]" % err)

        res = pray_pb2.PrayRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Pray failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refresh_pray(self, user_id, request):
        timer = Timer(user_id)
        req = pray_pb2.PrayReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh_pray, req, timer)
        defer.addCallback(self._refresh_pray_succeed, req, timer)
        defer.addErrback(self._refresh_pray_failed, req, timer)
        return defer


    def _calc_refresh_pray(self, data, req, timer):
        """
        """
        if req.pray_type == PrayInfo.PRAY_ALL:
            #到期自动触发刷新
            pray = data.pray.get()

            if pray.is_able_to_reset(timer.now):
                pray.reset(timer.now)
                logger.debug("reset pray info")
            else:
                pray.calc_next_refresh_time(timer.now)
                logger.warning("calc next pray refresh time")

        else:
            #涉及到跨天的数据统计，所以此处要更新所有跨天数据
            if not account_business.update_across_day_info(data, timer.now):
                raise Exception("Update across day info failed")

            #玩家手动触发，刷新制定祈福类型
            cost_gold = 0
            if req.HasField("cost_gold"):
                cost_gold = req.cost_gold

            building_level = 0
            #找出寺庙
            for building in data.building_list.get_all(True):
                if building.is_temple():
                    building_level = building.level
                    break
            if building_level == 0:
                raise Exception("Refresh pray failed, no temple")

            original_gold = pray_business.refresh_pray(
                    data, req.pray_type, building_level, cost_gold, timer.now)[1]
            if not pray_business.refresh_pray(
                    data, req.pray_type, building_level, cost_gold, timer.now)[0]:
                raise Exception("Refresh pray failed")

            if cost_gold != 0:
                log = log_formater.output_gold(data, -cost_gold, log_formater.REFRESH_PRAY,
                    "Refresh pray by gold", before_gold = original_gold, pray_type = req.pray_type)
                logger.notice(log)

        return DataBase().commit(data)


    def _refresh_pray_succeed(self, data, req, timer):
        res = pray_pb2.PrayRes()
        res.status = 0
        pack.pack_pray_info(data.pray.get(True), res.pray_info, timer.now)
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Refresh pray succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _refresh_pray_failed(self, err, req, timer):
        logger.fatal("Refresh pray failed[reason=%s]" % err)

        res = pray_pb2.PrayRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh pray failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def choose_card(self, user_id, request):
        timer = Timer(user_id)
        req = pray_pb2.PrayReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_choose_card, req, timer)
        defer.addCallback(self._choose_card_succeed, req, timer)
        defer.addErrback(self._choose_card_failed, req, timer)
        return defer


    def _calc_choose_card(self, data, req, timer):
        """
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        cost_gold = 0
        if req.HasField("cost_gold"):
            cost_gold = req.cost_gold

        if not pray_business.choose_card(data, req.choose_index, cost_gold):
            raise Exception("Choose card failed")

        for item in req.item:
            compare.check_item(data, item)

        pray = data.pray.get()
        #if cost_gold != 0:
        #   log = log_formater.output_gold(data, -cost_gold, log_formater.CHOOSE_CARD,
        #       "Choose card by gold", choose_index = (pray.get_choose_card_num() + 1))
        #   logger.notice(log)

        if pray.is_need_broadcast():
            #祈福最后一次是翻倍的奖励发广播
            try:
                self._add_pray_broadcast(data.user.get(), pray)
            except:
                logger.warning("Send pray broadcast failed")

        return DataBase().commit(data)


    def _add_pray_broadcast(self, user, arena):
        """广播玩家祈福数据
        Args:

        """
        (mode, priority, life_time, content) = arena.create_broadcast_content(user)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add pray broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_pray_broadcast_result)
        return defer


    def _check_add_pray_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast result failed")

        return True


    def _choose_card_succeed(self, data, req, timer):
        res = pray_pb2.PrayRes()
        res.status = 0
        pack.pack_pray_info(data.pray.get(True), res.pray_info, timer.now)
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Choose card succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _choose_card_failed(self, err, req, timer):
        logger.fatal("Choose card failed[reason=%s]" % err)

        res = pray_pb2.PrayRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Choose card failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def giveup_pray(self, user_id, request):
        timer = Timer(user_id)
        req = pray_pb2.PrayReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_giveup_pray, req, timer)
        defer.addCallback(self._giveup_pray_succeed, req, timer)
        defer.addErrback(self._giveup_pray_failed, req, timer)
        return defer


    def _calc_giveup_pray(self, data, req, timer):
        """
        """
        pray = data.pray.get()

        if not pray.give_up():
            raise Exception("Giveup pray failed")

        return DataBase().commit(data)


    def _giveup_pray_succeed(self, data, req, timer):
        res = pray_pb2.PrayRes()
        res.status = 0
        pack.pack_pray_info(data.pray.get(True), res.pray_info, timer.now)
        response = res.SerializeToString()

        log = log_formater.output(data, "Giveup pray succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _giveup_pray_failed(self, err, req, timer):
        logger.fatal("Giveup pray failed[reason=%s]" % err)

        res = pray_pb2.PrayRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Giveup pray failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


