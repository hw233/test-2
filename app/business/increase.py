#coding:utf8
"""
Created on 2016-5-4
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 大地图上资源点的增产逻辑
         目前增速只针对己方生效，与其他玩家暂无交互:
         1. 己方的资源点可以开保护罩
         2. 资源点开保护后，不影响随机事件概率(客户端为了显示效果，限制了有防御事件时就不能发起增产请求)
         3. 收菜时，根据增产倍率计算可收获资源值

"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.node import NodeInfo
from app import log_formater


def increase(data, node, rate, use_gold, duration, item, now):
    """进行资源点增产
    """
    if node == None:
        return False

    if not node.is_own_side() or not node.is_exploit_exist():
        logger.warning("Wrong node type[node_id=%d][type=%d]" % (node.id, node.type))
        return False

    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)

    if node.is_exploit_money():
        key = "businesscity_boost_" + str(duration / 3600)
    elif node.is_exploit_food():
        key = "agriculturecity_boost_" + str(duration / 3600)
    else:
        key = "miningcity_boost_" + str(duration / 3600)
       
    need_gold = int(float(data_loader.OutputIncreaseBasicInfo_dict[key].goldNum))
    increase_rate = float(data_loader.OutputIncreaseBasicInfo_dict[key].increaseRate)
    if rate != increase_rate:
        logger.warning("Increase rate error[req_rate=%f][rate=%f]" % (rate, increase_rate))
        return False

    if use_gold:
        if not resource.cost_gold(need_gold):
            return False

        log = log_formater.output_gold(data, -need_gold, log_formater.INCREASE,
                "Increase by gold", before_gold = original_gold, increase_hour = (duration/3600))
        logger.notice(log)

    else:
        if ((node.is_exploit_money() and not item.is_increase_node_money_item())
                or (node.is_exploit_food() and not item.is_increase_node_food_item())
                or (node.is_exploit_material() and not item.is_increase_node_material_item())):
            logger.warning("Increase item error[type=%d][item_id=%d]" % (type, item.basic_id))
            return False
        consume = item.consume(1)
        if not consume[0]:
            return False
        output_items= []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(data, "use increase item", log_formater.INCREASE_ITEM, item)
        logger.notice(log)
	#logger.notice("increase %s"%''.join(output_items))
	
    node.increase(rate, now, duration)
    return True


