#coding:utf8
"""
Created on 2015-10-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 随机事件处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import event_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app import compare
from app import log_formater
from app.data.node import NodeInfo
from app.business import map as map_business
from app.business import exploitation as exploitation_business
from app.business import visit as visit_business
from app.business import question as question_business
from app.business import account as account_business
from app.business import hero as hero_business


class EventProcessor(object):

    def upgrade(self, user_id, request):
        """升级关键点
        """
        timer = Timer(user_id)

        req = event_pb2.NodeUpgradeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade, req, timer)
        defer.addErrback(self._upgrade_failed, req, timer)
        return defer


    def _calc_upgrade(self, data, req, timer):
        """进行升级
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)
        gold = 0
        if req.HasField("gold"):
            gold = req.gold

        if not exploitation_business.finish_upgrade_event(data, node, timer.now, gold):
            raise Exception("Finish upgrade event failed")

        resource = data.resource.get(True)
        res = self._pack_upgrade_response(data, resource, node, timer.now)

        map_business.check_map_data(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._upgrade_succeed, req, res, timer)
        return defer


    def _pack_upgrade_response(self, data, resource, node, now):
        res = event_pb2.NodeUpgradeRes()
        res.status = 0
        pack.pack_node_info(data, node, res.node, now)
        pack.pack_resource_info(resource, res.resource)
        return res


    def _upgrade_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Upgrade node succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _upgrade_failed(self, err, req, timer):
        logger.fatal("Upgrade node failed[reason=%s]" % err)
        res = event_pb2.NodeUpgradeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Upgrade node failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start_visit(self, user_id, request):
        """开始探访
        """
        timer = Timer(user_id)

        req = event_pb2.StartEventVisitReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_visit, req, timer)
        defer.addErrback(self._start_visit_failed, req, timer)
        return defer


    def _calc_start_visit(self, data, req, timer):
        """开始探访逻辑
        """
        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)

        candidate = []
        if not visit_business.start_visit_event(data, node, candidate, timer.now):
            raise Exception("Start visit failed")

        res = self._pack_start_visit_response(candidate)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_visit_succeed, req, res, timer)
        return defer


    def _pack_start_visit_response(self, candidate):
        """打包开始探访的响应
        """
        res = event_pb2.StartEventVisitRes()
        res.status = 0
        for visit_id in candidate:
            res.visit_id.append(visit_id)
        return res


    def _start_visit_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Start visit succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_visit_failed(self, err, req, timer):
        logger.fatal("Start visit failed[reason=%s]" % err)
        res = event_pb2.StartEventVisitRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start visit failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def search_visit(self, user_id, request):
        """查询探访
        """
        timer = Timer(user_id)

        req = event_pb2.StartEventVisitReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_search_visit, req, timer)
        defer.addErrback(self._search_visit_failed, req, timer)
        return defer


    def _calc_search_visit(self, data, req, timer):
        """查询探访逻辑
        """
        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)

        candidate = []
        if not visit_business.search_visit_event(data, node, candidate, timer.now):
            raise Exception("Search visit failed")

        res = self._pack_search_visit_response(candidate)

        defer = DataBase().commit(data)
        defer.addCallback(self._search_visit_succeed, req, res, timer)
        return defer


    def _pack_search_visit_response(self, candidate):
        """打包查询探访的响应
        """
        res = event_pb2.StartEventVisitRes()
        res.status = 0
        for visit_id in candidate:
            res.visit_id.append(visit_id)
        return res


    def _search_visit_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Search visit succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _search_visit_failed(self, err, req, timer):
        logger.fatal("Search visit failed[reason=%s]" % err)
        res = event_pb2.StartEventVisitRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Search visit failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_visit(self, user_id, request):
        """结束探访
        """
        timer = Timer(user_id)

        req = event_pb2.FinishEventVisitReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_visit, req, timer)
        defer.addCallback(self._finish_visit_succeed, req, timer)
        defer.addErrback(self._finish_visit_failed, req, timer)
        return defer


    def _calc_finish_visit(self, data, req, timer):
        """结束探访逻辑
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)

        gold = 0
        if req.HasField("gold"):
            gold = req.gold

        candidate = []
        if not visit_business.finish_visit_event(data, node, req.visit_id, timer.now, gold):
            raise Exception("Finish visit failed")

        #验证
        if req.HasField("hero"):
            compare.check_hero(data, req.hero)
        if req.HasField("item"):
            compare.check_item(data, req.item)

        #获得S级武将要播广播
        if req.visit_id != 0:
            hero_basic_id = data_loader.EventVisitBasicInfo_dict[req.visit_id].heroBasicId
            if hero_basic_id != 0 and hero_business.is_need_broadcast(hero_basic_id):
                try:
                    self._add_get_hero_broadcast(data.user.get(), hero_basic_id)
                except:
                    logger.warning("Send get hero broadcast failed")

        return DataBase().commit(data)


    def _add_get_hero_broadcast(self, user, hero_basic_id):
        """广播玩家获得S级英雄数据
        Args:

        """
        (mode, priority, life_time, content) = hero_business.create_broadcast_content(user, hero_basic_id, type = 3)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add get hero visit broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_get_hero_broadcast_result)
        return defer


    def _check_add_get_hero_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast result failed")

        return True


    def _finish_visit_succeed(self, data, req, timer):
        res = event_pb2.FinishEventVisitRes()
        res.status = 0
        if req.HasField("hero"):
            hero = hero_business.get_hero_by_id(data, req.hero.basic_id, True)
            pack.pack_hero_info(hero, res.hero, timer.now)
        pack.pack_resource_info(data.resource.get(True), res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Finish visit succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _finish_visit_failed(self, err, req, timer):
        logger.fatal("Finish visit failed[reason=%s]" % err)
        res = event_pb2.FinishEventVisitRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish visit failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start_question(self, user_id, request):
        """开始问答
        """
        timer = Timer(user_id)

        req = event_pb2.StartEventQuestionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_question, req, timer)
        defer.addCallback(self._start_question_succeed, req, timer)
        defer.addErrback(self._start_question_failed, req, timer)
        return defer


    def _calc_start_question(self, data, req, timer):
        """开始问答逻辑
        """
        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)

        if not question_business.start_question_event(data, node, timer.now):
            raise Exception("Start question failed")

        return DataBase().commit(data)


    def _start_question_succeed(self, data, req, timer):
        res = event_pb2.StartEventQuestionRes()
        res.status = 0
        question = data.question.get(True)
        res.question_id = question.question_id

        response = res.SerializeToString()
        log = log_formater.output(data, "Start question succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_question_failed(self, err, req, timer):
        logger.fatal("Start question failed[reason=%s]" % err)
        res = event_pb2.StartEventQuestionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start question failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_question(self, user_id, request):
        """结束问答
        """
        timer = Timer(user_id)

        req = event_pb2.FinishEventQuestionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_question, req, timer)
        defer.addCallback(self._finish_question_succeed, req, timer)
        defer.addErrback(self._finish_question_failed, req, timer)
        return defer


    def _calc_finish_question(self, data, req, timer):
        """结束问答逻辑
        """
        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)

        if not question_business.finish_question_event(data, node,
                req.question_id, req.answer, req.correct, timer.now):
            raise Exception("Finish question failed")

        #验证
        if req.HasField("hero"):
            compare.check_hero(data, req.hero, with_level = True, with_soldier = True)
        for item_info in req.items:
            compare.check_item(data, item_info)

        return DataBase().commit(data)


    def _finish_question_succeed(self, data, req, timer):
        res = event_pb2.FinishEventQuestionRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Finish question succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _finish_question_failed(self, err, req, timer):
        logger.fatal("Finish question failed[reason=%s]" % err)
        res = event_pb2.FinishEventQuestionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish question failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


