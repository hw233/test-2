#coding:utf8
"""
Created on 2015-05-18
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief:  每日任务
"""

import time
import random
from copy import deepcopy
from utils import logger
from utils import utils
from utils.timer import Timer
from twisted.internet import defer
from proto import mission_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import compare
from app import pack
from app import log_formater
from app.business import mission as mission_business
from app.data.mission import MissionInfo


class MissionProcessor(object):

    def finish_mission(self, user_id, request):
        timer = Timer(user_id)

        req = mission_pb2.FinishMissionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_mission, req, timer)
        defer.addCallback(self._finish_mission_succeed, req, timer)
        defer.addErrback(self._finish_mission_failed, req, timer)

        return defer


    def _calc_finish_mission(self, data, req, timer):
        if not mission_business.finish_mission(req.mission.basic_id, data, timer.now):
            raise Exception("mission not finished.")

        #验证
        if req.HasField("monarch"):
            compare.check_user(data, req.monarch, with_level = True)
        for item_info in req.items:
            compare.check_item(data, item_info)

        #删除当前任务
        mission_id = MissionInfo.generate_id(data.id, req.mission.basic_id)
        data.mission_list.delete(mission_id)

        mission_data = data_loader.AllMission_dict[req.mission.basic_id]
        mission_name = mission_business.MissionPool().get_mission_name(req.mission.basic_id)
        if mission_data.type == mission_business.MISSION_TYPE_DAILY and  \
            mission_name != mission_business.MISSION_VITALITY and \
            mission_name != mission_business.MISSION_VIP_LEVEL:
            #记录次数
            trainer = data.trainer.get()
            trainer.add_daily_vitality(1)
        if mission_data.type >= 11 and mission_data.type <= 17 and \
            mission_name != mission_business.DAY7_MISSION_VITALITY:
            trainer = data.trainer.get()
            trainer.add_day7_vitality(1)

        return DataBase().commit(data)


    def _finish_mission_succeed(self, data, req, timer):
        """请求处理成功"""
        res = mission_pb2.FinishMissionRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        pack.pack_energy_info(data.energy.get(True), res.energy_info, timer.now)

        response = res.SerializeToString()
        log = log_formater.output(data, "Finish mission succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _finish_mission_failed(self, err, req, timer):
        logger.fatal("Finish mission failed[reason=%s]" % err)
        res = mission_pb2.FinishMissionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish mission failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def update_last_user_level(self, user_id, request):
        """内部接口:更新战力排行榜中第50名用户的等级"""
        timer = Timer(user_id)

        req = mission_pb2.UpdateLastUserLevelReq()
        req.ParseFromString(request)

        defer = mission_business.update_last_user_level()
        defer.addCallback(self._update_last_user_level_succeed, req, timer)
        defer.addErrback(self._update_last_user_level_failed, req, timer)
        return defer

    def _update_last_user_level_succeed(self, level, req, timer):
        res = mission_pb2.UpdateLastUserLevelRes()
        res.status = 0
        res.level = level
        
        response = res.SerializeToString()
        logger.notice("Update last user level succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _update_last_user_level_failed(self, err, req, timer):
        logger.fatal("Update last user level Failed[reason=%s]" % err)
        res = mission_pb2.UpdateLastUserLevelRes()
        res.status = -1
        
        response = res.SerializeToString()
        logger.notice("Update last user level Failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
