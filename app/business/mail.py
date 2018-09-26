#coding:utf8
"""
Created on 2015-09-29
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 邮件相关业务逻辑
"""

import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.mail import MailInfo
from app.data.item import ItemInfo
from app.data.mail import PostofficeInfo
from app.data.node import NodeInfo
from app.business import item as item_business
from app import log_formater


def init_postoffice(data, now):
    postoffice = PostofficeInfo.create(data.id)
    data.postoffice.add(postoffice)

    #_init_welcome_mail(data, now)
    return True


def _init_welcome_mail(data, now):
    welcome_mail_basic_id = 100
    mail = _create(data, welcome_mail_basic_id, now)
    mail.attach_reward(0, 0, 0, [])

    subject = data_loader.ServerDescKeyInfo_dict["welcome_mail_subject"].value.encode("utf-8")
    sender = data_loader.ServerDescKeyInfo_dict["welcome_mail_sender"].value.encode("utf-8")
    content = data_loader.ServerDescKeyInfo_dict["welcome_mail_content"].value.encode("utf-8")

    mail.write(subject, sender, content)
    return mail


def create_node_city_defense_succeed_mail(data, now):
    #TODO 配置化
    mail_basic_id = random.sample([1, 2, 3, 4, 5], 1)[0]
    mail = _create(data, mail_basic_id, now)

    return mail


def create_node_city_defeat_mail(data, now):
    #TODO 配置化
    mail_basic_id = random.sample([6, 7, 8, 9, 10], 1)[0]
    mail = _create(data, mail_basic_id, now)

    return mail


def create_node_resource_defense_succeed_mail(data, now):
    #TODO 配置化
    mail_basic_id = random.sample([11, 12, 13, 14, 15], 1)[0]
    mail = _create(data, mail_basic_id, now)

    return mail


def create_node_resource_defeat_mail(data, now):
    #TODO 配置化
    mail_basic_id = random.sample([16, 17, 18, 19, 20], 1)[0]
    mail = _create(data, mail_basic_id, now)

    return mail


def create_exploitation_mail(data, node_basic_id, now):
    """创建采集邮件
    邮件附件包括：
        node id、获得金钱、获得粮草、获得元宝、获得物品
    """
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    node = data.node_list.get(node_id, True)

    #TODO 配置化
    if node.is_exploit_money():
        mail_basic_id = 21
    elif node.is_exploit_food():
        mail_basic_id = 22
    elif node.is_exploit_gold():
        mail_basic_id = 24
    elif node.is_exploit_material():
        mail_basic_id = 23
    elif node.is_exploit_random_item():
        mail_basic_id = 50
    elif node.is_exploit_enchant_material():
        mail_basic_id = 51
    elif node.is_exploit_hero_star_soul():
        mail_basic_id = 52

    mail = _create(data, mail_basic_id, now)

    exploitation = data.exploitation.get(True)
    if node.is_exploit_random_item():
        mail.attach_node_offline_exploitation(
                exploitation.search_level,
                exploitation.get_search_progress())
    elif node.is_exploit_enchant_material():
        mail.attach_node_offline_exploitation(
                exploitation.deep_mining_level,
                exploitation.get_deep_mining_progress())
    elif node.is_exploit_hero_star_soul():
        mail.attach_node_offline_exploitation(
                exploitation.hermit_level,
                exploitation.get_hermit_progress())

    return mail


def create_appoint_mail(data, node_basic_id, now):
    """创建委任邮件
    """
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    node = data.node_list.get(node_id, True)

    battle = data.battle_list.get(node_id)

    #TODO 配置化
    if battle.appoint_result:
        if node.is_key_node():
            mail_basic_id = random.sample([25, 26, 27, 28, 29], 1)[0]
        else:
            mail_basic_id = random.sample([35, 36, 37, 38, 39], 1)[0]
    else:
        if node.is_key_node():
            mail_basic_id = random.sample([30, 31, 32, 33, 34], 1)[0]
        else:
            mail_basic_id = random.sample([40, 41, 42, 43, 44], 1)[0]

    mail = _create(data, mail_basic_id, now)

    return mail


