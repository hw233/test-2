#coding:utf8
"""
Created on 2015-10-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 世界地图战斗事件逻辑
"""

import math
import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.map import MapGraph
from app.data.map import MapInfo
from app.data.node import NodeInfo
from app.data.visit import VisitInfo
from app.data.question import QuestionInfo
from app.data.dungeon import DungeonInfo
from app.business import mail as mail_business
from app.core.event import EventHandler
from app.rival_matcher import RivalMatcher
from app import log_formater


def init_map(data, pattern, now):
    """初始化地图
    创建新用户时，调用
    Args:
        data[UserData]: 用户数据
        pattern[int]: 初始化模式
        now[int]: 时间戳
    Returns:
        True
        False
    """
    user = data.user.get()

    #创建地图信息
    map = MapInfo.create(data.id)
    data.map.add(map)

    #创建问答, 副本信息
    question = QuestionInfo.create(data.id)
    data.question.add(question)
    dungeon = DungeonInfo.create(data.id)
    data.dungeon.add(dungeon)

    #创建所有节点信息
    for basic_id in MapGraph():
        node = NodeInfo.create(data.id, basic_id)
        data.node_list.add(node)

    #第一次刷新，占领自己主城
    own_basic_id = NodeInfo.get_own_node_basic_id()
    own_id = NodeInfo.generate_id(data.id, own_basic_id)
    own = data.node_list.get(own_id)
    own.update_own_city_level(user.level)

    ##开启主城邻接关键点
    #for basic_id in MapGraph().get_neighbors(own.basic_id):
    #    neighbor_id = NodeInfo.generate_id(data.id, basic_id)
    #    neighbor = data.node_list.get(neighbor_id)
    #    if not neighbor.is_visible():
    #        respawn_enemy_key_node(data, neighbor, now)

    ##为新刷出的敌方节点匹配敌人：只有 PVE
    #node_enemy_scores = [100, 101, 102]  #硬编码，初始三个node上固定敌人
    #i = 0
    #matcher = RivalMatcher(user.level, [data.id])
    #for node in data.node_list.get_all():
    #    if node.is_lack_enemy_detail():
    #        node.rival_score_min = node_enemy_scores[i]
    #        node.rival_score_max = node_enemy_scores[i]
    #        i = i + 1
    #        matcher.add_condition(data, node)
    #matcher.match(only_pve = True)

    ##为初次刷新的敌人添加 debuff 效果，为了让玩家初次攻击可以轻易取胜
    #for node in data.node_list.get_all():
    #    if node.is_enemy_complete():
    #        rival_id = node.rival_id
    #        rival = data.rival_list.get(rival_id)
    #        buff_id = data_loader.InitUserBasicInfo_dict[pattern].enemyBuffId
    #        rival.set_buff(buff_id)

    map.update_next_war_time(now)
    # map.update_next_luck_time(now)
    return True


def upgrade_key_node(data, node, now, use_gold = 0):
    """关键节点升级
    1 花费金钱粮草
    2 关键节点升一级
    """
    user = data.user.get(True)
    map = data.map.get()
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)

    level_add = max(1, int(math.ceil((user.level - node.level)/2.0)))

    #钱粮消耗
    money = data_loader.KeyNodeUpgradeBasicInfo_dict[node.level].costMoney
    food = data_loader.KeyNodeUpgradeBasicInfo_dict[node.level].costFood

    #如果金钱/粮草不够，使用元宝兑换
    money_gap = 0
    food_gap = 0
    if resource.money < money:
        money_gap = money - resource.money
    if resource.food < food:
        food_gap = food - resource.food
    cost_gold = resource.gold_exchange_resource(money = money_gap, food = food_gap)
    #if cost_gold != use_gold:
    #    logger.warning("Gold exchange resource failed[try cost gold=%d][real cost gold=%d]" %
    #            (use_gold, cost_gold))
    #    return False

    if not resource.cost_money(money) or not resource.cost_food(food):
        return False

    #更新己方资源信息 -
    map.update_for_own_exploit_amount(node, add = False)

    if not node.upgrade_key_node(user, now, level_add):
        return False

    #更新己方资源信息 +
    map.update_for_own_exploit_amount(node, add = True)

    if cost_gold > 0:
        log = log_formater.output_gold(data, -cost_gold, log_formater.UPGRADE_KEYNODE,
                "Upgrade keynode by gold", money = money_gap, food = food_gap, before_gold = original_gold)
        logger.notice(log)

    return True


