#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 广播数据处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import broadcast_pb2
from datalib.global_data import DataBase
from common.business import broadcast as broadcast_business
from common.business import console as console_business


class BroadcastProcessor(object):

    def query(self, common_id, request):
        """查询广播信息
        """
        timer = Timer(common_id)

        req = broadcast_pb2.QueryBroadcastInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        """查询广播逻辑
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")
        logger.notice("1111111111")
        broadcast_list = broadcast_business.query_broadcast(data, timer.now)
        logger.notice("BROAD")

        res = broadcast_pb2.QueryBroadcastInfoRes()
        res.status = 0
        for broadcast in broadcast_list:
            record = res.records.add()
            record.mode_id = broadcast.mode_id
            record.passed_time = 0 #to delete in next version
            record.content = broadcast.get_readable_content()
            record.id = broadcast.id

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query broadcast succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query broadcast failed[reason=%s]" % err)
        res = broadcast_pb2.QueryBroadcastInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query broadcast failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def add(self, common_id, request):
        """添加广播信息
        """
        timer = Timer(common_id)

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_add, req, timer)
        defer.addErrback(self._add_failed, req, timer)
        return defer


    def _calc_add(self, data, req, timer):
        """添加广播逻辑
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        if not broadcast_business.add_broadcast(
                data, timer.now, req.mode_id, req.priority, req.life_time, req.content):
            raise Exception("Add broadcast failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._add_succeed, req, timer)
        return defer


    def _add_succeed(self, data, req, timer):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Add broadcast succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _add_failed(self, err, req, timer):
        logger.fatal("Add broadcast failed[reason=%s]" % err)
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add broadcast failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def delete(self, common_id, request):
        """删除广播信息
        """
        timer = Timer(common_id)

        req = broadcast_pb2.DeleteBroadcastInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_delete, req, timer)
        defer.addErrback(self._delete_failed, req, timer)
        return defer


    def _calc_delete(self, data, req, timer):
        """删除广播逻辑
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        if not broadcast_business.delete_broadcast(
                data, timer.now, req.ids):
            raise Exception("Delete broadcast failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._delete_succeed, req, timer)
        return defer


    def _delete_succeed(self, data, req, timer):
        res = broadcast_pb2.DeleteBroadcastInfoRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Delete broadcast succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _delete_failed(self, err, req, timer):
        logger.fatal("Delete broadcast failed[reason=%s]" % err)
        res = broadcast_pb2.DeleteBroadcastInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete broadcast failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


