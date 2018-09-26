#coding:utf8
"""
Created on 2016-05-05
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief:  使用兑换码
"""

from utils import logger
from utils.timer import Timer
from proto import user_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app.data.item import ItemInfo
from app.data.cdkey import CDkeyRedisAgent
from app.business import item as item_business
from app import log_formater


class CDkeyProcessor(object):

    def use_cdkey(self, user_id, request):
        """使用兑换码 CDKEY"""
        timer = Timer(user_id)
        req = user_pb2.UseCDkeyReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_use_cdkey, req, timer)
        defer.addErrback(self._use_cdkey_failed, req, timer)
        return defer


    def _calc_use_cdkey(self, data, req, timer):
        """兑换奖励
        """
        res = self._check_and_use_cdkey(data, req, timer)
        defer = DataBase().commit(data)
        defer.addCallback(self._use_cdkey_succeed, req, res, timer)
        return defer


    def _check_and_use_cdkey(self, data, req, timer):
        """校验并使用激活码
        Returns:
            response
        """
        user = data.user.get()
        goodybag_id = CDkeyRedisAgent().get(req.key)
        if goodybag_id == 0:
            logger.warning("CDkey invalid[key=%s]" % req.key)
            return self._pack_invalid_cdkey_response(    #无效激活码
                    data_loader.ServerDescKeyInfo_dict["invalid_cdkey"].value.encode("utf-8"))

        if not user.is_cdkey_valid(goodybag_id):
            logger.warning("CDkey can not be used[key=%s]" % req.key)
            return self._pack_invalid_cdkey_response(    #同一种礼包只能领取一次
                    data_loader.ServerDescKeyInfo_dict["cdkey_get_once"].value.encode("utf-8"))

        if not CDkeyRedisAgent().finish(req.key):
            logger.warning("Delete cdkey failed[key=%s]" % req.key)
            return self._pack_invalid_cdkey_response(    #激活码已失效
                    data_loader.ServerDescKeyInfo_dict["cdkey_failure"].value.encode("utf-8"))

        user.use_cdkey(goodybag_id)
        logger.notice("Use valid cdkey[user id=%d][key=%s][goodybag id=%d]" %
                (data.id, req.key, goodybag_id))
        return self._use_valid_cdkey(data, req.key, goodybag_id)


    def _use_valid_cdkey(self, data, key, goodybag_id):
        """使用有效的 cdkey，获得奖励
        """
        bag = data_loader.GoodyBagBasicInfo_dict[goodybag_id]
        resource = data.resource.get()
        original_gold = resource.gold
        if bag.gold > 0:
            resource.gain_gold(bag.gold)
            log = log_formater.output_gold(data, bag.gold, log_formater.BAG_GOLD,
                "Gain gold frome bag", before_gold = original_gold)
            logger.notice(log)

        if bag.money > 0:
            resource.gain_money(bag.money)
        if bag.food > 0:
            resource.gain_food(bag.food)

        assert len(bag.itemsBasicId) == len(bag.itemsNum)
        item_list = []
        for i in range(0, len(bag.itemsBasicId)):
            item_list.append((bag.itemsBasicId[i], bag.itemsNum[i]))

        if not item_business.gain_item(data, item_list, "cdkey reward", log_formater.CDKEY_REWARD):
            raise Exception("Gain item failed")

        return self._pack_valid_cdkey_response(data, goodybag_id, resource, item_list)


    def _pack_invalid_cdkey_response(self, reason):
        """封装无效激活码的响应
        """
        res = user_pb2.UseCDkeyRes()
        res.status = 0
        res.reason = reason
        return res


    def _pack_valid_cdkey_response(self, data, goodybag_id, resource, item_list):
        """封装响应
        """
        res = user_pb2.UseCDkeyRes()
        res.status = 0

        res.goodybag_id = goodybag_id
        pack.pack_resource_info(resource, res.resource)
        for (basic_id, num) in item_list:
            item_id = ItemInfo.generate_id(data.id, basic_id)
            item = data.item_list.get(item_id)
            pack.pack_item_info(item, res.items.add())

        return res


    def _use_cdkey_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Use cdkey succeed[id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _use_cdkey_failed(self, err, req, timer):
        logger.fatal("Use cdkey failed[reason=%s]" % err)

        res = user_pb2.UseCDkeyRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Use cdkey failed[id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