def enemy_invade_key_node(data, node, now):
    """敌人入侵己方关键点，关键点目前仍然是我方占据
    1 节点上出现敌人信息
    """
    assert node.is_key_node() and node.is_own_side() and not node.is_rival_exist()
    logger.debug("Enemy invade key node[basic id=%d]" % node.basic_id)

    map = data.map.get()
    user = data.user.get(True)
    node.respawn_key_node_enemy(map, now, user.allow_pvp)

    # 更新可见的敌人信息 +
    map.update_for_key_node_enemy_type(node, add = True)
    return True


def protect_key_node_from_invasion(data, node, now):
    """保卫关键点成功：入侵的敌人被击败
    1 节点上敌人信息消失
    """
    assert node.is_key_node() and node.is_own_side() and node.is_rival_exist()
    logger.debug("Protect key node from invasion[basic id=%d]" % node.basic_id)

    map = data.map.get()

    # 更新可见的敌人信息 -
    map.update_for_key_node_enemy_type(node, add = False)
    node.clear_enemy()
    return True


def lost_key_node_of_invasion(data, node, lost_time, change_nodes, new_items, new_mails):
    """由于敌人入侵成功，丢失关键点
    1 敌人信息、资源信息不发生变化
    2 变更节点控制权状态
        a 如果是孤立节点，变为不可见
        b 否则，生成新敌方节点
    3 中止/清除所有附属点上的随机事件
    4 邻接的敌方关键点，如果是孤立节点，视野消失
    """
    logger.debug("Lost key node of invasion[basic id=%d]" % node.basic_id)
    map = data.map.get()
    user = data.user.get(True)

    #关键节点丢失邮件
    mail = mail_business.create_node_resource_defeat_mail(data, lost_time)
    new_mails.append(mail)
    mail.attach_node_info(node)
    mail.attach_battle_info(False)
    rival_id = node.id
    rival = data.rival_list.get(rival_id, True)
    mail.attach_enemy_info(rival)

    #1 更新己方占有的关键点信息 -
    #2 更新己方资源信息 -
    map.update_for_own_key_node(node, add = False)
    map.update_for_own_exploit_amount(node, add = False)

    if is_key_node_isolated(data, node):
        #清除节点
        if not clear_key_node(data, node):
            return False
    else:
        if not node.lost_key_node_of_invasion(lost_time):
            return False
    change_nodes.append(node)

    return _post_lost_key_node(data, map, node, lost_time, lost_time,
            change_nodes, new_items, new_mails)


def lost_key_node(data, node, lost_time, now,
        change_nodes, new_items, new_mails, is_dungeon = False):
    """
    失去关键节点：关键点从己方占有，变为敌方占有
    1 如果节点上有随机事件，中止/清除随机事件
    2 变更节点状态
        a 如果是孤立节点，变为不可见
        b 否则，生成新敌方节点
    3 中止/清除所有附属点上的随机事件
    4 邻接的敌方关键点，如果是孤立节点，视野消失
    """
    map = data.map.get()
    user = data.user.get(True)

    #关键节点丢失邮件，副本事件不发送邮件
    if not is_dungeon:
        mail = mail_business.create_node_resource_defeat_mail(data, lost_time)
        new_mails.append(mail)
        mail.attach_node_info(node)
        mail.attach_battle_info(False)

    if node.is_event_arised():
        if not _stop_lucky_event_on_node(data, node, lost_time, now,
                change_nodes, new_items, new_mails):
            return False

    #清除节点
    if not clear_key_node(data, node):
        return False
    #当关键点不是孤立的时候，是可见的，生成新的敌方关键点
    if not is_key_node_isolated(data, node) or is_dungeon:
        if not respawn_enemy_key_node(data, node, lost_time, is_dungeon):
            return False

    change_nodes.append(node)

    return _post_lost_key_node(data, map, node, lost_time, now, change_nodes, new_items, new_mails)


