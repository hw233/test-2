#coding:utf8
"""
Created on 2016-03-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 充值相关计算逻辑
"""

from utils import logger
from datalib.data_loader import data_loader
from app.core.pay import PayLogic
from app.data.pay import PayPool
from app.data.pay import PayInfo
from app.data.pay_record import PayRecordInfo
from app.business import item as item_business
from app import log_formater

def init_pay(data, pattern, now):
    """创建充值商店信息
    """
    pay = PayInfo.create(data.id, pattern, now, PayLogic().is_sandbox, PayLogic().enable_multi_count)
    data.pay.add(pay)
    return True


def query_pay(data, now):
    """查询充值商店的信息
    如果到了刷新时间，则刷新一次后再返回
    Returns:
        list(int): 可以购买的商品 id
    """
    pay = data.pay.get()

    if data_loader.OtherBasicInfo_dict.has_key("init_id"):
        pattern = int(float(data_loader.OtherBasicInfo_dict['init_id'].value))
    else:
        pattern = 1
    if not pay.try_refresh(now, PayLogic().is_sandbox, PayLogic().enable_multi_count, pattern):
        logger.warning("Try refresh pay failed")
        return None

    return pay.get_all()


def get_order(data, platform, id, now, value = None):
    """获得订单信息
    根据用户的购买需求，生成对应的订单信息
    Args:
        data
        platform: 充值平台:
        id: 购买商品 id
        now: 时间戳
    Returns:
        string: 订单信息
        空字符串，表示失败
    """
    #下单，获取订单信息、订单号和商品信息
    (info, order_number, order) = PayLogic().calc_order_info(data.id, platform, id, now, value)

    #商店进行预购记录
    pay = data.pay.get()
    pay.pre_order(order_number)

    #添加充值记录（未完成状态）
    record = PayRecordInfo.create(data.id, pay.pay_count, platform, now)
    record.set_detail(order.id, order_number, order.truePrice)
    data.pay_record_list.add(record)

    return (info, order_number)


def pay_for_order(data, platform, order_number, reply, now):
    """支付订单
    检查支付是否有效，完成购买行为
    获得元宝，物品
    如果购买月卡，更新月卡信息
    Args:
        platform[int]: 充值平台
        id[int]: 商品 id
        reply[string]: 支付响应
        now[int]: 当前时间戳
    Returns:
        (ret, update_paycard, items)
        (是否成功, 是否更新了月卡, 获得的物品)
    """
    update_paycard = False
    items = []

    #如果充值已完成（这次是重复的请求） 返回充值内容
    record = _get_record_by_order_number(data, order_number)
    if record is not None and record.is_finish:
        order = PayPool().get(record.order_id)
        if order.cardType != 0:
            update_paycard = True
        for index in range(0, len(order.itemsBasicId)):
            items.append((order.itemsBasicId[index], order.itemsNum[index]))
        return (True, update_paycard, items)

    #获取完成的充值，获得对应的商品信息
    infos = PayLogic().check_order_reply(
            data.id, platform, order_number, reply, now)
    if infos is None or len(infos) == 0:
        #临时解决，合服之后多个server_id存在一个服里
        infos = PayLogic().check_order_reply(
            data.id, platform, order_number, reply, now, data.id / 10000000)
        if infos is None or len(infos) == 0:
            logger.warning("No finished order")
            return (False, update_paycard, items)

    #更新商店信息
    pay = data.pay.get()
    for (order, order_number) in infos:
        pay.pay_order(order)
        if order.cardType != 0:
            #更新月卡
            pay.add_card(order.cardType, now)
            update_paycard = True

        if order.id == 10110200:
            #特殊处理,针对一元购的
            trainer = data.trainer.get()
            trainer.add_buy_daily_discount(1)

    #更新充值记录
    for (order, order_number) in infos:
        record = _get_record_by_order_number(data, order_number)
        if record is not None:
            record.finish(order)
        else:
            logger.debug("Record not found[order_number=%s]" % order_number)
            #添加充值记录（完成状态）
            pay.pre_order(order_number)

            record = PayRecordInfo.create(data.id, pay.pay_count, platform, now)
            record.set_detail(order.id, order_number, order.truePrice)
            data.pay_record_list.add(record)
            record.finish(order)

    #获得元宝
    for (order, order_number) in infos:
        resource = data.resource.get()
        original_gold = resource.gold
        resource.gain_gold(order.gold)
        log = log_formater.output_gold(data, order.gold, log_formater.PAY_GOLD,
                "Gain gold from pay", before_gold = original_gold)
        logger.notice(log)

        #更新用户vip
        user = data.user.get()
        user.gain_vip_points(order.truePrice)

        #获得物品
        gain_items = []
        for index in range(0, len(order.itemsBasicId)):
            gain_items.append((order.itemsBasicId[index], order.itemsNum[index]))
            items.append((order.itemsBasicId[index], order.itemsNum[index]))
        item_business.gain_item(data, gain_items, "pay reward", log_formater.PAY_REWARD)

    return (True, update_paycard, items)


