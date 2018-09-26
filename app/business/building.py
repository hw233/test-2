#coding:utf8
"""
Created on 2015-01-26
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 建筑物相关数值计算
"""

import time
from utils import logger
from utils.ret import Ret
from datalib.data_loader import data_loader
from app.data.defense import DefenseInfo
from app.data.conscript import ConscriptInfo
from app.data.technology import TechnologyInfo
from app.core import building as building_module
from app.core import resource as resource_module
from app.core import battle as battle_module
from app.core import defense as defense_module
from app.business import hero as hero_business
from app.business import user as user_business
from app import log_formater


def start_upgrade(building, resource, heroes, technologys, user, mansion, now):
    """开始升级建筑
    Args:
        buildig[BuildingInfo out]: 建筑信息
        resource[ResourceInfo out]: 资源信息
        heroes[list(HeroInfo) out]: 参与建造的英雄, 可能有None
        technologys[list(TechnologhInfo)]: 起作用的非战斗科技
        user_level[int]: 用户等级
        mansion_level[int]: 官邸等级
    Returns:
        True 开始升级成功
        False 开始升级失败
    """
    #检查是否满足了升级依赖
    if not building.is_able_to_upgrade(user.level, mansion.level):
        logger.warning("Building is not able to start upgrading")
        return False

    #升级需要消耗金钱、粮草
    (need_money, need_food) = building_module.calc_consume_resource(
            building, heroes, technologys)
    if (not resource.cost_money(need_money) or
            not resource.cost_food(need_food)):
        return False

    #升级需要耗费时间
    need_time = building_module.calc_consume_time(building, heroes, technologys, user)

    #指派英雄参与
    for hero in heroes:
        if hero is not None and not hero.assign_working_in_building(building.id, now):
            return False

    #开始升级
    if not building.start_upgrade(need_money, need_food, need_time, heroes, now):
        return False

    return True


def finish_upgrade(data, building, resource, user, heroes, now, force = False, ret = Ret()):
    """完成建筑升级
    1 可以使用元宝加速完成升级
    2 结算英雄和用户经验
    Args:
        building[BuildingInfo out]: 建筑信息
        resource_info[ResourceInfo out]: 资源信息
        user[UserInfo out]: 用户信息
        heroes[list(HeroInfo) out]: 英雄信息列表
        now[int]: 当前时间戳
        force[bool]: 是否强制完成，强制完成需要花费元宝
    Returns:
        True 顺利完成升级
        False 建筑物完成升级失败
    """
    #查看是否开启了支持剩余时间不多时建造立即完成的功能
    open_flags = get_flags()
    can_finish_immediately = False
    if "is_open_buildinglist" in open_flags:
        can_finish_immediately = True
    
    if (building.calc_time_gap_of_finish_upgrade(now) > 
        data_loader.VipBasicInfo_dict[user.vip_level].finishImediatelyTime):
        can_finish_immediately = False

    if can_finish_immediately:
        force = True

    #判断是否可以完成升级
    if not building.is_able_to_finish_upgrade(heroes, now, force, ret):
        logger.warning("Building is not able to finish upgrading")
        return False

    #如果强制完成：加速建造，需要花费元宝兑换时间
    gap = 0
    need_gold = 0
    original_gold = resource.gold
    if force:
        gap = building.calc_time_gap_of_finish_upgrade(now)

        if can_finish_immediately:
            need_gold = 0
        else:
            need_gold = resource.gold_exchange_time(gap)
            if need_gold < 0:
                return False

    #结算升级的经验
    if not _calc_build_exp(data, building, user, heroes, now):
        return False

    #结束升级
    if not building.finish_upgrade(heroes):
        return False

    #英雄结束工作
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False

    #尝试解锁驻守位
    building.unlock_garrison_position(user.vip_level)
   
    if force and not can_finish_immediately:
        log = log_formater.output_gold(data, -need_gold, log_formater.FINISH_BUILDING,
                "Finish building by gold", before_gold = original_gold, reduce_time = gap)
        logger.notice(log)
    
    return True


