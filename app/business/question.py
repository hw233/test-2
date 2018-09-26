#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 问答随机事件逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.node import NodeInfo
from app.business import hero as hero_business
from app.business import item as item_business
from app import log_formater

def arise_question_event(data, node, now, **kwargs):
    """出现问答事件
    """
    if not node.arise_event(NodeInfo.EVENT_TYPE_QUESTION, now):
        return False

    map = data.map.get()
    map.update_for_question_event()
    return True


def clear_question_event(data, node, now, **kwargs):
    """清除探访事件
    """
    #节点上必须有合法的探访随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_QUESTION:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    question = data.question.get()
    question.finish()
    return node.clear_event()


def start_question_event(data, node, now):
    """启动问答事件
    Returns:
        True/False
    """
    #节点上必须有合法的问答随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_QUESTION:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False
    if not node.launch_event(now):
        return False

    question = data.question.get()
    question.start(node, now)
    return True


def finish_question_event(data, node, question_id, answer, correct, now):
    """结束问答事件
    Args:
        data
        node[NodeInfo]: 节点信息
        question_id[int]: 问题 id
        answer[list(int)]: 回答
        correct[bool]: 回答是否正确
        now[int]: 当前时间戳
    Returns:
        True/False
    """
    #节点上必须有合法的问答随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_QUESTION:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False
    if not node.is_event_launched():
        logger.warning("Lucky event not launched")
        return False

    #结束问答流程
    question = data.question.get()
    if correct != question.answer(question_id, answer):
        logger.warning("Answer check error")
        return False
    question.finish()

    if correct:
        #如果回答正确，用户获得收益（英雄、物品）
        hero_basic_id = data_loader.EventQuestionBasicInfo_dict[question_id].heroBasicId
        items_basic_id = data_loader.EventQuestionBasicInfo_dict[question_id].itemBasicId
        items_num = data_loader.EventQuestionBasicInfo_dict[question_id].itemNum
        assert len(items_basic_id) == len(items_num)
        item_info = []
        for i in range(0, len(items_basic_id)):
            item_info.append((items_basic_id[i], items_num[i]))

        if hero_basic_id != 0 and not hero_business.gain_hero(data, hero_basic_id):
            return False
        if len(item_info) > 0 and not item_business.gain_item(data, item_info, " question reward", log_formater.QUESTION_REWARD):
            return False

        #如果回答正确，获得功勋值
        user = data.user.get(True)
        resource = data.resource.get()
        resource.update_current_resource(now)
        ac_base = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementBase
        ac_coe = data_loader.LuckyEventBasicInfo_dict[node.event_type].achievementCoefficient
        achievement = ac_base + ac_coe * user.level
        resource.gain_achievement(achievement)

    return node.finish_event(now)

