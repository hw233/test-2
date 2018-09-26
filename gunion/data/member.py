#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟成员相关数据存储结构
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnionMemberInfo(object):
    """联盟成员信息
    """
    POSITION_LEADER = 1
    POSITION_VICE = 2
    POSITION_MEMBER = 3

    __slots__ = [
            "id",
            "union_id",
            "user_id",

            "position",
            "join_time",
            "history_honor",

            "is_join_battle",           #是否参加此次战争
            "battle_score",             #此次战争中的战功
            "battle_score_accept_step", #此次战争中的战功阶段奖励领取情况
            "battle_kills",             #此次战争中杀敌数
            "battle_drum",              #此次战争中擂鼓数
            ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.user_id = 0
        self.position = 3
        self.join_time = 0
        self.history_honor = 0

        self.is_join_battle = False
        self.battle_score = 0
        self.battle_score_accept_step = 0
        self.battle_kills = 0
        self.battle_drum = 0

    @staticmethod
    def generate_id(union_id, user_id):
        id = union_id << 32 | user_id
        return id


    @staticmethod
    def create(union_id, user_id, now):
        id = UnionMemberInfo.generate_id(union_id, user_id)

        member = UnionMemberInfo()
        member.id = id
        member.union_id = union_id
        member.user_id = user_id
        member.position = UnionMemberInfo.POSITION_MEMBER
        member.join_time = now
        member.history_honor = 0

        member.is_join_battle = False
        member.battle_score = 0
        member.battle_score_accept_step = 0
        member.battle_kills = 0
        member.battle_drum = 0

        return member


    def set_as_leader(self):
        self.position = self.POSITION_LEADER


    def set_as_vice_leader(self):
        self.position = self.POSITION_VICE


    def set_as_normal_member(self):
        self.position = self.POSITION_MEMBER


    def is_leader(self):
        return self.position == self.POSITION_LEADER


    def is_vice_leader(self):
        return self.position == self.POSITION_VICE


    def is_normal_member(self):
        return self.position == self.POSITION_MEMBER


    def gain_honor(self, value):
        """获得联盟荣誉
        """
        assert value >= 0
        self.history_honor += value


    def gain_battle_score_immediate(self, value):
        """获得联盟战争战功
        """
        assert value >= 0
        self.battle_score += value


    def drum(self, drum_count):
        """擂鼓
        """
        assert drum_count >= 0
        self.battle_drum += drum_count


    def add_kills(self, kills):
        """增加杀敌数
        """
        assert kills >= 0
        self.battle_kills += kills


    def calc_battle_score_by_drum(self, drum_count, user_level):
        """擂鼓
        """
        assert drum_count >= 0
        value = data_loader.UnionBattleScoreForDrumInfo_dict[user_level].score * drum_count
        return value


    def calc_battle_score_by_kills(self, kills):
        assert kills >= 0
        value = kills * int(
                float(data_loader.UnionConfInfo_dict["battle_kill_score"].value))
        return value


    def reset_season(self):
        """重置联盟赛季信息
        """
        self.reset_battle()


    def reset_battle(self):
        """重置联盟战争信息
        """
        self.is_join_battle = False
        self.battle_score = 0
        self.battle_score_accept_step = 0
        self.battle_kills = 0
        self.battle_drum = 0


    def join_battle(self):
        """允许参战
        """
        self.is_join_battle = True


    def accept_battle_score_step_award(self, user_level, target_step):
        """领取战争战功阶段奖励
        """
        target_score = data_loader.UnionBattleIndividualTargetInfo_dict[
                user_level].target[target_step - 1]

        if self.battle_score < target_score:
            #战功不够
            logger.warning("Union battle score not enough[%d<%d]" %
                    (self.battle_score, target_score))
            return False

        if self.battle_score_accept_step + 1 != target_step:
            #不是按照顺序领取奖励
            logger.warning("Union battle scrore step error[now=%d][accept=%d]" %
                    (self.battle_score_accept_step, target_step))
            return False
        self.battle_score_accept_step = target_step

        #获得联盟荣誉
        award_index = data_loader.UnionBattleIndividualTargetInfo_dict[
                user_level].awardIndex[target_step - 1]
        award = data_loader.UnionBattleIndivStepAwardInfo_dict[award_index]
        self.gain_honor(award.honor)

        return True
        