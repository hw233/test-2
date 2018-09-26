#coding:utf8
"""
Created on 2016-03-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 活动相关处理逻辑
"""

import base64
import random
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils import utils
from utils.timer import Timer
from proto import activity_pb2
from proto import internal_pb2
from proto import broadcast_pb2
from datalib.data_loader import data_loader
from datalib.global_data import DataBase
from app import basic_view
from app import pack
from app import compare
from app import log_formater
from app.business import activity as activity_business
from app.business import basic_init as basic_init_business
from app.business import hero as hero_business
from app.data.activity import ActivityInfo
from twisted.internet.defer import Deferred


class ActivityProcessor(object):
    """活动相关逻辑
    """

    def query_activity(self, user_id, request):
        """查询活动信息
        """
        timer = Timer(user_id)

        req = activity_pb2.QueryActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._query_activity, user_id, req, timer)
        return defer


    def _query_activity(self, basic_data, user_id, req, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_activity, basic_data, req, timer)
        defer.addErrback(self._query_activity_failed, req, timer)
        return defer


    def _calc_query_activity(self, data, basic_data, req, timer):
        """处理操作，更新活动，再查询
        """
        if not activity_business.update_activity(basic_data, data, timer.now):
            raise Exception("Update activity failed")

        if req.HasField("style_id"):
            style = req.style_id
        else:
            style = 0

        is_cat = False
        for activity in data.activity_list.get_all(True):
            basic_activity = basic_data.activity_list.get(activity.basic_id) 
            if basic_activity.type_id == 30:
                is_cat = True
        if is_cat:
            defer = GlobalObject().remote["common"].callRemote("query_cat", 1, '')
            defer.addCallback(self._pack_query_activitycat_response, data, basic_data, style, timer.now)
            return defer
       
        res = self._pack_query_activity_response(data, basic_data, style, timer.now)
        defer = DataBase().commit(data)
        defer.addCallback(self._query_activity_succeed, req, res, timer)
        return defer


    def _pack_query_activity_response(self, data, basic_data, style, now):
        """封装查询活动的响应
        """
        res = activity_pb2.QueryActivityRes()
        res.status = 0

        #临时：活动按照id大的在前排序（为了客户端显示时比较符合习惯）
        sort_activity = []
        for activity in data.activity_list.get_all(True):
            index = 0
            for i in range(len(sort_activity)):
                if sort_activity[i].basic_id < activity.basic_id:
                    index = i
                    break
            
            sort_activity.insert(index, activity)

        for activity in sort_activity:
            basic_activity = basic_data.activity_list.get(activity.basic_id)
            if basic_activity is None:
                logger.fatal("basic activity not exsit[id=%d]" % activity.basic_id)
                continue

            if basic_activity.style_id == style and activity.is_living(now, style, True):
                basic_steps = activity_business.get_basic_activity_steps(basic_data, basic_activity)
                pack.pack_activity_info(activity, basic_activity, basic_steps, res.activities.add(), now, basic_data, data, [])

        return res


    def _pack_query_activitycat_response(self, response, data, basic_data, style, now):
        """封装查询活动的响应 
        """    
        resq= activity_pb2.QueryActivityRes()
        resq.status = 0

        common_res = activity_pb2.QueryCatRes()
        common_res.ParseFromString(response)
         
        for activity in data.activity_list.get_all(True):
            basic_activity = basic_data.activity_list.get(activity.basic_id)
            if basic_activity is None:
                logger.fatal("basic activity not exsit[id=%d]" % activity.basic_id)
                continue
            if basic_activity.style_id == style and activity.is_living(now, style, True):
                basic_steps = activity_business.get_basic_activity_steps(basic_data, basic_activity)
                pack.pack_activity_info(activity, basic_activity, basic_steps, resq.activities.add(), now, basic_data, data, common_res.cats) 
        res =  resq.SerializeToString()                                                    
        return res


    def _query_activity_succeed(self, data, req, res, timer):
        """查询活动成功
        """
        defer = DataBase().commit(data)
        response = res.SerializeToString()
        log = log_formater.output(data, "Query activity succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response

 
    def _query_activitycat_succeed(self, data, req, timer):                                                                                                                             
        """查询活动成功                                                                                                                                                                   
        """            
        #defer = DataBase().commit(data)
        response = res.SerializeToString()                                                                                                                                                                    
        log = log_formater.output(data, "Query activity succeed", req, res, timer.count_ms())                                                                                             
        logger.notice(log)                                                                                                                                                                
        return res

    def _query_activity_failed(self, err, req, timer):
        """查询活动失败
        """
        logger.fatal("Query activity failed[reason=%s]" % err)

        res = activity_pb2.QueryActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def accept_activity_reward(self, user_id, request):
        """领取奖励
        """
        timer = Timer(user_id)

        req = activity_pb2.AcceptActivityRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._accept_activity_reward, user_id, req, timer)
        return defer


    def _accept_activity_reward(self, basic_data, user_id, req, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_accept_activity_reward, basic_data, req, timer)
        defer.addErrback(self._accept_activity_reward_failed, req, timer)
        return defer


    def _calc_accept_activity_reward(self, data, basic_data, req, timer):
        """领取奖励
        """
        if not activity_business.accept_reward(basic_data, data, req.id, req.step_id, timer.now):
            raise Exception("Accept activity reward failed")

        #check
        for itemInfo in req.items:
            compare.check_item(data, itemInfo)
        for heroInfo in req.heroes:
            compare.check_hero(data, heroInfo)

        res = self._pack_accept_activity_reward_response(data, req, timer)
        basic_activity = basic_data.activity_list.get(req.id)
        if basic_activity.type_id == 1:
            #首充活动奖励发广播
            try:
                self._firstpay_broadcast(data)
            except:
                logger.warning("Send firstpay broadcast failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._accept_activity_reward_succeed, req, res, timer)
        return defer

    def _firstpay_broadcast(self, data):
        """首充活动奖励发广播"""
        user_name = data.user.get(True).name

        broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_firstpay'].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(user_name), 1)

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)

    def _pack_accept_activity_reward_response(self, data, req, timer):
        """封装领取活动奖励的响应
        """
        res = activity_pb2.AcceptActivityRewardRes()
        res.status = 0
        for hero_info in req.heroes:
            hero = hero_business.get_hero_by_id(data, hero_info.basic_id, True)
            pack.pack_hero_info(hero, res.heroes.add(), timer.now)

        resource = data.resource.get(True)
        pack.pack_resource_info(resource, res.resource)
        return res


    def _accept_activity_reward_succeed(self, data, req, res, timer):
        """领取活动奖励成功
        """
        response = res.SerializeToString()
        log = log_formater.output(data, "Accept activity reward succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _accept_activity_reward_failed(self, err, req, timer):
        """领取活动奖励失败
        """
        logger.fatal("Accept activity reward failed[reason=%s]" % err)

        res = activity_pb2.AcceptActivityRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept activity reward failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def operate_activity(self, user_id, request):
        """参与活动
        """
        timer = Timer(user_id)

        req = activity_pb2.OperateActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._operate_activity, user_id, req, timer)
        return defer


    def _operate_activity(self, basic_data, user_id, req, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_operate_activity, basic_data, req, timer)
        defer.addCallback(self._operate_activity_succeed, basic_data, req, timer)
        defer.addErrback(self._operate_activity_failed, req, timer)
        return defer


    def _calc_operate_activity(self, data, basic_data, req, timer):
        """参与活动
        """
        activity_basic_id = req.id
        activity_step_id = 0
        if req.HasField("step_id"):
            activity_step_id = req.step_id
        op_type = 0
        if req.HasField("op_type"):
            op_type = req.op_type
        op_input = ""
        if req.HasField("op_input"):
            op_input = req.op_input

        if not activity_business.operate_activity(basic_data, data,
                activity_basic_id, activity_step_id, op_type, op_input, timer.now):
            #XXX:有待改进，status不应该为-1
            raise Exception("Operate activity failed")

        return DataBase().commit(data)


    def _operate_activity_succeed(self, data, basic_data, req, timer):
        """参与活动成功
        """
        res = activity_pb2.OperateActivityRes()
        res.status = 0

        activity_id = ActivityInfo.generate_id(data.id, req.id)
        activity = data.activity_list.get(activity_id, True)
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        if basic_activity is None:
            logger.fatal("basic activity not exsit[id=%d]" % activity.basic_id)
            raise Exception("Operate activity failed")

        basic_steps = activity_business.get_basic_activity_steps(basic_data, basic_activity)
        pack.pack_activity_info(activity, basic_activity, basic_steps, res.activity, timer.now, basic_data, data, [])

        pack.pack_resource_info(data.resource.get(True), res.resource)

        response = res.SerializeToString()
        log = log_formater.output(data, "Operate activity succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _operate_activity_failed(self, err, req, timer):
        """参与活动失败
        """
        logger.fatal("Buy activity funds failed[reason=%s]" % err)

        res = activity_pb2.OperateActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Operate activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_activity(self, user_id, request):
        """
        向指定用户添加活动
        内部接口
        """
        timer = Timer(user_id)

        req = internal_pb2.AddActivityReq()
        req.ParseFromString(request)

        defer = self._forward_activity_invitation(req.target_user_id, req.activities, timer)
        defer.addCallback(self._add_activity_succeed, req, timer)
        defer.addErrback(self._add_activity_failed, req, timer)
        return defer


    def _forward_activity_invitation(self, user_id, activities, timer):
        """邀请指定用户参加活动
        """
        req = internal_pb2.ActivityInvitationReq()
        req.activities.extend(activities)
        request = req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_activity_invitation",
                user_id, request)
        defer.addCallback(self._check_forward_activity)
        return defer


    def _check_forward_activity(self, response):
        res = internal_pb2.ActivityInvitationRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward activity invitation failed")


    def _add_activity_succeed(self, data, req, timer):
        res = internal_pb2.AddActivityRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Add activity succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_activity_failed(self, err, req, timer):
        logger.fatal("Use activity failed[reason=%s]" % err)
        res = internal_pb2.AddActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_activity_invitation(self, user_id, request):
        """帐号接收活动邀请
        """
        timer = Timer(user_id)

        req = internal_pb2.ActivityInvitationReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._receive_activity_invitation, user_id, req, timer)
        return defer


    def _receive_activity_invitation(self, basic_data, user_id, req, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_activity, basic_data, req, timer)
        defer.addCallback(self._receive_activity_succeed, req, timer)
        defer.addErrback(self._receive_activity_failed, req, timer)
        return defer


    def _calc_receive_activity(self, data, basic_data, req, timer):
        """接收活动邀请
        """
        for activity_basic_id in req.activities:
            basic_activity = basic_data.activity_list.get(activity_basic_id)
            if basic_activity is None:
                logger.fatal("basic activity not exsit[id=%d]" % activity_basic_id)
                continue

            basic_steps = activity_business.get_basic_activity_steps(basic_data, basic_activity)
            if not activity_business.add_activity(data, activity_basic_id, 
                    basic_activity, basic_steps):
                raise Exception("Receive activity invitation failed")

        return DataBase().commit(data)


    def _receive_activity_succeed(self, data, req, timer):
        res = internal_pb2.ActivityInvitationRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive activity succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _receive_activity_failed(self, err, req, timer):
        logger.fatal("Receive activity failed[reason=%s]" % err)
        res = internal_pb2.ActivityInvitationRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def award_activity_hero(self, user_id, request):
        """
        向指定用户发送拍卖英雄活动的奖励
        内部接口
        """
        timer = Timer(user_id)

        req = activity_pb2.AwardActivityHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._award_activity_hero, user_id, req, timer)
        return defer


    def _award_activity_hero(self, basic_data, user_id, req, timer):
        """
        """
        defer = self._calc_award_activity_hero(basic_data, req, timer)
        defer.addCallback(self._award_activity_hero_succeed, req, timer)
        defer.addErrback(self._award_activity_hero_failed, req, timer)
        return defer


    def _calc_award_activity_hero(self, basic_data, req, timer):
        """向用户转发拍卖英雄活动的奖励邮件
        """
        basic_activity = basic_data.activity_list.get(req.activity_id)
        items = activity_business.get_activity_hero_award(basic_data, basic_activity.hero_basic_id, req.rank)

        forward_req = internal_pb2.ReceiveMailReq()
        forward_req.user_id = req.user_id
        forward_req.mail.basic_id = 101
        forward_req.mail.subject = data_loader.ServerDescKeyInfo_dict[
                "activity_hero_reward_subject"].value.encode("utf-8")
        content = data_loader.ServerDescKeyInfo_dict[
                "activity_hero_reward_content"].value.encode("utf-8")
        content = content.replace("@ranking", str(req.rank))
        forward_req.mail.content = content
        forward_req.mail.sender = data_loader.ServerDescKeyInfo_dict[
                "activity_hero_reward_sender"].value.encode("utf-8")
        for (item_basic_id, item_num) in items:
            info = forward_req.mail.reward_items.add()
            info.basic_id = item_basic_id
            info.num = item_num

        request = forward_req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_mail", req.user_id, request)
        defer.addCallback(self._check_award_activity_hero)

        return defer


    def _check_award_activity_hero(self, response):
        res = internal_pb2.ReceiveMailRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward award mail failed")


    def _award_activity_hero_succeed(self, data, req, timer):
        res = activity_pb2.AwardActivityHeroRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Award activity hero succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _award_activity_hero_failed(self, err, req, timer):
        logger.fatal("Award activity hero failed[reason=%s]" % err)
        res = activity_pb2.AwardActivityHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Award activity hero failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response




    def clear_activity_hero_scores(self, user_id, request):
        """
        向指定用户发送清空拍卖英雄活动的积分
        内部接口
        """
        timer = Timer(user_id)

        req = activity_pb2.ClearActivityHeroScoresReq()
        req.ParseFromString(request)

        defer = self._forward_clear_activity_hero_scores(req.user_id, timer)
        defer.addCallback(self._clear_activity_hero_scores_succeed, req, timer)
        defer.addErrback(self._clear_activity_hero_scores_failed, req, timer)
        return defer


    def _forward_clear_activity_hero_scores(self, user_id, timer):
        """向用户转发清空拍卖英雄活动积分的请求
        """
        req = activity_pb2.ReceiveClearActivityHeroScoresReq()
        req.user_id = user_id
        request = req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_clear_activity_hero_scores", user_id, request)
        defer.addCallback(self._check_forward_clear_activity_hero_scores)
        return defer


    def _check_forward_clear_activity_hero_scores(self, response):
        res = activity_pb2.ReceiveClearActivityHeroScoresRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward clear activity hero scores failed")


    def _clear_activity_hero_scores_succeed(self, data, req, timer):
        res = activity_pb2.ClearActivityHeroScoresRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Clear activity hero scores succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _clear_activity_hero_scores_failed(self, err, req, timer):
        logger.fatal("Clear activity hero scores failed[reason=%s]" % err)
        res = activity_pb2.ClearActivityHeroScoresRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Clear activity hero scores failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_clear_activity_hero_scores(self, user_id, request):
        """帐号接收清空拍卖英雄活动积分的请求
        """
        timer = Timer(user_id)

        req = activity_pb2.ReceiveClearActivityHeroScoresReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_clear_activity_hero_scores, req, timer)
        defer.addCallback(self._receive_clear_activity_hero_scores_succeed, req, timer)
        defer.addErrback(self._receive_clear_activity_hero_scores_failed, req, timer)
        return defer


    def _calc_receive_clear_activity_hero_scores(self, data, req, timer):
        """更新演武场数据
        """
        draw = data.draw.get()
        draw.clear_activity_scores()

        defer = DataBase().commit(data)
        return defer


    def _receive_clear_activity_hero_scores_succeed(self, data, req, timer):
        res = activity_pb2.ReceiveClearActivityHeroScoresRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Receive clear activity hero scores succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _receive_clear_activity_hero_scores_failed(self, err, req, timer):
        logger.fatal("Receive clear activity hero scores failed[reason=%s]" % err)
        res = activity_pb2.ReceiveClearActivityHeroScoresRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive clear activity hero scores failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def fortune_cat(self, user_id, request):
        """招财猫
        """
        timer = Timer(user_id)
        req = activity_pb2.GoldCutReq()
        req.ParseFromString(request)
        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._accept_cat_reward, user_id, req, timer)
        return defer


    def _accept_cat_reward(self, basic_data, user_id, req, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_accept_cat_reward, basic_data, req, timer)
        defer.addErrback(self._accept_cat_reward_failed, req, timer)
        return defer

    def _calc_accept_cat_reward(self, data, basic_data, req, timer):
        """领取奖励
        """
        cost_gold = 0
        min_gold = 0
        max_gold = 0
        resource = data.resource.get()
        user = data.user.get()

        (cost_gold, min_gold, max_gold) = activity_business.cat_reward(basic_data, data, req.id, req.step_id, timer.now)
        if not resource.cost_gold(cost_gold):
            return False

        log = log_formater.output_gold(data, -cost_gold, log_formater.FORTUNE_CAT,
           "fortune cat cost")
        logger.notice(log)
  
        gain_gold = random.randint(min_gold, max_gold)
        resource.gain_gold(gain_gold)
        resource.gain_total_cat_gold(gain_gold)

        log = log_formater.output_gold(data, gain_gold, log_formater.FORTUNE_CAT,
           "fortune cat gain")
        logger.notice(log)

        #请求common模块添加记录
        common_req = internal_pb2.InternalCatReq()
        common_req.user_id = data.id
        common_req.name = user.get_readable_name()
        common_req.gold = gain_gold
        common_request = common_req.SerializeToString()
        defer = GlobalObject().remote["common"].callRemote("fortune_cat", 1, common_request)

        defer.addCallback(self._accept_reward_result, data, req, timer, gain_gold, resource)                                                                                                       
        return defer 


    def _accept_reward_result(self, response, data, req, timer, gain_gold, resource):
        res = activity_pb2.GoldCutRes()
        res.status = 0
        res.getgolds = gain_gold
        pack.pack_resource_info(resource, res.resource)
        res.totalgolds = resource.total_gain_cat

        defer = DataBase().commit(data)
        defer.addCallback(self._accept_cat_reward_succeed, req, res, gain_gold, resource, timer)
        return defer


    def _accept_cat_reward_succeed(self, data, req, res, gain_gold, resource, timer):
        response = res.SerializeToString()

        logger.notice("fortune cat succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _accept_cat_reward_failed(self, err, req, timer):
        logger.fatal("Accept cat reward failed[reason=%s]" % err)
        
        res = activity_pb2.GoldCutRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("fortune cat failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response
