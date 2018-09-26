#coding:utf8
"""
Created on 2015-06-24
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 签到相关
"""

from utils import utils
from utils import logger
from app.data.item import ItemInfo
from datalib.data_loader import data_loader


class SignInfo(object):
    """签到信息
    """
    def __init__(self, user_id = 0, index = 0, last_time = 0):
        self.user_id = user_id
        self.index = index
        self.last_time = last_time


    @staticmethod
    def create(user_id):
        """创建签到信息
        """
        sign = SignInfo(user_id)
        return sign


    def signin(self, index, now, force):
        """
        执行签到
        一天只允许签到一次
        """
        if force == False:
            if utils.is_same_day(self.last_time, now):
                logger.warning("Sign in error, same day![last time=%s][now=%s]" %
                        (self.last_time, now))
                return False

            if self.index + 1 != index:
                logger.warning("Sign in index error[index=%d][exp index=%d]" %
                        (index, self.index + 1))
                return False
            self.last_time = now
        else:
            #强制更新过签到日期，将last_time改掉，用户还能手动签到一次
            self.last_time = now - utils.SECONDS_OF_DAY

        self.index = index
        return True


    def get_reward(self, vip_level, hero_list, item_list):
        """
        获得签到奖励
        Args:
            vip_level[int]: vip 等级
            hero_list[list(hero_basic_id, hero_num) out]
            item_list[list(item_basic_id, item_num) out]
        Returns:
            是否成功
        """
        sign_info = data_loader.SignInGiftBasicInfo_dict[self.index]
        item_basic_id = sign_info.itemBasicId
        item_num = sign_info.itemNum
        hero_basic_id = sign_info.heroBasicId
        hero_num = 1

        #vip 加成: 可以获取 x 倍的物品
        if self.index in data_loader.SignInVipAdditionBasicInfo_dict:
            vip_limit = data_loader.SignInVipAdditionBasicInfo_dict[self.index].vipLevel
            time = data_loader.SignInVipAdditionBasicInfo_dict[self.index].vipTimes
            if vip_level >= vip_limit:
                item_num *= time
        if item_basic_id != 0:
            item_list.append((item_basic_id, item_num))
        if hero_basic_id != 0:
            hero_list.append((hero_basic_id, hero_num))
	
        return True


    def try_reset(self, now):
        """重置签到信息
        在一个签到周期开始的时候（月初）执行
        """
        if not utils.is_same_month(self.last_time, now):
            self.index = 0



