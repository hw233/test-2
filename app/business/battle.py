#coding:utf8
"""
Created on 2015-09-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief:  战斗相关业务逻辑
"""

import base64
from utils import logger
from datalib.data_loader import data_loader
from app.data.hero import HeroInfo
from app.data.node import NodeInfo
from app.data.battle import BattleInfo
from app.data.map import MapGraph
from app.core import reward as reward_module
from app.core import battle as battle_module
from app.business import mail as mail_business
from app.business import map as map_business
from app.business import hero as hero_business
from app.business import item as item_business
from app.business import user as user_business
from app.business import dungeon as dungeon_business
from app.business import arena as arena_business
from app.business import melee as melee_business
from app.business import defend as defend_business
from app.business import jungle as jungle_business
from app.business import spy as spy_business
from app.business import anneal as anneal_business
from app.business import worldboss as worldboss_business
from app.business import account as account_business
from app import log_formater


def start_battle(data, node, rival, mail, teams, heroes, now, force = False, appoint = False):
    """开始战斗
    1 消耗粮草、兵力
    2 如果战斗地点是资源点，计算可以抢夺的资源
    3 计算战利品
    Args:
        data
        node[NodeInfo]: 战斗发生节点
        rival[RivalInfo]: 敌方阵容信息
        heroes[list(HeroInfo)]: 我方参战英雄信息
        now
        force
        appoint:委任
    """
    node_basic_id = 0
    #if node == None:
    #    #通过邮件复仇、试炼场,不存在node
    #    node_basic_id = 0 #0表示主城
    #    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    #else:
    #    node_basic_id = node.basic_id
    #    node_id = node.id
    node_basic_id = node.basic_id
    node_id = node.id

    user = data.user.get()
    battle = data.battle_list.get(node_id)
    if battle is None:
        battle = BattleInfo.create(node_id, data.id)
        data.battle_list.add(battle)

    if not battle.is_able_to_start():
        logger.warning("Not able to start battle[battle node id=%d]" % node_id)
        return True    #为避免网络失败请求重复发，此处返回true

    if rival is None:
        logger.warning("Rival not exist")
        return False

    #队伍是否可以参战
    for team in teams:
        if not team.is_able_to_join_battle():
            logger.warning("Team not able to join battle[index=%d]" % team.index)
            return False

    battle.set_is_appoint(appoint)

    need_food = 0
    if not rival.is_melee_player():
        #消耗粮草
        resource = data.resource.get()
        resource.update_current_resource(now)
        need_food = _calc_food_consume(heroes)
        if not resource.cost_food(need_food):
            return False

        #消耗兵力
        if not _consume_soldier(data, battle, now, heroes, force):
            return False

    #启动相关随机事件
    if node is not None and \
        node.event_type not in (
            NodeInfo.EVENT_TYPE_ARENA,
            NodeInfo.EVENT_TYPE_EXPAND_DUNGEON,
            NodeInfo.EVENT_TYPE_WORLDBOSS):
        logger.debug("node[basic id=%d][event type=%d]" % (node.basic_id, node.event_type))
        if node_basic_id != 0 and node.is_event_arised() and not _start_related_event(data, node, now):
            return False

    #计算战利品
    reward_money = 0
    reward_food = 0
    reward_items = []

    trainer = data.trainer.get(True)
    if rival.is_arena_player() and trainer.daily_arena_num > 120:
        #当天刷演武场次数超过120天，不再发奖励
        reward_hero_exp = rival.reward_hero_exp
        reward_user_exp = 0
        pass
    else:
        if node is not None:
            #战利品1：抢夺资源点
            if (node.is_key_node() and
                    node.event_type != NodeInfo.EVENT_TYPE_DUNGEON and
                    node.event_type != NodeInfo.EVENT_TYPE_ARENA and
                    node.event_type != NodeInfo.EVENT_TYPE_EXPAND_DUNGEON):
                (reward_money, reward_food, reward_item_count) = node.calc_grab_income()
                if reward_item_count > 0:
                    reward_items = reward_module.random_exploit_material(
                            node.exploit_level, reward_item_count)

            #战利品2：野怪战利品
            elif node.is_dependency() and node.event_type == NodeInfo.EVENT_TYPE_JUNGLE:
                (reward_money, reward_food) = node.calc_jungle_income()
        else:
            #战利品1：资源奖励
            if rival.is_anneal_rival():
                (reward_money, reward_food) = anneal_business.calc_resource_income(rival.level)

        #战利品3：击败敌人奖励
        reward_money += rival.reward_money
        reward_food += rival.reward_food
        reward_hero_exp = rival.reward_hero_exp
        if rival.is_arena_player() or rival.is_worldboss_rival():
            reward_user_exp = 0
        else:
            reward_user_exp = rival.reward_user_exp
        reward_items.extend(rival.get_reward_items())

        #战利品4：胜利随机物品奖励
        if node.event_type != NodeInfo.EVENT_TYPE_EXPAND_DUNGEON:
            if node is not None and node.is_dependency():
                gifts = reward_module.random_jungle_gift(rival.level)
            else:
                gifts = reward_module.random_battle_gift(rival.level)
            reward_items.extend(gifts)

    if node is not None:
        #设置战斗状态
        node.set_in_battle()

        #攻打资源点和敌主城，会使所有保护罩失效
        if not node.is_able_to_battle_in_protect():
            for node_info in data.node_list.get_all():
                if node_info.is_in_protect(now):
                    node_info.clear_in_protect()
                if node_info.is_own_city():
                    user.set_in_protect(False)

    battle.set_food_consume(need_food)
    battle.set_reward(reward_money, reward_food,
            reward_hero_exp, reward_user_exp, reward_items)

    return battle.start(node, rival, mail, teams, heroes, now, user.vip_level)


