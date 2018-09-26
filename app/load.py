#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : App 模块逻辑入口，被 Firefly 框架的 FFServer import
"""

from twisted.internet import reactor
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.chat_pool import ChatPool
from datalib.data_proxy4redis import DataRedisAgent
from datalib.data_loader import load_data
from datalib.table import TableDescription
from datalib.global_data import DataBase
from app.user_view import UserData
from app.basic_view import BasicData
from app.core.pay import PayRedisAgent
from app.data.cdkey import CDkeyRedisAgent
import app.service
from app.business import event
from app.core.pay import PayLogic


#初始化 Redis 连接
_redis_conf = GlobalObject().cache_config.get('data_redis')
DataRedisAgent().connect(
        _redis_conf.get('ip'),
        _redis_conf.get('port'),
        _redis_conf.get('db'),
        _redis_conf.get('password'))

_pay_redis_conf = GlobalObject().cache_config.get('pay_redis')
PayRedisAgent().connect(
        _pay_redis_conf.get('ip'),
        _pay_redis_conf.get('port'),
        _pay_redis_conf.get('db'),
        _pay_redis_conf.get('password'))

_cdkey_redis_conf = GlobalObject().cache_config.get('cdkey_redis')
CDkeyRedisAgent().connect(
        _cdkey_redis_conf.get('ip'),
        _cdkey_redis_conf.get('port'),
        _cdkey_redis_conf.get('db'),
        _cdkey_redis_conf.get('password'))


#读入所有 Excel
_data_conf = GlobalObject().json_config.get('dataconf')
load_data(_data_conf)

#初始化 DB
_table_conf = GlobalObject().json_config.get("tableconf")
table = TableDescription()
table.parse(_table_conf)
GlobalObject().table_desc = table

DataBase().register_datatype(UserData)
DataBase().register_basic_datatype(BasicData)


_pay_conf = GlobalObject().json_config.get("payconf")
PayLogic().init_pay(_pay_conf)

_chat_conf = GlobalObject().json_config.get("chatconf")
ChatPool().load_conf(_chat_conf)


event.register_lucky_event()


logger.trace("Load App module succeed")

# def test_thread(x):
#     print "x"
#     print x
#     while (1):
#         print "run in thread"
#         import time
#         time.sleep(1)

# reactor.callFromThread(test_thread, 3)

