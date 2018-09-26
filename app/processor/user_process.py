#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : User 相关处理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from utils import utils
from proto import monarch_pb2
from proto import guide_pb2
from proto import user_pb2
from proto import internal_pb2
from app.data.item import ItemInfo
from datalib.global_data import DataBase
from datalib.data_proxy4redis import DataProxy
from datalib.data_loader import data_loader
from app import log_formater
from app import pack


class UserProcessor(object):
    """处理 User 相关逻辑"""

    def update_name(self, user_id, request):
        """更新主公名称"""
        timer = Timer(user_id)
        req = monarch_pb2.UpdateMonarchReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._change_name, req)
        defer.addCallback(self._update_succeed, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer


    def _change_name(self, data, req):
        """
        """
        if not req.monarch.HasField("name"):
            raise Exception("Invalid request, empty name")

        user = data.user.get()
        gold_cost = user.calc_change_name_gold_cost()
        resource = data.resource.get()
        pay = data.pay.get(True)
        original_gold = resource.gold
        #新手引导期内改名字不扣元宝
        if user.is_basic_guide_finish():
            if not resource.cost_gold(gold_cost):
                raise Exception("Change user name failed")
        log = log_formater.output_gold(data, -gold_cost, log_formater.UPDATE_USER_NAME,
           "Update user name by gold", before_gold = original_gold)
        logger.notice(log)


        if not user.change_name(req.monarch.name):
            raise Exception("Change user name failed")
        
	    logger.notice("Submit Role[user_id=%d][level=%d][name=%s][vip=%d][status=CHANGE_NAME][create_time=%d][last_login_time=%d][money=%d][food=%d][gold=%d][pay_count=%d][pay_amount=%.2f]"
                % (user.id, user.level, user.name, user.vip_level, user.create_time, user.last_login_time, resource.money, resource.food, resource.gold, pay.pay_count, pay.pay_amount))
        defer = DataBase().commit(data)
        return defer


    def _update_succeed(self, data, req, timer):
        res = monarch_pb2.UpdateMonarchRes()
        res.status = 0
        response = res.SerializeToString()
        
        log = log_formater.output(data, "Update user succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_failed(self, err, req, timer):
        logger.fatal("Update user failed[reason=%s]" % err)

        res = monarch_pb2.UpdateMonarchRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update user failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_icon(self, user_id, request):
        """更新主公头像"""
        timer = Timer(user_id)

        req = monarch_pb2.UpdateMonarchReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._change_icon, req)
        defer.addCallback(self._update_succeed, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer


    def _change_icon(self, data, req):
        if not req.monarch.HasField("headicon_id"):
            raise Exception("Invalid request, empty icon")

        user = data.user.get()

        if not user.change_icon(req.monarch.headicon_id):
            raise Exception("Change icon failed")

        defer = DataBase().commit(data)
        return defer


    def forward_guide(self, user_id, request):
        """完成新手引导 stage
        """
        timer = Timer(user_id)

        req = guide_pb2.ForwardGuideReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_forward_guide, req, timer)
        defer.addCallback(self._forward_guide_succeed, req, timer)
        defer.addErrback(self._forward_guide_failed, req, timer)
        return defer


    def _calc_forward_guide(self, data, req, timer):
        user = data.user.get()
        if not user.finish_guide_stage(req.stage):
            raise Exception("Finish guide stage failed")

        return DataBase().commit(data)


    def _forward_guide_succeed(self, data, req, timer):
        res = guide_pb2.ForwardGuideRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Forward guide succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _forward_guide_failed(self, err, req, timer):
        logger.fatal("Forward guide failed[reason=%s]" % err)

        res = guide_pb2.ForwardGuideRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Forward guide failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def manage_guide(self, user_id, request):
        """管理新手引导
        """
        timer = Timer(user_id)

        req = guide_pb2.ManageGuideReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_manage_guide, req, timer)
        defer.addCallback(self._manage_guide_succeed, req, timer)
        defer.addErrback(self._manage_guide_failed, req, timer)
        return defer


    def _calc_manage_guide(self, data, req, timer):
        user = data.user.get()

        for stage_id in req.finish.stages:
            user.finish_guide_stage(stage_id)
        for stage_id in req.reset.stages:
            user.reset_guide_stage(stage_id)

        return DataBase().commit(data)


    def _manage_guide_succeed(self, data, req, timer):
        res = guide_pb2.ManageGuideRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Manage guide succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _manage_guide_failed(self, err, req, timer):
        logger.fatal("Manage guide failed[reason=%s]" % err)

        res = guide_pb2.ManageGuideRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Manage guide failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_vip_points(self, user_id, request):
        """添加vip points
        """
        timer = Timer(user_id)
        req = internal_pb2.AddVipPointsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_vip_points, req)
        defer.addCallback(self._add_vip_points_succeed, req, timer)
        defer.addErrback(self._add_vip_points_failed, req, timer)
        return defer


    def _calc_add_vip_points(self, data, req):
        """
        """
        user = data.user.get()
        user.gain_vip_points(req.pay_price)

        defer = DataBase().commit(data)
        return defer


    def _add_vip_points_succeed(self, data, req, timer):
        res = internal_pb2.AddVipPointsRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Add vip points succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_vip_points_failed(self, err, req, timer):
        logger.fatal("Add vip points failed[reason=%s]" % err)

        res = internal_pb2.AddVipPointsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add vip points failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def be_invited(self, user_id, request):
        """被邀请者发起请求
        """
        timer = Timer(user_id)
        req = user_pb2.InviteReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_be_invited, req, timer)
        defer.addErrback(self._be_invited_failed, req, timer)
        return defer


    def _calc_be_invited(self, data, req, timer):
        """
        """
        inviter_id = utils.decode(req.invite_code, utils.INVITE_CODE_KEY)
        if inviter_id == "":
            inviter_id = 0
        else:
            inviter_id = long(inviter_id)

        cache_proxy = DataProxy()
        #查询玩家所在房间人数
        cache_proxy.search("user", inviter_id)
        defer = cache_proxy.execute()
        defer.addCallback(self._check_inviter_id, data, inviter_id, req, timer)
        return defer       
        

    def _check_inviter_id(self, proxy, data, inviter_id, req, timer):
        user = data.user.get(True)
        if user.is_invited() or user.id == inviter_id:
            res = user_pb2.InviteRes()
            res.status = 0
            res.ret = user_pb2.INVITE_DUPLICATE
            defer = DataBase().commit(data)
            defer.addCallback(self._be_invited_succeed, req, res, timer)
            return defer

        user_result = proxy.get_result("user", inviter_id)
        if user_result is None:
            logger.warning("Invalid inviter[err_inviter_id=%d]" % inviter_id)

            res = user_pb2.InviteRes()
            res.status = 0
            res.ret = user_pb2.INVITE_CODE_INVALID
            defer = DataBase().commit(data)
            defer.addCallback(self._be_invited_succeed, req, res, timer)
            return defer

        forward_req = user_pb2.InviteReq()
        forward_req.invite_code = req.invite_code
        forward_req.invitee_id = user.id
        forward_req.invitee_level = user.level
        forward_request = forward_req.SerializeToString()

        defer = GlobalObject().root.callChild(
                'portal', "forward_be_invited", user_result.id, forward_request)
        defer.addCallback(self._check_forward_be_invited_result, data, inviter_id, req, timer)
        return defer


    def _check_forward_be_invited_result(self, response, data, inviter_id, req, timer):
        res = user_pb2.InviteRes()
        res.ParseFromString(response)

        if res.status != 0:
            logger.warning("Forward be invited result failed")
            #raise Exception("Notice battle result failed")
        else:
            if res.ret == user_pb2.INVITE_OK:
                user = data.user.get()
                user.set_inviter(inviter_id)
                res.inviter_user_id = inviter_id

        defer = DataBase().commit(data)
        defer.addCallback(self._be_invited_succeed, req, res, timer)
        return defer


    def _be_invited_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Be invited succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _be_invited_failed(self, err, req, timer):
        logger.fatal("Be invited failed[reason=%s]" % err)

        res = user_pb2.InviteRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Be invited failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_from_invitee(self, user_id, request):
        """接收到被邀请者发来的请求
        """
        timer = Timer(user_id)

        req = user_pb2.InviteReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_from_invitee, req, timer)
        defer.addErrback(self._receive_from_invitee_failed, req, timer)
        return defer


    def _calc_receive_from_invitee(self, data, req, timer):
        """
        """
        res = user_pb2.InviteRes()
        res.status = 0

        user = data.user.get()
        if user.add_invitee(req.invitee_id, req.invitee_level):
            res.ret = user_pb2.INVITE_OK
        else:
            res.ret = user_pb2.INVITE_CODE_REACH_LIMITED
        
        defer = DataBase().commit(data)
        defer.addCallback(self._receive_from_invitee_succeed, req, res, timer)
        return defer


    def _receive_from_invitee_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Receive from invitee succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _receive_from_invitee_failed(self, err, req, timer):
        logger.fatal("Receive from invitee failed[reason=%s]" % err)
        res = user_pb2.InviteRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive from invitee failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_invitee_upgrade(self, user_id, request):
        """接收到被邀请者发来的升级情况
        """
        timer = Timer(user_id)

        req = user_pb2.InviteReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_invitee_upgrade, req, timer)
        defer.addErrback(self._receive_invitee_upgrade_failed, req, timer)
        return defer


    def _calc_receive_invitee_upgrade(self, data, req, timer):
        """
        """
        res = user_pb2.InviteRes()
        res.status = 0

        user = data.user.get()
        user.update_invitee(req.invitee_id, req.invitee_level)
        res.ret = user_pb2.INVITE_OK
        
        defer = DataBase().commit(data)
        defer.addCallback(self._receive_invitee_upgrade_succeed, req, res, timer)
        return defer


    def _receive_invitee_upgrade_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Receive invitee upgrade succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _receive_invitee_upgrade_failed(self, err, req, timer):
        logger.fatal("Receive invitee upgrade failed[reason=%s]" % err)
        res = user_pb2.InviteRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive invitee upgrade failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_suggested_country(self, user_id, request):
        """查询推荐的国家势力
        """
        timer = Timer(user_id)
        req = monarch_pb2.QuerySuggestedCountryReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_suggested_country, req, timer)
        defer.addErrback(self._query_suggested_country_failed, req, timer)
        return defer


    def _calc_query_suggested_country(self, data, req, timer):
        """
        """
        req = monarch_pb2.QuerySuggestedCountryReq()
        request = req.SerializeToString()

        logger.debug("sync common country[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("query_suggested_country", 1, request)
        defer.addCallback(self._check_query_suggested_country_result, data, req, timer)
        return defer


    def _check_query_suggested_country_result(self, response, data, req, timer):
        res = monarch_pb2.QuerySuggestedCountryRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Check query suggested country result failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._query_suggested_country_succeed, req, res, timer)
        return defer


    def _query_suggested_country_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query suggested country succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_suggested_country_failed(self, err, req, timer):
        logger.fatal("Query suggested country failed[reason=%s]" % err)

        res = monarch_pb2.QuerySuggestedCountryRes()
        #就算错误，也返回一个值
        res.status = 0
        res.country = 1
        res.reward_gold = int(float(data_loader.OtherBasicInfo_dict["reward_gold_for_choose_country"].value)) - 100
        response = res.SerializeToString()
        logger.notice("Query suggested country failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_country(self, user_id, request):
        """更改国家势力
        """
        timer = Timer(user_id)
        req = monarch_pb2.UpdateCountryReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_country, req, timer)
        defer.addErrback(self._update_country_failed, req, timer)
        return defer


    def _calc_update_country(self, data, req, timer):
        """
        """
        #使用将军令
        item_id = ItemInfo.generate_id(data.id, req.item_basic_id)
        item = data.item_list.get(item_id)
        if item is None:
            logger.warning("Item not exist")
        else:
            item.consume(max(0, req.item_num))

        request = req.SerializeToString()

        logger.debug("sync common country[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("update_country", 1, request)
        defer.addCallback(self._check_update_country_result, data, req, timer)
        return defer


    def _check_update_country_result(self, response, data, req, timer):
        res = monarch_pb2.UpdateCountryRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Check update country result failed")

        user = data.user.get()
        user.update_country(req.new_country)

        resource = data.resource.get()
        original_gold = resource.gold
        resource.gain_gold(req.reward_gold)
        log = log_formater.output_gold(data, req.reward_gold, log_formater.CHECK_UPDATE_COUNTRY,
                "Gain gold from check update country", before_gold = original_gold)
        logger.notice(log)

	 
        resource.update_current_resource(timer.now)
        pack.pack_resource_info(resource, res.resource)
        
        defer = DataBase().commit(data)
        defer.addCallback(self._update_country_succeed, req, res, timer)
        return defer


    def _update_country_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Update country succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _update_country_failed(self, err, req, timer):
        logger.fatal("Update country failed[reason=%s]" % err)

        res = monarch_pb2.UpdateCountryRes()
        res.status = 1
        response = res.SerializeToString()
        logger.notice("Update country failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



