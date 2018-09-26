#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
"""

from firefly.server.globalobject import GlobalObject
from firefly.server.globalobject import remoteserviceHandle
from utils import logger
from portal.online_manager import OnlineManager
from portal.command_table import CommandTable


@remoteserviceHandle('app')
def push_mail(user_id, msg):
    """向用户推送邮件
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 邮件内容
    """
    session_id = OnlineManager().get_user_session_id(user_id)

    #如果用户不在线，则不推送
    if session_id == -1:
        logger.debug("User is offline[user id=%d]" % user_id)
        return
    else:
        logger.debug("User is online[user id=%d]" % user_id)

    command_id = CommandTable().commands["push_mail"]

    user_list = []
    user_list.append(session_id)

    logger.debug("all len:%d" % len(user_list))
    for u in user_list:
        logger.debug("session:%s" % str(u))

    GlobalObject().netfactory.pushObject(command_id, msg, user_list)
    logger.debug("push mail to user[user id=%d][session id=%d][command id=%d]" %
            (user_id, session_id, command_id))


@remoteserviceHandle('app')
def forward_mail(user_id, msg):
    """向用户转发邮件
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 邮件内容
    """
    defer = GlobalObject().remote['app'].callRemote("receive_mail", user_id, msg)
    logger.notice("forward mail[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_add_honor(user_id, msg):
    """转发添加联盟荣誉请求
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 请求内容
    """
    defer = GlobalObject().remote['app'].callRemote("add_union_honor", user_id, msg)
    logger.debug("forward add honor[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_chat_operation(user_id, msg):
    """向用户转发聊天管理命令
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 聊天管理
    """
    defer = GlobalObject().remote['app'].callRemote("receive_chat_operation", user_id, msg)
    logger.debug("forward chat operation[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_battle_notice(user_id, msg):
    """向用户转发战斗结果
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 内容
    """
    defer = GlobalObject().remote['app'].callRemote("receive_battle_notice", user_id, msg)
    logger.debug("forward battle notice[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_legendcity_battle_notice(user_id, msg):
    """向用户转发史实城战斗结果
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 内容
    """
    defer = GlobalObject().remote['app'].callRemote(
            "receive_legendcity_battle_notice", user_id, msg)
    logger.debug("forward legendcity battle notice[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_activity_invitation(user_id, msg):
    """向用户转发活动邀请
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 活动内容
    """
    defer = GlobalObject().remote['app'].callRemote(
            "receive_activity_invitation", user_id, msg)
    logger.debug("forward activity invitation[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_arena_notice(user_id, msg):
    """向用户转发演武场战斗结果
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 内容
    """
    defer = GlobalObject().remote['app'].callRemote("receive_arena_notice", user_id, msg)
    logger.debug("forward arena notice[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def push_arena_record(user_id, msg):
    """向用户推送演武场对战记录
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]:
    """
    session_id = OnlineManager().get_user_session_id(user_id)

    #如果用户不在线，则不推送
    if session_id == -1:
        logger.debug("User is offline[user id=%d]" % user_id)
        return
    else:
        logger.debug("User is online[user id=%d]" % user_id)

    command_id = CommandTable().commands["push_arena_record"]

    user_list = []
    user_list.append(session_id)

    logger.debug("all len:%d" % len(user_list))
    for u in user_list:
        logger.debug("session:%s" % str(u))

    GlobalObject().netfactory.pushObject(command_id, msg, user_list)
    logger.debug("push arena record to user[user id=%d][session id=%d][command id=%d]" %
            (user_id, session_id, command_id))


@remoteserviceHandle('app')
def forward_melee_notice(user_id, msg):
    """向用户转发乱斗场战斗结果
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 内容
    """
    defer = GlobalObject().remote['app'].callRemote("receive_melee_notice", user_id, msg)
    logger.debug("forward melee notice[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def push_melee_record(user_id, msg):
    """向用户推送乱斗场对战记录
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]:
    """
    session_id = OnlineManager().get_user_session_id(user_id)

    #如果用户不在线，则不推送
    if session_id == -1:
        logger.debug("User is offline[user id=%d]" % user_id)
        return
    else:
        logger.debug("User is online[user id=%d]" % user_id)

    command_id = CommandTable().commands["push_melee_record"]

    user_list = []
    user_list.append(session_id)

    logger.debug("all len:%d" % len(user_list))
    for u in user_list:
        logger.debug("session:%s" % str(u))

    GlobalObject().netfactory.pushObject(command_id, msg, user_list)
    logger.debug("push melee record to user[user id=%d][session id=%d][command id=%d]" %
            (user_id, session_id, command_id))


@remoteserviceHandle('app')
def forward_update_arena_offline(user_id, msg):
    """向用户转发离线更新演武场的请求
    Args:
        user_id[int]: 用户 id
    """
    defer = GlobalObject().remote['app'].callRemote("receive_update_arena_offline", user_id, msg)
    logger.debug("forward update arena offline[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_clear_activity_hero_scores(user_id, msg):
    """向用户转发清空拍卖英雄活动积分的请求
    Args:
        user_id[int]: 用户 id
    """
    defer = GlobalObject().remote['app'].callRemote("receive_clear_activity_hero_scores", user_id, msg)
    logger.debug("forward clear activity hero scores[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_union_battle_deploy_force(user_id, msg):
    """向用户转发部署强制联盟战的请求
    Args:
        user_id[int]: 用户 id
    """
    defer = GlobalObject().remote['app'].callRemote("receive_deploy_union_battle_force", user_id, msg)
    logger.debug("receive union battle deploy force[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_union_battle_season_forward(user_id, msg):
    """向用户转发进入下一个联盟战争赛季的请求
    Args:
        user_id[int]: 用户 id
    """
    defer = GlobalObject().remote['app'].callRemote("forward_union_battle_season", user_id, msg)
    logger.debug("forward union battle season[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_refresh_all_teams(user_id, msg):
    """向用户转发更新所有team的请求
    Args:
        user_id[int]: 用户 id
    """
    defer = GlobalObject().remote['app'].callRemote("receive_refresh_all_teams", user_id, msg)
    logger.debug("forward refresh all teams[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_clear_worldboss_merit(user_id, msg):
    """向用户转发清空世界boss战功的请求
    Args:
        user_id[int]: 用户 id
    """
    defer = GlobalObject().remote['app'].callRemote("receive_clear_worldboss_merit", user_id, msg)
    logger.debug("forward clear worldboss merit[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_delete(user_id, msg):
    """转发删除用户的请求
    """
    defer = GlobalObject().remote['app'].callRemote("user_delete", user_id, msg)
    logger.debug("forward delete user[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_update_user_info_offline(user_id, msg):
    """转发用户离线更新数据的请求
    """
    defer = GlobalObject().remote['app'].callRemote("receive_update_user_info_offline", user_id, msg)
    logger.debug("forward update_user_info_offline[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_recalc_resource(user_id, msg):
    """转发重算资源请求"""
    defer = GlobalObject().remote['app'].callRemote("recalc_resource", user_id, msg)
    logger.debug("forward recalc resource user[to user id=%d]" % user_id)
    return defer

@remoteserviceHandle('app')
def forward_transfer_notice(user_id, msg):
    """转发换位演武场通知"""
    defer = GlobalObject().remote['app'].callRemote("receive_transfer_notice", user_id, msg)
    logger.debug("forward transfer notice[to user id=%d]" % user_id)
    return defer

@remoteserviceHandle('app')
def push_transfer_record(user_id, msg):
    """向用户推送换位演武场对战记录"""
    session_id = OnlineManager().get_user_session_id(user_id)

    #如果用户不在线，则不推送
    if session_id == -1:
        logger.debug("User is offline[user id=%d]" % user_id)
        return
    else:
        logger.debug("User is online[user id=%d]" % user_id)

    command_id = CommandTable().commands["push_transfer_record"]

    user_list = []
    user_list.append(session_id)

    logger.debug("all len:%d" % len(user_list))
    for u in user_list:
        logger.debug("session:%s" % str(u))

    GlobalObject().netfactory.pushObject(command_id, msg, user_list)
    logger.notice("push transfer record to user[user id=%d][session id=%d][command id=%d]" %
            (user_id, session_id, command_id))


@remoteserviceHandle('app')
def forward_be_invited(user_id, msg):
    """向用户转发来自被邀请者的请求
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 内容
    """
    defer = GlobalObject().remote['app'].callRemote("receive_from_invitee", user_id, msg)
    logger.debug("forward be invited notice[to user id=%d]" % user_id)
    return defer


@remoteserviceHandle('app')
def forward_invitee_upgrade(user_id, msg):
    """向邀请者转发被邀请者的升级请求
    Args:
        user_id[int]: 用户 id
        msg[string(protobuf)]: 内容
    """
    defer = GlobalObject().remote['app'].callRemote("receive_invitee_upgrade", user_id, msg)
    logger.debug("forward invitee upgrade notice[to user id=%d]" % user_id)
    return defer




