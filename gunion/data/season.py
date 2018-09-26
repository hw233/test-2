#coding:utf8
"""
Created on 2016-07-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争赛季相关数据存储结构
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnionSeasonInfo(object):
    """联盟赛季信息
    """

    __slots__ = [
            "union_id",
            "index",                    #赛季编号
            "start_time",               #赛季开始时间戳
            "current_battle_index",     #当前联盟战争编号
            "is_able_to_join_battle",   #是否可以参加联盟战争
            "score",                    #赛季联盟胜场积分
            "match_score",              #联盟用于匹配的隐藏分
            ]

    def __init__(self):
        self.union_id = 0

        self.index = 0
        self.start_time = 0

        self.current_battle_index = 0
        self.is_able_to_join_battle = False
        self.score = 0
        self.match_score = 0

    @staticmethod
    def create(union_id, index, start_time):
        season = UnionSeasonInfo()
        season.union_id = union_id

        season.index = index
        season.start_time = start_time

        season.current_battle_index = 0
        season.is_able_to_join_battle = False
        season.score = 0
        season.match_score = 0
        return season


    def force_finish(self, now):
        """强制改变赛季开始时间，使赛季结束（内部接口）
        """
        finish_time = self.get_finish_time()
        if now < finish_time:
            period = int(float(data_loader.UnionConfInfo_dict["battle_season_last_day"].value))
            one_season = period * utils.SECONDS_OF_DAY
            self.start_time -= one_season


    def get_finish_time(self):
        """计算赛季结束时间
        """
        period = int(float(data_loader.UnionConfInfo_dict["battle_season_last_day"].value))
        return self.start_time + period * utils.SECONDS_OF_DAY


    def forward(self, index, start_time):
        """进入下一赛季
        """
        self.index = index
        self.start_time = start_time

        self.score = 0
        #隐藏分进行衰减
        ratio = float(
            data_loader.UnionConfInfo_dict["battle_match_score_forward_ratio"].value)
        self.match_score = int(self.match_score * ratio)


    def forward_battle_index(self):
        """进入下一场战争
        """
        self.current_battle_index += 1
        return self.current_battle_index


    def update_join_battle_status(self, member_number, available):
        """更新是否可以参加联盟战争
        """
        if available and member_number >= int(
                float(data_loader.UnionConfInfo_dict["battle_join_member_count_min"].value)):
            logger.debug("Able to join battle[union_id=%d][num=%d]" %
                    (self.union_id, member_number))
            self.is_able_to_join_battle = True
        else:
            logger.debug("Not able to join battle[union_id=%d][num=%d]" %
                    (self.union_id, member_number))
            self.is_able_to_join_battle = False


    def is_able_to_launch_battle(self, now):
        """是否可以发起战争
        """
        if not self.is_able_to_join_battle:
            return False

        #距离赛季结束没多少时间了，禁止发起战争，因为时间不够完成一场战争
        if self.is_near_end(now):
            return False

        return True


    def is_near_end(self, now):
        """是否临近结束，距离结束不到2天
        此时禁止发起战争，因为时间不够完成一场战争
        """
        #return self.get_finish_time() - now < utils.SECONDS_OF_DAY * 2
        
        #改成系统匹配后这里只需要判断不超过5小时即可
        return self.get_finish_time() - now < utils.SECONDS_OF_HOUR * 5


    def gain_union_score(self, value = 1):
        """增加联盟胜场积分
        """
        assert value >= 0
        self.score += value
        self.match_score += value


