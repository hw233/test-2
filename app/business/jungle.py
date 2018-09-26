#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 野怪随机事件逻辑
"""

from utils import logger
from datalib.data_loader import data_loader
from app.data.map import MapGraph
from app.data.node import NodeInfo


def arise_jungle_event(data, node, now, **kwargs):
    """出现野怪事件
    1 附属点变为活跃
    2 附属点出现 PVE 敌人
    """
    change_nodes = kwargs["change_nodes"]

    parent_basic_id = MapGraph().get_parent(node.basic_id)
    parent_id = NodeInfo.generate_id(data.id, parent_basic_id)
    parent = data.node_list.get(parent_id, True)

    map = data.map.get()
    user = data.user.get(True)
    node.respawn_dependency_with_enemy(map, parent, user, now)

    return node.arise_event(NodeInfo.EVENT_TYPE_JUNGLE, now)


def clear_jungle_event(data, node, now, **kwargs):
    """野怪事件消失
    附属点变为不活跃
    """
    change_nodes = kwargs["change_nodes"]

    #节点上必须有合法的野怪随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_JUNGLE:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    map = data.map.get()
    node.reset_dependency(map)
    change_nodes.append(node)

    return node.clear_event()


def start_jungle_event(data, node, now):
    """启动野怪事件: 攻击
    并不真正启动，只是检查事件是否处于合法状态
    """
    #节点上必须有合法的野怪随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_JUNGLE:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if node.is_event_over_idletime(now):
        logger.warning("Event over idletime[node basic id=%d][event type=%d][arise time=%d]" %
                (node.basic_id, node.event_type, node.event_arise_time))
        return False
    return True


def finish_jungle_event_succeed(data, node, now, change_nodes):
    """结束野怪事件: 成功，攻击野怪胜利
    """
    #节点上必须有合法的野怪随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_JUNGLE:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if not node.launch_event(now, overtime = True):
        return False

    #获得成就值
    rival_id = node.rival_id
    rival = data.rival_list.get(rival_id, True)
    resource = data.resource.get()
    resource.update_current_resource(now)
    ac_base = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementBase
    ac_coe = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementCoefficient
    achievement = ac_base + ac_coe * rival.level
    resource.gain_achievement(achievement)

    if not node.finish_event(now, overtime = True):
        return False

    #节点变为不活跃
    map = data.map.get()
    node.reset_dependency(map)

    change_nodes.append(node)
    return True


def finish_jungle_event_fail(data, node, now, change_nodes):
    """结束野怪事件: 失败
    """
    #如果附属点所在的key node已经丢失，则野怪事件结束，附属点也消失
    parent_basic_id = MapGraph().get_parent(node.basic_id)
    parent_id = NodeInfo.generate_id(data.id, parent_basic_id)
    parent = data.node_list.get(parent_id, True)
    if not parent.is_visible() or not parent.is_own_side():
        #节点上必须有合法的野怪随机事件
        if node.event_type != NodeInfo.EVENT_TYPE_JUNGLE:
            logger.warning("Wrong event[type=%d]" % node.event_type)
            return False
        
        if not node.launch_event(now, overtime = True):
            return False
        
        if not node.finish_event(now, overtime = True):
            return False
        
        #节点变为不活跃
        map = data.map.get()
        node.reset_dependency(map)
        
        change_nodes.append(node)

    return True


