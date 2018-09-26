#coding:utf8
"""
Created on 2015-05-12
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : City 相关处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import city_pb2
from datalib.global_data import DataBase
from app.data.city import CityInfo
from app import log_formater


class CityProcessor(object):

    def update_city_info(self, user_id, request):
        timer = Timer(user_id)

        req = city_pb2.UpdateCityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._update_city_info, req)
        defer.addCallback(self._update_city_info_succeed, req, timer)
        defer.addErrback(self._update_city_info_failed, req, timer)
        return defer


    def _update_city_info(self, data, req):
        city_id = CityInfo.generate_id(data.id, req.city.basic_id)
        city = data.city_list.get(city_id)

        if not city.change_name(req.city.name):
            raise Exception("Change city name failed")

        defer = DataBase().commit(data)
        return defer


    def _update_city_info_succeed(self, data, req, timer):
        res = city_pb2.UpdateCityRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Update city info succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_city_info_failed(self, err, req, timer):
        logger.fatal("Update city info failed[reason=%s]" % err)
        res = city_pb2.UpdateCityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update city info failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

