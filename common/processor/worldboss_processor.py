#coding:utf8
"""
Created on 2016-11-09
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 世界boss处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import boss_pb2
from datalib.global_data import DataBase
from common.business import worldboss as worldboss_business
from common.business import console as console_business


class WorldBossProcessor(object):

    def query(self, common_id, request):
        """查询世界boss公共信息
        """
        timer = Timer(common_id)

        req = boss_pb2.QueryCommonWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        """查询逻辑
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        worldboss = data.worldboss.get()

        arise_time = 0
        start_time = 0
        end_time = 0
        boss_id = 0
        total_soldier_num = 0
        kills_addition = 0
        user_id = 0
        user_name = ''
        if req.HasField("arise_time"):
            arise_time = req.arise_time
        if req.HasField("start_time"):
            start_time = req.start_time
        if req.HasField("end_time"):
            end_time = req.end_time
        if req.HasField("boss_id"):
            boss_id = req.boss_id
        if req.HasField("total_soldier_num"):
            total_soldier_num = req.total_soldier_num
        if req.HasField("kills_addition"):
            kills_addition = req.kills_addition
        if req.HasField("user_id"):
            user_id = req.user_id
        if req.HasField("user_name"):
            user_name = req.user_name

        if not worldboss_business.update_worldboss(data, timer.now, arise_time, 
                start_time, end_time, boss_id, kills_addition, total_soldier_num,
                user_id, user_name):
            raise Exception("Update worldboss failed")

        
        res = boss_pb2.QueryCommonWorldBossRes()
        res.status = 0
        res.total_soldier_num = worldboss.get_total_soldier_num()
        res.current_soldier_num = worldboss.get_current_soldier_num()
        if worldboss.is_dead():
            res.kill_user_name = worldboss.kill_user_name
            res.kill_user_id = worldboss.kill_user_id

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query common worldboss succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query common worldboss failed[reason=%s]" % err)
        res = boss_pb2.QueryCommonWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query common worldboss failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def modify(self, common_id, request):
        """修改世界boss公共信息
        """
        timer = Timer(common_id)

        req = boss_pb2.ModifyWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_modify, req, timer)
        defer.addErrback(self._modify_failed, req, timer)
        return defer


    def _calc_modify(self, data, req, timer):
        """修改逻辑
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        worldboss = data.worldboss.get()
        if req.HasField("total_soldier_num"):
            worldboss.total_soldier_num = req.total_soldier_num

        if req.HasField("current_soldier_num"):
            worldboss.current_soldier_num = req.current_soldier_num
             
        if req.HasField("kill_user_name"):
            worldboss.kill_user_name = req.kill_user_name

        if req.HasField("kill_user_id"):
            worldboss.kill_user_id = req.kill_user_id

        res = boss_pb2.ModifyWorldBossRes()
        res.status = 0

        defer = DataBase().commit(data)
        defer.addCallback(self._modify_succeed, req, res, timer)
        return defer


    def _modify_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Modify common worldboss succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _modify_failed(self, err, req, timer):
        logger.fatal("Modify common worldboss failed[reason=%s]" % err)
        res = boss_pb2.ModifyWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Modify common worldboss failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


