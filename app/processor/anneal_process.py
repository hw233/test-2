#coding:utf8
"""
Created on 2016-05-18
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 试炼场相关逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from utils.ret import Ret
from proto import anneal_pb2
from proto import internal_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.item import ItemInfo
from app.data.team import TeamInfo
from app.data.anneal import AnnealInfo
from app.business import anneal as anneal_business
from app import log_formater
from app.business import account as account_business


class AnnealProcessor(object):

    def query_anneal(self, user_id, request):
        """查询试炼场
        """
        timer = Timer(user_id)

        req = anneal_pb2.QueryAnnealInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_anneal, req, timer)
        defer.addCallback(self._query_anneal_succeed, req, timer)
        defer.addErrback(self._query_anneal_failed, req, timer)
        return defer


    def _calc_query_anneal(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        anneal = data.anneal.get()
        anneal.update_current_attack_num(timer.now)
        if 'is_open_new_anneal' in account_business.get_flags():
            anneal.try_forward_floor()
        if timer.now < anneal.next_refresh_time:
            #刷新攻击次数
            anneal_business.refresh_attack_num(anneal, timer.now)

        return DataBase().commit(data)


    def _query_anneal_succeed(self, data, req, timer):
        res = anneal_pb2.QueryAnnealInfoRes()
        res.status = 0

        pack.pack_anneal_info(data, data.anneal.get(True), res.anneal, timer.now)
        response = res.SerializeToString()

        log = log_formater.output(data, "Query anneal succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_anneal_failed(self, err, req, timer):
        logger.fatal("Query anneal failed[reason=%s]" % err)

        res = anneal_pb2.QueryAnnealInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query anneal failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def get_pass_reward(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = anneal_pb2.GetPassRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_get_pass_reward, req, timer)
        defer.addCallback(self._get_pass_reward_succeed, req, timer)
        defer.addErrback(self._get_pass_reward_failed, req, timer)
        return defer


    def _calc_get_pass_reward(self, data, req, timer):
        anneal = data.anneal.get()
        if not anneal_business.get_pass_reward(data, anneal, req.mode_type):
            raise Exception("Anneal get pass reward failed")

        #验证客户端正确性
        for item_info in req.items:
            compare.check_item(data, item_info)
        
        return DataBase().commit(data)


    def _get_pass_reward_succeed(self, data, req, timer):
        res = anneal_pb2.GetPassRewardRes()
        res.status = 0

        pack.pack_anneal_info(data, data.anneal.get(True), res.anneal, timer.now)
        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Get pass reward succeed",
                req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _get_pass_reward_failed(self, err, req, timer):
        logger.fatal("Get pass reward failed[reason=%s]" % err)

        res = anneal_pb2.GetPassRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Get pass reward reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def buy_attack_num(self, user_id, request):
        timer = Timer(user_id)
        req = anneal_pb2.BuyAttackNumReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_buy_attack_num, req, timer)
        defer.addCallback(self._buy_attack_num_succeed, req, timer)
        defer.addErrback(self._buy_attack_num_failed, req, timer)
        return defer


    def _calc_buy_attack_num(self, data, req, timer):
        """
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        anneal = data.anneal.get()
        anneal.update_current_attack_num(timer.now)

        item = None
        if req.HasField("item"):
            item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
            item = data.item_list.get(item_id)

        need_gold, original_gold = anneal_business.buy_attack_num(data, anneal, item, timer.now)
        if need_gold < 0:
            raise Exception("Buy attack num failed")

        #记录次数
        #trainer = data.trainer.get()
        #trainer.add_daily_buy_attack_num(1)

        if req.HasField("item"):
            compare.check_item(data, req.item)

        if need_gold> 0:
            log = log_formater.output_gold(data, -need_gold, log_formater.BUY_ATTACK_NUM,
                    "Buy attack num by gold", before_gold = original_gold,  attack_num = anneal.get_attack_num_of_buy())
            logger.notice(log)

        return DataBase().commit(data)


    def _buy_attack_num_succeed(self, data, req, timer):
        res = anneal_pb2.BuyAttackNumRes()
        res.status = 0
        pack.pack_anneal_info(data, data.anneal.get(True), res.anneal, timer.now)
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Buy attack num succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _buy_attack_num_failed(self, err, req, timer):
        logger.fatal("Buy attack num failed[reason=%s]" % err)

        res = anneal_pb2.BuyAttackNumRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Buy attack num failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start_sweep(self, user_id, request):
        """开始扫荡
        """
        timer = Timer(user_id)

        req = anneal_pb2.StartSweepReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_sweep, req, timer)
        defer.addErrback(self._start_sweep_failed, req, timer)
        return defer


    def _calc_start_sweep(self, data, req, timer):
        """
        """
        #参战team/英雄
        teams = []
        heroes = []
        for team in req.teams:
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
            raise Exception("Sweep teams is NULL")

        if 'is_open_new_anneal' in account_business.get_flags():
            mode = req.anneal_type
        else:
            mode = AnnealInfo.NORMAL_MODE

        total_time = req.total_time if req.HasField('total_time') else None
        attack_num = req.attack_num if req.HasField('attack_num') else None

        anneal = data.anneal.get()
        if not anneal_business.start_sweep(data, anneal, req.direction,
                req.floor, total_time, attack_num, teams, heroes, timer.now, mode):
            raise Exception("Start anneal sweep failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._start_sweep_succeed, anneal, req, timer)
        return defer


    def _start_sweep_succeed(self, data, anneal, req, timer):

        #构造返回
        res = anneal_pb2.StartSweepRes()
        res.status = 0
        pack.pack_anneal_info(data, anneal, res.anneal, timer.now)
        response = res.SerializeToString()

        log = log_formater.output(data, "Start sweep succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _start_sweep_failed(self, err, req, timer):
        logger.fatal("Start sweep failed[reason=%s]" % err)

        res = anneal_pb2.StartSweepRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start sweep failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_sweep(self, user_id, request):
        """结束扫荡
        """
        timer = Timer(user_id)

        req = anneal_pb2.FinishSweepReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_sweep, req, timer)
        defer.addErrback(self._finish_sweep_failed, req, timer)
        return defer


    def _calc_finish_sweep(self, data, req, timer):
        """
        """ 
        anneal = data.anneal.get()
        sweep_rewards = []
        items = []
        heroes = []
        if not anneal_business.finish_sweep(data, anneal, sweep_rewards,
                items, heroes, timer.now):
            raise Exception("Finish anneal sweep failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_sweep_succeed, anneal, sweep_rewards, 
                items, heroes, req, timer)
        return defer


    def _finish_sweep_succeed(self, data, anneal, sweep_rewards, items, heroes, req, timer):

        #构造返回
        res = anneal_pb2.FinishSweepRes()
        res.status = 0
        pack.pack_anneal_info(data, anneal, res.anneal, timer.now)

        pack.pack_resource_info(data.resource.get(True), res.resource)

        for (money, food, reward) in sweep_rewards:
            reward_message = res.reward.add()
            reward_message.resource.money = money
            reward_message.resource.food = food
            for (basic_id, num) in reward:
                item_message = reward_message.items.add()
                item_message.basic_id = basic_id
                item_message.num = num

        for item in items:
            pack.pack_item_info(item, res.items.add())

        for hero in heroes:
            hero_message = res.heros.add()
            hero_message.basic_id = hero[0]
            hero_message.level = hero[1]
            hero_message.exp = hero[2]

        response = res.SerializeToString()

        log = log_formater.output(data, "Finish sweep succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _finish_sweep_failed(self, err, req, timer):
        logger.fatal("Finish sweep failed[reason=%s]" % err)

        res = anneal_pb2.FinishSweepRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish sweep failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_anneal_record(self, user_id, request):
        """查询通关记录
        """
        timer = Timer(user_id)

        req = anneal_pb2.QueryAnnealRecordReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_anneal_record, request, req, timer)
        defer.addErrback(self._query_anneal_record_failed, req, timer)
        return defer


    def _calc_query_anneal_record(self, data, request, req, timer):
        """
        """
        #查询通关信息
        defer = GlobalObject().remote["common"].callRemote("query_anneal_record", 1, request)
        defer.addCallback(self._check_query_anneal_record_result, data, req, timer)
        return defer


    def _check_query_anneal_record_result(self, response, data, req, timer):
        res = anneal_pb2.QueryAnnealRecordRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Query anneal record result failed")

        logger.notice("Query anneal record succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _query_anneal_record_failed(self, err, req, timer):
        logger.fatal("Query anneal record failed[reason=%s]" % err)

        res = anneal_pb2.QueryAnnealRecordRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query anneal record failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def modify_anneal_progress(self, user_id, request):
        """修改试炼场进度
        """
        timer = Timer(user_id)

        req = internal_pb2.ModifyAnnealProgressReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_modify_anneal_progress, req, timer)
        defer.addCallback(self._modify_anneal_progress_succeed, req, timer)
        defer.addErrback(self._modify_anneal_progress_failed, req, timer)
        return defer


    def _calc_modify_anneal_progress(self, data, req, timer):
        anneal = data.anneal.get()
        anneal.modify_progress(req.mode.type, req.mode.floor, req.mode.level, False)

        return DataBase().commit(data)


    def _modify_anneal_progress_succeed(self, data, req, timer):
        res = internal_pb2.ModifyAnnealProgressRes()
        res.status = 0
        response = res.SerializeToString()

        log = log_formater.output(data, "Modify anneal progress succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _modify_anneal_progress_failed(self, err, req, timer):
        logger.fatal("Modify anneal progress failed[reason=%s]" % err)

        res = internal_pb2.ModifyAnnealProgressRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Modify anneal progress failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def modify_anneal_sweep_time(self, user_id, request):
        """修改试炼场进度
        """
        timer = Timer(user_id)

        req = internal_pb2.ModifyAnnealSweepTimeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_modify_anneal_sweep_time, req, timer)
        defer.addCallback(self._modify_anneal_sweep_time_succeed, req, timer)
        defer.addErrback(self._modify_anneal_sweep_time_failed, req, timer)
        return defer


    def _calc_modify_anneal_sweep_time(self, data, req, timer):
        anneal = data.anneal.get()
        anneal.modify_sweep_start_time(req.back_time)

        return DataBase().commit(data)


    def _modify_anneal_sweep_time_succeed(self, data, req, timer):
        res = internal_pb2.ModifyAnnealSweepTimeRes()
        res.status = 0
        response = res.SerializeToString()

        log = log_formater.output(data, "Modify anneal sweep time succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _modify_anneal_sweep_time_failed(self, err, req, timer):
        logger.fatal("Modify anneal sweep time failed[reason=%s]" % err)

        res = internal_pb2.ModifyAnnealSweepTimeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Modify anneal sweep time failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def reset_hard_attack_num(self, user_id, request):
        """重置困难模式攻击次数"""
        timer = Timer(user_id)

        req = anneal_pb2.ResetHardAttackNumReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reset_hard_attack_num, req, timer)
        defer.addErrback(self._reset_hard_attack_num_failed, req, timer)
        return defer
        
    def _calc_reset_hard_attack_num(self, data, req, timer):
        res = anneal_pb2.ResetHardAttackNumRes()
        res.status = 0

        ret = Ret()
        if not anneal_business.reset_hard_attack_num(data, req.floor, timer.now, ret):
            if ret.get() == 'GOLD_NOT_ENOUGH':
                res.ret = anneal_pb2.ResetHardAttackNumRes.GOLD_NOT_ENOUGH
            elif ret.get() == 'VIP_NOT_ENOUGH':
                res.ret = anneal_pb2.ResetHardAttackNumRes.VIP_NOT_ENOUGH

            return self._reset_hard_attack_num_succeed(data, req, res, timer)
      
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        res.ret = anneal_pb2.ResetHardAttackNumRes.OK
        pack.pack_resource_info(resource, res.resource)
        pack.pack_anneal_info(data, data.anneal.get(True), res.anneal, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._reset_hard_attack_num_succeed, req, res, timer)
        return defer

    def _reset_hard_attack_num_succeed(self, data, req, res, timer):
        if res.ret != anneal_pb2.ResetHardAttackNumRes.OK:
            logger.notice("Reset anneal hard attack num failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Reset anneal hard attack num succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _reset_hard_attack_num_failed(self, err, req, timer):
        logger.fatal("Reset anneal hard attack num failed[reason=%s]" % err)
        res = anneal_pb2.ResetHardAttackNumRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reset anneal hard attack num failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
