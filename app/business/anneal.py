#coding:utf8
"""
Created on 2016-08-28
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 试炼场相关逻辑
"""

import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.anneal import AnnealInfo
from app.data.rival import RivalInfo
from app.data.team import TeamInfo
from app.data.item import ItemInfo
from app.core import reward as reward_module
from app import log_formater
from app.business import item as item_business
from app.business import hero as hero_business
#from app import pack


def init_anneal(data, now):
    """创建政令信息
    """
    user = data.user.get(True)

    anneal = AnnealInfo.create(data.id, now)
    
    return anneal


def buy_attack_num(data, anneal, item, now):
    """购买攻击次数
    Returns:
        消耗的元宝数量
        小于0，表示兑换失败
    """
    resource = data.resource.get()
    original_gold = resource.gold
    gold_cost = 0
    if item is not None:
        if not item.use_anneal_attack_num_item():
            return -1
    else:
        user = data.user.get(True)
        gold_cost = anneal.calc_gold_consume_of_buy_attack_num(user.vip_level)
        if gold_cost == -1:
            return -1

        if not resource.cost_gold(gold_cost):
            return -1

    anneal.buy_attack_num()

    return gold_cost, original_gold


def refresh_attack_num(anneal, now):
    """刷新攻击次数的信息
    """
    if now > anneal.next_refresh_time:
        anneal.reset(now)

    return True


def start_battle(data, anneal, type, floor, level, now):
    """开始试炼场战斗
    """
    anneal.update_current_attack_num(now) 
    if not anneal.cost_attack_num(1):
        return False

    if not anneal.start_battle(type, floor, level, now):
        logger.warning("anneal start battle failed")
        return False

    if 'is_open_new_anneal' in utils.get_flags() and type == AnnealInfo.HARD_MODE:
        if anneal.get_hrad_attack_remain_num(floor) <= 0:
            logger.warning("hard mode attack num not enough")
            return False

        if not anneal.cost_hard_attack_num(floor, 1):
            logger.warning("cost hard attack num failed")
            return False

    return _update_anneal_rival(data, anneal, type, floor, level)


def finish_battle(data, anneal, result):
    """结束试炼场战斗
    """
    anneal.finish_battle(result)
    return True


def start_sweep(data, anneal, direction, floor, total_time, attack_num, teams, heroes, now,
        mode=AnnealInfo.NORMAL_MODE):
    """开始扫荡
    """
    anneal.update_current_attack_num(now)

    if anneal.is_in_sweep():
        relieve_sweep(data, anneal)
     
    if not anneal.is_able_to_sweep((floor-1)/6 +1):
        logger.warning("Not able to sweep")
        return False

    if attack_num == None and total_time != None:
        attack_num = _get_sweep_num_by_time(total_time)
    elif total_time == None and attack_num != None:
        total_time = _get_time_by_sweep_num(attack_num)
    else:
        raise Exception("Bad args!")

    #扣减攻击次数
    if not anneal.cost_attack_num(attack_num):
        logger.warning("Not enough anneal attack num")
        return False

    if not anneal.start_sweep(floor, direction, total_time, attack_num, teams, heroes, now, mode):
        logger.warning("Start sweep failed")
        return False

    if 'is_open_new_anneal' in utils.get_flags() and mode == AnnealInfo.HARD_MODE:
        if not anneal.cost_hard_attack_num((floor-1)/6 +1, attack_num):
            logger.warning("Not enouth hard anneal attack num")
            return False

        if anneal.get_hrad_attack_remain_num((floor-1)/6 + 1) <= 0:
            anneal.set_sweep_at_least()

    #设置状态
    for team in teams:
        team.set_in_anneal_sweep((floor-1)/6 + 1)
    for hero in heroes:
        hero.set_in_anneal_sweep((floor-1)/6 + 1)

    return True


