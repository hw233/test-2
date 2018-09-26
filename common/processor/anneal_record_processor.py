#coding:utf8
"""
Created on 2016-09-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 试炼场记录数据处理逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import broadcast_pb2
from proto import anneal_pb2
from datalib.global_data import DataBase
from common.business import anneal_record as anneal_record_business
from common.business import console as console_business


class AnnealRecordProcessor(object):

    def query_anneal_record(self, common_id, request):
        """查询信息
        """
        timer = Timer(common_id)

        req = anneal_pb2.QueryAnnealRecordReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_query_anneal_record, req, timer)
        defer.addErrback(self._query_anneal_record_failed, req, timer)
        return defer


    def _calc_query_anneal_record(self, data, req, timer):
        """查询逻辑
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        record = anneal_record_business.query_anneal_record(data, req.floor)

        res = anneal_pb2.QueryAnnealRecordRes()
        res.status = 0
       
        record_message = res.records.add()
        record_message.type = 1
        record_message.name = record.get_readable_first_name()
        record_message.level = record.first_level
        record_message.icon_id = record.first_icon_id
        record_message.finish_passed_time = timer.now - record.first_finished_time
        
        record_message = res.records.add()
        record_message.type = 2
        record_message.name = record.get_readable_fast_name()
        record_message.level = record.fast_level
        record_message.icon_id = record.fast_icon_id
        record_message.finish_passed_time = timer.now - record.fast_finished_time
        record_message.cost_time = record.fast_cost_time

        defer = DataBase().commit(data)
        defer.addCallback(self._query_anneal_record_succeed, req, res, timer)
        return defer


    def _query_anneal_record_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query anneal record succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _query_anneal_record_failed(self, err, req, timer):
        logger.fatal("Query anneal record failed[reason=%s]" % err)
        res = anneal_pb2.QueryAnnealRecordRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query anneal record failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def update_anneal_record(self, common_id, request):
        """更新试炼记录信息
        """
        timer = Timer(common_id)

        req = anneal_pb2.UpdateAnnealRecordReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_update_anneal_record, req, timer)
        defer.addErrback(self._update_anneal_record_failed, req, timer)
        return defer


    def _calc_update_anneal_record(self, data, req, timer):
        """更新逻辑
        """
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")

        for record in req.records:
            if not anneal_record_business.update_anneal_record(data, req.floor, 
                    record.type, record.name, record.level, record.icon_id, 
                    record.finish_passed_time, record.cost_time, timer.now):
                raise Exception("Update anneal record failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._update_anneal_record_succeed, req, timer)
        return defer


    def _update_anneal_record_succeed(self, data, req, timer):
        res = anneal_pb2.UpdateAnnealRecordRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("update anneal record succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _update_anneal_record_failed(self, err, req, timer):
        logger.fatal("Update anneal record failed[reason=%s]" % err)
        res = anneal_pb2.UpdateAnnealRecordRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update anneal record failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


