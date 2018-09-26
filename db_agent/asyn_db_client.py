#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 异步方式，和 MySQL 通信
"""

import time
from MySQLdb.cursors import DictCursor
from twisted.enterprise import adbapi
from utils import logger


class AsynDBClient(object):
    def __init__(self):
        self._avaiable = False


    def connect(self, args):
        self._dbpool = adbapi.ConnectionPool("MySQLdb", **args)
        self._avaiable = True


    def execute(self, commands):
        return self._dbpool.runInteraction(self._call, commands)


    def _call(self, txn, commands):
        for sql in commands:
            logger.debug("SQL execute[sql=%s]" % sql)
            txn.execute(sql)

        return txn.fetchall()


aclient = AsynDBClient()

