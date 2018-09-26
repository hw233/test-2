#coding:utf8
"""
Created on 2016-06-22
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟逻辑
"""

from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.chat_pool import ChatPool
from utils.chat import ChatRoomCreator
from utils.chat import ChatRoomDestroyer
from gunion.data.member import UnionMemberInfo
from gunion.data.union import UnionInfo
from gunion.data.season import UnionSeasonInfo
from gunion.data.battle import UnionBattleInfo
from gunion.season_allocator import SeasonAllocator
from gunion.business import donate as donate_business
from proto import internal_pb2
from utils import utils
from datalib.data_loader import data_loader
import copy
import pdb


def init_union(data, user_id, name, icon, now):
    """初始化联盟
    """
    union_id = data.id

    #初始化联盟
    union = UnionInfo.create(union_id, name, icon, now)
    data.union.add(union)

    #添加成员（创建者）
    if not union.add_member():
        return False
    member = UnionMemberInfo.create(union_id, user_id, now)

    #设为盟主
    union.set_as_leader(user_id)
    member.set_as_leader()

    data.member_list.add(member)

    #建立聊天室
    _create_union_chatroom(union)

    #初始化联盟战斗信息
    (season_index, season_start_time) = SeasonAllocator().allocate(now)
    season = UnionSeasonInfo.create(union_id, season_index, season_start_time)
    battle = UnionBattleInfo.create(
            data.id, season.forward_battle_index(), season.is_near_end(now))
    season.update_join_battle_status(union.current_number, battle.is_able_to_join())
    data.season.add(season)
    data.battle_list.add(battle)

    #初始化联盟捐献宝箱
    for i in range(3):
        donate_box = donate_business.create_new_donate_box(data)
        donate_business.add_donate_box(data, donate_box)

    union.donate_last_auto_time = now

    return True


def _create_union_chatroom(union):
    """创建联盟聊天室
    """
    info = ChatPool().get_union_chat_info()
    union.calc_chatroom(GlobalObject().server_id, info.room, info.service)

    #连接并建立聊天室
    jid = info.get_jid(ChatPool().admin_username)
    agent = ChatRoomCreator(
            jid, ChatPool().admin_password, union.chatroom, union.chatpasswd)
    agent.connect()
    agent.process()
    logger.debug("Create union chatroom[name=%s][passwd=%s]" %
            (union.chatroom, union.chatpasswd))


def update_union(data, member, name, icon_id, need_level, join_status, announcement):
    """更新联盟
    Returns:
        是否成功（是否有权限操作）
    """
    union = data.union.get()

    if name is not None:
        if not member.is_leader():
            return False
        if not union.change_name(name):
            raise Exception("Change name failed")

    if icon_id is not None:
        if not member.is_leader():
            return False
        union.change_icon(icon_id)

    if need_level is not None:
        if not member.is_leader():
            return False
        if not union.change_level_limit(need_level):
            raise Exception("Change level limit failed")

    if join_status is not None:
        if not member.is_leader():
            return False
        if not union.change_join_status(join_status):
            raise Exception("Change join status failed")

    if announcement is not None:
        if not member.is_leader() and not member.is_vice_leader():
            return False
        if not union.change_announcement(announcement):
            raise Exception("Change announcement failed")

    return True


def dismiss_union(data):
    """解散联盟
    """
    union = data.union.get()
    union.dismiss()

    _destroy_union_chatroom(union)


def _destroy_union_chatroom(union):
    """创建联盟聊天室
    """
    info = ChatPool().get_union_chat_info()

    #销毁聊天室
    jid = info.get_jid(ChatPool().admin_username)
    agent = ChatRoomDestroyer(
            jid, ChatPool().admin_password, union.chatroom, union.chatpasswd)
    agent.connect()
    agent.process()
    logger.debug("Destroy union chatroom[name=%s][passwd=%s]" %
            (union.chatroom, union.chatpasswd))

def get_leader(data):
    """获取盟主"""
    member_list = data.member_list.get_all(True)
    for member in member_list:
        if member.position == UnionMemberInfo.POSITION_LEADER:
            leader = member
            break
    
    app_req = internal_pb2.GetUserBasicInfoReq()
    app_req.user_id = leader.user_id

    defer = GlobalObject().remote['app'].callRemote("get_user_basic_info",
            leader.user_id, app_req.SerializeToString())
    defer.addCallback(_get_leader_info, leader)
    return defer

def _get_leader_info(app_response, leader):
    app_res = internal_pb2.GetUserBasicInfoRes()
    app_res.ParseFromString(app_response)

    assert app_res.status == 0
    leader_info = utils.object2dict(leader)
    leader_info['name'] = app_res.user_info.name
    leader_info['last_login_time'] = app_res.user_info.last_login_time
    return leader_info

def is_need_transfer_leader(data, leader_info, now):
    """是否需要转让盟主"""
    days = utils.count_days_diff(leader_info['last_login_time'], now)
    return days > 3

