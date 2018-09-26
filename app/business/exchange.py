#coding:utf8
"""
Created on 2016-07-03
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 兑换逻辑
"""

from datalib.global_data import DataBase
from utils import utils
from datalib.data_loader import data_loader
from proto import exchange_pb2

MONEY_TO_FOOD = exchange_pb2.MONEYTOFOOD
FOOD_TO_MONEY = exchange_pb2.FOODTOMONEY

def reset_exchange_num(data, now):
    """重置刷新次数"""
    user = data.user.get()
    if not utils.is_same_day(user.last_refresh_exchange_time, now):
        user.exchange_num = user.day_exchange_num()
        user.last_refresh_exchange_time = now

def get_exchange_resource(data):
    """获取兑换物最大数量"""
    user = data.user.get(True)
    money = data_loader.MonarchLevelBasicInfo_dict[user.level].moneyToExchange
    food = data_loader.MonarchLevelBasicInfo_dict[user.level].foodToExchange
    return (money, food)

def is_able_to_exchange(data, money, food, exchange_type, now):
    """是否能够兑换"""
    resource = data.resource.get()
    resource.update_current_resource(now)
    if exchange_type == MONEY_TO_FOOD:
        is_resource = money <= resource.money
    else:
        is_resource = food <= resource.food
    
    user = data.user.get(True)
    is_num = user.exchange_num > 0

    if is_num and is_resource:
        return True
    else:
        if not is_resource:
            return exchange_pb2.EXCHANGE_NO_RESOURCE
        else:
            return exchange_pb2.EXCHANGE_NO_NUM

def food_exchange(data, money, food, now):
    """粮食兑换成金币"""
    resource = data.resource.get()
    resource.update_current_resource(now)

    resource.cost_food(food)
    resource.gain_money(money)

    user = data.user.get()
    user.exchange_num -= 1


def money_exchange(data, money, food, now):
    """金币兑换成粮食"""
    resource = data.resource.get()
    resource.update_current_resource(now)

    resource.cost_money(money)
    resource.gain_food(food)

    user = data.user.get()
    user.exchange_num -= 1

def check_exchange_req(data, message, food_proportion, money_proportion):
    """检查请求的合法性"""
    (money, food) = get_exchange_resource(data)

    if message.type == MONEY_TO_FOOD:
        return 0 < message.money <= money and message.food == int(message.money * money_proportion)
    else:
        return 0 < message.food <= food and message.money == int(message.food * food_proportion)