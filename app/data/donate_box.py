#coding:utf8
"""
Created on 2016-10-27
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 用户宝箱信息
"""

from proto import union_pb2
from datalib.data_loader import data_loader
import random

class UserDonateBox(object):
    """用户宝箱信息"""

    PRIMARY_DONATE = union_pb2.Primary
    MIDDLE_DONATE = union_pb2.Intermediate
    HIGH_DONATE = union_pb2.Advanced

    IDLE = union_pb2.UnionDonateTreasureBoxInfo.IDLE            #未发起捐献
    DONATING = union_pb2.UnionDonateTreasureBoxInfo.DONATING    #捐献中
    UNLOCKED = union_pb2.UnionDonateTreasureBoxInfo.UNLOCKED    #可领取
    NULL = union_pb2.UnionDonateTreasureBoxInfo.NULL            #不存在

    __slots__ = [
        "id",
        "user_id",
        "box_id",
        "is_primary",#是否可以进行初级捐献,下同
        "is_middle",
        "is_high",
        "status",
        "is_rewarded",
    ]

    def __init__(self):
        self.id = 0
        self.user_id = 0
        self.box_id = 0
        self.is_primary = 0
        self.is_middle = 0
        self.is_high = 0
        self.status = 0
        self.is_rewarded = 0

    @staticmethod
    def generate_id(user_id, box_id):
        return user_id << 32 | box_id
    
    @staticmethod
    def create(user_id, box_id, is_primary = 0, is_middle = 0, is_high = 0):
        id = UserDonateBox.generate_id(user_id, box_id)
        donate = UserDonateBox()
        donate.id = id
        donate.user_id = user_id
        donate.box_id = box_id
        donate.is_primary = is_primary
        donate.is_middle = is_middle
        donate.is_high = is_high
        donate.status = UserDonateBox.NULL
        donate.is_rewarded = 0

        return donate

    def get_donate_level(self):
        """返回用list表示的可捐助的等级"""
        donate_level = []
        if self.is_primary:
            donate_level.append(self.PRIMARY_DONATE)
        if self.is_middle:
            donate_level.append(self.MIDDLE_DONATE)
        if self.is_high:
            donate_level.append(self.HIGH_DONATE)
        
        return donate_level

    def refresh_donate_level(self):
        """刷新可捐献的等级"""
        rand = random.random()
        self.is_primary = int(rand < self.get_donate_probability(self.PRIMARY_DONATE))
        rand = random.random()
        self.is_middle = int(rand < self.get_donate_probability(self.MIDDLE_DONATE))
        rand = random.random()
        self.is_high = int(rand < self.get_donate_probability(self.HIGH_DONATE))

    def get_donate_probability(self, grade):
        """获取指定捐献等级的可捐献概率"""
        box_type = data_loader.UnionDonateTreasureBoxBasicInfo_dict[self.box_id].type
        key = str(box_type) + "_" + str(grade)
        return data_loader.UnionDonateCostBasicInfo_dict[key].probability

    def update_donate_box_by_boxinfo(self, box_info):
        """更新宝箱状态"""
        if self.status != self.UNLOCKED and box_info.current_state == self.UNLOCKED:
            self.is_rewarded = 0
        self.status = box_info.current_state

    def reward_donate_box(self):
        assert self.status == self.UNLOCKED
        self.is_rewarded = 1