def _stop_lucky_event_on_node(data, node, end_time, now,
        change_nodes, new_items, new_mails):
    """节点发生变动，清除节点上的随机事件
    """
    if not node.is_event_launched():
        #事件未启动
        return EventHandler().clear(data, node, now,
                change_nodes = change_nodes, new_items = new_items, new_mails = new_mails)
    else:
        return EventHandler().stop(data, node, now,
                change_nodes = change_nodes, end_time = end_time, new_items = new_items,
                new_mails = new_mails)


def _post_lost_key_node(data, map, node, lost_time, now, change_nodes, new_items, new_mails):
    """丢失邻接节点的后续处理
    1 对附属点的影响: 清除附属点上随机事件
    2 对邻接关键点的影响: 邻接的敌方关键点，如果是孤立节点，视野消失
    """
    #对附属点的影响
    for basic_id in MapGraph().get_children(node.basic_id):
        child_id = NodeInfo.generate_id(data.id, basic_id)
        child = data.node_list.get(child_id)
        #如果附属点正在发生战斗，不处理，跳过
        if child.is_in_battle():
            continue

        #中止/清除所有附属点上的随机事件
        if child.is_event_arised():
            if not _stop_lucky_event_on_node(data, child, lost_time, now,
                    change_nodes, new_items, new_mails):
                return False
        assert not child.is_dependency_active()

    ##对邻接关键点的影响
    #for basic_id in MapGraph().get_neighbors(node.basic_id):
    #    neighbor_id = NodeInfo.generate_id(data.id, basic_id)
    #    neighbor = data.node_list.get(neighbor_id)

    #    #如果邻接节点发生副本事件，视野不受影响
    #    if neighbor.event_type == NodeInfo.EVENT_TYPE_DUNGEON:
    #        continue
    #    #如果邻接点发生演武场事件，视野不受影响
    #    elif neighbor.event_type == NodeInfo.EVENT_TYPE_ARENA:
    #        continue

    #    #如果邻接点正发生战斗事件（委任），视野不受影响
    #    if neighbor.is_in_battle():
    #        continue

    #    #邻接敌方孤立关键点，视野消失，清除节点
    #    if neighbor.is_enemy_side() and is_key_node_isolated(data, neighbor):
    #        #清除随机事件
    #        if neighbor.is_event_arised():
    #            if not _stop_lucky_event_on_node(data, neighbor, lost_time, now,
    #                    change_nodes, new_items, new_mails):
    #                return False
    #        if not clear_key_node(data, neighbor):
    #            return False
    #        change_nodes.append(neighbor)

    #减少领地数
    map.lost_node(1)

    return True


def dominate_key_node(data, node, change_nodes, now):
    """占领关键节点，关键节点从敌方占据，变为我方占据
    1 占领关键节点
    2 开启邻接关键节点
    """
    logger.debug("Dominate key node[basic id=%d]" % node.basic_id)

    map = data.map.get()

    #更新可见关键点敌人类型信息 -
    map.update_for_key_node_enemy_type(node, add = False)

    #占领关键节点
    if not node.dominate_key_node(map, now):
        return False
    change_nodes.append(node)

    #更新己方占有的关键点信息 +
    #更新己方资源信息 +
    map.update_for_own_key_node(node, add = True)
    map.update_for_own_exploit_amount(node, add = True)

    return _post_dominate_key_node(data, node, map, change_nodes, now)


def _post_dominate_key_node(data, node, map, change_nodes, now):
    """占领关键点的后续处理
    1 开启邻接不可见关键点
    """
    user = data.user.get(True)

    ##邻接关键点，如果是不可见的，开启，生成敌方关键点
    #for basic_id in MapGraph().get_neighbors(node.basic_id):
    #    neighbor_id = NodeInfo.generate_id(data.id, basic_id)
    #    neighbor = data.node_list.get(neighbor_id)
    #    if not neighbor.is_visible():
    #        respawn_enemy_key_node(data, neighbor, now)
    #        change_nodes.append(neighbor)

    #增加领地数
    map.occupy_node(1)

    return True


def forward_dungeon_key_node(data, node, now):
    """副本关键点，进度前进，开启下一关
    """
    logger.debug("Forward dungeon key node")
    #更新可见的敌人信息 -
    map = data.map.get()
    map.update_for_key_node_enemy_type(node, add = False)

    dungeon = data.dungeon.get()
    #仅仅重新生成敌人信息
    node.respawn_key_node_enemy(map, now, False, dungeon)

    #更新可见的敌人信息 +
    map.update_for_key_node_enemy_type(node, add = True)
    return True


