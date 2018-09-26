#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 世界地图随机事件逻辑
"""

import random
from utils import logger
from utils import utils
from utils.ret import Ret
from datalib.data_loader import data_loader
from app import log_formater
from app.data.map import MapGraph
from app.data.node import NodeInfo
from app.core.event import EventHandler
from app.business import map as map_business
from app.business import spy as spy_business
from app.business import visit as visit_business
from app.business import question as question_business
from app.business import jungle as jungle_business
from app.business import dungeon as dungeon_business
from app.business import arena as arena_business
from app.business import defend as defend_business
from app.business import exploitation as exploitation_business
from app.business import scout as scout_business
from app.business import user as user_business
from app.business import worldboss as worldboss_business


def register_lucky_event():
    """注册随机事件的方法
    """
    EventHandler().register(NodeInfo.EVENT_TYPE_TAX,
            arise = _default_arise_lucky_event,
            clear = _default_clear_lucky_event,
            stop = exploitation_business.stop_exploit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_FARM,
            arise = _default_arise_lucky_event,
            clear = _default_clear_lucky_event,
            stop = exploitation_business.stop_exploit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_MINING,
            arise = _default_arise_lucky_event,
            clear = _default_clear_lucky_event,
            stop = exploitation_business.stop_exploit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_GOLD,
            arise = exploitation_business.arise_gold_event,
            clear = exploitation_business.clear_gold_event,
            stop = exploitation_business.stop_exploit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_SEARCH,
            arise = exploitation_business.arise_offline_exploit_event,
            clear = exploitation_business.clear_offline_exploit_event,
            stop = exploitation_business.stop_exploit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_DEEP_MINING,
            arise = exploitation_business.arise_offline_exploit_event,
            clear = exploitation_business.clear_offline_exploit_event,
            stop = exploitation_business.stop_exploit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_HERMIT,
            arise = exploitation_business.arise_offline_exploit_event,
            clear = exploitation_business.clear_offline_exploit_event,
            stop = exploitation_business.stop_exploit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_UPGRADE,
            arise = _default_arise_lucky_event,
            clear = _default_clear_lucky_event,
            stop = _default_clear_lucky_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_DEFEND,
            arise = defend_business.arise_defend_event,
            clear = defend_business.clear_defend_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_JUNGLE,
            arise = jungle_business.arise_jungle_event,
            clear = jungle_business.clear_jungle_event,
            stop = jungle_business.clear_jungle_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_VISIT,
            arise = visit_business.arise_visit_event,
            clear = _default_clear_lucky_event,
            timeout = visit_business.clear_visit_event,
            stop = visit_business.clear_visit_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_QUESTION,
            arise = question_business.arise_question_event,
            clear = _default_clear_lucky_event,
            timeout = question_business.clear_question_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_SPY,
            arise = spy_business.arise_spy_event,
            clear = spy_business.clear_spy_event,
            stop = spy_business.clear_spy_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_DUNGEON,
            arise = dungeon_business.arise_dungeon_event,
            clear = dungeon_business.clear_dungeon_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_ARENA,
            arise = arena_business.arise_arena_event,
            clear = arena_business.clear_arena_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_SCOUT,
            arise = scout_business.arise_scout_event)

    EventHandler().register(NodeInfo.EVENT_TYPE_WORLDBOSS,
            arise = worldboss_business.arise_worldboss_event,
            clear = worldboss_business.clear_worldboss_event)



def trigger_custom_event(data, now, node_basic_id, event_type, change_nodes):
    """触发特定的事件
    可以指定发生事件的节点，事件的类型
    """
    logger.debug("Trigger custom event")
    map = data.map.get()
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    node = data.node_list.get(node_id)

    candidate = _calc_candidate_event(data, node, now)
    candidate.extend(_calc_candidate_event(data, node, now, False))
    if len(candidate) == 0:
        logger.warning("Node not prepared for event[node basic id=%d]" % node.basic_id)
        return False

    if event_type not in candidate:
        logger.warning("Node not matched event"
                "[node basic id=%d][event type=%d][available=%s]" %
                (node.basic_id, event_type, utils.join_to_string(candidate)))
        return False

    if not _node_arise_event(data, node_id, event_type, now,
            change_nodes, [], []):
        return False

    change_nodes.append(node)
    logger.debug("node trigger event[basic id=%d][event type=%d]" %
            (node.basic_id, node.event_type))

    map.update_next_luck_time(now)
    return True


def trigger_lucky_event(data, now,
        change_nodes = [], new_items = [], new_mails = []):
    """触发随机事件
    """
    #判断是否可以触发随机事件
    map = data.map.get()
    if not map.is_able_to_trigger_lucky_event(now):
        logger.warning("Not able to trigger lucky event[next time=%d][now=%d]" %
                (map.next_luck_time, now))
        return True

    user = data.user.get(True)
    #检查当前玩家等级
    need_level = int(float(
        data_loader.LuckyEventConfInfo_dict["lucky_event_unlock_level"].value))
    if user.level < need_level:
        logger.debug("User level not statisfy, not trigger lucky event[level=%d]" % user.level)
        # map.update_next_luck_time(now, 0)
        return True

    #检查是否完成基础新手引导
    if not user.is_basic_guide_finish():
        logger.debug("Basic guide not finish, not trigger lucky event")
        map.update_next_luck_time(now, 0)
        return True

    logger.debug("Trigger lucky event")

    node_list = data.node_list.get_all(True)

    #避免每次都从相同的点开始遍历，随机选择一个起始点
    random.seed()
    index = random.randint(0, len(node_list) - 1)
    for i in range(0, len(node_list)):
        node = node_list[index]
        (node_id, event_type) = _is_node_arise_lucky_event(data, node, now)
        if event_type != NodeInfo.EVENT_TYPE_INVALID:
            change_nodes.append(node)

            if not _node_arise_event(data, node_id, event_type, now,
                    change_nodes, new_items, new_mails):
                return False

        index = (index + 1) % len(node_list)

    #如果此时没有发生随机事件，缩短下次触发随机事件的间隔
    event_count = len([node for node in node_list if node.is_event_arised()])
    if event_count == 0:
        map.update_next_luck_time(now, reduce_gap = True)
    else:
        map.update_next_luck_time(now)

    return True


def trigger_specified_event(data, event_type, now,
        change_nodes = [], new_items = [], new_mails = []):
    """触发指定事件
    """
    user = data.user.get(True)
    ##检查当前玩家等级
    #need_level = int(float(
    #    data_loader.LuckyEventConfInfo_dict["lucky_event_unlock_level"].value))
    #if user.level < need_level:
    #    logger.debug("User level not statisfy, not trigger lucky event[level=%d]" % user.level)
    #    return True

    #判断是否有足够政令值触发指定事件
    energy = data.energy.get()
    need_energy = energy.calc_energy_consume_of_event(event_type)
    if need_energy is None:
        logger.warning("Not able to calc energy consume[type=%d]" % event_type)
        return False

    energy.update_current_energy(now)
    if need_energy > energy.energy:
        logger.warning("Not enough energy to trigger event[type=%d][need_energy=%d][energy=%d]" %
                (event_type, need_energy, energy.energy))
        return False

    #扣减政力值
    if not energy.cost_energy(need_energy, event_type, now):
        return False

    #用户获得经验(1点政力值获得1点主公经验)
    monarch_per_energy = 1
    if data_loader.OtherBasicInfo_dict.has_key("monarch_per_energy"):
        monarch_per_energy = int(float(data_loader.OtherBasicInfo_dict["monarch_per_energy"].value))
    if not user_business.level_upgrade(data, need_energy * monarch_per_energy, now, "event exp", log_formater.EXP_EVENT):
        return False

    logger.debug("Trigger specified event")

    node_list = _get_nodes_can_arise_specified_event(data, event_type, now)
    if len(node_list) == 0:
        logger.debug("No node to trigger specified event[type=%d]" % event_type)
        return True

    trigger_nodes = []

    if (event_type == NodeInfo.EVENT_TYPE_VISIT
            or event_type == NodeInfo.EVENT_TYPE_DUNGEON
            or event_type == NodeInfo.EVENT_TYPE_SEARCH
            or event_type == NodeInfo.EVENT_TYPE_DEEP_MINING
            or event_type == NodeInfo.EVENT_TYPE_HERMIT):
        #visit事件、dungeon事件和离线开采事件，随机选一个点
        index = random.randint(0, len(node_list) - 1)
        trigger_nodes.append(node_list[index])
    else:
        limit_min = _get_event_trigger_limit_min(event_type, user)
        enemy_neighbor_count = 0
        if event_type == NodeInfo.EVENT_TYPE_SCOUT:
            enemy_neighbor_count = _get_all_enemy_neighbor_count(data)

        for node in node_list:
            if _is_node_arise_specified_event(data, node, event_type, now, enemy_neighbor_count):
                trigger_nodes.append(node)

        #保证最少触发limit_min个点
        if len(trigger_nodes) < limit_min:
            diff = limit_min - len(trigger_nodes)
            diff = min(diff, len(node_list) - len(trigger_nodes))
            left_nodes = [ node for node in node_list if node not in trigger_nodes ]
            trigger_nodes.extend(random.sample(left_nodes, diff))

    for node in trigger_nodes:
        change_nodes.append(node)
        if not _node_arise_event(data, node.id, event_type, now,
                change_nodes, new_items, new_mails):
            return False

    logger.debug("trigger specified event[basic id=%d][event type=%d][nodes_num=%d]" %
            (node.basic_id, node.event_type, len(trigger_nodes)))
    return True


def _get_nodes_can_arise_specified_event(data, event_type, now):
    """
    获取可以触发指定事件的所有node
    Args:
        data[UserData]: 玩家所有数据
        event_type[int]: 事件类型
    Returns:
        list(node)
    """
    candidate_nodes = []

    node_list = data.node_list.get_all(True)
    #避免每次都从相同的点开始遍历，随机选择一个起始点
    random.seed()
    index = random.randint(0, len(node_list) - 1)
    for i in range(0, len(node_list)):
        node = node_list[index]
        index = (index + 1) % len(node_list)

        candidate = _calc_candidate_event(data, node, now, False)
        if len(candidate) == 0:
            continue
        if event_type not in candidate:
            continue
        candidate_nodes.append(node)

    return candidate_nodes


def _is_node_arise_lucky_event(data, node, now):
    """
    判断节点上是否新发生随机事件，发生了什么随机事件
    Args:
        data[UserData]: 玩家所有数据
        node[NodeInfo]: 节点信息, readonly
    Returns:
        (node_id, event_type)
    """
    candidate = _calc_candidate_event(data, node, now)
    if len(candidate) == 0:
        logger.debug("node not ready for event[node basic id=%d]" % node.basic_id)
        return (node.id, NodeInfo.EVENT_TYPE_INVALID)

    #按照优先级顺序，优先级高，排在前面
    candidate = sorted(candidate,
            key = lambda type : data_loader.LuckyEventBasicInfo_dict[type].priority)

    return _roll_lucky_event(data, node, candidate, now)


def _is_node_arise_specified_event(data, node, event_type, now, enemy_neighbor_count):
    """判断节点是否触发指定事件
    """
    #计算指定事件的概率
    r = _calc_lucky_event_ratio(data, event_type, node, now, enemy_neighbor_count)

    #random
    random.seed()
    c = random.random()

    logger.debug("specified event[node basic id=%d][event type=%d][ratio=%f][random=%f]" %
            (node.basic_id, event_type, r, c))
    if c < r:
        return True
    else:
        return False


def _get_event_trigger_limit_min(event_type, user):
    """获得事件触发的最少节点个数
    """
    limit_min = 0
    if event_type == NodeInfo.EVENT_TYPE_TAX:
        limit_min = data_loader.EventTaxBasicInfo_dict[user.level].limitMin
    elif event_type == NodeInfo.EVENT_TYPE_FARM:
        limit_min = data_loader.EventFarmBasicInfo_dict[user.level].limitMin
    elif event_type == NodeInfo.EVENT_TYPE_MINING:
        limit_min = data_loader.EventMiningBasicInfo_dict[user.level].limitMin
    elif event_type == NodeInfo.EVENT_TYPE_GOLD:
        limit_min = data_loader.EventGoldBasicInfo_dict[user.level].limitMin
    elif event_type == NodeInfo.EVENT_TYPE_JUNGLE:
        limit_min = data_loader.EventJungleBasicInfo_dict[user.level].limitMin
    elif event_type == NodeInfo.EVENT_TYPE_SCOUT:
        limit_min = data_loader.EventEnemyBasicInfo_dict[user.level].limitMin

    return limit_min


def _calc_candidate_event(data, node, now, is_lucky = True):
    """计算可能发生的事件
    根据节点状态决定
    Args:
        is_luck： 是否是随机事件
    Returns:
        candidate: list(event_type)
    """
    #如果节点正在战斗，不会发生随机事件
    if node.is_in_battle():
        return []

    if node.is_dependency():
        parent_basic_id = MapGraph().get_parent(node.basic_id)
        parent_id = NodeInfo.generate_id(data.id, parent_basic_id)
        parent = data.node_list.get(parent_id, True)
        #父节点（关键点）不是己方节点，附属点不会发生随机事件
        if not parent.is_own_side():
            return []

        #父节点有防御、地下城、演武场事件时，附属点不会发生随机事件
        if (parent.event_type == NodeInfo.EVENT_TYPE_DEFEND
                or parent.event_type == NodeInfo.EVENT_TYPE_DUNGEON
                or parent.event_type == NodeInfo.EVENT_TYPE_ARENA):
            return []

    #如果节点正在战斗，不会发生随机事件
    if node.is_in_battle():
        return []

    #节点如果已经发生随机事件，不会再次发生
    if node.is_event_arised():
        return []

    candidate = []
    if node.is_key_node() and not node.is_visible():
        for basic_id in MapGraph().get_neighbors(node.basic_id):
            #找出邻接点是可见的点
            neighbor_id = NodeInfo.generate_id(data.id, basic_id)
            neighbor = data.node_list.get(neighbor_id)
            if neighbor.is_visible():
                if neighbor.is_own_side() and not is_lucky:
                    #邻接点是己方点时会触发侦察事件
                    candidate.append(NodeInfo.EVENT_TYPE_SCOUT)

                if not is_lucky:
                    candidate.append(NodeInfo.EVENT_TYPE_DUNGEON)
                    candidate.append(NodeInfo.EVENT_TYPE_SEARCH)
                    candidate.append(NodeInfo.EVENT_TYPE_DEEP_MINING)
                    candidate.append(NodeInfo.EVENT_TYPE_HERMIT)
                else:
                    candidate.append(NodeInfo.EVENT_TYPE_ARENA)

    else:
        if node.is_own_city():
            #我方主城
            if is_lucky:
                flags = get_flags()
                if 'is_open_question_event' in flags:
                    candidate.append(NodeInfo.EVENT_TYPE_QUESTION)

        elif node.is_key_node():
            if node.is_own_side():
                #我方占据的关键点
                if is_lucky:
                    candidate.append(NodeInfo.EVENT_TYPE_UPGRADE)
                    if map_business.is_key_node_dangerous(data, node):
                        #己方边界点可能发生防御事件
                        candidate.append(NodeInfo.EVENT_TYPE_DEFEND)
                else:
                    if node.is_exploit_money():
                        candidate.append(NodeInfo.EVENT_TYPE_TAX)
                    elif node.is_exploit_food():
                        candidate.append(NodeInfo.EVENT_TYPE_FARM)
                    elif node.is_exploit_material():
                        candidate.append(NodeInfo.EVENT_TYPE_MINING)

                    candidate.append(NodeInfo.EVENT_TYPE_VISIT)

            elif node.is_enemy_side():
                #敌方占据的关键点
                if not node.is_rival_pvp_city() and not node.is_rival_dungeon():
                    if is_lucky:
                        candidate.append(NodeInfo.EVENT_TYPE_SPY)

        elif node.is_dependency():
            #附属点
            if not is_lucky:
                candidate.append(NodeInfo.EVENT_TYPE_JUNGLE)
                candidate.append(NodeInfo.EVENT_TYPE_GOLD)
            else:
                candidate.append(NodeInfo.EVENT_TYPE_WORLDBOSS)

    return candidate


def _roll_lucky_event(data, node, candidate, now):
    """计算节点上发生了什么随机事件
    Args:
        data[UserData]: 玩家所有数据
        node[NodeInfo]: 节点信息 readonly
        candidate[list(int)]: 节点上可以发生的随机事件类型列表
    Returns:
        (node_id, event_type)
    """
    #计算各个可能发生的随机事件的概率
    ratio = []
    for event in candidate:
        r = _calc_lucky_event_ratio(data, event, node, now)
        if len(ratio) > 0:
            r += ratio[-1]
        logger.debug("candidate event[node basic id=%d][event type=%d][ratio=%f]" %
                (node.basic_id, event, r))
        ratio.append(r)
        if r >= 1.0:
            break

    #roll
    random.seed()
    c = random.random()
    event_type = NodeInfo.EVENT_TYPE_INVALID
    for index, r in enumerate(ratio):
        if c < r:
            event_type = candidate[index]
            break

    logger.debug("roll event[node basic id=%d][roll=%f][choose type=%d]" %
            (node. basic_id, c, event_type))
    return (node.id, event_type)


def _calc_lucky_event_ratio(data, event_type, node, now, enemy_neighbor_count = 0):
    """计算当前情况下，指定类型的随机事件发生的概率
    Args:
        event_type[int]: 随机事件类型
        node[NodeInfo]: 节点信息, readonly
    """
    user = data.user.get(True)
    map = data.map.get()
    resource = data.resource.get()
    resource.update_current_resource(now)

    if event_type == NodeInfo.EVENT_TYPE_SCOUT:
        return _calc_event_scout_ratio(user, enemy_neighbor_count)
    elif event_type == NodeInfo.EVENT_TYPE_TAX:
        return _calc_event_tax_ratio(map, user, resource)
    elif event_type == NodeInfo.EVENT_TYPE_FARM:
        return _calc_event_farm_ratio(map, user, resource)
    elif event_type == NodeInfo.EVENT_TYPE_MINING:
        return _calc_event_mining_ratio(map, user)
    elif event_type == NodeInfo.EVENT_TYPE_GOLD:
        return _calc_event_gold_ratio(map, user)
    elif event_type == NodeInfo.EVENT_TYPE_JUNGLE:
        #获取所有dependence node个数
        own_dependency_count = _get_all_own_dependency_node_count(data)
        return _calc_event_jungle_ratio(user, own_dependency_count)
    elif event_type == NodeInfo.EVENT_TYPE_SEARCH:
        exploitation = data.exploitation.get()
        return _calc_event_search_ratio(user, exploitation, now)
    elif event_type == NodeInfo.EVENT_TYPE_DEEP_MINING:
        exploitation = data.exploitation.get()
        return _calc_event_deep_mining_ratio(user, exploitation, now)
    elif event_type == NodeInfo.EVENT_TYPE_HERMIT:
        exploitation = data.exploitation.get()
        return _calc_event_hermit_ratio(user, exploitation, now)
    elif event_type == NodeInfo.EVENT_TYPE_WORLDBOSS:
        worldboss = data.worldboss.get()
        return _calc_event_worldboss_ratio(user, worldboss, now)
    elif event_type == NodeInfo.EVENT_TYPE_ARENA:
        arena = data.arena.get()
        return _calc_event_arena_ratio(user, arena, now)
    elif event_type == NodeInfo.EVENT_TYPE_DUNGEON:
        dungeon = data.dungeon.get(user)
        return _calc_event_dungeon_ratio(user, dungeon, now)
    elif event_type == NodeInfo.EVENT_TYPE_UPGRADE:
        return _calc_event_upgrade_ratio(node, user)
    elif event_type == NodeInfo.EVENT_TYPE_DEFEND:
        return _calc_event_defend_ratio(user)
    elif event_type == NodeInfo.EVENT_TYPE_QUESTION:
        return _calc_event_question_ratio(map, user)
    elif event_type == NodeInfo.EVENT_TYPE_VISIT:
        return _calc_event_visit_ratio(map, user)
    elif event_type == NodeInfo.EVENT_TYPE_SPY:
        return _calc_event_spy_ratio(user)

    else:
        logger.warning("Invalid event[type=%d]" % event_type)
        raise Exception("Invalid event type")


def _is_event_unlocked(user, event_type):
    """随机事件是否解锁
    """
    return user.level >= data_loader.LuckyEventBasicInfo_dict[event_type].unlockMonarchLevel


def _get_all_enemy_neighbor_count(data):
    """获得我方总临近地城数目
    """
    node_list = data.node_list.get_all(True)
    count = 0
    for node in node_list:
        if node.is_own_side():
            continue
        for basic_id in MapGraph().get_neighbors(node.basic_id):
            neighbor_id = NodeInfo.generate_id(data.id, basic_id)
            neighbor = data.node_list.get(neighbor_id)
            if neighbor.is_own_side():
                count += 1
                break

    return count


def _calc_event_scout_ratio(user, enemy_neighbor_count):
    """计算侦察事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_SCOUT):
        return 0.0

    e = data_loader.EventEnemyBasicInfo_dict[user.level].outputExpectation

    p = 1.0 * e / enemy_neighbor_count
    return p


