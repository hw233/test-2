#coding:utf8
"""
Created on 2017-03-01
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟boss数据
"""

from utils import utils
from datalib.data_loader import data_loader
import random

class UserUnionBossInfo(object):
    """联盟boss数据结构"""

    INACTIVE = 1
    BATTLE = 2
    KILLED = 3

    __slots__ = (
        "id",
        "user_id",
        "boss_id",

        "level",
        "arrays_id",                #boss阵容
        "can_attack_arrays_index",  #可攻击的阵容
        "attack_array_index",       #战斗时选择的boss阵容
    )

    def __init__(self):
        self.id = 0
        self.user_id = 0
        self.boss_id = 0

        self.level = 0
        self.arrays_id = ""
        self.can_attack_arrays_index = ""
        self.attack_array_index = 0

    @staticmethod
    def create(user_id, boss_id):
        id = UserUnionBossInfo.generate_id(user_id, boss_id)
        boss = UserUnionBossInfo()
        boss.id = id
        boss.user_id = user_id
        boss.boss_id = boss_id

        boss.level = 0
        boss.arrays_id = ""
        boss.can_attack_arrays_index = ""
        boss.attack_array_index = 0

        return boss

    @staticmethod
    def generate_id(user_id, boss_id):
        return user_id << 32 | boss_id

    def init(self, user_level):
        """通过用户等级初始化"""
        self.level = user_level - user_level % 5

        arrays = []
        arrays.append("%s_%s_%s" % (self.boss_id, self.level, 1))
        arrays.append("%s_%s_%s" % (self.boss_id, self.level, 2))
        arrays.append("%s_%s_%s" % (self.boss_id, self.level, 3))
        self.arrays_id = utils.join_to_string(arrays)

        self.calc_can_attack_array_index(0, 0)

    def reset(self, user_level):
        """重置"""
        self.level = 0
        self.arrays_id = ""
        self.can_attack_arrays_index = ""
        self.attack_array_index = 0

        self.init(user_level)
        
    def calc_can_attack_array_index(self, array_index, win):
        """计算出可以被攻击的阵容"""
        can_attack_index = []

        key = "%s_%s" % (array_index, int(win))
        probabilities = data_loader.UnionBossArrayAttackRatio_dict[key]

        array_one_probability = 1.0 * probabilities.arrayOneAvailableProbability / 100.0
        array_two_probability = 1.0 * probabilities.arrayTwoAvailableProbability / 100.0
        array_three_probability = 1.0 * probabilities.arrayThreeAvailableProbability / 100.0

        random.seed()
        c = random.random()
        if c < array_one_probability:
            can_attack_index.append(1)
        else:
            can_attack_index.append(0)

        c = random.random()
        if c < array_two_probability:
            can_attack_index.append(1)
        else:
            can_attack_index.append(0)

        c = random.random()
        if c < array_three_probability:
            can_attack_index.append(1)
        else:
            can_attack_index.append(0)

        self.can_attack_arrays_index = utils.join_to_string(can_attack_index)

    def get_arrays_id(self):
        return self.arrays_id.split('#')

    def get_can_attack_arrays_index(self):
        return utils.split_to_int(self.can_attack_arrays_index)

    def get_arrays_merit_ratio(self):
        arrays = self.get_arrays_id()
        merit_ratios = []
        for array in arrays:
            merit_ratios.append(data_loader.UnionBossArrayBasicInfo_dict[array].meritRatio)

        return merit_ratios

    def start_battle(self, array_index):
        self.attack_array_index = array_index

    def finish_battle(self, win):
        self.calc_can_attack_array_index(self.attack_array_index, win)
        self.attack_array_index = 0

    @staticmethod
    def get_description(boss_id):
        """获取介绍"""
        return data_loader.UnionBossBasicInfo_dict[boss_id].description.encode("utf8")

    def description(self):
        return UserUnionBossInfo.get_description(self.boss_id)

    def boss_hero_id(self):
        """获取boss的hero id"""
        array_id = self.get_arrays_id()[0]
        return data_loader.UnionBossArrayBasicInfo_dict[array_id].heroIds[-2]
        