def win_battle(data, node, enemy_soldier_info, own_soldier_info,
        change_nodes, now, new_arena_records = [], 
        is_legendcity = False, is_unionboss = False, is_plunder = False):
    """战斗胜利
    1 获得战利品
    2 获得经验：用户经验，英雄经验
    3 返还存活士兵
    4 更新统计信息
    5 结算节点影响
    Args:
        change_nodes[list(NodeInfo) out]: 发生变化的节点列表
    """
    if node == None:
        #通过邮件复仇、试炼场,不存在node
        node_id = NodeInfo.generate_id(data.id, 0)     #0表示主城
    else:
        node_id = node.id

    battle = data.battle_list.get(node_id)
    if battle is None:
        logger.warning("Battle is not exist[battle node id=%d]" % node_id)
        return False

    node = data.node_list.get(node_id)
    rival = data.rival_list.get(battle.rival_id)

    force = False
    #如果dependence节点所在key node已不可见，强制结束战斗
    if node is not None and node.is_dependency():
        parent_basic_id = MapGraph().get_parent(node.basic_id)
        parent_id = NodeInfo.generate_id(data.id, parent_basic_id)
        parent = data.node_list.get(parent_id, True)
        if not parent.is_visible() or not parent.is_own_side():
            force = True
    if not battle.is_able_to_finish(now, force):
        logger.warning("Not able to finish battle[battle node id=%d][battle rival id=%d]" %
                (battle.node_id, battle.rival_id))
        return False

    #获得战利品
    resource = data.resource.get()
    resource.update_current_resource(now)
    resource.gain_money(battle.reward_money)
    resource.gain_food(battle.reward_food)
    if not item_business.gain_item(data, battle.get_reward_items(), "win battle", log_formater.WIN_BATTLE):
        return False

    if not rival.is_melee_player():
        #返还己方存活士兵
        if not _reclaim_soldier(data, battle, now, own_soldier_info):
            return False

    #用户获得经验,扣除政令
    if 'is_battle_cost_energy' in account_business.get_flags():
        energy = data.energy.get()
        energy.update_current_energy(now)
        if not energy.cost_energy(battle.reward_user_exp, None, now):
            return False

        if not user_business.level_upgrade(data, battle.reward_user_exp, now, "exp win battle", log_formater.EXP_WIN_BATTLE):
            return False

    #参战英雄获得经验
    heroes_id = battle.get_battle_hero()
    exp = int(battle.reward_hero_exp / len(heroes_id)) if len(heroes_id) > 0 else 0
    for hero_id in heroes_id:
        hero = data.hero_list.get(hero_id)
        if not hero_business.level_upgrade(data, hero, exp, now):
            return False

    #更新统计信息
    if not _update_statistics(data, battle, True, rival, node,
            enemy_soldier_info, own_soldier_info):
        return False

    #如果是复仇成功，更新邮件
    mail_id = battle.mail_id
    if mail_id != 0:
        mail = data.mail_list.get(mail_id)
        if not mail_business.use_mail_to_revenge_succeed(data, mail, now):
            return False
        rival.clear()

    #如果是演武场的对手
    if rival.is_arena_player():
        arena = data.arena.get()
        record = arena_business.calc_arena_battle_finish(data, arena, True, rival)
        new_arena_records.append(record)
        rival.clear()

    #如果是乱斗场的对手
    if rival.is_melee_player():
        melee = data.melee.get()
        record = melee_business.calc_melee_battle_finish(data, melee, True, rival)
        new_arena_records.append(record)
        rival.clear()

    #如果是试炼场
    if rival.is_anneal_rival():
        rival.clear()

    #如果是世界boss
    if rival.is_worldboss_rival():
        rival.clear()

    if (not is_legendcity and not is_unionboss and not is_plunder and
            node.event_type not in (
                NodeInfo.EVENT_TYPE_EXPAND_DUNGEON,
                NodeInfo.EVENT_TYPE_ARENA,
                NodeInfo.EVENT_TYPE_WORLDBOSS) and
            node.basic_id != 0 and
            not _update_node_of_win_battle(data, node, now, change_nodes)):
        logger.warning("Update node of win battle failed")
        return False

    #取消战斗状态
    if node is not None:
        node.clear_in_battle()

    return battle.finish()


