#coding:utf8
"""
Created on 2015-04-14
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 守卫队（防守阵容）信息
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class GuardInfo(object):
    def __init__(self, user_id = 0, defense_id = 0,
            score = 0, heroes_id = "", heroes_score = '', heroes_count = 0,
            teams_id = '', teams_score = '', teams_hero = ''):
        self.user_id = user_id
        self.defense_id = defense_id

        #评分：帐号历史上战力最高的 n 个武将的战力之和 - 用于 PVP 匹配
        self.score = score
        self.heroes_id = heroes_id
        self.heroes_score = heroes_score
        self.heroes_count = heroes_count

        #防守阵容：当前最强的 X 支部队, X 是当前可上阵的队伍数量 - 用于 PVP 对战
        self.teams_id = teams_id
        self.teams_score = teams_score
        self.teams_hero = teams_hero


    @staticmethod
    def create(user_id, defense_id):
        """
        """
        guard = GuardInfo(user_id, defense_id)
        return guard


    def try_update_top_score(self, hero_list, team_count):
        """尝试更新历史最高战力
        Args:
            hero_list[list(HeroInfo)]: 英雄信息
            team_count[int]: 可以同时上阵的武将数量
        """
        self.heroes_count = team_count * 3 #取决于一次战斗可以上阵的队伍数量

        top_heroes_id = utils.split_to_int(self.heroes_id)
        top_heroes_score = utils.split_to_int(self.heroes_score)
        assert len(top_heroes_id) == len(top_heroes_score)

        min_score = 0
        if len(top_heroes_score) >= self.heroes_count:
            min_score = min(top_heroes_score)

        top = []
        for hero in hero_list:
            if hero.id in top_heroes_id:
                #如果英雄原来就在 top 阵容中，并且战力有提升，更新记录的 top 战力值
                index = top_heroes_id.index(hero.id)
                if hero.battle_score > top_heroes_score[index]:
                    top_heroes_score[index] = hero.battle_score
            else:
                #如果英雄原本不在 top 阵容中，但是目前战力足以排入 top 阵容
                if hero.battle_score > min_score:
                    top.append((hero.id, hero.battle_score))

        for index in range(0, len(top_heroes_id)):
            top.append((top_heroes_id[index], top_heroes_score[index]))

        #按照战力评分，从大到小排序
        sort_top = sorted(top, key = lambda info : info[1], reverse = True)
        count = min(self.heroes_count, len(sort_top))
        sort_top = sort_top[0:count]

        self.heroes_id = utils.join_to_string(
                [str(hero_id) for (hero_id, hero_score) in sort_top])
        self.heroes_score = utils.join_to_string(
                [str(hero_score) for (hero_id, hero_score) in sort_top])

        self.score = sum([hero_score for (hero_id, hero_score) in sort_top])
        return True


    def update_team(self, teams, count):
        """更新防守阵容
        Args:
            teams[list(TeamInfo)]: 所有队伍信息
            count[int]: 可以上阵的最大队伍数量
        """
        #按照队伍战力评分，从大到小排序
        sort_teams = sorted(teams, key = lambda team : team.battle_score, reverse = True)
        count = min(count, len(sort_teams))
        top = sort_teams[0:count]

        self.teams_id = utils.join_to_string([team.id for team in top])
        self.teams_score = utils.join_to_string([team.battle_score for team in top])
        self.teams_hero = utils.join_to_string([team.heroes_id for team in top])

        return True


    def get_team_score(self):
        """得到防守阵容的战斗力 score
        """
        return sum(utils.split_to_int(self.teams_score))