def finish_sweep(data, anneal, sweep_rewards, items, heroes, now):
    """
       sweep_reward : list(list(item_basic_id, item_num)) out 记录每轮扫荡的奖励
       items[list((ItemInfo)  out]
       heroes[list((basic_id, level, exp)元组)  out]
    """
    #根据扫荡时间来计算攻击次数
    #total_attack_num = data_loader.AnnealAttackNumConsumeData_dict[anneal.sweep_total_time].attack_num
    total_attack_num = anneal.sweep_attack_num
    #passed_time = min(anneal.sweep_total_time, now - anneal.sweep_start_time)
    passed_time = anneal.sweep_total_time
    actual_attack_num = int(1.0 * passed_time / anneal.sweep_total_time * total_attack_num)
    logger.debug("actual sweep cost attack num = %d" % actual_attack_num)

    if 'is_open_new_anneal' in utils.get_flags():
        if not calc_sweep_reward(data, anneal, actual_attack_num, sweep_rewards, items, now):
            logger.warning("get sweep income failed")
            return False
    else:
        if not calc_sweep_income(data, anneal, actual_attack_num, sweep_rewards, items, now):
            logger.warning("get sweep income failed")
            return False

    teams_index = anneal.get_sweep_teams_index()
    heroes_id = anneal.get_sweep_heroes_id()
    
    #计算扫荡英雄获得的经验
    user = data.user.get()
    total_exp = data_loader.MonarchLevelBasicInfo_dict[user.level].heroBattleExp * actual_attack_num
    exp = int(total_exp / len(heroes_id))
    for hero_id in heroes_id:
        hero = data.hero_list.get(hero_id)
        if not hero_business.level_upgrade(data, hero, exp, now):
            return False

    for team_index in teams_index:
        team_id = TeamInfo.generate_id(data.id, team_index)
        team = data.team_list.get(team_id)
        #解除队伍的扫荡状态
        team.clear_in_anneal_sweep()
    for hero_id in heroes_id:
        hero = data.hero_list.get(hero_id)
        #解除英雄的扫荡状态
        hero.clear_in_anneal_sweep()
        heroes.append((hero.basic_id, hero.level, hero.exp))

    anneal.finish_sweep()
    return True


def get_pass_reward(data, anneal, type):
    """领取过关奖励
    """
    #先判断是否可以领取
    if not anneal.is_able_to_get_pass_reward(type):
        logger.warning("not able to get pass reward")
        return False

    #获得奖励物品
    items_info = anneal.calc_pass_reward(type)
    if not item_business.gain_item(data, items_info, "pass reward", log_formater.PASS_REWARD):
        return False

    if not anneal.get_pass_reward(type):
        return False

    return True


def calc_resource_income(level):
    """计算试炼场战斗的资源奖励
        Returns:
            (奖励的金钱、粮草)
    """
    base_money = data_loader.MoneyExploitationBasicInfo_dict[level].reserves
    base_food = data_loader.FoodExploitationBasicInfo_dict[level].reserves

    ratio_mu = float(data_loader.AnnealConfInfo_dict["anneal_mu"].value)
    ratio_sigma = float(data_loader.AnnealConfInfo_dict["anneal_sigma"].value)
    ratio_min = float(data_loader.AnnealConfInfo_dict["anneal_num_min"].value)
    ratio_max = float(data_loader.AnnealConfInfo_dict["anneal_num_max"].value)

    random.seed()
    ratio_money = random.gauss(ratio_mu, ratio_sigma)
    ratio_money = max(ratio_money, ratio_min)
    ratio_money = min(ratio_money, ratio_max)
    ratio_food = random.gauss(ratio_mu, ratio_sigma)
    ratio_food = max(ratio_food, ratio_min)
    ratio_food = min(ratio_food, ratio_max)

    money = int(base_money * ratio_money)
    food = int(base_food * ratio_food)
    return (money, food)


def calc_sweep_income(data, anneal, attack_num, sweep_rewards, items, now):
    """计算试炼场战斗的扫荡奖励
       sweep_reward : list(list(item_basic_id, item_num)) out 记录每轮扫荡的奖励
       items[list((ItemInfo)  out]
    """
    #计算扫荡奖励
    reward_items = []
    is_normal = True
    reward_total_money = 0
    reward_total_food = 0
    for i in range(attack_num):
        if is_normal:
            type = AnnealInfo.NORMAL_MODE
            is_normal = not is_normal
        else:
            type = AnnealInfo.HARD_MODE
            is_normal = not is_normal

        #enemy的level
        level = anneal.get_anneal_enemy_level(type, anneal.sweep_floor, 
                AnnealInfo.LEVEL_NUM_PER_FLOOR)
    
        #随机奖励
        spoils = reward_module.random_anneal_spoils(level, type, 
                True, anneal.sweep_direction)
        for spoil in spoils:
            reward_items.append(spoil)

        #资源奖励
        (reward_money, reward_food) = calc_resource_income(level)
        reward_total_money += reward_money
        reward_total_food += reward_food

        sweep_rewards.append((reward_money, reward_food, spoils))    #返回每轮奖励

    resource = data.resource.get()
    resource.update_current_resource(now)
    resource.gain_money(reward_total_money)
    resource.gain_food(reward_total_food)
    
    if not item_business.gain_item(data, reward_items, "sweep reward", log_formater.SWEEP_REWARD):
        logger.warning("gain reward item failed")
        return False

    #合并重复的 item
    merge_items = {}
    for (basic_id, num) in reward_items:
        if basic_id not in merge_items:
            merge_items[basic_id] = num 
        else: 
            merge_items[basic_id] += num

    for key in merge_items:
        item_id = ItemInfo.generate_id(data.id, key)
        item = data.item_list.get(item_id)
        items.append(item)     #返回有变化的item列表

    return True


