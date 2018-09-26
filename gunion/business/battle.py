#coding:utf8
"""
Created on 2016-07-29
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争逻辑
"""

from utils import logger
from datalib.data_loader import data_loader
from proto import broadcast_pb2
from gunion.data.member import UnionMemberInfo
from firefly.server.globalobject import GlobalObject
from gunion.data.union import UnionInfo
from gunion.data.season import UnionSeasonInfo
from gunion.data.battle import UnionBattleInfo
from gunion.data.battle_node import UnionBattleMapNodeInfo
from gunion.data.battle_record import UnionBattleRecordInfo
from gunion.season_allocator import SeasonAllocator
from gunion.rival_matcher import PVEEnemyPool
import base64
import random

def update_battle(data, now, no_record = False):
    """刷新战争信息
    """
    battle = get_current_battle(data, now)
    if battle.stage == battle.BATTLE_STAGE_PREPARE:
        #备战阶段，尝试进入战斗状态
        _try_start_fight(data, battle, now)
    elif battle.stage == battle.BATTLE_STAGE_FIGHT:
        #战斗阶段，尝试结束超时战斗
        _try_calc_timeout_node_battle(data, battle, now, no_record)
        #尝试结束战争
        _try_close_fight(data, battle, now)
    elif battle.stage == battle.BATTLE_STAGE_CLOSE:
        #战斗结束，尝试结束超时战斗（因为仍然可能有结束前开始的战斗）
        _try_calc_timeout_node_battle(data, battle, now, no_record)
        pass

    return battle


def forward_season(data, index, start_time):
    """进入下一个赛季
    """
    season = data.season.get()
    season.forward(index, start_time)

    #清除个人战功
    for member in data.member_list.get_all():
        member.reset_season()

    #清除上赛季的所有战争信息
    pre_season_battle = []
    for battle in data.battle_list.get_all():
        pre_season_battle.append(battle.id)
    for battle_id in pre_season_battle:
        data.battle_list.delete(battle_id)

    #开启下一场战斗
    forward_battle(data, start_time)


def get_current_battle(data, now):
    """获取当前的联盟战争
    """
    season = data.season.get(True)

    battle_id = UnionBattleInfo.generate_id(data.id, season.current_battle_index)
    battle = data.battle_list.get(battle_id)
    return battle


def forward_battle(data, now):
    """进入下一场战争
    """
    #创建下一场战争的数据
    union = data.union.get(True)
    season = data.season.get()
    battle_index = season.forward_battle_index()
    battle = UnionBattleInfo.create(data.id, battle_index, season.is_near_end(now))
    data.battle_list.add(battle)
    season.update_join_battle_status(union.current_number, battle.is_able_to_join())

    #清除个人战争战功
    for member in data.member_list.get_all():
        member.reset_battle()

    #清除节点部署
    for node in data.battle_node_list.get_all():
        node.reset()

    #清除上一场战争的战斗记录
    pre_battle_record = []
    for record in data.battle_record_list.get_all():
        pre_battle_record.append(record.id)
    for record_id in pre_battle_record:
        data.battle_record_list.delete(record_id)

    return battle


def get_battle_map(data):
    """获取战争地图
    如果地图不存在，创建地图上所有节点
    """
    count = int(float(data_loader.UnionConfInfo_dict["battle_map_node_count"].value))
    if len(data.battle_node_list) < count:
        #不足的节点补上
        for index in range(len(data.battle_node_list) + 1, count + 1):
            node = UnionBattleMapNodeInfo.create(data.id, index)
            data.battle_node_list.add(node)
    elif len(data.battle_node_list) > count:
        #多余的节点删除
        for index in range(count + 1, len(data.battle_node_list) + 1):
            for battle_node in data.battle_node_list.get_all():
                if battle_node.index == index:
                    data.battle_node_list.delete(battle_node.id)
                    break;

    return data.battle_node_list.get_all(True)


