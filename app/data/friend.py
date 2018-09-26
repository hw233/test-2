#coding:utf8
"""
Created on 2015-02-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 好友相关逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader



class FriendInfo(object):
    def __init__(self, id = 0,
            user_id = 0, friend_index = 0, friend_id = 0, message_index_list = ''):
        self.id = id
        self.user_id = user_id
        self.friend_index = friend_index
        self.friend_id = friend_id
        self.message_index_list = message_index_list

    @staticmethod                                                                                                                                                                          
    def generate_id(user_id, friend_index):
        id = user_id << 32 | friend_index
        return id


    @staticmethod
    def create(user_id, friend_id, friend_index):
        """创建一个好友关系
        Args:
            user_id[int]: 用户 id
            friend_index[int]: 在好友列表中的位置
            message_index[int]: 和当前好友聊天的邮件序号
        Returns:
            friendinfo[FriendInfo] 好友记录
        """

        #处理之后的数据
        id = FriendInfo.generate_id(user_id, friend_index)
        friendinfo = FriendInfo(id, user_id, friend_index, friend_id)
        return friendinfo


    def get_message_index(self):
        """获取消息的index
        """                                                                                                                                                                                
        return utils.split_to_int(self.message_index_list)