def close_dungeon_key_node(data, node, change_nodes, now):
    """关闭副本节点，失去视野
    """
    if not clear_key_node(data, node):
        return False

    change_nodes.append(node)
    return True


def close_arena_key_node(data, node, lost_time, now,
        change_nodes, new_items, new_mails):
    """
    关闭演武场节点，失去视野
    """
    #清除节点
    if not clear_key_node(data, node):
        return False

    change_nodes.append(node)
    return True


def close_spy_key_node(data, node, change_nodes, now):
    """
    关闭谍报节点，失去视野
    """
    #清除节点
    if not clear_key_node(data, node):
        return False

    change_nodes.append(node)
    return True


def close_offline_exploit_key_node(data, node, change_nodes):
    """
    关闭离线事件的几个开采节点（探索废墟/秘矿/探访隐士），失去视野
    """
    #清除节点
    if not clear_key_node(data, node):
        return False

    change_nodes.append(node)
    return True


def clear_key_node(data, node):
    """清除关键点
    我方关键点 -> 视野外关键点
    我方关键点 -> 视野外关键点
    """
    assert node.is_key_node()
    logger.debug("Clear key node[basic id=%d]" % node.basic_id)

    map = data.map.get()

    if node.is_own_side():
        #1 更新己方占有的关键点信息 -
        #2 更新己方资源信息 -
        map.update_for_own_key_node(node, add = False)
        map.update_for_own_exploit_amount(node, add = False)

    if node.is_rival_exist():
        #更新可见的敌人信息 -
        map.update_for_key_node_enemy_type(node, add = False)

    #更新所有可见关键点信息 -
    map.update_for_key_node_type(node, add = False)

    return node.clear_key_node()


def respawn_enemy_key_node_custom(data, node, now,
        exploit_type, exploit_level, rival_type, rival_score_min, rival_score_max):
    """生成指定的敌方关键点
    指定资源信息和敌人信息
    """
    logger.debug("Respawn enemy key node custom[basic id=%d]" % node.basic_id)

    map = data.map.get()
    user = data.user.get(True)
    if not node.respawn_key_node_custom(exploit_type, exploit_level,
            rival_type, rival_score_min, rival_score_max, now):
        return False

    #1 更新可见关键点类型信息 +
    #2 更新可见关键点敌人类型信息 +
    map.update_for_key_node_type(node, add = True)
    map.update_for_key_node_enemy_type(node, add = True)
    return True


def respawn_enemy_key_node(data, node, now, is_dungeon = False):
    """重新生成敌方关键点
    视野外关键点 -> 敌方关键点
    """
    logger.debug("Respawn enemy key node[basic id=%d]" % node.basic_id)

    map = data.map.get()
    user = data.user.get(True)
    dungeon = None
    arena = None
    if is_dungeon:
        dungeon = data.dungeon.get()

    if not node.respawn_key_node(map, user, now, user.allow_pvp, dungeon):
        return False

    #1 更新可见关键点类型信息 +
    #2 更新可见关键点敌人类型信息 +
    map.update_for_key_node_type(node, add = True)
    map.update_for_key_node_enemy_type(node, add = True)
    return True


def rematch_key_node(data, node, now):
    """
    重新匹配关键点，保持敌人的类型不变
    """
    if not node.is_able_to_rematch(now):
        return False

    map = data.map.get()
    user = data.user.get(True)

    #更新可见关键点类型信息 -
    map.update_for_key_node_type(node, add = False)

    if not node.rematch_key_node(map, user, now):
        return False

    #更新可见关键点类型信息 +
    map.update_for_key_node_type(node, add = True)
    return True


