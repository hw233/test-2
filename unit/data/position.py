#coding:utf8
"""
Created on 2016-05-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城官职相关数据存储结构
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnitPositionInfo(object):
    """史实城官职信息
    """

    __slots__ = [
            "id",
            "city_id",
            "user_id",
            "is_robot",
            "level",
            "is_locked",
            "lock_time",
            "reputation",
            "update_time",
            ]

    def __init__(self):
        self.id = 0
        self.city_id = 0
        self.user_id = 0
        self.is_robot = False
        self.level = 0
        self.is_locked = False
        self.lock_time = 0
        self.reputation = 0
        self.update_time = 0

    @staticmethod
    def create(city_id, user_id, now, robot = False):
        """创建官职信息
        """
        id = UnitPositionInfo.generate_id(city_id, user_id)
        position = UnitPositionInfo()
        position.id = id
        position.city_id = city_id
        position.user_id = user_id
        position.is_robot = robot
        position.level = 0
        position.is_locked = False
        position.lock_time = 0
        position.reputation = 0
        position.update_time = now
        return position


    @staticmethod
    def generate_id(city_id, user_id):
        id = city_id << 32 | user_id
        return id


    def change_level(self, level, now):
        """更改官职
        Args:
            level[int]: 职位等级
        """
        #先结算之前的声望
        if self.level != 0:
            self.update_reputation(now)

        self.level = level
        self.update_time = now


    def is_leader(self):
        """是否是首领（太守）
        """
        key = "%d_%d" % (self.city_id, self.level)
        return data_loader.LegendCityPositionBasicInfo_dict[key].isLeader


    def is_able_to_gain_position_reputation(self, now):
        """是否可以结算官职声望收益
        """
        if self.level <= 0:
            return False

        gap = int(float(data_loader.MapConfInfo_dict["legendcity_reputation_check_gap"].value))
        return now - self.update_time > gap


    def update_reputation(self, end_time):
        """结算获得的声望
        """
        key = "%d_%d" % (self.city_id, self.level)
        info = data_loader.LegendCityPositionBasicInfo_dict[key]

        duration = end_time - self.update_time
        add = info.reputationPerHour * duration / 3600
        self.reputation += int(add)
        self.update_time = end_time
        logger.debug("Update reputation[duration=%s][add=%d][remain=%d]" % (
            duration, int(add), self.reputation))


    def gain_reputation(self, value):
        """获得声望
        """
        assert value >= 0
        self.reputation += int(value)
        logger.debug("Gain reputation[add=%d][remain=%d]" % (int(value), self.reputation))


    def cost_reputation(self, value):
        """消费声望
        """
        assert value >= 0
        if self.reputation < value:
            logger.warning("Not enough reputation[own=%d][need=%d]" %
                    (self.reputation, value))
            return False

        self.reputation -= int(value)
        logger.debug("Cost reputation[cost=%d][remain=%d]" % (int(value), self.reputation))
        return True


    def lock(self, now):
        """锁定
        """
        assert not self.is_locked
        self.is_locked = True
        self.lock_time = now


    def unlock(self):
        """解锁
        """
        assert self.is_locked
        self.is_locked = False


    def check_lock_status(self, now):
        """检查锁定状态
        如果超过锁定时间，自动解锁
        """
        if self.is_locked and self.get_unlock_time(now) <= 0:
            self.unlock()


    def get_unlock_time(self, now):
        """获取解锁还需要的时间
        """
        duration = int(float(data_loader.MapConfInfo_dict["legendcity_lock_duration"].value))
        return self.lock_time + duration - now

