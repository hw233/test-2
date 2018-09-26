#coding:utf8
"""
Created on 2016-06-01
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 数据重复查询
"""
from utils import logger
from utils import utils
from datalib.data_proxy4redis import DataProxy


class DataDupChecker(object):

    def check(self, name, field_name, field_value):
        """检查字段值是否重复
        """
        self.name = name
        self.field_name = field_name
        self.field_value = field_value
        proxy = DataProxy()
        proxy.is_value_exist(self.name, self.field_name, self.field_value)

        defer = proxy.execute()
        defer.addCallback(self._calc_result)
        return defer


    def _calc_result(self, proxy):
        return proxy.get_value_exist(self.name, self.field_name, self.field_value)

