#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 探访随机事件逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.node import NodeInfo
from app.data.visit import VisitInfo
from app.business import hero as hero_business
from app.business import item as item_business
from app import log_formater


def arise_visit_event(data, node, now, **kwargs):
    """出现探访事件
    """
    if not node.arise_event(NodeInfo.EVENT_TYPE_VISIT, now):
        return False

    map = data.map.get()
    map.update_for_visit_event()
    return True


def clear_visit_event(data, node, now, **kwargs):
    """清除探访事件
    """
    #节点上必须有合法的探访随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_VISIT:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    visit = data.visit_list.get(node.id)
    visit.finish()
    return node.clear_event()


def start_visit_event(data, node, candidate, now):
    """启动探访事件
    Args:
        data
        node[NodeInfo]: 节点信息
        candidate[list(visit_id) out]: 探访候选项
        now[int]: 当前时间戳
    Returns:
        True/False
    """
    #节点上必须有合法的探访随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_VISIT:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False
    if not node.launch_event(now):
        return False

    visit = data.visit_list.get(node.id)
    if visit is None:
        visit = VisitInfo.create(data.id, node.id)
        data.visit_list.add(visit)

    visit.start(now)
    candidate.extend(visit.get_candidate())
    return True


def search_visit_event(data, node, candidate, now):
    """查询探访事件
    查询一个节点上出现的探访事件
    """
    #节点上必须有合法的探访随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_VISIT:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if node.is_event_over_lifetime(now):
        logger.warning("Visit event over lifetime[arise time=%d][launch time=%d]" %
                (node.event_arise_time, node.event_launch_time))
        return False

    visit = data.visit_list.get(node.id, True)
    candidate.extend(visit.get_candidate())
    return True


def finish_visit_event(data, node, visit_id, now, use_gold = 0):
    """结束探访事件
    Args:
        data
        node[NodeInfo]: 节点信息
        visit_id[int]: 探访选项 visit_id == 0, 表示放弃选择
        now[int]: 当前时间戳
    Returns:
        True/False
    """
    #节点上必须有合法的探访随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_VISIT:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    #结束探访流程
    visit = data.visit_list.get(node.id)
    if visit_id != 0 and not visit.is_candidate_valid(visit_id):
        return False
    visit.finish()

    if visit_id != 0:
        #用户花费金钱/元宝，获得收益（英雄、物品）
        user = data.user.get(True)
        resource = data.resource.get()
        original_gold = resource.gold
        resource.update_current_resource(now)

        money_base = data_loader.EventVisitBasicInfo_dict[visit_id].costMoneyBase
        money_coe = data_loader.EventVisitBasicInfo_dict[visit_id].costMoneyCoefficient
        gold = data_loader.EventVisitBasicInfo_dict[visit_id].costGold
        money = money_base + money_coe * user.level

        #如果金钱不够，使用元宝兑换
        cost_gold = 0
        money_gap = 0
        if resource.money < money:
            money_gap = money - resource.money
            cost_gold = resource.gold_exchange_resource(money = money_gap)
            if cost_gold != use_gold:
                logger.warning("Gold exchange resource failed"
                        "[try cost gold=%d][real cost gold=%d]" %
                        (use_gold, cost_gold))
                return False

        if not resource.cost_money(money) or not resource.cost_gold(gold):
            return False

        hero_basic_id = data_loader.EventVisitBasicInfo_dict[visit_id].heroBasicId
        item_basic_id = data_loader.EventVisitBasicInfo_dict[visit_id].itemBasicId
        item_num = data_loader.EventVisitBasicInfo_dict[visit_id].itemNum
        if hero_basic_id != 0 and not hero_business.gain_hero(data, hero_basic_id):
            return False
        if item_basic_id != 0 and not item_business.gain_item(data, [(item_basic_id, item_num)], "visit reward", log_formater.VISIT_REWARD):
            return False

        #获得成就值
        ac_base = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementBase
        ac_coe = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementCoefficient
        achievement_value = ac_base + ac_coe * user.level
        resource.gain_achievement(achievement_value)

        if cost_gold + gold > 0:
            visit_items_id = []
            visit_items_num = []
            visit_heroes_id = []
            if item_basic_id != 0:
                visit_items_id.append(item_basic_id)
                visit_items_num.append(item_num)

            if hero_basic_id != 0:
                visit_heroes_id.append(hero_basic_id)
                
            log = log_formater.output_gold(data, -(cost_gold + gold), log_formater.VISIT,
                "Visit by gold", money = money_gap, before_gold = original_gold,  achievement = achievement_value,
                items_id = visit_items_id, items_num = visit_items_num, 
                heroes_id = visit_heroes_id)
            logger.notice(log)


    return node.finish_event(now)