def transfer_leader(data, leader_info, now):
    """转让盟主"""
    defer = _get_transfer_member(data, now)
    defer.addCallback(_transfer_leader_member, data, leader_info)
    return defer

def _transfer_leader_member(member_info, data, leader_info):
    if member_info is None:
        defer = Deferred()
        defer.callback(None)
        defer.addCallback(_transfer_leader_mail, False)
        return defer

    leader = data.member_list.get(UnionMemberInfo.generate_id(data.id, leader_info['user_id']))
    member = data.member_list.get(UnionMemberInfo.generate_id(data.id, member_info['user_id']))

    leader.set_as_normal_member()
    member.set_as_leader()
    union = data.union.get()
    union.set_as_leader(member.user_id)

    subject = data_loader.ServerDescKeyInfo_dict["transfer_leader_subject"].value.encode("utf8")
    sender = data_loader.ServerDescKeyInfo_dict["union_sender"].value.encode("utf8")
    content_templet = data_loader.ServerDescKeyInfo_dict["transfer_leader_content"].value.encode("utf8")
   
    content = content_templet.replace("@user_name", leader_info['name'], 1)
    content = content.replace("@user_name", member_info['name'], 1)

    mail = internal_pb2.CustomMailInfo()
    mail.subject = subject
    mail.sender = sender
    mail.content = content

    defer = _send_mail_to_all_members(data, data.id, mail)
    defer.addCallback(_transfer_leader_mail, True)
    return defer

def _transfer_leader_mail(app_res, result):
    return result

def _get_transfer_member(data, now):
    """获取要转让的新盟主"""
    members = data.member_list.get_all(True)
    members_info = []
    defer = _get_members_info(members, members_info, 0)
    defer.addCallback(_get_transfer_member_result, data, now)
    return defer

def _get_transfer_member_result(members_info, data, now):
    members_info = [member_info for member_info in members_info 
            if utils.count_days_diff(member_info['last_login_time'], now) <= 3]
    if len(members_info) == 0:
        return None
    
    vices_info = [member_info for member_info in members_info
            if member_info['position'] == UnionMemberInfo.POSITION_VICE]
    if len(vices_info) == 0:
        members_info.sort(key = lambda member_info: member_info['history_honor'], reverse = True)
        return members_info[0]
    else:
        vices_info.sort(key = lambda vice_info: vice_info['history_honor'], reverse = True)
        return vices_info[0]

def _get_members_info(members, members_info, i):
    app_req = internal_pb2.GetUserBasicInfoReq()
    app_req.user_id = members[i].user_id

    defer = GlobalObject().remote['app'].callRemote("get_user_basic_info",
            members[i].user_id, app_req.SerializeToString())
    defer.addCallback(_get_members_info_result, members, members_info, i)
    return defer

def _get_members_info_result(app_response, members, members_info, i):
    app_res = internal_pb2.GetUserBasicInfoRes()
    app_res.ParseFromString(app_response)
    assert app_res.status == 0

    member_info = utils.object2dict(members[i])
    member_info['name'] = app_res.user_info.name
    member_info['last_login_time'] = app_res.user_info.last_login_time
    members_info.append(member_info)

    #递归出口
    if app_res.status !=0 or i >= len(members) - 1:
        return members_info

    i += 1
    return _get_members_info(members, members_info, i)

def _send_mail_to_all_members(data, user_id, mail_message):
    """给全员发送邮件"""
    member_list = data.member_list.get_all(True)
    return _calc_send_mail_to_all_members(member_list, 0, user_id, mail_message)

def _calc_send_mail_to_all_members(member_list, i, user_id, mail_message):
    app_req = internal_pb2.AddMailReq()
    app_req.user_id = user_id
    app_req.recipients_user_id = member_list[i].user_id
    app_req.mail.CopyFrom(mail_message)

    defer = GlobalObject().remote['app'].callRemote("add_mail",
            user_id, app_req.SerializeToString())
    defer.addCallback(_calc_send_mail_to_all_members_result, member_list, i, user_id, mail_message)
    return defer

def _calc_send_mail_to_all_members_result(app_response, member_list, i, user_id, mail_message):
    app_res = internal_pb2.AddMailRes()
    app_res.ParseFromString(app_response)
    assert app_res.status == 0

    if app_res.status != 0 or i >= len(member_list) - 1:
        return app_res

    i += 1
    return _calc_send_mail_to_all_members(member_list, i, user_id, mail_message)

def get_transfer_member_simple(data):
    """通过简单的算法获取要转让的新盟主"""
    all_member = data.member_list.get_all(True)
    all_member = [member for member in all_member
            if member.position != UnionMemberInfo.POSITION_LEADER]
    
    if len(all_member) <= 0:
        return None

    vices = [member for member in all_member if member.position == UnionMemberInfo.POSITION_VICE]
    #优先转让给副盟主
    if len(vices) != 0:
        vices.sort(key=lambda vice:vice.history_honor, reverse=True)
        return vices[0]
    else:
        all_member.sort(key=lambda member:member.history_honor, reverse=True)
        return all_member[0]
