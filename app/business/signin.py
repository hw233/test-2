#coding:utf8
"""
Created on 2015-09-29
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 签到 相关业务逻辑
"""

from utils import logger
from utils import utils


def signin(sign, index, user, hero_list, item_list, now, force):
    """
    执行签到
    1 只允许连续天数的签到
    2 同一天只允许签到一次
    """
    if not sign.signin(index, now, force):
        return False

    return sign.get_reward(user.vip_level, hero_list, item_list)


