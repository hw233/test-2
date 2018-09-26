#coding:utf8
"""
Created on 2016-06-25
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟成员管理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.chat_pool import ChatPool
from utils.chat import ChatRoomDecapitator
from datalib.data_loader import data_loader
from gunion.data.member import UnionMemberInfo
from gunion.data.aid import UnionAidInfo
from gunion.data.application import UnionApplicationInfo
from gunion.data.battle import UnionBattleInfo


def find_member(data, user_id):
    """查询联盟中玩家
    """
    member_id = UnionMemberInfo.generate_id(data.id, user_id)
    member = data.member_list.get(member_id)
    return member


def is_able_to_join(data, user_level):
    """联盟是否可以加入
    """
    union = data.union.get()
    if union.is_member_full():
        return False

    if user_level < union.join_level_limit:
        return False

    return True


def join_union(data, user_id, now, force = False):
    """加入联盟
    Args:
        force[bool]: 是否强制加入，可以无视加入状态
    """
    union = data.union.get()

    if not force and union.join_status == union.JOIN_STATUS_DISABLE:
        logger.warning("Union disable join")
        return False

    #添加成员
    if not union.add_member():
        return False

    member = UnionMemberInfo.create(data.id, user_id, now)
    data.member_list.add(member)

    #更新联盟战争情况
    season = data.season.get()
    battle_id = UnionBattleInfo.generate_id(data.id, season.current_battle_index)
    battle = data.battle_list.get(battle_id, True)
    season.update_join_battle_status(union.current_number, battle.is_able_to_join())
    return True


def leave_union(data, member):
    """离开联盟
    消除影响：援助，职务
    """
    union = data.union.get()

    #删除对应的援助信息
    aid_id = UnionAidInfo.generate_id(data.id, member.user_id)
    aid = data.aid_list.get(aid_id)
    if aid is not None:
        data.aid_list.delete(aid.id)

    #如果是副盟主，解除职务
    if member.is_vice_leader():
        union.clear_vice_leader(member.user_id)

    #删除用户
    union.remove_member()
    data.member_list.delete(member.id)

    #从聊天室中踢出
    _kickfrom_union_chatroom(union, member)

    #更新联盟战争情况
    season = data.season.get()
    battle_id = UnionBattleInfo.generate_id(data.id, season.current_battle_index)
    battle = data.battle_list.get(battle_id, True)
    season.update_join_battle_status(union.current_number, battle.is_able_to_join())

    #如果正在备战阶段，取消该成员所有驻防
    if battle.is_able_to_deploy():
        for node in data.battle_node_list.get_all():
            if node.defender_user_id == member.user_id:
                node.cancel_deploy()


def _kickfrom_union_chatroom(union, target_member):
    """从联盟聊天室中踢出
    """
    info = ChatPool().get_union_chat_info()

    #从聊天室中踢出
    jid = info.get_jid(ChatPool().admin_username)
    target_nickname = str(target_member.user_id) #用玩家的 user id（和客户端约定）
    agent = ChatRoomDecapitator(
            jid, ChatPool().admin_password, union.chatroom, union.chatpasswd, target_nickname)
    agent.connect()
    agent.process()
    logger.debug("Kick from union chatroom[name=%s][passwd=%s][target user id=%d]" %
            (union.chatroom, union.chatpasswd, target_member.user_id))


def promotion_to_vice_leader(data, target_member):
    """提升为副盟主
    """
    if target_member.is_vice_leader():
        logger.warning("Target member is vice leader now[user_id=%d]" %
                target_member.user_id)
        return True

    union = data.union.get()
    if not union.set_as_vice_leader(target_member.user_id):
        return False

    target_member.set_as_vice_leader()
    return True


def demotion_to_member(data, target_member):
    """降职为普通成员
    """
    if target_member.is_normal_member():
        logger.warning("Target member is normal member now[user_id=%d]" %
                target_member.user_id)
        return True

    union = data.union.get()
    if not union.clear_vice_leader(target_member.user_id):
        return False

    target_member.set_as_normal_member()
    return True


def demise_leader(data, leader, target_member):
    """转让盟主职位
    """
    union = data.union.get()

    if target_member.is_vice_leader():
        union.clear_vice_leader(target_member.user_id)
    union.set_as_leader(target_member.user_id)
    target_member.set_as_leader()

    leader.set_as_normal_member()


def add_application(data, user_id, name, icon, level, battle_score, now):
    """添加申请
    """
    application_id = UnionApplicationInfo.generate_id(data.id, user_id)
    application = data.application_list.get(application_id)
    if application is None:
        #删除一些过旧的申请
        max_num = int(float(data_loader.UnionConfInfo_dict["application_max_num"].value))
        if len(data.application_list) >= max_num:
            _delete_oldest_application(
                    data, len(data.application_list) - max_num + 1, now)

        application = UnionApplicationInfo.create(data.id, user_id)
        data.application_list.add(application)

    application.set_detail(name, icon, level, battle_score, now)


def find_application(data, user_id, now):
    """查找申请
    """
    application_id = UnionApplicationInfo.generate_id(data.id, user_id)
    application = data.application_list.get(application_id)
    if application is None:
        return None
    if not application.is_available(now):
        data.application_list.delete(application.id)
        return None
    return application


def agree_application(data, application, now):
    """同意申请
    玩家加入联盟（不在乎当前的联盟状态）
    删除申请
    """
    user_id = application.user_id
    assert join_union(data, user_id, now, force = True)

    logger.debug("Agree application[user_id=%d]" % user_id)
    data.application_list.delete(application.id)


def disagree_application(data, application):
    """拒绝申请
    删除申请
    """
    logger.debug("Disagree application[user_id=%d]" % application.user_id)
    data.application_list.delete(application.id)


def delete_not_available_application(data, now):
    """删除过期的申请
    """
    to_delete = []
    for application in data.application_list.get_all(True):
        if not application.is_available(now):
            to_delete.append(application.id)

    for application_id in to_delete:
        data.application_list.delete(application_id)


def _delete_oldest_application(data, num, now):
    """删除最旧的申请
    """
    to_delete = []
    for application in data.application_list.get_all(True):
        if len(to_delete) < num:
            to_delete.append(application)
            to_delete = sorted(to_delete, key = lambda a:a.time)
        elif application.time < to_delete[-1].time:
            to_delete.pop()
            to_delete.append(application)
            to_delete = sorted(to_delete, key = lambda a:a.time)

    for application in to_delete:
        data.application_list.delete(application.id)


