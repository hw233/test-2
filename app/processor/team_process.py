#coding:utf8
"""
Created on 2015-09-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 军队相关请求
"""

from utils import logger
from utils.timer import Timer
from firefly.server.globalobject import GlobalObject
from proto import team_pb2
from datalib.global_data import DataBase
from app import compare
from app import log_formater
from app.data.team import TeamInfo
from app.business import team as team_business
from app.core import technology as technology_module

class TeamProcessor(object):

    def update(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = team_pb2.ModifyTeamsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update, req)
        defer.addCallback(self._update_succeed, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer


    def _calc_update(self, data, req):
        """更新军队信息
        """
        #先清除有变化部队的所有英雄的buff
        heroes_id = []
        for team_info in req.teams:
            team_id = TeamInfo.generate_id(data.id, team_info.index)
            team = data.team_list.get(team_id)
            if team is not None:
                heroes_id.extend(team.get_heroes())
        for hero_id in heroes_id:
            if hero_id !=0:
                hero = data.hero_list.get(hero_id)
                if hero.buffs_id != '':
                    #清除英雄所有羁绊，需要重新计算战力
                    #影响英雄所带兵种战力的科技
                    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
                            data.technology_list.get_all(True), hero.soldier_basic_id)
                    hero.clear_buffs(battle_technology_basic_id)
                    logger.debug("clear buffs and calc battlescore[hero_id=%d]" % hero_id)

        for team_info in req.teams:
            heroes_basic_id = []
            for hero_info in team_info.heroes:
                heroes_basic_id.append(hero_info.basic_id)

            #更换英雄
            if not team_business.update_team(data, team_info.index, heroes_basic_id):
                raise Exception("Update team failed")

        if not team_business.validation(data):
            raise Exception("Teams invalid")

        return DataBase().commit(data)


    def _update_succeed(self, data, req, timer):
        res = team_pb2.ModifyTeamsRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Update team succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_failed(self, err, req, timer):
        logger.fatal("Update team failed[reason=%s]" % err)

        res = team_pb2.ModifyTeamsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update team failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refresh_all_teams(self, user_id, request):
        """向指定用户发送更新所有team的请求
        """
        timer = Timer(user_id)

        req = team_pb2.RefreshAllTeamsReq()
        req.ParseFromString(request)

        defer = self._forward_refresh_all_teams(req.trigger_user_id, timer)
        defer.addCallback(self._refresh_all_teams_succeed, req, timer)
        defer.addErrback(self._refresh_all_teams_failed, req, timer)
        return defer


    def _forward_refresh_all_teams(self, user_id, timer):
        """转发
        """
        req = team_pb2.ReceiveRefreshAllTeamsReq()
        req.user_id = user_id
        request = req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_refresh_all_teams", user_id, request)
        defer.addCallback(self._check_refresh_all_teams)
        return defer


    def _check_refresh_all_teams(self, response):
        res = team_pb2.ReceiveRefreshAllTeamsRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward refresh all teams failed")


    def _refresh_all_teams_succeed(self, data, req, timer):
        res = team_pb2.RefreshAllTeamsRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Refresh all teams succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _refresh_all_teams_failed(self, err, req, timer):
        logger.fatal("Refresh all teams failed[reason=%s]" % err)

        res = team_pb2.RefreshAllTeamsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh all teams failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_refresh_all_teams(self, user_id, request):
        """接受更新所有team的请求
        """
        timer = Timer(user_id)

        req = team_pb2.ReceiveRefreshAllTeamsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_refresh_all_teams, req)
        defer.addCallback(self._receive_refresh_all_teams_succeed, req, timer)
        defer.addErrback(self._receive_refresh_all_teams_failed, req, timer)
        return defer


    def _calc_receive_refresh_all_teams(self, data, req):
        """
        """
        team_list = data.team_list.get_all()
        for team in team_list:
            if not team_business.refresh_team(data, team):
                logger.warning("Refresh team error")
                return False

        if not team_business.validation(data):
            raise Exception("Teams invalid")

        return DataBase().commit(data)


    def _receive_refresh_all_teams_succeed(self, data, req, timer):
        res = team_pb2.ReceiveRefreshAllTeamsRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive refresh all teams succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _receive_refresh_all_teams_failed(self, err, req, timer):
        logger.fatal("Receive refresh all teams failed[reason=%s]" % err)

        res = team_pb2.ReceiveRefreshAllTeamsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive refresh all teams failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response





