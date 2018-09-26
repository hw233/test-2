#coding:utf8
"""
Created on 2016-5-4
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 大地图上己方点的保护逻辑
         目前保护只针对己方生效，与其他玩家暂无交互:
         1. 己方的资源点和主城可以开保护罩
         2. 资源点若正有防御事件，无法开保护罩
         3. 资源点若已开保护罩，不会触发防御事件和dungeon,也不会触发战争事件
         4. 若主城开保护，且收到被攻打的战报，不通报玩家
            若某资源点开保护，防守成功的点不选择改点通报（防守失败的现有逻辑就是不通知玩家）
         5. 若玩家主动发起战斗（pve山贼叛军、dungeon、演武场除外）,所有保护罩消失

"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.node import NodeInfo
from app.core import reward as reward_module
from app.business import mail as mail_business
from app.business import hero as hero_business
from app.business import item as item_business
from app.business import map as map_business
from app import log_formater


def protect(data, node, type, use_gold, duration, item, now):
    """进行资源采集
    """
    if node == None:
        return False

    if node.is_dependency():
        logger.warning("Wrong node type[node_id=%d][type=%d]" % (node.id, node.type))
        return False

    if not node.is_own_side():
        logger.warning("Wrong node status[node_id=%d][status=%d]" % (node.id, node.status))
        return False

    if node.event_type == NodeInfo.EVENT_TYPE_DEFEND:
        logger.warning("Node has defend event[node_id=%d]" % node.id)
        return False

    if type == NodeInfo.PROTECT_TYPE_CITY:
        if not node.is_own_city():
            return False
    elif type == NodeInfo.PROTECT_TYPE_RESOURCE_NODE:
        if node.is_own_city():
            return False
    else:   
        logger.warning("protect type error")
        return False

    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    output_items = []
    if use_gold:
        if type == NodeInfo.PROTECT_TYPE_CITY:
            key = "protect_city_cost_" + str(duration / 3600)
        else:
            key = "protect_resource_node_cost_" + str(duration / 3600)
           
        need_gold = int(float(data_loader.OtherBasicInfo_dict[key].value))
        if not resource.cost_gold(need_gold):
            return False

        log = log_formater.output_gold(data, -need_gold, log_formater.PROTECT,
                "Protect by gold", before_gold = original_gold, protect_hour = (duration/3600))
        logger.notice(log)

    else:
        if ((type == NodeInfo.PROTECT_TYPE_CITY 
                and not item.is_protect_city_item())
            or (type == NodeInfo.PROTECT_TYPE_RESOURCE_NODE 
                and not item.is_protect_resource_node_item())):
            logger.warning("protect item error[type=%d][item_id=%d]" % (type, item.basic_id))
            return False
        consume =  item.consume(1)
        if not consume[0]:
            return False
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        log = log_formater.output_item(data, "protect", log_formater.PROTECT, ''.join(output_items))
        logger.notice(log)

    node.protect(now, duration)
    if type == NodeInfo.PROTECT_TYPE_CITY:
        user = data.user.get()
        user.set_in_protect(True)

    return True


