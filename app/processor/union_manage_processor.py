#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟管理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import union_pb2
from proto import internal_union_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app.union_patcher import UnionPatcher
from app.union_member_matcher import UnionMemberMatcher
from app.union_member_matcher import UnionMemberDetailMatcher
from app.business import union_battle as union_battle_business
from app.business import mail as mail_business
from datalib.data_proxy4redis import DataProxy


class UnionManageProcessor(object):

    def join(self, user_id, request):
        """加入联盟
        """
        timer = Timer(user_id)

        req = union_pb2.JoinUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_join, req, timer)
        defer.addErrback(self._join_failed, req, timer)
        return defer


    def _calc_join(self, data, req, timer):
        union = data.union.get(True)
        if union.is_locked(timer.now):
            #处于锁定状态
            res = union_pb2.JoinUnionRes()
            res.status = 0
            res.ret = union_pb2.UNION_LOCKED

            defer = DataBase().commit(data)
            defer.addCallback(self._join_succeed, req, res, timer)
            return defer

        if union.is_belong_to_union() and not union.is_belong_to_target_union(req.union_id):
            #已经属于某个其他联盟
            res = union_pb2.JoinUnionRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

            defer = DataBase().commit(data)
            defer.addCallback(self._join_succeed, req, res, timer)
            return defer

        #请求 Union 模块，加入联盟
        user = data.user.get(True)
        battle_score = data.battle_score.get(True)

        union_req = internal_union_pb2.InternalJoinUnionReq()
        union_req.user_id = data.id
        union_req.user_name = user.get_readable_name()
        union_req.user_icon_id = user.icon_id
        union_req.user_level = user.level
        union_req.user_battle_score = battle_score.score

        defer = GlobalObject().remote['gunion'].callRemote(
                "join_union", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_join_result, data, req, timer)
        return defer


    def _calc_join_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Join union res error")

        if union_res.ret != union_pb2.UNION_OK:
            res = union_pb2.JoinUnionRes()
            res.status = 0
            res.ret = union_res.ret
            defer = DataBase().commit(data)
            defer.addCallback(self._join_succeed, req, res, timer)
            return defer

        else:
            return self._patch_query_info(union_res, data, req, timer)


    def _patch_query_info(self, union_res, data, req, timer):
        """补充联盟信息
        """
        assert union_res.ret == union_pb2.UNION_OK
        union = data.union.get()
        if not union.is_belong_to_target_union(union_res.union.id):
            union.join_union(union_res.union.id, timer.now)

        res = union_pb2.JoinUnionRes()
        res.status = 0
        res.ret = union_res.ret

        #填充 union message
        defer = UnionPatcher().patch(res.union, union_res.union, data, timer.now)
        defer.addCallback(self._do_patch_query_info, data, req, res, timer)
        return defer


    def _do_patch_query_info(self, patcher, data, req, res, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._join_succeed, req, res, timer)
        return defer


    def _join_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Join union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _join_failed(self, err, req, timer):
        logger.fatal("Join union failed[reason=%s]" % err)
        res = union_pb2.JoinUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Join union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def approve(self, user_id, request):
        """审批联盟加入申请
        """
        timer = Timer(user_id)

        req = union_pb2.ApproveUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_approve, req, timer)
        defer.addErrback(self._approve_failed, req, timer)
        return defer


    def _calc_approve(self, data, req, timer):
        """审批
        """
        #判断目标用户是否存在
        proxy = DataProxy()
        proxy.search("user", req.target_user_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_approve_query, data, req, timer)
        return defer

    def _calc_approve_query(self, proxy, data, req, timer):
        if proxy.get_result("user", req.target_user_id) is None:
            res = union_pb2.ApproveUnionRes()
            res.status = 0
            res.ret = UNION_MEMBER_INVALID
            
            defer = DataBase().commit(data)
            defer.addCallback(self._approve_succeed, req, res, timer)
            return defer

        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            #玩家已经不属于联盟
            logger.debug("User is not belong to union")
            res = union_pb2.ApproveUnionRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

            defer = DataBase().commit(data)
            defer.addCallback(self._approve_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalApproveUnionReq()
        union_req.user_id = data.id
        union_req.target_user_id = req.target_user_id
        union_req.agree = req.agree

        #请求 Union 模块，查询联盟情况
        defer = GlobalObject().remote['gunion'].callRemote(
                "approve_union", union.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_approve_result, data, req, timer)
        return defer


    def _calc_approve_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Approve union res error")

        res = union_pb2.ApproveUnionRes()
        res.status = 0
        res.ret = union_res.ret

        defer = DataBase().commit(data)
        defer.addCallback(self._approve_succeed, req, res, timer)
        return defer


    def _approve_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Approve union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _approve_failed(self, err, req, timer):
        logger.fatal("Approve union failed[reason=%s]" % err)
        res = union_pb2.ApproveUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Approve union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def been_accept(self, user_id, request):
        """入盟申请被联盟接受
        """
        timer = Timer(user_id)

        req = internal_union_pb2.InternalUnionOperateReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_accept, req, timer)
        defer.addErrback(self._accept_failed, req, timer)
        return defer


    def _calc_accept(self, data, req, timer):
        res = internal_union_pb2.InternalUnionOperateRes()
        res.status = 0

        union = data.union.get()
        if union.is_belong_to_target_union(req.union_id):
            #玩家已经属于该联盟，重复接受
            res.ret = union_pb2.UNION_OK
        elif not union.is_application_valid(req.time):
            #申请已失效
            logger.debug("Application is not valid")
            res.ret = union_pb2.UNION_APPLICATION_INVALID
        else:
            union.join_union(req.union_id, timer.now)
            #添加邮件
            content = data_loader.ServerDescKeyInfo_dict[
                    "accept_by_union_content"].value.encode("utf-8")
            content = content.replace("@union_name", req.union_name)
            content = content.replace("@union_id", str(req.union_id))
            self._add_notice_mail(data, content, timer)
            res.ret = union_pb2.UNION_OK

        defer = DataBase().commit(data)
        defer.addCallback(self._accept_succeed, req, res, timer)
        return defer


    def _accept_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Accept union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _accept_failed(self, err, req, timer):
        logger.fatal("Accept union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalUnionOperateRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_notice_mail(self, data, content, timer):
        mail = mail_business.create_union_mail(data, content, timer.now)
        if mail is None:
            raise Exception("Add union notice receive mail failed")
        return mail


    def been_kickout(self, user_id, request):
        """被踢出联盟
        """
        timer = Timer(user_id)

        req = internal_union_pb2.InternalUnionOperateReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_kickout, req, timer)
        defer.addErrback(self._kickout_failed, req, timer)
        return defer


    def _calc_kickout(self, data, req, timer):
        res = internal_union_pb2.InternalUnionOperateRes()
        res.status = 0

        union = data.union.get()
        if union.union_id != req.union_id:
            #已经不是对应联盟的成员
            res.ret = union_pb2.UNION_OK

        else:
            if not union.leave_union(req.union_id, timer.now, False):
                raise Exception("Leave union failed")

            #如果参加了联盟战争防御部署，移除防御队伍
            union_battle_business.cancel_all_deploy_for_union_battle(data)

            #添加邮件
            content = data_loader.ServerDescKeyInfo_dict[
                    "remove_from_union_content"].value.encode("utf-8")
            content = content.replace("@union_name", req.union_name)
            content = content.replace("@union_id", str(req.union_id))
            self._add_notice_mail(data, content, timer)
            res.ret = union_pb2.UNION_OK

        defer = DataBase().commit(data)
        defer.addCallback(self._kickout_succeed, req, res, timer)
        return defer


    def _kickout_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Kickout from union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _kickout_failed(self, err, req, timer):
        logger.fatal("Kickout from union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalUnionOperateRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Kickout from union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def manage(self, user_id, request):
        """管理联盟
        """
        timer = Timer(user_id)

        req = union_pb2.ManageUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_manage, req, timer)
        defer.addErrback(self._manage_failed, req, timer)
        return defer


    def _calc_manage(self, data, req, timer):
        """管理
        """
        union = data.union.get()
        if  req.op != union_pb2.ManageUnionReq.DISMISSFORCE: 
            if not union.is_belong_to_target_union(req.union_id):
                #玩家已经不属于联盟
                logger.debug("User is not belong to union")
                res = union_pb2.ManageUnionRes()
                res.status = 0
                res.ret = union_pb2.UNION_NOT_MATCHED
                res.monarch.user_id = data.id 
                res.monarch.union_id = union.union_id

                defer = DataBase().commit(data)
                defer.addCallback(self._manage_succeed, req, res, timer)
                return defer

        union_req = internal_union_pb2.InternalManageUnionReq()
        union_req.user_id = data.id
        union_req.op = req.op
        union_req.target_user_id = req.target_user_id

        #请求 Union 模块，管理联盟
        defer = GlobalObject().remote['gunion'].callRemote(
                    "manage_union", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_manage_result, data, req, timer)
        return defer


    def _calc_manage_result(self, union_response, data, req, timer):
        """
        """
        union_res = internal_union_pb2.InternalQueryUnionRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Manage union res error")

        res = union_pb2.ManageUnionRes()
        res.status = 0
        res.ret = union_res.ret

        if res.ret == union_pb2.UNION_OK and req.op == req.EXIT:
            #主动退出联盟
            union = data.union.get()
            if not union.leave_union(req.union_id, timer.now):
                raise Exception("Leave union failed")

            #如果参加了联盟战争防御部署，移除防御队伍
            union_battle_business.cancel_all_deploy_for_union_battle(data)

        elif res.ret == union_pb2.UNION_OK and req.op == req.DISMISS:
            #解散联盟
            union = data.union.get()
            if not union.leave_union(req.union_id, timer.now, initiative = False):
                raise Exception("Leave union failed")
        elif res.ret == union_pb2.UNION_OK and req.op == req.DISMISSFORCE:
            #强制解散联盟
            union = data.union.get()
            if not union.leave_union(req.union_id, timer.now, initiative = False, force = True):
                raise Exception("Leave union failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._manage_succeed, req, res, timer)
        return defer


    def _manage_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Manage union succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _manage_failed(self, err, req, timer):
        logger.fatal("Manage union failed[reason=%s]" % err)
        res = union_pb2.ManageUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Manage union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_member(self, user_id, request):
        """查询联盟成员信息
        """
        timer = Timer(user_id)

        req = union_pb2.QueryUnionMemberReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_member, req, timer)
        defer.addErrback(self._query_member_failed, req, timer)
        return defer


    def _calc_query_member(self, data, req, timer):
        """查询联盟成员详细信息
        """
        union = data.union.get()
        if not union.is_belong_to_target_union(req.union_id):
            #玩家不属于联盟
            logger.debug("User is not belong to union")
            res = union_pb2.QueryUnionMemberRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

            defer = DataBase().commit(data)
            defer.addCallback(self._query_member_succeed, req, res, timer)
            return defer

        matcher = UnionMemberDetailMatcher()
        defer = matcher.match(req.target_user_id, req.union_id)
        defer.addCallback(self._calc_member_detail, data, req, timer)
        return defer


    def _calc_member_detail(self, matcher, data, req, timer):
        res = union_pb2.QueryUnionMemberRes()
        res.status = 0

        if matcher.union.union_id != req.union_id:
            logger.debug("User is not belong to union")
            res.ret = union_pb2.UNION_MEMBER_INVALID

        else:
            res.ret = union_pb2.UNION_OK

            #队伍 & 英雄
            for team in matcher.teams:
                pack.pack_team_info(team, res.teams.add())
            for team_msg in res.teams:
                for hero_msg in team_msg.heroes:
                    if hero_msg.basic_id != 0:
                        hero = matcher.heroes[hero_msg.basic_id]
                        pack.pack_hero_info(hero, hero_msg, timer.now)

            #战斗科技
            for tech in matcher.technologys:
                if tech.is_battle_technology():
                    res.battle_tech_ids.append(tech.basic_id)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_member_succeed, req, res, timer)
        return defer


    def _query_member_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union member succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_member_failed(self, err, req, timer):
        logger.fatal("Query union member failed[reason=%s]" % err)
        res = union_pb2.QueryUnionMemberRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union member failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_honor(self, user_id, request):
        """添加荣誉
        """
        timer = Timer(user_id)

        req = union_pb2.AddUnionHonorReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_honor, req, timer)
        defer.addErrback(self._add_honor_failed, req, timer)
        return defer


    def _calc_add_honor(self, data, req, timer):
        """
        """
        union = data.union.get()
        if not union.is_belong_to_target_union(req.union_id):
            #玩家不属于联盟
            logger.debug("User is not belong to union")
            res = union_pb2.AddUnionHonorRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED
            res.monarch.user_id = data.id
            res.monarch.union_id = union.union_id

            defer = DataBase().commit(data)
            defer.addCallback(self._add_honor_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalAddUnionHonorReq()
        union_req.user_id = data.id
        union_req.honor = req.honor

        defer = GlobalObject().remote['gunion'].callRemote(
                "add_honor", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_add_honor_result, data, req, timer)
        return defer


    def _calc_add_honor_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalAddUnionHonorRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Add union honor res error")

        if union_res.ret == union_pb2.UNION_OK:
            union = data.union.get()
            union.gain_honor(req.honor)

        res = union_pb2.JoinUnionRes()
        res.status = 0
        res.ret = union_res.ret

        defer = DataBase().commit(data)
        defer.addCallback(self._add_honor_succeed, req, res, timer)
        return defer


    def _add_honor_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Add union honor succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_honor_failed(self, err, req, timer):
        logger.fatal("Add union honor failed[reason=%s]" % err)
        res = union_pb2.AddUnionHonorRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add union honor failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

