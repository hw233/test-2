#coding:utf8
"""
Created on 2015-10-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 世界地图战斗事件逻辑
"""

import random
import math
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.map import MapGraph
from app.data.node import NodeInfo
from app.business import map as map_business


def trigger_custom_war_event(data, now,
        node_basic_id, exploit_type, exploit_level,
        rival_type, rival_score_min, rival_score_max, change_nodes):
    """触发指定的战争事件
    在指定的（我方占据）关键点发生战争事件，节点丢失
    指定新生成的敌人占据关键点的资源和敌人信息
    Args:
        node_basic_id[int]: 指定节点 basic id
        exploit_type[int]: 指定节点资源类型
        exploit_level[int]: 指定节点资源类型
        rival_type[int]: 指定节点敌人类型
        rival_score_min[int]: 指定节点敌人战力下限
        rival_score_max[int]: 指定节点敌人战力上限
    """
    logger.debug("Trigger custom war event")

    user = data.user.get(True)
    map = data.map.get()
    resource = data.resource.get()
    resource.update_current_resource(now)
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    node = data.node_list.get(node_id)
    change_nodes.append(node)

    if not map_business.clear_key_node(data, node):
        return False
    if not map_business.respawn_enemy_key_node_custom(
            data, node, now, exploit_type, exploit_level,
            rival_type, rival_score_min, rival_score_max):
        return False
    if not map_business._post_lost_key_node(
            data, map, node, now, now, change_nodes, [], []):
        return False

    map.update_next_war_time(now)
    return True


def trigger_war_event(data, now,
        change_nodes = [], new_items = [], new_mails = []):
    """触发战争事件
    """
    user = data.user.get(True)
    resource = data.resource.get()
    resource.update_current_resource(now)

    #判断是否可以触发战争事件
    map = data.map.get()
    if not map.is_able_to_trigger_war_event(now):
        logger.warning("Not able to trigger war event[next time=%d][now=%d]" %
                (map.next_war_time, now))
        return False

    logger.debug("Trigger war event")

    #计算哪些关键节点发生战争事件，丢失
    lost_nodes_id = calc_lost_key_nodes(data, map, user, now)

    if not update_for_lost_key_nodes(
            data, map, user, lost_nodes_id, new_items, new_mails, change_nodes, now):
        logger.warning("Update for lost key node failed")
        return False

    map.update_next_war_time(now)
    return True


def calc_lost_key_nodes(data, map, user, now):
    """
    计算丢失的关键节点
    己方占领的边界（与敌方占领的关键点相邻）关键点，有一定概率丢失
    Args:
        map[MapInfo]
        user[UserInfo]
        now[int]
    Returns:
        list(int): 丢失的关键节点 id 列表
    """
    own_nodes = {} #己方拥有的节点
    dangerous_nodes = []
    lost_nodes_id = [] #丢失的节点
    max_lost_num = 0 #单次最多丢失的节点个数

    all_nodes_num = 0
    for node in data.node_list.get_all(True):
        if node.is_key_node() and node.is_own_side():
            all_nodes_num = all_nodes_num + 1
            if map_business.is_key_node_dangerous(data, node):
                dangerous_nodes.append(node)
            else:
                own_nodes[node.basic_id] = node

    max_lost_num = utils.floor_to_int(all_nodes_num * 0.125)
    logger.debug("calc war max lost num[own_nodes_num=%d][lost_num=%d]" 
            % (all_nodes_num, max_lost_num))
    
    lost_num = 0
    while len(dangerous_nodes) > 0:
        node = dangerous_nodes.pop()

        #正在发生战争或处于保护中的节点，不会丢失
        if node.is_in_battle() or node.is_in_protect(now):
            continue

        #危险状态的节点，有概率发生战争事件，导致丢失
        if lost_num < max_lost_num and _is_node_arise_war_event(map, node, user, now):
            lost_nodes_id.append(node.id)
            lost_num = lost_num + 1

            #其邻接关键节点，变成危险状态
            for basic_id in MapGraph().get_neighbors(node.basic_id):
                if basic_id in own_nodes:
                    neighbor = own_nodes[basic_id]
                    dangerous_nodes.append(neighbor)
                    del own_nodes[basic_id]
        else:
            own_nodes[node.basic_id] = node

    logger.debug("lost node[list=%s]" % utils.join_to_string(lost_nodes_id))
    return lost_nodes_id


def _is_node_arise_war_event(map, node, user, now):
    """
    判断节点上是否发生战争事件
    Returns:
        True/False
    """
    #本方占领的关键点
    assert node.is_key_node() and node.is_own_side()

    #计算发生战争事件的概率

    #如果节点发生防御事件，不会发生战争
    if node.event_type == NodeInfo.EVENT_TYPE_DEFEND:
        logger.debug("war not arise[basic id=%d]" % node.basic_id)
        return False

    #1 和占领时间相关
    duration = now - node.hold_time
    hold_time_min = float(data_loader.MapConfInfo_dict["hold_time_min"].value)
    hold_time_max = float(data_loader.MapConfInfo_dict["hold_time_max"].value)
    if duration < hold_time_min:
        logger.debug("war not arise[basic id =%d][hold duration=%d]" % (
            node.basic_id, duration))
        return False
    elif duration >= hold_time_max:
        hold_ratio = 0.0
    else:
        radix = float(data_loader.MapConfInfo_dict["hold_ratio_of_time_radix"].value)
        power = float(data_loader.MapConfInfo_dict["hold_ratio_of_time_power"].value)
        hold_ratio = radix * math.pow(hold_time_max - duration, power)

    #2 和当前用户等级，以及当前拥有的资源点相关
    war_ratio_base = _calc_base_war_ratio(node, map, user)
    war_ratio = war_ratio_base - hold_ratio
    random.seed()
    if random.random() < war_ratio:
        logger.debug("war arise[basic id =%d]"
                "[hold ratio=%f][war ratio base=%f][war ratio=%f]" %
                (node.basic_id, hold_ratio, war_ratio_base, war_ratio))
        return True
    else:
        logger.debug("war not arise[basic id =%d]"
                "[hold ratio=%f][war ratio base=%f][war ratio=%f]" %
                (node.basic_id, hold_ratio, war_ratio_base, war_ratio))
        return False


def _calc_base_war_ratio(node, map, user):
    """计算节点发生战争事件的基础概率
    """
    #和目前拥有的资源点、用户等级相关
    lost_ratio_radix = float(data_loader.MapConfInfo_dict["lost_ratio_radix"].value)
    lost_ratio_power = float(data_loader.MapConfInfo_dict["lost_ratio_power"].value)
    lost_weight_of_user = data_loader.KeyNodeMatchBasicInfoOfMonarch_dict[
            user.level].lostWeight

    war_ratio_base = lost_ratio_radix * math.pow(
            map.own_key_lost_weight / lost_weight_of_user,
            lost_ratio_power)
    war_ratio_base = min(1.0, war_ratio_base)
    war_ratio_base = max(0.0, war_ratio_base)

    return war_ratio_base


def update_for_lost_key_nodes(data, map, user, lost_nodes_id,
        new_items, new_mails, change_nodes, now):
    """计算丢失的关键节点，更新相关信息
    """
    #丢失的时间 - 即发生战争的时间
    war_time = map.calc_war_time(now)
    logger.debug("War time[time=%d]" % war_time)

    for node_id in lost_nodes_id:
        node = data.node_list.get(node_id)

        #丢失节点
        if not map_business.lost_key_node(
                data, node, war_time, now, change_nodes, new_items, new_mails):
            logger.warning("Lost key node failed")
            return False

    return True

