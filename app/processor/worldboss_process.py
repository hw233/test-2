#coding:utf8
"""
Created on 2016-11-09
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 处理世界boss请求
"""

import base64
from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import internal_pb2
from proto import broadcast_pb2
from proto import boss_pb2
from datalib.global_data import DataBase
from app import basic_view
from app import pack
from app import compare
from app import log_formater
from app.business import worldboss as worldboss_business



class WorldBossProcessor(object):
    """处理世界boss相关逻辑
    """

    def query_worldboss(self, user_id, request):
        """查询世界boss信息
        """
        timer = Timer(user_id)

        req = boss_pb2.QueryWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._query_worldboss, user_id, req, timer)
        return defer


    def _query_worldboss(self, basic_data, user_id, req, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_worldboss, basic_data, req, timer)
        defer.addCallback(self._query_worldboss_succeed, req, timer)
        defer.addErrback(self._query_worldboss_failed, req, timer)
        return defer


    def _calc_query_worldboss(self, data, basic_data, req, timer):
        worldboss = data.worldboss.get()
        user = data.user.get(True)

        if not worldboss_business.update_worldboss(data, basic_data, worldboss, user.level, timer.now):
            raise Exception("Update worldboss error")

        #与common通信一次，更新boss的公共信息
        return self.query_common_worldboss(data, worldboss)


    def _query_worldboss_succeed(self, data, req, timer):
        res = boss_pb2.QueryWorldBossRes()
        res.status = 0

        #根据boss不同状态打包不同数据
        pack.pack_worldboss_info(data.worldboss.get(True), data.user.get(True),
                res.boss, timer.now)
        
        response = res.SerializeToString()
        log = log_formater.output(data, "Query worldboss succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_worldboss_failed(self, err, req, timer):
        logger.fatal("Query worldboss failed[reason=%s]" % err)

        res = boss_pb2.QueryWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query worldboss failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_worldboss_soldier_num(self, user_id, request):
        """查询世界boss血量
        """
        timer = Timer(user_id)

        req = boss_pb2.QueryWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_worldboss_soldier_num, req, timer)
        defer.addCallback(self._query_worldboss_soldier_num_succeed, req, timer)
        defer.addErrback(self._query_worldboss_soldier_num_failed, req, timer)
        return defer


    def _calc_query_worldboss_soldier_num(self, data, req, timer):
        """
        """
        worldboss = data.worldboss.get()
        #与common通信一次，更新boss的公共信息
        return self.query_common_worldboss(data, worldboss)


    def _query_worldboss_soldier_num_succeed(self, data, req, timer):
        res = boss_pb2.QueryWorldBossRes()
        res.status = 0

        #根据boss不同状态打包不同数据
        worldboss = data.worldboss.get(True)
        res.boss.current_soldier_num = worldboss.current_soldier_num
        res.boss.total_soldier_num = worldboss.total_soldier_num
        if worldboss.is_killed():
            res.boss.kill_user_name = base64.b64decode(worldboss.kill_user_name) 
            res.boss.kill_user_id = worldboss.kill_user_id
        
        response = res.SerializeToString()
        log = log_formater.output(data, "Query worldboss soldier num succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_worldboss_soldier_num_failed(self, err, req, timer):
        logger.fatal("Query worldboss soldier num failed[reason=%s]" % err)

        res = boss_pb2.QueryWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query worldboss soldier num failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_common_worldboss(self, data, worldboss):
        """同步世界boss信息
        Args:
        """
        if not worldboss.is_arised():
            return data

        req = boss_pb2.QueryCommonWorldBossReq()
        req.arise_time = worldboss.arise_time
        req.start_time = worldboss.start_time
        req.end_time = worldboss.end_time
        req.total_soldier_num = worldboss.total_soldier_num
        
        request = req.SerializeToString()

        logger.debug("sync worldboss[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("query_common_worldboss", 1, request)
        defer.addCallback(self._check_worldboss_result, data, worldboss)
        return defer


    def _check_worldboss_result(self, response, data, worldboss):
        res = boss_pb2.QueryCommonWorldBossRes()
        res.ParseFromString(response)
        worldboss.total_soldier_num = res.total_soldier_num
        worldboss.current_soldier_num = res.current_soldier_num
        worldboss.kill_user_name = res.kill_user_name
        worldboss.kill_user_id = res.kill_user_id

        if res.status != 0:
            raise Exception("Check query common worldboss result failed")

        return DataBase().commit(data)


    def modify_common_worldboss(self, user_id, request):
        """修改世界boss的公共信息
        """
        timer = Timer(user_id)

        req = boss_pb2.ModifyWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_modify_common_worldboss, request, req, timer)
        defer.addErrback(self._modify_common_worldboss_failed, req, timer)
        return defer


    def _calc_modify_common_worldboss(self, data, request, req, timer):
        defer = GlobalObject().remote["common"].callRemote("modify_common_worldboss", 1, request)
        defer.addCallback(self._check_modify_common_worldboss_result, data, req, timer)
        return defer


    def _check_modify_common_worldboss_result(self, response, data, req, timer):
        res = boss_pb2.ModifyWorldBossRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Check query common worldboss result failed")

        logger.notice("Modify worldboss succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms())) 
        return response


    def _modify_common_worldboss_failed(self, err, req, timer):
        logger.fatal("Modify common worldboss failed[reason=%s]" % err)

        res = boss_pb2.ModifyWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Modify common worldboss failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def clear_worldboss_merit(self, user_id, request):
        """清空玩家世界boss的战功
        """
        timer = Timer(user_id)

        req = boss_pb2.ClearWorldBossMeritReq()
        req.ParseFromString(request)

        defer = self._forward_clear_worldboss_merit(req.user_id, timer)
        defer.addCallback(self._clear_worldboss_merit_succeed, req, timer)
        defer.addErrback(self._clear_worldboss_merit_failed, req, timer)
        return defer


    def _forward_clear_worldboss_merit(self, user_id, timer):
        """向用户转发清空世界boss战功的请求
        """
        req = boss_pb2.ReceiveClearWorldBossMeritReq()
        request = req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_clear_worldboss_merit", user_id, request)
        defer.addCallback(self._check_forward_clear_worldboss_merit)
        return defer


    def _check_forward_clear_worldboss_merit(self, response):
        res = boss_pb2.ReceiveClearWorldBossMeritRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward clear worldboss merit failed")


    def _clear_worldboss_merit_succeed(self, data, req, timer):
        res = boss_pb2.ClearWorldBossMeritRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Clear worldboss merit succeed[req=%s][res=%s][consume=%d]" % (req, res, timer.count_ms()))

        return response


    def _clear_worldboss_merit_failed(self, err, req, timer):
        logger.fatal("Clear worldboss merit failed[reason=%s]" % err)

        res = boss_pb2.ClearWorldBossMeritRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Clear worldboss merit failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_clear_worldboss_merit(self, user_id, request):
        """帐号接收清空世界boss战功的请求
        """
        timer = Timer(user_id)

        req = boss_pb2.ReceiveClearWorldBossMeritReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_clear_worldboss_merit, req, timer)
        defer.addCallback(self._receive_clear_worldboss_merit_succeed, req, timer)
        defer.addErrback(self._receive_clear_worldboss_merit_failed, req, timer)
        return defer


    def _calc_receive_clear_worldboss_merit(self, data, req, timer):
        """
        """
        worldboss = data.worldboss.get()
        worldboss.clear_merit()
        
        defer = DataBase().commit(data)
        return defer


    def _receive_clear_worldboss_merit_succeed(self, data, req, timer):
        res = boss_pb2.ReceiveClearWorldBossMeritRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Receive clear worldboss merit succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        DataBase().clear_data(data) 
        return response


    def _receive_clear_worldboss_merit_failed(self, err, req, timer):
        logger.fatal("Receive clear worldboss merit failed[reason=%s]" % err)
        res = boss_pb2.ReceiveClearWorldBossMeritRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive clear worldboss merit failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


