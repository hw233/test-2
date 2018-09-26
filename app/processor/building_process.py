#coding:utf8
"""
Created on 2015-02-04
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 建造/升级 相关处理逻辑
"""

from utils import logger
from utils.timer import Timer
from utils.ret import Ret
from proto import building_pb2
from app import pack
from app import log_formater
from datalib.global_data import DataBase
from app.data.hero import HeroInfo
from app.data.city import CityInfo
from app.data.building import BuildingInfo
from app.business import building as building_business
from app.business import city as city_business
from app.business import technology as technology_business
from app.business import account as account_business
from app import compare


class BuildingProcessor(object):

    def start_create(self, user_id, request):
        """开始新建建筑
        """
        timer = Timer(user_id)

        req = building_pb2.UpgradeBuildingReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_create, req, timer)
        defer.addCallback(self._start_create_succeed, req, timer)
        defer.addErrback(self._start_create_failed, req, timer)
        return defer


    def _calc_start_create(self, data, req, timer):
        """
        新建建筑
        1 指派英雄参与建造
        2 开始建造一个建筑，计算消耗时间和消耗资源
        Args:
            data[UserData]: 原来的数据，包括
            req[protobuf]: 请求
        """
        user = data.user.get(True)
        resource = data.resource.get()

        build_heroes = [] #参与升级的英雄
        for basic_id in req.building.hero_basic_ids:
            if basic_id == 0:
                build_heroes.append(None)
            else:
                hero_id = HeroInfo.generate_id(data.id, basic_id)
                hero = data.hero_list.get(hero_id)
                build_heroes.append(hero)

        #更新资源
        resource.update_current_resource(timer.now)

        #如果参与建造的英雄驻守在其他的建筑物中，将其从其他建筑物中移除
        #不结算经验，但是会对建筑物造成影响
        for hero in build_heroes:
            if hero is not None and hero.is_working_in_building():
                building = data.building_list.get(hero.place_id)
                if not building_business.remove_garrison(
                        building, hero, resource, timer.now):
                    raise Exception("Reassign build hero error")

        city_id = CityInfo.generate_id(data.id, req.building.city_basic_id)
        city = data.city_list.get(city_id)
        mansion = data.building_list.get(city.mansion_id, True)

        #新建建筑，此时建筑物为0级
        new_building = city_business.create_building(city, user, mansion.level,
                req.building.location_index, req.building.basic_id)
        if new_building is None:
            raise Exception("Create buliding failed[basic_id=%d]" % req.building.basic_id)
        data.building_list.add(new_building)

        #所有生效的内政科技
        interior_technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]

        #升级建筑，从0级升到1级
        if not building_business.start_upgrade(new_building, resource,
                build_heroes, interior_technologys, user, mansion, timer.now):
            raise Exception("Start upgrade building failed[basic_id=%d][level=%d]" %
                    (new_building.basic_id, new_building.level))

        #check
        if req.building.level != 0:
            raise Exception("Building level must equal 0")

        return DataBase().commit(data)


    def _start_create_succeed(self, data, req, timer):
        res = building_pb2.UpgradeBuildingRes()
        res.status = 0

        pack.pack_resource_info(data.resource.get(True), res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Start create building succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_create_failed(self, err, req, timer):
        logger.fatal("Start create building failed[reason=%s]" % err)

        res = building_pb2.UpgradeBuildingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start create building failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start_upgrade(self, user_id, request):
        """开始升级建筑
        """
        timer = Timer(user_id)
        req = building_pb2.UpgradeBuildingReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_upgrade, req, timer)
        defer.addCallback(self._start_upgrade_succeed, req, timer)
        defer.addErrback(self._start_upgrade_failed, req, timer)
        return defer


    def _calc_start_upgrade(self, data, req, timer):
        """开始升级
        """
        user = data.user.get(True)
        resource = data.resource.get()

        upgrade_building_id = BuildingInfo.generate_id(
                data.id, req.building.city_basic_id,
                req.building.location_index, req.building.basic_id)
        upgrade_building = data.building_list.get(upgrade_building_id)

        garrison_heroes = []#原有的驻守的英雄
        garrison_hero_ids = upgrade_building.get_working_hero()
        for hero_id in garrison_hero_ids:
            if hero_id == 0:
                garrison_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                garrison_heroes.append(hero)

        build_heroes = []#参与升级的英雄
        for basic_id in req.building.hero_basic_ids:
            if basic_id == 0:
                build_heroes.append(None)
            else:
                hero_id = HeroInfo.generate_id(data.id, basic_id)
                hero = data.hero_list.get(hero_id)
                build_heroes.append(hero)

        #更新资源
        resource.update_current_resource(timer.now)

        #升级前处理
        if not building_business.pre_upgrade(
                upgrade_building, timer.now, resource, garrison_heroes):
            raise Exception("Pre pocess for upgrade error")

        #如果参与建造的英雄驻守在其他的建筑物中，将其从其他建筑物中移除
        #不结算经验，但是会对建筑物造成影响
        for hero in build_heroes:
            if hero is not None and hero.is_working_in_building():
                building = data.building_list.get(hero.place_id)
                if not building_business.remove_garrison(
                        building, hero, resource, timer.now):
                    raise Exception("Reassign build hero error")

        #所有生效的内政科技
        interior_technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]

        city = data.city_list.get(upgrade_building.city_id)
        mansion = data.building_list.get(city.mansion_id, True)

        #开始升级 指派 build_heroes 参与升级
        if not building_business.start_upgrade(upgrade_building, resource,
                build_heroes, interior_technologys, user, mansion, timer.now):
            raise Exception("Start upgrade building failed[basic_id=%d][level=%d]" %
                    (upgrade_building.basic_id, upgrade_building.level))

        #check
        return DataBase().commit(data)
        return defer


    def _start_upgrade_succeed(self, data, req, timer):
        res = building_pb2.UpgradeBuildingRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Start upgrade building succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_upgrade_failed(self, err, req, timer):
        logger.fatal("Start upgrade building failed[reason=%s]" % err)

        res = building_pb2.UpgradeBuildingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start upgrade building failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def cancel_upgrade(self, user_id, request):
        """
        取消建筑升级, 包括取消建造
        """
        timer = Timer(user_id)

        req = building_pb2.UpgradeBuildingReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_cancel_upgrade, req, timer)
        defer.addCallback(self._cancel_upgrade_succeed, req, timer)
        defer.addErrback(self._cancel_upgrade_failed, req, timer)
        return defer


    def _calc_cancel_upgrade(self, data, req, timer):
        """
        """
        user = data.user.get(True)
        resource = data.resource.get()

        upgrade_building_id = BuildingInfo.generate_id(
                data.id, req.building.city_basic_id,
                req.building.location_index, req.building.basic_id)
        upgrade_building = data.building_list.get(upgrade_building_id)

        build_heroes = []#参与升级的英雄
        build_hero_ids = upgrade_building.get_working_hero()
        for hero_id in build_hero_ids:
            if hero_id == 0:
                build_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                build_heroes.append(hero)

        #更新资源
        resource.update_current_resource(timer.now)

        #建筑结束升级状态 包括结算参与建造的英雄获得的经验 结算主公获得的经验
        if not building_business.cancel_upgrade(data,
                upgrade_building, resource, user, build_heroes, timer.now):
            raise Exception("Cancel upgrade building failed")

        #所有生效的内政科技
        interior_technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]

        #升级完成之后的处理
        if not building_business.post_cancel(upgrade_building, timer.now,
                build_heroes, interior_technologys, resource):
            raise Exception("Post process for upgrade failed")

        #判断建筑物是否需要删除掉
        need_destroy = building_business.is_need_destroy(upgrade_building)
        if need_destroy:
            city = data.city_list.get(upgrade_building.city_id)
            logger.debug("Need delete building[basic_id=%d]" % upgrade_building.basic_id)
            if not city.destroy_building(upgrade_building):
                raise Exception("Destroy building failed")
            data.building_list.delete(upgrade_building.id)

        return DataBase().commit(data)


    def _cancel_upgrade_succeed(self, data, req, timer):
        res = building_pb2.UpgradeBuildingRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Cancel upgrade building succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _cancel_upgrade_failed(self, err, req, timer):
        logger.fatal("Cancle upgrade building failed[reason=%s]" % err)
        res = building_pb2.UpgradeBuildingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Cancle upgrade building failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_upgrade(self, user_id, request, force = False):
        """建筑升级完成 [正常完成]
        """
        timer = Timer(user_id)

        req = building_pb2.UpgradeBuildingReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_upgrade, req, timer, force)
        #defer.addCallback(self._finish_upgrade_succeed, req, timer)
        defer.addErrback(self._finish_upgrade_failed, req, timer)
        return defer


    def _calc_finish_upgrade(self, data, req, timer, force):
        """建筑升级完成
        1 完成建筑升级，更新建筑信息，包括结算英雄参与建造升级获得的经验
        2 指派新的驻守英雄
        3 更新建筑升级完成的影响（农田、市场、兵营、城防）
        """
        res = building_pb2.UpgradeBuildingRes()
        res.status = 0

        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        user = data.user.get(True)
        resource = data.resource.get()

        upgrade_building_id = BuildingInfo.generate_id(
                data.id, req.building.city_basic_id,
                req.building.location_index, req.building.basic_id)
        upgrade_building = data.building_list.get(upgrade_building_id)

        build_heroes = []#参与升级的英雄
        build_hero_ids = upgrade_building.get_working_hero()
        for hero_id in build_hero_ids:
            if hero_id == 0:
                build_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                build_heroes.append(hero)

        #更新资源
        resource.update_current_resource(timer.now)

        #如果不处于升级状态
        """if upgrade_building.is_upgrade == False:
            return DataBase().commit(data)"""

        #建筑结束升级状态 包括结算参与建造的英雄获得的经验 结算主公获得的经验
        ret = Ret()
        if not building_business.finish_upgrade(data,
                upgrade_building, resource, user, build_heroes, timer.now, force, ret):
            if ret.get() == "NOT_UPGRADING":
                res.ret = building_pb2.UpgradeBuildingRes.NOT_UPGRADING
                pack.pack_building_info(upgrade_building, res.building, timer.now)
                return self._finish_upgrade_succeed(data, req, res, timer)
            elif ret.get() == "CANNT_FINISH":
                res.ret = building_pb2.UpgradeBuildingRes.CANNT_FINISH
                pack.pack_building_info(upgrade_building, res.building, timer.now)
                return self._finish_upgrade_succeed(data, req, res, timer)
            else:
                raise Exception("Finish upgrade building failed")

        defense = None
        conscript = None
        if upgrade_building.is_defense():
            defense = data.defense_list.get(upgrade_building.id)
        elif upgrade_building.is_barrack():
            conscript = data.conscript_list.get(upgrade_building.id)

        #所有生效的内政科技
        interior_technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]

        #升级完成之后的处理
        new_technology = []
        new_defense = []
        new_conscript = []
        if not building_business.post_upgrade(data,
                upgrade_building, timer.now,
                build_heroes, interior_technologys,
                resource, defense, conscript,
                new_technology, new_defense, new_conscript):
            raise Exception("Post process for upgrade failed")

        #可能解锁出已经完成研究的兵种科技，因此可能会解锁新的兵种
        for technology in new_technology:
            data.technology_list.add(technology)
            if technology.is_soldier_technology():
                soldier = technology_business.post_research_for_soldier_technology(
                        data, data.id, technology, timer.now, new = True)
                if soldier is None:
                    raise Exception("Post process for soldier technology failed")
                data.soldier_list.add(soldier)

        for defense in new_defense:
            data.defense_list.add(defense)

        for conscript in new_conscript:
            data.conscript_list.add(conscript)

        #检查请求
        compare.check_user(data, req.monarch, with_level = True)

        res.ret = building_pb2.UpgradeBuildingRes.OK
        pack.pack_resource_info(data.resource.get(True), res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_upgrade_succeed, req, res, timer)
        return defer


    def _finish_upgrade_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Finish upgrade building succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _finish_upgrade_failed(self, err, req, timer):
        logger.fatal("Finish upgrade failed[reason=%s]" % err)
        res = building_pb2.UpgradeBuildingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish upgrade failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_garrison_hero(self, user_id, request):
        """更换驻守英雄
        """
        timer = Timer(user_id)

        req = building_pb2.UpdateGarrisonHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_garrison_hero, req, timer)
        defer.addCallback(self._update_garrison_hero_succeed, req, timer)
        defer.addErrback(self._update_garrison_hero_failed, req, timer)
        return defer


    def _calc_update_garrison_hero(self, data, req, timer):
        """
        """
        resource = data.resource.get()

        update_building_id = BuildingInfo.generate_id(
                data.id, req.building.city_basic_id,
                req.building.location_index, req.building.basic_id)
        update_building = data.building_list.get(update_building_id)

        origin_heroes = []#原有的驻守武将
        heroes_id = update_building.get_working_hero()
        for hero_id in heroes_id:
            if hero_id == 0:
                origin_heroes.append(None)
            else:
                hero = data.hero_list.get(hero_id)
                origin_heroes.append(hero)

        garrison_heroes = []#新的驻守武将
        for hero_basic_id in req.building.hero_basic_ids:
            if hero_basic_id == 0:
                garrison_heroes.append(None)
            else:
                hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
                hero = data.hero_list.get(hero_id)
                garrison_heroes.append(hero)

        #更新资源
        resource.update_current_resource(timer.now)

        #如果新的驻守英雄在其他的建筑物中，将其从其他建筑物中移除
        for hero in garrison_heroes:
            if hero is not None and hero.is_working_in_building():
                building = data.building_list.get(hero.place_id)

                if not building_business.remove_garrison(
                        building, hero, resource, timer.now):
                    raise Exception("Reassign build hero error")

        #将原来驻守在建筑物中的英雄移除
        for hero in origin_heroes:
            if hero is None or not hero.is_working_in_building():
                continue
            if not building_business.remove_garrison(
                    update_building, hero, resource, timer.now):
                raise Exception("Reassign build hero error")

        #所有生效的内政科技
        interior_technologys = [tech for tech in data.technology_list.get_all(True)
                if tech.is_interior_technology() and not tech.is_upgrade]

        #将新的英雄派驻进建筑物
        if not building_business.set_garrison(
                update_building, garrison_heroes, resource,
                interior_technologys, timer.now):
            raise Exception("Set garrison hero error")

        defer = DataBase().commit(data)
        return defer


    def _update_garrison_hero_succeed(self, data, req, timer):
        res = building_pb2.UpdateGarrisonHeroRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Update garrison hero succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_garrison_hero_failed(self, err, req, timer):
        logger.fatal("Update garrison hero failed[reason=%s]" % err)
        res = building_pb2.UpdateGarrisonHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update garrison hero failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


