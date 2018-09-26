#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.union import UserUnionInfo
from app.data.item import ItemInfo
from app.data.hero import HeroInfo
from app.business import item as item_business
from app.business import user as user_business
from app import log_formater

def init_union(data, now):
    """初始化联盟信息
    """
    union = UserUnionInfo.create(data.id)
    data.union.add(union)


def is_able_to_create_union(data, gold, now):
    """是否可以创建联盟
    需要等级满足要求，有足够元宝
    """
    union = data.union.get(True)
    if union.is_belong_to_union():
        logger.warning("Not able to create union")
        return False

    cost_gold = union.calc_create_cost_gold()
    need_level = union.calc_create_need_level()

    user = data.user.get(True)
    if user.level < need_level:
        logger.warning("Level error[need=%d][now=%d]" % (need_level, user.level))
        return False

    if cost_gold != gold:
        logger.warning("Cost gold error[need=%d][cost=%d]" % (cost_gold, gold))
        return False
    resource = data.resource.get()
    resource.update_current_resource(now)
    if resource.gold < cost_gold:
        logger.warning("Not enough gold[own=%d][cost=%d]" % (resource.gold, cost_gold))
    return True


def create_union(data, union_id, gold, now):
    """创建联盟
    不受联盟锁定时间影响
    消耗元宝
    """
    union = data.union.get()
    union.reset_lock_time(now)
    union.join_union(union_id, now)

    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold
    assert resource.cost_gold(gold)
    log = log_formater.output_gold(data, -gold, log_formater.CREATE_UNION,
            "Create union by gold", before_gold = original_gold)
    logger.notice(log)


def join_union(data, union_id, now):
    """加入联盟
    """
    union = data.union.get()
    if is_creator:
        union.reset_lock_time(now)

    union.join_union(union_id, now)


def is_able_to_start_aid(data, item_basic_id, item_num, now):
    """发起联盟援助
    """
    union = data.union.get(True)

    #需要拥有对应英雄或者拥有将魂石
    item_id = ItemInfo.generate_id(data.id, item_basic_id)
    item = data.item_list.get(item_id, True)
    if item is not None and not item.is_starsoul_item():
        logger.warning("Item is not a starsoul stone[item_basic_id=%d]" % item_basic_id)
        return False

    hero_basic_id = ItemInfo.get_corresponding_value(item_basic_id)
    hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
    hero = data.hero_list.get(hero_id, True)

    if item is None and hero is None:
        logger.warning("Can not start aid[item_basic_id=%d]" % item_basic_id)
        return False

    #数量正确
    expect_num = union.calc_aid_item_num(item_basic_id)
    if item_num != expect_num:
        logger.warning("Aid item num error[wrong_num=%d][item_num=%d]" % (
            item_num, expect_num))
        return False

    return True


def start_aid(data, now):
    """发起援助
    """
    union = data.union.get()
    union.start_aid(now)


def finish_aid(data, item_basic_id, item_num):
    """结束援助
    """
    #获得物品
    item_business.gain_item(data, [(item_basic_id, item_num)], "finish aid", log_formater.FINISH_AID)

    union = data.union.get()
    union.finish_aid()


def is_able_to_respond_aid(data, item_basic_id):
    """是否可以进行捐赠
    """
    item_id = ItemInfo.generate_id(data.id, item_basic_id)
    item = data.item_list.get(item_id, True)
    if item is None:
        logger.warning("No item to respond aid[item_basic_id=%d]" % item_basic_id)
        return False
    elif item.num < 1:
        logger.warning("Not enough item num to respond aid[item_basic_id=%d][item_num=%d]" %
                (item_basic_id, item.num))
        return False

    return True


def respond_aid(data, item_basic_id, honor, exp, gold, now):
    """响应援助，进行捐赠
    获得奖励
    """
    union = data.union.get()

    #消耗物品
    item_id = ItemInfo.generate_id(data.id, item_basic_id)
    item = data.item_list.get(item_id)
    consume = item.consume(1)
    if not consume[0]:
        return False
    output_items = []
    output_items.append("[item=")
    output_items.append(utils.join_to_string(list(consume[1])))
    output_items.append("]")
    log = log_formater.output_item(data, "respond aid", log_formater.RESPOND_AID, ''.join(output_items))
    logger.notice(log)
    #logger.notice("respond aid %s"%''.join(output_items))
    #获得联盟荣誉
    union.gain_honor(honor)

    #获得主公经验
    if not user_business.level_upgrade(data, exp, now, "exp aid", log_formater.EXP_AID):
        return False

    #获得元宝奖励
    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold
    resource.gain_gold(gold)
    log = log_formater.output_gold(data, gold, log_formater.RESPOND_AID_REWARD,
                "Gain gold from respond aid", before_gold = original_gold)
    logger.notice(log)


    return True