def cancel_upgrade(data, building, resource, user, heroes, now):
    """取消升级
    Args:
        building[BuildingInfo out]: 建筑信息
        resource_info[ResourceInfo out]: 资源信息
        user[UserInfo out]: 用户信息
        heroes[list(HeroInfo) out]: 英雄信息列表
        now[int]: 当前时间戳
    Returns:
        True 成功
        False 失败
    """
    if not building.is_able_to_cancel_upgrade(heroes):
        logger.warning("Building is not able to cancel upgrading")
        return False

    #退还部分金钱、粮草
    (remittal_money, remittal_food) = building.calc_resource_remittal_of_cancel_upgrade()
    resource.gain_money(remittal_money)
    resource.gain_food(remittal_food)

    #取消升级
    if not building.cancel_upgrade(heroes):
        return False

    #英雄结束工作
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False

    return True


def _calc_build_exp(data, building, user, heroes, now):
    """参与升级，英雄可以获得的经验，用户（主公）也可以获得经验
    在建升级完成之后，经验才会结算
    Args:
        building[BuildingInfo out]: 建筑信息
        user[UserInfo]: 用户（主公）信息
        heroes[list(HeroInfo) out]: 英雄信息列表
        now[int]: 当前时间戳
    Returns:
        True 计算成功
        False 计算失败
    """
    #用户得到经验
    base_exp = int(float(data_loader.OtherBasicInfo_dict["BuildingMonarchGetExp"].value))
    user_exp = (int(user.level / 10) + 1) * base_exp
    if not user_business.level_upgrade(data, user_exp, now, "building exp", log_formater.EXP_BUILDING):
        logger.warning("User upgrade failed")
        return False

    #英雄经验
    #如果使用『立即完成』，英雄也只会获得到到当前时间为止的经验
    end_time = min(building.upgrade_start_time + building.upgrade_consume_time, now)
    exp_per_hour = data_loader.MonarchLevelBasicInfo_dict[user.level].buildExpPerHour
    for hero in heroes:
        if hero is None:
            continue
        if not hero_business.level_upgrade_by_working(
                data, hero, exp_per_hour, end_time, now):
            logger.warning("Hero upgrade failed[hero basic id=%d]" % hero.basic_id)
            return False

    return True


def pre_upgrade(building, now, resource = None, heroes = []):
    """建筑物开始升级前的处理
    """
    if building.is_farmland():
        return _pre_upgrade_for_farmland(building, resource, heroes, now)
    elif building.is_market():
        return _pre_upgrade_for_market(building, resource, heroes, now)

    return True


def post_upgrade(data, building, now, heroes = [], technology = [],
        resource = None, defense = None, conscript = None,
        new_technology = [], new_defense = [], new_conscript = []):
    """建筑物升级完成后的后续处理
    """
    if building.is_farmland():
        return _post_upgrade_for_farmland(building, resource, heroes, technology, now)
    elif building.is_market():
        return _post_upgrade_for_market(building, resource, heroes, technology, now)
    elif building.is_barrack():
        return _post_upgrade_for_barrack(building, resource, technology, conscript,
                new_conscript)
    elif building.is_mansion():
        return _post_upgrade_for_mansion(data, building, resource, technology, now)
    elif building.is_defense():
        return _post_upgrade_for_defense(data, building, technology, defense, new_defense)
    elif building.is_generalhouse():
        return _post_upgrade_for_general_house(data, building, new_technology)
    elif building.is_moneyhouse():
        return _post_upgrade_for_moneyhouse(building, resource, heroes, technology, now)
    elif building.is_foodhouse():
        return _post_upgrade_for_foodhouse(building, resource, heroes, technology, now)
    elif building.is_watchtower():
        return _post_upgrade_for_watchtower(data, building)
    return True


def is_need_destroy(building):
    """判断建筑物是否要摧毁
    """
    #当建筑物等级为0，需要删除
    return building.level == 0


def post_cancel(building, now, heroes = [], technology = [], resource = None):
    """建筑物取消升级，或者取消建造 的后续处理
    """
    if building.is_farmland():
        return _post_cancel_for_farmland(building, resource, heroes, technology, now)
    elif building.is_market():
        return _post_cancel_for_market(building, resource, heroes, technology, now)

    return True