def abandon_key_node(data, node, now, change_nodes):
    """主动丢弃己方关键点:键点从己方占有，变为敌方占有
       1.如果有可见附属点，不能丢弃
       2.如果node上在战斗或者有随机事件，不能丢弃
       3.变更节点状态
        a 如果是孤立节点，变为不可见
        b 否则，生成新敌方节点
       4.邻接的敌方关键点，如果是孤立节点，视野消失
    """
    if not node.is_able_to_abandon(now):
        logger.debug("node is not able to abandon[basic id=%d]" % node.basic_id) 
        return False

    #如果有附属点则不可丢弃
    for basic_id in MapGraph().get_children(node.basic_id):
        child_id = NodeInfo.generate_id(data.id, basic_id)
        child = data.node_list.get(child_id)

        if child.is_dependency_active():
            logger.debug("child dependency node is active[basic id=%d]" % child.basic_id) 
            return False

    map = data.map.get()
    user = data.user.get(True)

    #清除节点
    if not clear_key_node(data, node):
        logger.debug("clear key node failed[basic id=%d]" % node.basic_id) 
        return False

    #当关键点不是孤立的时候，是可见的，生成新的敌方关键点
    #is_dungeon = False
    #if not is_key_node_isolated(data, node):
    #    if not respawn_enemy_key_node(data, node, now, is_dungeon):
    #        return False

    change_nodes.append(node)

    new_items = []
    new_mails = []

    return _post_lost_key_node(data, map, node, now, now, change_nodes, new_items, new_mails)


def is_key_node_isolated(data, node):
    """
    计算关键点是否孤立：相邻的没有己方关键点
    """
    assert node.is_key_node()

    for basic_id in MapGraph().get_neighbors(node.basic_id):
        neighbor_id = NodeInfo.generate_id(data.id, basic_id)
        neighbor = data.node_list.get(neighbor_id, True) #readonly
        logger.debug("node has neighbor[basic id=%d]"
                "[neighbor basic id=%d][neighbor own side=%r]"
                % (node.basic_id, neighbor.basic_id, neighbor.is_own_side()))
        if neighbor.is_own_side():
            return False

    return True


def is_key_node_dangerous(data, node):
    """
    判断关键点是否处于危险状态
    危险是指：
    1 我方占领的资源点
    2 和敌方关键点邻接
    """
    assert node.is_key_node()
    logger.debug("check dangerous[basic id=%d][status=%d]" %
            (node.basic_id, node.status))

    if not node.is_own_side():
        return False

    for basic_id in MapGraph().get_neighbors(node.basic_id):
        neighbor_id = NodeInfo.generate_id(data.id, basic_id)
        neighbor = data.node_list.get(neighbor_id, True)
        if not neighbor.is_own_side():
            logger.debug("node dangerous[basic id=%d]" % node.basic_id)
            return True

    logger.debug("node not dangerous[basic id=%d]" % node.basic_id)
    return False


