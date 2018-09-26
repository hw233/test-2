#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 异步通信
"""

import time
from twisted.internet.defer import Deferred
from utils import logger
from proto import db_pb2
from db_agent.asyn_db_client import aclient


class AsynAgentProcessor:


    def process(self, request):
        start_time = time.time()

        req = db_pb2.DBRequest()
        res = db_pb2.DBResponse()
        req.ParseFromString(request)
        res.seq_id = req.seq_id

        defer = Deferred()

        assert len(req.query) > 0
        #一个请求中，不允许既有读，又有写
        if req.query[0].type == db_pb2.Query.SELECT:
            defer.addCallback(self._read, req, res)
        else:
            defer.addCallback(self._write, req, res)

        defer.addCallback(self._process_succeed, req, res, start_time)
        defer.addErrback(self._process_failed, req, res, start_time)

        defer.callback(0)
        return defer


    def _process_succeed(self, status, req, res, start_time):
        assert status == 0

        res.status = 0
        consume_time = int((time.time() - start_time) * 1000)
        logger.notice("Query[req=%s][res=%s][consume=%d ms]" % (req, res, consume_time))

        return res.SerializeToString()


    def _process_failed(self, err, req, res, start_time):
        logger.fatal("Query failed[reason=%s]" % err)

        res.status = -1
        res.ClearField("result")
        consume_time = int((time.time() - start_time) * 1000)
        logger.notice("Query[req=%s][res=%s][consume=%d ms]" % (req, res, consume_time))

        return res.SerializeToString()


    def _read(self, status, req, res):
        assert status == 0

        defer = Deferred()

        for query in req.query:
            result = res.result.add()
            defer.addCallback(self._single_read, query, result)

        defer.callback(0)
        return defer


    def _single_read(self, status, query, result):
        assert status == 0

        result.user_id = query.user_id
        result.type = query.type
        result.table.name = query.table_name

        commands = []
        sql = self._pack_select(query)
        commands.append(sql)
        defer = aclient.execute(commands)
        defer.addCallback(self._parse_select, query, result)

        return defer


    def _pack_select(self, query):
        con_string = ""
        for item in query.condition:
            if con_string != "":
                con_string += " AND "
            if (item.type == db_pb2.Item.STRING):
                con_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                con_string += str(item.key) + "=" + str(item.value)

        expr_string = ""
        for item in query.expr:
            if expr_string != "":
                expr_string += ","
            expr_string += str(item.key)

        sql_string = "SELECT " + expr_string + \
                " FROM " + query.table_name + \
                " WHERE " + con_string
        return sql_string


    def _parse_select(self, res_list, query, result):
        for res_row in res_list:
            row = result.table.rows.add()
            index = 0
            for query_col in query.expr:
                col = row.cols.add()
                col.key = query_col.key
                col.type = query_col.type
                if isinstance(res_row[index], unicode):
                    print res_row[index]
                    col.value = res_row[index].encode('utf-8', 'ignore')
                else:
                    col.value = str(res_row[index])
                index += 1

        return 0


    def _write(self, status, req, res):
        assert status == 0

        commands = []
        for query in req.query:
            result = res.result.add()
            result.user_id = query.user_id
            result.type = query.type
            result.table.name = query.table_name

            if query.type == db_pb2.Query.INSERT:
                sql = self._pack_insert(query)
            elif query.type == db_pb2.Query.UPDATE:
                sql = self._pack_update(query)
            elif query.type == db_pb2.Query.DELETE:
                sql = self._pack_delete(query)
            commands.append(sql)

        #保证所有的写操作在一个事物内完成
        defer = aclient.execute(commands)
        defer.addCallback(self._parse_write)
        return defer


    def _parse_write(self, res_list):
        return 0


    def _pack_update(self, query):
        con_string = ""
        for item in query.condition:
            if con_string != "":
                con_string += " AND "
            if (item.type == db_pb2.Item.STRING):
                con_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                con_string += str(item.key) + "=" + str(item.value)

        expr_string = ""
        for item in query.expr:
            if expr_string != "":
                expr_string += ","
            if (item.type == db_pb2.Item.STRING):
                expr_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                expr_string += str(item.key) + "=" + str(item.value)

        sql_string = "UPDATE " + query.table_name + \
                " SET " + expr_string + \
                " WHERE " + con_string;
        return sql_string


    def _pack_insert(self, query):
        expr_string = ""
        for item in query.expr:
            if expr_string != "":
                expr_string += ","
            if (item.type == db_pb2.Item.STRING):
                expr_string += "\"" + item.value + "\""
            else:
                expr_string += str(item.value)

        sql_string = "INSERT " + \
                " INTO " + query.table_name + \
                " VALUES(" + expr_string +")"
        return sql_string


    def _pack_delete(self, query):
        con_string = ""
        for item in query.condition:
            if con_string != "":
                con_string += " AND "
            if (item.type == db_pb2.Item.STRING):
                con_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                con_string += str(item.key) + "=" + str(item.value)

        sql_string = "DELETE " + \
                " FROM " + query.table_name + \
                " WHERE " + con_string;
        return sql_string