def update_building_with_interior_technology(building, heroes, resource,
        data, new_technology, pre_technology = None):
    """更新由某项内政升级带来的建筑资源产量或容量、城防值的变更
    """
    assert new_technology is not None
    new_technologys = [new_technology]

    if pre_technology is None:
        pre_technologys = []
    else:
        pre_technologys = [pre_technology]

    #变更资源产量
    if building.is_farmland():
        output_delta = (
            resource_module.calc_food_output(building, heroes, new_technologys) -
            resource_module.calc_food_output(building, heroes, pre_technologys))

        resource.update_food_output(resource.food_output + output_delta) #变更粮食产量
        building.value += output_delta
    elif building.is_market():
        output_delta = (
            resource_module.calc_money_output(building, heroes, new_technologys) -
            resource_module.calc_money_output(building, heroes, pre_technologys))

        resource.update_money_output(resource.money_output + output_delta) #变更金钱产量
        building.value += output_delta
    #兵营征兵速度不需要变，在开始征兵时才生效

    #变更资源容量
    food_capacity_delta = (
        building_module.calc_food_capacity(building.basic_id, building.level, new_technologys) -
        building_module.calc_food_capacity(building.basic_id, building.level, pre_technologys))

    money_capacity_delta = (
        building_module.calc_money_capacity(building.basic_id, building.level, new_technologys) -
        building_module.calc_money_capacity(building.basic_id, building.level, pre_technologys))

    resource.update_food_capacity(resource.food_capacity + food_capacity_delta) #变更粮食容量
    resource.update_money_capacity(resource.money_capacity + money_capacity_delta) #变更金钱容量

    if building.is_barrack():
        soldier_capacity_delta = (
            building_module.calc_soldier_capacity(building.basic_id, building.level, new_technologys) -
            building_module.calc_soldier_capacity(building.basic_id, building.level, pre_technologys))

        conscript = data.conscript_list.get(building.id)
        conscript.update_soldier_capacity(conscript.soldier_capacity + soldier_capacity_delta) #变更士兵容量

    elif building.is_defense():
        defense = data.defense_list.get(building.id)
        defense_value_delta = (
            defense_module.calc_defense_value(defense, new_technologys) -
            defense_module.calc_defense_value(defense, pre_technologys))

        defense.update_defense_value(defense.defense_value + defense_value_delta) #变更城防值

    return True


def _pre_upgrade_for_farmland(building, resource, heroes, now):
    """农场即将进行升级时，需要进行的处理
    1 移除驻守的英雄
    2 不再产粮，直到升级完成
    """
    #对于农田建筑，building.value 存储粮食产量
    resource.update_food_output(resource.food_output - building.value)

    #移除英雄
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False

    #停止工作
    if not building.stop_working(heroes, 0):
        return False

    return True


def _post_upgrade_for_farmland(building, resource, heroes, technology, now):
    """农场结束升级的后续影响
    1 派驻英雄
    2 开始产粮
    3 影响粮食库存上限
    """
    capacity_delta = (
            building_module.calc_food_capacity(building.basic_id, building.level, technology) -
            building_module.calc_food_capacity(building.basic_id, building.level-1, technology))

    output = resource_module.calc_food_output(building, heroes, technology)
    output_delta = output - building.value

    resource.update_food_capacity(resource.food_capacity + capacity_delta)
    resource.update_food_output(resource.food_output + output_delta)

    #农田升级完成后，参与升级的英雄直接入驻，进行生产工作
    for hero in heroes:
        if hero is not None and not hero.assign_working_in_building(building.id, now):
            return False

    if not building.start_working(heroes, output, False):
        return False

    return True