def check_map_data(data):
    """检查 map 数据是否正确
    """
    #己方占领的关键点信息
    own_key_lost_weight = 0.0
    own_key_weight = 0.0

    #所有己方资源信息
    own_exploit_money_amount = 0.0
    own_exploit_food_amount = 0.0
    own_exploit_material_amount = 0.0
    own_exploit_gold_amount = 0.0

    #所有可见的关键点信息
    total_key_exploit_money_weight = 0.0
    total_key_exploit_food_weight = 0.0
    total_key_exploit_material_weight = 0.0

    #所有关键点上的敌人信息
    total_key_enemy_pve_weight = 0.0
    total_key_enemy_pvp_city_weight = 0.0
    total_key_enemy_pvp_resource_weight = 0.0

    own_node = []
    rival_node = []

    for node in data.node_list.get_all(True):
        #print ("check node[basic id=%d][type=%d][status=%d]" %
        #         (node.basic_id, node.type, node.status))

        if not node.is_key_node():
            # print "not key node, do nothing"
            continue

        if not node.is_visible():
            # print "not visible key node, do nothing"
            continue

        if node.is_own_side():
            own_node.append(node.basic_id)
            assert node.exploit_level == node.level

            #己方占领的关键点
            if (node.is_exploit_money()
                    or node.is_exploit_food()
                    or node.is_exploit_material()):
                key = node.exploit_level
            else:
                raise Exception("Invalid exploit type[type=%d]" % node.exploit_type)
            own_key_lost_weight += data_loader.KeyNodeMatchBasicInfo_dict[key].lostWeight
            own_key_weight += data_loader.KeyNodeMatchBasicInfo_dict[key].appearWeight

            #己方占领资源信息
            if node.is_exploit_money():
                reserves = data_loader.MoneyExploitationBasicInfo_dict[
                        node.exploit_level].reserves
                own_exploit_money_amount += reserves
            elif node.is_exploit_food():
                reserves = data_loader.FoodExploitationBasicInfo_dict[
                        node.exploit_level].reserves
                own_exploit_food_amount += reserves
            elif node.is_exploit_material():
                num_min = data_loader.MaterialExploitationBasicInfo_dict[
                        node.exploit_level].numMin
                num_max = data_loader.MaterialExploitationBasicInfo_dict[
                        node.exploit_level].numMax
                #assert node.exploit_reserve >= num_min and node.exploit_reserve <= num_max
                own_exploit_material_amount += node.exploit_reserve
            else:
                raise Exception("Invalid exploit type[type=%d]" % node.exploit_type)

            count = len(data_loader.MapNodeBasicInfo_dict[node.basic_id].children)
            assert count > 0
            reserves = data_loader.GoldExploitationBasicInfo_dict[
                    node.exploit_level].reserves * count
            own_exploit_gold_amount += reserves

        if node.is_rival_exist() and not node.is_rival_dungeon():
            rival_node.append(node.basic_id)

            #所有关键点上的敌人信息
            rival_id = node.rival_id
            rival = data.rival_list.get(rival_id)
            assert rival is not None

            key = "%s_%s" % (node.rival_type, node.level)
            weight = data_loader.EnemyMatchBasicInfo_dict[key].weight

            if node.is_rival_pve():
                total_key_enemy_pve_weight += weight
            elif node.is_rival_pvp_city():
                total_key_enemy_pvp_city_weight += weight
            elif node.is_rival_pvp_resource():
                total_key_enemy_pvp_resource_weight += weight
            else:
                raise Exception("Invalid enemy type[type=%d]" % node.rival_type)

        #所有可见的关键点信息
        appear_weight = data_loader.KeyNodeMatchBasicInfo_dict[node.exploit_level].appearWeight
        if node.is_exploit_money():
            total_key_exploit_money_weight += appear_weight
        elif node.is_exploit_food():
            total_key_exploit_food_weight += appear_weight
        elif node.is_exploit_material():
            total_key_exploit_material_weight += appear_weight
        elif node.is_exploit_random_item() or node.is_exploit_enchant_material() or node.is_exploit_hero_star_soul():
            pass
        else:
            raise Exception("Invalid exploit type[type=%d]" % node.exploit_type)

    logger.debug("Node OWN[%s]" % own_node)
    logger.debug("Node RIVAL[%s]" % rival_node)

    map = data.map.get(True)
    # logger.debug("map own info[%f][%f]" % (map.own_key_lost_weight, map.own_key_weight))
    # logger.debug("calc result[%f][%f]" % (own_key_lost_weight, own_key_weight))
    if map.own_key_lost_weight != own_key_lost_weight:
        logger.warning("wrong data[own_key_lost_weight][%f!=%f]" %
                (map.own_key_lost_weight, own_key_lost_weight))
    if map.own_key_weight != own_key_weight:
        logger.warning("wrong data[own_key_weight][%f!=%f]" %
                (map.own_key_weight, own_key_weight))

    # logger.debug("map exploit info[%d][%d][%d][%d]" %
    #     (map.own_exploit_money_amount,
    #         map.own_exploit_food_amount,
    #         map.own_exploit_material_amount,
    #         map.own_exploit_gold_amount))
    # logger.debug("calc result[%f][%f][%f][%f]" %
    #         (own_exploit_money_amount,
    #             own_exploit_food_amount,
    #             own_exploit_material_amount,
    #             own_exploit_gold_amount))

    if map.own_exploit_money_amount != own_exploit_money_amount:
        logger.warning("wrong data[own_exploit_money_amount][%d!=%f]" %
                (map.own_exploit_money_amount, own_exploit_money_amount))
    if map.own_exploit_food_amount != own_exploit_food_amount:
        logger.warning("wrong data[own_exploit_food_amount][%d!=%f]" %
                (map.own_exploit_food_amount, own_exploit_food_amount))
    if map.own_exploit_material_amount != own_exploit_material_amount:
        logger.warning("wrong data[own_exploit_material_amount][%d!=%f]" %
                (map.own_exploit_material_amount, own_exploit_material_amount))
    if map.own_exploit_gold_amount != own_exploit_gold_amount:
        logger.warning("wrong data[own_exploit_gold_amount][%d!=%f]" %
                (map.own_exploit_gold_amount, own_exploit_gold_amount))

    # logger.debug("map node type info[%f][%f][%f]" %
    #     (map.total_key_exploit_money_weight,
    #         map.total_key_exploit_food_weight,
    #         map.total_key_exploit_material_weight))
    # logger.debug("calc result[%f][%f][%f]" %
    #         (total_key_exploit_money_weight,
    #             total_key_exploit_food_weight,
    #             total_key_exploit_material_weight))

    if map.total_key_exploit_money_weight != total_key_exploit_money_weight:
        logger.warning("wrong data[total_key_exploit_money_weight][%f!=%f]" %
                (map.total_key_exploit_money_weight, total_key_exploit_money_weight))
    if map.total_key_exploit_food_weight != total_key_exploit_food_weight:
        logger.warning("wrong data[total_key_exploit_food_weight][%f!=%f]" %
                (map.total_key_exploit_food_weight, total_key_exploit_food_weight))
    if map.total_key_exploit_material_weight != total_key_exploit_material_weight:
        logger.warning("wrong data[total_key_exploit_material_weight][%f!=%f]" %
                (map.total_key_exploit_material_weight, total_key_exploit_material_weight))

    # logger.debug("map enemy info[%f][%f][%f]" %
    #     (map.total_key_enemy_pve_weight,
    #         map.total_key_enemy_pvp_city_weight,
    #         map.total_key_enemy_pvp_resource_weight))
    # logger.debug("calc result[%f][%f][%f]" %
    #         (total_key_enemy_pve_weight,
    #             total_key_enemy_pvp_city_weight,
    #             total_key_enemy_pvp_resource_weight))
    if map.total_key_enemy_pve_weight != total_key_enemy_pve_weight:
        logger.warning("wrong data[total_key_enemy_pve_weight][%f!=%f]" %
                (map.total_key_enemy_pve_weight, total_key_enemy_pve_weight))
    if map.total_key_enemy_pvp_city_weight != total_key_enemy_pvp_city_weight:
        logger.warning("wrong data[total_key_enemy_pvp_city_weight][%f!=%f]" %
                (map.total_key_enemy_pvp_city_weight, total_key_enemy_pvp_city_weight))
    if map.total_key_enemy_pvp_resource_weight != total_key_enemy_pvp_resource_weight:
        logger.warning("wrong data[total_key_enemy_pvp_resource_weight][%f!=%f]" %
                (map.total_key_enemy_pvp_resource_weight, total_key_enemy_pvp_resource_weight))

    repair_map_data(data,
        own_key_lost_weight,
        own_key_weight,
        own_exploit_money_amount,
        own_exploit_food_amount,
        own_exploit_material_amount,
        own_exploit_gold_amount,
        total_key_exploit_money_weight,
        total_key_exploit_food_weight,
        total_key_exploit_material_weight,
        total_key_enemy_pve_weight,
        total_key_enemy_pvp_city_weight,
        total_key_enemy_pvp_resource_weight)


