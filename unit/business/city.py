#coding:utf8
"""
Created on 2016-05-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城逻辑
"""

import random
from utils import logger
from datalib.data_loader import data_loader
from unit.data.city import UnitCityInfo
from unit.data.position import UnitPositionInfo


def init_city(data, now):
    """初始化史实城
    """
    city_id = data.id
    city = UnitCityInfo.create(city_id)
    data.city.add(city)

    #用 PVE 数据填满史实城官职榜
    for key in data_loader.LegendCityPositionBasicInfo_dict:
        info = data_loader.LegendCityPositionBasicInfo_dict[key]
        if info.cityId == city_id:
            _init_position_with_robot(data, city_id, info, now)

    return True


def _init_position_with_robot(data, city_id, info, now):
    """用机器人初始化史实城官职榜
    """
    random.seed()
    ids = random.sample(info.defaultRobotsId, info.totalNum)
    for id in ids:
        position = UnitPositionInfo.create(city_id, id, now, True)
        position.change_level(info.level, now)
        data.position_list.add(position)


def try_calc_today_tax_income(data, now):
    """结算今日税收，给太守
    """
    city = data.city.get()
    if not city.is_able_to_calc_income(now):
        return

    for position in data.position_list.get_all(True):
        if position.is_leader():
            if not position.is_robot:
                leader_position = data.position_list.get(position.id)
                leader_position.gain_reputation(city.tax_income)
                city.reset_income(now)
            return


def swap_position(data, user_position, rival_position, now):
    """交换官职
    """
    #如果对手是太守，结算税收收益
    if rival_position.is_leader():
        city = data.city.get()
        rival_position.gain_reputation(city.tax_income)
        city.reset_income(now)
        city.reset_tax()
        city.reset_slogan()

    #交换官职
    assert user_position.level < rival_position.level
    level = user_position.level
    user_position.change_level(rival_position.level, now)
    rival_position.change_level(level, now)
    logger.debug("Swap position[up id=%d][up position level=%d]"
            "[down id=%d][down position level=%d]" %
            (user_position.user_id, user_position.level,
                rival_position.user_id, rival_position.level))


def cancel_position(data, user_position, now):
    """取消玩家的官职，用机器人代替
    """
    if user_position.level == 0:
        return

    key = "%d_%d" % (data.id, user_position.level)
    info = data_loader.LegendCityPositionBasicInfo_dict[key]

    #选择一个合适的机器人帐号，进行交换排名
    for robot_id in info.defaultRobotsId:
        position_id = UnitPositionInfo.generate_id(data.id, robot_id)
        robot_position = data.position_list.get(position_id)
        if robot_position is not None and robot_position.level > 0:
            continue

        if robot_position is None:
            robot_position = UnitPositionInfo.create(data.id, robot_id, now, True)
            data.position_list.add(robot_position)

        #新的机器人的锁状态继承玩家的锁状态
        robot_position.is_locked = user_position.is_locked
        robot_position.lock_time = user_position.lock_time
        return swap_position(data, robot_position, user_position, now)

    #非预期，选择任一 level = 0 的机器人帐号，进行交换
    logger.warning("Can not found a suitable robot")
    for position in data.position_list.get_all():
        if position.level == 0 and position.is_robot:
            robot_position.is_locked = user_position.is_locked
            robot_position.lock_time = user_position.lock_time
            return swap_position(data, position, user_position, now)

    raise Exception("Cancel position invalid")


def query_position(data, user_id, user_position_level,
        rivals_info, now, rematch_position_level = 0):
    """查询史实城信息，包括：
    1 匹配的官职榜信息
    2 自己的信息
    Args:
        data[CityInfo]
        user_id[int]: 玩家 id
        user_position_level[int]: 玩家官职等级
        rivals_info[list((user_id, position_level))]: 玩家之前匹配到的对手信息
        rematch_position_level[bool]: 强制重新匹配对手的官职
    """
    #计算每个官职需要匹配的对手数目
    city = data.city.get(True)
    need_rival_count = {}
    for key in data_loader.LegendCityPositionBasicInfo_dict:
        info = data_loader.LegendCityPositionBasicInfo_dict[key]
        if info.cityId == city.id:
            need_rival_count[info.level] = info.displayNum
    if user_position_level != 0:
        #玩家自己的官职，可以少匹配一人，因为会显示玩家自己
        need_rival_count[user_position_level] -= 1

    #过滤失效的对手信息
    invalid_rivals = []
    disallow_rivals = [user_id] #不匹配自己

    for (rival_id, position_level) in rivals_info:
        id = UnitPositionInfo.generate_id(city.id, rival_id)
        position = data.position_list.get(id, True)

        if position is None:
            invalid_rivals.append(rival_id)
        elif position.level != position_level:
            #1 官职发生了改变的对手，为失效的对手
            invalid_rivals.append(rival_id)
        elif rematch_position_level != 0 and position.level == rematch_position_level:
            #2 强制重新匹配的对手
            invalid_rivals.append(rival_id)
            disallow_rivals.append(rival_id)
        else:
            need_rival_count[position_level] -= 1
            disallow_rivals.append(rival_id)

    #对于失效的对手，需要匹配相同数量的新对手
    new_rivals = _match_rivals(data, need_rival_count, disallow_rivals)

    return (invalid_rivals, new_rivals)


def query_user_position(data, user_id, now):
    """查询玩家信息
    如果不存在，初始化一份
    尝试结算声望收益
    """
    id = UnitPositionInfo.generate_id(data.id, user_id)
    position = data.position_list.get(id)
    if position is None:
        position = UnitPositionInfo.create(data.id, user_id, now)
        data.position_list.add(position)

    if position.is_able_to_gain_position_reputation(now):
        position.update_reputation(now)

    return position


def _match_rivals(data, need_info, disallow_info):
    """配置对手
    Args:
        data
        need_info[dict<position_level, count>]: 在官职上需要匹配的对手人数
        disallow_info[list(user_id)]: 禁止被匹配到的对手 user id
    """
    match = []

    all_position = {}
    for position in data.position_list.get_all(True):
        if position.level == 0:
            continue
        if position.user_id in disallow_info:#除去禁止被匹配到的玩家
            continue

        if position.level not in all_position:
            all_position[position.level] = []
        all_position[position.level].append(position)

    for level in need_info:
        count = need_info[level]
        if count <= 0:
            continue

        random.seed()
        choose = random.sample(all_position[level], count)
        match.extend(choose)

    return match


def is_able_to_update(data, user_id):
    """是否有权限更新史实城信息
    """
    #只有太守有权利
    id = UnitPositionInfo.generate_id(data.id, user_id)
    position = data.position_list.get(id, True)
    if not position.is_leader():
        logger.warning("User is not allowed to update[user id=%d][position level=%d]" %
                (user_id, position.level))
        return False
    return True


def update(data, slogan = None, tax = None, gold = 0):
    """更新史实城信息
    """
    city = data.city.get()
    if slogan is not None:
        return city.change_slogan(slogan, gold)
    elif tax is not None:
        return city.change_tax(tax, gold)

    logger.warning("Nothing to update")
    return False