def _update_node_of_win_battle(data, node, now, change_nodes):
    """战斗胜利的对节点的影响
    1 如果节点上有随机事件，结束（成功）随机事件
    2 如有没有随机事件，占领关键点
    """
    if node is None:
        return True

    if node.is_event_arised():
        #如果有随机事件，结束相关随机事件
        return _finish_related_event_succeed(data, node, now, change_nodes)
    else:
        #否则，占领节点
        if node.is_key_node():
            change_nodes.append(node)
            map = data.map.get()
            if map.is_able_to_occupy_more():
                return map_business.dominate_key_node(data, node, change_nodes, now)
            else:
                return node.clear_key_node()

    logger.warning("Unexpected node[node basic id=%d]" % node.basic_id)
    return False


def lose_battle(data, node, now, enemy_soldier_info = [], own_soldier_info = [],
        change_nodes = [], new_items = [], new_mails = [], new_arena_records = []):
    """战斗失败
    1 返还存活士兵
    2 更新统计信息
    3 结算节点影响
    """
    if node == None:
        #通过邮件复仇,不存在node
        node_id = NodeInfo.generate_id(data.id, 0)     #0表示主城
    else:
        node_id = node.id

    battle = data.battle_list.get(node_id)
    if battle is None:
        logger.warning("Battle is not exist[battle node id=%d]" % node_id)
        return False

    rival = data.rival_list.get(battle.rival_id)

    force = False
    #如果dependence节点所在key node已不可见，强制结束战斗
    if node is not None and node.is_dependency():
        parent_basic_id = MapGraph().get_parent(node.basic_id)
        parent_id = NodeInfo.generate_id(data.id, parent_basic_id)
        parent = data.node_list.get(parent_id, True)
        if not parent.is_visible() or not parent.is_own_side():
            force = True
    if not battle.is_able_to_finish(now, force):
        logger.warning("Not able to finish battle[battle node id=%d][battle rival id=%d]" %
                (battle.node_id, battle.rival_id))
        return False

    if not rival.is_melee_player():
        if not _reclaim_soldier(data, battle, now, own_soldier_info):
            return False

    #如果是演武场的对手
    if rival.is_arena_player():
        arena = data.arena.get()
        record = arena_business.calc_arena_battle_finish(data, arena, False, rival)
        new_arena_records.append(record)

    #如果是乱斗场的对手
    if rival.is_melee_player():
        melee = data.melee.get()
        record = melee_business.calc_melee_battle_finish(data, melee, False, rival)
        new_arena_records.append(record)

    #更新统计信息
    if not _update_statistics(data, battle, False, rival, node,
            enemy_soldier_info, own_soldier_info):
        return False

    if (node is not None and node.basic_id != 0 and
            node.event_type not in (
                NodeInfo.EVENT_TYPE_EXPAND_DUNGEON,
                NodeInfo.EVENT_TYPE_ARENA,
                NodeInfo.EVENT_TYPE_WORLDBOSS) and
            not _update_node_of_lose_battle(data, node, now, change_nodes, new_items, new_mails)):
        logger.warning("Update node of lose battle failed")
        return False

    #取消战斗状态
    if node is not None:
        node.clear_in_battle()

    return battle.finish()


