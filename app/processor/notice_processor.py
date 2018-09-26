#coding:utf8
"""
Created on 2015-10-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 接到相关通知处理逻辑
"""

import random
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils import utils
from utils.timer import Timer
from proto import battle_pb2
from proto import rival_pb2
from proto import internal_pb2
from proto import mail_pb2
from proto import unit_pb2
from proto import legendcity_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app.rival_matcher import RivalMatcher
from app.arena_matcher import ArenaMatcher
from app.data.hero import HeroInfo
from app.data.node import NodeInfo
from app.data.mail import MailInfo
from app.data.rival import RivalInfo
from app.data.arena import ArenaInfo
from app.data.arena_record import ArenaRecordInfo
from app.data.legendcity import LegendCityInfo
from app.business import map as map_business
from app.business import battle as battle_business
from app.business import mail as mail_business
from app.business import legendcity as legendcity_business
from app.business import plunder as plunder_business
from app import compare
from app import log_formater
import base64


class NoticeProcessor(object):


    def receive_notice(self, user_id, request):
        """接收到战斗结果通知的处理
        """
        timer = Timer(user_id)

        req = internal_pb2.BattleResultNoticeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_notice, req, timer)
        defer.addErrback(self._receive_notice_failed, req, timer)
        return defer


    def _calc_receive_notice(self, data, req, timer):
        """接收到战斗结果通知
        1 计算资源变化
        2 生成新邮件
        """
        if req.win:
            mail = self._calc_receive_win_notice(data, req.rival_type, timer.now)
        else:
            mail = self._calc_receive_lose_notice(data, req, req.rival_type, timer.now)
    
            if req.rival_type == NodeInfo.ENEMY_TYPE_PVP_CITY:
                #主城防守失败
                node_id = NodeInfo.generate_id(data.id, 0)     #0表示主城
                node = data.node_list.get(node_id)
                if node.is_in_protect(timer.now):
                    #主城若开保护罩
                    try:
                        self._add_protect_broadcast(data.user.get(), req.rival_name)
                    except:
                        logger.warning("Send protect broadcast failed")
                else:
                    #广播通知被掠夺消息
                    if req.HasField("lost_money") and req.HasField("lost_food"):
                        if req.lost_money != 0 or req.lost_food != 0:
                            try:
                                self._add_battle_defeated_broadcast(data.user.get(), req.rival_name, 
                                    req.lost_money, req.lost_food)
                            except:
                                logger.warning("Send battle defeated broadcast failed")
            

        if mail is not None:
            mail.attach_enemy_detail(req.rival_name, req.rival_user_id, req.rival_type)

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_notice_succeed, req, mail, timer)
        return defer


    def _calc_receive_win_notice(self, data, rival_type, now):
        """收到战斗胜利的通知
        """
        if not battle_business.win_defense(data):
            raise Exception("Defense succeed error")

        if rival_type == NodeInfo.ENEMY_TYPE_PVP_CITY:
            #主城防守成功
            node_id = NodeInfo.generate_id(data.id, 0)     #0表示主城
            node = data.node_list.get(node_id)
            #主城若开保护罩
            if node.is_in_protect(now):
                mail = mail_business.create_own_defence_mail(data, now)
                return mail
            else:
                mail = mail_business.create_node_city_defense_succeed_mail(data, now)
                mail.attach_battle_info(True)
                return mail

        elif rival_type == NodeInfo.ENEMY_TYPE_PVP_RESOURCE:
            #资源点防守成功
            #模拟，随机选择一个己方占领的且未在保护状态的点 key node
            own_nodes = [node for node in data.node_list.get_all(True)
                    if node.is_own_side() and node.is_key_node() and
                    not node.is_in_protect(now)]
            if len(own_nodes) > 0:
                choose = random.sample(own_nodes, 1)[0]
                #资源点防守成功
                mail = mail_business.create_node_resource_defense_succeed_mail(
                        data, now)
                mail.attach_node_info(choose)
                mail.attach_battle_info(True)
                return mail
            else:
                return None

        else:
            raise Exception("Unexpect rival type[type=%d]" % rival_type)


    def _calc_receive_lose_notice(self, data, req, rival_type, now):
        """收到战斗失败的通知
        """
        enemy = plunder_business.get_plunder_enemy(data, req.rival_user_id)
        if enemy is None:
            plunder_business.add_plunder_enemy(data, req.rival_user_id, 
                    base64.b64encode(req.rival_name), req.rival_level, 
                    req.rival_icon_id, req.rival_country,
                    req.rival_score, req.lost_money, req.lost_food)
        else:
            plunder_business.modify_plunder_enemy_by_robbed(
                    enemy, req.lost_money, req.lost_food)


        if rival_type == NodeInfo.ENEMY_TYPE_PVP_CITY:
            #主城防守失败
            node_id = NodeInfo.generate_id(data.id, 0)     #0表示主城
            node = data.node_list.get(node_id)
            #主城若开保护罩，则不通知
            if node.is_in_protect(now):
                mail = mail_business.create_own_defence_mail(data, now)
                return mail
            else:
                mail = mail_business.create_node_city_defeat_mail(data, now)
                mail.attach_battle_info(False)
                if not battle_business.lose_defense(data, True, mail, now):
                    raise Exception("Defense failed error")
                return mail

        elif rival_type == NodeInfo.ENEMY_TYPE_PVP_RESOURCE:
            #资源点防守失败
            if not battle_business.lose_defense(data, False, None, now):
                raise Exception("Defense failed error")
            return None

        elif (rival_type == NodeInfo.ENEMY_TYPE_PLUNDER or 
                rival_type == NodeInfo.ENEMY_TYPE_PLUNDER_ENEMY):
            #被掠夺模式击败
            pass
        else:
            raise Exception("Unexpect rival type[type=%d]" % rival_type)


    def _add_battle_defeated_broadcast(self, user, rival_user_name, money, food):
        """广播玩家被掠夺情况
        Args:

        """
        (mode, priority, life_time, content) = battle_business.create_broadcast_content_battle_defeated(
                rival_user_name, user, money, food)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add battle defeated broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_battle_defeated_broadcast_result)
        return defer


    def _check_add_battle_defeated_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add battle defeated broadcast win num result failed")

        return True


    def _add_protect_broadcast(self, user, rival_user_name):
        """广播玩家开保护罩
        Args:

        """
        (mode, priority, life_time, content) = battle_business.create_broadcast_content_protect(
                rival_user_name, user)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add protect broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_protect_broadcast_result)
        return defer


    def _check_add_protect_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add protect broadcast result failed")

        return True


    def _receive_notice_succeed(self, data, req, mail, timer):
        res = internal_pb2.BattleResultNoticeRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive battle notice succeed", 
                req, res, timer.count_ms())
        logger.notice(log)

        if mail is not None:
            self._push_mail(data.id, mail, timer)
        return response


    def _receive_notice_failed(self, err, req, timer):
        logger.fatal("Receive battle notice failed[reason=%s]" % err)
        res = internal_pb2.BattleResultNoticeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive battle notice failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _push_mail(self, user_id, mail, timer):
        """向客户端推送邮件，如果用户不在线，则推送失败
        """
        res = mail_pb2.QueryMailRes()
        res.status = 0
        pack.pack_mail_info(mail, res.mails.add(), timer.now)
        response = res.SerializeToString()
        return GlobalObject().root.callChild("portal", "push_mail", user_id, response)


    def receive_legendcity_notice(self, user_id, request):
        """接收到史实城战斗结果通知的处理
        """
        timer = Timer(user_id)

        req = internal_pb2.LegendCityBattleResultNoticeReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_legendcity_notice, req, timer)
        defer.addErrback(self._receive_legendcity_notice_failed, req, timer)
        return defer


    def _calc_receive_legendcity_notice(self, data, req, timer):
        """接收到史实城战斗结果通知
        添加战斗记录
        """
        legendcity = data.legendcity_list.get(
                LegendCityInfo.generate_id(data.id, req.city_id))
        user = data.user.get(True)
        guard = data.guard_list.get(data.id, True)

        #传过来的是对手的战斗记录，根据对手的战斗记录，进行赋值
        record = legendcity_business.add_battle_record(data, legendcity)
        if req.record.result == req.record.WIN:
            win = False
        else:
            win = True

        record.set_result(win, False, timer.now)

        rival_buffs = utils.join_to_string(
                [buff.city_buff_id for buff in req.record.rival.buffs])
        record.set_user(user, guard.get_team_score(), req.record.rival.level, rival_buffs)

        user_buffs = utils.join_to_string(
                [buff.city_buff_id for buff in req.record.user.buffs])
        record.set_rival_detail(
                req.record.user.user.user_id, req.record.user.user.name,
                req.record.user.user.level, req.record.user.user.headicon_id,
                req.record.user_battle_score,
                req.record.user.level, user_buffs)

        #防守方需要收到邮件
        mail = mail_business.create_legendcity_defense_mail(data, win, timer.now)
        mail.attach_battle_info(win)
        mail.attach_enemy_detail(req.record.user.user.name, req.record.user.user.user_id,
                NodeInfo.ENEMY_TYPE_LEGENDCITY)
        mail.attach_legendcity_detail(req.record.user.city_id, req.record.user.level)
        self._push_mail(data.id, mail, timer)

        #如果是太守发送广播
        if req.record.rival.level == 7:
            try:
                self._receive_broadcast(data, req, timer)
            except:
                logger.warning("Send receive broadcast failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_legendcity_notice_succeed, req, timer)
        return defer

    def _receive_broadcast(self, data, req, timer):
        """发送广播"""
        user_name = data.user.get(True).name
        rival_user_name = req.record.user.user.name
        city_name = data_loader.LegendCityBasicInfo_dict[req.city_id].nameKey.encode("utf-8")
        
        broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_legendcity_defeat'].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(rival_user_name), 1)
        content = content.replace("#str#", "@%s@" % city_name, 1)
        content = content.replace("#str#", base64.b64decode(user_name), 1)

        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)

    def _receive_legendcity_notice_succeed(self, data, req, timer):
        res = internal_pb2.LegendCityBattleResultNoticeRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive legendcity battle notice succeed", 
                req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _receive_legendcity_notice_failed(self, err, req, timer):
        logger.fatal("Receive legendcity battle notice failed[reason=%s]" % err)
        res = internal_pb2.LegendCityBattleResultNoticeRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive legendcity battle notice failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


