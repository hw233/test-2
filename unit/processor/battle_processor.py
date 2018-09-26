#coding:utf8
"""
Created on 2016-05-20
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城商店处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import unit_pb2
from proto import legendcity_pb2
from datalib.global_data import DataBase
from unit.data.position import UnitPositionInfo
from unit.business import city as city_business


class BattleProcessor(object):


    def start_battle(self, city_id, request):
        """开始战斗
        """
        timer = Timer(city_id)

        req = unit_pb2.UnitCheckLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_start_battle, req, timer)
        defer.addErrback(self._start_battle_failed, req, timer)
        return defer


    def _calc_start_battle(self, data, req, timer):
        """开始战斗
        1 检查对手官职，有没有发生变化
        2 检查玩家官职，可以向对手发起攻击
        3 检查双方是否被锁定，锁定双方
        """
        id = UnitPositionInfo.generate_id(data.id, req.user_id)
        user_position = data.position_list.get(id)
        id = UnitPositionInfo.generate_id(data.id, req.rival_id)
        rival_position = data.position_list.get(id)

        user_position.check_lock_status(timer.now)
        rival_position.check_lock_status(timer.now)

        if rival_position.level != req.rival_position_level:
            res = self._pack_check_response(legendcity_pb2.RIVAL_INVALID)
        elif user_position.level + 1 != rival_position.level and not rival_position.is_leader():
            #对手不是太守，玩家官职不比对手低一级
            res = self._pack_check_response(legendcity_pb2.USER_INVALID)
        elif user_position.is_locked:
            res = self._pack_check_response(
                    legendcity_pb2.USER_LOCKED, user_position.get_unlock_time(timer.now))
        elif rival_position.is_locked:
            res = self._pack_check_response(
                    legendcity_pb2.RIVAL_LOCKED, rival_position.get_unlock_time(timer.now))
        else:
            #锁定双方
            user_position.lock(timer.now)
            rival_position.lock(timer.now)
            res = self._pack_check_response(legendcity_pb2.OK,
                    user_position_level = user_position.level,
                    rival_position_level = rival_position.level)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_battle_succeed, req, res, timer)
        return defer


    def _pack_check_response(self, ret, unlock_time = 0,
            user_position_level = None, rival_position_level = None):
        res = unit_pb2.UnitCheckLegendCityRes()
        res.status = 0
        res.ret = ret
        res.unlock_time = unlock_time
        if user_position_level is not None:
            res.user_position_level = user_position_level
        if rival_position_level is not None:
            res.rival_position_level = rival_position_level
        return res


    def _start_battle_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Start legend city battle succeed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _start_battle_failed(self, err, req, timer):
        logger.fatal("Start legend city battle failed[reason=%s]" % err)
        res = unit_pb2.UnitCheckLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start legend city battle failed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_battle(self, city_id, request):
        """结束战斗
        """
        timer = Timer(city_id)

        req = unit_pb2.UnitCheckLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_finish_battle, req, timer)
        defer.addErrback(self._finish_battle_failed, req, timer)
        return defer


    def _calc_finish_battle(self, data, req, timer):
        """结束战斗
        1 检查战斗时间是否超时，超时的战斗算失败
        2 解锁双方
        """
        id = UnitPositionInfo.generate_id(data.id, req.user_id)
        user_position = data.position_list.get(id)
        id = UnitPositionInfo.generate_id(data.id, req.rival_id)
        rival_position = data.position_list.get(id)

        user_position.check_lock_status(timer.now)
        rival_position.check_lock_status(timer.now)

        if not user_position.is_locked or not rival_position.is_locked:
            #如果玩家已经解锁，说明战斗超时了，或者请求错误
            res = self._pack_check_response(
                    legendcity_pb2.BATTLE_OVERTIME,
                    user_position_level = user_position.level,
                    rival_position_level = rival_position.level)
        else:
            #解锁双方
            user_position.unlock()
            rival_position.unlock()

            #结算战斗结果，如果战胜，交换官职
            if req.win:
                city_business.swap_position(data, user_position, rival_position, timer.now)

            res = self._pack_check_response(legendcity_pb2.OK,
                    user_position_level = user_position.level,
                    rival_position_level = rival_position.level)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_battle_succeed, req, res, timer)
        return defer


    def _finish_battle_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Finish legend city battle succeed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_battle_failed(self, err, req, timer):
        logger.fatal("Finish legend city battle failed[reason=%s]" % err)
        res = unit_pb2.UnitCheckLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish legend city battle failed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

