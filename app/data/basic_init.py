#coding:utf8
"""
Created on 2016-09-21
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 
"""

from utils import logger
from utils import utils


class BasicInitInfo(object):
    """
    """

    __slots__ = [
            "basic_id",
            "init_activities"
            ]


    def __init__(self):
        self.basic_id = 0
        self.init_activities = ''

    @staticmethod
    def create(basic_id):
        """创建
        """
        init = BasicInitInfo()
        init.basic_id = basic_id

        init.init_activities = ""
        return init


    def add_init_activities(self, id_list):
        """添加新用户初始活动id
        """
        init_activities = utils.split_to_int(self.init_activities)
        for add_id in id_list:
            is_exist = False
            for id in init_activities:
                if id == add_id:
                    is_exist = True
                    break

            if not is_exist:
                init_activities.append(add_id)

        self.init_activities = utils.join_to_string(init_activities)


    def delete_init_activities(self, id_list):
        """删除新用户初始活动id
        """
        init_activities = utils.split_to_int(self.init_activities)
        for delete_id in id_list:
            for id in init_activities:
                if id == delete_id:
                    init_activities.remove(delete_id)

        self.init_activities = utils.join_to_string(init_activities)

 
    def get_init_activities(self):
        """获得新用户初始活动id
        """
        return utils.split_to_int(self.init_activities)



