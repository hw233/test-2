#coding:utf8
"""
Created on 2016-07-07
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 处理开红包的相关的请求
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import item_pb2
from proto import chest_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.resource import ResourceInfo
from app.data.item import ItemInfo
from app.business import item as item_business
from app.business import chest as chest_business


class ChestProcessor(object):

    def open_chest(self, user_id, request):
        """打开红包，获得奖励"""
        timer = Timer(user_id)

        req = chest_pb2.OpenChestReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_open_chest, req, timer)
        defer.addErrback(self._open_chest_failed, req, timer)
        return defer


    def _calc_open_chest(self, data, req, timer):
        """打开红包
            Args:
        """
        chest = data.chest.get()
        chest_old = chest_business.open_chest(data, chest, timer.now)
        if chest_old is None:
            raise Exception("Open chest failed")
        
        for i in range(0, len(req.items)):
            compare.check_item(data, req.items[i])

        #广播
        try:
            self._add_chest_broadcast(data, chest_old.gold)
        except:
            logger.warning("Send open chest broadcast failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._open_chest_succeed, req, chest_old, timer)
        return defer
    

    def _add_chest_broadcast(self, data, gold):
        (mode_id, priority, life_time, content) = chest_business.create_broadcast(
                data, gold)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add chest broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_chest_broadcast_result)
        return defer


    def _check_add_chest_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add chest broadcast result failed")

        return True


    def _open_chest_succeed(self, data, req, chest, timer):
        res = chest_pb2.OpenChestRes()
        res.status = 0

        pack.pack_chest_info(chest, res.chest, timer.now)
        pack.pack_resource_info(data.resource.get(True), res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Open chest succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _open_chest_failed(self, err, req, timer):
        logger.fatal("Open chest failed[reason=%s]" % err)

        res = chest_pb2.OpenChestRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Open chest failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_chest(self, user_id, request):
        """查询红包
        """
        timer = Timer(user_id)

        req = chest_pb2.QueryChestReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_chest, req, timer)
        defer.addCallback(self._query_chest_succeed, req, timer)
        defer.addErrback(self._query_chest_failed, req, timer)
        return defer


    def _calc_query_chest(self, data, req, timer):
        """打开红包
        Args:
        """
        chest = data.chest.get()
        if not chest_business.query_chest(chest, timer.now):
            raise Exception("Query chest failed")

        return DataBase().commit(data)


    def _query_chest_succeed(self, data, req, timer):
        res = chest_pb2.QueryChestRes()
        res.status = 0

        pack.pack_chest_info(data.chest.get(True), res.chest, timer.now)
        #pack.pack_resource_info(data.resource.get(True), res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Query chest succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_chest_failed(self, err, req, timer):
        logger.fatal("Query chest failed[reason=%s]" % err)

        res = chest_pb2.QueryChestRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query chest failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



