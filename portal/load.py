#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Portal 模块逻辑入口，被 Firefly 框架的 FFServer import
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from portal.online_manager import TokenRedisAgent
from portal.command_table import init_command
from portal.protocol import DataPacker
from portal.process import user_login
from portal.process import user_logout
from portal.process import data_received


#初始化 command id 表
command_file = GlobalObject().json_config.get("command_data")
init_command(command_file)

#定制 Factory 的方法
GlobalObject().netfactory.doDataReceived = data_received
GlobalObject().netfactory.doConnectionMade = user_login
GlobalObject().netfactory.doConnectionLost = user_logout

#初始化 token redis
_token_redis_conf = GlobalObject().cache_config.get("token_redis")
TokenRedisAgent().connect(
        _token_redis_conf.get('ip'),
        _token_redis_conf.get('port'),
        _token_redis_conf.get('db'),
        _token_redis_conf.get('password'))

#配置数据解析协议
dataprotocl = DataPacker()
GlobalObject().netfactory.setDataProtocl(dataprotocl)


import portal.service
import portal.forward


logger.trace("Load portal module succeed")


