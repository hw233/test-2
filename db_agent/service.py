#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : db_agent 模块提供的服务
"""

from firefly.server.globalobject import GlobalObject
from firefly.server.globalobject import rootserviceHandle
from utils import logger
from db_agent.process import AgentProcessor
from db_agent.asyn_process import AsynAgentProcessor


_asyndb_conf = GlobalObject().json_config.get('asyndb')
if _asyndb_conf:
    agent = AsynAgentProcessor()
else:
    agent = AgentProcessor()


@rootserviceHandle
def query(data):
    res = agent.process(data)
    return res


@rootserviceHandle
def sort(data):
    pass

