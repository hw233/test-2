#coding:utf8
"""
Created on 2015-02-04
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 守卫队（防守阵容）相关处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import cityDefence_pb2
from app import pack
from app import log_formater
from datalib.data_loader import data_loader
from datalib.global_data import DataBase
from app.data.guard import GuardInfo
from app.data.city import CityInfo
from app.data.building import BuildingInfo
from app.data.hero import HeroInfo
# from app.business import guard as guard_business


class GuardProcessor(object):

    def update_team(self, user_id, request):
        """更新防守阵容
        """
        timer = Timer(user_id)

        req = cityDefence_pb2.UpdateDefenseReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_team, req, timer)
        defer.addCallback(self._update_team_succeed, req, timer)
        defer.addErrback(self._update_team_failed, req, timer)
        return defer


    def _calc_update_team(self, data, req, timer):
        user = data.user.get()

        defense_building_id = BuildingInfo.generate_id(
                data.id, req.defence.city_basic_id,
                req.defence.location_index, req.defence.building_basic_id)
        defense_building = data.building_list.get(defense_building_id, True)
        defense = data.defense_list.get(defense_building_id)

        if not user.allow_pvp:
            #TODO 临时的规则：如果城防开启的话，那么可以使用防守阵容
            city_id = CityInfo.generate_id(data.id, req.defence.city_basic_id)
            city = data.city_list.get(city_id, True)
            mansion = data.building_list.get(city.mansion_id, True)

            key = "%d_%d" % (2, 1)
            need_user_level = data_loader.BuildingLevelBasicInfo_dict[key].limitMonarchLevel
            need_mansion_level = data_loader.BuildingLevelBasicInfo_dict[key].limitMansionLevel

            if user.level >= need_user_level and mansion.level >= need_mansion_level:
                user.allow_pvp = True
            else:
                raise Exception("PVP not allowed")

        guard = data.guard_list.get(defense.guard_id)
        if guard is None:
            index = len(data.guard_list) + 1
            guard = GuardInfo.create(data.id, index)
            defense.update_guard(guard.id)
            data.guard_list.add(guard)

        guard_heroes = []
        for basic_id in req.defence.hero_basic_ids:
            hero_id = HeroInfo.generate_id(data.id, basic_id)
            hero = data.hero_list.get(hero_id, True)
            guard_heroes.append(hero)

        grade = data.grade.get(True)

        if not guard.update(guard_heroes, grade.score):
            raise Exception("Update guard failed")

        all_guards = data.guard_list.get_all(True)
        if not guard_business.validation(all_guards):
            raise Exception("Validation guard failed")

        return DataBase().commit(data)


    def _update_team_succeed(self, data, req, timer):
        res = cityDefence_pb2.UpdateDefenceRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Update guard team succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_team_failed(self, err, req, timer):
        logger.fatal("[Exception=%s]" % err)
        res = cityDefence_pb2.UpdateDefenceRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update guard team Failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