def launch_battle(data, battle, rival_union_id, rival_battle_id, now, initiative = True):
    """发起战争
    Args:
        data
        battle
        rival_union_id
        rival_battle_id
        now
        initiative[bool]: 是否主动发起
    """
    union = data.union.get(True)
    season = data.season.get()
    battle.launch(now, rival_union_id, rival_battle_id, initiative)
    season.update_join_battle_status(union.current_number, battle.is_able_to_join())

    #允许此时在联盟中的成员参战
    for member in data.member_list.get_all():
        member.join_battle()


def _try_start_fight(data, battle, now):
    """尝试进行开战操作
    """
    if now < battle.fight_time:
        #未到开战时间
        return

    #检查是否有仍然未部署的节点，自动部署
    if not battle.is_deployed:
        _try_deploy_battle_map_auto(data, battle, now)

    battle.start_fight(now)


def _try_deploy_battle_map_auto(data, battle, now):
    """自动部署战争地图节点防御
    因为开战时，仍然有节点未进行部署，系统自动部署
    """
    nodes = get_battle_map(data)
    for node in nodes:
        if not node.is_deployed():
            _deploy_battle_map_node_auto(data, node.id, now)


def _deploy_battle_map_node_auto(data, node_id, now):
    """使用 PVE 阵容填充节点，进行防守部署
    """
    node = data.battle_node_list.get(node_id)

    #TODO 使用加入联盟最低的等级
    target_level = 14
    (enemy, name, icon) = PVEEnemyPool().get(target_level)
    node.deploy_auto(enemy, name, icon)


def deploy_node(data, node,
        user_id, user_name, user_icon, user_level,
        team, heroes, techs, city_level):
    """部署防守部队
    """
    node.deploy(user_id, user_name, user_icon, user_level, team, heroes, techs, city_level)


def cancel_deploy_node(data, node):
    """取消节点的防守部队
    """
    node.cancel_deploy()


def _calc_deploy_node_count_of_member(data, member):
    """计算成员布防节点个数
    """
    count = 0
    for node in data.battle_node_list.get_all(True):
        if node.defender_user_id == member.user_id:
            count += 1

    return count


def _try_calc_timeout_node_battle(data, battle, now, no_record = False):
    """尝试结束所有超时战斗
    """
    for node in data.battle_node_list.get_all(True):
        if node.get_battle_timeout_num(now) > 0:
            _finish_timeout_node_battle(data, battle, node, now, no_record)


def _finish_timeout_node_battle(data, battle, node, now, no_record = False):
    """结束超时战斗
    """
    defender_id = UnionMemberInfo.generate_id(data.id, node.defender_user_id)
    defender = data.member_list.get(defender_id)

    #强制结束，算战斗失败，击杀了进攻方所有兵力
    assert finish_node_battle_as_defender(
            data, battle, node.index, node.level, False, 0,
            defender, 0, 0, now, force = True, no_record = no_record)


def _try_close_fight(data, battle, now):
    """尝试结束战争
    """
    is_all_nodes_beaten = True
    nodes = get_battle_map(data)
    for node in nodes:
        if node.current_soldier_num > 0:
            is_all_nodes_beaten = False
            break

    if battle.is_fight_closed(now) or is_all_nodes_beaten:
        battle.close_fight()
        return


def start_node_battle_as_defender(data, battle,
        attacker_user_id, attacker_user_name, attacker_user_icon, attacker_soldier_num,
        node_index, node_level, now):
    """在节点上开始一场战斗（本联盟作为防守方）
    """
    if not battle.is_able_to_start():
        #战斗已经结束
        logger.warning("Not able to start battle")
        return False

    node_id = UnionBattleMapNodeInfo.generate_id(data.id, node_index)
    node = data.battle_node_list.get(node_id)

    if node_level != node.level:
        #节点状态发生了变化
        logger.warning("Node not matched[input level=%d][node level=%d]" %
                (node_level, node.level))
        return False

    if not node.is_able_to_start_battle():
        #节点正在被攻击
        logger.warning("Not able to start node battle")
        return False

    node.start_battle(attacker_user_id, now)
    return True


