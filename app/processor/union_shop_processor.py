#coding:utf8
"""
Created on 2016-07-06
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟商店相关的请求
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import wineShop_pb2
from proto import union_pb2
from proto import internal_union_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.item import ItemInfo
from app.data.shop import ShopInfo
from app.business import shop as shop_business


class UnionShopProcessor(object):
    """联盟商店
    """

    def _sync_union(self, data, union_id, timer):
        """同步联盟信息
        """
        #请求 Union 模块
        union_req = internal_union_pb2.InternalQueryUnionReq()
        union_req.user_id = data.id
        defer = GlobalObject().remote['gunion'].callRemote(
                "sync_union", union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_sync_result, data, timer)
        return defer


    def _calc_sync_result(self, union_response, data, timer):
        union_res = internal_union_pb2.InternalQueryUnionRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Sync union res error")

        union = data.union.get()
        if union_res.ret == union_pb2.UNION_OK:
            union.update_level(union_res.union.level)
        else:
            if not union.leave_union(union.union_id, timer.now, False):
                raise Exception("Sync and leave union error")

        return data


    def seek_goods(self, user_id, request):
        """查询联盟商店可以购买的物品
        """
        timer = Timer(user_id)

        req = wineShop_pb2.QueryGoodsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._sync_union, req.index, timer)
        defer.addCallback(self._calc_seek_goods, req, timer)
        defer.addErrback(self._seek_goods_failed, req, timer)
        return defer


    def _calc_seek_goods(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.index):
            #玩家不属于联盟
            logger.debug("User is not belong to union")
            res = wineShop_pb2.QueryGoodsRes()
            res.status = 0
            res.invalid = True

        else:
            type = ShopInfo.GOODS_TYPE_UNION
            shop_id = ShopInfo.generate_id(data.id, type)
            shop = data.shop_list.get(shop_id)

            goods = []
            if not shop_business.seek_goods(data, [shop], goods, timer.now):
                raise Exception("Seek goods failed")

            resource = data.resource.get(True)
            res = self._pack_refresh_goods_response(
                    goods, shop, resource, req, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._seek_goods_succeed, req, res, timer)
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


    def _seek_goods_succeed(self, data, req, res, timer):
        response = res.SerializeToString()

        log = log_formater.output(data, "Seek union goods succeed",
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


    def refresh_goods(self, user_id, request):
        """刷新联盟商店可以购买的物品
        """
        timer = Timer(user_id)

        req = wineShop_pb2.QueryGoodsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._sync_union, req.index, timer)
        defer.addCallback(self._calc_refresh_goods, req, timer)
        defer.addErrback(self._refresh_goods_failed, req, timer)
        return defer


    def _calc_refresh_goods(self, data, req, timer):
        union = data.union.get()
        if not union.is_belong_to_target_union(req.index):
            #玩家不属于联盟
            logger.debug("User is not belong to union")
            res = wineShop_pb2.QueryGoodsRes()
            res.status = 0
            res.invalid = True

        else:
            type = ShopInfo.GOODS_TYPE_UNION
            shop_id = ShopInfo.generate_id(data.id, type)
            shop = data.shop_list.get(shop_id)

            goods = []
            if not shop_business.refresh_goods(data, [shop], goods, timer.now):
                raise Exception("Refresh goods failed")

            resource = data.resource.get(True)
            res = self._pack_refresh_goods_response(
                    goods, shop, resource, req, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._refresh_goods_succeed, req, res, timer)
        return defer


    def _refresh_goods_succeed(self, data, req, res, timer):
        response = res.SerializeToString()

        log = log_formater.output(data, "Refresh union goods succeed",
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
        defer.addCallback(self._sync_union, req.index, timer)
        defer.addCallback(self._calc_buy_goods, req, timer)
        defer.addErrback(self._buy_goods_failed, req, timer)
        return defer


    def _calc_buy_goods(self, data, req, timer):
        union = data.union.get()
        if not union.is_belong_to_target_union(req.index):
            #玩家不属于联盟
            logger.debug("User is not belong to union")
            res = wineShop_pb2.BuyGoodsRes()
            res.status = 0
            res.invalid = True

        else:
            shop_id = ShopInfo.generate_id(data.id, req.goods.type)
            shop = data.shop_list.get(shop_id)
            if not shop_business.buy_goods(data, shop, req.goods.id, timer.now):
                raise Exception("Buy Goods failed")

            compare.check_item(data, req.item)

            res = wineShop_pb2.BuyGoodsRes()
            res.status = 0
            pack.pack_resource_info(data.resource.get(True), res.resource)
            res.current_tokens = union.honor

        defer = DataBase().commit(data)
        defer.addCallback(self._buy_goods_succeed, req, res, timer)
        return defer


    def _buy_goods_succeed(self, data, req, res, timer):
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

