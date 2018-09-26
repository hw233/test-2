#coding:utf8
"""
Created on 2016-05-18
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城处理逻辑
"""

from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import legendcity_pb2
from proto import wineShop_pb2
from proto import unit_pb2
from proto import internal_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import log_formater
from app import pack
from app import compare
from app.business import legendcity as legendcity_business
from app.data.legendcity import LegendCityInfo
from app.data.item import ItemInfo
from app.user_matcher import UserMatcher
from app.legendcity_rival_matcher import LegendCityRivalMatcher
import base64


class LegendCityProcessor(object):

    def query(self, user_id, request):
        """查询史实城信息
        包括用户手动刷新
        """
        timer = Timer(user_id)

        req = legendcity_pb2.QueryLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        """查询史实城
        """
        user = data.user.get(True)
        if not user.allow_pvp:
            raise Exception("User pvp locked")

        #获取之前匹配的对手信息
        city_id = LegendCityInfo.generate_id(data.id, req.city_id)
        legendcity = data.legendcity_list.get(city_id)

        #用户花费元宝重新匹配对手
        if req.HasField("rematch_position_level"):
            cost_gold = legendcity.calc_rematch_cost(req.rematch_position_level)
            if cost_gold != req.gold:
                raise Exception("Unmatched gold cost[expect=%d][cost=%d]" %
                        (cost_gold, req.gold))
            resource = data.resource.get()
            original_gold = resource.gold
            if not resource.cost_gold(cost_gold):
                raise Exception("Cost gold failed")
            log = log_formater.output_gold(data, -cost_gold, log_formater.LEGENDCITY_REMATCH,
                "Rematch player by gold", before_gold = original_gold)
            logger.notice(log)

        unit_req = unit_pb2.UnitQueryLegendCityReq()
        unit_req.user_id = data.id
        unit_req.rematch_position_level = req.rematch_position_level
        for (id, is_robot, position) in legendcity.get_rivals_info():
            unit_req.rivals_id.append(id)
            unit_req.rivals_position_level.append(position)

        #请求 Unit 模块，查询当前的史实城情况
        defer = GlobalObject().remote['unit'].callRemote(
                "query_city_info", legendcity.city_id, unit_req.SerializeToString())
        defer.addCallback(self._update_query_info, data, req, timer)
        return defer


    def _update_query_info(self, unit_response, data, req, timer):
        """更新史实城信息
        """
        unit_res = unit_pb2.UnitQueryLegendCityRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit res error[res=%s]" % unit_res)

        #更新匹配的对手
        rivals_info = []
        for index in range(0, len(unit_res.rivals_id)):
            rivals_info.append((
                    unit_res.rivals_id[index],
                    unit_res.rivals_is_robot[index],
                    unit_res.rivals_position_level[index]))

        city_id = LegendCityInfo.generate_id(data.id, req.city_id)
        legendcity = data.legendcity_list.get(city_id)
        legendcity.change_rivals(unit_res.invalid_rivals_id, rivals_info, timer.now)

        #查询对手当前情况
        matcher = UserMatcher()
        for (id, is_robot, position) in legendcity.get_rivals_info():
            matcher.add_condition(id, is_robot)

        defer = matcher.match()
        defer.addCallback(self._pack_query_response, data, legendcity, unit_res, req, timer)
        return defer


    def _pack_query_response(self, users, data, legendcity, unit_res, req, timer):
        """打包查询响应
        """
        res = legendcity_pb2.QueryLegendCityRes()
        res.status = 0
        res.ret = unit_res.ret

        res.city.city_id = legendcity.city_id
        res.city.slogan = unit_res.slogan
        res.city.update_slogan_free = unit_res.update_slogan_free
        res.city.tax = unit_res.tax
        res.city.update_tax_free = unit_res.update_tax_free
        res.city.income_by_tax = unit_res.income_by_tax

        #计算每个官职需要匹配的对手数目
        need_rival_count = {}
        for key in data_loader.LegendCityPositionBasicInfo_dict:
            info = data_loader.LegendCityPositionBasicInfo_dict[key]
            if info.cityId == legendcity.city_id:
                need_rival_count[info.level] = info.displayNum
        if unit_res.position_level != 0:
            #玩家自己的官职，可以少匹配一人，因为会显示玩家自己
            need_rival_count[unit_res.position_level] -= 1

        for (user_id, is_robot, position_level) in legendcity.get_rivals_info():
            if need_rival_count[position_level] <= 0:
                continue
            need_rival_count[position_level] -= 1
            position = res.city.positions.add()
            position.city_id = legendcity.city_id
            position.level = position_level
            pack.pack_monarch_info(users[user_id], position.user)

        res.city.user.position_level = unit_res.position_level
        res.city.user.reputation = unit_res.reputation
        res.city.user.attack_count_left = legendcity.get_attack_count_left()
        res.city.user.attack_reset_num = legendcity.reset_attack_num

        for (buff_id, left_time) in legendcity.get_buffs(timer.now):
            buff = res.city.user.buffs.add()
            buff.city_buff_id = buff_id
            buff.left_time = left_time

        for record in data.legendcity_record_list.get_all(True):
            if record.city_id == req.city_id:
                pack.pack_legendcity_record(record, res.city.records.add())

        pack.pack_resource_info(data.resource.get(True), res.resource)
        
        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Query legend city succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query legend city failed[reason=%s]" % err)
        res = legendcity_pb2.QueryLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query legend city failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update(self, user_id, request):
        """更新史实城信息
        只有太守有权利操作
        """
        timer = Timer(user_id)
        req = legendcity_pb2.UpdateLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer


    def _calc_update(self, data, req, timer):
        """更新史实城信息
        请求 unit 模块
        """
        city_id = LegendCityInfo.generate_id(data.id, req.city_id)
        legendcity = data.legendcity_list.get(city_id)

        unit_req = unit_pb2.UnitUpdateLegendCityReq()
        unit_req.user_id = data.id
        if req.HasField("slogan"):
            unit_req.slogan = req.slogan
        if req.HasField("tax"):
            unit_req.tax = req.tax
        if req.HasField("gold"):
            #消耗元宝
            unit_req.gold = req.gold
            resource = data.resource.get()
            original_gold = resource.gold
            if not resource.cost_gold(req.gold):
                raise Exception("Cost gold failed")
            log = log_formater.output_gold(data, -req.gold, log_formater.LEGENDCITY_UPDATE,
                "Updata legendcity", before_gold = original_gold)
            logger.notice(log)

        defer = GlobalObject().remote['unit'].callRemote(
                "update_city_info", legendcity.city_id, unit_req.SerializeToString())
        defer.addCallback(self._check_update, data, req, timer)
        defer.addCallback(self._update_succeed, data, req, timer)
        return defer


    def _check_update(self, unit_response, data, req, timer):
        unit_res = unit_pb2.UnitUpdateLegendCityRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit res error[res=%s]" % unit_res)

        #发广播
        try:
            defer = self._update_broadcast(data, req, timer)
        except:
            defer = Deferred()
            defer.callback(False)
        defer.addCallback(self._check_update_broadcast, data, unit_res, req, timer)
        return defer

    def _check_update_broadcast(self, result, data, unit_res, req, timer):
        if not result:
            logger.warning("Update legend city broadcast failed[user_id=%d]" % data.id)

        defer = DataBase().commit(data)
        defer.addCallback(self._pack_update_response, unit_res, req, timer)
        return defer

    def _update_broadcast(self, data, req, timer):
        user_name = data.user.get(True).name
        city_name = data_loader.LegendCityBasicInfo_dict[req.city_id].nameKey.encode("utf-8")
        if req.HasField("slogan"):
            broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_update_slogan'].value))
            value = str(req.slogan)
        elif req.HasField("tax"):
            broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_update_tex'].value))
            value = str(req.tax)
        else:
            defer = Deferred()
            defer.callback(False)
            return defer
        
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", "@%s@" % city_name, 1)
        content = content.replace("#str#", base64.b64decode(user_name), 1)
        content = content.replace("#str#", value, 1)

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._update_broadcast_result)
        return defer

    def _update_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        return res.status == 0

    def _pack_update_response(self, data, unit_res, req, timer):
        res = legendcity_pb2.UpdateLegendCityRes()
        res.status = 0
        res.ret = unit_res.ret
        pack.pack_resource_info(data.resource.get(True), res.resource)
        return res


    def _update_succeed(self, res, data, req, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Update legend city succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_failed(self, err, req, timer):
        logger.fatal("Update legend city failed[reason=%s]" % err)
        res = legendcity_pb2.UpdateLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update legend city failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def reset_attack_info(self, user_id, request):
        """重置攻击次数
        """
        timer = Timer(user_id)
        req = legendcity_pb2.ResetLegendCityAttackInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reset_attack, req, timer)
        defer.addErrback(self._reset_attack_failed, req, timer)
        return defer


    def _calc_reset_attack(self, data, req, timer):
        """花费元宝，重置攻击次数
        """
        city_id = LegendCityInfo.generate_id(data.id, req.city_id)
        legendcity = data.legendcity_list.get(city_id)

        if not legendcity.reset_attack_count(req.gold):
            raise Exception("Reset attack count failed")

        resource = data.resource.get()
        original_gold = resource.gold
        if not resource.cost_gold(req.gold):
            raise Exception("Cost gold failed")
        log = log_formater.output_gold(data, -req.gold, log_formater.LEGENDCITY_RESET,
                "Reset attack in legendcity", before_gold = original_gold)
        logger.notice(log)
        defer = DataBase().commit(data)
        defer.addCallback(self._reset_attack_succeed, req, timer)
        return defer


    def _reset_attack_succeed(self, data, req, timer):
        res = legendcity_pb2.ResetLegendCityAttackInfoRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Reset legend city attack info succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _reset_attack_failed(self, err, req, timer):
        logger.fatal("Reset legend city attack info failed[reason=%s]" % err)
        res = legendcity_pb2.ResetLegendCityAttackInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reset legend city attack info failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def buy_buff(self, user_id, request):
        """购买史实城 buff
        """
        timer = Timer(user_id)
        req = legendcity_pb2.BuyLegendCityBuffReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_buy_buff, req, timer)
        defer.addErrback(self._buy_buff_failed, req, timer)
        return defer


    def _calc_buy_buff(self, data, req, timer):
        city_id = LegendCityInfo.generate_id(data.id, req.city_id)
        legendcity = data.legendcity_list.get(city_id)

        if req.HasField("item"):
            #消耗物品获得 buff
            item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
            item = data.item_list.get(item_id)
            if not item.use_legendcity_buff_item():
                raise Exception("Use legendcity buff item failed")

            #检查 buff 和 item 是否匹配
            if not legendcity.check_buff_available(req.city_buff_id, req.item.basic_id):
                raise Exception("Check buff available failed")
        else:
            #消耗元宝获得 buff
            need = legendcity.get_buff_gold_cost(req.city_buff_id)
            if need != req.gold:
                raise Exception("Unmatch gold cost[need=%d][cost=%d]" % (need, req.gold))
            resource = data.resource.get()
            original_gold = resource.gold
            if not resource.cost_gold(need):
                raise Exception("Cost gold failed")
            log = log_formater.output_gold(data, -need, log_formater.LEGENDCITY_BUY_BUFF,
                "Buy buff by gold", before_gold = original_gold)
            logger.notice(log)
	    

        if not legendcity.add_buff(req.city_buff_id, timer.now):
            raise Exception("Add legendcity buff failed")

        if req.HasField("item"):
            compare.check_item(data, req.item)

        defer = DataBase().commit(data)
        defer.addCallback(self._buy_buff_succeed, req, timer)
        return defer


    def _buy_buff_succeed(self, data, req, timer):
        res = legendcity_pb2.BuyLegendCityBuffRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Buy legend city buff succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _buy_buff_failed(self, err, req, timer):
        logger.fatal("Buy legend city buff failed[reason=%s]" % err)
        res = legendcity_pb2.BuyLegendCityBuffRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Buf legend city buff failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_rival(self, user_id, request):
        """查询对手信息
        """
        timer = Timer(user_id)
        req = legendcity_pb2.QueryLegendCityRivalInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query_rival, req, timer)
        defer.addErrback(self._query_rival_failed, req, timer)
        return defer


    def _calc_query_rival(self, data, req, timer):
        """请求 unit 模块，核实对手信息
        """
        city_id = LegendCityInfo.generate_id(data.id, req.rival.city_id)
        legendcity = data.legendcity_list.get(city_id)

        unit_req = unit_pb2.UnitCheckLegendCityReq()
        unit_req.user_id = data.id
        unit_req.rival_id = req.rival.user.user_id
        unit_req.rival_position_level = req.rival.level

        #查询官职信息
        defer = GlobalObject().remote['unit'].callRemote(
                "check", legendcity.city_id, unit_req.SerializeToString())
        defer.addCallback(self._query_rival_detail, data, req, timer)
        defer.addCallback(self._query_rival_succeed, data, req, timer)
        return defer


    def _query_rival_detail(self, unit_response, data, req, timer):
        """查询对手现在的详细情况
        """
        unit_res = unit_pb2.UnitCheckLegendCityRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit res error[res=%s]" % unit_res)

        #如果对手已经处于不合法的状态，返回原因
        if unit_res.ret != legendcity_pb2.OK:
            return self._pack_query_rival_invalid_response(unit_res)

        city_id = LegendCityInfo.generate_id(data.id, req.rival.city_id)
        legendcity = data.legendcity_list.get(city_id, True)
        (rival_id, is_robot, position_level) = legendcity.get_rival_info(req.rival.user.user_id)

        #查询对手的详情
        matcher = LegendCityRivalMatcher()
        defer = matcher.match(data,
                req.rival.city_id, rival_id, is_robot, position_level, timer.now)
        defer.addCallback(self._check_rival_detail, data, timer)
        return defer


    def _pack_query_rival_invalid_response(self, unit_res):
        assert unit_res.ret != legendcity_pb2.OK

        res = legendcity_pb2.QueryLegendCityRivalInfoRes()
        res.status = 0
        res.ret = unit_res.ret
        if unit_res.HasField("unlock_time"):
            res.unlock_time = unit_res.unlock_time
        return res


    def _check_rival_detail(self, matcher, data, timer):
        defer = DataBase().commit(data)
        defer.addCallback(self._pack_query_rival_response, matcher, timer)
        return defer


    def _pack_query_rival_response(self, data, matcher, timer):
        res = legendcity_pb2.QueryLegendCityRivalInfoRes()
        res.status = 0
        res.ret = legendcity_pb2.OK
        pack.pack_rival_info(matcher.player, res.rival)
        return res


    def _query_rival_succeed(self, res, data, req, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Query legend city rival info succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_rival_failed(self, err, req, timer):
        logger.fatal("Query legend city rival info failed[reason=%s]" % err)
        res = legendcity_pb2.QueryLegendCityRivalInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query legend city rival info failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_reputation(self, user_id, request):
        """添加声望，内部接口
        """
        timer = Timer(user_id)
        req = internal_pb2.AddReputationReq()
        req.ParseFromString(request)

        unit_req = unit_pb2.UnitAddReputationReq()
        unit_req.user_id = user_id
        unit_req.reputation = req.reputation

        #请求 Unit 模块
        defer = GlobalObject().remote['unit'].callRemote(
                "add_reputation", req.city_id, unit_req.SerializeToString())
        defer.addCallback(self._add_reputation_succeed, req, timer)
        defer.addErrback(self._add_reputation_failed, req, timer)
        return defer


    def _add_reputation_succeed(self, unit_response, req, timer):
        unit_res = unit_pb2.UnitAddReputationRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit res error[res=%s]" % unit_res)

        res = internal_pb2.AddReputationRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Add reputation succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _add_reputation_failed(self, err, req, timer):
        logger.fatal("Add reputation failed[reason=%s]" % err)
        res = internal_pb2.AddReputationRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add reputation failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_legend_city(self, user_id, request):
        """删除史实城（内部接口）
        """
        timer = Timer(user_id)
        req = internal_pb2.DeleteLegendCityReq()
        req.ParseFromString(request)

        defer = Deferred()
        for city_id in req.citys_id:
            defer.addCallback(self._calc_delete_legend_city, city_id, timer)
        defer.addCallback(self._delete_legend_city_succeed, req, timer)
        defer.addErrback(self._delete_legend_city_failed, req, timer)
        defer.callback(0)
        return defer


    def _calc_delete_legend_city(self, status, city_id, timer):
        assert status == 0

        unit_req = unit_pb2.UnitDeleteLegendCityReq()
        defer = GlobalObject().remote['unit'].callRemote(
                "delete_city", city_id, unit_req.SerializeToString())
        defer.addCallback(self._check_delete_legend_city, city_id, timer)
        return defer


    def _check_delete_legend_city(self, unit_response, city_id, timer):
        unit_res = unit_pb2.UnitDeleteLegendCityRes()
        unit_res.ParseFromString(unit_response)

        if unit_res.status != 0:
            raise Exception("Unit res failed[city_id=%d][res=%s]" % (city_id, unit_res))

        return unit_res.status


    def _delete_legend_city_succeed(self, status, req, timer):
        res = internal_pb2.DeleteLegendCityRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Delete legend city succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _delete_legend_city_failed(self, err, req, timer):
        logger.fatal("Delete legend city failed[reason=%s]" % err)
        res = internal_pb2.DeleteLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete legend city failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def award_legend_city(self, user_id, request):
        """发放史实城奖励（内部接口）
        """
        timer = Timer(user_id)
        req = internal_pb2.AwardLegendCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_award_legend_city, req, timer)
        defer.addCallback(self._award_legend_city_succeed, req, timer)
        defer.addErrback(self._award_legend_city_failed, req, timer)
        return defer


    def _calc_award_legend_city(self, data, req, timer):
        items = legendcity_business.get_legendcity_award(req.city_id, req.position_level)

        forward_req = internal_pb2.ReceiveMailReq()
        forward_req.user_id = req.user_id
        forward_req.mail.basic_id = 101
        forward_req.mail.subject = data_loader.ServerDescKeyInfo_dict[
                "award_legendcity_subject"].value.encode("utf-8")
        forward_req.mail.content = data_loader.ServerDescKeyInfo_dict[
                "award_legendcity_content"].value.encode("utf-8")
        forward_req.mail.sender = data_loader.ServerDescKeyInfo_dict[
                "award_legendcity_sender"].value.encode("utf-8")
        for (item_basic_id, item_num) in items:
            info = forward_req.mail.reward_items.add()
            info.basic_id = item_basic_id
            info.num = item_num

        request = forward_req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_mail", req.user_id, request)
        defer.addCallback(self._check_award_legend_city)
        return defer


    def _check_award_legend_city(self, response):
        res = internal_pb2.ReceiveMailRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward award mail failed")


    def _award_legend_city_succeed(self, status, req, timer):
        res = internal_pb2.AwardLegendCityRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Award legend city succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _award_legend_city_failed(self, err, req, timer):
        logger.fatal("Award legend city failed[reason=%s]" % err)
        res = internal_pb2.AwardLegendCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Award legend city failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def get_position_rank(self, user_id, request):
        """获取史实城官职榜（内部接口）
        """
        timer = Timer(user_id)
        req = internal_pb2.GetLegendCityPositionRankReq()
        req.ParseFromString(request)

        res = internal_pb2.GetLegendCityPositionRankRes()
        res.status = 0

        defer = Deferred()
        for city_id in data_loader.LegendCityBasicInfo_dict:
            defer.addCallback(self._calc_get_position_rank, city_id, res, timer)
        defer.addCallback(self._get_position_rank_succeed, req, res, timer)
        defer.addErrback(self._get_position_rank_failed, req, timer)
        defer.callback(True)
        return defer


    def _calc_get_position_rank(self, state, city_id, res, timer):
        assert state == True

        unit_req = unit_pb2.UnitGetPositionRankReq()
        defer = GlobalObject().remote['unit'].callRemote(
                "get_position_rank", city_id, unit_req.SerializeToString())
        defer.addCallback(self._check_position_rank, city_id, res, timer)
        return defer


    def _check_position_rank(self, unit_response, city_id, res, timer):
        unit_res = unit_pb2.UnitGetPositionRankRes()
        unit_res.ParseFromString(unit_response)

        if unit_res.status != 0:
            raise Exception("Unit res failed[city_id=%d][res=%s]" % (city_id, unit_res))

        for index in range(0, len(unit_res.positions_level)):
            position_level = unit_res.positions_level[index]
            user_id = unit_res.users_id[index]
            is_robot = unit_res.users_is_robot[index]

            if not is_robot:
                position = res.positions.add()
                position.city_id = city_id
                position.level = position_level
                position.user.user_id = user_id

        return True


    def _get_position_rank_succeed(self, state, req, res, timer):
        assert state == True
        response = res.SerializeToString()
        logger.notice("Get legend city position rank succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _get_position_rank_failed(self, err, req, timer):
        logger.fatal("Get legend city position rank failed[reason=%s]" % err)
        res = internal_pb2.GetLegendCityPositionRankRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Get legend city position rank failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


