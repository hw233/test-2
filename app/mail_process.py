#coding:utf8
"""
Created on 2015-06-23
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief:  邮件
         1. 查询邮件
         2. 使用邮件(可能获得物品、资源等)
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import mail_pb2
from proto import internal_pb2
from datalib.global_data import DataBase
from app import pack
from app import log_formater
from app.revenge_rival_matcher import RevengeRivalMatcher
from app.data.mail import MailInfo
from app.data.node import NodeInfo
from app.business import mail as mail_business


class MailProcessor(object):

    def query_mail(self, user_id, request):
        """查询邮件
        """
        timer = Timer(user_id)

        req = mail_pb2.QueryMailReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._query_mail_succeed, req, timer)
        defer.addErrback(self._query_mail_failed, req, timer)
        return defer


    def _query_mail_succeed(self, data, req, timer):
        res = mail_pb2.QueryMailRes()
        res.status = 0
        mails = data.mail_list.get_all(True)
        for mail in mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)
        response = res.SerializeToString()

        log = log_formater.output(data, "Query mail succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _query_mail_failed(self, err, req, timer):
        logger.fatal("Query mail failed[reason=%s]" % err)

        res = mail_pb2.QueryMailRes()
        res.status = -1
        response = res.SerializeToString()

        logger.notice("Query mail failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def read_mail(self, user_id, request):
        """阅读邮件
        """
        timer = Timer(user_id)

        req = mail_pb2.UseMailReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_read_mail, req, timer)
        defer.addCallback(self._read_mail_succeed, req, timer)
        defer.addErrback(self._read_mail_failed, req, timer)
        return defer


    def _calc_read_mail(self, data, req, timer):
        """
        阅读邮件
        """
        if not mail_business.read(data, req.mail_indexs, timer.now):
            raise Exception("Read mail failed")

        return DataBase().commit(data)


    def _read_mail_succeed(self, data, req, timer):
        res = mail_pb2.UseMailRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Read mail succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _read_mail_failed(self, err, req, timer):
        logger.fatal("Use mail failed[reason=%s]" % err)
        res = mail_pb2.UseMailRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Read mail failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def use_mail(self, user_id, request):
        """使用邮件
        """
        timer = Timer(user_id)

        req = mail_pb2.UseMailReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_use_mail, req, timer)
        defer.addErrback(self._use_mail_failed, req, timer)
        return defer


    def _calc_use_mail(self, data, req, timer):
        """
        阅读邮件
        1 系统邮件：[有附件] 领取奖励
        2 战斗邮件：[主城防守失败] 复仇 （复仇邮件只能有一封）
        """
        if len(req.mail_indexs) == 1:
            mail_id = MailInfo.generate_id(data.id, req.mail_indexs[0])
            mail = data.mail_list.get(mail_id, True)
            #复仇
            if mail.is_battle_mail():
                return self._use_mail_get_rival(data, req, timer)

        return self._use_mail_get_reward(data, req, timer)


    def _use_mail_get_reward(self, data, req, timer):
        """使用邮件，领取奖励
        """
        if not mail_business.use_mail_to_get_reward(data, req.mail_indexs, timer.now):
            raise Exception("Use mail get reward failed")

        resource = data.resource.get(True)
        res = self._pack_use_mail_response(resource, None, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._use_mail_succeed, req, res, timer)
        return defer


    def _use_mail_get_rival(self, data, req, timer):
        """使用邮件，查询敌人
        """
        rival_user_id = mail_business.use_mail_to_get_rival(data, req.mail_indexs[0])
        if rival_user_id == 0:
            raise Exception("Use mail get rival failed")

        matcher = RevengeRivalMatcher()
        defer = matcher.search(data, rival_user_id)
        defer.addCallback(self._get_rival_detail, data, req, timer)
        return defer


    def _get_rival_detail(self, searcher, data, req, timer):
        res = self._pack_use_mail_response(None, searcher.player, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._use_mail_succeed, req, res, timer)
        return defer


    def _pack_use_mail_response(self, resource, rival, now):
        res = mail_pb2.UseMailRes()
        res.status = 0
        if resource is not None:
            pack.pack_resource_info(resource, res.resource)
        if rival is not None:
            pack.pack_rival_info(rival, res.rival)

        return res


    def _use_mail_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Use mail succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _use_mail_failed(self, err, req, timer):
        logger.fatal("Use mail failed[reason=%s]" % err)
        res = mail_pb2.UseMailRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Use mail failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_mail(self, user_id, request):
        """
        向指定用户添加邮件
        内部接口
        """
        timer = Timer(user_id)

        req = internal_pb2.AddMailReq()
        req.ParseFromString(request)

        defer = self._forward_mail(req.recipients_user_id, req.mail, timer)
        defer.addCallback(self._add_mail_succeed, req, timer)
        defer.addErrback(self._add_mail_failed, req, timer)
        return defer


    def _forward_mail(self, user_id, mail, timer):
        """向用户转发邮件
        """
        req = internal_pb2.ReceiveMailReq()
        req.user_id = user_id
        req.mail.CopyFrom(mail)
        request = req.SerializeToString()

        defer = GlobalObject().root.callChild("portal", "forward_mail", user_id, request)
        defer.addCallback(self._check_forward_mail)
        return defer


    def _check_forward_mail(self, response):
        res = internal_pb2.ReceiveMailRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward mail failed")


    def _add_mail_succeed(self, data, req, timer):
        res = internal_pb2.AddMailRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output2(req.user_id, "Add mail succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_mail_failed(self, err, req, timer):
        logger.fatal("Use mail failed[reason=%s]" % err)
        res = internal_pb2.AddMailRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add mail failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def receive_mail(self, user_id, request):
        """帐号接收邮件
        如果玩家在线，向玩家推送邮件
        """
        timer = Timer(user_id)

        req = internal_pb2.ReceiveMailReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_mail, req, timer)
        defer.addErrback(self._receive_mail_failed, req, timer)
        return defer


    def _calc_receive_mail(self, data, req, timer):
        """接收邮件
        """
        mail = mail_business.create_custom_mail(data, req.mail, timer.now)
        if mail is None:
            raise Exception("Create receive mail failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_mail_succeed, req, mail, timer)
        return defer


    def _receive_mail_succeed(self, data, req, mail, timer):
        res = internal_pb2.ReceiveMailRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive mail succeed", req, res, timer.count_ms())
        logger.notice(log)

        self._push_mail(data.id, mail, timer)
        DataBase().clear_data(data)
        return response


    def _push_mail(self, user_id, mail, timer):
        """向客户端推送邮件，如果用户不在线，则推送失败
        """
        res = mail_pb2.QueryMailRes()
        res.status = 0
        pack.pack_mail_info(mail, res.mails.add(), timer.now)
        response = res.SerializeToString()
        return GlobalObject().root.callChild("portal", "push_mail", user_id, response)


    def _receive_mail_failed(self, err, req, timer):
        logger.fatal("Receive mail failed[reason=%s]" % err)
        res = internal_pb2.ReceiveMailRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive mail failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