def finish_node_battle_as_defender(
    data, battle, node_index, node_level, is_attacker_win, attacker_user_id,
    defender, attacker_kills, defender_kills, now, force = False, no_record = False):
    """在节点上结束一场战斗（本联盟作为防守方）
    Args:
        data
        node_index
        node_level
        is_attacker_win
        defender
        defender_kills
        now
        force[bool]: 是否强制结束，忽略时间限制
    """
    node_id = UnionBattleMapNodeInfo.generate_id(data.id, node_index)
    node = data.battle_node_list.get(node_id)

    if node_level != node.level:
        logger.warning("Node not matched[input level=%d][node level=%d]" %
                (node_level, node.level))
        return False

    if not force and not node.is_able_to_finish_battle(attacker_user_id, now):
        logger.warning("Not able to finish node battle")
        return False

    if force:
        node.finish_battles_timeout(now)
    else:
        #防守方杀敌数增加
        # if defender is not None:
        #     defender.add_kills(defender_kills)
        #     score = defender.calc_battle_score_by_kills(defender_kills)
        #     battle.gain_individuals_score(score)

        #节点结束战斗
        node.finish_battle(attacker_user_id, attacker_kills)

    #如果所有节点被击败，地图进入下一层 level
    if is_attacker_win:
        _try_forward_battle_map(data)
        
    _try_close_fight(data, battle, now)

    return True


def finish_node_battle_as_attacker(data, battle, node_level, defender_battle_stage,
        is_attacker_win, attacker, attacker_level, attacker_kills, score_add,
        node_level_after_battle, is_node_broken_after_battle):
    """在节点上结束一场战斗（本联盟作为进攻方）
    """

    deploy_count = _calc_deploy_node_count_of_member(data, attacker)
    incr_ratio = float(
            data_loader.UnionConfInfo_dict["indivdiual_score_incr_ratio_of_deploy"].value)
    deploy_ratio = 1.0 + deploy_count * incr_ratio

    if is_attacker_win:
        #进攻胜利，获得战功 = ( 杀敌获得战功 * 部署节点加成 + 额外奖励战功 * X ) * Y
        kill_score = int(
                attacker.calc_battle_score_by_kills(attacker_kills) * deploy_ratio)
        #额外奖励战功: 等于 X 次擂鼓获得的战功
        extra_count = int(float(
            data_loader.UnionConfInfo_dict["indivdiual_score_extra_value_per_win"].value))
        extra_score = attacker.calc_battle_score_by_drum(extra_count, attacker_level)
        level_ratio = 1.0 + (battle.attack_level - 1) * float(
                data_loader.UnionConfInfo_dict["indivdiual_score_ratio_of_level"].value)

        score = int((kill_score + extra_score) * level_ratio)

    else:
        #进攻失败，获得战功 = 杀敌获得战功 * 部署节点加成
        #score = int(
        #        attacker.calc_battle_score_by_kills(attacker_kills) * deploy_ratio)
        score = 0
    score_add.append(score)
    attacker.gain_battle_score_immediate(score)
    attacker.add_kills(attacker_kills)
    battle.gain_individuals_score(score)

    if node_level < node_level_after_battle or is_node_broken_after_battle:
        win_node = True
    else:
        win_node = False
    
    #记录攻击结果
    battle.mark_attack_result(win_node)

    #胜利：联盟获得胜场积分
    if win_node:
        battle.gain_union_score()
        season = data.season.get()
        season.gain_union_score()

        if battle.score % 2 == 0 and battle.score != 0:
            try:
                _win_battle_broadcast(data, battle)
            except:
                logger.warning("Send win battle broadcast failed")

    #防守方若已提前结束，则进攻方也结束
    if defender_battle_stage == battle.BATTLE_STAGE_CLOSE:
        battle.close_fight()

    return True

