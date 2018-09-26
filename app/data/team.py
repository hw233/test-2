#coding:utf8
"""
Created on 2015-09-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 军队相关请求
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


HERO_COUNT = 3
NONE_HERO = 0
EMPTY_HEROES = "0#0#0"
HERO_RELATIONSHIP_NUM = 3   #一个英雄拥有的羁绊关系的个数


class TeamInfo(object):

    __slots__ = [
            "id",
            "user_id",
            "index",
            "status",

            "relationships_id",
            "heroes_id",
            "battle_score",
            "battle_node_basic_id",
            "union_battle_node_index",
            "anneal_sweep_floor",
            ]

    def __init__(self):
        self.id = 0
        self.user_id = 0
        self.index = 0
        self.status = 0

        self.relationships_id = ""
        self.heroes_id = EMPTY_HEROES
        self.battle_score = 0
        self.battle_node_basic_id = 0
        self.union_battle_node_index = 0
        self.anneal_sweep_floor = 0

    @staticmethod
    def generate_id(user_id, index):
        id = user_id << 32 | index
        return id


    @staticmethod
    def get_index(id):
        index = id & 0xFFFFFFFF
        return index


    @staticmethod
    def create(user_id, index):
        """创建队伍信息
        """
        id = TeamInfo.generate_id(user_id, index)
        team = TeamInfo()
        team.id = id
        team.user_id = user_id
        team.index = index
        team.status = 0

        team.relationships_id = ""
        team.heroes_id = EMPTY_HEROES
        team.battle_score = 0
        team.battle_node_basic_id = 0
        team.union_battle_node_index = 0
        team.anneal_sweep_floor = 0
        return team


    @staticmethod
    def calc_max_num(user_level, vip_level):
        """计算用户当前可以拥有的 team 数量上限
        """
        num = data_loader.MonarchLevelBasicInfo_dict[user_level].teamNumber
        addition = data_loader.VipBasicInfo_dict[vip_level].teamNumAddition
        return num + addition


    def update(self, heroes, relationships_id):
        """更新队伍阵容，同时更新队伍战力
        """
        assert len(heroes) == HERO_COUNT

        ids = []
        score = 0
        for hero in heroes:
            if hero is None:
                ids.append(NONE_HERO)
            else:
                ids.append(hero.id)
                score += hero.battle_score

        self.relationships_id = utils.join_to_string(relationships_id)
        self.heroes_id = utils.join_to_string(ids)
        self.battle_score = score

        return True


    def is_able_to_join_battle(self):
        return self.battle_node_basic_id == 0 and self.anneal_sweep_floor == 0


    def is_able_to_deploy_union_battle(self):
        return (self.battle_node_basic_id == 0 and self.union_battle_node_index == 0)

    def is_able_to_join_union_battle(self):
        return (self.battle_node_basic_id == 0 and self.anneal_sweep_floor == 0
                and self.union_battle_node_index == 0)


    def is_able_to_update(self):
        """是否可以更新队伍
        """
        return (self.battle_node_basic_id == 0 and self.anneal_sweep_floor == 0
                and self.union_battle_node_index == 0)


    def get_heroes(self):
        """获取队伍中英雄 id
        """
        ids = utils.split_to_int(self.heroes_id)
        return ids


    def is_hero_in_team(self, hero_id):
        """判断英雄是否在队伍中
        """
        if hero_id == 0:
            return False

        if hero_id in self.get_heroes():
            return True
        else:
            return False


    def is_in_battle(self):
        return self.battle_node_basic_id != 0


    def set_in_battle(self, node_basic_id):
        assert self.battle_node_basic_id == 0
        self.battle_node_basic_id = node_basic_id

    def clear_in_battle(self):
        assert self.battle_node_basic_id != 0
        self.battle_node_basic_id = 0


    def is_union_defender(self):
        return self.union_battle_node_index != 0


    def set_as_union_defender(self, node_index):
        assert self.union_battle_node_index == 0
        self.union_battle_node_index = node_index


    def clear_for_union_defender(self):
        assert self.union_battle_node_index != 0
        self.union_battle_node_index = 0


    def is_in_anneal_sweep(self):
        return self.anneal_sweep_floor != 0


    def set_in_anneal_sweep(self, floor):
        assert self.anneal_sweep_floor == 0
        self.anneal_sweep_floor = floor


    def clear_in_anneal_sweep(self):
        assert self.anneal_sweep_floor != 0
        self.anneal_sweep_floor = 0



