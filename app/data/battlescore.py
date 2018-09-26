#coding:utf8
"""
Created on 2015-12-02
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 战力排行
"""

import math
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


TOP_TEAM_LEN = 100#9    #为了和客户端计算总战力的方法保持一致，玩家战力榜也累加所有部队的战力和


class BattleScoreInfo(object):
    def __init__(self, user_id = 0, score = 0, powerful_teams_id = ''):
        self.user_id = user_id
        self.score = score
        self.powerful_teams_id = powerful_teams_id


    @staticmethod
    def create(user_id):
        """
            Args:
                user_id[int]: 用户 id
            Returns:
                BattleScoreInfo 战力信息
        """
        battle_score = BattleScoreInfo(user_id)
        return battle_score


    def get_powerful_teams_id(self):
        ids = utils.split_to_int(self.powerful_teams_id)
        return ids


    def update(self, team_list):
        """更新帐号战力
        帐号战力为玩家当前最强的9个队伍战力之和
        """
        if len(team_list) == 0:
            return

        #将队伍按照 battle_score 值由大到小排序, 并截取前九个
        team_sorted = sorted(team_list, key = lambda team : team.battle_score, reverse = True)
        count = min(len(team_list), TOP_TEAM_LEN)
        powerful_teams = team_sorted[0:count]

        self.powerful_teams_id = utils.join_to_string(
                [team.id for team in powerful_teams if team.battle_score > 0])
        self.score = sum(
                [team.battle_score for team in powerful_teams if team.battle_score > 0])