def create_legendcity_award_mail(data, now):
    """创建史实城奖励结算邮件
    """
    mail_basic_id = 104
    mail = _create(data, mail_basic_id, now)
    return mail


def create_arena_reward_mail(data, now):
    """创建竞技场结算奖励邮件
    """
    mail_basic_id = 102
    mail = _create(data, mail_basic_id, now)
    return mail


def create_arena_upgrade_reward_mail(data, now):
    """创建演武场升段位奖励邮件
    """
    mail_basic_id = 103
    mail = _create(data, mail_basic_id, now)
    return mail


def create_melee_reward_mail(data, now):
    """创建乱斗场结算奖励邮件
    """
    mail_basic_id = 104
    mail = _create(data, mail_basic_id, now)
    return mail


def create_melee_upgrade_reward_mail(data, now):
    """创建乱斗场升段位奖励邮件
    """
    mail_basic_id = 105
    mail = _create(data, mail_basic_id, now)
    return mail


def create_own_defence_mail(data, now):
    """创建主城防守成功邮件
    """
    mail_basic_id = 45
    mail = _create(data, mail_basic_id, now)
    return mail


def create_union_mail(data, content, now):
    """创建联盟通知邮件
    """
    mail_basic_id = 100
    mail = _create(data, mail_basic_id, now)
    mail.write(
            data_loader.ServerDescKeyInfo_dict["union_notice"].value.encode("utf-8"),
            data_loader.ServerDescKeyInfo_dict["union_sender"].value.encode("utf-8"),
            content)
    return mail


def create_legendcity_defense_mail(data, is_win, now):
    """创建史实城防守结局的邮件
    """
    if is_win:
        mail_basic_id = 61
    else:
        mail_basic_id = 60

    mail = _create(data, mail_basic_id, now)
    return mail


def create_custom_mail(data, message, now):
    custom_mail_basic_id = 100
    if message.HasField("basic_id"):
        custom_mail_basic_id = message.basic_id

    mail = _create(data, custom_mail_basic_id, now)

    if (message.HasField("subject") and
            message.HasField("sender") and
            message.HasField("content")):
        mail.write(message.subject, message.sender, message.content)

    reward_money = 0
    reward_food = 0
    reward_gold = 0
    reward_items = []
    if message.HasField("reward_resource"):
        reward_money = message.reward_resource.money
        reward_food = message.reward_resource.food
        reward_gold = message.reward_resource.gold
    for info in message.reward_items:
        reward_items.append((info.basic_id, info.num))
    mail.attach_reward(reward_money, reward_food, reward_gold, reward_items)

    lost_money = 0
    lost_food = 0
    lost_gold = 0
    lost_soldier = 0
    lost_items = []
    if message.HasField("lost_resource"):
        lost_money = message.lost_resource.money
        lost_food = message.lost_resource.food
        lost_gold = message.lost_resource.gold
        lost_soldier = message.lost_resource.soldier
    for info in message.lost_items:
        lost_items.append((info.basic_id, info.num))
    mail.attach_lost(lost_money, lost_food, lost_gold, lost_soldier, lost_items)

    if message.HasField("node_id") and message.HasField("exploitation_type"):
        mail.attach_node_detail(message.node_id, message.exploitation_type)

    if message.HasField("battle_win"):
        mail.attach_battle_info(message.battle_win)

    if (message.HasField("enemy_user_id") and
            message.HasField("enemy_type") and
            message.HasField("enemy_name")):
        mail.attach_enemy_detail(
                message.enemy_name, message.enemy_user_id, message.enemy_type)

    return mail