def _calc_event_tax_ratio(map, user, resource):
    """计算征税随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_TAX):
        return 0.0

    #由玩家等级决定征税之间收益的期望
    e = data_loader.EventTaxBasicInfo_dict[user.level].outputExpectation

    #通过玩家现有资源情况，动态调整期望 —— 平衡游戏经济系统
    #如果玩家金钱稀缺，给予补偿；如果玩家金钱充足，降低期望
    f = float(resource.money) / resource.money_capacity
    if f < float(data_loader.LuckyEventConfInfo_dict["tax_urgent_ratio"].value):
        e *= float(data_loader.LuckyEventConfInfo_dict["tax_urgent_coefficient"].value)
    elif f > float(data_loader.LuckyEventConfInfo_dict["tax_needless_ratio"].value):
        e *= float(data_loader.LuckyEventConfInfo_dict["tax_needless_coefficient"].value)

    p = 1.0 * e / map.own_exploit_money_amount
    return p


def _calc_event_farm_ratio(map, user, resource):
    """计算屯田随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_FARM):
        return 0.0

    e = data_loader.EventFarmBasicInfo_dict[user.level].outputExpectation

    f = float(resource.food) / resource.food_capacity
    if f < float(data_loader.LuckyEventConfInfo_dict["farm_urgent_ratio"].value):
        e *= float(data_loader.LuckyEventConfInfo_dict["farm_urgent_coefficient"].value)
    elif f > float(data_loader.LuckyEventConfInfo_dict["farm_needless_ratio"].value):
        e *= float(data_loader.LuckyEventConfInfo_dict["farm_needless_coefficient"].value)

    p = 1.0 * e / map.own_exploit_food_amount
    return p


