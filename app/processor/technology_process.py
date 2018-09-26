#coding:utf8
"""
Created on 2015-02-04
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 科技研究 相关处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils import utils
from utils.timer import Timer
from utils.ret import Ret
from proto import technology_pb2
from proto import broadcast_pb2
from datalib.data_loader import data_loader
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.technology import TechnologyInfo
from app.data.building import BuildingInfo
from app.data.hero import HeroInfo
from app.business import building as building_business
from app.business import technology as technology_business
from app.business import account as account_business


class TechnologyProcessor(object):

    def start_research(self, user_id, request):
        """开始研究科技
        """
        timer = Timer(user_id)

        req = technology_pb2.UpgradeTechReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_research, req, timer)
        defer.addCallback(self._start_research_succeed, req, timer)
        defer.addErrback(self._start_research_failed, req, timer)
        return defer


    def _calc_start_research(self, data, req, timer):
        """开始研究科技
        1 指派参与研究的英雄
        1 开始科技研究，计算时间消耗和资源消耗
        """
        user = data.user.get()
        resource = data.resource.get()

        research_building_id = BuildingInfo.generate_id(
                data.id, req.building.city_basic_id,
                req.building.location_index, req.building.basic_id)
        research_building = data.building_list.get(research_building_id)

        if research_building is None:
            raise Exception("Research building not exist");

        research_heroes = [] #参与升级的英雄
        for basic_id in req.building.hero_basic_ids:
            if basic_id == 0:
                research_heroes.append(None)
            else:
                hero_id = HeroInfo.generate_id(data.id, basic_id)
                hero = data.hero_list.get(hero_id)
                research_heroes.append(hero)

        #更新资源
        resource.update_current_resource(timer.now)

        #将参与研究的英雄从其他建筑物中移除，更新原有建筑的影响
        #不结算英雄经验 : 英雄经验由客户端周期性请求结算
        #WARNING : 在上一次请求到此时英雄驻守的经验不结算
        for hero in research_heroes:
            if hero is not None and hero.is_working_in_building():
                building = data.building_list.get(hero.place_id)
                if not building_business.remove_garrison(
                        building, hero, resource, timer.now):
                    raise Exception("Reassign build hero error")

        #前置依赖科技
        pre_technology_id = technology_business.get_pre_technology_id(
                data.id, req.tech.basic_id, req.tech.type)
        pre_technology = data.technology_list.get(pre_technology_id)

        #所有生效的内政科技
        interior_technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]

        #开始研究科技
        new_technology = technology_business.start_research(
                req.tech.basic_id, req.tech.type, user, research_building,
                research_heroes, resource,
                pre_technology, interior_technologys, timer.now)
        if not new_technology:
            raise Exception("Start reasearch technology failed[basic_id=%d]" %
                    req.tech.basic_id)
        data.technology_list.add(new_technology)

        #验证
        compare.check_technology(data, req.tech)

        return DataBase().commit(data)


    def _start_research_succeed(self, data, req, timer):
        res = technology_pb2.UpgradeTechRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Start research technology succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_research_failed(self, err, req, timer):
        logger.fatal("Start research technology failed[reason=%s]" % err)

        res = technology_pb2.UpgradeTechRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start research technology failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_research(self, user_id, request, force = False):
        """科技研究结束
        """
        timer = Timer(user_id)

        req = technology_pb2.UpgradeTechReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_research, req, timer, force)
        #defer.addCallback(self._finish_research_succeed, req, timer)
        defer.addErrback(self._finish_research_failed, req, timer)
        return defer


    def _calc_finish_research(self, data, req, timer, force):
        """
        """
        res = technology_pb2.UpgradeTechRes()
        res.status = 0

        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        user = data.user.get(True)
        resource = data.resource.get()

        technology_id = TechnologyInfo.generate_id(
                data.id, req.tech.basic_id, req.tech.type)
        technology = data.technology_list.get(technology_id)

        research_building = data.building_list.get(technology.building_id)
        if research_building is None:
            logger.fatal("research building is None[building_id=%d]" % technology.building_id)

        research_heroes = [] # 参与研究的英雄
        research_heroes_id = research_building.get_working_hero()
        for hero_id in research_heroes_id:
            if hero_id == 0:
                research_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                research_heroes.append(hero)

        resource.update_current_resource(timer.now)

        #结束研究
        ret = Ret()
        if not technology_business.finish_research(data, technology,
                user, research_building, research_heroes, resource, timer.now, force, ret):
            if ret.get() == "NOT_UPGRADING":
                res.ret = technology_pb2.UpgradeTechRes.NOT_UPGRADING
                pack.pack_technology_info(technology, res.tech, timer.now)
                return self._finish_research_succeed(data, req, res, timer)
            elif ret.get() == "CANNT_FINISH":
                res.ret = technology_pb2.UpgradeTechRes.CANNT_FINISH
                pack.pack_technology_info(technology, res.tech, timer.now)
                return self._finish_research_succeed(data, req, res, timer)
            else:
                raise Exception("Finish research technology failed")

        #前置依赖科技
        pre_technology_id = technology_business.get_pre_technology_id(
                data.id, technology.basic_id, technology.type)
        pre_technology = None
        if pre_technology_id != 0:
            pre_technology = data.technology_list.get(pre_technology_id)

        #升级完成的后续处理
        #兵种科技
        if technology.is_soldier_technology():
            #删除前置依赖科技
            if pre_technology_id != 0:
                data.technology_list.delete(pre_technology_id)

            #兵种科技研究完成后，会将原有兵种升级
            soldier_id = technology_business.get_related_soldier_id(
                    data.id, req.tech.basic_id)
            soldier = data.soldier_list.get(soldier_id)
            #所有配置相关兵种的英雄
            related_heroes = [hero.get() for hero in data.hero_list
                    if hero.get(True).soldier_basic_id == soldier.basic_id]

            soldier = technology_business.post_research_for_soldier_technology(
                    data, data.id, technology, timer.now, soldier, related_heroes)
            if not soldier:
                raise Exception("Post process for research soldier technology failed")

        #战斗科技
        elif technology.is_battle_technology():
            #删除前置依赖科技
            if pre_technology_id != 0:
                data.technology_list.delete(pre_technology_id)

            soldier_basic_ids = data_loader.BattleTechnologyBasicInfo_dict[
                    technology.basic_id].soldierBasicInfoId

            related_heroes = [] #所带兵种的战力受该科技影响的英雄
            for soldier_basic_id in soldier_basic_ids:
                for hero in data.hero_list:
                    if hero.get(True).soldier_basic_id == soldier_basic_id:
                        related_heroes.append(hero.get())

            if not technology_business.post_research_for_battle_technology(
                    data, technology, related_heroes):
                raise Exception("Post process for research battle technology failed")

        #内政科技
        elif technology.is_interior_technology():
            #遍历所有建筑，更新建筑产量或容量
            for building in data.building_list.get_all():
                building_heroes = []#建筑中驻守的英雄
                build_hero_ids = building.get_working_hero()
                for hero_id in build_hero_ids:
                    if hero_id == 0:
                        building_heroes.append(None)
                    else:
                        hero = data.hero_list.get(hero_id)
                        building_heroes.append(hero)

                if not building_business.update_building_with_interior_technology(
                        building, building_heroes, resource, data, technology, pre_technology):
                    raise Exception("Post process for research interior technology failed")

            #删除前置依赖科技
            if pre_technology_id != 0:
                data.technology_list.delete(pre_technology_id)



        #验证
        compare.check_technology(data, req.tech)

        #记录次数
        trainer = data.trainer.get()
        trainer.add_daily_tech_upgrade_num(1)

        #科技升级的广播
        try:
            self._add_technology_broadcast(user, technology)
        except:
            logger.warning("Send technology broadcast failed")

        res.ret = technology_pb2.UpgradeTechRes.OK
        pack.pack_resource_info(data.resource.get(True), res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_research_succeed, req, res, timer)
        return defer


    def _add_technology_broadcast(self, user, technology):
        """广播玩家科技升级
        Args:

        """
        (mode, priority, life_time, content) = technology.create_broadcast_content(user)
        if mode == 0:
            #不需要播广播
            return True

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add technology broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_technology_broadcast_result)
        return defer


    def _check_add_technology_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add technology broadcast result failed")

        return True


    def _finish_research_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Finish research technology succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _finish_research_failed(self, err, req, timer):
        logger.fatal("Finish research technology failed[reason=%s]" % err)

        res = technology_pb2.UpgradeTechRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish research technology failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def cancel_research(self, user_id, request):
        """取消科技升级"""
        timer = Timer(user_id)

        req = technology_pb2.UpgradeTechReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_cancel_research, req, timer)
        defer.addCallback(self._cancel_research_succeed, req, timer)
        defer.addErrback(self._cancel_research_failed, req, timer)
        return defer


    def _calc_cancel_research(self, data, req, timer):
        user = data.user.get(True)
        resource = data.resource.get()

        technology_id = TechnologyInfo.generate_id(
                data.id, req.tech.basic_id, req.tech.type)
        technology = data.technology_list.get(technology_id)

        research_building = data.building_list.get(technology.building_id)

        research_heroes = [] # 参与研究的英雄
        research_heroes_id = research_building.get_working_hero()
        for hero_id in research_heroes_id:
            if hero_id == 0:
                research_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                research_heroes.append(hero)

        #更新资源
        resource.update_current_resource(timer.now)

        #取消研究
        if not technology_business.cancel_research(data,
                technology, user, research_building, research_heroes, resource, timer.now):
            raise Exception("Cancel Research technology failed")

        data.technology_list.delete(technology.id)

        return DataBase().commit(data)


    def _cancel_research_succeed(self, data, req, timer):
        res = technology_pb2.UpgradeTechRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Cancel research technology succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _cancel_research_failed(self, err, req, timer):
        logger.fatal("Cancel research technology failed[reason=%s]" % err)

        res = technology_pb2.UpgradeTechRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Cancel research technology failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


