#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 聊天信息
"""

import json
from firefly.utils.singleton import Singleton
from utils import logger


class ChatPool(object):
    """聊天信息集合
    """
    __metaclass__ = Singleton


    def __init__(self):
        self._chat = {}
        self.admin_username = None
        self.admin_password = None


    def load_conf(self, conf_path):
        """读入配置
        """
        config = json.load(open(conf_path, 'r'))

        #读入不同类型聊天室配置
        type_conf = config.get("type")
        for chat_type in type_conf:
            chat = ChatRoom(
                    type_conf[chat_type].get("room").encode("utf-8"),
                    type_conf[chat_type].get("hostname").encode("utf-8"),
                    type_conf[chat_type].get("port"),
                    type_conf[chat_type].get("service").encode("utf-8"),
                    type_conf[chat_type].get("password").encode("utf-8"),
                    type_conf[chat_type].get("available"))
            self._chat[chat_type] = chat

        #读入聊天室管理员帐号配置
        admin_conf = config.get("admin")
        self.admin_username = admin_conf.get("username").encode("utf-8")
        self.admin_password = admin_conf.get("password").encode("utf-8")


    def get_world_chat_info(self):
        return self._chat["world"]


    def get_union_chat_info(self):
        return self._chat["union"]


class ChatRoom(object):
    """聊天室信息
    """

    def __init__(self, room, hostname, port, service, password, available):
        self.room = room
        self.hostname = hostname
        self.port = port
        self.service = service
        self.password = password
        self.available = available


    def get_roomname(self):
        return "%s@%s" % (self.room, self.service)


    def get_jid(self, username):
        return "%s@%s" % (username, self.hostname)