def _calc_event_mining_ratio(map, user):
    """计算采矿随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_MINING):
        return 0.0

    e = data_loader.EventMiningBasicInfo_dict[user.level].outputExpectation

    p = 1.0 * e / map.own_exploit_material_amount
    #logger.debug("calc event mining ratio[e=%d][exploit_material_amount=%d][p=%f]"
    #        % (e, map.own_exploit_material_amount, p))
    return p


def _calc_event_gold_ratio(map, user):
    """计算金矿随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_GOLD):
        return 0.0

    if map.own_exploit_gold_amount == 0:
        return 0.0

    e = data_loader.EventGoldBasicInfo_dict[user.level].outputExpectation

    p = 1.0 * e / map.own_exploit_gold_amount
    return p


def _calc_event_upgrade_ratio(node, user):
    """计算升级随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_UPGRADE):
        return 0.0

    #和用户等级与关键点等级的差相关
    level_gap = user.level - node.level

    p = 0.0
    if level_gap not in data_loader.EventUpgradeBasicInfo_dict:
        return p

    p = float(data_loader.EventUpgradeBasicInfo_dict[level_gap].probability)
    return p


def _calc_event_defend_ratio(user):
    """计算防御随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_DEFEND):
        return 0.0

    p = float(data_loader.LuckyEventConfInfo_dict["defend_probability"].value)
    return p