def _post_cancel_for_farmland(building, resource, heroes, technology, now):
    """农场取消升级、取消建造的后续处理
    """
    if building.level == 0:
        #取消建造，建筑物会被删除
        #不再派驻英雄
        return True
    else:
        #取消升级，不影响粮食库存上限
        #影响粮食产量
        output = resource_module.calc_food_output(building, heroes, technology)
        output_delta = output - building.value

        resource.update_food_output(resource.food_output + output_delta)

        #参与升级的英雄直接入驻，进行生产工作
        for hero in heroes:
            if hero is not None and not hero.assign_working_in_building(building.id, now):
                return False

        if not building.start_working(heroes, output, False):
            return False

        return True


def _pre_upgrade_for_market(building, resource, heroes, now):
    """市场即将进行升级时，需要进行的处理
    1 移除驻守的英雄
    2 不再产钱，直到升级完成
    """
    #移除英雄
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False

    #对于市场建筑，building.value 存储金钱产量
    resource.update_money_output(resource.money_output - building.value)

    #停止工作
    if not building.stop_working(heroes, 0):
        return False

    return True


def _post_upgrade_for_market(building, resource, heroes, technology, now):
    """市场结束升级的后续影响
    1 派驻英雄
    2 开始产钱
    3 影响金钱库存上限
    """
    capacity_delta = (
            building_module.calc_money_capacity(building.basic_id, building.level, technology) -
            building_module.calc_money_capacity(building.basic_id, building.level-1, technology))

    output = resource_module.calc_money_output(building, heroes, technology)
    output_delta = output - building.value

    resource.update_money_capacity(resource.money_capacity + capacity_delta)
    resource.update_money_output(resource.money_output + output_delta)

    #参与升级的英雄直接入驻，进行生产工作
    for hero in heroes:
        if hero is not None and not hero.assign_working_in_building(building.id, now):
            return False

    if not building.start_working(heroes, output, False):
        return False

    return True


def _post_cancel_for_market(building, resource, heroes, technology, now):
    """市场取消升级、取消建造的后续处理
    """
    if building.level == 0:
        #取消建造，建筑物会被删除
        #不再派驻英雄
        return True
    else:
        #取消升级，不再影响金钱库存上限
        #影响金钱产量
        output = resource_module.calc_money_output(building, heroes, technology)
        output_delta = output - building.value

        resource.update_money_output(resource.money_output + output_delta)

        #参与升级的英雄直接入驻，进行生产工作
        for hero in heroes:
            if hero is not None and not hero.assign_working_in_building(building.id, now):
                return False

        if not building.start_working(heroes, output, False):
            return False

        return True


def _post_upgrade_for_defense(data, building, technology, defense = None, new_defense = []):
    """城防建筑结束升级的后续处理
    1 更新城防信息
    """
    if building.level == 1:
        #新创建
        assert defense == None
        defense = DefenseInfo.create(building)
        new_defense.append(defense)

        #若guard信息在城防之前已经创建，改guard的defense_id
        guard_list = data.guard_list.get_all()
        for guard in guard_list:
            guard.defense_id = defense.building_id

    defense.update_defense_value(defense_module.calc_defense_value(defense, technology)) #变更城防值

    return defense.update(building)


def _post_upgrade_for_barrack(building, resource, technology, conscript = None, new_conscript = []):
    """兵营升级完成的后续影响
    1 影响兵力容量上限
    """
    new_barrack = False

    if building.level == 1:
        #新创建
        assert conscript == None
        conscript = ConscriptInfo.create(building)
        new_conscript.append(conscript)
        new_barrack = True

    capacity_delta = (
            building_module.calc_soldier_capacity(building.basic_id, building.level, technology) -
            building_module.calc_soldier_capacity(building.basic_id, building.level-1, technology))

    conscript.update_soldier_capacity(conscript.soldier_capacity + capacity_delta)

    #新创建后，兵营是全满兵的状态
    if new_barrack:
        conscript.reclaim_soldier(conscript.soldier_capacity)

    return True


