#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 商店（酒肆）相关的请求
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import wineShop_pb2
from proto import internal_pb2
from proto import unit_pb2
from proto import internal_union_pb2
from proto import legendcity_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.item import ItemInfo
from app.data.shop import ShopInfo
from app.data.legendcity import LegendCityInfo
from app.business import shop as shop_business
from app.business import account as account_business


class ShopProcessor(object):
    """商店逻辑
    """

    def seek_normal_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_MONEY]
        return self._seek_goods(user_id, request, types)


    def seek_achievement_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_ACHIEVEMENT]
        return self._seek_goods(user_id, request, types)


    def seek_legendcity_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_LEGENDCITY]
        return self._seek_goods(user_id, request, types)


    def seek_arena_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_ARENA]
        return self._seek_goods(user_id, request, types)

    def seek_soul_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_SOUL_SOUL]
        return self._seek_goods(user_id, request, types)

    def seek_gold_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_GOLD]
        return self._seek_goods(user_id, request, types)


    def _seek_goods(self, user_id, request, types):
        """查询酒肆中可购买的物品
        如果达到免费刷新的条件，会自动刷新一次
        """
        timer = Timer(user_id)

        req = wineShop_pb2.QueryGoodsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_seek_goods, req, types, timer)
        defer.addErrback(self._seek_goods_failed, req, timer)
        return defer


    def _calc_seek_goods(self, data, req, types, timer):
        """查询货物
        """
        shops = []
        index = 1
        if req.HasField("index"):
            index = req.index
        for type in types:
            shop_id = ShopInfo.generate_id(data.id, type, index)
            shops.append(data.shop_list.get(shop_id))
            logger.debug("Seek goods[type=%d][index=%d]" % (type, index))

        goods = []
        if not shop_business.seek_goods(data, shops, goods, timer.now):
            raise Exception("Seek goods failed")

        resource = data.resource.get(True)
        res = self._pack_refresh_goods_response(
                goods, shops[0], resource, req, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._seek_goods_succeed, types, req, res, timer)
        return defer


    def _seek_goods_succeed(self, data, types, req, res, timer):
        response = res.SerializeToString()

        seek_type = ''
        if types ==  [ShopInfo.GOODS_TYPE_MONEY]:
            seek_type = 'wineshop'
        elif types == [ShopInfo.GOODS_TYPE_ACHIEVEMENT]:
            seek_type = 'achievement'
        elif types == [ShopInfo.GOODS_TYPE_LEGENDCITY]:
            seek_type = 'legendcity'
        elif types == [ShopInfo.GOODS_TYPE_ARENA]:
            seek_type = 'arena'
        elif types == [ShopInfo.GOODS_TYPE_GOLD]:
            seek_type = 'gold'
        log = log_formater.output(data, ("Seek %s goods succeed" % seek_type),
                req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _seek_goods_failed(self, err, req, timer):
        logger.fatal("Seek goods failed[reason=%s]" % err)

        res = wineShop_pb2.QueryGoodsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Seek goods failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refresh_normal_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_MONEY]
        return self._refresh_goods(user_id, request, types)


    def refresh_achievement_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_ACHIEVEMENT]
        return self._refresh_goods(user_id, request, types)


    def refresh_legendcity_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_LEGENDCITY]
        return self._refresh_goods(user_id, request, types)


    def refresh_arena_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_ARENA]
        return self._refresh_goods(user_id, request, types)


    def refresh_soul_goods(self, user_id, request):
        types = [ShopInfo.GOODS_TYPE_SOUL_SOUL]
        return self._refresh_goods(user_id, request, types)


    def _refresh_goods(self, user_id, request, types):
        """刷新酒肆中可以购买的物品
        """
        timer = Timer(user_id)

        req = wineShop_pb2.QueryGoodsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh_goods, req, types, timer)
        defer.addErrback(self._refresh_goods_failed, req, timer)
        return defer


    def _calc_refresh_goods(self, data, req, types, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        shops = []
        index = 1
        if req.HasField("index"):
            index = req.index
        for type in types:
            shop_id = ShopInfo.generate_id(data.id, type, index)
            shops.append(data.shop_list.get(shop_id))

        is_refresh_with_item = False
        refresh_item = None
        if req.HasField("item"):
            #用刷新代币刷新商铺
            is_refresh_with_item = True
            item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
            refresh_item = data.item_list.get(item_id)
            if refresh_item is None:
                raise Exception("Item not exist")

        free = False
        if shops[0].is_able_to_refresh_free(timer.now):
            free = True

        goods = []
        if not shop_business.refresh_goods(data, shops, goods, timer.now, refresh_item, free):
            raise Exception("Refresh goods failed")

        if is_refresh_with_item:
            compare.check_item(data, req.item)  

        resource = data.resource.get(True)
        #任意选择一个商店的刷新次数
        res = self._pack_refresh_goods_response(
                goods, shops[0], resource, req, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._refresh_goods_succeed, types, req, res, timer)
        return defer


    def _pack_refresh_goods_response(self, goods, shop, resource, req, now):
        """打包货物信息
        Args:
            goods[list(GoodsInfo)]: 货物信息
        """
        res = wineShop_pb2.QueryGoodsRes()
        res.status = 0

        for info in goods:
            pack.pack_goods_info(info, res.goods.add())
        res.refresh_num = shop.refresh_num
        res.next_refresh_gap = shop.next_free_time - now
        pack.pack_resource_info(resource, res.resource)
        return res


    def _refresh_goods_succeed(self, data, types, req, res, timer):
        response = res.SerializeToString()

        seek_type = ''
        if types ==  [ShopInfo.GOODS_TYPE_MONEY]:
            seek_type = 'wineshop'
        elif types == [ShopInfo.GOODS_TYPE_ACHIEVEMENT]:
            seek_type = 'achievement'
        elif types == [ShopInfo.GOODS_TYPE_LEGENDCITY]:
            seek_type = 'legendcity'
        elif types == [ShopInfo.GOODS_TYPE_ARENA]:
            seek_type = 'arena'
        log = log_formater.output(data, ("Refresh %s goods succeed" % seek_type),
                req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _refresh_goods_failed(self, err, req, timer):
        logger.fatal("Refresh goods failed[reason=%s]" % err)

        res = wineShop_pb2.QueryGoodsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh goods failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def buy_goods(self, user_id, request):
        """购买酒肆中的物品
        """
        timer = Timer(user_id)

        req = wineShop_pb2.BuyGoodsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_buy_goods, req, timer)
        defer.addCallback(self._buy_goods_succeed, req, timer)
        defer.addErrback(self._buy_goods_failed, req, timer)
        return defer


    def _calc_buy_goods(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        shop_id = ShopInfo.generate_id(data.id, req.goods.type)
        shop = data.shop_list.get(shop_id)

        if not shop_business.buy_goods(data, shop, req.goods.id, timer.now):
            raise Exception("Buy Goods failed")

        compare.check_item(data, req.item)

        defer = DataBase().commit(data)
        return defer


    def _buy_goods_succeed(self, data, req, timer):
        res = wineShop_pb2.BuyGoodsRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        if req.type == wineShop_pb2.SHOP_ARENA:
            res.current_tokens = data.arena.get(True).coin
        
        response = res.SerializeToString()

        log = log_formater.output(data, "Buy goods succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _buy_goods_failed(self, err, req, timer):
        logger.fatal("Buy goods failed[reason=%s]" % err)

        res = wineShop_pb2.BuyGoodsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Buy goods failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def buy_legendcity_goods(self, user_id, request):
        """购买史实城货物
        """
        timer = Timer(user_id)
        req = wineShop_pb2.BuyLegendCityGoodsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_buy_legendcity_goods, req, timer)
        defer.addErrback(self._buy_legendcity_goods_failed, req, timer)
        return defer


    def _calc_buy_legendcity_goods(self, data, req, timer):
        """购买史实城商店中的商品
        """
        shop_id = ShopInfo.generate_id(data.id, ShopInfo.GOODS_TYPE_LEGENDCITY, req.index)
        shop = data.shop_list.get(shop_id)
        pay = shop.calc_goods_price(req.goods.id)
        extra_pay = int(pay * (req.tax / 100.0))

        if not shop_business.buy_goods(data, shop, req.goods.id, timer.now, req.tax):
            raise Exception("Buy Goods failed")

        compare.check_item(data, req.item)

        #请求 Unit 模块，缴税
        unit_req = unit_pb2.UnitBuyGoodsReq()
        unit_req.user_id = data.id
        unit_req.pay = pay
        unit_req.extra_pay = extra_pay
        unit_req.tax = req.tax
        defer = GlobalObject().remote['unit'].callRemote(
                "buy_goods", req.index, unit_req.SerializeToString())
        defer.addCallback(self._pack_buy_legendcity_goods_response, data, req, timer)
        return defer


    def _pack_buy_legendcity_goods_response(self, unit_response, data, req, timer):
        unit_res = unit_pb2.UnitBuyGoodsRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit res error[res=%s]" % unit_res)

        if unit_res.ret != legendcity_pb2.OK:
            #如果赋税发生改变
            return self._buy_legendcity_goods_invalid(unit_res)

        defer = DataBase().commit(data)
        defer.addCallback(self._buy_legendcity_goods_succeed, unit_res.reputation, req, timer)
        return defer


    def _buy_legendcity_goods_invalid(self, unit_res):
        assert unit_res.ret != legendcity_pb2.OK
        res = wineShop_pb2.BuyLegendCityGoodsRes()
        res.status = 0
        res.ret = unit_res.ret
        res.tax = unit_res.tax

        response = res.SerializeToString()
        log = log_formater.output(data, "buy goods succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _buy_legendcity_goods_succeed(self, data, reputation, req, timer):
        res = wineShop_pb2.BuyLegendCityGoodsRes()
        res.status = 0
        res.ret = legendcity_pb2.OK
        res.reputation = reputation

        response = res.SerializeToString()
        log = log_formater.output(data, "buy goods succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _buy_legendcity_goods_failed(self, err, req, timer):
        logger.fatal("Buy goods failed[reason=%s]" % err)
        res = wineShop_pb2.BuyLegendCityGoodsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Buy goods failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