def _calc_event_visit_ratio(map, user):
    """计算探访随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_VISIT):
        return 0.0

    i = map.event_daily_count
    t = map.event_visit_daily_count

    base = float(data_loader.LuckyEventConfInfo_dict["visit_probability_base"].value)
    delta = float(data_loader.LuckyEventConfInfo_dict["visit_probability_delta"].value)
    satisfy = float(data_loader.LuckyEventConfInfo_dict["visit_satisfy_count"].value)

    if t < satisfy:
        #当玩家一天启动的探访事件少于要求时，概率是不断上升的，保证出现机会
        p = base + delta * i
    else:
        #当玩家一天启动的探访事件达到游戏要求时，事件不再出现
        p = 0.0
    return p


def _calc_event_question_ratio(map, user):
    """计算问答随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_QUESTION):
        return 0.0

    i = map.event_daily_count
    t = map.event_question_daily_count

    base = float(data_loader.LuckyEventConfInfo_dict["question_probability_base"].value)
    delta = float(data_loader.LuckyEventConfInfo_dict["question_probability_delta"].value)
    satisfy = float(data_loader.LuckyEventConfInfo_dict["question_satisfy_count"].value)

    if t < satisfy:
        p = base + delta * i
    else:
        p = base
    return p


def _calc_event_jungle_ratio(user, own_dependency_count):
    """计算野怪随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_JUNGLE):
        return 0.0

    e = data_loader.EventJungleBasicInfo_dict[user.level].outputExpectation

    p = 1.0 * e / own_dependency_count
    return p


def _calc_event_spy_ratio(user):
    """计算谍报随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_SPY):
        return 0.0

    p = float(data_loader.LuckyEventConfInfo_dict["spy_probability"].value)
    return p


