#coding:utf8
"""
Created on 2015-01-26
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 建筑物相关数值计算
"""

import time
import math
from utils import logger
from utils import utils
from utils.ret import Ret
from datalib.data_loader import data_loader
from app.core import resource as resource_module
from app.business import hero as hero_business
from app import log_formater


def start_conscript(conscript, building, heroes, conscript_num, resource, technologys, now):
    """开始征兵
    Args:
        building : 征兵的建筑
        resource : 玩家资源
        heros : 负责征兵的英雄
        conscript_num : 征兵数目
    """
    #消耗金钱
    need_money = _calc_consume_money(conscript_num)
    if not resource.cost_money(need_money):
        return False

    #消耗时间
    need_time = _calc_consume_time(
            conscript_num, building, heroes, technologys)

    #指派参与征兵的英雄, 更新建筑和英雄的信息
    for hero in heroes:
        if hero is not None and not hero.assign_working_in_building(building.id, now):
            return False
    if not building.start_working(heroes, conscript_num):
        return False

    return conscript.start_conscript(conscript_num, need_money, need_time, now)


def add_conscript(conscript, resource, conscript_num, now):
    """补充征兵
    当前正在征兵中，但是征兵数量+当前士兵数 < 兵容上限，可以补充征兵
    """
    if not update_current_soldier(conscript, now):
        return False

    #按照当初开始征兵的情况进行补充征兵：即不考虑英雄升级、科技升级
    need_money = conscript.calc_money_supplement_of_add(conscript_num)
    if not resource.cost_money(need_money):
        return False

    need_time = conscript.calc_time_supplement_of_add(conscript_num)

    return conscript.add_conscript(conscript_num, need_money, need_time)


def end_conscript(data, conscript, building, resource, user, heroes, now, force = False, ret = Ret()):
    """结束征兵
    Args:
        building : [BuildingInfo] 征兵的兵营
        resource : [ResourceInfo]
        heros : [HeroInfo] list
        force : [bool] 是否是立即完成，立即完成需要花费元宝
    """
    if not building.is_heroes_working(heroes):
        logger.warning("heroes not working[building.hero_ids=%s]" % building.hero_ids)
        ret.setup("NOT_CONSCRIPTING")
        return False

    gap = conscript.calc_time_gap_to_finish(now)
    original_gold = resource.gold
    need_gold = 0
    if force:
        #花费元宝，立即完成征兵
        need_gold = resource.gold_exchange_time(gap)
        if need_gold < 0:
            return False
    elif gap > 0:
        logger.warning("Invalid conscript end time[now=%d][end time=%d]" %
                (now, conscript.end_time))
        ret.setup("CANNT_END")
        return False

    if force:
        end_time = conscript.end_time
    else:
        end_time = now

    if not update_current_soldier(conscript, end_time):
        return False

    #更新英雄经验
    if not _calc_conscript_exp(data, conscript, heroes, user, now):
        return False

    #移除驻守英雄
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False
    if not building.stop_working(heroes, now):
        return False

    if force:
        log = log_formater.output_gold(data, -need_gold,  log_formater.FINISH_CONSCRIPT,
                "Finish conscript by gold", before_gold = original_gold, reduce_time = gap)
        logger.notice(log)

    return conscript.finish_conscript()


def cancel_conscript(data, conscript, building, resource, user, heroes, now):
    """取消征兵、结束征兵。
    Args:
        building : [BuildingInfo] 征兵的兵营
        resource : [ResourceInfo]
        heros : [HeroInfo] list
    """
    if not update_current_soldier(conscript, now):
        return False

    #返回部分资源
    remittal_money = conscript.calc_money_remittal_of_cancel()
    resource.gain_money(remittal_money)

    #结算经验
    if not _calc_conscript_exp(data, conscript, heroes, user, now):
        return False

    #移除驻守英雄
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False
    if not building.stop_working(heroes, now):
        return False

    return conscript.finish_conscript()


def _calc_consume_money(conscript_num):
    """
    计算征兵消耗的金钱
    """
    need_money = int(conscript_num *
            float(data_loader.OtherBasicInfo_dict['SoldierMoneyCost'].value))

    return need_money


def _calc_consume_time(conscript_num, building, heroes, technologys):
    """
    计算征兵花费的时间
    Return:
        need_time : seconds
    """
    speed_hour = resource_module.calc_soldier_output(building, heroes, technologys)
    need_time = utils.ceil_to_int(conscript_num * 3600.0 / speed_hour)

    return need_time


def update_current_soldier(conscript, end_time):
    """
    根据当前更新士兵数
    """
    add_num = conscript.update_current_soldier(end_time)
    if add_num < 0:
        logger.warning("Update current soldier failed")
        return False
    return True


def _calc_conscript_exp(data, conscript, heroes, user, now):
    """
    结算英雄征兵经验
    """
    end_time = min(conscript.end_time, now)
    exp_per_hour = data_loader.MonarchLevelBasicInfo_dict[user.level].conscriptExpPerHour
    for hero in heroes:
        if hero is None:
            continue

        if not hero_business.level_upgrade_by_working(
                data, hero, exp_per_hour, end_time, now):
            logger.warning("Hero upgrade failed[hero basic id=%d]" % hero.basic_id)
            return False

    return True

