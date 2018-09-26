#coding:utf8
"""
Created on 2016-07-04
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 跑马灯相关逻辑
"""

from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from utils import utils
from proto import broadcast_pb2
from proto import internal_pb2
from app import basic_view
from app import pack
from app import compare
from app import log_formater
from datalib.global_data import DataBase
from app.business import activity as activity_business
from app.business import mission as mission_business


class CommonProcessor(object):

    def query_notice(self, user_id, request):
        """查询所有公告
        """
        timer = Timer(user_id)

        req = broadcast_pb2.QueryBroadcastInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_query_notice, user_id, request, req, timer)
        defer.addErrback(self._query_notice_failed, req, timer)
        return defer


    def _calc_query_notice(self, basic_data, user_id, request, req, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._query_notice, basic_data, request, req, timer)
        return defer


    def _query_notice(self, data, basic_data, request, req, timer):
        #查询广播信息

        defer = GlobalObject().remote["common"].callRemote("query_broadcast_record", 1, request)
        defer.addCallback(self._check_query_broadcast_record_result, basic_data, data, req, timer)
        return defer


    def _check_query_broadcast_record_result(self, response, basic_data, data, req, timer):
        res = broadcast_pb2.QueryBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Query broadcast record result failed")

        #是否聊天禁言
        user = data.user.get(True)
        if user.chat_available:
            res.chat_available = True
        else:
            res.chat_available = False
        
        message_list = data.message_list.get_all()
        
        res.chat = 0
        for message in message_list:
            if message.status == 1:
                res.chat = 1
                break
            
         
        
        #更新活动
        if not activity_business.update_activity(basic_data, data, timer.now):
            raise Exception("Update activity failed")

        #更新任务
        mission_business.update_all_missions(data, timer.now)

        #主界面活动按钮等提示
        pack.pack_button_tips(basic_data, data, res, timer.now)


        defer = DataBase().commit(data)
        defer.addCallback(self._query_notice_succeed, req, res, timer)
        return defer


    def _query_notice_succeed(self, data, req, res, timer):
        logger.notice("Query notice succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))

        response = res.SerializeToString()
        logger.notice("Query notice succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_notice_failed(self, err, req, timer):
        logger.fatal("Query notice failed[reason=%s]" % err)

        res = broadcast_pb2.QueryBroadcastInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query notice failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_notice(self, user_id, request):
        """添加公告(内部请求)
        """
        timer = Timer(user_id)

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_notice, request, req, timer)
        defer.addErrback(self._add_notice_failed, req, timer)
        return defer


    def _calc_add_notice(self, data, request, req, timer):
        """
        """
        #查询广播信息
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_broadcast_record_result, data, req, timer)
        return defer


    def _check_add_broadcast_record_result(self, response, data, req, timer):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add broadcast record result failed")

        #log = log_formater.output(data, "Add notice succeed", req, res, timer.count_ms())
        #logger.notice(log)
        logger.notice("Add notice succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _add_notice_failed(self, err, req, timer):
        logger.fatal("Add notice failed[reason=%s]" % err)

        res = broadcast_pb2.AddBroadcastInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add notice failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_notice(self, user_id, request):
        """删除公告(内部请求)
        """
        timer = Timer(user_id)

        req = broadcast_pb2.DeleteBroadcastInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_delete_notice, request, req, timer)
        defer.addErrback(self._delete_notice_failed, req, timer)
        return defer


    def _calc_delete_notice(self, data, request, req, timer):
        """
        """
        #删除广播信息
        defer = GlobalObject().remote["common"].callRemote("delete_broadcast_record", 1, request)
        defer.addCallback(self._check_delete_broadcast_record_result, data, req, timer)
        return defer


    def _check_delete_broadcast_record_result(self, response, data, req, timer):
        res = broadcast_pb2.DeleteBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Delete broadcast record result failed")

        #log = log_formater.output(data, "Delete notice succeed", req, res, timer.count_ms())
        #logger.notice(log)
        logger.notice("Delete notice succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _delete_notice_failed(self, err, req, timer):
        logger.fatal("Delete notice failed[reason=%s]" % err)

        res = broadcast_pb2.DeleteBroadcastInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete notice failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def delete_common(self, user_id, request):
        """删除common（内部接口）
        """
        timer = Timer(user_id)
        req = internal_pb2.DeleteCommonReq()
        req.ParseFromString(request)

        defer = Deferred()
        defer.addCallback(self._calc_delete_common, 1, timer)
        defer.addCallback(self._delete_common_succeed, req, timer)
        defer.addErrback(self._delete_common_failed, req, timer)
        defer.callback(0)
        return defer


    def _calc_delete_common(self, status, common_id, timer):
        assert status == 0

        req = internal_pb2.DeleteCommonReq()
        defer = GlobalObject().remote['common'].callRemote(
                "delete_common", common_id, req.SerializeToString())
        defer.addCallback(self._check_delete_common, common_id, timer)
        return defer


    def _check_delete_common(self, response, common_id, timer):
        res = internal_pb2.DeleteCommonRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Delete common res failed[city_id=%d][res=%s]" % (common_id, res))

        return res.status


    def _delete_common_succeed(self, status, req, timer):
        res = internal_pb2.DeleteCommonRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Delete common succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _delete_common_failed(self, err, req, timer):
        logger.fatal("Delete common failed[reason=%s]" % err)
        res = internal_pb2.DeleteCommonRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete common failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


