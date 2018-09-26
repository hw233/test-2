#coding:utf8
"""
Created on 2016-05-18
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import unit_pb2
from proto import legendcity_pb2
from datalib.global_data import DataBase
from unit.data.position import UnitPositionInfo
from unit.business import city as city_business


class CityProcessor(object):

    def query(self, city_id, request):
        """查询史实城信息
        """
        timer = Timer(city_id)

        req = unit_pb2.UnitQueryLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        """查询逻辑
        """
        #如果史实城数据不存在，初始化（lazy，第一次访问时初始化）
        if not data.is_valid():
            if not city_business.init_city(data, timer.now):
                raise Exception("Init city failed")

        city_business.try_calc_today_tax_income(data, timer.now)

        rivals_info = []
        for index in range(0, len(req.rivals_id)):
            rivals_info.append((req.rivals_id[index], req.rivals_position_level[index]))

        #查询玩家自己的官职信息
        valid = True
        rematch_position_level = req.rematch_position_level
        user_position = city_business.query_user_position(data, req.user_id, timer.now)
        if rematch_position_level != 0 and user_position.level + 1 != rematch_position_level:
            logger.warning("Not able to rematch[user level=%d][rematch level=%d]" %
                    (user_position.level, req.rematch_position_level))
            valid = False
            rematch_position_level = 0

        (invalid_rivals, new_rivals) = city_business.query_position(
                data, req.user_id, user_position.level,
                rivals_info, timer.now, rematch_position_level)

        res = self._pack_query_response(data, user_position, invalid_rivals, new_rivals, valid)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _pack_query_response(self, data,
            user_position, invalid_rivals, new_rivals, valid = True):
        res = unit_pb2.UnitQueryLegendCityRes()

        city = data.city.get(True)
        res.status = 0
        if valid:
            res.ret = legendcity_pb2.OK
        else:
            res.ret = legendcity_pb2.USER_INVALID
        res.slogan = city.get_readable_slogan()
        res.update_slogan_free = city.is_change_slogan_free()
        res.tax = city.tax
        res.update_tax_free = city.is_change_tax_free()
        res.income_by_tax = city.tax_income

        res.position_level = user_position.level
        res.reputation = user_position.reputation

        res.invalid_rivals_id.extend(invalid_rivals)
        for position in new_rivals:
            res.rivals_id.append(position.user_id)
            res.rivals_is_robot.append(position.is_robot)
            res.rivals_position_level.append(position.level)

        return res


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query legend city succeed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query legend city failed[reason=%s]" % err)
        res = unit_pb2.UnitQueryLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query legend city failed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update(self, city_id, request):
        """更新史实城信息
        """
        timer = Timer(city_id)

        req = unit_pb2.UnitUpdateLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_update, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer


    def _calc_update(self, data, req, timer):
        """更新逻辑
        """
        slogan = None
        tax = None
        gold = 0
        if req.HasField("slogan"):
            slogan = req.slogan
        if req.HasField("tax"):
            tax = req.tax
        if req.HasField("gold"):
            gold = req.gold

        valid = city_business.is_able_to_update(data, req.user_id)
        if valid and not city_business.update(data, slogan, tax, gold):
            raise Exception("Update legend city failed")

        res = self._pack_update_response(data, valid)
        defer = DataBase().commit(data)
        defer.addCallback(self._update_succeed, req, res, timer)
        return defer


    def _pack_update_response(self, data, valid):
        res = unit_pb2.UnitUpdateLegendCityRes()
        res.status = 0
        if valid:
            res.ret = legendcity_pb2.OK
        else:
            res.ret = legendcity_pb2.USER_INVALID
        return res


    def _update_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Update legend city succeed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _update_failed(self, err, req, timer):
        logger.fatal("Update legend city failed[reason=%s]" % err)
        res = unit_pb2.UnitUpdateLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update legend city failed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def check(self, city_id, request):
        """核实信息
        """
        timer = Timer(city_id)

        req = unit_pb2.UnitCheckLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_check, req, timer)
        defer.addErrback(self._check_failed, req, timer)
        return defer


    def _calc_check(self, data, req, timer):
        """核实信息
        1 检查对手官职，有没有发生变化
        2 检查玩家官职，可以向对手发起攻击
        3 检查双方是否被锁定
        """
        id = UnitPositionInfo.generate_id(data.id, req.user_id)
        user_position = data.position_list.get(id, True)
        id = UnitPositionInfo.generate_id(data.id, req.rival_id)
        rival_position = data.position_list.get(id, True)

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
            res = self._pack_check_response(legendcity_pb2.OK)

        defer = DataBase().commit(data)
        defer.addCallback(self._check_succeed, req, res, timer)
        return defer


    def _pack_check_response(self, ret, unlock_time = 0):
        res = unit_pb2.UnitCheckLegendCityRes()
        res.status = 0
        res.ret = ret
        res.unlock_time = unlock_time
        return res


    def _check_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Check legend city info succeed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _check_failed(self, err, req, timer):
        logger.fatal("Check legend city info failed[reason=%s]" % err)
        res = unit_pb2.UnitCheckLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Check legend city info failed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def cancel_position(self, city_id, request):
        """取消官职
        """
        timer = Timer(city_id)
        req = unit_pb2.UnitCancelPositionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_cancel_position, req, timer)
        defer.addErrback(self._cancel_position_failed, req, timer)
        return defer


    def _calc_cancel_position(self, data, req, timer):
        #如果史实城数据不存在，初始化（lazy，第一次访问时初始化）
        if not data.is_valid():
            if not city_business.init_city(data, timer.now):
                raise Exception("Init city failed")

        #如果玩家被锁定，无法取消官职
        position_id = UnitPositionInfo.generate_id(data.id, req.user_id)
        user_position = data.position_list.get(position_id)
        if user_position is not None:
            user_position.check_lock_status(timer.now)
            if user_position.is_locked and req.force == False:
                logger.debug("User is locked[user_id=%d]" % req.user_id)
                res = self._pack_cancel_position_response(
                        legendcity_pb2.USER_LOCKED,
                        user_position.get_unlock_time(timer.now))
            else:
                city_business.cancel_position(data, user_position, timer.now)
                res = self._pack_cancel_position_response(legendcity_pb2.OK)
        else:
            res = self._pack_cancel_position_response(legendcity_pb2.OK)

        defer = DataBase().commit(data)
        defer.addCallback(self._cancel_position_succeed, req, res, timer)
        return defer


    def _pack_cancel_position_response(self, ret, unlock_time = None):
        res = unit_pb2.UnitCancelPositionRes()
        res.status = 0
        res.ret = ret
        if unlock_time is not None:
            res.unlock_time = unlock_time
        return res


    def _cancel_position_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Cancel position succeed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _cancel_position_failed(self, err, req, timer):
        logger.fatal("Cancel position failed[reason=%s]" % err)
        res = unit_pb2.UnitCancelPositionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Cancel position failed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_reputation(self, city_id, request):
        """添加声望，内部接口
        """
        timer = Timer(city_id)
        req = unit_pb2.UnitAddReputationReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_add_reputation, req, timer)
        defer.addCallback(self._add_reputation_succeed, req, timer)
        defer.addErrback(self._add_reputation_failed, req, timer)
        return defer


    def _calc_add_reputation(self, data, req, timer):
        position = data.position_list.get(
                UnitPositionInfo.generate_id(data.id, req.user_id))

        if req.reputation >= 0:
            position.gain_reputation(req.reputation)
        else:
            value = min(legendcity.reputation, -req.reputation)
            position.cost_reputation(value)

        defer = DataBase().commit(data)
        return defer


    def _add_reputation_succeed(self, data, req, timer):
        res = unit_pb2.UnitAddReputationRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Add reputation succeed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_reputation_failed(self, err, req, timer):
        logger.fatal("Add reputation failed[reason=%s]" % err)
        res = unit_pb2.UnitAddReputationRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add reputation failed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_city(self, city_id, request):
        """删除史实城，内部接口
        """
        timer = Timer(city_id)
        req = unit_pb2.UnitAddReputationReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._calc_delete_city, req, timer)
        defer.addCallback(self._delete_city_succeed, req, timer)
        defer.addErrback(self._delete_city_failed, req, timer)
        return defer


    def _calc_delete_city(self, data, req, timer):
        if not data.is_valid():
            return data

        data.delete()
        defer = DataBase().commit(data)
        defer.addCallback(self._delete_cache)
        return defer


    def _delete_cache(self, data):
        DataBase().clear_data(data)
        return data


    def _delete_city_succeed(self, data, req, timer):
        res = unit_pb2.UnitAddReputationRes()
        res.status = 0
        response = res.SerializeToString()

        logger.notice("Delete city succeed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_city_failed(self, err, req, timer):
        logger.fatal("Delete city failed[reason=%s]" % err)

        res = unit_pb2.UnitAddReputationRes()
        res.status = -1
        response = res.serializetostring()
        logger.notice("Delete city failed[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def get_position_rank(self, city_id, request):
        """获取官职榜
        """
        timer = Timer(city_id)
        req = unit_pb2.UnitGetPositionRankReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(city_id)
        defer.addCallback(self._get_position_rank_succeed, req, timer)
        defer.addErrback(self._get_position_rank_failed, req, timer)
        return defer


    def _get_position_rank_succeed(self, data, req, timer):
        res = unit_pb2.UnitGetPositionRankRes()
        res.status = 0

        position_list = data.position_list.get_all(True)
        for position in position_list:
            if position.level > 0:
                res.positions_level.append(position.level)
                res.users_id.append(position.user_id)
                res.users_is_robot.append(position.is_robot)

        response = res.SerializeToString()
        logger.notice("Get position rank succeed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _get_position_rank_failed(self, err, req, timer):
        logger.fatal("Get position rank failed[reason=%s]" % err)
        res = unit_pb2.UnitGetPositionRankRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Get position rank failed"
                "[city_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


