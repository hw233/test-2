#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 处理物品相关的请求
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import speed_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.item import ItemInfo
from app.data.building import BuildingInfo
from app.data.technology import TechnologyInfo
from app.business import item as item_business
import pdb


class SpeedProcessor(object):

    def use_speed_item(self, user_id, request):
        """使用加速物品
        加速建筑建造、科技研究
        """
        timer = Timer(user_id)

        req = speed_pb2.UseSpeedItemReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_use_speed_item, req, timer)
        defer.addErrback(self._use_speed_item_failed, req, timer)
        return defer


    def _calc_use_speed_item(self, data, req, timer):
        res = speed_pb2.UseSpeedItemRes()
        res.status = 0

        building = None
        technology = None
        if req.HasField("building"):
            building_id = BuildingInfo.generate_id(
                    data.id, req.building.city_basic_id,
                    req.building.location_index, req.building.basic_id)
            building = data.building_list.get(building_id)

        elif req.HasField("tech"):
            technology_id = TechnologyInfo.generate_id(
                    data.id, req.tech.basic_id, req.tech.type)
            technology = data.technology_list.get(technology_id)

        item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
        item = data.item_list.get(item_id)

        use_num = item.num - req.item.num
        if not item_business.use_speed_item(item, use_num, building, technology):
            logger.warning("Use speed item failed")
            res.return_ret = speed_pb2.UseSpeedItemRes.SPEED_ITEM_ERROR
        else:
            res.return_ret = 0
 
        compare.check_item(data, req.item)

        defer = DataBase().commit(data)
        defer.addCallback(self._use_speed_item_succeed, req, res, timer)
        return defer


    def _use_speed_item_succeed(self, data, req, res, timer):
        if req.HasField("building"):
            building_id = BuildingInfo.generate_id(
                    data.id, req.building.city_basic_id,
                    req.building.location_index, req.building.basic_id)
            building = data.building_list.get(building_id)
            pack.pack_building_info(building, res.building, timer.now)

        elif req.HasField("tech"):
            technology_id = TechnologyInfo.generate_id(
                    data.id, req.tech.basic_id, req.tech.type)
            technology = data.technology_list.get(technology_id)
            pack.pack_technology_info(technology, res.tech, timer.now)

        response = res.SerializeToString()
        log = log_formater.output(data, "Use resource package succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _use_speed_item_failed(self, err, req, timer):
        logger.fatal("Use speed item failed[reason=%s]" % err)

        res = speed_pb2.UseSpeedItemRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Use speed item failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


