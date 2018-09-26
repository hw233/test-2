#coding:utf8
"""
Created on 2017-11-18
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 国家势力处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import monarch_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from common.business import console as console_business


class CountryProcessor(object):

    def query_suggested_country(self, common_id, request):
        """查询推荐的国家势力信息
        """
        timer = Timer(common_id)

        req = monarch_pb2.QuerySuggestedCountryReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_query_suggested_country, req, timer)
        defer.addErrback(self._query_suggested_country_failed, req, timer)
        return defer


    def _calc_query_suggested_country(self, data, req, timer):
        """
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        country = data.country.get()

        suggested_country = country.get_country_of_least_weight()
        reward_gold = int(float(data_loader.OtherBasicInfo_dict["reward_gold_for_choose_country"].value))

        res = monarch_pb2.QuerySuggestedCountryRes()
        res.status = 0
        res.country = suggested_country
        res.reward_gold = reward_gold

        defer = DataBase().commit(data)
        defer.addCallback(self._query_suggested_country_succeed, req, res, timer)
        return defer


    def _query_suggested_country_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query suggested country succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _query_suggested_country_failed(self, err, req, timer):
        logger.fatal("Query suggested country failed[reason=%s]" % err)
        res = monarch_pb2.QuerySuggestedCountryRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query suggested country failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def update_country(self, common_id, request):
        """更改国家势力
        """
        timer = Timer(common_id)

        req = monarch_pb2.UpdateCountryReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_update_country, req, timer)
        defer.addErrback(self._update_country_failed, req, timer)
        return defer


    def _calc_update_country(self, data, req, timer):
        """
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        country = data.country.get()

        if req.old_country == 1:
            country.reduce_wei_weight()
        elif req.old_country == 2:
            country.reduce_shu_weight()
        else:
            country.reduce_wu_weight()

        if req.new_country == 1:
            country.add_wei_weight()
        elif req.new_country == 2:
            country.add_shu_weight()
        else:
            country.add_wu_weight()

        res = monarch_pb2.UpdateCountryRes()
        res.status = 0

        defer = DataBase().commit(data)
        defer.addCallback(self._update_country_succeed, req, res, timer)
        return defer


    def _update_country_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Update country succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _update_country_failed(self, err, req, timer):
        logger.fatal("Update country failed[reason=%s]" % err)
        res = monarch_pb2.UpdateCountryRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update country failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


