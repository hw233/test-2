#coding:utf8
"""
Created on 2015-02-04
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 将星信息
"""

from datalib.data_loader import data_loader

class HeroStarInfo(object):
    """将星信息"""

    __slots__ = [
        "id",
        "user_id",
        "star_id",
    ]

    def __init__(self, user_id = 0, star_id = 0):
        id = HeroStarInfo.generate_id(user_id, star_id)
        self.id = id
        self.user_id = user_id
        self.star_id = star_id

    @staticmethod
    def generate_id(user_id, star_id):
        return user_id << 32 | star_id

    @staticmethod
    def create(user_id, star_id):
        return HeroStarInfo(user_id, star_id)

    @staticmethod
    def get_next_level_id(star_id):
        """获取下一等级的将星ID"""
        return data_loader.HeroStarBasicInfo_dict[star_id].nextId

    @staticmethod
    def get_battle_score(star_id):
        """获取将星增加的战力"""
        buffer_id = data_loader.HeroStarBasicInfo_dict[star_id].starBattleBuffID
        if buffer_id == 0:
            return 0
        return data_loader.HeroStarBuffInfo_dict[buffer_id].battleScoreCoefficient

    @staticmethod
    def get_interior_score(star_id):
        """获取将星增加的内政分"""
        politics_id = data_loader.HeroStarBasicInfo_dict[star_id].starPoliticsID
        if politics_id == 0:
            return 0
        return data_loader.PoliticsBasicInfo_dict[politics_id].politicsScore

    @staticmethod
    def get_constellation_id(star_id):
        """获取星宿id"""
        return data_loader.HeroStarBasicInfo_dict[star_id].constellationID

    def constellation_id(self):
        return HeroStarInfo.get_constellation_id(self.star_id)

    @staticmethod
    def get_herostar_level(star_id):
        """获取将星等级"""
        return data_loader.HeroStarBasicInfo_dict[star_id].starLv

    def herostar_level(self):
        return HeroStarInfo.get_herostar_level(self.star_id)