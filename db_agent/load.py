#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
"""

from firefly.server.globalobject import GlobalObject
from firefly.dbentrust.dbpool import dbpool
from utils import logger
from db_agent.asyn_db_client import aclient
import db_agent.service
import db_agent.process


_asyndb_conf = GlobalObject().json_config.get('asyndb')
if _asyndb_conf:
    aclient.connect(dbpool.config)


