#coding:utf8
"""
Created on 2015-12-24
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 副本随机事件逻辑
"""

from utils import logger
from datalib.data_loader import data_loader
from app.data.map import MapGraph
from app.data.node import NodeInfo
from app.business import map as map_business


def arise_dungeon_event(data, node, now, **kwargs):
    """出现副本事件
    1 关键节点从我方占据，变为敌人占据
    2 敌人类型为副本
    """
    change_nodes = kwargs['change_nodes']
    new_items = kwargs['new_items']
    new_mails = kwargs['new_mails']

    dungeon = data.dungeon.get()
    guard = data.guard_list.get(data.id) #副本必须在 PVP 之后开启
    user = data.user.get(True)
    
    if not dungeon.open(node, user.team_count, guard.score, now):
        return False

    if not map_business.respawn_enemy_key_node(data, node, now, is_dungeon=True):
        return False
     
    return node.arise_event(NodeInfo.EVENT_TYPE_DUNGEON, now)


def clear_dungeon_event(data, node, now, **kwargs):
    """副本事件消失
    1 生成一个新的普通敌人占据节点（非副本）
    """
    change_nodes = kwargs["change_nodes"]

    map = data.map.get()
    user = data.user.get(True)

    if not node.clear_event():
        return False

    if not map_business.close_dungeon_key_node(data, node, change_nodes, now):
        return False

    dungeon = data.dungeon.get()
    dungeon.close()
    return True


def start_dungeon_event(data, node, now):
    """启动副本事件: 攻击
    并不真正启动，只是检查事件是否处于合法状态
    """
    #节点上必须有合法的副本随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_DUNGEON:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if node.is_event_over_idletime(now):
        logger.warning("Event over idletime[node basic id=%d][event type=%d][arise time=%d]" %
                (node.basic_id, node.event_type, node.event_arise_time))
        return False
    return True


def finish_dungeon_event_succeed(data, node, now, change_nodes):
    """结束副本事件: 攻击成功
    不是最后一个关卡，开启下一个关卡
    是最后一个关卡，完成事件，占领节点
    """
    logger.debug("Finish dungeon event")

    #节点上必须有合法的副本随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_DUNGEON:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    rival_id = node.id
    rival = data.rival_list.get(rival_id, True)
    dungeon = data.dungeon.get()
    user = data.user.get(True)
    if not dungeon.forward(node, user.team_count, now):
        logger.warning("Forward dungeon failed")
        return False

    change_nodes.append(node)

    #如果副本通关
    if dungeon.finish:
        if not node.launch_event(now, overtime = True):
            return False

        #获得成就值
        user = data.user.get(True)
        resource = data.resource.get()
        resource.update_current_resource(now)
        ac_base = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementBase
        ac_coe = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementCoefficient
        achievement = ac_base + ac_coe * user.level
        resource.gain_achievement(achievement)

        #占领节点
        if not node.finish_event(now, overtime = True):
            return False

        dungeon = data.dungeon.get()
        dungeon.close()
        map = data.map.get() 
        if map.is_able_to_occupy_more():
            return map_business.dominate_key_node(data, node, change_nodes, now)
        else:
            return map_business.close_dungeon_key_node(data, node, change_nodes, now)
    else:
        #副本开启下一个关卡
        return map_business.forward_dungeon_key_node(data, node, now)