def _update_anneal_rival(data, anneal, type, floor, level):
    rival_id = anneal.generate_anneal_rival_id(type)
    rival = data.rival_list.get(rival_id)
    if rival is None:
        rival = RivalInfo.create(rival_id, data.id)
        data.rival_list.add(rival)

    #enemy的level
    level = anneal.get_anneal_enemy_level(type, floor, level)

    if anneal.get_hrad_attack_remain_num(floor) == 0 and 'is_open_new_anneal' in utils.get_flags():
        #在开启flag的情况下,最后一次为保底掉落
        at_least = True
    else:
        at_least = False
    
    #战斗pve随机奖励
    spoils = reward_module.random_anneal_spoils(level, type, at_least=at_least)
    logger.notice("SPOILS: %s" % spoils)

    #资源奖励
    (reward_money, reward_food) = calc_resource_income(level)

    rival.set_anneal(level, reward_money, reward_food, spoils)
    return True


def _get_sweep_num_by_time(sweep_time):
    """通过扫荡时间获取次数"""
    sweep_one_cost_time = int(float(data_loader.AnnealConfInfo_dict['sweep_one_cost_time'].value))
    return sweep_time /sweep_one_cost_time

def _get_time_by_sweep_num(sweep_num):
    """通过扫荡次数获取时间"""
    sweep_one_cost_time = int(float(data_loader.AnnealConfInfo_dict['sweep_one_cost_time'].value))
    return sweep_num * sweep_one_cost_time

def calc_sweep_reward(data, anneal, attack_num, sweep_rewards, items, now):
    """扫荡奖励(新版)"""
    reward_total_money = 0
    reward_total_food = 0
    reward_items = []

    for i in xrange(attack_num):
        level = anneal.get_anneal_enemy_level(anneal.sweep_mode, anneal.sweep_floor,
                AnnealInfo.LEVEL_NUM_PER_FLOOR)

        at_least = False
        if i == attack_num - 1 and anneal.sweep_at_least:
            """保底掉落"""
            at_least = True

        #随机奖励
        spoils = reward_module.random_anneal_spoils(anneal.sweep_floor, anneal.sweep_mode, True,
                anneal.sweep_direction, at_least)
        reward_items.extend(spoils)

        #资源奖励
        (reward_money, reward_food) = calc_resource_income(level)
        reward_total_money += reward_money
        reward_total_food += reward_food

        sweep_rewards.append((reward_money, reward_food, spoils))    #返回每轮奖励
    
    resource = data.resource.get()
    resource.update_current_resource(now)
    resource.gain_money(reward_total_money)
    resource.gain_food(reward_total_food)

    if not item_business.gain_item(data, reward_items, "new sweep reward", log_formater.NEW_SWEEP_REWARD):
        logger.warning("gain reward item failed")
        return False

    #合并重复的 item
    merge_items = {}
    for (basic_id, num) in reward_items:
        if basic_id not in merge_items:
            merge_items[basic_id] = num 
        else: 
            merge_items[basic_id] += num

    for key in merge_items:
        item_id = ItemInfo.generate_id(data.id, key)
        item = data.item_list.get(item_id)
        items.append(item)     #返回有变化的item列表

    return True


def reset_hard_attack_num(data, floor, now, ret):
    """重置困难模式攻击次数"""
    #1.消耗元宝
    #2.清空次数
    user = data.user.get(True)
    resource = data.resource.get()
    resource.update_current_resource(now)
    anneal = data.anneal.get()

    buy_num = anneal.get_hard_reset_num(floor) + 1
    if buy_num not in data_loader.AnnealHardAttackNumBuyData_dict:
        ret.setup("VIP_NOT_ENOUGH")
        return False

    if user.vip_level < data_loader.AnnealHardAttackNumBuyData_dict[buy_num].limitVipLevel:
        ret.setup("VIP_NOT_ENOUGH")
        return False

    original_gold =  resource.gold
    cost_gold = data_loader.AnnealHardAttackNumBuyData_dict[buy_num].gold
    if not resource.cost_gold(cost_gold):
        ret.setup("GOLD_NOT_ENOUGH")
        return False
    log = log_formater.output_gold(data, -cost_gold, log_formater.RESET_HARD_ATTACK,
                "reset hard attack num by gold", before_gold = original_gold)
    logger.notice(log)
    anneal.reset_hard_attack_num(floor)
    return True

def relieve_sweep(data, anneal):
    """解除扫荡"""
    teams_index = anneal.get_sweep_teams_index()
    heroes_id = anneal.get_sweep_heroes_id()

    for team_index in teams_index:
        team_id = TeamInfo.generate_id(data.id, team_index)
        team = data.team_list.get(team_id)
        #解除队伍的扫荡状态
        team.clear_in_anneal_sweep()
    for hero_id in heroes_id:
        hero = data.hero_list.get(hero_id)
        #解除英雄的扫荡状态
        hero.clear_in_anneal_sweep()

    anneal.finish_sweep()
