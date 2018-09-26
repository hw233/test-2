#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 抽奖相关的请求
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import wineShop_pb2
from proto import broadcast_pb2
from proto import activity_pb2
from datalib.global_data import DataBase
from app import basic_view
from app import pack
from app import compare
from app import log_formater
from app.data.shop import ShopInfo
from app.data.hero import HeroInfo
from app.data.item import ItemInfo
from app.data.soldier import SoldierInfo
from app.business import draw as draw_business
from app.business import hero as hero_business
from app.business import item as item_business
from app.business import account as account_business



class DrawProcessor(object):

    def __init__(self):
        self._TYPE_GOLD_DRAW = 1
        self._TYPE_MONEY_DRAW = 2
        self._TYPE_GOLD_MULTI_DRAW = 3
        self._TYPE_MONEY_MULTI_DRAW = 4
        self._TYPE_TREASURE_DRAW = 5
        self._TYPE_TREASURE_MULTI_DRAW = 6


    def get_draw_status(self, user_id, request):
        """查询抽奖的状态：剩余免费次数、距离下次免费的时间
        """
        timer = Timer(user_id)

        req = wineShop_pb2.QueryDrawStatusReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._get_draw_status_succeed, req, timer)
        defer.addErrback(self._get_draw_status_failed, req, timer)
        return defer


    def _get_draw_status_succeed(self, data, req, timer):
        draw = data.draw.get(True)

        res = wineShop_pb2.QueryDrawStatusRes()
        res.status = 0
        res.money_draw.search_num = draw.money_draw_free_num
        res.money_draw.next_left_time = max(0, draw.money_draw_free_time - timer.now)
        res.gold_draw.search_num = draw.gold_draw_free_num
        res.gold_draw.next_left_time = max(0, draw.gold_draw_free_time - timer.now)

        response = res.SerializeToString()
        log = log_formater.output(data, "Get draw status succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _get_draw_status_failed(self, err, req, timer):
        logger.fatal("Get draw status failed[reason=%s]" % err)

        res = wineShop_pb2.QueryDrawStatusRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Get draw status failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def draw_with_gold(self, user_id, request):
        return self._draw(user_id, request, self._TYPE_GOLD_DRAW)


    def draw_with_money(self, user_id, request):
        return self._draw(user_id, request, self._TYPE_MONEY_DRAW)


    def multi_draw_with_gold(self, user_id, request):
        return self._draw(user_id, request, self._TYPE_GOLD_MULTI_DRAW)


    def multi_draw_with_money(self, user_id, request):
        return self._draw(user_id, request, self._TYPE_MONEY_MULTI_DRAW)

   
    def treasure_draw(self, user_id, request):
        return self._treasure(user_id, request) 
   

    def _draw(self, user_id, request, type):
        """
        抽奖
        Args:
            request[protobuf] 请求
            type[int]: 抽奖类型
                _TYPE_GOLD_DRAW          元宝抽奖
                _TYPE_MONEY_DRAW         金钱抽奖
                _TYPE_GOLD_MULTI_DRAW    元宝十连抽
                _TYPE_MONEY_MULTI_DRAW   金钱十连抽
        """
        timer = Timer(user_id)

        req = wineShop_pb2.WineShopDrawReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._get_basic_data, user_id, req, type, timer)
        return defer

    def _treasure(self, user_id, request):
        """夺宝抽奖
        """
        type = 0
        timer = Timer(user_id)
        req = activity_pb2.TurntableDrawReq()
        req.ParseFromString(request)
        if req.times == 1:
            type = 5
        elif req.times == 10:
            type = 6
        else:
            raise Exception("treasure times error") 
 
        defer = DataBase().get_basic_data(basic_view.BASIC_ID)    #获取basic data
        defer.addCallback(self._get_treasure_basic_data, user_id, req, type, timer)
        return defer

    def _get_treasure_basic_data(self, basic_data, user_id, req, type, timer ):
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_treasure_draw, basic_data, req, type, timer)
        defer.addErrback(self._draw_treasure_failed, req, timer)
        return defer
 
    def _calc_treasure_draw(self, data, basic_data, req, type,timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")
        user = data.user.get()
        resource = data.resource.get()
        draw = data.draw.get()

        resource.update_current_resource(timer.now)
        item_list = []
        if not draw_business.treasure_draw(
                basic_data, data, user, resource, draw,
                item_list, req, timer.now):
            raise Exception("Treasure draw failed")
        #添加抽奖得到的英雄和物品
        if not item_business.gain_item(data, item_list, "trun draw ", log_formater.DRAW):
            raise Exception("Gain item failed")


        alltimes = draw.total_treasure_draw_num 
        res = self._pack_treasure_draw_response(data, item_list, resource, alltimes, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._draw_treasure_succeed, type, req, res, timer)
        return defer

    def _pack_treasure_draw_response(self, data, item_list, resource, alltimes, timer):
        win_item = []
        for (basic_id, num) in item_list:
            item = ItemInfo.create(data.id, basic_id, num)
            win_item.append(item)

        res = activity_pb2.TurntableDrawRes()
        res.status = 0
        for item in win_item:
            pack.pack_item_info(item, res.items.add())
        pack.pack_resource_info(resource, res.resource)
        res.all_times = alltimes
        return res



    def _get_basic_data(self, basic_data, user_id, req, type, timer):
        """
        """
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_draw, basic_data, req, type, timer)
        defer.addErrback(self._draw_failed, req, timer)
        return defer


    def _calc_draw(self, data, basic_data, req, type, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        user = data.user.get()
        resource = data.resource.get()
        draw = data.draw.get()

        resource.update_current_resource(timer.now)

        is_draw_with_item = False
        draw_item = None
        if req.HasField("item"):
            #用抽奖券抽
            is_draw_with_item = True
            item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
            draw_item = data.item_list.get(item_id)
            if draw_item is None:
                raise Exception("Item not exist")

        hero_list = []
        item_list = []
        if type == self._TYPE_GOLD_DRAW:
            if not draw_business.draw_with_gold(
                    basic_data, data, user, resource, draw,
                    hero_list, item_list, timer.now, draw_item, req.free):
                raise Exception("Draw with gold failed")
        elif type == self._TYPE_MONEY_DRAW:
            if not draw_business.draw_with_money(
                    user, resource, draw, hero_list, item_list, timer.now, draw_item, req.free):
                raise Exception("Draw with money failed")
        elif type == self._TYPE_GOLD_MULTI_DRAW:
            if not draw_business.multi_draw_with_gold(
                    basic_data, data, user, resource, draw, hero_list, item_list, 
                    timer.now, draw_item):
                raise Exception("Multi draw with gold failed")
        elif type == self._TYPE_MONEY_MULTI_DRAW:
            if not draw_business.multi_draw_with_money(
                    user, resource, draw, hero_list, item_list, timer.now, draw_item):
                raise Exception("Multi draw with money failed")
        #elif type == self._TYPE_TREASURE_DRAW:
        #    pass
        #elif type == self._TYPE_TREASURE_MULTI_DRAW:
        #    pass 
        else:
            raise Exception("Invalid draw type[type=%d]" % type)

        #添加抽奖得到的英雄和物品
        for (hero_basic_id, hero_num) in hero_list:
            if not hero_business.gain_hero(data, hero_basic_id, hero_num):
                raise Exception("Gain hero failed")
        if not item_business.gain_item(data, item_list, "draw ", log_formater.DRAW):
            raise Exception("Gain item failed")

        if is_draw_with_item:
            compare.check_item(data, req.item)

        #获得S级武将要播广播
        for (hero_basic_id, hero_num) in hero_list:
            if hero_business.is_need_broadcast(hero_basic_id):
                try:
                    self._add_get_hero_broadcast(data.user.get(), draw, hero_basic_id)
                except:
                    logger.warning("Send get hero broadcast failed")

        #构造返回
        if type == self._TYPE_GOLD_DRAW or type == self._TYPE_GOLD_MULTI_DRAW:
            free_num = draw.gold_draw_free_num
            free_time = draw.gold_draw_free_time
        else:
            free_num = draw.money_draw_free_num
            free_time = draw.money_draw_free_time

        res = self._pack_draw_response(data, hero_list, item_list, resource,
                free_num, free_time, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._draw_succeed, type, req, res, timer)
        return defer


    def _add_get_hero_broadcast(self, user, draw, hero_basic_id):
        """广播玩家获得S级英雄数据
        Args:

        """
        (mode, priority, life_time, content) = hero_business.create_broadcast_content(user, hero_basic_id, type = 1)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add get hero draw broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_get_hero_broadcast_result)
        return defer


    def _check_add_get_hero_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast result failed")

        return True



    def _pack_draw_response(self, data, hero_list, item_list,
            resource, search_num, next_time, now):
        """封装响应
        返回客户端的是抽奖获得的英雄和物品（并未将已经拥有的英雄分解成将魂石）
        客户端会自行进行分解
        """
        win_hero = []
        for (basic_id, num) in hero_list:
            soldier_basic_id = HeroInfo.get_default_soldier_basic_id(basic_id)
            soldier_id = SoldierInfo.generate_id(data.id, soldier_basic_id)
            soldier = data.soldier_list.get(soldier_id, True)

            hero = HeroInfo.create(data.id, basic_id, soldier, technology_basic_ids = [])
            for i in range(0, num):
                win_hero.append(hero)

        win_item = []
        for (basic_id, num) in item_list:
            item = ItemInfo.create(data.id, basic_id, num)
            win_item.append(item)

        res = wineShop_pb2.WineShopDrawRes()
        res.status = 0

        for item in win_item:
            pack.pack_item_info(item, res.items.add())
        for hero in win_hero:
            pack.pack_hero_info(hero, res.heroes.add(), now)
        pack.pack_resource_info(resource, res.resource)
        res.draw.search_num = search_num
        res.draw.next_left_time = max(0, next_time - now)
        return res

    def _draw_treasure_succeed(self, data, type, req, res, timer):
        response = res.SerializeToString()
        if type == self._TYPE_TREASURE_DRAW:
            draw_type = 'treasure_one'
        elif type == self._TYPE_TREASURE_MULTI_DRAW:
            draw_type = 'treasure_ten'
        else:
            raise Exception("treasure times error")  
        log = log_formater.output(data, ("Lucky %s treasure draw succeed" % draw_type),
                req, res, timer.count_ms())
        logger.notice(log)
        return response

    def _draw_treasure_failed(self, err, req, timer):
        logger.fatal("Lucky treasure draw failed[reason=%s]" % err)

        res = activity_pb2.TurntableDrawRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Lucky draw failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def _draw_succeed(self, data, type, req, res, timer):
        response = res.SerializeToString()
        draw_type = ''
        if type == self._TYPE_GOLD_DRAW:
            draw_type = 'gold_one'
        elif type == self._TYPE_MONEY_DRAW:
            draw_type = 'money_one'
        elif type == self._TYPE_GOLD_MULTI_DRAW:
            draw_type = 'gold_multi'
        elif type == self._TYPE_MONEY_MULTI_DRAW:
            draw_type = 'money_multi'
        log = log_formater.output(data, ("Lucky %s draw succeed" % draw_type),
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _draw_failed(self, err, req, timer):
        logger.fatal("Lucky draw failed[reason=%s]" % err)

        res = wineShop_pb2.WineShopDrawRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Lucky draw failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


