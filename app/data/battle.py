#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 战斗相关计算逻辑
"""

import time
import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


INVALID_NODE = -1
INVALID_RIVAL = -1
TEAM_COUNT_MAX = 3


class BattleInfo(object):
    """战斗信息，记录正在发生的战斗信息
    """
    __slots__ = [
            "node_id", "user_id",
            "rival_id", "mail_id",
            "time", "teams_index", "heroes_id", "food",
            "soldier_num", "conscripts_id", "conscripts_soldier_num",
            "reward_money", "reward_food",
            "reward_items_basic_id", "reward_items_num",
            "reward_hero_exp", "reward_user_exp",
            "is_appoint",
            "appoint_total_time",
            "appoint_result",
            "own_soldier_basic_id", "own_soldier_level", "own_soldier_survival",
            "enemy_soldier_basic_id", "enemy_soldier_level", "enemy_soldier_survival",
            ]

    def __init__(self, node_id = INVALID_NODE, user_id = 0,
            rival_id = INVALID_RIVAL, mail_id = 0,
            time = 0, teams_index = '', heroes_id = '', food = 0,
            soldier_num = 0, conscripts_id = '', conscripts_soldier_num = '',
            reward_money = 0, reward_food = 0,
            reward_items_basic_id = '', reward_items_num = '',
            reward_hero_exp = 0, reward_user_exp = 0,
            is_appoint = False,
            appoint_total_time = 0,
            appoint_result = False,
            own_soldier_basic_id = '', own_soldier_level = '', own_soldier_survival = '',
            enemy_soldier_basic_id = '', enemy_soldier_level = '', enemy_soldier_survival = ''):

        self.node_id = node_id
        self.user_id = user_id
        self.rival_id = rival_id
        self.mail_id = mail_id
        self.time = time

        self.teams_index = teams_index
        self.heroes_id = heroes_id
        self.food = food
        self.soldier_num = soldier_num
        self.conscripts_id = conscripts_id
        self.conscripts_soldier_num = conscripts_soldier_num

        self.reward_money = reward_money
        self.reward_food = reward_food
        self.reward_items_basic_id = reward_items_basic_id
        self.reward_items_num = reward_items_num
        self.reward_hero_exp = reward_hero_exp
        self.reward_user_exp = reward_user_exp

        #委任数据
        self.is_appoint = is_appoint
        self.appoint_total_time = appoint_total_time
        self.appoint_result = appoint_result
        self.own_soldier_basic_id = own_soldier_basic_id
        self.own_soldier_level = own_soldier_level
        self.own_soldier_survival = own_soldier_survival
        self.enemy_soldier_basic_id = enemy_soldier_basic_id
        self.enemy_soldier_level = enemy_soldier_level
        self.enemy_soldier_survival = enemy_soldier_survival


    @staticmethod
    def create(node_id, user_id):
        """创建战斗信息
        """
        battle = BattleInfo(node_id, user_id)
        return battle


    @staticmethod
    def is_able_to_appoint(user):
        if user.level >= int(
                float(data_loader.OtherBasicInfo_dict["AppointLimitMonarchLevel"].value)):
            return True
        else:
            return False


    def is_able_to_start(self):
        """是否可以开始战斗
        """
        if self.rival_id != INVALID_RIVAL:
            return False
        else:
            return True


    def is_revenge(self):
        """是否是复仇的battle
        """
        if (self.node_id & 0xFFFFFFFF) == 0:
            return True
        else:
            return False


    def set_is_appoint(self, is_appoint):
        self.is_appoint = is_appoint


    def set_food_consume(self, cost_food):
        self.food = cost_food


    def set_soldier_consume(self, consume_soldier_info):
        """消耗士兵
        """
        self.soldier_num = 0

        conscripts_id = []
        conscripts_soldier_num = []
        for id in consume_soldier_info:
            conscripts_id.append(id)
            num = consume_soldier_info[id]
            conscripts_soldier_num.append(num)
            self.soldier_num += num

        self.conscripts_id = utils.join_to_string(conscripts_id)
        self.conscripts_soldier_num = utils.join_to_string(conscripts_soldier_num)


    def get_soldier_consume(self):
        conscripts_id = utils.split_to_int(self.conscripts_id)
        conscripts_soldier_num = utils.split_to_int(self.conscripts_soldier_num)
        count = len(conscripts_id)

        consume_soldier_info = {}
        for index in range(0, count):
            consume_soldier_info[conscripts_id[index]] = conscripts_soldier_num[index]

        return consume_soldier_info


    def set_reward(self, reward_money, reward_food,
            reward_hero_exp, reward_user_exp, reward_items):
        """设置战利品
        """
        self.reward_money = reward_money
        self.reward_food = reward_food

        self.reward_hero_exp = reward_hero_exp
        self.reward_user_exp = reward_user_exp

        #合并重复的 item
        merge_items = {}
        for (basic_id, num) in reward_items:
            if basic_id not in merge_items:
                merge_items[basic_id] = num
            else:
                merge_items[basic_id] += num

        reward_items_basic_id = []
        reward_items_num = []
        for item_basic_id in merge_items:
            item_num = merge_items[item_basic_id]
            reward_items_basic_id.append(item_basic_id)
            reward_items_num.append(item_num)

        self.reward_items_basic_id = utils.join_to_string(reward_items_basic_id)
        self.reward_items_num = utils.join_to_string(reward_items_num)


    def start(self, node, rival, mail, teams, heroes, now, vip_level):
        """开始战斗
        """
        assert rival.id != INVALID_RIVAL

        self.rival_id = rival.id
        if mail is not None:
            self.mail_id = mail.id
        if node is not None:
            self.node_id = node.id

        teams_index = [team.index for team in teams]
        self.teams_index = utils.join_to_string(teams_index)

        heroes_id = [hero.id for hero in heroes]
        self.heroes_id = utils.join_to_string(heroes_id)

        self.time = now

        if self.is_appoint:
            appoint_time = int(float(data_loader.OtherBasicInfo_dict["BattleTime"].value))
            deduction_time = int(data_loader.VipBasicInfo_dict[vip_level].appointTimeDeduction)
            self.appoint_total_time = max(0, appoint_time - deduction_time)
        return True


    def is_able_to_finish(self, now, force = False):
        """是否可以结束战斗
        """
        if self.is_appoint:
            if force:
                return True

            if now - self.time >= self.appoint_total_time:
                return True
            else:
                return False
        else:
            return self.rival_id != INVALID_RIVAL


    def get_reward_items(self):
        """
        """
        item_list = []

        items_basic_id = utils.split_to_int(self.reward_items_basic_id)
        items_num = utils.split_to_int(self.reward_items_num)
        assert len(items_basic_id) == len(items_num)
        items_count = len(items_basic_id)

        for i in range(0, items_count):
            item_list.append((items_basic_id[i], items_num[i]))

        return item_list


    def get_battle_hero(self):
        """
        """
        ids = utils.split_to_int(self.heroes_id)
        return ids


    def get_battle_team(self):
        teams_index = utils.split_to_int(self.teams_index)
        return teams_index


    def finish(self):
        """结束战斗
        """
        self.rival_id = INVALID_RIVAL
        self.mail_id = 0
        self.time = 0

        self.teams_index = ''
        self.heroes_id = ''
        self.food = 0
        self.soldier_num = 0
        self.conscripts_id = ''
        self.conscripts_soldier_num = ''

        self.reward_money = 0
        self.reward_food = 0
        self.reward_items_basic_id = ''
        self.reward_items_num = ''
        self.reward_hero_exp = 0
        self.reward_user_exp = 0

        self.is_appoint = False
        self.appoint_total_time = 0
        self.appoint_result = False
        self.own_soldier_basic_id = ''
        self.own_soldier_level = ''
        self.own_soldier_survival = ''
        self.enemy_soldier_basic_id = ''
        self.enemy_soldier_level = ''
        self.enemy_soldier_survival = ''

        return True


    def set_appoint_result(self, result, own_soldier_info, enemy_soldier_info):
        """保存委托结果
        """
        self.appoint_result = result
        own_soldier_basic_id = []
        own_soldier_level = []
        own_soldier_survival = []
        enemy_soldier_basic_id = []
        enemy_soldier_level = []
        enemy_soldier_survival = []

        for info in own_soldier_info:
            own_soldier_basic_id.append(info[0])
            own_soldier_level.append(info[1])
            own_soldier_survival.append(info[2])

        for info in enemy_soldier_info:
            enemy_soldier_basic_id.append(info[0])
            enemy_soldier_level.append(info[1])
            enemy_soldier_survival.append(info[2])

        self.own_soldier_basic_id = utils.join_to_string(own_soldier_basic_id)
        self.own_soldier_level = utils.join_to_string(own_soldier_level)
        self.own_soldier_survival = utils.join_to_string(own_soldier_survival)
        self.enemy_soldier_basic_id = utils.join_to_string(enemy_soldier_basic_id)
        self.enemy_soldier_level = utils.join_to_string(enemy_soldier_level)
        self.enemy_soldier_survival = utils.join_to_string(enemy_soldier_survival)


    def get_own_soldier_info(self):
        own_soldier_basic_id = utils.split_to_int(self.own_soldier_basic_id)
        own_soldier_level = utils.split_to_int(self.own_soldier_level)
        own_soldier_survival = utils.split_to_int(self.own_soldier_survival)

        own_soldier_info = []
        for i in range(len(own_soldier_basic_id)):
            own_soldier_info.append(
                    (own_soldier_basic_id[i],
                     own_soldier_level[i],
                     own_soldier_survival[i]))

        return own_soldier_info


    def get_enemy_soldier_info(self):
        enemy_soldier_basic_id = utils.split_to_int(self.enemy_soldier_basic_id)
        enemy_soldier_level = utils.split_to_int(self.enemy_soldier_level)
        enemy_soldier_survival = utils.split_to_int(self.enemy_soldier_survival)

        enemy_soldier_info = []
        for i in range(len(enemy_soldier_basic_id)):
            enemy_soldier_info.append(
                    (enemy_soldier_basic_id[i],
                     enemy_soldier_level[i],
                     enemy_soldier_survival[i]))

        return enemy_soldier_info