def _post_upgrade_for_mansion(data, building, resource, technology, now):
    """官邸结束升级的后续影响
    1 影响金钱库存上限
    2 影响粮草库存上限
    3 可能解锁 PVP
    4 影响领地上限
    """
    money_capacity_delta = (
            building_module.calc_money_capacity(building.basic_id, building.level, technology) -
            building_module.calc_money_capacity(building.basic_id, building.level-1, technology))
    resource.update_money_capacity(resource.money_capacity + money_capacity_delta)

    food_capacity_delta = (
            building_module.calc_food_capacity(building.basic_id, building.level, technology) -
            building_module.calc_food_capacity(building.basic_id, building.level-1, technology))
    resource.update_food_capacity(resource.food_capacity + food_capacity_delta)

    if not user_business.check_pvp_authority(data):
        return False

    if not user_business.check_arena_authority(data, now):
        return False
    
    #领地占有数量的变更
    map = data.map.get()
    occupy_num = int(data_loader.OccupyNodeNumByMansion_dict[building.level].occupyNodeNum)
    map.update_occupy_node_num_mansion(occupy_num)

    return True


def _post_upgrade_for_general_house(data, building, new_soldier_technology):
    """将军府结束升级的后续处理
    1 可能会解锁兵种科技
    如果解锁的兵种科技是完成状态，会解锁或升级兵种
    如果解锁的兵种科技是未完成状态，可以被研究
    2 增加战斗中可上阵的队伍数量，同时可能会更新 top 阵容
    """
    finish_techs = building_module.calc_unlock_finish_soldier_technology(
            building.basic_id, building.level)

    for basic_id in finish_techs:
        new_technology = TechnologyInfo.create_soldier_technology(building.user_id, basic_id)
        new_soldier_technology.append(new_technology)
        #TODO 解锁的科技都必须没有前置科技

    user = data.user.get()
    team_count = battle_module.calc_fight_team_count(building)
    if user.update_team_count(team_count):
        #如果可以上阵的队伍数量发生变化
        all_team = data.team_list.get_all(True)
        all_hero = data.hero_list.get_all(True)
        guard_list = data.guard_list.get_all()
        for guard in guard_list:
            #更新防守阵容
            if not guard.update_team(all_team, user.team_count):
                return False
            #更新 top 阵容
            if not guard.try_update_top_score(all_hero, user.team_count):
                return False

    return True


def _post_upgrade_for_moneyhouse(building, resource, heroes, technology, now):
    """钱库升级的后续影响
      影响金钱库存的上限
    """
    capacity_delta = (
            building_module.calc_money_capacity(building.basic_id, building.level, technology) -
            building_module.calc_money_capacity(building.basic_id, building.level-1, technology))

    resource.update_money_capacity(resource.money_capacity + capacity_delta)

    return True


def _post_upgrade_for_foodhouse(building, resource, heroes, technology, now):
    """粮仓升级的后续影响
      影响粮食库存的上限
    """
    capacity_delta = (
            building_module.calc_food_capacity(building.basic_id, building.level, technology) -
            building_module.calc_food_capacity(building.basic_id, building.level-1, technology))

    resource.update_food_capacity(resource.food_capacity + capacity_delta)

    return True


def _post_upgrade_for_watchtower(data, building):
    """瞭望塔升级的后续影响
       影响领地上限
    """
    map = data.map.get()
    occupy_num = int(data_loader.OccupyNodeNumByWatchTower_dict[building.level].occupyNodeNum)
    map.update_occupy_node_num_watchtower(occupy_num)

    return True


def set_garrison(building, heroes, resource, technologys, now):
    """
    添加建筑物的驻守英雄
    1 不结算英雄经验
    2 影响建筑物的能力
    """
    if building.is_farmland():
        return _set_garrison_for_farmland(
                building, heroes, resource, technologys, now)
    elif building.is_market():
        return _set_garrison_for_market(
                building, heroes, resource, technologys, now)

    logger.warning("Invalid building for garrison[building basic id=%d]" %
            building.basic_id)
    return False


def _set_garrison_for_farmland(building, heroes, resource, technologys, now):
    """
    向农田派驻英雄
    影响粮食产量
    """
    output = resource_module.calc_food_output(building, heroes, technologys)
    output_delta = output - building.value

    resource.update_food_output(resource.food_output + output_delta)

    #派驻英雄
    for hero in heroes:
        if hero is not None and not hero.assign_working_in_building(building.id, now):
            return False
    #农田并不一定要有英雄驻守，英雄有可能未空
    if not building.start_working(heroes, output, False):
        return False

    return True


