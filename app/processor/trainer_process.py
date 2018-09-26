#coding:utf8
"""
Created on 2016-05-24
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 祈福相关逻辑
"""

from utils import logger
from utils.timer import Timer
from utils import utils
from proto import internal_pb2
from app import pack
from app import log_formater
from datalib.global_data import DataBase
from app.data.pray import PrayInfo
from app import log_formater


class TrainerProcessor(object):

    def add_kill_enemy_num(self, user_id, request):
        timer = Timer(user_id)
        req = internal_pb2.AddKillEnemyNumReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_kill_enemy_num, req, timer)
        defer.addCallback(self._add_kill_enemy_num_succeed, req, timer)
        defer.addErrback(self._add_kill_enemy_num_failed, req, timer)
        return defer


    def _calc_add_kill_enemy_num(self, data, req, timer):
        """
        """
        #更新资源
        trainer = data.trainer.get()
        trainer.add_kills(req.add_num)

        return DataBase().commit(data)


    def _add_kill_enemy_num_succeed(self, data, req, timer):
        res = internal_pb2.AddKillEnemyNumRes()
        res.status = 0
        response = res.SerializeToString()

        log = log_formater.output(data, "Add kill enemy num succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_kill_enemy_num_failed(self, err, req, timer):
        logger.fatal("Add kill enemy num failed[reason=%s]" % err)

        res = internal_pb2.AddKillEnemyNumRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add kill enemy num failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


