#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
"""

import time
from db_client import DBClient
from utils import logger
from proto import db_pb2
from firefly.dbentrust.dbpool import dbpool
from firefly.dbentrust.mmode import MAdmin
from firefly.dbentrust.memclient import mclient
from firefly.dbentrust.madminanager import MAdminManager

class AgentProcessor:
    def registe_admin(table_name):
        MAdminManager().registe(table_name)

    def init_mysql(self):
        hostname = 'localhost'
        user = 'yanglei'
        passwd = 'bingchennetwork'
        port = 3306
        dbname = 'san'
        charset = 'utf8'
        dbpool.initPool(host = hostname,
                        user = user,
                        passwd = passwd,
                        port = port,
                        db = dbname,
                        charset = charset)

    def init_memcached(self):
        address = ["127.0.0.1:11211"]
        hostname = 'localhost'
        mclient.connect(address, hostname)

    def __init__(self):
        pass

    def process(self, request):
        start_time = time.time()

        client = DBClient()
        client.connect()

        req = db_pb2.DBRequest()
        res = db_pb2.DBResponse()
        req.ParseFromString(request)
        res.seq_id = req.seq_id

        status = -1
        for query in req.query:
            logger.debug("process query[sql=%s]" % query)
            result = res.result.add()
            if query.type == Query.SELECT:
                status = self._select(client, query, result)
            elif query.type == Query.INSERT:
                status = self._insert(client, query, result)
            elif query.type == Query.UPDATE:
                status = self._update(client, query, result)
            elif query.type == Query.DELETE:
                status = self._delete(client, query, result)

            if status != 0:
                break

        client.commit()

        res.status = status
        consume_time = int((time.time() - start_time) * 1000)
        logger.notice("Query[req=%s][res=%s][consume=%d ms]" % (req, res, consume_time))

        return res.SerializeToString()

    def _select(self, client, query, result):
        result.user_id = query.user_id
        result.type = query.type

        tblname = query.table_name

        con_string = ""
        for item in query.condition:
            if con_string != "":
                con_string += " AND "
            if (item.type == Item.STRING):
                con_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                con_string += str(item.key) + "=" + str(item.value)

        expr_string = ""
        for item in query.expr:
            if expr_string != "":
                expr_string += ","
            expr_string += str(item.key)

        res_list = client.select(tblname, expr_string, con_string)

        result.table.name = tblname
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

    def _insert(self, client, query, result):
        result.user_id = query.user_id
        result.type = query.type

        tblname = query.table_name

        expr_string = ""
        for item in query.expr:
            if expr_string != "":
                expr_string += ","
            if (item.type == Item.STRING):
                expr_string += "\"" + item.value + "\""
            else:
                expr_string += str(item.value)

        num = client.insert(tblname, expr_string)
        if num == 0:
            logger.warning("Failed insert into DB")
            return -1

        return 0

    def _update(self, client, query, result):
        result.user_id = query.user_id
        result.type = query.type

        tblname = query.table_name

        con_string = ""
        for item in query.condition:
            if con_string != "":
                con_string += " AND "
            if (item.type == Item.STRING):
                con_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                con_string += str(item.key) + "=" + str(item.value)

        expr_string = ""
        for item in query.expr:
            if expr_string != "":
                expr_string += ","
            if (item.type == Item.STRING):
                expr_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                expr_string += str(item.key) + "=" + str(item.value)

        num = client.update(tblname, expr_string, con_string)
        if num == 0:
            logger.warning("Failed update DB")
            return -1

        return 0

    def _delete(self, client, query, result):
        result.user_id = query.user_id
        result.type = query.type

        tblname = query.table_name

        con_string = ""
        for item in query.condition:
            if con_string != "":
                con_string += " AND "
            if (item.type == Item.STRING):
                con_string += str(item.key) + "=\"" + str(item.value) + "\""
            else:
                con_string += str(item.key) + "=" + str(item.value)

        num = client.delete(tblname, con_string)
        if num == 0:
            logger.warning("Failed delete from DB")
            return -1

        return 0


