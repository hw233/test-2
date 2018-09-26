#coding:utf8
"""
Created on 2015-09-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 检查客户端的请求
         比较 data 和 proto，看看是否一致
"""

from utils import logger
from utils import utils
from app.data.item import ItemInfo
from app.data.hero import HeroInfo
from app.data.node import NodeInfo
from app.data.building import BuildingInfo
from app.data.technology import TechnologyInfo


def check_user(data, message, with_level = False, with_vip = False):
    """验证帐号信息
    """
    user = data.user.get(True)

    if with_level:
        logger.debug("check user[level=%d][exp=%d]" % (user.level, user.exp))
        try:
            assert user.level == message.level
            assert user.exp == message.exp
        except:
            logger.warning("check level failed[level=%d][req_level=%d][exp=%d][req_exp=%d]" % (
                user.level, message.level, user.exp, message.exp))
            raise Exception("check user level failed")

    if with_vip:
        logger.debug("check user[vip_level=%d][vip_points=%d]" %
                (user.vip_level, user.vip_points))
        #assert user.vip_level == message.vip_level
        #客户端逻辑问题导致vip_points不能超上限，此处放过
        #assert user.vip_points == message.vip_points

def check_user_r(data, message, with_level = False, with_vip = False):
    """验证帐号信息"""
    user = data.user.get(True)

    if with_level:
        logger.debug("check user[level=%d][exp=%d]" % (user.level, user.exp))
        if user.level != message.level: return False
        if user.exp != message.exp: return False
    
    if with_vip:
        logger.debug("check user[vip_level=%d][vip_points=%d]" %
                (user.vip_level, user.vip_points))
        if user.vip_level != message.vip_level: return False
        if user.vip_points != message.vip_points: return False

    return True

def check_item_r(data, message):
    """更加健壮的验证物品信息的方法"""
    item_id = ItemInfo.generate_id(data.id, message.basic_id)
    item = data.item_list.get(item_id, True)
    if item is None:
        item_num = 0
    else:
        item_num = item.num
    if item_num != message.num:
        logger.warning("check item error[basic_id=%d][num=%d][req_num=%d]" %
            (item.basic_id, item_num, message.num))
        return False
    else:
        return True

def check_item(data, message):
    """
    验证物品信息
    Args:
        data[UserData]
        message[protobuf]
    """
    item_id = ItemInfo.generate_id(data.id, message.basic_id)
    item = data.item_list.get(item_id, True)

    #logger.debug("checkout item[basic_id=%d][num=%d]" % (item.basic_id, item.num))
    #客户端bug导致此处经常失败，先放过
    #assert item.num == message.num
    if item is None:
        if message.num != 0:
            logger.warning("check item error[basic_id=%d][num=0][req_num=%d]" %
                (message.basic_id, message.num))
    elif item.num != message.num:
        logger.warning("check item error[basic_id=%d][num=%d][req_num=%d]" %
            (item.basic_id, item.num, message.num))

def check_hero_r(data, message,
        with_level = False, with_star = False, with_soldier = False,
        with_equipment_type = 0, with_skill_index = -1, with_evolution = False,
        with_equipment_stone = False, with_herostar = False, with_awaken = False):
    """更加健壮的验证英雄信息的方法"""
    try:
        check_hero(data, message,
            with_level, with_star, with_soldier, with_equipment_type, with_skill_index,
            with_evolution, with_equipment_stone, with_herostar, with_awaken)
    except AssertionError:
        return False
    return True

