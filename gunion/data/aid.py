#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟援助相关数据存储结构
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnionAidInfo(object):
    """联盟援助信息
    """

    __slots__ = [
            "id",
            "union_id",
            "user_id",
            "item_basic_id",
            "item_need_num",
            "item_current_num",
            "start_time",
            "contributor",
            "is_finish",
            ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.user_id = 0
        self.item_basic_id = 0
        self.item_current_num = 0
        self.start_time = 0
        self.contributor = ''
        self.is_finish = False

    @staticmethod
    def generate_id(union_id, user_id):
        id = union_id << 32 | user_id
        return id


    @staticmethod
    def create(union_id, user_id):
        id = UnionAidInfo.generate_id(union_id, user_id)

        aid = UnionAidInfo()
        aid.id = id
        aid.union_id = union_id
        aid.user_id = user_id
        aid.is_finish = True

        return aid


    def start(self, item_basic_id, item_num, now):
        """开始援助
        """
        self.item_basic_id = item_basic_id
        self.item_need_num = item_num
        self.item_current_num = 0
        self.start_time = now
        self.contributor = ""
        self.is_finish = False


    def is_available(self, user_id):
        """对应玩家是否可以进行援助
        """
        if user_id == self.user_id:
            #自己不能进行援助
            return False

        if user_id in utils.split_to_int(self.contributor):
            #已经进行过援助的，不能再次援助
            return False
        return True


    def is_active_for(self, user_id, now):
        """针对某个玩家是否可见
        """
        #已经领取（结束）不在可见
        if self.is_finish:
            return False

        #自己发布的援助，未领取（结束），可见
        if user_id == self.user_id:
            return True

        #别人发布的援助，已经达到了领取（结束）条件的，不可见
        if self.is_able_to_finish(now):
            return False
        return True


    def is_able_to_finish(self, now):
        """是否可以结束援助
        """
        if self.is_finish:
            return False

        if self.item_current_num >= self.item_need_num:
            return True

        #有效期内
        level = data_loader.ItemBasicInfo_dict[self.item_basic_id].level
        lifetime = data_loader.UnionAidBasicInfo_dict[level].expiryTime
        if now - self.start_time >= lifetime:
            return True

        return False


    def finish(self, now):
        """结束援助
        """
        if self.is_able_to_finish(now):
            self.is_finish = True
            return True

        return False


    def accept(self, user_id, item_basic_id, now):
        """接受援助
        """
        if self.is_able_to_finish(now):
            logger.warning("Union aid is finished")
            return False

        if item_basic_id != self.item_basic_id:
            logger.warning("Unmatched item basic id[accept=%d][need=%d]" %
                    (item_basic_id, self.item_basic_id))
            return False

        if not self.is_available(user_id):
            logger.warning("Aid not available to user[user_id=%d]" % user_id)
            return False

        contributor =  utils.split_to_int(self.contributor)
        contributor.append(user_id)
        self.contributor = utils.join_to_string(contributor)
        self.item_current_num += 1
        return True


    def calc_user_benefit(self):
        """援助个人获得的收益：联盟荣誉、主公经验、元宝
        """
        level = data_loader.ItemBasicInfo_dict[self.item_basic_id].level
        honor = data_loader.UnionAidBasicInfo_dict[level].honor
        exp = data_loader.UnionAidBasicInfo_dict[level].monarchExp
        gold = data_loader.UnionAidBasicInfo_dict[level].gold
        return (honor, exp, gold)


    def calc_union_benefit(self):
        """援助联盟获得的收益：繁荣度
        """
        level = data_loader.ItemBasicInfo_dict[self.item_basic_id].level
        return data_loader.UnionAidBasicInfo_dict[level].prosperity



