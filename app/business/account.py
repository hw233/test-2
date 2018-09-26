#coding:utf8
"""
Created on 2016-07-05
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 帐号相关业务逻辑
"""

import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.resource import ResourceInfo
from app.data.user import UserInfo
from app.data.node import NodeInfo
from app.data.guard import GuardInfo
from app.core.name import NameGenerator
from app.business import conscript as conscript_business
from app.business import building as building_business
from app.business import mission as mission_business
from app.business import anneal as anneal_business
from app.business import plunder as plunder_business


def update_across_day_info(data, now, force = False):
    """更新所有离线数据
    """
    #判断是否是隔天登录
    user = data.user.get()
    is_same_day = utils.is_same_day(now, user.last_login_time)
    logger.debug("Is same day:%r" % is_same_day)

    if not force and is_same_day:
        return True

    days_diff = utils.count_days_diff(user.last_login_time, now)

    #更新用户登录信息
    user.login(now)
    trainer = data.trainer.get()
    trainer.add_login_num(1)

    #更新资源
    resource = data.resource.get()
    resource.update_current_resource(now)
    if not is_same_day:
        resource.reset_daily_statistics(days_diff)

    #更新兵力
    for conscript_data in data.conscript_list:
        conscript = conscript_data.get()
        if not is_same_day:
            conscript.reset_daily_statistics()
        if not conscript_business.update_current_soldier(conscript, now):
            return False

    #更新英雄驻守经验
    for building_data in data.building_list:
        building = building_data.get(True)
        if (building.is_able_to_garrison() and
                not building.is_upgrade and
                building.has_working_hero()):
            heroes_id = building.get_working_hero()
            heroes = []
            for id in heroes_id:
                heroes.append(data.hero_list.get(id))

            if not building_business.calc_garrison_exp(data, building, heroes, now):
                return False

    #更新签到信息
    sign = data.sign.get()
    sign.try_reset(now)

    #更新地图信息
    if not is_same_day:
        map = data.map.get()
        map.reset_daily_statistics(now)

    #更新抽奖信息
    if not is_same_day:
        draw = data.draw.get()
        draw.try_reset_draw(now)
        draw.reset_daily_statistics()

    #更新充值信息（月卡）
    pay = data.pay.get()
    pay.refresh_card(now)

    #更新一些统计信息
    trainer = data.trainer.get()
    if not is_same_day:
        trainer.reset_daily_statistics()

    #重置日常任务
    if not is_same_day:
        pattern = 1
        if data_loader.OtherBasicInfo_dict.has_key("init_id"):
            pattern = int(float(data_loader.OtherBasicInfo_dict['init_id'].value))
        mission_business.reset_daily_missions(data, pattern)

    #更新任务状态
    mission_business.update_all_missions(data, now)

    #更新政令
    if not is_same_day:
        energy = data.energy.get()
        energy.reset_daily_use_energy()

    #更新史实城信息
    if not is_same_day:
        for legendcity in data.legendcity_list.get_all():
            legendcity.reset_attack_count_daily_auto()

    #更新试炼场信息
    if not is_same_day:
        anneal = data.anneal.get()
        anneal.try_forward_floor()
        anneal_business.refresh_attack_num(anneal, now)

    #更新换位演武场
    if not is_same_day:
        transfer = data.transfer.get()
        transfer.reset()

    if not is_same_day:
        plunder = data.plunder.get()
        plunder.reset()
        plunder_business.decay_all_plunder_enemy_daily(data)

    return True


def update_user_basic_info(user, message):
    """修改用户基础数据"""
    if message.HasField('level'):
        user.level = message.level
    if message.HasField('exp'):
        user.exp = message.exp
    if message.HasField('vip_level'):
        user.vip_level = message.vip_level
    if message.HasField('vip_points'):
        user.vip_points = message.vip_points
    if message.HasField('name'):
        user.name = message.name
    if message.HasField('create_time'):
        user.create_time = message.create_time
    if message.HasField('last_login_time'):
        user.last_login_time = message.last_login_time
    if message.HasField('team_count'):
        user.team_count = message.team_count
    
    return True


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))
    
    return open_flags
