#coding:utf-8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 通信协议类，处理和客户端通信的报文
"""

import time
import struct
from utils import logger


class DataPacker(object):
    """通信协议方法类
    提供打包、解包、校验方法
    @格式
    HEAD : version, commandID, magicNumber, reserved, bodyLength
    BODY : protobuf
    """
    version = 1

    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.seq_id = 0
        self.token = 0


    def getHeadlength(self):
        """
        uint32 version: 协议版本
        uint32 seqID: 请求序号
        uint32 token: 用户 token
        uint32 commandID: 请求 ID
        uint32 bodyLength: 请求包长度
        """
        return 20


    def unpack(self, data):
        """解析 Head
        Return:
            (result, token, command_id, body_length)
        """
        self.start_time = time.time()
        try:
            head = struct.unpack('5I', data)
        except Exception, e:
            logger.warning("Header invalid")
            return (False, 0, 0, 0)

        #check
        if (self.version <> int(head[0])):
            logger.warning("Header version error")
            return (False, 0, 0, 0)

        self.seq_id = head[1]
        self.token = int(head[2])
        command_id = head[3]
        body_length = head[4]

        return (True, self.token, self.seq_id, command_id, body_length)


    def pack(self, response, command_id):
        """打包方法
        @param response : 消息体 BODY
        @param command_id : 请求 id
        """
        length = response.__len__()
        data = struct.pack('5I', \
                self.version, \
                self.seq_id, \
                self.token, \
                command_id, \
                length)
        data = data + response

        self.end_time = time.time()
        logger.notice("Command finish[command id=%d]"
                "[token=%d][seq id=%d][comsume=%d(ms)][length=%d(Byte)]" %
                (command_id, self.token, self.seq_id,
                    (self.end_time - self.start_time) * 1000,
                    len(data)))
        return data

