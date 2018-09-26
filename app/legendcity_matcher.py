#coding:utf8
"""
Created on 2016-05-18
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 玩家信息匹配逻辑
"""

from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy
from app.data.rival import RivalInfo
from app.data.legendcity import LegendCityInfo


class LegendCityMatcher(object):
    """史实城信息查询
    根据 city_id 查询史实城信息：slogan、tax
    """

    def __init__(self):
        self.city = None


    def match(self, data, city_id):
        """进行匹配
        """
        proxy = DataProxy()
        proxy.search("unitcity", city_id)

        defer = proxy.execute()
        defer.addCallback(self._calc_result, city_id)
        return defer


    def _calc_result(self, proxy, city_id):
        self.city = proxy.get_result("unitcity", city_id)
        return self

