#coding:utf8
"""
Created on 2015-09-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief: 随机产生奖励
"""

import random
from utils import logger
from datalib.data_loader import data_loader
from app.data.reward import DungeonRewardPool
from app.data.reward import OfflineExploitRewardPool
from app.data.anneal import AnnealInfo

GIFT_TYPE_BATTLE = 1
GIFT_TYPE_EXPLOITATION = 2
GIFT_TYPE_JUNGLE = 3


def random_starsoul_spoils():
    """计算战斗获得的将魂石物品
    """
    ratio = float(
            data_loader.OtherBasicInfo_dict["PVPGetStarsoulRatio"].value) / 100.0
    assert ratio >= 0.0 and ratio <= 1.0

    random.seed()
    if random.random() <= ratio:
        return _random_starsoul()
    else:
        return []


def _random_starsoul():
    """随机将魂石
    在当前版本允许的武将将魂石中随机
    """
    random.seed()
    hero_basic_id = random.sample(data_loader.HeroAvailableInfo_dict.keys(), 1)[0]
    item_basic_id = data_loader.HeroBasicInfo_dict[hero_basic_id].starSoulBasicId
    return [(item_basic_id, 1)]


def random_battle_gift(level):
    """随机战斗胜利的礼品
    """
    return _random_gift(GIFT_TYPE_BATTLE, level)


def random_jungle_gift(level):
    """随机战斗胜利的礼品
    """
    return _random_gift(GIFT_TYPE_JUNGLE, level)


def random_exploit_gift(level, ratio):
    """随机采集的礼品
    """
    return _random_gift(GIFT_TYPE_EXPLOITATION, level, ratio)


def random_exploit_material(level, count):
    """计算材料矿的收益
    Returns:
        list((item_basic_id, item_num))
    """
    pool = data_loader.MaterialExploitationBasicInfo_dict[level]
    length = len(pool.itemsBasicId)
    assert length == len(pool.itemsNum)
    assert length == len(pool.itemsWeight)

    total_weight = 0
    for weight in pool.itemsWeight:
        total_weight += weight

    random.seed()
    items = []
    while len(items) < count:
        roll_weight = random.randint(0, total_weight)

        cur_weight = 0
        for index in range(0, length):
            cur_weight += pool.itemsWeight[index]
            if roll_weight <= cur_weight:
                items.append((pool.itemsBasicId[index], pool.itemsNum[index]))
                break

    return items


def random_pve_spoils(level):
    """计算 PVE 战利品
    根据 PVE 敌人等级随机计算
    """
    name = "%s_dict" % data_loader.PVERewardLevelBasicInfo_dict[level].poolName
    pool = getattr(data_loader, name)

    num_min = int(float(data_loader.MapConfInfo_dict["pve_reward_num_min"].value))
    num_max = int(float(data_loader.MapConfInfo_dict["pve_reward_num_max"].value))
    num_mu = float(data_loader.MapConfInfo_dict["pve_reward_num_mu"].value)
    num_sigma = float(data_loader.MapConfInfo_dict["pve_reward_num_sigma"].value)

    random.seed()
    num = int(random.gauss(num_mu, num_sigma))
    num = max(num, num_min)
    num = min(num, num_max)

    return _random(pool, num)


