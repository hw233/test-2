#coding:utf8
"""
Created on 2016-05-17
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 政令值相关逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.energy import EnergyInfo
from app import log_formater


def init_energy(data, now):
    """创建政令信息
    """
    user = data.user.get(True)

    energy = EnergyInfo.create(data.id, user.level, user.vip_level, now)
    return energy


def buy_energy(data, energy, now):
    """购买政令值
    Returns:
        消耗的元宝数量
        小于0，表示兑换失败
    """
    user = data.user.get(True)
    gold_cost = energy.calc_gold_consume_of_buy_energy(user.vip_level)
    if gold_cost == -1:
        return -1

    resource = data.resource.get()
    original_gold = resource.gold
    if not resource.cost_gold(gold_cost):
        return -1

    energy.buy_energy()

    return gold_cost, original_gold


def refresh_energy(data, energy, now):
    """刷新政令(购买次数、trigger事件的次数)
    """
    if now > energy.next_refresh_time:
        energy.reset(now)

    return True



