#coding:utf8
"""
Created on 2016-02-20
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 处理委托请求
"""

from utils import logger
from utils.timer import Timer
from utils.ret import Ret
from proto import appoint_pb2
from app import pack
from app import compare
from app import log_formater
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app.rival_matcher import RivalMatcher
from app.data.item import ItemInfo
from app.data.team import TeamInfo
from app.data.hero import HeroInfo
from app.data.node import NodeInfo
from app.business import map as map_business
from app.business import appoint as appoint_business
from app.business import account as account_business


class AppointProcessor(object):
    def start_appoint(self, user_id, request):
        """开始委任战斗"""
        timer = Timer(user_id)

        req = appoint_pb2.StartAppointReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_appoint, req, timer)
        defer.addErrback(self._calc_start_appoint_failed, req, timer)
        return defer


    def _calc_start_appoint(self, data, req, timer):
        item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
        item = data.item_list.get(item_id)
        if item is None:
            raise Exception("Item not exist")

        #扣减1个虎符
        if not item.use_appoint_item(1):
            raise Exception("Use appoint item failed")

        compare.check_item(data, req.item)

        #参战team/英雄
        teams = []
        heroes = []
        for team in req.battle.attack_teams:
            team_id = TeamInfo.generate_id(data.id, team.index)
            team = data.team_list.get(team_id)
            if team is None:
                continue

            teams.append(team)

            for hero_id in team.get_heroes():
                if hero_id != 0:
                    hero = data.hero_list.get(hero_id)
                    heroes.append(hero)

        if len(teams) == 0:
            raise Exception("Appoint teams is NULL")

        #敌人信息
        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        rival_id = node_id
        node = data.node_list.get(node_id)
        rival = data.rival_list.get(rival_id)

        if node.rival_type in (NodeInfo.ENEMY_TYPE_PVE_BANDIT, NodeInfo.ENEMY_TYPE_PVE_REBEL):
            """山贼"""
            rival.reward_user_exp = int(float(data_loader.OtherBasicInfo_dict['bandit_battle_cost_energy'].value))
        else:
            """侦察敌军"""
            rival.reward_user_exp = int(float(data_loader.OtherBasicInfo_dict['keynode_battle_cost_energy'].value))

        user = data.user.get()
        if not appoint_business.start_appoint(data, user, node, rival,
                teams, heroes, timer.now, force = True):
            raise Exception("Start appoint failed")

        #构造返回
        res = self._pack_start_appoint_response(data, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_appoint_succeed, node, rival, req, res, timer)
        return defer


    def _pack_start_appoint_response(self, data, now):
        """构造返回
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        resource = data.resource.get(True)
        conscript_list = data.conscript_list.get_all(True)

        res = appoint_pb2.StartAppointRes()
        res.status = 0

        pack.pack_resource_info(resource, res.resource)
        for conscript in conscript_list:
            pack.pack_conscript_info(conscript, res.conscripts.add(), now)

        return res


    def _start_appoint_succeed(self, data, node, rival, req, res, timer):
        response = res.SerializeToString()

        log = log_formater.output_battle(data, node.id, rival, "Start appoint succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _calc_start_appoint_failed(self, err, req, timer):
        logger.fatal("Start appoint failed[reason=%s]" % err)

        res = appoint_pb2.StartAppointRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start appoint failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_appoint(self, user_id, request):
        """结束委任战斗
        """
        timer = Timer(user_id)

        req = appoint_pb2.FinishAppointReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_appoint, req, timer)
        defer.addErrback(self._calc_finish_appoint_failed, req, timer)
        return defer


    def _calc_finish_appoint(self, data, req, timer):
        node_id = NodeInfo.generate_id(data.id, req.node.basic_id)
        node = data.node_list.get(node_id)
        battle = data.battle_list.get(node_id)

        #存活兵力信息
        own_soldier_info = battle.get_own_soldier_info()
        enemy_soldier_info = battle.get_enemy_soldier_info()

        change_nodes = []
        items = []
        heroes = []
        mails = []

        ret = Ret()
        if not appoint_business.finish_appoint(data, node,
                battle, change_nodes, items, heroes, mails, timer.now, ret):
            if ret.get() == "FINISHED":
                res = appoint_pb2.FinishAppointRes()
                res.status = 0
                res.ret = appoint_pb2.FinishAppointRes.FINISHED
                pack.pack_node_info(data, node, res.node, timer.now)
                return self._finish_appoint_succeed(data, req, res, timer)
            else:
                raise Exception("Finish appoint failed")

        #为新刷出的敌方节点匹配敌人
        invalid_rival = [data.id]
        for node in data.node_list.get_all(True):
            if node.is_rival_pvp() and node.is_enemy_complete():
                rival_id = node.id
                rival = data.rival_list.get(rival_id, True)
                invalid_rival.append(rival.rival_id)

        user = data.user.get(True)
        matcher = RivalMatcher(user.level, invalid_rival)
        for node in change_nodes:
            if node.is_lack_enemy_detail():
                matcher.add_condition(data, node)

        defer = matcher.match(user.country)
        defer.addCallback(self._pack_finish_appoint_response,
                data, change_nodes, items, heroes, mails, req, timer)
        return defer


    def _pack_finish_appoint_response(self, matcher, data,
            node_list, items, heroes, mails, req, timer):
        """构造返回
        args:
            items : list((num, basic_id)元组)
            heroes: list((basic_id, level, exp, battle_node_basic_id )元组)
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        resource = data.resource.get(True)
        user = data.user.get(True)

        conscript_list = data.conscript_list.get_all(True)

        res = appoint_pb2.FinishAppointRes()
        res.status = 0
        res.ret = appoint_pb2.FinishAppointRes.OK

        pack.pack_resource_info(resource, res.resource)
        pack.pack_monarch_info(user, res.monarch)
        for conscript in conscript_list:
            pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)
        for node in node_list:
            pack.pack_node_info(data, node, res.nodes.add(), timer.now)

        for item in items:
            pack.pack_item_info(item, res.items.add())

        for hero in heroes:
            hero_message = res.heros.add()
            hero_message.basic_id = hero[0]
            hero_message.level = hero[1]
            hero_message.exp = hero[2]
            hero_message.battle_node_id = hero[3]

        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        if 'is_battle_cost_energy' in account_business.get_flags():
            energy = data.energy.get()
            energy.update_current_energy(timer.now)
            pack.pack_energy_info(energy, res.energy, timer.now)

        map_business.check_map_data(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_appoint_succeed, req, res, timer)
        return defer


    def _finish_appoint_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Finish appoint succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _calc_finish_appoint_failed(self, err, req, timer):
        logger.fatal("Finish appoint failed[reason=%s]" % err)

        res = appoint_pb2.FinishAppointRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish appoint failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