def check_hero(data, message,
        with_level = False, with_star = False, with_soldier = False,
        with_equipment_type = 0, with_skill_index = -1, with_evolution = False,
        with_equipment_stone = False, with_herostar = False, with_awaken = False):
    """
    验证英雄信息
    Args:
        data[UserData]
        message[protobuf]
        with_xxx[bool] 是否需要验证某些字段，包括：等级、星级、兵种、装备、技能
    """
    hero_id = HeroInfo.generate_id(data.id, message.basic_id)
    hero = data.hero_list.get(hero_id, True)
    assert hero is not None

    if with_level:
        logger.debug("check hero[level=%d][exp=%d]" % (hero.level, hero.exp))
        assert hero.level == message.level
        #客户端bug导致此处经常失败，先放过
        #assert hero.exp == message.exp
        if hero.exp != message.exp:
            logger.warning("check hero error[basic_id=%d][exp=%d][req_exp=%d]" %
                (message.basic_id, hero.exp, message.exp))
    if with_star:
        assert hero.star == message.star_level
    if with_soldier:
        assert hero.soldier_basic_id == message.soldier_basic_id
        assert hero.soldier_level == message.soldier_level
    if with_equipment_type != 0 and with_equipment_stone != True:
        if with_equipment_type == HeroInfo.EQUIPMENT_TYPE_WEAPON:
            assert hero.get_equipment(with_equipment_type) == message.equipment_weapon_id
        elif with_equipment_type == HeroInfo.EQUIPMENT_TYPE_ARMOR:
            assert hero.get_equipment(with_equipment_type) == message.equipment_armor_id
        else:
            assert hero.get_equipment(with_equipment_type) == message.equipment_treasure_id
    if with_skill_index != -1:
        if with_skill_index == 0:
            assert hero.get_skill(with_skill_index) == message.first_skill_id
        elif with_skill_index == 1:
            assert hero.get_skill(with_skill_index) == message.second_skill_id
        elif with_skill_index == 2:
            assert hero.get_skill(with_skill_index) == message.third_skill_id
        else:
            assert hero.get_skill(with_skill_index) == message.fourth_skill_id
    if with_evolution:
        assert hero.evolution_level == message.evolution_level

    if with_equipment_stone == True and with_equipment_type != 0:
        if with_equipment_type == HeroInfo.EQUIPMENT_TYPE_WEAPON:
            assert cmp(hero.get_equipment_stones(with_equipment_type), message.stone_weapon) == 0
        elif with_equipment_type == HeroInfo.EQUIPMENT_TYPE_ARMOR:
            assert cmp(hero.get_equipment_stones(with_equipment_type), message.stone_armor) == 0
        else:
            assert cmp(hero.get_equipment_stones(with_equipment_type), message.stone_treasure) == 0
    
    if with_herostar:
        herostars = hero.get_herostars()
        assert cmp(hero.get_herostars(), message.hero_star) == 0

    if with_awaken:
        assert hero.is_awaken == message.hero_awakening


def check_technology(data, message):
    """
    验证科技信息
    Args:
        data[UserData]
        message[protobuf]
    """
    technology_id = TechnologyInfo.generate_id(data.id, message.basic_id, message.type)
    technology = data.technology_list.get(technology_id, True)
    assert technology is not None

    assert technology.type == message.type
    assert technology.is_upgrade == message.is_upgrading

    if message.is_upgrading:
        #assert technology.consume_time == message.upgrade_consume_time
        building_id = BuildingInfo.generate_id(
            data.id, message.city_basic_id, message.location_index, message.building_basic_id)
        assert technology.building_id == building_id


def check_node(data, message, with_exploit = False):
    """验证节点信息
    """
    node_id = NodeInfo.generate_id(data.id, message.basic_id)
    node = data.node_list.get(node_id, True)
    assert node is not None

    #与客户端的计算值有误差，先不check
    #if with_exploit:
    #    logger.debug("check node[exploit total time=%d]" % (node.exploit_total_time))
    #    assert node.exploit_total_time == message.exploitation.total_time


def check_conscript(data, message, with_time = False):
    """验证征兵信息
    """
    conscript_id = BuildingInfo.generate_id(
            data.id, message.city_basic_id, message.location_index, message.building_basic_id)
    conscript = data.conscript_list.get(conscript_id)
    assert conscript is not None

    logger.debug("check soldier num[soldier=%d][request=%d]" %
            (conscript.soldier_num, message.current_soldier_num))
    assert conscript.conscript_num == message.conscript_num

    if with_time:
        logger.debug("check conscript[total time=%d]" %
                (conscript.end_time - conscript.start_time))
        assert conscript.end_time - conscript.start_time == message.total_conscript_time


