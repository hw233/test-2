#coding:utf8
"""
Created on 2016-12-31
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 处理乱斗场请求
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
from app.data.melee_record import MeleeRecordInfo
from app.melee_matcher import MeleeMatcher
from app.business import melee as melee_business
from app.business import account as account_business


class MeleeProcessor(object):
    """处理乱斗场场相关逻辑
    """

    def query_melee(self, user_id, request):
        """查询乱斗场场
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_melee, req, timer)
        defer.addErrback(self._query_melee_failed, req, timer)
        return defer


    def _calc_query_melee(self, data, req, timer):
        user = data.user.get()
        melee = data.melee.get()

        if not melee.is_able_to_unlock(user):
            raise Exception("Melee is not unlock[user_level=%d]" % user.level)

        arena = data.arena.get(True)
        melee.node_id = arena.node_id
        
        new_mails = []
        melee_matcher = MeleeMatcher()
        if timer.now < melee.next_time:
            logger.warning("Melee can not query now")

        #若乱斗场轮次过时，需要清算
        if melee.is_arena_round_overdue(timer.now):
            melee_business.calc_melee_round_result(data, melee, new_mails, timer.now)
            logger.debug("calc melee round result")

        #更新乱斗场场next_time
        melee.update_next_time(timer.now)

        if melee.is_arena_active(timer.now):
            if melee.rivals_user_id == '':
                #匹配对手
                defer = melee_matcher.match(data, melee)
            else:
                defer = melee_matcher.query_ranking(data, melee)
            #更新段位
            defer.addCallback(self._update_title_level,
                    data, melee, melee_matcher, new_mails, timer)
            defer.addCallback(self._pack_query_melee_response,
                data, melee, melee_matcher, new_mails, req, timer)
            return defer

        else:
            if melee.need_query_rank():
                defer = melee_matcher.query_ranking(data, melee)
                defer.addCallback(self._pack_query_melee_response,
                    data, melee, melee_matcher, new_mails, req, timer)
            else:
                defer = Deferred()
                defer.addCallback(self._pack_query_melee_response,
                    data, melee, melee_matcher, new_mails, req, timer)
                defer.callback(True)
            return defer


    def _pack_query_melee_response(self, proxy, data, melee, melee_matcher, mails, req, timer):
        """构造返回
        args:
            mails : list(MailInfo)
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_melee_info(data.user.get(True), melee, res.arena_info, timer.now, melee_matcher.rank)
        if melee.is_arena_active(timer.now):
            #胜场奖励
            if melee.is_able_to_get_win_num_reward():
                pack.pack_arena_reward_info(melee, res.arena_info.win_num_reward)
            #对手信息
            rivals_id = melee.generate_arena_rivals_id()
            for rival_id in rivals_id:
                rival = data.rival_list.get(rival_id, True)
                pack.pack_melee_player(rival, res.arena_info.rivals.add())
            #对战记录
            record_list = data.melee_record_list.get_all(True)
            for record in record_list:
                pack.pack_arena_record(record, res.arena_info.records.add())

        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_melee_succeed, req, res, timer)
        return defer


    def _query_melee_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Query melee succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_melee_failed(self, err, req, timer):
        logger.fatal("Query melee failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query melee failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refresh_melee(self, user_id, request):
        """刷新竞技场对手
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh_melee, req, timer)
        defer.addErrback(self._refresh_melee_failed, req, timer)
        return defer


    def _calc_refresh_melee(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")
        
        user = data.user.get()
        melee = data.melee.get()
        if not melee.is_able_to_unlock(user):
            raise Exception("Melee is not unlock[user_level=%d]" % user.level)

        arena = data.arena.get(True)
        melee.node_id = arena.node_id
        
        if not melee_business.refresh_melee(data, melee, timer.now):
            raise Exception("Refresh melee failed")

        #匹配对手
        melee_matcher = MeleeMatcher()
        defer = melee_matcher.match(data, melee)
        defer.addCallback(self._pack_refresh_melee_response,
                data, melee, melee_matcher, req, timer)
        return defer


    def _pack_refresh_melee_response(self, proxy, data, melee, melee_matcher, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_melee_info(data.user.get(True), melee, res.arena_info, timer.now, melee_matcher.rank)
        #对手信息
        rivals_id = melee.generate_arena_rivals_id()
        for rival_id in rivals_id:
            rival = data.rival_list.get(rival_id, True)
            pack.pack_melee_player(rival, res.arena_info.rivals.add())

        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._refresh_melee_succeed, req, res, timer)
        return defer


    def _refresh_melee_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Refresh melee succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _refresh_melee_failed(self, err, req, timer):
        logger.fatal("Refresh melee failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh melee failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_melee(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_melee, req, timer)
        defer.addErrback(self._update_melee_failed, req, timer)
        return defer


    def _calc_update_melee(self, data, req, timer):
        user = data.user.get()
        melee = data.melee.get()
        if not melee.is_able_to_unlock(user):
            raise Exception("melee is not unlock[user_level=%d]" % user.level)

        arena = data.arena.get(True)
        melee.node_id = arena.node_id
        
        mails = []
        last_battle_win = melee.last_battle_win
        old_title_level = melee.title_level
        melee_matcher = MeleeMatcher()
        #if last_battle_win:
        #    #更新段位
        #    defer = Deferred()
        #    defer.addCallback(self._update_title_level,
        #            data, melee, melee_matcher, mails, timer)
        #    defer.addCallback(self._check)
        #    defer.callback(True)
        #else:
        #    if melee.need_query_rank():
        #        defer = melee_matcher.query_ranking(data, melee)
        #        defer.addCallback(self._update_title_level,
        #                data, melee, melee_matcher, mails, timer)
        #        defer.addCallback(self._check)
        #    else:
        #        defer = Deferred()
        #        defer.addCallback(self._update_title_level,
        #                data, melee, melee_matcher, mails, timer)
        #        defer.addCallback(self._check)
        #        defer.callback(True)
        if melee.need_query_rank():
            defer = melee_matcher.query_ranking(data, melee)
            defer.addCallback(self._update_title_level,
                    data, melee, melee_matcher, mails, timer)
            defer.addCallback(self._check)
        else:
            defer = Deferred()
            defer.addCallback(self._update_title_level,
                    data, melee, melee_matcher, mails, timer)
            defer.addCallback(self._check)
            defer.callback(True)

        #if melee_business.is_need_broadcast_title(old_title_level, melee):
        #    #演武场获得高段位发广播
        #    self._add_melee_broadcast_title(user, melee)
            
        defer.addCallback(self._pack_update_melee_response,
                data, melee, melee_matcher, mails, last_battle_win, req, timer)
        return defer


    def _update_title_level(self, proxy, data, melee, melee_matcher, mails, timer):
        if not melee_business.update_melee_title_level(data, melee, melee_matcher.rank, mails, timer.now):
            raise Exception("Update melee title level fail")
        melee.reset_last_battle_win()

        return True


    def _add_melee_broadcast_title(self, user, melee):
        """广播玩家演武场战况
        Args:

        """
        (mode, priority, life_time, content) = melee_business.create_broadcast_content_title(user, melee)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add melee broadcast title[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_melee_broadcast_title_result)
        return defer


    def _check_add_melee_broadcast_title_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add melee broadcast title result failed")

        return True


    def _pack_update_melee_response(self, proxy, data, melee, melee_matcher, mails,
            last_battle_win, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_melee_info(data.user.get(True), melee, res.arena_info, timer.now, melee_matcher.rank)
        #if last_battle_win:
        #    #对手信息
        #    rivals_id = melee.generate_arena_rivals_id()
        #    for rival_id in rivals_id:
        #        rival = data.rival_list.get(rival_id, True)
        #        if rival is not None:
        #            pack.pack_melee_player(rival, res.arena_info.rivals.add())

        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._update_melee_succeed, req, res, timer)
        return defer


    def _update_melee_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Update melee succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _update_melee_failed(self, err, req, timer):
        logger.fatal("Update melee failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update melee failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def get_melee_win_num_reward(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_get_melee_win_num_reward, req, timer)
        defer.addErrback(self._get_melee_win_num_reward_failed, req, timer)
        return defer


    def _calc_get_melee_win_num_reward(self, data, req, timer):
        user = data.user.get()
        melee = data.melee.get()
        if not melee.is_able_to_unlock(user):
            raise Exception("melee is not unlock[user_level=%d]" % user.level)

        if not melee_business.get_melee_win_num_reward(data, melee, timer.now):
            raise Exception("melee get win num reward failed")

        #验证客户端正确性
        for item_info in req.items:
            compare.check_item(data, item_info)

        melee_matcher = MeleeMatcher()
        if melee.need_query_rank():
            defer = melee_matcher.query_ranking(data, melee)
        else:
            defer = Deferred()
            defer.callback(True)

        defer.addCallback(self._pack_get_melee_win_num_reward_response,
                data, melee, melee_matcher, req, timer)
        return defer


    def _pack_get_melee_win_num_reward_response(self, proxy, data, melee,
            melee_matcher, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_melee_info(data.user.get(True), melee, res.arena_info,
                timer.now, melee_matcher.rank)
        #胜场奖励
        if melee.is_able_to_get_win_num_reward():
            pack.pack_arena_reward_info(melee, res.arena_info.win_num_reward)

        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)


        defer = DataBase().commit(data)
        defer.addCallback(self._get_melee_win_num_reward_succeed, req, res, timer)
        return defer


    def _get_melee_win_num_reward_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Get melee win num reward succeed",
                req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _get_melee_win_num_reward_failed(self, err, req, timer):
        logger.fatal("Get melee win num reward failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Get melee win num reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_melee_ranking(self, user_id, request):
        """
        """
        timer = Timer(user_id)

        req = arena_pb2.QueryArenaInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_melee_ranking, req, timer)
        defer.addErrback(self._query_melee_ranking_failed, req, timer)
        return defer


    def _calc_query_melee_ranking(self, data, req, timer):
        user = data.user.get()
        if not user.allow_pvp_arena:
            raise Exception("melee is not unlock[user_level=%d]" % user.level)

        melee = data.melee.get()
        melee_matcher = MeleeMatcher()
        RANKING_COUNT = 20
        users = []
        defer = melee_matcher.query_melee_users_by_ranking(data, melee, RANKING_COUNT, users)
        defer.addCallback(self._pack_query_melee_ranking_response,
                data, melee, melee_matcher, users, req, timer)
        return defer


    def _pack_query_melee_ranking_response(self, proxy, data, melee, melee_matcher, users, req, timer):
        """构造返回
        args:
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_melee_info(data.user.get(True), melee, res.arena_info, timer.now,
                melee_matcher.rank)
        res.arena_info.own.ranking_index = melee_matcher.rank
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
        log = log_formater.output(data, "Query melee ranking succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _query_melee_ranking_failed(self, err, req, timer):
        logger.fatal("Query melee ranking failed[reason=%s]" % err)

        res = arena_pb2.QueryArenaInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query melee ranking failed[user_id=%d][req=%s][res=%s][consume=%d]" %
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
        melee = data.melee.get()
        (win_score, lose_score) = melee_business.calc_battle_score(melee, req.rival_score)
        score_delta = 0
        if req.status == MeleeRecordInfo.STATUS_DEFEND_LOSE:
            score_delta = lose_score
        else:
            score_delta = win_score

        melee.add_score(score_delta)
        record = melee_business.add_melee_record(data,
                req.rival_user_id, base64.b64encode(req.rival_name), req.rival_level,
                req.rival_icon_id, req.status, score_delta)

        mails = []
        melee_matcher = MeleeMatcher()
        if melee.need_query_rank():
            defer = melee_matcher.query_ranking(data, melee)
            defer.addCallback(self._update_title_level,
                    data, melee, melee_matcher, mails, timer)
            defer.addCallback(self._check)
        else:
            defer = Deferred()
            defer.addCallback(self._update_title_level,
                    data, melee, melee_matcher, mails, timer)
            defer.addCallback(self._check)
            defer.callback(True)

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_notice_succeed, req, melee, melee_matcher, record, timer)
        return defer


    def _receive_notice_succeed(self, data, req, melee, melee_matcher, record, timer):
        res = internal_pb2.ArenaResultNoticeRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive melee notice succeed", req, res, timer.count_ms())
        logger.notice(log)

        self._push_record(data, data.user.get(True), melee, melee_matcher.rank, record, timer)
        return response


    def _push_record(self, data, user, melee, ranking, record, timer):
        """向客户端推送对战记录，如果用户不在线，则推送失败
        """
        res = arena_pb2.QueryArenaInfoRes()
        res.status = 0

        pack.pack_melee_info(user, melee, res.arena_info, timer.now, ranking)
        #对战记录
        pack.pack_arena_record(record, res.arena_info.records.add())

        response = res.SerializeToString()
        return GlobalObject().root.callChild("portal", "push_melee_record", data.id, response)


    def _receive_notice_failed(self, err, req, timer):
        logger.fatal("Receive melee notice failed[reason=%s]" % err)
        res = internal_pb2.ArenaResultNoticeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive melee notice failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _check(self, status):
        assert status is True
        return self


