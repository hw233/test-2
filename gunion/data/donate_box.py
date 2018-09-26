#coding:utf8
"""
Created on 2016-10-27
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟捐献的宝箱信息
"""

from proto import union_pb2
from datalib.data_loader import data_loader
from utils import utils

class UnionDonateBox(object):
    """联盟捐献宝箱"""

    IDLE = union_pb2.UnionDonateTreasureBoxInfo.IDLE            #未发起捐献
    DONATING = union_pb2.UnionDonateTreasureBoxInfo.DONATING    #捐献中
    UNLOCKED = union_pb2.UnionDonateTreasureBoxInfo.UNLOCKED    #可领取
    NULL = union_pb2.UnionDonateTreasureBoxInfo.NULL            #不存在


    __slots__ = [
        "id",
        "union_id",
        "box_id",

        "status",
        "start_time",           #可领取的时间
        "progress",
    ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.box_id = 0

        self.status = 0
        self.start_time = 0
        self.progress = 0

    @staticmethod
    def generate_id(union_id, box_id):
        return union_id << 32 | box_id
    
    @staticmethod
    def create(union_id, box_id, status = NULL):
        id = UnionDonateBox.generate_id(union_id, box_id)

        donate = UnionDonateBox()
        donate.id = id
        donate.union_id = union_id
        donate.box_id = box_id

        donate.status = status
        donate.start_time = 0
        donate.progress = 0

        return donate

    def get_max_progress(self):
        return data_loader.UnionDonateTreasureBoxBasicInfo_dict[self.box_id].totalProgress

    def get_unlocked_time(self):
        return data_loader.UnionDonateTreasureBoxBasicInfo_dict[self.box_id].getRewardTime

    @staticmethod
    def get_reward_item_list(box_id):
        """获取奖励物品列表"""
        id_list = data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id].reward.itemIds
        num_list = data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id].reward.itemNums
        return (id_list, num_list)

    @staticmethod
    def get_reward_resource_list(box_id):
        """获取奖励资源列表"""
        money = 0
        gold = data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id].reward.gold
        food = 0
        return (money, gold, food)

    def update_status(self, now):
        """更新状态"""
        if self.status == self.UNLOCKED:
            if now - self.start_time > self.get_unlocked_time():
                self.status = self.NULL


    def get_status(self, now):
        self.update_status(now)
        return self.status

    def is_refresh(self, union_data, now):
        """是否允许手动刷新"""
        self.update_status(now)
        union = union_data.union.get(True)
        last_refresh_time = union.donate_last_refresh_time
        return not utils.is_same_day(last_refresh_time, now) and self.status == self.IDLE

    def is_auto_refresh(self, union_data, now):
        """是否需要自动刷新"""
        self.update_status(now)
        union = union_data.union.get(True)
        last_auto_time = union.donate_last_auto_time
        return not utils.is_same_day(last_auto_time, now) and self.status == self.IDLE

    def initiate_donate(self, now):
        """发起捐献"""
        #assert self.status == self.IDLE
        self.status = self.DONATING
        self.start_time = 0
        self.progress = 0

    def gain_donate_progress(self, add_progress, now):
        """增加捐献进度"""
        #assert self.status == self.DONATING
        assert add_progress > 0
        self.progress += add_progress
        if self.progress >= self.get_max_progress():
            self.progress = self.get_max_progress()
            self.status = self.UNLOCKED
            self.start_time = now
