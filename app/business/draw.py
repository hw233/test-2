#coding:utf8
"""
Created on 2016-01-08
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 抽奖相关计算逻辑
"""

from utils import utils
from utils import logger
from datalib.data_loader import data_loader
from app.business.activity import ActivityPool
from app.data.draw import DrawInfo
from app import log_formater


def init_draw(data, now):
    """创建抽奖信息
    """
    draw = DrawInfo.create(data.id)
    data.draw.add(draw)
    draw.try_reset_draw(now)

    return True


def draw_with_money(user, resource, draw, hero_list, item_list, now, draw_item, free = False):
    """使用金钱进行一次抽奖
    """
    draw.try_reset_draw(now)

    if user.is_first_money_draw:
        type = draw.DRAW_TYPE_MONEY_FIRST
        user.mark_money_draw()
    else:
        type = draw.DRAW_TYPE_MONEY

    if draw_item != None:
        #耗费抽奖券
        if draw_item.basic_id != int(float(
                data_loader.OtherBasicInfo_dict["MoneySearchOneItemId"].value)):
            logger.warning("draw item is wrong[basic_id=%d]" % draw_item.basic_id)
            return False

        if not draw_item.use_draw_item(1):
            raise Exception("Use draw item failed")
    else:
        #耗费金钱
        need_money = draw.calc_draw_cost(type, now, free)
        if need_money < 0:
            return False
        if not resource.cost_money(need_money):
            return False
        logger.debug("money draw[free=%r][cost=%d]" % (free, need_money))

    if not draw.calc_draw_reward(user, type, hero_list, item_list):
        return False

    return True

def treasure_draw(basic_data, data, user, resource, draw,  item_list, req, now):
    need_gold = 0
    original_gold = resource.gold
    if req.times == 1:
        need_gold = int(float(data_loader.OtherBasicInfo_dict["TurntableSearchOneCost"].value))
    elif req.times == 10:
        need_gold = int(float(data_loader.OtherBasicInfo_dict["TurntableSearchTenCost"].value))
    else:
        raise Exception("Treasure draw times error")
    if not resource.cost_gold(need_gold):
        return False
    log = log_formater.output_gold(data, -need_gold, log_formater.TURN_DRAW,
       "turn draw cost")
    logger.notice(log)
    if not draw.calc_treasure_draw_reward(basic_data, user, req,  item_list):
        return False

    if need_gold > 0:
        _output_draw_by_gold(data, need_gold, original_gold, log_formater.DRAW_ONE,
                "Treasure draw by gold", item_list, [])

    _update_treasure_scores(basic_data, data, draw, req.times, now)

    return True

def draw_with_gold(basic_data, data, user, resource, draw, hero_list, item_list, now, draw_item, free = False):
    """使用元宝进行一次抽奖
    """
    draw.try_reset_draw(now)

    if user.is_first_gold_draw:
        type = draw.DRAW_TYPE_GOLD_FIRST
        user.mark_gold_draw()
    else:
        type = draw.DRAW_TYPE_GOLD

    need_gold = 0
    original_gold = resource.gold
    if draw_item != None:
        #耗费抽奖券
        if draw_item.basic_id != int(float(
                data_loader.OtherBasicInfo_dict["GoldSearchOneItemId"].value)):
            logger.warning("draw item is wrong[basic_id=%d]" % draw_item.basic_id)
            return False

        if not draw_item.use_draw_item(1):
            raise Exception("Use draw item failed")
    else:
        #耗费元宝
        need_gold = draw.calc_draw_cost(type, now, free)
        if need_gold < 0:
            return False
        if not resource.cost_gold(need_gold):
            return False
        logger.debug("gold draw[free=%r][cost=%d]" % (free, need_gold))

    if not draw.calc_draw_reward(user, type, hero_list, item_list):
        return False

    if need_gold > 0:
        _output_draw_by_gold(data, need_gold, original_gold, log_formater.DRAW_ONE,
                "Draw one by gold", item_list, hero_list)

    draw.set_last_gold_draw_time(now)
    _update_activity_scores(basic_data, data, draw, 1, now)

    return True


