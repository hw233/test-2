#coding:utf8
"""
Created on 2016-05-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 资源点保护相关逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import protection_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.node import NodeInfo
from app.data.item import ItemInfo
from app.business import protection as protection_business
from app.business import account as account_business


class ProtectionProcessor(object):

    def protect(self, user_id, request):
        """保护
        """
        timer = Timer(user_id)

        req = protection_pb2.ProtectReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_protect, req, timer)
        defer.addCallback(self._protect_succeed, req, timer)
        defer.addErrback(self._protect_failed, req, timer)
        return defer


    def _calc_protect(self, data, req, timer):
        """
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        node_id = NodeInfo.generate_id(data.id, req.node.basic_id)
        node = data.node_list.get(node_id)

        use_gold = req.node.protect.use_gold
        type = req.node.protect.type
        duration = req.node.protect.total_time

        if use_gold:
            item = None
        else:
            item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
            item = data.item_list.get(item_id)

        if not protection_business.protect(
                data, node, type, use_gold, duration, item, timer.now):
            raise Exception("Protect failed")

        return DataBase().commit(data)


    def _protect_succeed(self, data, req, timer):
        res = protection_pb2.ProtectRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Protect succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _protect_failed(self, err, req, timer):
        logger.fatal("Protect failed[reason=%s]" % err)
        res = protection_pb2.ProtectRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Protect failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


