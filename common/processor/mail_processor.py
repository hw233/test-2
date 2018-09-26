#coding:utf8
"""
Created on 2016-07-11
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 公共邮件
"""

from utils import logger
from utils.timer import Timer
from proto import broadcast_pb2
from datalib.global_data import DataBase


class MailProcessor(object):


    def query(self, common_id, request):
        """
        """
        #TODO
        timer = Timer()

        req = broadcast_pb2.QueryBroadcastInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(common_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer



