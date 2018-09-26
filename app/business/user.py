#coding:utf8
"""
Created on 2015-09-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 帐号相关业务逻辑
"""

import random
from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from datalib.data_loader import data_loader
from app.data.resource import ResourceInfo
from app.data.user import UserInfo
from app.data.node import NodeInfo
from app.data.guard import GuardInfo
from app.core.name import NameGenerator
from proto import user_pb2
from app import log_formater


def init_user(data, user_id, pattern, now):
    """创建用户基础信息
    """
    user = UserInfo.create(user_id, now)
    icon_id = random.sample(data_loader.InitUserBasicInfo_dict[pattern].userIconId, 1)[0]
    name = NameGenerator().gen()

    if not user.change_name(name):
        return False
    if not user.change_icon(icon_id):
        return False

    #更新用户登录信息
    user.login(now)

    data.user.add(user)
    return True


def init_resource(data, pattern, now):
    """用户创建帐号时的初始资源信息
    Args:
        data[UserData]: 用户数据
        pattern[int]: 初始化模式
        now[int]: 当前时间戳
    Returns:
        resource[ResourceInfo]
    """
    user = data.user.get()

    #初始化金钱、粮草、元宝情况
    resource = ResourceInfo.create(user.id, user.vip_level, now)
    original_gold = resource.gold
    gold = data_loader.InitUserBasicInfo_dict[pattern].gold
    resource.gain_money(data_loader.InitUserBasicInfo_dict[pattern].money, True)
    resource.gain_food(data_loader.InitUserBasicInfo_dict[pattern].food, True)
    resource.gain_gold(gold)
    data.resource.add(resource)
    
    #log = log_formater.output_gold(data, gold, log_formater.INIT_RESOURCE_GOLD,
    #            "Gain gold from init resource", before_gold = original_gold)
    #logger.notice(log)

    return True


def level_upgrade(data, exp, now, str, type):
    """用户升级
    用户升级渠道：
    1 战斗胜利
    2 完成建筑的建造和升级
    Returns:
        True/False: 升级是否成功 
    """
    user = data.user.get()
    pay = data.pay.get(True)
    resource = data.resource.get(True)
    old_level = user.level
    if not user.level_up(exp, str, type):
	#log = log_formater.output_exp(data, str, type, exp, oldlevel, data_loader.MonarchLevelBasicInfo_dict[old_level+1].exp)
	#logger.notice(log)
        return True #由于主公经验已满导致的升级失败，也返回True
    else:
        if old_level != user.level:
           # logger.notice("Submit Role[user_id=%d][level=%d][name=%s][status=LEVELUP]"
           #        % (user.id, user.level, user.name))
	     
             logger.notice("Submit Role[user_id=%d][level=%d][name=%s][vip=%d][status=LEVELUP][create_time=%d][last_login_time=%d][money=%d][food=%d][gold=%d][pay_count=%d][pay_amount=%.2f]"
                % (user.id, user.level, user.name, user.vip_level, user.create_time, user.last_login_time, resource.money, resource.food, resource.gold, pay.pay_count, pay.pay_amount))
        new_level = user.level

        return _post_upgrade(data, user, old_level, new_level, now)


def _post_upgrade(data, user, old_level, new_level, now):
    """用户升级后的处理
    1 可能解锁 PVP
    2 可能解锁 pvp arena
    3 升级世界地图上己方主城的等级
    4 增加政令值
    5 想邀请者转发升级通知
    """
    if not check_pvp_authority(data):
        return False
    if not check_arena_authority(data, now):
        return False
    if not check_worldboss_authority(data):
        return False

    own_basic_id = NodeInfo.get_own_node_basic_id()
    own_id = NodeInfo.generate_id(data.id, own_basic_id)
    own = data.node_list.get(own_id)
    own.update_own_city_level(user.level)

    energy = data.energy.get()
    level_diff = new_level - old_level
    diff = 1
    while diff <= level_diff:
        energy.update_energy_and_capacity(old_level + diff)
        diff += 1

    if user.is_invited():
        _forward_invitee_upgrade(data, user)

    return True


def _forward_invitee_upgrade(data, user):
    """转发升级通知给邀请者
    """
    forward_req = user_pb2.InviteReq()
    forward_req.invitee_id = user.id
    forward_req.invitee_level = user.level
    forward_request = forward_req.SerializeToString()
 
    defer = GlobalObject().root.callChild(
            'portal', "forward_invitee_upgrade", user.inviter, forward_request)
    defer.addCallback(_check_forward_invitee_upgrade_result, data)
    return defer


def _check_forward_invitee_upgrade_result(response, data):
    res = user_pb2.InviteRes()
    res.ParseFromString(response)

    if res.status != 0:
        logger.warning("Forward invitee upgrade result failed")
        #raise Exception("Forward invitee upgrade result failed")

    return DataBase().commit(data)


def check_worldboss_authority(data):
    """检查用户是否能够参加世界boss
    """
    user = data.user.get()
    worldboss = data.worldboss.get()
    if not worldboss.is_unlock():
        limit_level = int(float(data_loader.OtherBasicInfo_dict["unlock_worldboss_level"].value))
        if limit_level <= user.level:
            worldboss.unlock()
    
    return True


def check_arena_authority(data, now):
    """检查用户是否能够参加演武场
    """
    user = data.user.get()
    if not user.allow_pvp: #pvp不解锁，演武场也不会开启
        return True
    if user.allow_pvp_arena:
        return True

    limit_level = int(float(data_loader.OtherBasicInfo_dict["ArenaLimitMonarchLevel"].value))
    from app.business.building import is_unlock_citydefence
    if  user.level >= limit_level and is_unlock_citydefence(data):
        user.unlock_pvp_arena()
        #更新轮次
        arena = data.arena.get()
        arena.update_round(now)

    return True


def check_pvp_authority(data):
    """检查用户是否能够进行 PVP
    Returns:
        True/False: 操作是否成功
    """
    logger.debug("Check pvp authority")
    user = data.user.get()
    if user.allow_pvp:
        return True

    ##如果未开启 PVP，尝试开启
    #for building in data.building_list.get_all(True):
    #    if building.is_mansion():
    #        mansion = building
    #    elif building.is_defense():
    #        defense = building

    ##城防建筑活跃，则开启 PVP
    #if defense.is_active(user.level, mansion.level):
    #    user.unlock_pvp()
    #    return _init_guard(data, defense)

    defense = None
    for building in data.building_list.get_all(True):
        if building.is_defense():
            defense = building
    #主公等级满足要求，开启pvp
    if user.level >= int(float(data_loader.OtherBasicInfo_dict["guard_limit_monarch_level"].value)):
        user.unlock_pvp()
        return _init_guard(data, defense)

    return True


def _init_guard(data, building):
    """
    创建防守阵容: 用于 PVP 对战和匹配
    1 使用当前最强的 x 支队伍 - 对战（防守）
    2 记录当前的 top 阵容 - 匹配
    Args:
        data[UserData]: 用户数据
        building[BuildingInfo]: 城防建筑
    """
    if building is not None:
        defense = data.defense_list.get(building.id, True)
        defense_id = defense.building_id
    else:
        defense_id = 0

    guard = GuardInfo.create(data.id, defense_id)
    data.guard_list.add(guard)

    user = data.user.get(True)
    teams = data.team_list.get_all(True)
    guard.update_team(teams, user.team_count)

    all_hero = data.hero_list.get_all(True)
    guard.try_update_top_score(all_hero, user.team_count)

    logger.debug("Unlock pvp")
    return True

