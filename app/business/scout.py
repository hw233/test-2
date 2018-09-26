#coding:utf8
"""
Created on 2016-05-20
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 侦察事件逻辑
"""

from utils import logger
from app.data.node import NodeInfo
from app.business import map as map_business


def arise_scout_event(data, node, now, **kwargs):
    """出现侦察事件
    """
    if not node.arise_event(NodeInfo.EVENT_TYPE_VISIT, now):
        return False

    return map_business.respawn_enemy_key_node(data, node, now)


