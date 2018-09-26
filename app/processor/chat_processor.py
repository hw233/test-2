#coding:utf8
"""
Created on 2016-07-07
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 聊天相关处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from utils.chat_pool import ChatPool
from proto import chat_pb2
from proto import union_pb2
from proto import internal_union_pb2
from datalib.global_data import DataBase
from app import log_formater


class ChatProcessor(object):
    """聊天
    """

    def start_chat(self, user_id, request):
        """开始聊天"""
        timer = Timer(user_id)
        req = chat_pb2.StartChatReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_chat, req, timer)
        defer.addErrback(self._start_chat_failed, req, timer)
        return defer


    def _calc_chat(self, data, req, timer):
        """
        """
        defer = Deferred()

        user = data.user.get(True)
        if not user.is_chat_available(timer.now):
            defer.addCallback(self._calc_invalid_chat, req, timer)
        elif req.type == req.WORLD:
            defer.addCallback(self._calc_world_chat, req, timer)
        elif req.type == req.UNION:
            flags = get_flags()
            if 'is_combined_chat' in flags:
                defer.addCallback(self._calc_world_chat, req, timer)
            else:
                defer.addCallback(self._calc_union_chat, req, timer)
        else:
            raise Exception("Not support chat type now[type=%d]" % req.type)

        defer.addCallback(self._start_chat_succeed, req, timer)
        defer.callback(data)
        return defer


    def _calc_invalid_chat(self, data, req, timer):
        res = chat_pb2.StartChatRes()
        res.status = 0
        res.available = False
        return res


    def _calc_world_chat(self, data, req, timer):
        #assert req.type == req.WORLD

        chat = ChatPool().get_world_chat_info()

        res = chat_pb2.StartChatRes()
        res.status = 0
        res.available = chat.available
        if res.available:
            res.hostname = chat.hostname
            res.port = chat.port
            res.roomname = chat.get_roomname()
            res.password = chat.password
        return res


    def _calc_union_chat(self, data, req, timer):
        #assert req.type == req.UNION

        union_req = internal_union_pb2.InternalStartUnionChatReq()
        union_req.user_id = data.id
        defer = GlobalObject().remote['gunion'].callRemote(
                "start_union_chat", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_union_chat_result, req, timer)
        return defer


    def _calc_union_chat_result(self, union_response, req, timer):
        union_res = internal_union_pb2.InternalStartUnionChatRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Start union chat res error")

        res = chat_pb2.StartChatRes()
        res.status = 0

        if union_res.ret != union_pb2.UNION_OK:
            res.available = False
        else:
            chat = ChatPool().get_union_chat_info()
            res.available = chat.available
            if res.available:
                res.hostname = chat.hostname
                res.port = chat.port
                res.roomname = union_res.roomname
                res.password = union_res.password
        return res


    def _start_chat_succeed(self, res, req, timer):
        response = res.SerializeToString()
        logger.notice("Start chat succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _start_chat_failed(self, err, req, timer):
        logger.fatal("Start chat failed[reason=%s]" % err)

        res = chat_pb2.StartChatRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start chat failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def manage(self, user_id, request):
        """管理聊天
        """
        timer = Timer(user_id)
        req = chat_pb2.ManageChatReq()
        req.ParseFromString(request)

        defer = GlobalObject().root.callChild("portal", "forward_chat_operation",
                req.target_user_id, request)
        defer.addCallback(self._calc_manage_result, req, timer)
        defer.addErrback(self._calc_manage_failed, req, timer)
        return defer


    def _calc_manage_result(self, app_response, req, timer):
        """
        """
        res = chat_pb2.ManageChatRes()
        res.ParseFromString(app_response)
        logger.notice("Manage chat succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return app_response


    def _calc_manage_failed(self, err, req, timer):
        logger.fatal("Manage chat failed[reason=%s]" % err)

        res = chat_pb2.ManageChatRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("mManage chat failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_operation(self, user_id, request):
        """接收命令: 封禁、解封
        """
        timer = Timer(user_id)
        req = chat_pb2.ManageChatReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_operation, req, timer)
        defer.addCallback(self._receive_operation_succeed, req, timer)
        defer.addErrback(self._receive_operation_failed, req, timer)
        return defer


    def _calc_receive_operation(self, data, req, timer):
        assert data.id == req.target_user_id
        user = data.user.get()

        if req.enable:
            user.enable_chat()
        else:
            lock_min = 0
            if req.HasField("lock_min"):
                lock_min = req.lock_min
            user.disable_chat(timer.now, lock_min)

        defer = DataBase().commit(data)
        return defer


    def _receive_operation_succeed(self, data, req, timer):
        res = chat_pb2.ManageChatRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Receive chat operation succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _receive_operation_failed(self, err, req, timer):
        logger.fatal("Start chat failed[reason=%s]" % err)

        res = chat_pb2.ManageChatRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive chat operation failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))
            
    return open_flags

