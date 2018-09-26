#coding:utf8
"""
Created on 2016-05-24
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 祈福相关逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.pray import PrayInfo
from app.data.item import ItemInfo
from app.core import reward as reward_business
from app.business import item as item_business
from app import log_formater


def init_pray(data, now):
    """创建祈福信息
    """
    user = data.user.get(True)

    pray = PrayInfo.create(data.id, now)
    return pray


def start_pray(data, type, building_level, cost_gold=0):
    """开始祈福
    """
    resource = data.resource.get()
    pray = data.pray.get()
    food_cost = pray.calc_pray_food_cost(type, building_level)
    user = data.user.get()
    original_gold = resource.gold

    if not pray.is_able_to_pray(type, building_level) and cost_gold == 0:
        logger.warning("Not able to pray[user_id=%d]" % data.id)
        return False

    if cost_gold == 0:
        if food_cost != 0 and not resource.cost_food(food_cost):
            logger.warning("No enough food[user_id=%d]" % data.id)
            return False
    else:
        need_gold = pray.calc_force_pray_gold_cost(type, user.vip_level)
        if need_gold != cost_gold:
            logger.warning("Force pray gold number error"
                    "[user_id=%s][req_gold=%s][true_gold=%s]" % 
                    (data.id, cost_gold, need_gold))

        if cost_gold != 0 and not resource.cost_gold(cost_gold):
            logger.warning("No enough gold[user_id=%d]" % data.id)
            return False
        
        log = log_formater.output_gold(data, -cost_gold, log_formater.REFRESH_PRAY,
                "Pray by gold", before_gold = original_gold)
        logger.notice(log)

    pray_item_list = reward_business.random_pray_gift(type, building_level)
    if not pray.pray(type, pray_item_list, cost_gold):
        return False

    return True


def refresh_pray(data, type, building_level, cost_gold, now):
    """
    """
    user = data.user.get()
    pray = data.pray.get()
    resource = data.resource.get()
    original_gold = resource.gold

    need_gold = pray.calc_refresh_gold_cost(type, user.vip_level)
    if need_gold is None:
        return (False, original_gold)

    if need_gold != cost_gold:
        logger.warning("pray gold cost is error[need_gold=%d][cost_gold=%d]"
                % (need_gold, cost_gold))
        return (False, original_gold)

    if need_gold != 0 and not resource.cost_gold(need_gold):
        logger.warning("not enough gold[need_gold=%d][gold=%d]"
                % (need_gold, resource.gold))
        return (False, original_gold)
    log = log_formater.output_gold(data, -need_gold, log_formater.REFRESH_PRAY,
                "Refresh pray by gold", before_gold = original_gold)
    logger.notice(log)

    if not pray.refresh(type):
        return (False, original_gold)

    return (True, original_gold)


def choose_card(data, choose_index, cost_gold):
    """翻牌
    """
    pray = data.pray.get()
    #消耗祈福令
    cost_item = pray.calc_choose_card_use_item()
    id = ItemInfo.generate_id(data.id, cost_item[0])
    item = data.item_list.get(id)
    if cost_item[1] != 0 and item == None and cost_gold == 0:
        logger.warning("Pray item and gold error")
        return False
    if cost_item[1] != 0:
        need_gold = 0
        output_items = []
        if item == None:
            need_gold = cost_item[1] * int(float(data_loader.OtherBasicInfo_dict["ItemPrayGoldCost"].value))
        elif cost_item[1] > item.num:
            need_gold = (cost_item[1] - item.num) * int(float(data_loader.OtherBasicInfo_dict["ItemPrayGoldCost"].value))
            consume = item.consume(item.num)
            output_items.append("[item=")
            output_items.append(utils.join_to_string(list(consume[1])))
            output_items.append("]")
        else:
            consume = item.consume(cost_item[1])
            output_items.append("[item=")
            output_items.append(utils.join_to_string(list(consume[1])))
            output_items.append("]")
        log = log_formater.output_item(data, "choose card", log_formater.CHOOSE_CARD, ''.join(output_items))
        logger.notice(log)
        if need_gold != cost_gold:
            logger.warning("choose card gold cost is error[need_gold=%d][cost_gold=%d]"
                    % (need_gold, cost_gold))
            return False

        resource = data.resource.get()
        original_gold = resource.gold
        if need_gold != 0 and not resource.cost_gold(need_gold):
            logger.warning("not enough gold[need_gold=%d][has_gold=%d]"
                % (need_gold, resource.gold))
            return False
        log = log_formater.output_gold(data, -need_gold, log_formater.CHOOSE_CARD,
                "Choose card by gold ", before_gold = original_gold)
        logger.notice(log)
	    

    #翻牌
    get_item = pray.choose_card(choose_index)
    if get_item is None:
        return False
    if not PrayInfo.is_item_pray_multi(get_item[0]):
        id = ItemInfo.generate_id(data.id, get_item[0])
        item = data.item_list.get(id)
        #if item == None:
        items = []
        items.append(get_item)
        item_business.gain_item(data, items, "choose card", log_formater.CHOOSE_CARD)
        #else:
        #    item.acquire(get_item[1])

    #统计
    trainer = data.trainer.get()
    trainer.add_daily_choose_card_num(1)

    return True


