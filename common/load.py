#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : common模块逻辑入口
"""

from twisted.internet import reactor
from firefly.server.globalobject import GlobalObject
from utils import logger
from datalib.data_proxy4redis import DataRedisAgent
from datalib.table import TableDescription
from datalib.data_loader import load_data
from datalib.global_data import DataBase
from common.common_view import CommonData
import common.service


_redis_conf = GlobalObject().cache_config.get('data_redis')
DataRedisAgent().connect(
        _redis_conf.get('ip'),
        _redis_conf.get('port'),
        _redis_conf.get('db'),
        _redis_conf.get('password'))

#读入Excel
_data_conf = GlobalObject().json_config.get('dataconf')
load_data(_data_conf)

#初始化 DB
_table_conf = GlobalObject().json_config.get("tableconf")
table = TableDescription()
table.parse(_table_conf)
GlobalObject().table_desc = table

DataBase().register_datatype(CommonData)


logger.trace("Load Common module succeed")