def _calc_event_dungeon_ratio(user, dungeon, now):
    """计算副本随机事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_DUNGEON):
        return 0.0

    #如果未开启 PVP，不允许副本
    if not user.allow_pvp:
        return 0.0

    if dungeon.is_able_to_open(now):
        return 1.0
    return 0.0


def _calc_event_arena_ratio(user, arena, now):
    """计算演武场副本随机事件发生的概率
       (其他的pvp副本都共用演武场的事件)
    """
    #if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_ARENA):
    #    return 0.0

    #如果未开启演武场功能 ，不允许副本
    #if not user.allow_pvp_arena:
    #    return 0.0

    #if arena.is_able_to_open(user, now):
    #    return 1.0
    return 0.0


def _calc_event_search_ratio(user, exploitation, now):
    """计算探索废墟事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_SEARCH):
        return 0.0

    if exploitation.is_able_to_open_search():
        return 1.0
    return 0.0


def _calc_event_deep_mining_ratio(user, exploitation, now):
    """计算勘探秘矿事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_DEEP_MINING):
        return 0.0

    if exploitation.is_able_to_open_deep_mining():
        return 1.0
    return 0.0


def _calc_event_hermit_ratio(user, exploitation, now):
    """计算探访隐士事件发生的概率
    """
    if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_HERMIT):
        return 0.0

    if exploitation.is_able_to_open_hermit():
        return 1.0
    return 0.0


def _calc_event_worldboss_ratio(user, worldboss, now):
    """计算世界boss随机事件发生的概率
    """
    #if not _is_event_unlocked(user, NodeInfo.EVENT_TYPE_WORLDBOSS):
    #    return 0.0

    #如果未开启世界boss
    #if not worldboss.is_arised():
    #    return 0.0

    #if not worldboss.is_node_exist():
    #    return 1.0
    return 0.0


def _get_all_own_dependency_node_count(data):
    """获得己方所有附属点的个数
    """
    node_list = data.node_list.get_all(True)
    count = 0
    for node in node_list:
        if node.is_dependency():
            parent_basic_id = MapGraph().get_parent(node.basic_id)
            parent_id = NodeInfo.generate_id(data.id, parent_basic_id)
            parent = data.node_list.get(parent_id, True)
            #父节点（关键点）是己方节点
            if parent.is_own_side():
                count += 1
    return count


def _default_arise_lucky_event(data, node, now, **kwargs):
    """默认的随机事件启动方法
    """
    event_type = kwargs['event_type']
    return node.arise_event(event_type, now)


def _default_clear_lucky_event(data, node, now, **kwargs):
    """默认的随机事件清除方法
    """
    return node.clear_event()


def _node_arise_event(data, node_id, event_type, now,
        change_nodes, new_items, new_mails):
    """节点上出现了随机事件
    Args:
        data[UserData]: 玩家所有数据
        node_id[int]: 节点 id
        event_type[int]: 随机事件类型
        now[int]: 当前时间戳
    """
    logger.debug("arise lucky event[type=%d]" % event_type)
    node = data.node_list.get(node_id)
    return EventHandler().arise(data, node, now, event_type = event_type,
            change_nodes = change_nodes, new_items = new_items, new_mails = new_mails)


def clear_lucky_event(data, node, now, change_nodes, new_items, new_mails, ret = Ret()):
    """清除随机事件
    1 随机事件出现未启动，超过 idletime
    2 随机事件启动未结束，超过 lifetime
    """
    #节点未发生随机事件
    if not node.is_event_arised():
        logger.warning("Node has no lucky event[basic id=%d]" % node.basic_id)
        ret.setup("NO_EVENT")
        return False
        #return True

    #如果节点上有世界boss时间，直接clear
    if node.is_worldboss_event_arised():
        return EventHandler().clear(data, node, now,
                change_nodes = change_nodes, new_items = new_items, new_mails = new_mails)

    if not node.is_event_launched():
        #事件未启动
        if node.is_event_over_idletime(now):
            return EventHandler().clear(data, node, now,
                    change_nodes = change_nodes, new_items = new_items, new_mails = new_mails)
    else:
        #事件已启动
        if node.is_event_over_lifetime(now):
            return EventHandler().timeout(data, node, now,
                    change_nodes = change_nodes, new_items = new_items, new_mails = new_mails)

    logger.warning("Clear lucky event error")
    return False


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))

    return open_flags


