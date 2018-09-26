#coding:utf8
"""
Created on 2015-02-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 好友消息逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.friend import FriendInfo
MESSAGE_STATUS_UNREAD = 1  #未读
MESSAGE_STATUS_READ = 2    #已读

OWN = 1     #自己发的消息
OTHER = 2   #别人发的消息
class MessageInfo(object):
    def __init__(self, id = 0, user_id = 0, friend_index = 0, message_index = 0,
            content = '', status = MESSAGE_STATUS_READ, message_from = OWN):
        self.id = id
        self.user_id = user_id
        self.friend_index = friend_index
        self.message_index = message_index
        self.content = content
        self.status = status
        self.message_from = message_from
    @staticmethod
    def generate_id(user_id, friend_index, message_index):
        id = user_id << 32 | friend_index << 12 | message_index
        return id

    @staticmethod
    def create(user_id, friend_index, message_index, content, status, message_from):
        id = MessageInfo.generate_id(user_id, friend_index, message_index)
        message = MessageInfo(id, user_id, friend_index, message_index, content, status, message_from)
        return message
