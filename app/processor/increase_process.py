#coding:utf8
"""
Created on 2016-05-07
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 资源点增产相关逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import increase_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.node import NodeInfo
from app.data.item import ItemInfo
from app.business import increase as increase_business
from app.business import account as account_business


class IncreaseProcessor(object):

    def increase(self, user_id, request):
        """增产
        """
        timer = Timer(user_id)

        req = increase_pb2.IncreaseReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_increase, req, timer)
        defer.addCallback(self._increase_succeed, req, timer)
        defer.addErrback(self._increase_failed, req, timer)
        return defer


    def _calc_increase(self, data, req, timer):
        """
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        node_id = NodeInfo.generate_id(data.id, req.node.basic_id)
        node = data.node_list.get(node_id)

        use_gold = req.node.increase.use_gold
        rate = req.node.increase.rate
        duration = req.node.increase.total_time

        if use_gold:
            item = None
        else:
            item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
            item = data.item_list.get(item_id)

        if not increase_business.increase(data, node, rate, use_gold, duration, item, timer.now):
            raise Exception("Increase failed")

        #记录次数
        trainer = data.trainer.get()
        trainer.add_daily_increase_item_num(1)

        return DataBase().commit(data)


    def _increase_succeed(self, data, req, timer):
        res = increase_pb2.IncreaseRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Increase succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _increase_failed(self, err, req, timer):
        logger.fatal("Increase failed[reason=%s]" % err)
        res = increase_pb2.IncreaseRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Increase failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


