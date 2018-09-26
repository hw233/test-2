#coding:utf8
"""
Created on 2015-02-04
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 将星盘相关流程
"""

from utils.timer import Timer
from utils import logger
from app.business import herostar as herostar_business
from app.business import hero as hero_business
from app.business import building as building_business
from app.data.hero import HeroInfo
from app.data.herostar import HeroStarInfo
from proto import herostar_pb2
from proto import broadcast_pb2
from app.user_view import UserData
from datalib.global_data import DataBase
from app import pack
from app import log_formater
from firefly.server.globalobject import GlobalObject

class HeroStarProcessor(object):
    """将星盘相关流程"""

    def strength(self, user_id, request):
        """将星升级"""
        timer = Timer(user_id)

        req = herostar_pb2.StrengthHeroStarReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_strength, req, timer)
        defer.addCallback(self._strength_succeed, req, timer)
        defer.addErrback(self._strength_failed, req, timer)
        return defer

    def _calc_strength(self, data, req, timer):
        herostar = herostar_business.get_herostar_by_id(data, req.hero_star)
        if herostar is None:
            raise Exception("No Such HeroStar")

        next_star_id = HeroStarInfo.get_next_level_id(req.hero_star)
        if next_star_id == 0:
            raise Exception("Hero star is full level")

        if not herostar_business.is_micefu_level_ok(data, req.hero_star):
            raise Exception("Micefu's' level dissatisfaction")
        
        (items_id, items_num) = herostar_business.get_strength_items(data, req.hero_star)
        if not herostar_business.validate_items(data, items_id, items_num, req.item):
            raise Exception("Bad items")

        cost_money = herostar_business.get_cost_money(data, req.hero_star)
        herostar_business.strength_herostar(data, req.hero_star, items_id, items_num, cost_money, timer)
       
        #将星收集同种几件套效果的广播
        if herostar_business.is_need_broadcast(data, req.hero_star):
            try:
                constellation_num = herostar_business.calc_herostar_constellations_num(data, req.hero_star)
                self._add_get_herostar_broadcast(data, req.hero_star, constellation_num)
            except:
                logger.warning("Send get herostar broadcast failed")

        #将星升级到3级及以上的广播
        if herostar_business.is_need_broadcast_of_upgrade(data, req.hero_star):
            try:
                self._add_upgrade_herostar_broadcast(data, req.hero_star)
            except:
                logger.warning("Send upgrade herostar broadcast failed")

        return DataBase().commit(data)

    def _add_get_herostar_broadcast(self, data, star_id, constellation_num):
        (mode_id, priority, life_time, content) = herostar_business.create_broadcast(
                data, HeroStarInfo.get_constellation_id(star_id), constellation_num)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add get herostar visit broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_herostar_broadcast_result)
        return defer


    def _add_upgrade_herostar_broadcast(self, data, star_id):
        (mode_id, priority, life_time, content) = herostar_business.create_broadcast_of_upgrade(
                data, star_id)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add upgrade herostar broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_herostar_broadcast_result)
        return defer


    def _check_add_herostar_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast result failed")

        return True


    def _strength_succeed(self, data, req, timer):
        res = herostar_pb2.StrengthHeroStarRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Strength hero star succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response

    def _strength_failed(self, err, req, timer):
        logger.fatal("Strength hero star failed[reason=%s]" % err)

        res = herostar_pb2.StrengthHeroStarRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Strength hero star failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def wear(self, user_id, request):
        """装备将星"""
        timer = Timer(user_id)

        req = herostar_pb2.WearHeroStarReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_wear, req, timer)
        defer.addCallback(self._wear_succeed, req, timer)
        defer.addErrback(self._wear_failed, req, timer)
        return defer

    def _calc_wear(self, data, req, timer):
        herostar = herostar_business.get_herostar_by_id(data, req.hero_star)
        if herostar is None:
            raise Exception("No Such HeroStar")
        if HeroStarInfo.get_herostar_level(herostar.star_id) <= 0:
            raise Exception("Can't wear herostar which level is 0")
        hero = hero_business.get_hero_by_id(data, req.hero.basic_id)
        if hero is None:
            raise Exception("No Such Hero")

        if req.hero_star in hero.get_herostars_set():
            raise Exception("HeroStar Already weared.")

        index = [item_id for item_id in req.hero.hero_star].index(req.hero_star)

        if not herostar_business.is_hero_star_ok(data, hero, index):
            raise Exception("Hero Star too low")

        if hero.get_herostars()[index] != 0:
            raise Exception("Weared a herostar in this pos")

        herostar_business.wear_herostar(data, hero, req.hero_star, index, timer)
        if not herostar_business.validate_hero_herostar(data, hero, req.hero):
            raise Exception("Bad herostar")
        

        return DataBase().commit(data)

    def _wear_succeed(self, data, req, timer):
        res = herostar_pb2.WearHeroStarRes()
        res.status = 0

        response = res.SerializeToString()
        log = log_formater.output(data, "Wear hero star succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response

    def _wear_failed(self, err, req, timer):
        logger.fatal("Wear hero star failed[reason=%s]" % err)

        res = herostar_pb2.WearHeroStarRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Wear hero star failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def unload(self, user_id, request):
        """卸下将星"""
        timer = Timer(user_id)

        req = herostar_pb2.UnloadHeroStarReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_unload, req, timer)
        defer.addCallback(self._unload_succeed, req, timer)
        defer.addErrback(self._unload_failed, req, timer)
        return defer

    def _calc_unload(self, data, req, timer):
        herostar = herostar_business.get_herostar_by_id(data, req.hero_star)
        if herostar is None:
            raise Exception("No Such HeroStar")
        hero = hero_business.get_hero_by_id(data, req.hero.basic_id)
        if hero is None:
            raise Exception("No Such Hero")
        if req.hero_star not in hero.get_herostars_set():
            raise Exception("No Such herostar in this hero")
        
        herostar_business.unload_herostar(data, hero, req.hero_star, timer)
        if not herostar_business.validate_hero_herostar(data, hero, req.hero):
            raise Exception("Bad herostar")

        return DataBase().commit(data)

    def _unload_succeed(self, data, req, timer):
        res = herostar_pb2.UnloadHeroStarRes()
        res.status = 0

        response = res.SerializeToString()
        log = log_formater.output(data, "Unload hero star succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response

    def _unload_failed(self, err, req, timer):
        logger.fatal("Unload hero star failed[reason=%s]" % err)

        res = herostar_pb2.UnloadHeroStarRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Unload hero star failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
