#coding:utf8
"""
Created on 2016-05-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Unit 模块逻辑入口
"""

from twisted.internet import reactor
from firefly.server.globalobject import GlobalObject
from utils import logger
from datalib.data_proxy4redis import DataRedisAgent
from datalib.data_loader import load_data
from datalib.table import TableDescription
from datalib.global_data import DataBase
from unit.city_view import CityData
import unit.service


_redis_conf = GlobalObject().cache_config.get('data_redis')
DataRedisAgent().connect(
        _redis_conf.get('ip'),
        _redis_conf.get('port'),
        _redis_conf.get('db'),
        _redis_conf.get('password'))

_data_conf = GlobalObject().json_config.get('dataconf')
load_data(_data_conf)


_table_conf = GlobalObject().json_config.get("tableconf")
table = TableDescription()
table.parse(_table_conf)
GlobalObject().table_desc = table

DataBase().register_datatype(CityData)


logger.trace("Load Unit module succeed")

