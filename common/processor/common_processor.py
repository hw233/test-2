#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : common逻辑
"""

from utils import logger
from utils.timer import Timer
from proto import internal_pb2
from proto import activity_pb2
from datalib.global_data import DataBase
from common.business import cat as cat_business
from common.business import console as console_business

class CommonProcessor(object):

    def delete_common(self, common_id, request):
        """删除common信息
        """
        timer = Timer(common_id)

        req = internal_pb2.DeleteCommonReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_delete_common, req, timer)
        defer.addCallback(self._delete_common_succeed, req, timer)
        defer.addErrback(self._delete_common_failed, req, timer)
        return defer


    def _calc_delete_common(self, data, req, timer):
        """
        """
        if not data.is_valid():
            return data

        data.delete()
        defer = DataBase().commit(data)
        defer.addCallback(self._delete_cache)
        return defer


    def _delete_cache(self, data):
        DataBase().clear_data(data)
        return data


    def _delete_common_succeed(self, data, req, timer):
        res = internal_pb2.DeleteCommonRes()
        res.status = 0
        response = res.SerializeToString()

        logger.notice("Delete common succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _delete_common_failed(self, err, req, timer):
        logger.fatal("Delete common failed[reason=%s]" % err)
        res = internal_pb2.DeleteCommonRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete common failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def add_cat(self, common_id, request):
        """添加招财猫获得元宝记录"""
        logger.notice("===============add")
        timer = Timer(common_id)
        req = internal_pb2.InternalCatReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_add, req, common_id, timer)
        defer.addErrback(self._add_failed, req, timer)
        return defer


    def _calc_add(self, data, req, common_id, timer):
        cat_list = data.cat_list.get_all()
        index = 1
        if len(cat_list) == 0:
            index = 1
        else:
            index = cat_list[-1].index + 1
        logger.notice("index =%s"%index)
        if not data.is_valid():
            if not console_business.init_console(data, timer.now):
                raise Exception("Init console failed")
        if not cat_business.add_cat(data, common_id, req.user_id, req.name, req.gold, index):                                                                                                   
            raise Exception("Add cat failed")
        logger.notice("===============1")
        defer = DataBase().commit(data)
                                                                                                                                                            
        logger.notice("===============2")
        defer.addCallback(self._add_succeed, req, timer)                                                                                                                                   
        return defer  

    def _add_succeed(self, data, req, timer):
        res = internal_pb2.InternalCatRes()                                                                                                                                          
        res.status = 0                                                                                                                                                                     
        response = res.SerializeToString()                                                                                                                                                 
        logger.notice("Add cat succeed[req=%s][res=%s][consume=%d]" %                                                                                                                
                (req, res, timer.count_ms()))                                                                                                                                              
        return response

    def _add_failed(self, err, req, timer):                                                                                                                                                
        logger.fatal("Add cat failed[reason=%s]" % err)                                                                                                                              
        res = internal_pb2.InternalCatRes()                                                                                                                                          
        res.status = -1                                                                                                                                                                    
        response = res.SerializeToString()                                                                                                                                                 
        logger.notice("Add cat failed[req=%s][res=%s][consume=%d]" %                                                                                                                 
                (req, res, timer.count_ms()))                                                                                                                                              
        return response     

    def query_cat(self, common_id, request):
        """查询招财猫获得元宝记录"""
        timer = Timer(common_id)
        req = activity_pb2.QueryCatReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(common_id) 
        defer.addCallback(self._calc_query_cat, req, common_id, timer)                                                                                                                           
        defer.addErrback(self._query_cat_failed, req, timer)                                                                                                                                     
        return defer

    def _calc_query_cat(self, data, req, common_id, timer):
        cat_list = data.cat_list.get_all()
        if len(cat_list) == 0:
            res = activity_pb2.QueryCatRes()                                                                                                                                                  
            res.status = 0 
            return  self._query_cat_succeed(data, req, res, timer)
        logger.notice("cat_len=%d"%len(cat_list))
        candidates = []
        candidates = cat_list[::-1]
        res = activity_pb2.QueryCatRes()
        res.status = 0
        for candidate in candidates:
            cat = res.cats.add()
            cat.name = candidate.name
            cat.gold = candidate.gold
        defer = DataBase().commit(data)
        defer.addCallback(self._query_cat_succeed, req, res, timer)
        return defer
     
    def _query_cat_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query cat succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _query_cat_failed(self, err, req, timer):
        logger.fatal("Query cat failed[reason=%s]" % err)
        res = activity_pb2.QueryCatRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query cat failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


         

      
