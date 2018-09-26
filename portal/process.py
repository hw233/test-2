#coding:utf-8
"""
Created on 2015-01-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
"""

from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from portal.online_manager import OnlineManager


def user_login(conn):
    """
    玩家建立连接 connect
    """
    logger.notice("User connect[conn=%d][addr=%s:%d]" %
            (conn.transport.sessionno, conn.transport.client[0], conn.transport.client[1]))


def user_logout(conn):
    """玩家断开连接
    """
    session_key = OnlineManager().delete_user(conn)
    logger.notice("User disconnect[conn=%d][addr=%s:%d]" %
            (conn.transport.sessionno, conn.transport.client[0], conn.transport.client[1]))


def data_received(conn, token, seq_id, command_id, data):
    """收到客户端数据时的处理
    1 更新用户活跃信息
    2 转发请求到具体处理逻辑
    """
    user_id = OnlineManager().update_user(token, conn)
    if user_id == -1:
        logger.warning("Update user failed[token=%d][conn=%d][addr=%s:%d]" %
                (token, conn.transport.sessionno,
                    conn.transport.client[0], conn.transport.client[1]))
        return ""

    logger.notice("Command received[command id=%d]"
                "[token=%d][seq id=%d][length=%d(Byte)]" %
                (command_id, token, seq_id, len(data)))

    res = OnlineManager().fetch_response(user_id, seq_id)
    if res != None:
        #此次请求的seq_id与上一条相同，则直接返回上一次结果，不向app转发请求
        #避免二次请求
        defer = Deferred()
        defer.addCallback(return_response, res)
        defer.callback(True)
        return defer

    defer = GlobalObject().netfactory.service.callTarget(command_id, seq_id, user_id, conn, data)
    return defer


def return_response(data, res):
    return res

