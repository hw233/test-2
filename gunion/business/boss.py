#coding:utf8
"""
Created on 2017-03-01
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟boss
"""

from gunion.data.boss import UnionBossInfo
from proto import union_pb2
from proto import internal_union_pb2
from datalib.data_loader import data_loader
from utils import logger
from utils import utils
import random

def get_union_boss(data, boss_id, readonly = False):
    """获取联盟boss"""
    id = UnionBossInfo.generate_id(data.id, boss_id)
    return data.union_boss_list.get(id, readonly)

def attack_boss(data, boss, kill_soldier_num, user_id, user_name):
    """攻击boss"""
    boss.attack(kill_soldier_num, user_id, user_name)
    if boss.status == UnionBossInfo.KILLED:
        union = data.union.get()
        union.boss_step += 1
        bosses_id = union.get_bosses_id()
        now_boss_id = union.get_attacking_unionboss()
        if now_boss_id != 0:
            now_boss = get_union_boss(data, now_boss_id)
            now_boss.set_activity()

def is_able_to_accept_boss_reward(data, member, boss):
    """是否可以领取相应的boss宝箱"""
    if member.user_id in boss.get_accepted_members():
        logger.warning("member has received boss reward[union_id=%d][boss_id=%d][user_id=%d]" % (
                data.id, boss.boss_id, member.user_id))
        return False
    
    if boss.status != boss.KILLED:
        logger.warning("boss not be killed[union_id=%d][boss_id=%d]" % (
                data.id, boss.boss_id))
        return False

    return True

def accept_boss_reward(data, user_id, user_name, icon_id, boss, now):
    """领取boss奖励宝箱"""
    union = data.union.get()
    index = union.get_bosses_id().index(boss.boss_id)
    if 0 <= index <= 2:
        pool = data_loader.UnionBossBoxPoolOne_dict
    if 3 <= index <= 6:
        pool = data_loader.UnionBossBoxPoolTwo_dict
    if 7 <= index <= 9:
        pool = data_loader.UnionBossBoxPoolThree_dict

    weight_sum = 0
    for key in pool:
        weight_sum += pool[key].weight

    rand = random.uniform(0, weight_sum)
    per_weight = 0
    choose = None
    for key in pool:
        if per_weight <= rand <= pool[key].weight + per_weight:
            choose = key
            break
        per_weight += pool[key].weight

    item_id = pool[choose].itemBasicId
    item_num = pool[choose].itemNum

    boss.add_reward_record(user_id, user_name, icon_id, item_id, item_num, now)
    
'''
def update_unioboss_from_basic_data(data, basic_data, now):
    """更新unionboss
        @return: True已更新, False未更新
    """
    union = data.union.get()
    all_groups = basic_data.unionbossgroup_list.get_all(True)
    group = basic_data.unionbossgroup_list.get(union.boss_group)

    if not (union.boss_group == 0 or group.is_overdue(now)):
        return False

    new_group = None
    for g in all_groups:
        if not g.is_overdue(now):
            new_group = g
            break
    
    union.update_boss_group(new_group, now)

    for boss_id in union.get_bosses_id():
        new_boss = UnionBossInfo.create(data.id, boss_id)
        new_boss.status = UnionBossInfo.INACTIVE
        new_boss.total_soldier_num = data_loader.UnionBossBasicInfo_dict[boss_id].totalSoldierNum
        new_boss.current_soldier_num = new_boss.total_soldier_num
        old_boss = data.union_boss_list.get(new_boss.id)
        if old_boss is None:
            data.union_boss_list.add(new_boss)
        else:
            old_boss.reset()

    boss_id = union.get_attacking_unionboss()
    if boss_id != 0:
        first_boss = get_union_boss(data, boss_id)
        first_boss.set_activity()
    return True
'''

def _is_boss_group_overdue(group_id, last_change_time, now):
    """boss阵容是否过期"""
    if group_id not in data_loader.UnionBossGroupBasicInfo_dict:
        return True
    duration = data_loader.UnionBossGroupBasicInfo_dict[group_id].duration
    if utils.count_days_diff(last_change_time, now) >= duration and duration != 0:
        return True
    else:
        return False


def try_change_unionboss(data, now):
    """尝试变换boss阵容"""
    union = data.union.get()
    group_id = union.boss_group
    if _is_boss_group_overdue(group_id, union.boss_last_change_time, now):
        if group_id not in data_loader.UnionBossGroupBasicInfo_dict:
            group_id = data_loader.UnionBossGroupBasicInfo_dict.keys()[0]
        else:
            group_id = data_loader.UnionBossGroupBasicInfo_dict[group_id].next

        bosses_id = data_loader.UnionBossGroupBasicInfo_dict[group_id].bosses_id
        union.update_boss_group(group_id, bosses_id, now)

        for boss_id in union.get_bosses_id():
            new_boss = UnionBossInfo.create(data.id, boss_id)
            new_boss.status = UnionBossInfo.INACTIVE
            new_boss.total_soldier_num = data_loader.UnionBossBasicInfo_dict[boss_id].totalSoldierNum
            new_boss.current_soldier_num = new_boss.total_soldier_num
            old_boss = data.union_boss_list.get(new_boss.id)
            if old_boss is None:
                data.union_boss_list.add(new_boss)
            else:
                old_boss.reset()

        boss_id = union.get_attacking_unionboss()
        if boss_id != 0:
            first_boss = get_union_boss(data, boss_id)
            first_boss.set_activity()
        return True
    
    return False


def try_reset_unionboss(data, now):
    """尝试重置联盟boss"""
    union = data.union.get()
    if utils.count_days_diff(union.boss_last_update_time, now) < 3:
        return False

    bosses = data.union_boss_list.get_all()
    for boss in bosses:
        boss.reset()
    
    union.reset_boss(now)

    boss_id = union.get_attacking_unionboss()
    if boss_id != 0:
        first_boss = get_union_boss(data, boss_id)
        first_boss.set_activity()
    
    return True