def random_anneal_spoils(level, mode, is_sweep = False, sweep_direction = 0, at_least = False):
    """计算 试炼场战利品
    根据敌人等级、选择的困难模式、是否扫荡以及扫荡的方向 随机计算
    at_least:是否是保底奖励
    """
    if mode == AnnealInfo.NORMAL_MODE:
        if not is_sweep:
            name = "%s_dict" % data_loader.AnnealRewardLevelBasicInfo_dict[level].poolName
        else:
            key = "%s_%s" % (level, sweep_direction)
            name = "%s_dict" % data_loader.SweepRewardLevelBasicInfo_dict[key].poolName

    elif mode == AnnealInfo.HARD_MODE:
        if not is_sweep:
            name = "%s_dict" % data_loader.AnnealHardRewardLevelBasicInfo_dict[level].poolName
        else:
            key = "%s_%s" % (level, sweep_direction)
            name = "%s_dict" % data_loader.SweepHardRewardLevelBasicInfo_dict[key].poolName

    pool = getattr(data_loader, name)

    num_min = int(float(data_loader.AnnealConfInfo_dict["anneal_reward_num_min"].value))
    num_max = int(float(data_loader.AnnealConfInfo_dict["anneal_reward_num_max"].value))
    num_mu = float(data_loader.AnnealConfInfo_dict["anneal_reward_num_mu"].value)
    num_sigma = float(data_loader.AnnealConfInfo_dict["anneal_reward_num_sigma"].value)

    random.seed()
    num = int(random.gauss(num_mu, num_sigma))
    num = max(num, num_min)
    num = min(num, num_max)

    reward = _random(pool, num)

    if at_least:
        """算上保底奖励"""
        least_reward = _anneal_least_reward(level, mode, is_sweep, sweep_direction)
        reward.extend(least_reward)

    return reward

def _anneal_least_reward(level, mode, is_sweep, sweep_direction):
    """试炼场保底奖励"""
    if mode == AnnealInfo.NORMAL_MODE:
        if not is_sweep:
            name = "%s_dict" % data_loader.AnnealRewardLevelBasicInfo_dict[level].poolName
            least_list = data_loader.AnnealRewardLevelBasicInfo_dict[level].least
        else:
            key = "%s_%s" % (level, sweep_direction)
            name = "%s_dict" % data_loader.SweepRewardLevelBasicInfo_dict[key].poolName
            least_list = data_loader.SweepRewardLevelBasicInfo_dict[key].least

    elif mode == AnnealInfo.HARD_MODE:
        if not is_sweep:
            name = "%s_dict" % data_loader.AnnealHardRewardLevelBasicInfo_dict[level].poolName
            least_list =  data_loader.AnnealHardRewardLevelBasicInfo_dict[level].least
        else:
            key = "%s_%s" % (level, sweep_direction)
            name = "%s_dict" % data_loader.SweepHardRewardLevelBasicInfo_dict[key].poolName
            least_list = data_loader.SweepHardRewardLevelBasicInfo_dict[key].least

    win = {}
    pool = getattr(data_loader, name)
    for id in least_list:
        item_id = pool[id].itemBasicId
        item_num = pool[id].itemNum
        if item_id in win:
            win[item_id] += item_num
        else:
            win[item_id] = item_num

    return win.items()

def _random_gift(type, level, ratio = 1.0):
    """计算随机物品奖励
    """
    assert ratio >= 0.0 and ratio <= 1.0

    key = "%s_%s" % (type, level)
    name = "%s_dict" % data_loader.RandomRewardMatchBasicInfo_dict[key].poolName
    pool = getattr(data_loader, name)

    num_min = int(float(data_loader.MapConfInfo_dict["random_reward_num_min"].value))
    num_max = int(float(data_loader.MapConfInfo_dict["random_reward_num_max"].value))
    num_mu = float(data_loader.MapConfInfo_dict["random_reward_num_mu"].value)
    num_sigma = float(data_loader.MapConfInfo_dict["random_reward_num_sigma"].value)

    random.seed()
    num = int(random.gauss(num_mu, num_sigma))
    num = max(num, num_min)
    num = min(num, num_max)

    num = int(num * ratio)
    return _random(pool, num)


def _random(pool, num):
    """抽取，在 pool 中抽取 num 个项
       物品抽取的概率 = weight / total_weight
    Args:
        pool: 选择池
        num: 最终选出的项的个数
    Returns:
        list((item_basic_id, item_num)) 最终选出的项，重复项合并
    """
    if num == 0:
        return []

    assert num > 0
    assert len(pool) > 0

    total_weight = 0
    for id in pool:
        total_weight += pool[id].weight

    win = {}
    win_num = 0
    random.seed()
    while win_num < num:
        roll = random.randint(0, total_weight-1)

        sum = 0
        for id in pool:
            sum += pool[id].weight
            if roll < sum:
                basic_id = pool[id].itemBasicId
                item_num = pool[id].itemNum
                if basic_id in win:
                    win[basic_id] += item_num
                else:
                    win[basic_id] = item_num

                win_num += 1
                logger.debug("choose[id=%d]" % id)
                break

    win_list = []
    for basic_id in win:
        win_list.append((basic_id, win[basic_id]))
    return win_list


def random_dungeon_spoils(dungeon_id, level):
    """计算副本战利品
    """
    num_min = int(float(data_loader.MapConfInfo_dict["dungeon_reward_num_min"].value))
    num_max = int(float(data_loader.MapConfInfo_dict["dungeon_reward_num_max"].value))
    num_mu = float(data_loader.MapConfInfo_dict["dungeon_reward_num_mu"].value)
    num_sigma = float(data_loader.MapConfInfo_dict["dungeon_reward_num_sigma"].value)

    random.seed()
    num = int(random.gauss(num_mu, num_sigma))
    num = max(num, num_min)
    num = min(num, num_max)

    return DungeonRewardPool().random(dungeon_id, level, num)


def random_pray_gift(type, building_level):
    """计算祈福的礼品
      祈福的奖励分3段，需要从三个奖池里去随机
    """
    key = "%s_%s" % (type, building_level)
    pray_basic = data_loader.PrayRewardBasicInfo_dict[key]
    first_name = "%s_dict" % pray_basic.firstPoolName
    second_name = "%s_dict" % pray_basic.secondPoolName
    third_name = "%s_dict" % pray_basic.thirdPoolName
    first_index_min = int(float(pray_basic.firstPoolIndexMin))
    first_index_max = int(float(pray_basic.firstPoolIndexMax))
    second_index_min = int(float(pray_basic.secondPoolIndexMin))
    second_index_max = int(float(pray_basic.secondPoolIndexMax))
    third_index_min = int(float(pray_basic.thirdPoolIndexMin))
    third_index_max = int(float(pray_basic.thirdPoolIndexMax))
    
    first_pool = getattr(data_loader, first_name)
    second_pool = getattr(data_loader, second_name)
    third_pool = getattr(data_loader, third_name)
    first_num = first_index_max - first_index_min + 1
    second_num = second_index_max - second_index_min + 1
    third_num = third_index_max - third_index_min + 1

    pray_list = []

    pray_list.extend(_random_pray(first_pool, first_num))
    pray_list.extend(_random_pray(second_pool, second_num)) 
    pray_list.extend(_random_pray(third_pool, third_num))

    return pray_list


def _random_pray(pool, num):
    """抽取，在 pool 中抽取 num 个项
       物品抽取的概率 = weight / total_weight
    Args:
        pool: 选择池
        num: 最终选出的项的个数
    Returns:
        list((item_basic_id, item_num)) 最终选出的项，重复项不合并
    """
    if num == 0:
        return []

    assert num > 0
    assert len(pool) > 0

    total_weight = 0
    for id in pool:
        total_weight += pool[id].weight

    win = {}
    win_num = 0
    random.seed()
    win_list = []
    while win_num < num:
        roll = random.randint(0, total_weight-1)
        
        sum = 0
        for id in pool:
            sum += pool[id].weight
            if roll < sum:
                basic_id = pool[id].itemBasicId
                item_num = pool[id].itemNum
                
                win_list.append((basic_id, item_num))

                logger.debug("choose[id=%d]" % id)
                break
        win_num += 1

    return win_list


def random_exploit_offline(event_type, level, num):
    """计算离线开采事件的奖励
    """
    return OfflineExploitRewardPool().random(event_type, level, num)


def random_country_spoils():
    """国家势力、国战奖励
    """
    item_basic_id = int(float(data_loader.OtherBasicInfo_dict["item_country_id"].value))
    item_num = 1

    item_list = []
    item_list.append((item_basic_id, item_num))
    return item_list