def _update_node_of_lose_battle(data, node, now, change_nodes, new_items, new_mails):
    """战斗失败对节点的影响
    1 如果节点上有随机事件，结束（失败）随机事件
    """
    if node is None:
        return True

    #结束相关随机事件
    if node.is_event_arised() and not _finish_related_event_failed(
            data, node, now, change_nodes, new_items, new_mails):
        return False

    return True


def _calc_food_consume(heroes):
    """计算一个英雄方阵（固定人数）的粮草消耗
    """
    need_food = 0
    count_per_array = int(float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value))
    for hero in heroes:
        key = "%s_%s" % (hero.soldier_basic_id, hero.soldier_level)
        need_food += int(data_loader.SoldierBasicInfo_dict[key].foodCost * count_per_array)

    return need_food


def _calc_soldier_consume(soldier_basic_id, soldier_level):
    """计算一个英雄方阵（固定人数）的士兵数消耗
    """
    need_soldier_num = 0
    count_per_array = int(float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value))
    key = "%s_%s" % (soldier_basic_id, soldier_level)
    need_soldier_num += int(
            data_loader.SoldierBasicInfo_dict[key].soldierCost * count_per_array)

    return need_soldier_num


def _calc_soldier_consume_with_count(soldier_basic_id, soldier_level, count):
    """计算指定数量的士兵消耗
    """
    need_soldier_num = 0
    key = "%s_%s" % (soldier_basic_id, soldier_level)
    need_soldier_num += int(
            data_loader.SoldierBasicInfo_dict[key].soldierCost * count)

    return need_soldier_num


def _calc_number_of_death(soldier_info):
    """
    计算阵亡士兵数量
    """
    count_per_array = int(float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value))

    num = 0
    for (soldier_basic_id, soldier_level, survivals) in soldier_info:
        num += _calc_soldier_consume_with_count(
                soldier_basic_id, soldier_level, count_per_array - survivals)
    return num


def _consume_soldier(data, battle, now, heroes, force):
    """征用士兵
    """
    need_soldier_num = 0
    for hero in heroes:
        need_soldier_num += _calc_soldier_consume(
                hero.soldier_basic_id, hero.soldier_level)

    conscripts = data.conscript_list.get_all()
    total_soldier_num = 0
    for conscript in conscripts:
        conscript.update_current_soldier(now)
        total_soldier_num += (conscript.soldier_num - conscript.lock_soldier_num)

    #消耗兵力，兵力不够时，可以使用元宝兑换
    if not force and total_soldier_num < need_soldier_num:
        logger.warning("Soldier not enough")
        return False

    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    if total_soldier_num < need_soldier_num:
        gold = resource.gold_exchange_soldier(need_soldier_num - total_soldier_num)
        if gold == -1:
            return False
        log = log_formater.output_gold(data, -gold, log_formater.RESOURCE_ITEM_GOLD,
                "consuem gold  for soilder")
        logger.notice(log)
    need_soldier_num = min(total_soldier_num, need_soldier_num)
    if need_soldier_num == 0:
        return True

    #按照兵营当前拥有的士兵数量比例，从兵营中征用
    consume_soldier_info = {}
    provide_soldier_num = 0
    for conscript in conscripts:
        num = int(float(conscript.soldier_num - conscript.lock_soldier_num)\
                / total_soldier_num * need_soldier_num)
        assert num >= 0
        if battle.is_appoint == False:
            if not conscript.provide_soldier(num):
                return False
        else:
            if not conscript.lock_soldier(num):
                return False

        consume_soldier_info[conscript.building_id] = num
        provide_soldier_num += num

    diff = need_soldier_num - provide_soldier_num
    for conscript in conscripts:
        if diff <= 0:
            break

        if battle.is_appoint == False:
            num = min(conscript.soldier_num, diff)
            if num <= 0:
                continue
            if not conscript.provide_soldier(num):
                return False
        else:
            num = min(conscript.soldier_num - conscript.lock_soldier_num, diff)
            if num <= 0:
                continue
            if not conscript.lock_soldier(num):
                return False

        consume_soldier_info[conscript.building_id] += num
        diff -= num

    assert diff == 0

    battle.set_soldier_consume(consume_soldier_info)

    if force and need_soldier_num - total_soldier_num > 0:
        log = log_formater.output_gold(data, -gold, log_formater.EXCHANGE_SOLDIER,
                "Exchange soldier by gold", before_gold = original_gold, soldier = need_soldier_num - total_soldier_num)
        logger.notice(log)

    return True