def _create(data, basic_id, now):
    """创建邮件
    """
    postoffice = data.postoffice.get()
    type = MailInfo.get_type_by_basic_id(basic_id)
    count = postoffice.get_mail_count(type)

    limit = 25 #TODO 每个类型的邮件，最多50封
    if count >= limit:
        _delete_earliest_mail(data, type, now)

    mail = postoffice.create_mail(basic_id, now)
    try:
        data.mail_list.add(mail)
    except:
        pass
    logger.debug("create mail[mail id=%d][current count=%s]" %
            (mail.id, postoffice.count))
    return mail


def _delete_earliest_mail(data, type, now):
    delete_mail = None
    time = now

    for mail in data.mail_list.get_all(True):
        if mail.type != type:
            continue

        if delete_mail is None:
            delete_mail = mail
            continue

        #删除更早创建的邮件
        if mail.time < delete_mail.time:
            delete_mail = mail
            continue

        #如果是同时创建的邮件，删除 id 更靠前的邮件
        if mail.id < delete_mail.id:
            delete_mail = mail

    if delete_mail != None:
        logger.debug("delete earliest mail[mail id=%d]" % delete_mail.id)
        _delete_mail(data, delete_mail)


def delete_mails_on_demand(data, now):
    """删除需要删除的邮件
    """
    delete_mails = []
    for mail in data.mail_list.get_all(True):
        if mail.is_need_delete(now):
            delete_mails.append(mail)

    for mail in delete_mails:
        _delete_mail(data, mail)


def _delete_mail(data, mail):
    """删除邮件
    """
    postoffice = data.postoffice.get()
    postoffice.delete_mail(mail.type)
    data.mail_list.delete(mail.id)

    logger.debug("delete mail[mail id=%d][current count=%s]" %
            (mail.id, postoffice.count))


def read(data, mail_indexs, now):
    """阅读邮件
    """
    for mail_index in mail_indexs:
        mail_id = MailInfo.generate_id(data.id, mail_index)
        mail = data.mail_list.get(mail_id)
        if not mail.read():
            return False

    return True


def use_mail_to_get_reward(data, mail_indexs, now):
    """
    使用邮件
    1 可能会获取资源和物品奖励
    2 标记邮件状态为已读
    3 确定邮件是否需要删除
    """
    for mail_index in mail_indexs:
        mail_id = MailInfo.generate_id(data.id, mail_index)
        mail = data.mail_list.get(mail_id)

        assert mail.is_system_mail()

        #可以领取奖励
        resource = data.resource.get()
        original_gold = resource.gold
        reward_gold = mail.reward_gold
        resource.update_current_resource(now)
        resource.gain_money(mail.reward_money)
        resource.gain_food(mail.reward_food)
        resource.gain_gold(reward_gold)
        log = log_formater.output_gold(data, reward_gold, log_formater.MAIL_REWARD_GOLD,
                "Gain gold from mail", before_gold = original_gold)
        logger.notice(log)

        new_items = mail.get_reward_items()
        if not item_business.gain_item(data, new_items, "mail reward", log_formater.MAIL_REWARD):
            return False

        if not mail.use():
            return False

        if mail.is_need_delete(now):
            _delete_mail(data, mail)

    return True


def use_mail_to_get_rival(data, mail_index):
    """使用邮件，获取入侵的敌人信息
    然后根据敌人信息进行复仇战
    这里并不使用邮件
    """
    mail_id = MailInfo.generate_id(data.id, mail_index)
    mail = data.mail_list.get(mail_id, True)

    assert mail.is_battle_mail()

    if mail.is_used():
        logger.warning("Mail is used")
        return 0

    return mail.related_enemy_user_id


def use_mail_to_revenge_succeed(data, mail, now):
    """使用邮件成功复仇
    使用邮件
    """
    assert mail.is_battle_mail()

    if not mail.use():
        return False

    if mail.is_need_delete(now):
        _delete_mail(data, mail)

    return True

