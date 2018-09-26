#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 模块提供的服务
"""

from firefly.server.globalobject import rootserviceHandle
from gunion.processor.union_processor import UnionProcessor
from gunion.processor.member_processor import MemberProcessor
from gunion.processor.aid_processor import AidProcessor
from gunion.processor.battle_processor import BattleProcessor
from gunion.processor.donate_processor import DonateProcess
from gunion.processor.boss_processor import BossProcess


_union_processor = UnionProcessor()
@rootserviceHandle
def create_union(union_id, data):
    """创建联盟
    """
    return _union_processor.create(union_id, data)

@rootserviceHandle
def delete_union(union_id, data):
    """删除联盟，内部接口
    """
    return _union_processor.delete(union_id, data)


@rootserviceHandle
def query_union(union_id, data):
    """查询联盟信息
    """
    return _union_processor.query(union_id, data)


@rootserviceHandle
def query_union_force(union_id, data):
    """查询联盟信息(不用管查询者是否属于本联盟)
    """
    return _union_processor.query(union_id, data, True)


@rootserviceHandle
def query_union_summary(union_id, data):
    """查询联盟信息(不用管查询者是否属于本联盟)
    """
    return _union_processor.query_summary(union_id, data)


@rootserviceHandle
def update_union(union_id, data):
    """设置联盟
    """
    return _union_processor.update(union_id, data)


@rootserviceHandle
def start_union_chat(union_id, data):
    """联盟聊天
    """
    return _union_processor.start_chat(union_id, data)


@rootserviceHandle
def sync_union(union_id, data):
    """同步联盟信息（内部）
    """
    return _union_processor.sync(union_id, data)


@rootserviceHandle
def add_prosperity(union_id, data):
    """添加繁荣度
    """
    return _union_processor.add_prosperity(union_id, data)


_member_processor = MemberProcessor()
@rootserviceHandle
def join_union(union_id, data):
    """尝试加入联盟
    """
    return _member_processor.join(union_id, data)

@rootserviceHandle
def approve_union(union_id, data):
    """审批入盟申请
    """
    return _member_processor.approve(union_id, data)

@rootserviceHandle
def manage_union(union_id, data):
    """管理联盟
    """
    return _member_processor.manage(union_id, data)

@rootserviceHandle
def add_honor(union_id, data):
    """添加联盟荣誉（内部接口）
    """
    return _member_processor.add_honor(union_id, data)

@rootserviceHandle
def try_transfer_leader(union_id, data):
    """自动盟主转让"""
    return _member_processor.try_transfer(union_id, data)

_aid_processor = AidProcessor()
@rootserviceHandle
def start_aid(union_id, data):
    """启动联盟援助
    """
    return _aid_processor.start(union_id, data)

@rootserviceHandle
def finish_aid(union_id, data):
    """结束联盟援助
    """
    return _aid_processor.finish(union_id, data)

@rootserviceHandle
def query_aid(union_id, data):
    """查询联盟援助
    """
    return _aid_processor.query(union_id, data)

@rootserviceHandle
def respond_aid(union_id, data):
    """响应联盟援助
    """
    return _aid_processor.respond(union_id, data)


_battle_processor = BattleProcessor()
@rootserviceHandle
def query_battle(union_id, data):
    """查询联盟战争
    """
    return _battle_processor.query(union_id, data)


@rootserviceHandle
def launch_battle(union_id, data):
    """发起联盟战争
    """
    return _battle_processor.launch(union_id, data)

@rootserviceHandle
def launch_battle_force(union_id, data):
    """发起联盟战争(可由联盟外成员强制发起)
    """
    return _battle_processor.launch(union_id, data, True)


@rootserviceHandle
def launch_battle_two(union_id, data):
    """发起两个指定联盟的战争
    """
    return _battle_processor.launch_two(union_id, data)


@rootserviceHandle
def accept_battle(union_id, data):
    """接受联盟战争
    """
    return _battle_processor.accept(union_id, data)


@rootserviceHandle
def deploy_battle(union_id, data):
    """部署联盟战争
    """
    return _battle_processor.deploy(union_id, data)


@rootserviceHandle
def cancel_deploy_battle(union_id, data):
    """取消部署联盟战争
    """
    return _battle_processor.cancel_deploy(union_id, data)


@rootserviceHandle
def start_battle(union_id, data):
    """开始战斗
    """
    return _battle_processor.start(union_id, data)


@rootserviceHandle
def finish_battle(union_id, data):
    """结束战斗
    """
    return _battle_processor.finish(union_id, data)


@rootserviceHandle
def drum_for_battle(union_id, data):
    """擂鼓
    """
    return _battle_processor.drum(union_id, data)


@rootserviceHandle
def accept_battle_node_reward(union_id, data):
    return _battle_processor.node_reward(union_id, data)


@rootserviceHandle
def accept_union_battle_box_succeed(union_id, data):
    return _battle_processor.battle_box_reward(union_id, data)


@rootserviceHandle
def accept_individual_step_award(union_id, data):
    """领取战功阶段奖励
    """
    return _battle_processor.accept_individual_step_award(union_id, data)


@rootserviceHandle
def gain_battle_score(union_id, data):
    """增加胜场积分/战功
    """
    return _battle_processor.gain_battle_score(union_id, data)



@rootserviceHandle
def force_update_battle(union_id, data):
    """强制更新联盟战争状态
    """
    return _battle_processor.force_update(union_id, data)


@rootserviceHandle
def try_forward_battle(union_id, data):
    """尝试进入下一场战斗
    """
    return _battle_processor.try_forward_battle(union_id, data)


@rootserviceHandle
def try_forward_season(union_id, data):
    """尝试进入下一个赛季
    """
    return _battle_processor.try_forward_season(union_id, data)

_donate_processor = DonateProcess()

@rootserviceHandle
def query_donate(union_id, data):
    """查询联盟捐献信息"""
    return _donate_processor.query(union_id, data)

@rootserviceHandle
def initiate_donate(union_id, data):
    """发起联盟捐献"""
    return _donate_processor.initiate(union_id, data)

@rootserviceHandle
def start_donate(union_id, data):
    """进行联盟捐献"""
    return _donate_processor.start(union_id, data)

@rootserviceHandle
def reward_donate(union_id, data):
    """领取捐献奖励"""
    return _donate_processor.reward(union_id, data)

@rootserviceHandle
def refresh_donate(union_id, data):
    """刷新捐献箱"""
    return _donate_processor.refresh(union_id, data)


_boss_processor = BossProcess()

@rootserviceHandle
def query_unionboss(union_id, data):
    return _boss_processor.query(union_id, data)

@rootserviceHandle
def sync_unionboss(union_id, data):
    return _boss_processor.sync(union_id, data)

@rootserviceHandle
def accept_unionboss_reward(union_id, data):
    return _boss_processor.boss_reward(union_id, data)

@rootserviceHandle
def query_unionboss_reward(union_id, data):
    return _boss_processor.query_boss_reward(union_id, data)
'''
@rootserviceHandle
def update_unionboss(union_id, data):
    return _boss_processor.update(union_id, data)
'''