def _set_garrison_for_market(building, heroes, resource, technologys, now):
    """
    向市场派驻英雄
    影响金钱产量
    """
    output = resource_module.calc_money_output(building, heroes, technologys)
    output_delta = output - building.value

    resource.update_money_output(resource.money_output + output_delta)

    #派驻英雄
    for hero in heroes:
        if hero is not None and not hero.assign_working_in_building(building.id, now):
            return False
    #市场并不一定要有英雄驻守，英雄有可能未空
    if not building.start_working(heroes, output, False):
        return False

    return True


def remove_garrison(building, hero, resource, now):
    """
    将 hero 从其驻守的建筑物中移除
    1 并不会结算经验
    2 会影响建筑物的能力
    """
    if building.is_farmland():
        return _remove_garrison_for_farmland(building, hero, resource, now)
    elif building.is_market():
        return _remove_garrison_for_market(building, hero, resource, now)

    logger.warning("Invalid building for garrison[building basic id=%d]" %
            building.basic_id)
    return False


def _remove_garrison_for_farmland(building, hero, resource, now):
    """
    移除农田中指定的驻守英雄
    影响粮食产量
    """
    output_base = resource_module.calc_output_base(building.basic_id, building.level)
    output_delta = resource_module.calc_food_output_addition_of_hero(
            output_base, building.level, hero.interior_score)

    resource.update_food_output(resource.food_output - output_delta)

    #移除英雄
    if not hero.finish_working():
        return False
    if not building.update_working_by_remove_hero([hero], building.value - output_delta):
        return False

    return True


def _remove_garrison_for_market(building, hero, resource, now):
    """
    移除市场中指定的驻守英雄
    影响金钱产量
    """
    output_base = resource_module.calc_output_base(building.basic_id, building.level)
    output_delta = resource_module.calc_money_output_addition_of_hero(
            output_base, building.level, hero.interior_score)

    resource.update_money_output(resource.money_output - output_delta)

    #移除英雄
    if not hero.finish_working():
        return False
    if not building.update_working_by_remove_hero([hero], building.value - output_delta):
        return False
    return True


def calc_garrison_exp(data, building, heroes, now):
    """
    计算英雄驻守在建筑物中所获得的经验
    """
    assert not building.is_upgrade
    user = data.user.get(True)

    #非可驻守建筑
    if not building.is_able_to_garrison():
        logger.warning("Building is not able to garrison")
        return False

    if not building.is_hero_in_building(heroes):
        return False

    #英雄经验
    exp_per_hour = data_loader.MonarchLevelBasicInfo_dict[user.level].garrisonExpPerHour
    for hero in heroes:
        if hero is None:
            continue

        if not hero_business.level_upgrade_by_working(
                data, hero, exp_per_hour, now, now):
            logger.warning("Hero upgrade failed[hero basic id=%d]" % hero.basic_id)
            return False

    return True

def get_buildings_by_basic_id(data, basic_id, readonly=False):
    """通过建筑id获取建筑"""
    buildings = []
    building_list = data.building_list.get_all(readonly)
    for building in building_list:
        if building.basic_id == basic_id:
            buildings.append(building)
    return buildings

def get_mansion_level(data):
    """获取官府等级"""
    building_basic_id = int(float(data_loader.OtherBasicInfo_dict['building_mansion'].value))
    mansion = get_buildings_by_basic_id(data, building_basic_id, True)[0]
    return mansion.level

def is_unlock_citydefence(data):
    """是否解锁城防"""
    citydefence_basic_id = int(float(data_loader.OtherBasicInfo_dict['building_citydefence'].value))
    key = "%d_%d" % (citydefence_basic_id, 1)
    mansion_level = get_mansion_level(data)
    return mansion_level >= data_loader.BuildingLevelBasicInfo_dict[key].limitMansionLevel


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))
    
    return open_flags


