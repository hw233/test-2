#coding:utf8
"""
Created on 2015-09-07
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 兵种相关逻辑
"""

from utils import logger
from app.data.soldier import SoldierInfo


def upgrade(soldier, heroes):
    """
    兵种进阶
    Args:
        soldier[SoldierInfo]: 兵种信息
        heroes[list(HeroInfo)]: 配置该兵种的所有英雄信息
    Returns:
        True: 成功
        False: 失败
    """
    if not soldier.upgrade():
        return False

    #更新所有配置该兵种的英雄的信息
    for hero in heroes:
        if not hero.update_soldier(soldier):
            return False

    return True


def unlock(user_id, basic_id):
    """
    解锁新兵种
    Args:
        user_id[int]: 用户 id
        basic_id[int]: 兵种 basic id
    Returns:
        SoldierInfo 兵种信息

    """
    soldier = SoldierInfo.create(user_id, basic_id)
    return soldier

