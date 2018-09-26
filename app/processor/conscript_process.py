#coding:utf8
"""
Created on 2015-05-14
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 征兵相关逻辑
"""
import time
from copy import deepcopy
from utils import logger
from utils import utils
from utils.timer import Timer
from utils.ret import Ret
from proto import conscript_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.hero import HeroInfo
from app.data.building import BuildingInfo
from app.business import conscript as conscript_business
from app.business import building as building_business
from app.business import account as account_business


class ConscriptProcessor(object):

    def start_conscript(self, user_id, request):
        timer = Timer(user_id)

        req = conscript_pb2.StartConscriptReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_conscript, req, timer)
        defer.addCallback(self._start_conscript_succeed, req, timer)
        defer.addErrback(self._start_conscript_failed, req, timer)
        return defer


    def _calc_start_conscript(self, data, req, timer):
        """开始执行征兵
        """
        resource = data.resource.get()

        conscript_building_id = BuildingInfo.generate_id(
                    data.id, req.building.city_basic_id,
                    req.building.location_index, req.building.basic_id)
        conscript_building = data.building_list.get(conscript_building_id)
        conscript = data.conscript_list.get(conscript_building_id)

        work_heroes = [] #来征兵的英雄
        for basic_id in req.building.hero_basic_ids:
            if basic_id == 0:
                work_heroes.append(None)
            else:
                hero_id = HeroInfo.generate_id(data.id, basic_id)
                hero = data.hero_list.get(hero_id)
                work_heroes.append(hero)

        resource.update_current_resource(timer.now)

        #将参与研究的英雄从其他建筑物中移除，更新原有建筑的影响
        #不结算英雄经验 : 英雄经验由客户端周期性请求结算
        #WARNING : 在上一次请求到此时英雄驻守的经验不结算
        for hero in work_heroes:
            if hero is not None and hero.is_working_in_building():
                building = data.building_list.get(hero.place_id)
                defense = None
                if building.is_defense():
                    defense = data.defense_list.get(building.id)
                if not building_business.remove_garrison(
                        building, hero, resource, timer.now):
                    raise Exception("Reassign build hero error")

        #所有生效的内政科技
        interior_technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]

        if not conscript_business.start_conscript(
                conscript, conscript_building, work_heroes,
                req.conscript.conscript_num, resource, interior_technologys, timer.now):
            raise Exception("Start conscript building failed")

        #compare.check_conscript(data, req.conscript, with_time = True)

        return DataBase().commit(data)


    def _start_conscript_succeed(self, data, req, timer):
        res = conscript_pb2.StartConscriptRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Start conscript succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_conscript_failed(self, err, req, timer):
        logger.fatal("Start conscript failed[reason=%s]" % err)
        res = conscript_pb2.StartConscriptRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start conscript failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_conscript(self, user_id, request):
        """补充征兵
        """
        timer = Timer(user_id)

        req = conscript_pb2.StartConscriptReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_conscript, req, timer)
        defer.addCallback(self._add_conscript_succeed, req, timer)
        defer.addErrback(self._add_conscript_failed, req, timer)
        return defer


    def _calc_add_conscript(self, data, req, timer):
        resource = data.resource.get(True)

        conscript_building_id = BuildingInfo.generate_id(
                data.id, req.conscript.city_basic_id,
                req.conscript.location_index, req.conscript.building_basic_id)
        conscript = data.conscript_list.get(conscript_building_id)

        resource.update_current_resource(timer.now)

        add_soldier_num = req.conscript.conscript_num - conscript.conscript_num
        if add_soldier_num < 0:
            raise Exception("Invalid add conscript[num=%d]" % add_soldier_num)

        if not conscript_business.add_conscript(
                conscript, resource, add_soldier_num, timer.now):
            raise Exception("Add conscript failed")

        #compare.check_conscript(data, req.conscript, with_time = True)

        return DataBase().commit(data)


    def _add_conscript_succeed(self, data, req, timer):
        res = conscript_pb2.StartConscriptRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        log = log_formater.output(data, "Add conscript succeed", req, res, timer.count_ms())
        logger.notice(log)

        response = res.SerializeToString()
        return response


    def _add_conscript_failed(self, err, req, timer):
        logger.fatal("Add conscript failed[reason=%s]" % err)
        res = conscript_pb2.StartConscriptRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add conscript failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def end_conscript(self, user_id, request):
        """
        结束征兵
        """
        return self._end_conscript(user_id, request)


    def end_conscript_with_gold(self, user_id, request):
        """花gold结束
        """
        return self._end_conscript(user_id, request, True)


    def _end_conscript(self, user_id, request, force = False):
        """
        force:  True 花费元宝提前结束征兵
                False 正常结束征兵
        """
        timer = Timer(user_id)

        req = conscript_pb2.EndConscriptReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_end_conscript, req, timer, force)
        #defer.addCallback(self._end_conscript_succeed, req, timer)
        defer.addErrback(self._end_conscript_failed, req, timer)
        return defer


    def _calc_end_conscript(self, data, req, timer, force):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        res = conscript_pb2.EndConscriptRes()
        res.status = 0

        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        user = data.user.get(True)
        resource = data.resource.get()

        conscript_building_id = BuildingInfo.generate_id(
                data.id, req.building.city_basic_id,
                req.building.location_index, req.building.basic_id)
        conscript_building = data.building_list.get(conscript_building_id)
        conscript = data.conscript_list.get(conscript_building_id)

        work_heroes = [] #来征兵的英雄
        work_heroes_id = conscript_building.get_working_hero()
        for hero_id in work_heroes_id:
            if hero_id == 0:
                work_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                work_heroes.append(hero)

        ret = Ret()
        if not conscript_business.end_conscript(data,
                conscript, conscript_building, resource, user, work_heroes, timer.now, force):
            if ret.get() == "NOT_CONSCRIPTING":
                res.ret = conscript_pb2.EndConscriptRes.NOT_CONSCRIPTING
                pack.pack_conscript_info(conscript, res.conscript, timer.now)
                pack.pack_building_info(conscript_building, res.building, timer.now)
                return self._end_conscript_succeed(data, req, res, timer)
            elif ret.get() == "CANNT_END":
                res.ret = conscript_pb2.EndConscriptRes.CANNT_END
                pack.pack_conscript_info(conscript, res.conscript, timer.now)
                pack.pack_building_info(conscript_building, res.building, timer.now)
                return self._end_conscript_succeed(data, req, res, timer)
            else:
                raise Exception('End conscript failed')

        #由于网络原因导致end_conscript一直重发，此处不check，直接返回
        #compare.check_conscript(data, req.conscript)   

        res.ret = conscript_pb2.EndConscriptRes.OK
        pack.pack_resource_info(data.resource.get(True), res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._end_conscript_succeed, req, res, timer)
        return defer


    def _end_conscript_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "End conscript succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _end_conscript_failed(self, err, req, timer):
        logger.fatal("End conscript failed[reason=%s]" % err)
        res = conscript_pb2.EndConscriptRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("End conscript failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def cancel_conscript(self, user_id, request):
        """
        取消征兵， 和结束征兵操作一样
        """
        timer = Timer(user_id)

        req = conscript_pb2.EndConscriptReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_cancel_conscript, req, timer)
        defer.addCallback(self._cancel_conscript_succeed, req, timer)
        defer.addErrback(self._cancel_conscript_failed, req, timer)
        return defer


    def _calc_cancel_conscript(self, data, req, timer):
        user = data.user.get(True)
        resource = data.resource.get()

        conscript_building_id = BuildingInfo.generate_id(
                data.id, req.building.city_basic_id,
                req.building.location_index, req.building.basic_id)
        conscript_building = data.building_list.get(conscript_building_id)
        conscript = data.conscript_list.get(conscript_building_id)

        work_heroes = [] #来征兵的英雄
        work_heroes_id = conscript_building.get_working_hero()
        for hero_id in work_heroes_id:
            if hero_id == 0:
                work_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                work_heroes.append(hero)

        if not conscript_business.cancel_conscript(data,
                conscript, conscript_building, resource, user, work_heroes, timer.now):
            raise Exception('End conscript failed')

        compare.check_conscript(data, req.conscript)

        return DataBase().commit(data)


    def _cancel_conscript_succeed(self, data, req, timer):
        res = conscript_pb2.EndConscriptRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Cancel conscript succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _cancel_conscript_failed(self, err, req, timer):
        logger.fatal("Cancel conscript failed[reason=%s]" % err)
        res = conscript_pb2.EndConscriptRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Cancel conscript failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


