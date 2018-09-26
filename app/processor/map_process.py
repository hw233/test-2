#coding:utf8
"""
Created on 2015-10-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 世界地图处理逻辑
"""

from utils import logger
from utils.timer import Timer
from utils.ret import Ret
from proto import map_pb2
from proto import event_pb2
from proto import internal_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app import compare
from app import log_formater
from app.data.node import NodeInfo
from app.core.name import NameGenerator
from app.rival_matcher import RivalMatcher
from app.business import map as map_business
from app.business import war as war_business
from app.business import event as event_business
from app.business import arena as arena_business
from app.business import account as account_business


class MapProcessor(object):

    WAR_EVENT = "war"
    LUCKY_EVENT = "lucky"
    SPECIFIED_EVENT = "specified"


    def trigger_custom_war_event(self, user_id, request):
        """触发指定的战争事件
        """
        timer = Timer(user_id)

        req = internal_pb2.TriggerCustomEventReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_trigger_custom_event, self.WAR_EVENT, req, timer)
        defer.addErrback(self._trigger_custom_event_failed, self.WAR_EVENT, req, timer)
        return defer


    def trigger_custom_event(self, user_id, request):
        """触发指定的事件
        """
        timer = Timer(user_id)

        req = internal_pb2.TriggerCustomEventReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_trigger_custom_event, self.LUCKY_EVENT, req, timer)
        defer.addErrback(self._trigger_custom_event_failed, self.LUCKY_EVENT, req, timer)
        return defer


    def _calc_trigger_custom_event(self, data, type, req, timer):
        """触发事件
        Args:
            data
            type
            req
            timer
        """
        change_nodes = []
        #触发战争事件
        if type == self.WAR_EVENT:
            if not war_business.trigger_custom_war_event(
                    data, timer.now, req.node_basic_id,
                    req.exploit_type, req.exploit_level,
                    req.rival_type, req.rival_score_min, req.rival_score_max, change_nodes):
                raise Exception("Trigger custom war event failed")
        elif type == self.LUCKY_EVENT:
            if not event_business.trigger_custom_event(
                    data, timer.now, req.node_basic_id, req.event_type, change_nodes):
                raise Exception("Trigger custom event failed")

        #为新刷出的敌方节点匹配敌人
        #不合法的敌人：自己，以及已经在地图上出现过的 PVP 敌人
        invalid_rival = [data.id]
        for node in data.node_list.get_all(True):
            if node.is_rival_pvp() and node.is_enemy_complete():
                rival_id = node.id
                rival = data.rival_list.get(rival_id, True)
                invalid_rival.append(rival.rival_id)

        user = data.user.get(True)
        matcher = RivalMatcher(user.level, invalid_rival)

        for node in change_nodes:
            if node.is_lack_enemy_detail():
                matcher.add_condition(data, node)

        defer = matcher.match(user.country)
        defer.addCallback(self._pack_trigger_custom_event_response, data, type, req, timer)
        return defer


    def _pack_trigger_custom_event_response(self, matcher, data, type, req, timer):
        defer = DataBase().commit(data)
        res = internal_pb2.TriggerCustomEventRes()
        res.status = 0

        defer = DataBase().commit(data)
        defer.addCallback(self._trigger_custom_event_succeed, type, req, res, timer)
        return defer


    def _trigger_custom_event_succeed(self, data, type, req, res, timer):
        res = internal_pb2.TriggerCustomEventRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, ("Trigger custom %s event succeed" % type),
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _trigger_custom_event_failed(self, err, type, req, timer):
        logger.fatal("Trigger custom event failed[reason=%s]" % err)
        res = internal_pb2.TriggerCustomEventRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Trigger custom %s event failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (type, timer.id, req, res, timer.count_ms()))
        return response


    def trigger_war_event(self, user_id, request):
        """触发战争事件
        """
        timer = Timer(user_id)

        req = map_pb2.TriggerEventReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_trigger_event, self.WAR_EVENT, req, timer)
        defer.addErrback(self._trigger_event_failed, self.WAR_EVENT, req, timer)
        return defer


    def trigger_lucky_event(self, user_id, request):
        """触发随机事件
        """
        timer = Timer(user_id)

        req = map_pb2.TriggerEventReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_trigger_event, self.LUCKY_EVENT, req, timer)
        defer.addErrback(self._trigger_event_failed, self.LUCKY_EVENT, req, timer)
        return defer


    def trigger_specified_event(self, user_id, request):
        """触发指定事件
        """
        timer = Timer(user_id)

        req = map_pb2.TriggerEventReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_trigger_event, self.SPECIFIED_EVENT, req, timer)
        defer.addErrback(self._trigger_event_failed, self.SPECIFIED_EVENT, req, timer)
        return defer


    def _calc_trigger_event(self, data, type, req, timer):
        """触发事件
        Args:
            data
            type
            req
            timer
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        change_nodes = []
        new_items = []
        new_mails = []

        #触发战争事件
        if type == self.WAR_EVENT:
            if not war_business.trigger_war_event(
                    data, timer.now, change_nodes, new_items, new_mails):
                raise Exception("Trigger war event failed")

        elif type == self.SPECIFIED_EVENT:
            if not req.HasField("type"):
                raise Exception("Trigger specified event failed, no type")

            if not event_business.trigger_specified_event(
                    data, req.type, timer.now, change_nodes):
                raise Exception("Trigger specified event failed")
            #compare.check_user(data, req.monarch, with_level = True)
            #记录次数
            trainer = data.trainer.get()
            trainer.add_daily_event_num(req.type, 1)

        elif type == self.LUCKY_EVENT:
            if not event_business.trigger_lucky_event(
                    data, timer.now, change_nodes):
                raise Exception("Trigger lucky event failed")

        #为新刷出的敌方节点匹配敌人
        #不合法的敌人：自己，以及已经在地图上出现过的 PVP 敌人
        invalid_rival = [data.id]
        for node in data.node_list.get_all(True):
            if node.is_rival_pvp() and node.is_enemy_complete():
                rival_id = node.id
                rival = data.rival_list.get(rival_id, True)
                invalid_rival.append(rival.rival_id)

        user = data.user.get(True)
        matcher = RivalMatcher(user.level, invalid_rival)

        energy = data.energy.get()
        if (req.type == NodeInfo.EVENT_TYPE_SCOUT or req.type == NodeInfo.EVENT_TYPE_JUNGLE) and energy.total_trigger_scout_num == 1:
            #第一次侦察事件刷出的敌人
            node_enemy_scores = [100, 101, 102]  #硬编码，初始三个node上固定敌人
            energy.total_trigger_scout_num += 1
            i = 0
            for node in data.node_list.get_all():
                if node.is_lack_enemy_detail():
                    node.rival_score_min = node_enemy_scores[i]
                    node.rival_score_max = node_enemy_scores[i]
                    i = i + 1
                    matcher.add_condition(data, node)
            defer = matcher.match(user.country, only_pve = True)

            pattern = 1
            #为初次刷新的敌人添加 debuff 效果，为了让玩家初次攻击可以轻易取胜
            for node in data.node_list.get_all():
                if node.is_enemy_complete():
                    rival_id = node.rival_id
                    rival = data.rival_list.get(rival_id)
                    buff_id = data_loader.InitUserBasicInfo_dict[pattern].enemyBuffId
                    rival.set_buff(buff_id)

        else:
            for node in change_nodes:
                if node.is_lack_enemy_detail():
                    matcher.add_condition(data, node)
            defer = matcher.match(user.country)

        defer.addCallback(self._pack_event_response,
                data, new_items, new_mails, change_nodes, type, req, timer)
        return defer


    def _pack_event_response(self, matcher, data, items, mails, nodes, type, req, timer):
        """打包返回 response
        """
        resource = data.resource.get(True)
        map = data.map.get(True)

        #更新邮件中的敌人信息
        for mail in mails:
            if mail.related_node_id in matcher.players:
                rival_id = mail.related_node_id
                rival = data.rival_list.get(rival_id)
                mail.attach_enemy_info(rival)
            else:
                node = data.node_list.get(mail.related_node_id)
                if node.is_key_node():
                    mail.attach_enemy_detail(
                            NameGenerator().gen(), 0,
                            NodeInfo.ENEMY_TYPE_PVE_RESOURCE)#TODO 随机

        #打包响应
        res = map_pb2.TriggerEventRes()
        res.status = 0

        #res.map.next_war_gap = map.next_war_time - timer.now
        res.map.next_luck_gap = map.next_luck_time - timer.now
        for node in nodes:
            pack.pack_node_info(data, node, res.map.nodes.add(), timer.now)
        pack.pack_resource_info(resource, res.resource)
        for item in items:
            item_message = res.items.add()
            item_message.basic_id = item[1]
            item_message.num = item[0]
        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)
        energy = data.energy.get(True)
        pack.pack_energy_info(energy, res.energy_info, timer.now)

        map_business.check_map_data(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._trigger_event_succeed, req, res, timer)
        return defer


    def _trigger_event_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, ("Trigger event succeed"),
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _trigger_event_failed(self, err, type, req, timer):
        logger.fatal("Trigger event failed[reason=%s]" % err)
        res = map_pb2.TriggerEventRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Trigger event failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def rematch_node(self, user_id, request):
        """手动重新匹配敌人(仅限PVP)占领的关键点
        """
        timer = Timer(user_id)

        req = map_pb2.RematchNodeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_rematch_node, req, timer)
        defer.addErrback(self._rematch_node_failed, req, timer)
        return defer


    def _calc_rematch_node(self, data, req, timer):
        """
        """
        rematch_node_id = NodeInfo.generate_id(data.id, req.node.basic_id)
        rematch_node = data.node_list.get(rematch_node_id)

        rival_id = rematch_node.id
        rival = data.rival_list.get(rival_id, True)
        invalid_rival = [data.id, rival.rival_id]#不允许出现原来的敌人

        if not map_business.rematch_key_node(data, rematch_node, timer.now):
            raise Exception("Rematch node failed")

        #为新刷出的敌方节点匹配敌人
        for node in data.node_list.get_all(True):
            if node.is_rival_pvp() and node.is_enemy_complete():
                rival_id = node.id
                rival = data.rival_list.get(rival_id, True)
                invalid_rival.append(rival.rival_id)

        user =  data.user.get(True)
        matcher = RivalMatcher(user.level, invalid_rival)
        matcher.add_condition(data, rematch_node)

        defer = matcher.match(user.country)
        defer.addCallback(self._pack_rematch_node_response, data, rematch_node, req, timer)
        return defer


    def _pack_rematch_node_response(self, matcher, data, node, req, timer):
        res = map_pb2.RematchNodeRes()
        res.status = 0
        pack.pack_node_info(data, node, res.node, timer.now)

        map_business.check_map_data(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._rematch_node_succeed, req, res, timer)
        return defer


    def _rematch_node_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Rematch node succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _rematch_node_failed(self, err, req, timer):
        logger.fatal("Rematch node failed[reason=%s]" % err)
        res = map_pb2.RematchNodeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Rematch node failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def clear_lucky_event(self, user_id, request):
        """清除随机事件
        1 随机事件未启动，超过 idletime
        2 随机事件未结束，超过 lifetime
        """
        timer = Timer(user_id)

        req = map_pb2.ClearLuckyEventReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_clear_lucky_event, req, timer)
        defer.addErrback(self._clear_lucky_event_failed, req, timer)
        return defer


    def _calc_clear_lucky_event(self, data, req, timer):
        """
        """
        node_basic_id = req.node.basic_id
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)

        change_nodes = []
        new_items = []
        new_mails = []

        ret = Ret()
        if not event_business.clear_lucky_event(
                data, node, timer.now, change_nodes, new_items, new_mails, ret):
            if ret.get() == "NO_EVENT":
                res = map_pb2.ClearLuckyEventRes()
                res.status = 0
                res.ret = map_pb2.ClearLuckyEventRes.NO_EVENT
                pack.pack_node_info(data, node, res.node, timer.now)
                return self._clear_lucky_event_succeed(data, req, res, timer)
            else:
                raise Exception("Clear lucky event failed")

        #为新刷出的敌方节点匹配敌人
        #不合法的敌人：自己，以及已经在地图上出现过的 PVP 敌人
        invalid_rival = [data.id]
        for node in data.node_list.get_all(True):
            if node.is_rival_pvp() and node.is_enemy_complete():
                rival_id = node.id
                rival = data.rival_list.get(rival_id, True)
                invalid_rival.append(rival.rival_id)

        user = data.user.get(True)
        matcher = RivalMatcher(user.level, invalid_rival)

        for node in change_nodes:
            if node.is_lack_enemy_detail():
                matcher.add_condition(data, node)

        defer = matcher.match(user.country)
        defer.addCallback(self._pack_clear_lucky_event_response,
                data, change_nodes, new_items, new_mails, req, timer)
        return defer


    def _pack_clear_lucky_event_response(self, matcher, data,
            change_nodes, items, mails, req, timer):
        """打包
        """
        resource = data.resource.get()
        map = data.map.get()

        #更新邮件中的敌人信息
        for mail in mails:
            if mail.related_node_id in matcher.players:
                rival_id = mail.related_node_id
                rival = data.rival_list.get(rival_id)
                mail.attach_enemy_info(rival)
            else:
                node = data.node_list.get(mail.related_node_id)
                if node.is_key_node():
                    mail.attach_enemy_detail(
                            NameGenerator().gen(), 0,
                            NodeInfo.ENEMY_TYPE_PVE_RESOURCE)#TODO 随机

        #打包响应
        res = map_pb2.ClearLuckyEventRes()
        res.status = 0
        res.ret = map_pb2.ClearLuckyEventRes.OK

        for node in change_nodes:
            pack.pack_node_info(data, node, res.nodes.add(), timer.now)
        pack.pack_resource_info(resource, res.resource)
        for item in items:
            item_message = res.items.add()
            item_message.basic_id = item[1]
            item_message.num = item[0]
        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        map_business.check_map_data(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._clear_lucky_event_succeed, req, res, timer)
        return defer


    def _clear_lucky_event_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Clear lucky event succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _clear_lucky_event_failed(self, err, req, timer):
        logger.fatal("Clear lucky event failed[reason=%s]" % err)
        res = map_pb2.ClearLuckyEventRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Clear lucky event failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def abandon_node(self, user_id, request):
        """手动丢弃自己的关键点
           tips:1.只能丢弃关键点（主城除外）
                2.有随机事件的关键点不能丢
                3.有附属点的关键点不能丢弃
        """
        timer = Timer(user_id)

        req = event_pb2.AbandonNodeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_abandon_node, req, timer)
        defer.addErrback(self._abandon_node_failed, req, timer)
        return defer


    def _calc_abandon_node(self, data, req, timer):
        """
        """
        abandon_node_id = NodeInfo.generate_id(data.id, req.node_id)
        abandon_node = data.node_list.get(abandon_node_id)

        change_nodes = []
        if not map_business.abandon_key_node(data, abandon_node, timer.now, change_nodes):
            raise Exception("Abandon node failed")

        #为新刷出的敌方节点匹配敌人
        #不合法的敌人：自己，以及已经在地图上出现过的 PVP 敌人
        invalid_rival = [data.id]
        for node in data.node_list.get_all(True):
            if node.is_rival_pvp() and node.is_enemy_complete():
                rival_id = node.id
                rival = data.rival_list.get(rival_id, True)
                invalid_rival.append(rival.rival_id)

        user =  data.user.get(True)
        matcher = RivalMatcher(user.level, invalid_rival)

        for node in change_nodes:
            if node.is_lack_enemy_detail():
                matcher.add_condition(data, node)

        defer = matcher.match(user.country)
        defer.addCallback(self._pack_abandon_node_response,
                data, change_nodes, req, timer)
        return defer


    def _pack_abandon_node_response(self, matcher, data, change_nodes, req, timer):
        res = event_pb2.AbandonNodeRes()
        res.status = 0
        for node in change_nodes:
            pack.pack_node_info(data, node, res.nodes.add(), timer.now)

        map_business.check_map_data(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._abandon_node_succeed, req, res, timer)
        return defer


    def _abandon_node_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Abandon node succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _abandon_node_failed(self, err, req, timer):
        logger.fatal("Abandon node failed[reason=%s]" % err)
        res = event_pb2.AbandonNodeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Abandon node failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