def repair_map_data(data,
        own_key_lost_weight,
        own_key_weight,
        own_exploit_money_amount,
        own_exploit_food_amount,
        own_exploit_material_amount,
        own_exploit_gold_amount,
        total_key_exploit_money_weight,
        total_key_exploit_food_weight,
        total_key_exploit_material_weight,
        total_key_enemy_pve_weight,
        total_key_enemy_pvp_city_weight,
        total_key_enemy_pvp_resource_weight):

    map = data.map.get(True)
    map.own_key_lost_weight = own_key_lost_weight
    map.own_key_weight = own_key_weight
    map.own_exploit_money_amount = int(own_exploit_money_amount)
    map.own_exploit_food_amount = int(own_exploit_food_amount)
    map.own_exploit_material_amount = int(own_exploit_material_amount)
    map.own_exploit_gold_amount = int(own_exploit_gold_amount)
    map.total_key_exploit_money_weight = total_key_exploit_money_weight
    map.total_key_exploit_food_weight = total_key_exploit_food_weight
    map.total_key_exploit_material_weight = total_key_exploit_material_weight
    map.total_key_enemy_pve_weight = total_key_enemy_pve_weight
    map.total_key_enemy_pvp_city_weight = total_key_enemy_pvp_city_weight
    map.total_key_enemy_pvp_resource_weight = total_key_enemy_pvp_resource_weight

