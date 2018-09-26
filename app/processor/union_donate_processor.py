#coding:utf8
"""
Created on 2016-10-27
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟捐献处理流程
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from proto import union_donate_pb2
from proto import union_pb2
from proto import internal_union_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app.data.donate_box import UserDonateBox
from app.data.union import UserUnionInfo
from app.business import union_donate
import base64
import pdb


class UnionDonateProcessor(object):

    def query(self, user_id, request):
        """查询联盟捐献信息"""
        timer = Timer(user_id)

        req = union_donate_pb2.QueryUnionDonateInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_donate_pb2.QueryUnionDonateInfoRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._query_succeed, req, res, timer)
            return defer
        
        union_req = internal_union_pb2.InternalQueryUnionDonateReq()
        union_req.user_id = data.id
        defer = GlobalObject().remote['gunion'].callRemote(
            "query_donate", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_query_result, data, req, timer)
        return defer

    def _calc_query_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionDonateRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union donate res error")
        if union_res.ret != union_pb2.UNION_OK:
            res = union_donate_pb2.QueryUnionDonateInfoRes()
            res.status = 0
            res.ret = union_res.ret

            defer = DataBase().commit(data)
            defer.addCallback(self._query_succeed, req, res, timer)
            return defer
        
        union_donate.syn_donate_boxes(data, union_res.boxes_info)

        for box_info in union_res.boxes_info:
            if box_info.current_state == UserDonateBox.DONATING:
                donate_level = union_donate.query_donate_level(data, box_info.treasurebox_id)
                for is_donate in donate_level:
                    box_info.donate_types.append(is_donate)
        
        res = union_donate_pb2.QueryUnionDonateInfoRes()
        res.status = 0
        res.ret = union_res.ret
    
        for box_info in union_res.boxes_info:
            if box_info.current_state != UserDonateBox.NULL and \
                not union_donate.is_donate_box_rewarded(data, box_info.treasurebox_id):
                res.boxes_info.add().CopyFrom(box_info)


        res.info.coldtime = union_donate.get_true_cold_time(data, timer)
        #defer = union_donate.trun_donate_records_to_strings(union_res.donate_records)
        strings = union_donate.trun_donate_records_to_strings(union_res.donate_records)
        '''
        defer.addCallback(self._calc_query_result_records, data, req, res, timer)
        return defer

    def _calc_query_result_records(self, strings, data, req, res, timer):
        '''
        for string in strings:
            res.info.donate_records.add().CopyFrom(string)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer        

    def _query_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Query union donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Query union donate succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _query_failed(self, err, req, timer):
        logger.fatal("Query union donate failed[reason=%s]" % err)
        res = union_donate_pb2.QueryUnionDonateInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def initiate(self, user_id, request):
        """发起捐献"""
        timer = Timer(user_id)

        req = union_donate_pb2.OpenDonateReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_initiate, req, timer)
        defer.addErrback(self._initiate_failed, req, timer)
        return defer
        
    def _calc_initiate(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_donate_pb2.OpenDonateRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._initiate_succeed, req, res, timer)
            return defer
        
        union_req = internal_union_pb2.InternalInitiateDonateReq()
        union_req.user_id = data.id
        union_req.box_id = req.treasurebox_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "initiate_donate", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_initiate_result, data, req, timer)
        return defer

    def _calc_initiate_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalInitiateDonateRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("initiate union donate error")
        if union_res.ret != union_pb2.UNION_OK:
            res = union_donate_pb2.OpenDonateRes()
            res.status = 0
            res.ret = union_res.ret

            defer = DataBase().commit(data)
            defer.addCallback(self._initiate_succeed, req, res, timer)
            return defer

        union_donate.syn_donate_box(data, union_res.box_info)
        
        if union_res.box_info.current_state == UserDonateBox.DONATING:
            donate_level = union_donate.query_donate_level(
                data, union_res.box_info.treasurebox_id)
            for is_donate in donate_level:
                union_res.box_info.donate_types.append(is_donate)
        
        res = union_donate_pb2.OpenDonateRes()
        res.status = 0
        res.ret = union_res.ret
        res.box_info.CopyFrom(union_res.box_info)

        defer = DataBase().commit(data)
        defer.addCallback(self._initiate_succeed, req, res, timer)
        return defer

    def _initiate_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Initiate donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Initiate donate succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response
        
    def _initiate_failed(self, err, req, timer):
        logger.fatal("Initiate donate failed[reason=%s]" % err)
        res = union_donate_pb2.OpenDonateRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Initiate donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def start(self, user_id, request):
        """进行捐献"""
        timer = Timer(user_id)

        req = union_donate_pb2.StartDonateReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start, req, timer)
        defer.addErrback(self._start_failed, req, timer)
        return defer

    def _calc_start(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_donate_pb2.StartDonateRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalQueryUnionDonateReq()
        union_req.user_id = data.id
        defer = GlobalObject().remote['gunion'].callRemote(
            "query_donate", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_start_syn, data, req, timer)
        return defer
    
    def _calc_start_syn(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionDonateRes()
        union_res.ParseFromString(union_response)
        
        if union_res.status != 0:
            raise Exception("Query union donate res error")
        if union_res.ret != union_pb2.UNION_OK:
            res = union_donate_pb2.StartDonateRes()
            res.status = 0
            res.ret = union_res.ret

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        union_donate.syn_donate_boxes(data, union_res.boxes_info)

        if not union_donate.is_donate_box_valid(data, req.treasurebox_id):
            res = union_donate_pb2.StartDonateRes()
            res.status = 0
            res.ret = union_pb2.UNION_DONATE_BOX_INVALID

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        if not union_donate.is_able_start_donate(
            data, req.treasurebox_id, req.donate_type, timer):
            res = union_donate_pb2.StartDonateRes()
            res.status = 0
            res.ret = union_pb2.UNION_DONATE_NO_CONDITION

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer

        user = data.user.get(True)
        union_req = internal_union_pb2.InternalStartUnionDonateReq()
        union_req.user_id = data.id
        union_req.user_name = user.name
        union_req.box_id = req.treasurebox_id
        union_req.donate_type = req.donate_type
        if req.donate_type == UserDonateBox.HIGH_DONATE:
            union_req.gold = req.gold
        else:
            union_req.money = req.money
        
        defer = GlobalObject().remote['gunion'].callRemote(
            "start_donate", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_start_result, data, req, timer)
        return defer

    def _calc_start_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalStartUnionDonateRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Start Donate Failed")
        if union_res.ret != union_pb2.UNION_OK:
            res = union_donate_pb2.StartDonateRes()
            res.status = 0
            res.ret = union_res.ret

            defer = DataBase().commit(data)
            defer.addCallback(self._start_succeed, req, res, timer)
            return defer
        
        union_donate.syn_donate_box(data, union_res.box_info)
        union_donate.start_donate(
            data, union_res.box_info.treasurebox_id, union_res.honor, req.donate_type, timer)

        if union_res.box_info.current_state == UserDonateBox.DONATING:
            donate_level = union_donate.query_donate_level(data, union_res.box_info.treasurebox_id)
            for is_donate in donate_level:
                union_res.box_info.donate_types.append(is_donate)
        
        trainer = data.trainer.get()
        trainer.add_daily_start_donate(1)

        res = union_donate_pb2.StartDonateRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK
        res.box_info.CopyFrom(union_res.box_info)
        res.resource.CopyFrom(union_donate.pack_resources(data, timer))
        res.info.coldtime = union_donate.get_true_cold_time(data, timer)

        strings = union_donate.trun_donate_records_to_strings(union_res.donate_records)
        for string in strings:
            res.info.donate_records.add().CopyFrom(string)

        #发广播
        try:
            defer = self._start_broadcast(data, req, timer)
        except:
            defer = Deferred()
            defer.callback(False)
        defer.addCallback(self._calc_start_result_broadcast, data, req, res, timer)
        return defer
    
    def _calc_start_result_broadcast(self, result, data, req, res, timer):
        if not result:
            logger.warning("Start donate send broadcast failed[user_id=%d]" % data.id)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_succeed, req, res, timer)
        return defer

    def _start_broadcast(self, data, req, timer):
        user_name = data.user.get(True).name
        box_name = data_loader.UnionDonateTreasureBoxBasicInfo_dict[req.treasurebox_id].nameKey.encode("utf-8")

        broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_start_uniondonate'].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(user_name), 1)
        content = content.replace("#str#", "@%s@" % box_name, 1)

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._start_broadcast_result)
        return defer

    def _start_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        return res.status == 0

    def _start_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Start donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Start donate succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _start_failed(self, err, req, timer):
        logger.fatal("Start donate failed[reason=%s]" % err)
        res = union_donate_pb2.StartDonateRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def reward(self, user_id, request):
        """领取宝箱奖励"""
        timer = Timer(user_id)

        req = union_donate_pb2.GetBoxRewardReq()
        req.ParseFromString(request)
        
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reward, req, timer)
        defer.addErrback(self._reward_failed, req, timer)
        return defer

    def _calc_reward(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_donate_pb2.GetBoxRewardRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._reward_succeed, req, res, timer)
            return defer
        
        union_req = internal_union_pb2.InternalQueryUnionDonateReq()
        union_req.user_id = data.id
        defer = GlobalObject().remote['gunion'].callRemote(
            "query_donate", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_reward_syn, data, req, timer)
        return defer
    
    def _calc_reward_syn(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionDonateRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Query union donate res error")
        if union_res.ret != union_pb2.UNION_OK:
            res = union_donate_pb2.GetBoxRewardRes()
            res.status = 0
            res.ret = union_res.ret

            defer = DataBase().commit(data)
            defer.addCallback(self._reward_succeed, req, res, timer)
            return defer

        union_donate.syn_donate_boxes(data, union_res.boxes_info)

        if not union_donate.is_able_reward_donate_box(data, req.treasurebox_id):
            res = union_donate_pb2.GetBoxRewardRes()
            res.status = 0
            res.ret = union_pb2.UNION_DONATE_BOX_INVALID

            defer = DataBase().commit(data)
            defer.addCallback(self._reward_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalGetBoxRewardReq()
        union_req.user_id = data.id
        union_req.box_id = req.treasurebox_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "reward_donate", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_reward_result, data, req, timer)
        return defer

    def _calc_reward_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalGetBoxRewardRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Reward donate box failed")
        if union_res.ret != union_pb2.UNION_OK:
            res = union_donate_pb2.GetBoxRewardRes()
            res.status = 0
            res.ret = union_res.ret

            defer = DataBase().commit(data)
            defer.addCallback(self._reward_succeed, req, res, timer)
            return defer
        
        union_donate.reward_donate_box(data, union_res.reward, req.treasurebox_id, timer)

        res = union_donate_pb2.GetBoxRewardRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK
        for id in union_res.reward.item_id:
            res.reward.item_id.append(id)
        for num in union_res.reward.item_num:
            res.reward.item_num.append(num)
        res.reward.resource.CopyFrom(union_donate.pack_resources(data, timer))

        defer = DataBase().commit(data)
        defer.addCallback(self._reward_succeed, req, res, timer)
        return defer

    def _reward_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Reward donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Reward donate succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()        
        return response

    def _reward_failed(self, err, req, timer):
        logger.fatal("Reward donate failed[reason=%s]" % err)
        res = union_donate_pb2.GetBoxRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reward donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def refresh(self, user_id, request):
        """刷新宝箱"""
        timer = Timer(user_id)

        req = union_donate_pb2.RefreshBoxInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh, req, timer)
        defer.addErrback(self._refresh_failed, req, timer)
        return defer

    def _calc_refresh(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_donate_pb2.RefreshBoxInfoRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._refresh_succeed, req, res, timer)
            return defer

        union_req = internal_union_pb2.InternalRefreshBoxReq()
        union_req.user_id = data.id
        union_req.box_id = req.treasurebox_id

        defer = GlobalObject().remote['gunion'].callRemote(
            "refresh_donate", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_refresh_result, data, req, timer)
        return defer

    def _calc_refresh_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalRefreshBoxRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Refresh donate box failed")
        if union_res.ret != union_pb2.UNION_OK:
            res = union_donate_pb2.RefreshBoxInfoRes()
            res.status = 0
            res.ret = union_res.ret

            defer = DataBase().commit(data)
            defer.addCallback(self._refresh_succeed, req, res, timer)
            return defer

        union_donate.refresh_donate_box(data, req.treasurebox_id, union_res.box_info)

        res = union_donate_pb2.RefreshBoxInfoRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK
        res.box_info.CopyFrom(union_res.box_info)

        defer = DataBase().commit(data)
        defer.addCallback(self. _refresh_succeed, req, res, timer)
        return defer

    def _refresh_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Refresh donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Refresh donate succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _refresh_failed(self, err, req, timer):
        logger.fatal("Refresh donate failed[reason=%s]" % err)
        res = union_donate_pb2.RefreshBoxInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh donate failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def clear(self, user_id, request):
        """清空冷却时间"""
        timer = Timer(user_id)

        req = union_donate_pb2.ClearDonateColdTimeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_clear, req, timer)
        defer.addErrback(self._clear_failed, req, timer)
        return defer

    def _calc_clear(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_donate_pb2.ClearDonateColdTimeRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._clear_succeed, req, res, timer)
            return defer

        if not union_donate.is_able_clear_coldtime(data, req.gold, timer):
            res = union_donate_pb2.ClearDonateColdTimeRes()
            res.status = 0
            res.ret = union_pb2.UNION_DONATE_NO_CONDITION

            defer = DataBase().commit(data)
            defer.addCallback(self._clear_succeed, req, res, timer)
            return defer
            
        union_donate.clear_coldtime(data, req.gold, timer)

        res = union_donate_pb2.ClearDonateColdTimeRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK
        res.cold_time = union_donate.get_true_cold_time(data, timer)
        res.resource.CopyFrom(union_donate.pack_resources(data, timer))

        defer = DataBase().commit(data)
        defer.addCallback(self._clear_succeed, req, res, timer)
        return defer

    def _clear_succeed(self, data, req, res, timer):
        if res.ret != union_pb2.UNION_OK:
            logger.notice("Clear donate cold time failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Clear donate cold time succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response
        
    def _clear_failed(self, err, req, timer):
        logger.fatal("Clear donate cold time failed[reason=%s]" % err)
        res = union_donate_pb2.ClearDonateColdTimeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Clear donate cold time failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
