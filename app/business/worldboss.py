#coding:utf8
"""
Created on 2016-11-05
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 世界boss相关逻辑
"""

import random
import time
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.basic_worldboss import BasicWorldBossInfo
from app.data.map import MapGraph
from app.data.node import NodeInfo
from app.data.hero import HeroInfo
from app.data.soldier import SoldierInfo
from app.data.worldboss import WorldBossInfo
from app.data.rival import RivalInfo
from app.core import reward as reward_module


def arise_worldboss_event(data, node, now, **kwargs):
    """出现世界boss事件
    1 己方附属点出现该事件
    """
    change_nodes = kwargs['change_nodes']
    
    parent_basic_id = MapGraph().get_parent(node.basic_id)
    parent_id = NodeInfo.generate_id(data.id, parent_basic_id)
    parent = data.node_list.get(parent_id, True)

    map = data.map.get()
    user = data.user.get(True)
    node.respawn_dependency_with_worldboss(map, parent, user, now)

    worldboss = data.worldboss.get()
    user = data.user.get(True)    
    if not worldboss.is_arised():
        return False
    
    worldboss.trigger_node(node.id)
    _update_worldboss_rival(data, worldboss)
    
    return node.arise_event(NodeInfo.EVENT_TYPE_WORLDBOSS, worldboss.arise_time)


def clear_worldboss_event(data, node, now, **kwargs):
    """worldboss事件消失
    """
    change_nodes = kwargs["change_nodes"]

    map = data.map.get()
    node.reset_dependency(map)
    change_nodes.append(node)

    worldboss = data.worldboss.get()
    worldboss.clear_node()
    return node.clear_event()


def start_worldboss_event(data, node, now):
    """启动世界boss事件
    并不真正启动，只是检查事件是否处于合法状态
    """
    #节点上必须有合法的副本随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_WORLDBOSS:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False
    
    #if node.is_event_over_idletime(now):
    #    logger.warning("Event over idletime[node basic id=%d]"
    #            "[event type=%d][arise time=%d]" %
    #            (node.basic_id, node.event_type, node.event_arise_time))
    #    return False
    
    return True


def finish_worldboss_event(data, node, now, change_nodes):
    """结束世界boss的战斗
    """
    #节点上必须有合法的野怪随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_WORLDBOSS:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    worldboss = data.worldboss.get()
    if worldboss.is_killed():
        #if not node.launch_event(now, overtime = True):
        #    return False


        #if not node.finish_event(now, overtime = True):
        #    return False

        node.clear_event()
        
        #节点变为不活跃
        map = data.map.get()
        node.reset_dependency(map)
        
        change_nodes.append(node)

    return True



def init_worldboss(basic_data, data, now):
    """
    """
    worldboss = WorldBossInfo.create(data.id, now)
    user = data.user.get(True)
    limit_level = int(float(data_loader.OtherBasicInfo_dict["unlock_worldboss_level"].value))
    if limit_level <= user.level:
        worldboss.unlock()
        #update_worldboss(basic_data, worldboss, user.level, now)

    return worldboss


def update_worldboss(data, basic_data, worldboss, user_level, now):
    """更新世界boss
    """
    if not worldboss.is_unlock():
        return True

    if worldboss.is_arised():
        #如果查不到世界boss的基础信息，表示已删除，直接结束
        basic_boss = None
        for boss_basic in basic_data.worldboss_list.get_all():
            if boss_basic.boss_id == worldboss.boss_id and \
                    boss_basic.get_arise_time() == worldboss.arise_time:
                basic_boss = boss_basic
                break

        if basic_boss is None:
            logger.debug("basic worldboss info not exist[boss_id=%d]" % worldboss.boss_id)
            worldboss.clear()
        if worldboss.is_overdue(now):
            logger.debug("worldboss is overdue[boss_id=%d]" % worldboss.boss_id)
            #若已有过期世界boss事件，则先清除
            worldboss.clear()
        else:
            #当天已有世界boss
            #更新一下时间、描述、boss血量等，有可能会临时修改
            start_time = utils.get_spec_second(now, basic_boss.start_time)
            end_time = utils.get_spec_second(now, basic_boss.end_time)
            total_soldier_num = basic_boss.total_soldier_num
            description = basic_boss.description
            worldboss.update_basic_info(start_time, end_time, total_soldier_num, description)

            node_basic_id = worldboss.get_node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id)
            if node is None:
                node = NodeInfo.create(data.id, node_basic_id)
                data.node_list.add(node)
            
            node.set_world_boss()
            _update_worldboss_rival(data, worldboss, node_id)

            return True

    basic_worldboss_list = basic_data.worldboss_list.get_all()
    for basic_worldboss in basic_worldboss_list:
        start_second = utils.get_start_second_by_timestring(basic_worldboss.date)
        is_same_day = utils.is_same_day(now, start_second)
        if is_same_day:
            boss_id = basic_worldboss.boss_id
            start_time = utils.get_spec_second(now, basic_worldboss.start_time)
            end_time = utils.get_spec_second(now, basic_worldboss.end_time)
            total_soldier_num = basic_worldboss.total_soldier_num
            description = basic_worldboss.description

            node_basic_id = worldboss.get_node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id)
            if node is None:
                node = NodeInfo.create(data.id, node_basic_id)
                data.node_list.add(node)
            
            node.set_world_boss()
            _update_worldboss_rival(data, worldboss, node_id)

            if not worldboss.arise(now, boss_id, start_time, end_time, total_soldier_num,
                    description, user_level):
                logger.warning("arise worldboss failed")
                return True
            logger.debug("Arise worldboss[boss_id=%d][arise_time=%d]" % (worldboss.boss_id, worldboss.arise_time))
            
            break

    return True


