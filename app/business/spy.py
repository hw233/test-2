#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 谍报随机事件逻辑
"""

from utils import logger
from datalib.data_loader import data_loader
from app.data.node import NodeInfo
from app.data.spy import SpyPool
from app.business import map as map_business


def arise_spy_event(data, node, now, **kwargs):
    """出现谍报事件
    虚弱敌人
    """
    if not node.arise_event(NodeInfo.EVENT_TYPE_SPY, now):
        return False

    rival_id = node.rival_id
    rival = data.rival_list.get(rival_id)

    spy_id = SpyPool().choose(rival.level)
    logger.debug("spy enemy[rival id=%d][rival level=%d][spy id=%d]" %
            (rival.id, rival.level, spy_id))
    buff_id = data_loader.EventSpyBasicInfo_dict[spy_id].buffId
    rival.set_buff(buff_id)
    return True


def clear_spy_event(data, node, now, **kwargs):
    """清除谍报事件
    敌人的减益效果消失
    """
    #节点上必须有合法的谍报随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_SPY:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    rival_id = node.rival_id
    rival = data.rival_list.get(rival_id)
    rival.clear_buff()
    return node.clear_event()


def start_spy_event(data, node, now):
    """启动谍报事件：攻击
    并不真正启动，只是检查事件是否处于合法状态
    """
    #节点上必须有合法的谍报随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_SPY:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if node.is_event_over_idletime(now):
        logger.warning("Event over idletime[node basic id=%d][event type=%d][arise time=%d]" %
                (node.basic_id, node.event_type, node.event_arise_time))
        return False
    return True


def finish_spy_event_succeed(data, node, now, change_nodes):
    """结束谍报事件：胜利
    战胜敌人
    敌人的减益效果消失
    占据关键点
    """
    #节点上必须有合法的谍报随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_SPY:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if not node.launch_event(now, overtime = True):
        return False

    #获得成就值
    rival_id = node.rival_id
    rival = data.rival_list.get(rival_id)
    resource = data.resource.get()
    resource.update_current_resource(now)
    ac_base = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementBase
    ac_coe = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementCoefficient
    achievement = ac_base + ac_coe * rival.level
    resource.gain_achievement(achievement)

    rival.clear_buff()

    if not node.finish_event(now, overtime = True):
        return False

    map = data.map.get()
    if map.is_able_to_occupy_more():
        return map_business.dominate_key_node(data, node, change_nodes, now)
    else:
        return map_business.close_spy_key_node(data, node, change_nodes, now)


