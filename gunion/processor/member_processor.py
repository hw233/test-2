#coding:utf8
"""
Created on 2016-06-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟成员管理逻辑
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from proto import internal_union_pb2
from proto import internal_pb2
from proto import union_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from gunion.business import union as union_business
from gunion.business import member as member_business
from gunion.business import battle as battle_business
from gunion import pack


class MemberProcessor(object):


    def join(self, union_id, request):
        """加入联盟
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalJoinUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_join, req, timer)
        defer.addErrback(self._join_failed, req, timer)
        return defer


    def _calc_join(self, data, req, timer):
        """加入
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_join_response_invalid(union_pb2.UNION_JOIN_INVALID)
            return self._join_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        if member is not None:
            #已经加入此联盟
            logger.debug("User is belong to union")
            res = self._pack_join_response(data, req.user_id, timer)
        else:
            union = data.union.get()
            if union.is_member_full():
                #联盟已满员
                logger.debug("Union is full")
                res = self._pack_join_response_invalid(union_pb2.UNION_JOIN_FULL)

            elif req.user_level < union.join_level_limit:
                #玩家等级不满足要求
                logger.debug("User level is not satisfy")
                res = self._pack_join_response_invalid(union_pb2.UNION_JOIN_LEVEL_ERROR)

            elif union.join_status == union.JOIN_STATUS_DISABLE:
                #不允许加入
                logger.debug("Union is disable join")
                res = self._pack_join_response_invalid(union_pb2.UNION_JOIN_INVALID)

            elif union.join_status == union.JOIN_STATUS_VERIFY:
                #需要验证，添加申请
                logger.debug("Add join application")
                member_business.add_application(data,
                        req.user_id, req.user_name, req.user_icon_id,
                        req.user_level, req.user_battle_score, timer.now)
                res = self._pack_join_response_invalid(union_pb2.UNION_JOIN_WAIT_VERIFY)

            else:
                #允许加入，添加成员
                if member_business.join_union(data, req.user_id, timer.now):
                    res = self._pack_join_response(data, req.user_id, timer)
                else:
                    res = self._pack_join_response_invalid(union_pb2.UNION_JOIN_INVALID)

        defer = DataBase().commit(data)
        defer.addCallback(self._join_succeed, req, res, timer)
        return defer


    def _pack_join_response_invalid(self, ret):
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_join_response(self, data, user_id, timer):
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        union = data.union.get(True)
        pack.pack_union_info(union, res.union)

        for member in data.member_list.get_all(True):
            pack.pack_member_info(member, res.union.members.add())

        for aid in data.aid_list.get_all(True):
            if aid.is_active_for(data.id, timer.now):
                pack.pack_aid_info(aid, res.union.aids.add(), user_id, timer.now)

        #战争基础信息
        season = data.season.get(True)
        battle = battle_business.update_battle(data, timer.now)
        pack.pack_battle_info(union, season, battle, res.union.battle, timer.now)

        #个人数据
        member = member_business.find_member(data, user_id)
        pack.pack_battle_individual_info(member, res.union.battle.user)

        #己方防守地图信息
        nodes = battle_business.get_battle_map(data)
        pack.pack_battle_map_info(union, season,
                battle, nodes, res.union.battle.own_map, timer.now)

        #战斗记录
        records = data.battle_record_list.get_all(True)
        for record in records:
            pack.pack_battle_record_info(record, res.union.battle.records.add(), timer.now)

        return res


    def _join_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Join union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _join_failed(self, err, req, timer):
        logger.fatal("Join union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Join union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def approve(self, union_id, request):
        """审批联盟申请
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalApproveUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_approve, req, timer)
        defer.addErrback(self._approve_failed, req, timer)
        return defer


    def _calc_approve(self, data, req, timer):
        """审批
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_approve_response(union_pb2.UNION_NOT_MATCHED)
            return self._approve_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        target_member = member_business.find_member(data, req.target_user_id)
        application = member_business.find_application(data, req.target_user_id, timer.now)
        if member is None:
            res = self._pack_approve_response(union_pb2.UNION_NOT_MATCHED)
        elif member.is_normal_member():
            #普通成员没有权限
            res = self._pack_approve_response(union_pb2.UNION_NO_AUTH)
        elif target_member is not None:
            #待审批玩家已经加入联盟
            res = self._pack_approve_response(union_pb2.UNION_OK)
        elif application is None:
            #申请已经失效
            res = self._pack_approve_response(union_pb2.UNION_APPLICATION_INVALID)
        elif not req.agree:
            #拒绝申请
            member_business.disagree_application(data, application)
            res = self._pack_approve_response(union_pb2.UNION_OK)
        elif req.agree:
            #同意申请
            union = data.union.get()
            if union.is_member_full():
                #已满员，拒绝申请
                member_business.disagree_application(data, application)
                res = self._pack_approve_response(union_pb2.UNION_APPLICATION_INVALID)
            else:
                return self._accept(data, member, application, req, timer)

        defer = DataBase().commit(data)
        defer.addCallback(self._approve_succeed, req, res, timer)
        return defer


    def _accept(self, data, member, application, req, timer):
        """接受玩家申请
        """
        union = data.union.get()

        app_req = internal_union_pb2.InternalUnionOperateReq()
        app_req.operator_user_id = member.user_id
        app_req.union_name = union.get_readable_name()
        app_req.union_id = union.id
        app_req.time = application.time

        defer = GlobalObject().remote['app'].callRemote("been_accept_by_union",
                application.user_id, app_req.SerializeToString())
        defer.addCallback(self._post_accept, data, application, req, timer)
        return defer


    def _post_accept(self, app_response, data, application, req, timer):
        app_res = internal_union_pb2.InternalUnionOperateRes()
        app_res.ParseFromString(app_response)
        if app_res.status != 0:
            raise Exception("Accept user failed")

        if app_res.ret == union_pb2.UNION_OK:
            member_business.agree_application(data, application, timer.now)
        else:
            member_business.disagree_application(data, application)

        res = self._pack_approve_response(app_res.ret)
        defer = DataBase().commit(data)
        defer.addCallback(self._approve_succeed, req, res, timer)
        return defer


    def _pack_approve_response(self, ret):
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = ret
        return res


    def _approve_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Approve union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _approve_failed(self, err, req, timer):
        logger.fatal("Approve union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Approve union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def manage(self, union_id, request):
        """管理
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalManageUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_manage, req, timer)
        defer.addErrback(self._manage_failed, req, timer)
        return defer


    def _calc_manage(self, data, req, timer):
        if not data.is_valid():
            #联盟不存在
            res = self._pack_manage_response(union_pb2.UNION_NOT_MATCHED)
            return self._manage_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        if member is None:
            if req.op == union_pb2.ManageUnionReq.DISMISSFORCE:
                 self._pack_manage_response(union_pb2.UNION_OK)
            else:
                #玩家已经不属于联盟
                logger.warning("Member is not exist")
                res = self._pack_manage_response(union_pb2.UNION_NOT_MATCHED)
                defer = DataBase().commit(data)
                defer.addCallback(self._manage_succeed, req, res, timer)
                return defer

        defer = Deferred()

        if req.op == union_pb2.ManageUnionReq.KICKOUT:
            defer.addCallback(self._kickout, member, req.target_user_id, timer)
        elif req.op == union_pb2.ManageUnionReq.PROMOTION:
            defer.addCallback(self._promotion, member, req.target_user_id, timer)
        elif req.op == union_pb2.ManageUnionReq.DEMOTION:
            defer.addCallback(self._demotion, member, req.target_user_id, timer)
        elif req.op == union_pb2.ManageUnionReq.DEMISE:
            defer.addCallback(self._demise, member, req.target_user_id, timer)
        elif req.op == union_pb2.ManageUnionReq.DISMISS:
            defer.addCallback(self._dismiss, member, timer)
        elif req.op == union_pb2.ManageUnionReq.DISMISSFORCE:
            defer.addCallback(self._dismiss, member, timer, True)
        elif req.op == union_pb2.ManageUnionReq.EXIT:
            defer.addCallback(self._exit, member, timer)
        else:
            raise Exception("Invalid operation[op=%d]" % req.op)

        defer.addCallback(self._post_manage, data, req, timer)
        defer.callback(data)
        return defer


    def _post_manage(self, res, data, req, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._manage_succeed, req, res, timer)
        return defer


    def _kickout(self, data, member, target_user_id, timer):
        """踢人
        """
        target_member = member_business.find_member(data, target_user_id)
        if target_member is None:
            logger.debug("User is not belong to union")
            return self._pack_manage_response(union_pb2.UNION_MEMBER_INVALID)

        if member.user_id == target_user_id:
            #任何人都不能踢自己
            logger.debug("User is not belong to union")
            return self._pack_manage_response(union_pb2.UNION_NO_AUTH)

        elif member.is_normal_member():
            #成员不能踢人
            return self._pack_manage_response(union_pb2.UNION_NO_AUTH)

        elif member.is_vice_leader() and not target_member.is_normal_member():
            #副盟主只可以踢成员
            return self._pack_manage_response(union_pb2.UNION_NO_AUTH)

        union = data.union.get()
        member_business.leave_union(data, target_member)

        app_req = internal_union_pb2.InternalUnionOperateReq()
        app_req.operator_user_id = member.user_id
        app_req.union_name = union.get_readable_name()
        app_req.union_id = union.id

        defer = GlobalObject().remote['app'].callRemote("been_kickout_from_union",
                target_user_id, app_req.SerializeToString())
        defer.addCallback(self._post_kickout, data, timer)
        return defer


    def _post_kickout(self, app_response, data, timer):
        app_res = internal_union_pb2.InternalUnionOperateRes()
        app_res.ParseFromString(app_response)
        if app_res.status != 0:
            raise Exception("Kick out user failed")

        return self._pack_manage_response(union_pb2.UNION_OK)


    def _dismiss(self, data, leader, timer, force = False):
        """解散联盟
        """
        logger.notice("dismiss")
        if not force and not leader.is_leader():
            #只有盟主可以操作
            return self._pack_manage_response(union_pb2.UNION_NO_AUTH)

        #战争时期，无法解散联盟
        battle = battle_business.get_current_battle(data, timer.now)
        if battle.is_at_war():
            return self._pack_manage_response(union_pb2.UNION_OP_INVALID)

        #通知成员
        union = data.union.get()
        member_list = data.member_list.get_all()
        members_id = []
        if not leader == None:
            for member in member_list:
                if member.user_id != leader.user_id:
                    members_id.append(member.user_id)
            for user_id in members_id:
                self._dismiss_notice(union, user_id)
        else:
            for member in member_list:
                self._dismiss_notice(union, member.user_id)

        #解散
        union_business.dismiss_union(data)

        data.delete()
        return self._pack_manage_response(union_pb2.UNION_OK)


    def _dismiss_notice(self, union, user_id):
        """解散通知
        """
        app_req = internal_union_pb2.InternalUnionOperateReq()
        app_req.operator_user_id = user_id
        app_req.union_name = union.get_readable_name()
        app_req.union_id = union.id
        app_req.union_available = False
        defer = GlobalObject().remote['app'].callRemote("been_kickout_from_union",
                user_id, app_req.SerializeToString())
        defer.addCallback(self._post_dismiss)
        return defer


    def _post_dismiss(self, app_response):
        app_res = internal_union_pb2.InternalUnionOperateRes()
        app_res.ParseFromString(app_response)
        if app_res.status != 0:
            logger.warning("Dismiss notice failed")


    def _promotion(self, data, member, target_user_id, timer):
        """提升为副盟主
        """
        target_member = member_business.find_member(data, target_user_id)
        if target_member is None:
            return self._pack_manage_response(union_pb2.UNION_MEMBER_INVALID)

        if not member.is_leader() or member.user_id == target_user_id:
            #只有盟主可以操作，不能操作自己
            return self._pack_manage_response(union_pb2.UNION_NO_AUTH)

        if not member_business.promotion_to_vice_leader(data, target_member):
            return self._pack_manage_response(union_pb2.UNION_OP_INVALID)

        union = data.union.get(True)
        notice_content = data_loader.ServerDescKeyInfo_dict[
                "union_promote_vice_leader"].value.encode("utf-8")
        notice_content = notice_content.replace("@union_name", union.get_readable_name())
        notice_content = notice_content.replace("@union_id", str(union.id))
        self._manage_notice(target_user_id, notice_content)

        return self._pack_manage_response(union_pb2.UNION_OK)


    def _demotion(self, data, member, target_user_id, timer):
        """撤职副盟主
        """
        target_member = member_business.find_member(data, target_user_id)
        if target_member is None:
            return self._pack_manage_response(union_pb2.UNION_MEMBER_INVALID)

        if not member.is_leader() or member.user_id == target_user_id:
            #只有盟主可以操作，不能操作自己
            return self._pack_manage_response(union_pb2.UNION_NO_AUTH)

        if not member_business.demotion_to_member(data, target_member):
            return self._pack_manage_response(union_pb2.UNION_OP_INVALID)

        union = data.union.get(True)
        notice_content = data_loader.ServerDescKeyInfo_dict[
                "union_cancel_vice_leader"].value.encode("utf-8")
        notice_content = notice_content.replace("@union_name", union.get_readable_name())
        notice_content = notice_content.replace("@union_id", str(union.id))
        self._manage_notice(target_user_id, notice_content)

        return self._pack_manage_response(union_pb2.UNION_OK)


    def _demise(self, data, member, target_user_id, timer):
        """转让盟主
        """
        target_member = member_business.find_member(data, target_user_id)
        if target_member is None:
            return self._pack_manage_response(union_pb2.UNION_MEMBER_INVALID)

        if not member.is_leader() or member.user_id == target_user_id:
            #只有盟主可以操作，不能操作自己
            return self._pack_manage_response(union_pb2.UNION_NO_AUTH)

        member_business.demise_leader(data, member, target_member)

        union = data.union.get(True)
        notice_content = data_loader.ServerDescKeyInfo_dict[
                "union_promote_leader"].value.encode("utf-8")
        notice_content = notice_content.replace("@union_name", union.get_readable_name())
        notice_content = notice_content.replace("@union_id", str(union.id))
        self._manage_notice(target_user_id, notice_content)
        return self._pack_manage_response(union_pb2.UNION_OK)


    def _exit(self, data, member, timer):
        """退出联盟
        """
        union = data.union.get()
        if member.is_leader():
            #如果是盟主, 则先执行转让盟主的逻辑
            new_leader = union_business.get_transfer_member_simple(data)
            if new_leader is None:
                #联盟只剩下盟主一人,解散联盟
                return self._dismiss(data, member, timer)
            else:
                member_business.demise_leader(data, member, new_leader)

        if member.is_vice_leader():
            union.clear_vice_leader(member.user_id)

        member_business.leave_union(data, member)
        return self._pack_manage_response(union_pb2.UNION_OK)


    def _manage_notice(self, user_id, content):
        """操作通知
        """
        forward_req = internal_pb2.ReceiveMailReq()
        forward_req.user_id = user_id
        forward_req.mail.basic_id = 100
        forward_req.mail.subject = data_loader.ServerDescKeyInfo_dict[
                "union_notice"].value.encode("utf-8")
        forward_req.mail.content = content
        forward_req.mail.sender = data_loader.ServerDescKeyInfo_dict[
                "union_sender"].value.encode("utf-8")

        defer = GlobalObject().remote['app'].callRemote(
                "receive_mail", user_id, forward_req.SerializeToString())
        defer.addCallback(self._post_notice)
        return defer


    def _post_notice(self, app_response):
        app_res = internal_pb2.ReceiveMailRes()
        app_res.ParseFromString(app_response)
        if app_res.status != 0:
            logger.warning("Manage notice failed")


    def _pack_manage_response(self, ret):
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = ret
        return res


    def _manage_succeed(self, data, req, res, timer):
        if req.op == union_pb2.ManageUnionReq.DISMISS and res.ret == union_pb2.UNION_OK:
            #解散联盟成功
            DataBase().clear_data(data)

        response = res.SerializeToString()
        logger.notice("Manage union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _manage_failed(self, err, req, timer):
        logger.fatal("Manage union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Manage union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_honor(self, union_id, request):
        """添加联盟荣誉
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalAddUnionHonorReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_add_honor, req, timer)
        defer.addErrback(self._add_honor_failed, req, timer)
        return defer


    def _calc_add_honor(self, data, req, timer):
        if not data.is_valid():
            #联盟不存在
            res = self._pack_add_honor_response(union_pb2.UNION_NOT_MATCHED)
            return self._add_honor_succeed(data, req, res, timer)

        member = member_business.find_member(data, req.user_id)
        if member is None:
            #已经不在此联盟中
            logger.debug("User is not belong to union")
            res = self._pack_add_honor_response(union_pb2.UNION_NOT_MATCHED)
        else:
            member.gain_honor(req.honor)
            res = self._pack_add_honor_response(union_pb2.UNION_OK)

        defer = DataBase().commit(data)
        defer.addCallback(self._add_honor_succeed, req, res, timer)
        return defer


    def _pack_add_honor_response(self, ret):
        res = internal_union_pb2.InternalAddUnionHonorRes()
        res.status = 0
        res.ret = ret
        return res


    def _add_honor_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Add union honor succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_honor_failed(self, err, req, timer):
        logger.fatal("Add union honor failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add union honor failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def try_transfer(self, union_id, request):
        """自动转让盟主"""
        timer = Timer(union_id)

        req = internal_union_pb2.InternalTryTransferUnionLeaderReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_transfer, req, timer)
        defer.addErrback(self._transfer_failed, req, timer)
        return defer

    def _calc_transfer(self, data, req, timer):
        defer = union_business.get_leader(data)
        defer.addCallback(self._calc_transfer_userinfo, data, req, timer)
        return defer

    def _calc_transfer_userinfo(self, leader_info, data, req, timer):
        if union_business.is_need_transfer_leader(data, leader_info, timer.now):
            defer = union_business.transfer_leader(data, leader_info, timer.now)
            defer.addCallback(self._calc_transfer_transfer, data, req, timer)
            return defer
        else:
            defer = Deferred()
            defer.callback(False)
            defer.addCallback(self._calc_transfer_transfer, data, req, timer)
            return defer
    
    def _calc_transfer_transfer(self, result, data, req, timer):
        res = internal_union_pb2.InternalTryTransferUnionLeaderRes()
        res.status = 0
        if result:
            res.ret = res.OK
        else:
            res.ret = res.NEEDNT

        defer = DataBase().commit(data)
        defer.addCallback(self._transfer_succeed, req, res, timer)
        return defer

    def _transfer_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Try transfer union leader succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _transfer_failed(self, err, req, timer):
        logger.fatal("Try transfer union leader failed[reason=%s]" % err)
        res = internal_union_pb2.InternalTryTransferUnionLeaderRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Try transfer union leader failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