def multi_draw_with_gold(basic_data, data, user, resource, draw, hero_list, item_list, now, draw_item):
    """使用元宝进行十次连续抽奖
    Args:
        resource[ResourceInfo]: 资源信息
        draw[DrawInfo]: 抽奖的信息
        hero_list[list((hero_basic_id, num)) out]: 获得的英雄信息列表
        item_list[list((item_basic_id, num)) out]: 获得的物品信息列表
    Returns:
        失败返回 False
        成功返回 True
    """
    draw.try_reset_draw(now)

    need_gold = 0
    original_gold = resource.gold
    if draw_item != None:
        #耗费抽奖券
        if draw_item.basic_id != int(float(
                data_loader.OtherBasicInfo_dict["GoldSearchTenItemId"].value)):
            logger.warning("draw item is wrong[basic_id=%d]" % draw_item.basic_id)
            return False

        if not draw_item.use_draw_item(1):
            raise Exception("Use draw item failed")
    else:
        #耗费元宝
        need_gold = draw.calc_draw_cost(draw.DRAW_TYPE_GOLD_MULTI, now)
        if need_gold < 0:
            return False
        if not resource.cost_gold(need_gold):
            return False
        logger.debug("multi gold draw[cost=%d]" % need_gold)

    if not draw.calc_draw_reward(user, draw.DRAW_TYPE_GOLD_MULTI, hero_list, item_list):
        return False

    if need_gold > 0:
        _output_draw_by_gold(data, need_gold, original_gold, log_formater.DRAW_MULTI,
                "Draw ten by gold", item_list, hero_list)
    
    draw.set_last_gold_draw_time(now)
    scores_before = draw.activity_scores
    basic_activities = _update_activity_scores(basic_data, data, draw, 10, now)
    scores_after = draw.activity_scores
    
    if basic_activities != None and scores_before != scores_after and scores_before / 10 != scores_after / 10:
        basic_activity = basic_activities[0]
        #每满20积分送一个神将魂石
        info = None
        for key in data_loader.ItemBasicInfo_dict:
            info = data_loader.ItemBasicInfo_dict[key]
            if info.type == 3 and info.value == basic_activity.hero_basic_id:
                break
            else:
                info = None
        if info is not None:
            item_list.pop()
            item_list.append((info.id, 1))

    return True


def multi_draw_with_money(user, resource, draw, hero_list, item_list, now, draw_item):
    """使用金钱进行十次连续抽奖
    """
    draw.try_reset_draw(now)

    if draw_item != None:
        #耗费抽奖券
        if draw_item.basic_id != int(float(
                data_loader.OtherBasicInfo_dict["MoneySearchTenItemId"].value)):
            logger.warning("draw item is wrong[basic_id=%d]" % draw_item.basic_id)
            return False

        if not draw_item.use_draw_item(1):
            raise Exception("Use draw item failed")
    else:
        #耗费金钱
        need_money = draw.calc_draw_cost(draw.DRAW_TYPE_MONEY_MULTI, now)
        if need_money < 0:
            return False
        if not resource.cost_money(need_money):
            return False
        logger.debug("multi money draw[cost=%d]" % need_money)

    if not draw.calc_draw_reward(user, draw.DRAW_TYPE_MONEY_MULTI, hero_list, item_list):
        return False

    return True


def _output_draw_by_gold(data, gold, original_gold,  type, str, item_list, hero_list):
    """
    """
    draw_items_id = []
    draw_items_num = []
    draw_heroes_id = []
    for item in item_list:
        draw_items_id.append(item[0])
        draw_items_num.append(item[1])
    for hero in hero_list:
        draw_heroes_id.append(hero[0])

    log = log_formater.output_gold(data, -gold, type,
            str, before_gold = original_gold, items_id = draw_items_id, items_num = draw_items_num, 
            heroes_id = draw_heroes_id)
    logger.notice(log)

def _update_treasure_scores(basic_data, data, draw, times, now):
    assert times == 1 or times == 10
    
    #拿到活动
   # activity_treasure_type_id = int(float(
   #     data_loader.OtherBasicInfo_dict["activity_treasure_type_id"].value))
    #先更新活动
    ActivityPool().update_activity_by_type(basic_data, data, 29)
  
    activities = ActivityPool().get_activity_by_type(basic_data, data, 29, now)
    if len(activities) == 0:
        return None
    #draw.add_treasure_scores(req.times)
    basic_activities = []
    for activity in activities:
        #更新活动的progress
        #progress = utils.split_to_int(activity.progress)[0]
        #progress += activity_addition_scores
        progress = draw.total_treasure_draw_num
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        activity.forward_all(basic_activity, progress, now)
        basic_activities.append(basic_activity)

    return basic_activities

    

def _update_activity_scores(basic_data, data, draw, gold_draw_num, now):
    """更新活动的进度
    """
    assert gold_draw_num == 1 or gold_draw_num == 10

    #拿到活动
    activity_hero_type_id = int(float(
        data_loader.OtherBasicInfo_dict["activity_hero_type_id"].value))
   
    #先更新活动
    ActivityPool().update_activity_by_type(basic_data, data, activity_hero_type_id)
    
    activities = ActivityPool().get_activity_by_type(basic_data, data, activity_hero_type_id, now)
    if len(activities) == 0:
        return None
        
    draw_one_score = int(float(
        data_loader.OtherBasicInfo_dict["gold_draw_one_activity_score"].value))
    #计算增加的积分
    activity_addition_scores = gold_draw_num * draw_one_score
    draw.add_activity_scores(activity_addition_scores)
   
    basic_activities = []
    for activity in activities:
        #更新活动的progress
        #progress = utils.split_to_int(activity.progress)[0]
        #progress += activity_addition_scores
        progress = draw.activity_scores
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        activity.forward_all(basic_activity, progress, now)
        basic_activities.append(basic_activity)

    return basic_activities
    