def _get_record_by_order_number(data, order_number):
    """根据订单号获取充值记录
    """
    record_id = 0
    for record in data.pay_record_list.get_all(True):
        if record.order_number == order_number:
            record_id = record.id
            break
    if record_id != 0:
        return data.pay_record_list.get(record_id)
    else:
        return None


def patch_order(data, platform, id, order_number, now):
    """修复完成订单
    检查支付是否有效，完成购买行为
    获得元宝，物品
    如果购买月卡，更新月卡信息
    Args:
        platform[int]: 充值平台
        id[int]: 商品 id
        order_number[string]: 支付订单 id: order number
        now[int]: 当前时间戳
    Returns:
        (ret, update_paycard)
        (是否成功, 是否更新了月卡)
    """
    update_paycard = False

    pay = data.pay.get()
    order = pay.patch_order(platform, id, order_number, now)
    if order is None:
        return (False, update_paycard)

    #添加/更新充值记录（已完成）
    update_record_id = 0
    for record in data.pay_record_list.get_all(True):
        if record.order_number == order_number:
            update_record_id = record.id
            break
    if update_record_id == 0:
        record = PayRecordInfo.create(data.id, pay.pay_count, platform, now)
        record.set_detail(order.id, order_number, order.truePrice)
        record.finish()
        data.pay_record_list.add(record)
    else:
        record = data.pay_record_list.get(update_record_id)
        record.finish(order)

    #更新月卡
    if order.cardType != 0:
        if not pay.add_card(order.cardType, now):
            return (False, update_paycard)
        update_paycard = True

    #获得元宝
    resource = data.resource.get()
    original_gold = resource.gold
    resource.gain_gold(order.gold)
    log = log_formater.output_gold(data, order.gold, log_formater.PATCH_PAY_GOLD,
                "Gain gold from patch pay", before_gold = original_gold)
    logger.notice(log)


    #更新用户vip
    user = data.user.get()
    user.gain_vip_points(order.truePrice)

    #获得物品
    items = []
    for index in range(0, len(order.itemsBasicId)):
        items.append((order.itemsBasicId[index], order.itemsNum[index]))

    ret = item_business.gain_item(data, items, "pay reward", log_formater.PAY_REWARD)
    return (ret, update_paycard)


def try_check_all_order(data, now):
    """尝试修复所有漏单
    """
    #尝试修复订单
    unfinish_record = []
    for record in data.pay_record_list.get_all(True):
        if not record.is_finish:
            unfinish_record.append((record.order_id, record.order_number, record.platform))

    for (order_id, order_number, platform) in unfinish_record:
        pay_for_order(data, platform, order_number, "success", now)

    #删除失效订单
    INVALID_DURATION = 86400#1天，超过的未完成订单会被删除
    delete_record_id = []
    for record in data.pay_record_list.get_all(True):
        if now - record.time > INVALID_DURATION and not record.is_finish:
            delete_record_id.append(record.id)

    for record_id in delete_record_id:
        data.pay_record_list.delete(record_id)


def try_finish_order_outside(data, platform, now):
    """尝试修复非游戏内正常渠道的充值
       tips:
         目前只有soha渠道可以这样做，soha不需要order_number，直接一把拿回所有支付数据
    """

    update_paycard = False
    items = []

    #获取完成的充值，获得对应的商品信息
    infos = PayLogic().check_order_reply(
            data.id, platform, None, None, now)
    if infos is None:
        #临时解决，合服之后多个server_id存在一个服里
        infos = PayLogic().check_order_reply(
            data.id, platform, None, None, now, data.id / 10000000)
        if infos is None:
            logger.warning("No finished order")
            return (False, update_paycard, items)
    else:
        logger.notice("Get finished order")

    #更新商店信息
    pay = data.pay.get()
    for (order, order_number) in infos:
        pay.pay_order(order)
        if order.cardType != 0:
            #更新月卡
            pay.add_card(order.cardType, now)
            update_paycard = True

    #更新充值记录
    for (order, order_number) in infos:
        record = _get_record_by_order_number(data, order_number)
        if record is not None:
            record.finish(order)
        else:
            logger.debug("Record not found[order_number=%s]" % order_number)
            #添加充值记录（完成状态）
            pay.pre_order(order_number)

            record = PayRecordInfo.create(data.id, pay.pay_count, platform, now)
            record.set_detail(order.id, order_number, order.truePrice)
            data.pay_record_list.add(record)
            record.finish(order)

    #获得元宝
    for (order, order_number) in infos:
        resource = data.resource.get()
        original_gold = resource.gold
        resource.gain_gold(order.gold)
        log = log_formater.output_gold(data, order.gold, log_formater.CHECK_PAY_GOLD,
                "Gain gold from check pay", before_gold = original_gold)
        logger.notice(log)


        #更新用户vip
        user = data.user.get()
        user.gain_vip_points(order.truePrice)

        #获得物品
        gain_items = []
        for index in range(0, len(order.itemsBasicId)):
            gain_items.append((order.itemsBasicId[index], order.itemsNum[index]))
            items.append((order.itemsBasicId[index], order.itemsNum[index]))
        item_business.gain_item(data, gain_items, "pay reward", log_formater.PAY_REWARD)

    return (True, update_paycard, items)