def _reclaim_soldier(data, battle, now, own_soldier_info):
    """
    返还存活士兵
    按照征收的比例，向各个兵营返还
    """
    soldier_num = battle.soldier_num
    consume_soldier_info = battle.get_soldier_consume()

    conscripts = data.conscript_list.get_all()
    for conscript in conscripts:
        conscript.update_current_soldier(now)

    reclaim_soldier_num = 0
    for (soldier_basic_id, soldier_level, count) in own_soldier_info:
        reclaim_soldier_num += _calc_soldier_consume_with_count(
                soldier_basic_id, soldier_level, count)

    #不返还金钱兑换的士兵数量
    reclaim_soldier_num = min(soldier_num, reclaim_soldier_num)
    if battle.is_appoint == False:
        if reclaim_soldier_num == 0: #兵死光，直接返回
            return True
    else:
        if soldier_num == 0:  #没有兵需要解锁（全部花的元宝）
            return True

    diff = reclaim_soldier_num
    for conscript_id in consume_soldier_info:
        num = int(float(consume_soldier_info[conscript_id]) /
                soldier_num * reclaim_soldier_num)

        conscript = data.conscript_list.get(conscript_id)
        if battle.is_appoint == False:
            if not conscript.reclaim_soldier(num):
                return False
        else:
            if not conscript.unlock_soldier(consume_soldier_info[conscript_id]):
                return False
            if not conscript.provide_soldier(consume_soldier_info[conscript_id] - num):
                return False

        diff -= num

    for conscript_id in consume_soldier_info:
        if diff <= 0:
            break

        conscript = data.conscript_list.get(conscript_id)
        num = conscript.get_available_conscript_num()
        num = min(diff, num)
        if battle.is_appoint == False:
            if not conscript.reclaim_soldier(num):
                return False
        else:
            #对于委任，上面的循环中，被多扣的兵再补回来
            if not conscript.reclaim_soldier(num):
                return False

        diff -= num

    return True


def _update_statistics(data, battle, win, rival, node, enemy_soldier_info, own_soldier_info):
    """更新统计数据
    """
    trainer = data.trainer.get()

    #统计杀敌数
    kills = _calc_number_of_death(enemy_soldier_info)
    trainer.add_kills(kills)

    #统计己方死亡兵数
    deads = _calc_number_of_death(own_soldier_info)
    trainer.add_deads(deads)

    if not win:
        return True

    #更新击败敌人的最高战力
    trainer.update_rival_highest_battlescore(rival.score)

    #更新征服的节点信息
    if (node is not None and node.is_rival_exist()
            and node.event_type != NodeInfo.EVENT_TYPE_ARENA):
        if node.is_key_node():
            rival = data.rival_list.get(node.rival_id)
            trainer.update_knode_statistic_data(1, rival.level)
        elif node.is_dependency():
            rival = data.rival_list.get(node.rival_id)
            trainer.update_dnode_statistic_data(1, rival.level)

    return True


def _start_related_event(data, node, now):
    """启动相关的随机事件
    """
    logger.debug("start related event before battle[event type=%d]" % node.event_type)
    if node.event_type == NodeInfo.EVENT_TYPE_DEFEND:
        #防御事件
        return defend_business.start_defend_event(data, node, now)

    elif node.event_type == NodeInfo.EVENT_TYPE_JUNGLE:
        #野怪事件
        return jungle_business.start_jungle_event(data, node, now)

    elif node.event_type == NodeInfo.EVENT_TYPE_SPY:
        #谍报事件
        return spy_business.start_spy_event(data, node, now)

    elif node.event_type == NodeInfo.EVENT_TYPE_DUNGEON:
        #副本事件
        return dungeon_business.start_dungeon_event(data, node, now)

    elif node.event_type == NodeInfo.EVENT_TYPE_ARENA:
        #演武场事件
        return arena_business.start_arena_event(data, node, now)

    elif node.event_type == NodeInfo.EVENT_TYPE_WORLDBOSS:
        #演武场事件
        return worldboss_business.start_worldboss_event(data, node, now)

    else:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False