def _win_battle_broadcast(data, battle):
    """获得积分发广播"""
    union_name = data.union.get(True).name

    broadcast_id = int(float(data_loader.OtherBasicInfo_dict['broadcast_id_win_unionbattle'].value))
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(union_name), 1)
    content = content.replace("#str#", str(battle.score), 1)

    req = broadcast_pb2.AddBroadcastInfoReq()
    req.user_id = data.id
    req.mode_id = mode_id
    req.priority = priority
    req.life_time = life_time
    req.content = content
    request = req.SerializeToString()

    defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)

def _try_forward_battle_map(data):
    """尝试进入一下 level 的地图
    """
    #需要所有的节点都可以进入下一个 level
    for node in data.battle_node_list.get_all(True):
        if not node.is_able_to_forward():
            return

    for node in data.battle_node_list.get_all():
        node.forward()


def drum(data, battle, member, user_level, drum_count = 1):
    """擂鼓
    Returns:
        score: 个人获得的战功
    """
    battle.beat_drum(drum_count)

    #成员擂鼓，获得战功
    deploy_count = _calc_deploy_node_count_of_member(data, member)
    incr_ratio = float(
            data_loader.UnionConfInfo_dict["indivdiual_score_incr_ratio_of_deploy"].value)
    deploy_ratio = 1.0 + deploy_count * incr_ratio

    score = int(member.calc_battle_score_by_drum(drum_count, user_level) * deploy_ratio)
    member.drum(drum_count)
    member.gain_battle_score_immediate(score)

    battle.gain_individuals_score(score)
    return score


def is_able_to_accept_node_reward(data, user_id, node):
    """是否可以领取相应的node宝箱"""
    if user_id in node.get_accepted_members():
        logger.warning("Attacker has received node reward[union_id=%d][nodex_index=%d][user_id=%d]" % (
                data.id, node.index, user_id))
        return False
    
    if node.status != node.NODE_STATUS_BEATEN:
        logger.warning("node not be beaten[union_id=%d][node_index=%d]" % (
                data.id, node.index))
        return False

    return True


def accept_node_reward(data, user_id, user_name, icon_id, node, now):
    """领取node奖励宝箱"""
    union = data.union.get()

    if node.city_level == 2:
        pool = data_loader.UnionBattleBoxThree_dict
    if node.city_level == 1:
        pool = data_loader.UnionBattleBoxTwo_dict
    if node.city_level == 0:
        pool = data_loader.UnionBattleBoxOne_dict

    weight_sum = 0
    for key in pool:
        weight_sum += pool[key].weight

    rand = random.uniform(0, weight_sum)
    per_weight = 0
    choose = None
    for key in pool:
        if per_weight <= rand <= pool[key].weight + per_weight:
            choose = key
            break
        per_weight += pool[key].weight

    item_id = pool[choose].itemBasicId
    item_num = pool[choose].itemNum

    node.add_reward_record(user_id, user_name, icon_id, item_id, item_num, now)


def is_able_to_accept_battle_box_reward(data, user_id, battle):
    """是否可以领取大宝箱奖励"""
    if user_id in battle.get_accepted_members():
        logger.warning("Attacker has received battle box[union_id=%d][user_id=%d]" % (
                data.id, user_id))
        return False
    
    if not battle.is_able_to_accept_box():
        logger.warning("battle box can not be accepted[union_id=%d]" % data.id)
        return False

    return True


def accept_battle_box_reward(data, battle, user_id, user_name, icon_id, now):
    """领取大宝箱奖励"""
    union = data.union.get()

    pool = data_loader.UnionBattleBoxFour_dict

    weight_sum = 0
    for key in pool:
        weight_sum += pool[key].weight

    rand = random.uniform(0, weight_sum)
    per_weight = 0
    choose = None
    for key in pool:
        if per_weight <= rand <= pool[key].weight + per_weight:
            choose = key
            break
        per_weight += pool[key].weight

    item_id = pool[choose].itemBasicId
    item_num = pool[choose].itemNum

    battle.add_reward_record(user_id, user_name, icon_id, item_id, item_num, now)


