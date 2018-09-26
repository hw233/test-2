#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 和 MySQL 通信
"""

import time
from MySQLdb.cursors import DictCursor
from firefly.dbentrust.dbpool import dbpool
from utils import logger


class DBClient(object):
    def __init__(self):
        pass

    def connect(self):
        self._conn = dbpool.connection()

    def commit(self):
        self._conn.commit()
        self._conn.close()
        self._conn = None

    def select(self, table_name, expr_string, condition_string):
        """查询
        Returns:
            查询结果的 list
        """
        sql_string = "SELECT " + expr_string + \
                " FROM " + table_name
        if len(condition_string) > 0:
            sql_string = sql_string + \
                " WHERE " + condition_string
        start_time = time.time()
        cursor = self._conn.cursor()
        num = cursor.execute(sql_string)
        result = cursor.fetchall()
        consume_time = int((time.time() - start_time) * 1000)
        logger.debug("SQL execute[sql=%s][consume=%d ms]" % (sql_string, consume_time))
        cursor.close()
        return result

    def insert(self, table_name, expr_string):
        """插入
        Returns:
            插入成功的条目数
        """
        sql_string = "INSERT " + \
                " INTO " + table_name + \
                " VALUES(" + expr_string +")"
        start_time = time.time()
        cursor = self._conn.cursor()
        num = cursor.execute(sql_string)
        consume_time = int((time.time() - start_time) * 1000)
        logger.debug("SQL execute[sql=%s][consume=%d ms]" % (sql_string, consume_time))
        cursor.close()
        return num

    def update(self, table_name, expr_string, condition_string):
        """更新
        Returns:
            更新成功的条目数
        """
        sql_string = "UPDATE " + table_name + \
                " SET " + expr_string + \
                " WHERE " + condition_string;
        start_time = time.time()
        cursor = self._conn.cursor()
        cursor.execute(sql_string)
        num = cursor.fetchall()
        consume_time = int((time.time() - start_time) * 1000)
        logger.debug("SQL execute[sql=%s][consume=%d ms]" % (sql_string, consume_time))
        cursor.close()
        return num

    def delete(self, table_name, condition_string):
        """删除
        Returns:
            删除成功的条目数
        """
        sql_string = "DELETE " + \
                " FROM " + table_name + \
                " WHERE " + condition_string;
        start_time = time.time()
        cursor = self._conn.cursor()
        num = cursor.execute(sql_string)
        consume_time = int((time.time() - start_time) * 1000)
        logger.debug("SQL execute[sql=%s][consume=%d ms]" % (sql_string, consume_time))
        cursor.close()
        return num


