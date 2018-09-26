#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场
"""

from firefly.server.globalobject import GlobalObject
from utils.timer import Timer
from proto import transfer_arena_pb2
from proto import battle_pb2
from proto import internal_pb2
from datalib.global_data import DataBase
from utils import logger
from utils.ret import Ret
from datalib.data_loader import data_loader
from app import pack
from app.user_matcher import UserMatcherWithBattle
from app.business import account as account_business
from app.business import transfer as transfer_business
from app.data.transfer_record import TransferRecordInfo

class TransferProcessor(object):

    def query(self, user_id, request):
        """查询换位演武场"""
        timer = Timer(user_id)

        req = transfer_arena_pb2.QueryTransferArenaReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        transfer = data.transfer.get(True)
        transfer_records = data.transfer_record_list.get_all(True)

        res = transfer_arena_pb2.QueryTransferArenaRes()
        res.status = 0
        res.arena_info.remain_times = transfer.get_remain_times()
        res.arena_info.cd_end_time = transfer.get_cd_end_time(timer.now)
        for transfer_record in transfer_records:
            pack.pack_transfer_record(transfer_record, res.arena_info.records.add())

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query transfer arena succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _query_failed(self, err, req, timer):
        logger.fatal("Query transfer arena failed[reason=%s]" % err)
        res = transfer_arena_pb2.QueryTransferArenaRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query transfer arena failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def buy(self, user_id, request):
        """购买挑战次数"""
        timer = Timer(user_id)

        req = transfer_arena_pb2.BuyChallengeTimesReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_buy, req, timer)
        defer.addErrback(self._buy_failed, req, timer)
        return defer

    def _calc_buy(self, data, req, timer):
        res = transfer_arena_pb2.BuyChallengeTimesRes()
        res.status = 0

        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        ret = Ret()
        if not transfer_business.buy_attack_times(data, timer.now, ret):
            if ret.get() == "NO_ENOUGH_GOLD":
                res.ret = transfer_arena_pb2.BuyChallengeTimesRes.NO_ENOUGH_GOLD
                return self._buy_succeed(data, req, res, timer)
            elif ret.get() == "UPPER_LIMIT":
                res.ret = transfer_arena_pb2.BuyChallengeTimesRes.UPPER_LIMIT
                return self._buy_succeed(data, req, res, timer)

        transfer = data.transfer.get()
        transfer_records = data.transfer_record_list.get_all(True)

        res.ret = transfer_arena_pb2.BuyChallengeTimesRes.OK
        res.arena_info.remain_times = transfer.get_remain_times()
        res.arena_info.cd_end_time = transfer.get_cd_end_time(timer.now)
        for transfer_record in transfer_records:
            pack.pack_transfer_record(transfer_record, res.arena_info.records.add())

        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)
        
        defer = DataBase().commit(data)
        defer.addCallback(self._buy_succeed, req, res, timer)
        return defer

    def _buy_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        if res.ret == transfer_arena_pb2.BuyChallengeTimesRes.OK:
            logger.notice("Buy transfer attack times succeed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        else:
            logger.notice("Buy transfer attack times failed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        return response

    def _buy_failed(self, err, req, timer):
        logger.fatal("Buy transfer attack times failed[reason=%s]" % err)
        res = transfer_arena_pb2.BuyChallengeTimesRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Buy transfer attack times failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def reset(self, user_id, request):
        """重置冷却时间"""
        timer = Timer(user_id)

        req = transfer_arena_pb2.ResetCDReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reset, req, timer)
        defer.addErrback(self._reset_failed, req, timer)
        return defer

    def _calc_reset(self, data, req, timer):
        res = transfer_arena_pb2.ResetCDRes()
        res.status = 0

        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        ret = Ret()
        if not transfer_business.reset_cd(data, timer.now, ret):
            if ret.get() == 'NO_ENOUGH_GOLD':
                res.ret = transfer_arena_pb2.ResetCDRes.NO_ENOUGH_GOLD
                return self._reset_succeed(data, req, res, timer)

        transfer = data.transfer.get()
        transfer_records = data.transfer_record_list.get_all(True)

        res.ret = transfer_arena_pb2.BuyChallengeTimesRes.OK
        res.arena_info.remain_times = transfer.get_remain_times()
        res.arena_info.cd_end_time = transfer.get_cd_end_time(timer.now)
        for transfer_record in transfer_records:
            pack.pack_transfer_record(transfer_record, res.arena_info.records.add())

        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._reset_succeed, req, res, timer)
        return defer

    def _reset_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        if res.ret == transfer_arena_pb2.BuyChallengeTimesRes.OK:
            logger.notice("Reset transfer cd succeed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        else:
            logger.notice("Reset transfer cd failed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        return response

    def _reset_failed(self, err, req, timer):
        logger.fatal("Reset transfer cd failed[reason=%s]" % err)
        res = transfer_arena_pb2.ResetCDRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reset transfer cd failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def start_battle(self, user_id, request):
        """开始战斗"""
        timer = Timer(user_id)

        req = transfer_arena_pb2.StartTransferArenaBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_battle, req, timer)
        defer.addErrback(self._start_battle_failed, req, timer)
        return defer

    def _calc_start_battle(self, data, req, timer):
        res = transfer_arena_pb2.StartTransferArenaBattleRes()
        res.status = 0

        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        ret = Ret()
        if not transfer_business.start_battle(data, req.target_id, timer.now, ret):
            if ret.get() == "NO_CHALLENGE_TIMES":
                res.ret = transfer_arena_pb2.StartTransferArenaBattleRes.NO_CHALLENGE_TIMES
            elif ret.get() == "COOLING":
                res.ret = transfer_arena_pb2.StartTransferArenaBattleRes.COOLING
            elif ret.get() == "TARGET_ERROR":
                res.ret = transfer_arena_pb2.StartTransferArenaBattleRes.TARGET_ERROR
            return self._start_battle_succeed(data, req, res, timer)

        res.ret = transfer_arena_pb2.StartTransferArenaBattleRes.OK
        defer = DataBase().commit(data)
        defer.addCallback(self._start_battle_succeed, req, res, timer)
        return defer

    def _start_battle_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        if res.ret == transfer_arena_pb2.StartTransferArenaBattleRes.OK:
            logger.notice("Start transfer battle succeed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        else:
            logger.notice("Start transfer battle failed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        return response

    def _start_battle_failed(self, err, req, timer):
        logger.fatal("Start transfer battle failed[reason=%s]" % err)
        res = transfer_arena_pb2.StartTransferArenaBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start transfer battle failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def finish_battle(self, user_id, request):
        """结束战斗"""
        timer = Timer()

        req = transfer_arena_pb2.FinishTransferArenaBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_battle, req, timer)
        defer.addErrback(self._finish_battle_failed, req, timer)
        return defer

    def _calc_finish_battle(self, data, req, timer):
        res = transfer_arena_pb2.FinishTransferArenaBattleRes()
        res.status = 0

        #记录次数
        trainer = data.trainer.get()
        trainer.add_daily_battle_transfer(1)

        transfer = data.transfer.get()
        if req.target_id not in transfer.get_match_ids():
            res.ret = transfer_arena_pb2.FinishTransferArenaBattleRes.TARGET_ERROR
            return self._finish_battle_succeed(data, req, res, timer)

        transfer.finish_battle(timer.now)
        win = True if req.battle.result == battle_pb2.BattleOutputInfo.WIN else False

        #请求common模块进行换位
        common_req = internal_pb2.InternalExchangeTransferReq()
        common_req.user_id = data.id
        common_req.target_user_id = req.target_id
        common_req.exchange = win
        common_request = common_req.SerializeToString()

        defer = GlobalObject().remote["common"].callRemote("exchange_transfer", 1, common_request)
        defer.addCallback(self._calc_finish_battle_result, data, req, timer)
        return defer

    def _calc_finish_battle_result(self, common_response, data, req, timer):
        common_res = internal_pb2.InternalExchangeTransferRes()
        common_res.ParseFromString(common_response)

        if common_res.status != 0:
            raise Exception("Exchange transfer rank failed")

        transfer = data.transfer.get()
        matcher = UserMatcherWithBattle()
        matcher.add_condition(req.target_id, transfer.target_is_robot(req.target_id))
        
        defer = matcher.match()
        defer.addCallback(self._calc_finish_battle_match, data, req,
                common_res.self_rank, common_res.rival_rank, timer)
        return defer

    def _calc_finish_battle_match(self, results, data, req, self_rank, rival_rank, timer):
        win = True if req.battle.result == battle_pb2.BattleOutputInfo.WIN else False

        #添加对战记录
        transfer_business.add_battle_record(
            data,
            req.target_id,
            results[req.target_id]['name'],
            results[req.target_id]['level'],
            results[req.target_id]['icon_id'],
            TransferRecordInfo.ATTACK_WIN if win else TransferRecordInfo.ATTACK_LOSE,
            self_rank,
            rival_rank
        )

        user = data.user.get(True)
        transfer = data.transfer.get()
        #通知对手
        if not transfer.target_is_robot(req.target_id):
            forward_req = internal_pb2.InternalTransferNoticeReq()
            forward_req.user_id = req.target_id
            forward_req.rival_user_id = user.id
            forward_req.rival_user_name = user.get_readable_name()
            forward_req.rival_level = user.level
            forward_req.rival_icon = user.icon_id
            forward_req.win = not win
            forward_req.self_rank = rival_rank
            forward_req.rival_rank = self_rank

            forward_request = forward_req.SerializeToString()
            defer = GlobalObject().root.callChild(
                'portal', "forward_transfer_notice", req.target_id, forward_request)
            defer.addCallback(self._calc_finish_battle_notice, data, req, timer)
            return defer

        else:
            res = transfer_arena_pb2.FinishTransferArenaBattleRes()
            res.status = 0
            res.ret = transfer_arena_pb2.FinishTransferArenaBattleRes.OK

            defer = DataBase().commit(data)
            defer.addCallback(self._finish_battle_succeed, req, res, timer)
            return defer

    def _calc_finish_battle_notice(self, forward_response, data, req, timer):
        forward_res = internal_pb2.InternalTransferNoticeRes()
        if forward_res.status != 0:
            logger.warning("Notice transfer battle failed[user_id=%d][target_user_id=%d]" % (
                data.id, req.target_id))

        res = transfer_arena_pb2.FinishTransferArenaBattleRes()
        res.status = 0
        res.ret = transfer_arena_pb2.FinishTransferArenaBattleRes.OK

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_battle_succeed, req, res, timer)
        return defer

    def _finish_battle_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        if res.ret == transfer_arena_pb2.FinishTransferArenaBattleRes.OK:
            logger.notice("Finish transfer battle succeed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        else:
            logger.notice("Finish transfer battle failed[req=%s][res=%s][consume=%d]" %
                    (req, res, timer.count_ms()))
        return response
    
    def _finish_battle_failed(self, err, req, timer):
        logger.fatal("Finish transfer battle failed[reason=%s]" % err)
        res = transfer_arena_pb2.FinishTransferArenaBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish transfer battle failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def receive(self, user_id, request):
        """接收战斗通知"""
        timer = Timer(user_id)

        req = internal_pb2.InternalTransferNoticeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive, req, timer)
        defer.addErrback(self._receive_failed, req, timer)
        return defer

    def _calc_receive(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        #添加对战记录
        transfer_business.add_battle_record(
            data,
            req.rival_user_id,
            req.rival_user_name,
            req.rival_level,
            req.rival_icon,
            TransferRecordInfo.DEFEND_WIN if req.win else TransferRecordInfo.DEFEND_LOSE,
            req.self_rank,
            req.rival_rank
        )

        #向用户推送
        transfer = data.transfer.get(True)
        transfer_records = data.transfer_record_list.get_all(True)

        push_res = transfer_arena_pb2.QueryTransferArenaRes()
        push_res.status = 0
        push_res.arena_info.remain_times = transfer.get_remain_times()
        push_res.arena_info.cd_end_time = transfer.get_cd_end_time(timer.now)
        for transfer_record in transfer_records:
            pack.pack_transfer_record(transfer_record, push_res.arena_info.records.add())

        push_response = push_res.SerializeToString()
        GlobalObject().root.callChild("portal", "push_transfer_record", data.id, push_response)

        res = internal_pb2.InternalTransferNoticeRes()
        res.status = 0

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_succeed, req, res, timer)
        return defer

    def _receive_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Receive transfer notice succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _receive_failed(self, err, req, timer):
        logger.fatal("Receive transfer notice failed[reason=%s]" % err)
        res = internal_pb2.InternalTransferNoticeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive transfer notice failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def award(self, user_id, request):
        """发放奖励(内部接口)"""
        timer = Timer(user_id)

        req = transfer_arena_pb2.TransferArenaRewardReq()
        req.ParseFromString(request)

        (gold, items_id, items_num) = transfer_business.rank_reward(req.ranking)

        if gold == None:
            logger.notice("No reward[user_id=%d]" % req.user_id)
            res = transfer_arena_pb2.TransferArenaRewardRes()
            res.status = 0
            response = res.SerializeToString()
            return self._award_succeed(response, req, timer)

        forward_req = internal_pb2.ReceiveMailReq()
        forward_req.user_id = req.user_id
        forward_req.mail.basic_id = 101
        forward_req.mail.subject = data_loader.ServerDescKeyInfo_dict[
                "award_transfer_subject"].value.encode("utf-8")
        forward_req.mail.content = data_loader.ServerDescKeyInfo_dict[
                "award_transfer_content"].value.encode("utf-8")
        forward_req.mail.sender = data_loader.ServerDescKeyInfo_dict[
                "award_transfer_sender"].value.encode("utf-8")

        for i, item_id in enumerate(items_id):
            info = forward_req.mail.reward_items.add()
            info.basic_id = item_id
            info.num = items_num[i]

        forward_req.mail.reward_resource.gold = gold

        forward_request = forward_req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_mail", req.user_id, forward_request)
        defer.addCallback(self._award_succeed, req, timer)
        defer.addErrback(self._award_failed, req, timer)
        return defer

    def _award_succeed(self, response, req, timer):
        res = transfer_arena_pb2.TransferArenaRewardRes()
        res.ParseFromString(response)
        logger.notice("Award transfer succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _award_failed(self, err, req, timer):
        logger.fatal("Award transfer failed[reason=%s]" % err)
        res = internal_pb2.TransferArenaRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Award transfer failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response
