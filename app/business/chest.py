#coding:utf8
"""
Created on 2016-07-08
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 红包相关逻辑
"""

import copy
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.chest import ChestInfo
from app.data.item import ItemInfo
from app.business import item as item_business
from app import log_formater


def init_chest(data, now):
    """创建红包信息
    """
    user = data.user.get(True)

    chest = ChestInfo.create(data.id, now)
    chest.update_info(now)
    return chest


def open_chest(data, chest, now):

    if not chest.is_in_duration(now):
        logger.warning("Open chest not in duration[start=%d][now=%d]" % (chest.next_start_time, now))
        #return None

    items_info = chest.get_items_info()
    #领取物品奖励
    if not item_business.gain_item(data, items_info, "chest reward", log_formater.CHEST_REWARD):
        return None
    
    result = copy.deepcopy(chest)
    result._calc_next_start_time(now)
    
    #领取资源奖励
    resource = data.resource.get()
    original_gold =  resource.gold
    resource.update_current_resource(now)
    chest_reward_gold = int(float(chest.gold))
    resource.gain_money(int(float(chest.money)))
    resource.gain_food(int(float(chest.food)))
    resource.gain_gold(chest_reward_gold)
    log = log_formater.output_gold(data, chest_reward_gold, log_formater.CHEST_REWARD_GOLD,
                "Gain gold from chest", before_gold = original_gold)
    logger.notice(log)

    chest.update_info(now)
    return result


def query_chest(chest, now):
    """
    """
    if not chest.is_in_duration(now):
        chest.update_info(now)

    return True


def create_broadcast(data, gold):
    """创建广播"""
    broadcast_id = \
            int(float(data_loader.OtherBasicInfo_dict["broadcast_id_baoxiang"].value))

    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    user = data.user.get(True)
    content = template.replace("#str#", user.get_readable_name(), 1)
    content = content.replace("#str#", ("@%s@" % str(gold)), 1)
    
    return (mode_id, priority, life_time, content)


