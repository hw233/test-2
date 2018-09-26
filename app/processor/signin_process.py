#coding:utf8
"""
Created on 2015-06-23
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief:  签到
"""

from utils import logger
from utils.timer import Timer
from proto import user_pb2
from datalib.global_data import DataBase
from app import pack
from app import log_formater
from app.data.hero import HeroInfo
from app.data.item import ItemInfo
from app.data.soldier import SoldierInfo
from app.business import hero as hero_business
from app.business import item as item_business
from app.business import signin as signin_business


class SigninProcessor(object):

    def signin(self, user_id, request):
        """
        执行签到
        """
        timer = Timer(user_id)

        req = user_pb2.SignInReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_signin, req, timer, False)
        defer.addErrback(self._signin_failed, req, timer)
        return defer


    def signin_custom(self, user_id, request):
        """
        执行签到(可以指定签到的天数)
        """
        timer = Timer(user_id)

        req = user_pb2.SignInReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_signin, req, timer, True)
        defer.addErrback(self._signin_failed, req, timer)
        return defer


    def _calc_signin(self, data, req, timer, force = False):
        """
        """
        sign = data.sign.get()
        user = data.user.get()

        hero_list = []
        item_list = []
        if not signin_business.signin(
                sign, req.index, user, hero_list, item_list, timer.now, force):
            raise Exception("Sign in failed")

        for (hero_basic_id, hero_num) in hero_list:
            if not hero_business.gain_hero(data, hero_basic_id, hero_num):
                raise Exception("Gain hero failed")
        if not item_business.gain_item(data, item_list, "signin reward", log_formater.SIGNIN_REWARD):
            raise Exception("Gain item failed")

        res = self._pack_signin_response(data, hero_list, item_list, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._signin_succeed, req, res, timer)
        return defer


    def _pack_signin_response(self, data, hero_list, item_list, now):
        """封装签到响应
        """
        #为了封装 response 构造 HeroInfo 和 ItemInfo
        win_hero = []
        for (basic_id, num) in hero_list:
            soldier_basic_id = HeroInfo.get_default_soldier_basic_id(basic_id)
            soldier_id = SoldierInfo.generate_id(data.id, soldier_basic_id)
            soldier = data.soldier_list.get(soldier_id, True)
            hero = HeroInfo.create(data.id, basic_id, soldier, [])
            for i in range(0, num):
                win_hero.append(hero)

        win_item = []
        for (basic_id, num) in item_list:
            item = ItemInfo.create(data.id, basic_id, num)
            win_item.append(item)

        res = user_pb2.SignInRes()
        res.status = 0
        if len(win_hero) > 0:
            assert len(win_hero) == 1
            pack.pack_hero_info(win_hero[0], res.hero, now)
        if len(win_item) > 0:
            assert len(win_item) == 1
            pack.pack_item_info(win_item[0], res.item)

        return res


    def _signin_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Signin succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _signin_failed(self, err, req, timer):
        logger.fatal("[Exception=%s]" % err)
        res = user_pb2.SignInRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Signin Failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


