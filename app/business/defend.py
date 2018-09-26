#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 防御随机事件逻辑
"""

from utils import logger
from datalib.data_loader import data_loader
from app.data.node import NodeInfo
from app.business import map as map_business


def arise_defend_event(data, node, now, **kwargs):
    """出现防御事件
    节点上出现敌人
    """
    change_nodes = kwargs["change_nodes"]

    if not node.arise_event(NodeInfo.EVENT_TYPE_DEFEND, now):
        return False

    #敌人入侵节点
    return map_business.enemy_invade_key_node(data, node, now)


def clear_defend_event(data, node, now, **kwargs):
    """清除防御事件
    节点变为敌方占据
    """
    change_nodes = kwargs['change_nodes']
    new_items = kwargs['new_items']
    new_mails = kwargs['new_mails']

    if not map_business.lost_key_node_of_invasion(
            data, node, now, change_nodes, new_items, new_mails):
        return False
    return node.clear_event()


def start_defend_event(data, node, now):
    """启动防御事件：攻击
    并不真正启动，只是检查事件是否处于合法状态
    """
    #节点上必须有合法的防御随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_DEFEND:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if node.is_event_over_idletime(now):
        logger.warning("Event over idletime[node basic id=%d][event type=%d][arise time=%d]" %
                (node.basic_id, node.event_type, node.event_arise_time))
        return False
    return True


def finish_defend_event_succeed(data, node, now, change_nodes):
    """结束防御事件：胜利
    战胜了敌人，敌人消失
    """
    #节点上必须有合法的防御随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_DEFEND:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if not node.launch_event(now, overtime = True):
        return False

    #获得功勋值
    rival_id = node.rival_id
    rival = data.rival_list.get(rival_id, True)
    resource = data.resource.get()
    resource.update_current_resource(now)
    ac_base = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementBase
    ac_coe = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementCoefficient
    achievement = ac_base + ac_coe * rival.level
    resource.gain_achievement(achievement)

    #守卫节点成功，敌人消失
    if not map_business.protect_key_node_from_invasion(data, node, now):
        return False

    if not node.finish_event(now, overtime = True):
        return False

    change_nodes.append(node)
    return True


def finish_defend_event_fail(data, node, now, change_nodes, new_items, new_mails):
    """结束防御事件：失败
    攻击敌人失败
    """
    #节点上必须有合法的防御随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_DEFEND:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if not node.launch_event(now, overtime = True):
        return False

    if not node.finish_event(now, overtime = True):
        return False

    #节点丢失
    if not map_business.lost_key_node_of_invasion(
            data, node, now, change_nodes, new_items, new_mails):
        return False
    return True

