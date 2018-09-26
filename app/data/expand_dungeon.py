#coding:utf8
"""
Created on 2017-03-11
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 扩展副本数据
"""

from datalib.data_loader import data_loader
from utils import utils

class ExpandDungeonInfo(object):
    INACTIVE = 1
    ACTIVE = 2
    LOCKED = 3

    __slots__ = (
        "id",
        "user_id",
        "basic_id",

        "last_update_time",
        "attack_count",
        "reset_count",
    )

    def __init__(self):
        self.id = 0
        self.user_id = 0
        self.basic_id = 0
        self.last_update_time = 0
        self.attack_count = 0
        self.reset_count = 0

    @staticmethod
    def create(user_id, basic_id):
        dungeon = ExpandDungeonInfo()
        id = ExpandDungeonInfo.generate_id(user_id, basic_id)
        dungeon.id = id
        dungeon.user_id = user_id
        dungeon.basic_id = basic_id
        dungeon.last_update_time = 0
        dungeon.attack_count = 0
        dungeon.reset_count = 0

        return dungeon

    @staticmethod
    def generate_id(user_id, basic_id):
        return user_id << 32 | basic_id

    @staticmethod
    def get_open_time(basic_id, now):
        """获取开启时间"""
        start_time = data_loader.ExpandDungeonBasicInfo_dict[basic_id].startTime
        end_time = data_loader.ExpandDungeonBasicInfo_dict[basic_id].endTime

        start = utils.get_spec_second(now, start_time)
        end = utils.get_spec_second(now, end_time)
        return (start, end)

    @staticmethod
    def generate_award(basic_id, battle_level):
        """生成奖励"""
        items_id = []
        items_num = []

        if battle_level == 0:
            #兼容老的随机副本模式
            items_id_pool = data_loader.ExpandDungeonRewardBasicInfo_dict[basic_id].itemBasicIds
            items_num_pool = data_loader.ExpandDungeonRewardBasicInfo_dict[basic_id].itemNums
            weights = data_loader.ExpandDungeonRewardBasicInfo_dict[basic_id].weights
            num = data_loader.ExpandDungeonRewardBasicInfo_dict[basic_id].num
        else:
            key = "%d_%d" % (basic_id, battle_level)
            items_id_pool = data_loader.ExpandDungeonRewardBasicInfo_dict[key].itemBasicIds
            items_num_pool = data_loader.ExpandDungeonRewardBasicInfo_dict[key].itemNums
            weights = data_loader.ExpandDungeonRewardBasicInfo_dict[key].weights
            num = data_loader.ExpandDungeonRewardBasicInfo_dict[key].num

        assert len(items_id_pool) == len(items_num_pool) == len(weights)

        choice_index_list = utils.random_weight(weights, num, False)
        for index in choice_index_list:
            items_id.append(items_id_pool[index])
            items_num.append(items_num_pool[index])

        return (items_id, items_num)

    @staticmethod
    def get_level(user_level):
        """获取副本的等级"""
        return user_level - user_level % 5

    def level(self, user_level):
        return ExpandDungeonInfo.get_level(user_level)

    def node_basic_id(self):
        return int(float(data_loader.MapConfInfo_dict['expand_dungeon_node_basic_id'].value))

    def reset_attack_count(self, now):
        """重置攻击次数"""
        self.attack_count = 0
        self.reset_count += 1

    def daily_update(self, now):
        """重置每日数据"""
        if not utils.is_same_day(self.last_update_time, now):
            self.attack_count = 0
            self.reset_count = 0
            self.last_update_time = now

    def status(self, user_level, now):
        """获取当前状态"""
        limit_level = data_loader.ExpandDungeonBasicInfo_dict[self.basic_id].monarchLimitLevel
        if limit_level > user_level:
            return self.LOCKED
        
        start_time, end_time = ExpandDungeonInfo.get_open_time(self.basic_id, now)
        if start_time <= now <= end_time:
            return self.ACTIVE
        else:
            return self.INACTIVE

    def end_time(self, user_level, now):
        """当前状态结束时间"""
        limit_level = data_loader.ExpandDungeonBasicInfo_dict[self.basic_id].monarchLimitLevel
        if limit_level > user_level:
            return 0
        
        start_time, end_time = ExpandDungeonInfo.get_open_time(self.basic_id, now)
        if start_time <= now <= end_time:
            return end_time - now
        else:
            return start_time + utils.SECONDS_OF_DAY - now

    def get_remain_num(self):
        """获取剩余的攻击次数"""
        #attack_num = data_loader.ExpandDungeonBasicInfo_dict[self.basic_id].dailyAttackNum
        attack_num = int(float(data_loader.OtherBasicInfo_dict['ExpandDungeonEnterNum'].value))
        return max(attack_num - self.attack_count, 0)

    def attack(self):
        self.attack_count += 1
