#coding:utf8
"""
Created on 2016-11-05
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 世界boss
"""

import random
import base64
from utils import logger
from datalib.data_loader import data_loader
from common.data.worldboss import CommonWorldBossInfo
from common.business import broadcast as broadcast_business


def init_worldboss(data, now):
    worldboss = CommonWorldBossInfo.create(data.id)
    data.worldboss.add(worldboss)
    return True


def update_worldboss(data, now, arise_time = 0, start_time = 0, end_time = 0,
        boss_id = 0, kills_addition = 0, total_soldier_num = 0, 
        user_id = 0, user_name = ''):
    """更新世界boss数据
    """
    worldboss = data.worldboss.get()
    if (arise_time != 0 and arise_time != worldboss.get_arise_time()) \
            and (start_time != 0 and start_time != worldboss.start_time) \
            and (end_time != 0 and end_time != worldboss.end_time):
        #boss时间有变，证明更新boss了
        worldboss.reset(arise_time, start_time, end_time, total_soldier_num, boss_id)
    
    if kills_addition > 0:
        worldboss.update_current_soldier_num(kills_addition)
        add_broadcast_of_decline(data, worldboss, now)

    boss_killed_now = False
    if worldboss.is_dead() and worldboss.kill_user_name == '':
        worldboss.update_kill_user(user_id, user_name, now)
        if worldboss.kill_user_name != '':
            boss_killed_now  = True

    if boss_killed_now:
        add_broadcast_of_kill(data, worldboss, now)

    return True


def add_broadcast_of_decline(data, worldboss, now):
    """
    """
    broadcast_id = 70001
    declines = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    ratio = 1.0 * worldboss.current_soldier_num / worldboss.total_soldier_num

    for i in range(len(declines)):
        decline = declines[i]
        if ratio < decline and worldboss.update_broadcast_status(i):
            mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
            life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
            template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
            priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority
            content = template.replace("#str#", str(int(decline * 100)), 1)
            broadcast_business.add_broadcast(data, now, mode_id, priority, life_time, content)

    return True


def add_broadcast_of_kill(data, worldboss, now):
    """
    """
    broadcast_id = 70002
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority
    content = template.replace("#str#", base64.b64decode(worldboss.kill_user_name), 1)
    
    broadcast_business.add_broadcast(data, now, mode_id, priority, life_time, content)
    return True