def generate_array_detail(worldboss, user):
    """生成阵容详情返回
    """
    teams = []
    for array_id in worldboss.get_arrays_id():
        array = data_loader.WorldBossArrayBasicInfo_dict[array_id]
        #buff和tech是针对整个阵容生效的
        buffs_id = array.buffIds
        techs_id = array.techIds

        heroes = []
        for i in range(len(array.heroIds)):
            basic_id = array.heroIds[i]
            star = array.heroStars[i]
            equipments_id = []
            equipments_id.append(array.heroEquipmentIds[i * 3])
            equipments_id.append(array.heroEquipmentIds[i * 3 + 1])
            equipments_id.append(array.heroEquipmentIds[i * 3 + 2])
            evolution_level = array.heroEvolutionLevels[i]
            soldier_basic_id = array.soldierBasicIds[i]
            soldier_level = array.soldierLevels[i]
            soldier = SoldierInfo.create(user.id, soldier_basic_id, soldier_level)

            hero = HeroInfo.create_special(user.id, user.level, basic_id, 
                    user.level, star, soldier, [], techs_id, equipments_id, 
                    buffs_id, False, evolution_level, False)
            heroes.append(hero)

        teams.append(heroes)

    return teams


def start_battle(data, worldboss, choose_array_index, now):
    """开始世界boss战斗
    """
    if worldboss.is_killed():
        return WorldBossInfo.BOSS_KILLED

    if not worldboss.is_in_battle_time(now):
        return WorldBossInfo.BOSS_EXPIRED

    if not worldboss.start_battle(choose_array_index, now):
        logger.warning("worldboss start battle failed")
        return -1

    return WorldBossInfo.BOSS_OK


def finish_battle(data, worldboss, result, kill_soldier_num, now):
    """结束世界boss战斗
    """
    
    if worldboss.is_killed():
        ret = WorldBossInfo.BOSS_KILLED
    elif not worldboss.is_in_battle_time(now, True) and worldboss.is_attack_overtime(now):
        ret = WorldBossInfo.BOSS_OVERTIME
    else:
        ret = WorldBossInfo.BOSS_OK

    worldboss.finish_battle(result, kill_soldier_num, now)
    node_basic_id = worldboss.get_node_basic_id()
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    _update_worldboss_rival(data, worldboss, node_id)
    return ret


def _update_worldboss_rival(data, worldboss, node_id=None):
    user = data.user.get(True)
    rival_id = node_id if node_id is not None else worldboss.node_id
    rival = data.rival_list.get(rival_id)
    if rival is None:
        rival = RivalInfo.create(rival_id, data.id)
        data.rival_list.add(rival)

    #enemy的level
    spoils = reward_module.random_pve_spoils(user.level)
    rival.set_worldboss(user.level, spoils)
    logger.debug("update worldboss rival[rival_id=%d]" % rival_id)

    return True



def add_basic_worldboss(basic_data, basic_id, worldbosses):
    """添加世界boss的基础信息
       worldboss:
         (id, date, start_time, end_battle_time, description, 
             total_soldier_num, list(arrays_id)) 七元组
    """
    for add_worldboss in worldbosses:
        id = add_worldboss[0]
        boss_id = add_worldboss[1]
        date = add_worldboss[2]
        start_time = add_worldboss[3]
        end_time = add_worldboss[4]
        description = add_worldboss[5]
        total_soldier_num = add_worldboss[6]
        
        worldboss = basic_data.worldboss_list.get(id)
        if worldboss is None:
            worldboss = BasicWorldBossInfo.create(id, basic_id)
            basic_data.worldboss_list.add(worldboss)
        worldboss.update(boss_id, date, start_time, end_time, description,
                total_soldier_num)   

    return True


def delete_basic_worldboss(basic_data, id_list):
    """删除世界boss的基础信息
    """
    id_list = list(set(id_list))
    for id in id_list:
        worldboss = basic_data.worldboss_list.get(id)
        if worldboss is not None:
            basic_data.worldboss_list.delete(id)
    
    return True


def eliminate_invalid_basic_worldboss(basic_data, now):
    """删除过期的世界boss基础数据
    """
    basic_worldbosses = basic_data.worldboss_list.get_all()

    delete_worldbosses_id = []
    for basic_boss in basic_worldbosses:
        if basic_boss.is_invalid(now):
            delete_worldbosses_id.append(basic_boss.id)

    logger.notice("eliminate invalide basic worldbosses[ids=%s]" % utils.join_to_string(delete_worldbosses_id))

    delete_basic_worldboss(basic_data, delete_worldbosses_id)



