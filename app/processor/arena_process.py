#coding:utf8
"""
Created on 2016-03-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 处理竞技场请求
"""

import base64
from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import arena_pb2
from proto import internal_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.arena_record import ArenaRecordInfo
from app.arena_matcher import ArenaMatcher
from app.business import arena as arena_business
from app.business import account as account_business


class ArenaProcessor(object):
    """处理竞技场相关逻辑
    """

    def query_arena(self, user_id, request):
        """查询竞技场
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_arena, req, timer)
        defer.addErrback(self._query_arena_failed, req, timer)
        return defer


    def _calc_query_arena(self, data, req, timer):
        user = data.user.get()
        if not user.allow_pvp_arena:
            raise Exception("Arena is not unlock[user_level=%d]" % user.level)

        new_mails = []
        arena_matcher = ArenaMatcher()
        arena = data.arena.get()
        if timer.now < arena.next_time:
            #raise Exception("Arena can not query now")
            logger.warning("Arena can not query now")

        #若演武场轮次过时，需要清算
        if arena.is_arena_round_overdue(timer.now):
            arena_business.calc_arena_round_result(data, arena, new_mails, timer.now)
            logger.debug("calc arena round result")

        #更新演武场next_time
        arena.update_next_time(timer.now)

        if arena.is_arena_active(timer.now):
            if arena.rivals_user_id == '':
                #匹配对手
                defer = arena_matcher.match(data, arena)
            else:
                defer = arena_matcher.query_ranking(data, arena)
            #更新段位
            defer.addCallback(self._update_title_level,
                    data, arena, arena_matcher, new_mails, timer)
            defer.addCallback(self._pack_query_arena_response,
                data, arena, arena_matcher, new_mails, req, timer)
            return defer

        else:
            if arena.need_query_rank():
                defer = arena_matcher.query_ranking(data, arena)
                defer.addCallback(self._pack_query_arena_response,
                    data, arena, arena_matcher, new_mails, req, timer)
            else:
                defer = Deferred()
                defer.addCallback(self._pack_query_arena_response,
                    data, arena, arena_matcher, new_mails, req, timer)
                defer.callback(True)
            return defer


    def _pack_query_arena_response(self, proxy, data, arena, arena_matcher, mails, req, timer):
        """构造返回
        args:
            mails : list(MailInfo)
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_arena_info(data.user.get(True), arena, res.arena_info, timer.now, arena_matcher.rank)
        if arena.is_arena_active(timer.now):
            #胜场奖励
            if arena.is_able_to_get_win_num_reward():
                pack.pack_arena_reward_info(arena, res.arena_info.win_num_reward)
            #对手信息
            rivals_id = arena.generate_arena_rivals_id()
            for rival_id in rivals_id:
                rival = data.rival_list.get(rival_id, True)
                pack.pack_arena_player(rival, res.arena_info.rivals.add())
            #系统选定的对战对手
            choose_rival_id = arena.get_choose_rival_id()
            choose_rival = data.rival_list.get(choose_rival_id, True)
            res.arena_info.choosed_user_id = choose_rival.rival_id
            #对战记录
            record_list = data.arena_record_list.get_all(True)
            for record in record_list:
                pack.pack_arena_record(record, res.arena_info.records.add())

        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_arena_succeed, req, res, timer)
        return defer


    def _query_arena_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Query arena succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_arena_failed(self, err, req, timer):
        logger.fatal("Query arena failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query arena failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refresh_arena(self, user_id, request):
        """刷新竞技场对手
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh_arena, req, timer)
        defer.addErrback(self._refresh_arena_failed, req, timer)
        return defer


    def _calc_refresh_arena(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")
        
        user = data.user.get()
        if not user.allow_pvp_arena:
            raise Exception("Arena is not unlock[user_level=%d]" % user.level)

        arena = data.arena.get()
        if not arena_business.refresh_arena(data, arena, timer.now):
            raise Exception("Refresh arena failed")

        #匹配对手
        arena_matcher = ArenaMatcher()
        defer = arena_matcher.match(data, arena)
        defer.addCallback(self._pack_refresh_arena_response,
                data, arena, arena_matcher, req, timer)
        return defer


    def _pack_refresh_arena_response(self, proxy, data, arena, arena_matcher, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_arena_info(data.user.get(True), arena, res.arena_info, timer.now, arena_matcher.rank)
        #对手信息
        rivals_id = arena.generate_arena_rivals_id()
        for rival_id in rivals_id:
            rival = data.rival_list.get(rival_id, True)
            pack.pack_arena_player(rival, res.arena_info.rivals.add())
        #系统选定的对战对手
        choose_rival_id = arena.get_choose_rival_id()
        choose_rival = data.rival_list.get(choose_rival_id, True)
        res.arena_info.choosed_user_id = choose_rival.rival_id

        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._refresh_arena_succeed, req, res, timer)
        return defer


    def _refresh_arena_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Refresh arena succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _refresh_arena_failed(self, err, req, timer):
        logger.fatal("Refresh arena failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh arena failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_arena(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_arena, req, timer)
        defer.addErrback(self._update_arena_failed, req, timer)
        return defer


    def _calc_update_arena(self, data, req, timer):
        user = data.user.get()
        if not user.allow_pvp_arena:
            raise Exception("Arena is not unlock[user_level=%d]" % user.level)

        arena = data.arena.get()
        mails = []
        last_battle_win = arena.last_battle_win
        old_title_level = arena.title_level
        arena_matcher = ArenaMatcher()
        #if last_battle_win:
        #    #更新段位
        #    defer = Deferred()
        #    defer.addCallback(self._update_title_level,
        #            data, arena, arena_matcher, mails, timer)
        #    defer.addCallback(self._check)
        #    defer.callback(True)
        #else:
        #    if arena.need_query_rank():
        #        defer = arena_matcher.query_ranking(data, arena)
        #        defer.addCallback(self._update_title_level,
        #                data, arena, arena_matcher, mails, timer)
        #        defer.addCallback(self._check)
        #    else:
        #        defer = Deferred()
        #        defer.addCallback(self._update_title_level,
        #                data, arena, arena_matcher, mails, timer)
        #        defer.addCallback(self._check)
        #        defer.callback(True)
        if arena.need_query_rank():
            defer = arena_matcher.query_ranking(data, arena)
            defer.addCallback(self._update_title_level,
                    data, arena, arena_matcher, mails, timer)
            defer.addCallback(self._check)
        else:
            defer = Deferred()
            defer.addCallback(self._update_title_level,
                    data, arena, arena_matcher, mails, timer)
            defer.addCallback(self._check)
            defer.callback(True)

        if arena_business.is_need_broadcast_title(old_title_level, arena):
            #演武场获得高段位发广播
            try:
                self._add_arena_broadcast_title(user, arena)
            except:
                logger.warning("Send arena broadcast failed")
            
        defer.addCallback(self._pack_update_arena_response,
                data, arena, arena_matcher, mails, last_battle_win, req, timer)
        return defer


    def _update_title_level(self, proxy, data, arena, arena_matcher, mails, timer):
        if not arena_business.update_arena_title_level(data, arena, arena_matcher.rank, mails, timer.now):
            raise Exception("Update arena title level fail")
        arena.reset_last_battle_win()

        return True


    def _add_arena_broadcast_title(self, user, arena):
        """广播玩家演武场战况
        Args:

        """
        (mode, priority, life_time, content) = arena_business.create_broadcast_content_title(user, arena)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add arena broadcast title[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_arena_broadcast_title_result)
        return defer


    def _check_add_arena_broadcast_title_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast title result failed")

        return True


    def _pack_update_arena_response(self, proxy, data, arena, arena_matcher, mails,
            last_battle_win, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_arena_info(data.user.get(True), arena, res.arena_info, timer.now, arena_matcher.rank)
        if arena.is_arena_active(timer.now):
            #胜场奖励
            if arena.is_able_to_get_win_num_reward():
                pack.pack_arena_reward_info(arena, res.arena_info.win_num_reward)

        #if last_battle_win:
        #    #对手信息
        #    rivals_id = arena.generate_arena_rivals_id()
        #    for rival_id in rivals_id:
        #        rival = data.rival_list.get(rival_id, True)
        #        if rival is not None:
        #            pack.pack_arena_player(rival, res.arena_info.rivals.add())

        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._update_arena_succeed, req, res, timer)
        return defer


    def _update_arena_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Update arena succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _update_arena_failed(self, err, req, timer):
        logger.fatal("Update arena failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update arena failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def get_arena_win_num_reward(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_get_arena_win_num_reward, req, timer)
        defer.addErrback(self._get_arena_win_num_reward_failed, req, timer)
        return defer


    def _calc_get_arena_win_num_reward(self, data, req, timer):
        user = data.user.get()
        if not user.allow_pvp_arena:
            raise Exception("Arena is not unlock[user_level=%d]" % user.level)

        arena = data.arena.get()
        if not arena_business.get_arena_win_num_reward(data, arena, timer.now):
            raise Exception("Arena get win num reward failed")

        #验证客户端正确性
        for item_info in req.items:
            compare.check_item(data, item_info)

        arena_matcher = ArenaMatcher()
        if arena.need_query_rank():
            defer = arena_matcher.query_ranking(data, arena)
        else:
            defer = Deferred()
            defer.callback(True)

        defer.addCallback(self._pack_get_arena_win_num_reward_response,
                data, arena, arena_matcher, req, timer)
        return defer


    def _pack_get_arena_win_num_reward_response(self, proxy, data, arena,
            arena_matcher, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_arena_info(data.user.get(True), arena, res.arena_info,
                timer.now, arena_matcher.rank)
        #胜场奖励
        if arena.is_able_to_get_win_num_reward():
            pack.pack_arena_reward_info(arena, res.arena_info.win_num_reward)

        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)


        defer = DataBase().commit(data)
        defer.addCallback(self._get_arena_win_num_reward_succeed, req, res, timer)
        return defer


    def _get_arena_win_num_reward_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Get arena win num reward succeed",
                req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _get_arena_win_num_reward_failed(self, err, req, timer):
        logger.fatal("Get arena win num reward failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Get arena win num reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_arena_ranking(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_arena_ranking, req, timer)
        defer.addErrback(self._query_arena_ranking_failed, req, timer)
        return defer


    def _calc_query_arena_ranking(self, data, req, timer):
        user = data.user.get()
        if not user.allow_pvp_arena:
            raise Exception("Arena is not unlock[user_level=%d]" % user.level)

        arena = data.arena.get()
        arena_matcher = ArenaMatcher()
        RANKING_COUNT = 20
        users = []
        defer = arena_matcher.query_arena_users_by_ranking(data, arena, RANKING_COUNT, users)
        defer.addCallback(self._pack_query_arena_ranking_response,
                data, arena, arena_matcher, users, req, timer)
        return defer


    def _pack_query_arena_ranking_response(self, proxy, data, arena, arena_matcher, users, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_arena_info(data.user.get(True), arena, res.arena_info, timer.now,
                arena_matcher.rank)
        res.arena_info.own.ranking_index = arena_matcher.rank
        if arena.is_arena_active(timer.now):
            #胜场奖励
            if arena.is_able_to_get_win_num_reward():
                pack.pack_arena_reward_info(arena, res.arena_info.win_num_reward)

        #榜单信息
        for user in users:
            message = res.arena_info.player_rankings.add()
            message.user_id = user[0]
            message.name = user[1]
            message.level = user[2]
            message.icon_id = user[3]
            message.title_level = user[4]
            message.score = user[5]
            message.ranking_index = user[6]

        response = res.SerializeToString()
        log = log_formater.output(data, "Query arena ranking succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_arena_ranking_failed(self, err, req, timer):
        logger.fatal("Query arena ranking failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query arena ranking failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_notice(self, user_id, request):
        """接收到演武场对战结果的通知
        """
        timer = Timer(user_id)

        req = internal_pb2.ArenaResultNoticeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_notice, req, timer)
        defer.addErrback(self._receive_notice_failed, req, timer)
        return defer


    def _calc_receive_notice(self, data, req, timer):
        """接收到战斗结果通知
        1 变更演武场积分
        2 新增演武场对战记录
        """
        arena = data.arena.get()
        (win_score, lose_score) = arena_business.calc_battle_score(arena, req.rival_score)
        score_delta = 0
        if req.status == ArenaRecordInfo.STATUS_DEFEND_LOSE:
            score_delta = lose_score
        else:
            score_delta = win_score

        arena.add_score(score_delta)
        record = arena_business.add_arena_record(data,
                req.rival_user_id, base64.b64encode(req.rival_name), req.rival_level,
                req.rival_icon_id, req.status, score_delta)

        mails = []
        arena_matcher = ArenaMatcher()
        if arena.need_query_rank():
            defer = arena_matcher.query_ranking(data, arena)
            defer.addCallback(self._update_title_level,
                    data, arena, arena_matcher, mails, timer)
            defer.addCallback(self._check)
        else:
            defer = Deferred()
            defer.addCallback(self._update_title_level,
                    data, arena, arena_matcher, mails, timer)
            defer.addCallback(self._check)
            defer.callback(True)

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_notice_succeed, req, arena, arena_matcher, record, timer)
        return defer


    def _receive_notice_succeed(self, data, req, arena, arena_matcher, record, timer):
        res = internal_pb2.ArenaResultNoticeRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive arena notice succeed", req, res, timer.count_ms())
        logger.notice(log)

        self._push_record(data, data.user.get(True), arena, arena_matcher.rank, record, timer)
        DataBase().clear_data(data)
        return response


    def _push_record(self, data, user, arena, ranking, record, timer):
        """向客户端推送对战记录，如果用户不在线，则推送失败
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_arena_info(user, arena, res.arena_info, timer.now, ranking)
        #对战记录
        pack.pack_arena_record(record, res.arena_info.records.add())

        response = res.SerializeToString()
        return GlobalObject().root.callChild("portal", "push_arena_record", data.id, response)


    def _receive_notice_failed(self, err, req, timer):
        logger.fatal("Receive arena notice failed[reason=%s]" % err)
        res = internal_pb2.ArenaResultNoticeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive arena notice failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _check(self, status):
        assert status is True
        return self


    def update_arena_offline(self, user_id, request):
        """
        向指定用户发送离线更新演武场信息的请求
        内部接口
        """
        timer = Timer(user_id)

        req = internal_pb2.UpdateArenaOfflineReq()
        req.ParseFromString(request)

        defer = self._forward_update_arena_offline(req.trigger_user_id, timer)
        defer.addCallback(self._update_arena_offline_succeed, req, timer)
        defer.addErrback(self._update_arena_offline_failed, req, timer)
        return defer


    def _forward_update_arena_offline(self, user_id, timer):
        """向用户转发离线更新演武场信息的请求
        """
        req = internal_pb2.ReceiveArenaOfflineReq()
        req.user_id = user_id
        request = req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_update_arena_offline", user_id, request)
        defer.addCallback(self._check_forward_update_arena_offline)
        return defer


    def _check_forward_update_arena_offline(self, response):
        res = internal_pb2.ReceiveArenaOfflineRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward update arena offline failed")


    def _update_arena_offline_succeed(self, data, req, timer):
        res = internal_pb2.UpdateArenaOfflineRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Update arena offline succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _update_arena_offline_failed(self, err, req, timer):
        logger.fatal("Update arena offline failed[reason=%s]" % err)
        res = internal_pb2.UpdateArenaOfflineRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update arena offline failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_update_arena_offline(self, user_id, request):
        """帐号接收离线更新演武场信息的请求
        """
        timer = Timer(user_id)

        req = internal_pb2.ReceiveArenaOfflineReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_update_arena_offline, req, timer)
        defer.addCallback(self._receive_update_arena_offline_succeed, req, timer)
        defer.addErrback(self._receive_update_arena_offline_failed, req, timer)
        return defer


    def _calc_receive_update_arena_offline(self, data, req, timer):
        """更新演武场数据
        """
        user = data.user.get()
        if not user.allow_pvp_arena:
            return True

        arena = data.arena.get()
        new_mails = []
        #若演武场轮次过时，需要清算
        if arena.is_arena_round_overdue(timer.now):
            arena_business.calc_arena_round_result(data, arena, new_mails, timer.now)

        #离线更新演武场数据
        if not arena_business.update_arena_offline(data, user, arena):
            raise Exception("Update arena offline failed")

        #TODO 先更新积分，再更改段位，排队信息就不对了   to fix

        arena_matcher = ArenaMatcher()
        if arena.need_query_rank():
            defer = arena_matcher.query_ranking(data, arena)
            defer.addCallback(self._update_title_level,
                    data, arena, arena_matcher, new_mails, timer)
            defer.addCallback(self._check)
        else:
            defer = Deferred()
            defer.addCallback(self._update_title_level,
                    data, arena, arena_matcher, new_mails, timer)
            defer.addCallback(self._check)
            defer.callback(True)

        defer = DataBase().commit(data)
        return defer


    def _receive_update_arena_offline_succeed(self, data, req, timer):
        res = internal_pb2.ReceiveArenaOfflineRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Receive update arena offline succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        DataBase().clear_data(data)
        return response


    def _receive_update_arena_offline_failed(self, err, req, timer):
        logger.fatal("Receive update arena offline failed[reason=%s]" % err)
        res = internal_pb2.ReceiveArenaOfflineRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive update arena offline failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_arena_coin(self, user_id, request):
        """增加演武场代币（内部接口）
        """
        timer = Timer(user_id)
        req = internal_pb2.AddArenaCoinReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_arena_coin, req, timer)
        defer.addCallback(self._add_arena_coin_succeed, req, timer)
        defer.addErrback(self._add_arena_coin_failed, req, timer)
        return defer


    def _calc_add_arena_coin(self, data, req, timer):
        """
        """
        #更新资源
        arena = data.arena.get()
        arena.gain_coin(req.add_num)

        return DataBase().commit(data)


    def _add_arena_coin_succeed(self, data, req, timer):
        res = internal_pb2.AddArenaCoinRes()
        res.status = 0
        response = res.SerializeToString()

        log = log_formater.output(data, "Add arena coin succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_arena_coin_failed(self, err, req, timer):
        logger.fatal("Add arena coin failed[reason=%s]" % err)

        res = internal_pb2.AddArenaCoinRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add arena coin failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