def _finish_related_event_succeed(data, node, now, change_nodes):
    """成功结束相关随机事件
    """
    logger.debug("finish related event after battle win[event type=%d]" % node.event_type)
    if node.event_type == NodeInfo.EVENT_TYPE_DEFEND:
        #防御事件
        return defend_business.finish_defend_event_succeed(data, node, now, change_nodes)

    elif node.event_type == NodeInfo.EVENT_TYPE_JUNGLE:
        #野怪事件
        return jungle_business.finish_jungle_event_succeed(data, node, now, change_nodes)

    elif node.event_type == NodeInfo.EVENT_TYPE_SPY:
        #谍报事件
        return spy_business.finish_spy_event_succeed(data, node, now, change_nodes)

    elif node.event_type == NodeInfo.EVENT_TYPE_DUNGEON:
        #副本事件
        return dungeon_business.finish_dungeon_event_succeed(data, node, now, change_nodes)

    elif node.event_type == NodeInfo.EVENT_TYPE_ARENA:
        #演武场事件
        return True #do nothing

    elif node.event_type == NodeInfo.EVENT_TYPE_WORLDBOSS:
        #世界boss事件
        return worldboss_business.finish_worldboss_event(data, node, now, change_nodes)

    else:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False


def _finish_related_event_failed(data, node, now, change_nodes, new_items, new_mails):
    """失败结束相关随机事件
    """
    logger.debug("finish related event after battle lose[event type=%d]" % node.event_type)
    if node.event_type == NodeInfo.EVENT_TYPE_DEFEND:
        #防御事件
        return defend_business.finish_defend_event_fail(
                data, node, now, change_nodes, new_items, new_mails)

    elif node.event_type == NodeInfo.EVENT_TYPE_JUNGLE:
        #野怪事件
        return jungle_business.finish_jungle_event_fail(data, node, now, change_nodes)

    elif node.event_type == NodeInfo.EVENT_TYPE_SPY:
        #谍报事件
        return True #do nothing

    elif node.event_type == NodeInfo.EVENT_TYPE_DUNGEON:
        #副本事件
        return True #do nothing

    elif node.event_type == NodeInfo.EVENT_TYPE_ARENA:
        #演武场事件
        return True #do nothing

    elif node.event_type == NodeInfo.EVENT_TYPE_WORLDBOSS:
        #世界boss事件
        return worldboss_business.finish_worldboss_event(data, node, now, change_nodes)

    else:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False


def lose_defense(data, loss, mail, now):
    """被击败
    Args:
        data[UserData]
        loss[bool]: 是否损失资源
        mail[MailInfo]: 邮件信息
        now[int]: 当前时间戳
    Returns:
        True/False
    """
    if loss:
        user = data.user.get()
        resource = data.resource.get()
        resource.update_current_resource(now)
        defense_list = data.defense_list.get_all(True)
        assert len(defense_list) == 1
        defense = defense_list[0]

        (lost_money, lost_food) = battle_module.calc_defender_loss(defense, resource, user.level)
        if not resource.cost_money(lost_money):
            return False
        if not resource.cost_food(lost_food):
            return False

        mail.attach_lost(money = lost_money, food = lost_food)

    return True


def win_defense(data):
    """防守成功
    """
    #记录防御胜利的次数
    trainer = data.trainer.get()
    trainer.add_defense_win(1)

    return True

def is_speed_cheat(data, node, limit_time, now):
    """判断玩家是否进行了加速作弊"""
    #兼容旧版本
    if limit_time == 0:
        return False
    if node == None:
        #通过邮件复仇,不存在node
        node_id = NodeInfo.generate_id(data.id, 0)     #0表示主城
    else:
        node_id = node.id

    battle = data.battle_list.get(node_id)
    if battle is None:
        logger.warning("Battle is not exist[battle node id=%d]" % node_id)
        return False

    during_time = now - battle.time
    if during_time < limit_time:
        return True
    else:
        return False


def create_broadcast_content_battle_defeated(rival_user_name, user, money, food):
    """
    """
    broadcast_id = int(float(data_loader.OtherBasicInfo_dict["broadcast_id_battle_defeated"].value))
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", rival_user_name, 1)
    content = content.replace("#str#", base64.b64decode(user.name), 1)
    content = content.replace("#str#", str(money), 1)
    content = content.replace("#str#", str(food), 1)

    return (mode_id, priority, life_time, content)


def create_broadcast_content_protect(rival_user_name, user):
    """
    """
    broadcast_id = int(float(data_loader.OtherBasicInfo_dict["broadcast_id_protect"].value))
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(user.name), 1)
    content = content.replace("#str#", rival_user_name, 1)

    return (mode_id, priority, life_time, content)



