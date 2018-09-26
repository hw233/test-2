#coding:utf8
"""
Created on 2016-06-01
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 数据查询
"""

from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy


class DataDumper(object):

    def get_all(self, name, field_name):
        """获取字段所有值
        """
        self.name = name
        self.field_name = field_name
        proxy = DataProxy()
        proxy.get_all_values(self.name, self.field_name)

        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        ids = []
        for id in proxy.get_all_values_result(self.name, self.field_name):
            ids.append(id)
        return ids



