#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.union import UserUnionInfo
from app.data.item import ItemInfo
from app.data.hero import HeroInfo
from app.data.node import NodeInfo
from app.data.rival import RivalInfo
from app.data.battle import BattleInfo
from app.core import reward as reward_module
from app.business import item as item_business
from app.business import user as user_business
from app.business import hero as hero_business
from app.business import battle as battle_business
from app import log_formater

def is_able_to_deploy(data, node_index, teams, force = False):
    """是否可以派驻防守
    检查队伍是否合法：上阵队伍数量、队伍可以派驻
    """
    #队伍可以派驻
    old_teams_id = []
    for team in data.team_list.get_all(True):
        if team.union_battle_node_index == node_index:
            old_teams_id.append(team.id)

    for team in teams:
        if team.id not in old_teams_id and not team.is_able_to_deploy_union_battle():
            logger.warning("Team is not able to deploy[index=%d]" % team.index)
            return False

    #上阵队伍数量
    user = data.user.get(True)
    if not force and user.team_count < len(teams):
        logger.warning("Team count is invalid[max=%d]" % user.team_count)
        return False

    return True


def deploy_for_union_battle(data, node_index, teams):
    """派驻联盟战争防守部队
    """
    #清除原有派驻的队伍
    old_team = []
    for team in data.team_list.get_all(True):
        if team.union_battle_node_index == node_index:
            old_team.append(team.id)
    for team_id in old_team:
        team = data.team_list.get(team_id)
        team.clear_for_union_defender()

    #派驻新的队伍
    for team in teams:
        team.set_as_union_defender(node_index)


def cancel_all_deploy_for_union_battle(data):
    """移除所有驻防部队
    """
    #清除派驻的队伍
    defend_team = []
    for team in data.team_list.get_all(True):
        if team.is_union_defender():
            defend_team.append(team.id)

    for team_id in defend_team:
        team = data.team_list.get(team_id)
        team.clear_for_union_defender()


def is_able_to_start_battle(data, teams, heroes, now, cost_gold = 0):
    """是否可以开始战斗
    """
    #是否有足够的攻击次数
    union = data.union.get(True)
    if union.battle_attack_count_left <= 0:
        logger.warning("Union battle attack count invalid")
        return False

    #队伍是否可以参战
    for team in teams:
        if not team.is_able_to_join_union_battle():
            logger.warning("Team not able to join battle[index=%d]" % team.index)
            return False

    #粮草是否足够
    resource = data.resource.get()
    resource.update_current_resource(now)
    need_food = battle_business._calc_food_consume(heroes)
    if resource.food < need_food:
        logger.warning("Not enough food")
        return False

    #兵力是否足够
    need_soldier_num = 0
    for hero in heroes:
        need_soldier_num += battle_business._calc_soldier_consume(
                hero.soldier_basic_id, hero.soldier_level)
    conscripts = data.conscript_list.get_all()
    total_soldier_num = 0
    for conscript in conscripts:
        conscript.update_current_soldier(now)
        total_soldier_num += (conscript.soldier_num - conscript.lock_soldier_num)
    if total_soldier_num >= need_soldier_num:
        return True
    soldier_num_gap = need_soldier_num - total_soldier_num
    gold = resource.soldier_to_gold(soldier_num_gap)
    #if gold != cost_gold:
    if gold > cost_gold:    #客户端有逻辑错，会比服务器多扣一些gold，此处先放过
        logger.warning("Exchange soldier gold error[need soldier=%d][%d!=%d]" % (
            soldier_num_gap, gold, cost_gold))
        return False

    return True


def calc_soldier_consume(heroes):
    need_soldier_num = 0
    for hero in heroes:
        need_soldier_num += battle_business._calc_soldier_consume(
                hero.soldier_basic_id, hero.soldier_level)
    return need_soldier_num


def is_able_to_drum(data, item, cost_gold, drum_count = 1):
    """是否可以擂鼓
    要么消耗物品，要么消耗元宝
    """
    if item is not None:
        if not item.is_union_battle_drum_item():
            logger.warning("Wrong item type")
            return False
        return item.num >= drum_count
    else:
        union = data.union.get(True)
        need_gold = union.calc_drum_cost_gold(drum_count)
        if need_gold != cost_gold:
            logger.warning("Drum cost error[%d!=%d]" % (need_gold, cost_gold))
            return False

        resource = data.resource.get(True)
        return resource.gold >= cost_gold


def drum(data, item, cost_gold, score, now, drum_count = 1):
    """擂鼓
    """
    #擂鼓，添加战功
    union = data.union.get()
    union.drum_for_union_battle(score, drum_count)

    #消耗物品或元宝
    output_items = []
    if item is not None:
        consume = item.consume(drum_count)
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        log = log_formater.output_item(data, "drum", log_formater.DRUM, ''.join(output_items))
        logger.notice(log)
        
    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold
    log = log_formater.output_gold(data, -cost_gold, log_formater.DRUM,
                "Drum by gold", before_gold = original_gold)
    logger.notice(log)
    return resource.cost_gold(cost_gold)


def refresh_attack(data, cost_gold, now):
    """刷新攻击次数
    1 元宝
    2 vip 要求
    """
    user = data.user.get(True)
    union = data.union.get()

    (need_gold, need_vip_level) = union.calc_refresh_battle_requirement()
    if need_gold != cost_gold:
        logger.warning("Cost gold error[%d!=%d]" % (need_gold, cost_gold))
        return False
    if need_vip_level > user.vip_level:
        logger.warning("Vip level error[%d<%d]" % (user.vip_level, need_vip_level))
        return False

    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold
    if not resource.cost_gold(cost_gold):
        return False
    log = log_formater.output_gold(data, -cost_gold, log_formater.REFRESH_ATTACK,  
                "Refresh attack by gold", before_gold = original_gold)
    logger.notice(log)

    union.refresh_battle_attack()
    return True


def start_battle(data, teams, heroes, rival_user_id, rival, now, force = False):
    """开始战斗
    """
    user = data.user.get(True)
    union = data.union.get()
    node_id = NodeInfo.generate_id(data.id, union.get_battle_mapping_node_basic_id())
    battle = data.battle_list.get(node_id)
    if battle is None:
        battle = BattleInfo.create(node_id, data.id)
        data.battle_list.add(battle)
    node = data.node_list.get(node_id)
    if node is None:
        node = NodeInfo.create(data.id, union.get_battle_mapping_node_basic_id())
        data.node_list.add(node)
    r = data.rival_list.get(node_id)
    if r is None:
        r = RivalInfo.create(node_id, data.id)
        data.rival_list.add(r)

    #标记敌对玩家
    r.set_union_battle_enemy_detail(rival_user_id, rival)

    #消耗攻击次数
    union.consume_battle_attack()

    #消耗粮草
    resource = data.resource.get()
    resource.update_current_resource(now)
    need_food = battle_business._calc_food_consume(heroes)
    if not resource.cost_food(need_food):
        return False
    battle.set_food_consume(need_food)

    #消耗兵力
    if not battle_business._consume_soldier(data, battle, now, heroes, force):
        return False

    #计算战利品
    reward_money = 0
    reward_food = 0
    reward_user_exp = 0
    reward_hero_exp = data_loader.MonarchLevelBasicInfo_dict[
                user.level].heroBattleExp
    reward_items = reward_module.random_battle_gift(user.level)
    battle.set_reward(reward_money, reward_food,
            reward_hero_exp, reward_user_exp, reward_items)

    return battle.start(None, r, None, teams, heroes, now, user.vip_level)


def is_able_to_finish_battle(data, now):
    """是否可以结束战斗
    """
    union = data.union.get()
    node_id = NodeInfo.generate_id(data.id, union.get_battle_mapping_node_basic_id())
    battle = data.battle_list.get(node_id)

    return battle.is_able_to_finish(now)


def calc_kills(soldier_info):
    kills = 0
    count_per_array = int(float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value))

    for (soldier_basic_id, soldier_level, survival_count) in soldier_info:
        kills += battle_business._calc_soldier_consume_with_count(
                soldier_basic_id, soldier_level, count_per_array - survival_count)

    return kills


def win_battle(data, enemy_soldier_info, own_soldier_info, score, now):
    """战斗胜利
    """
    user = data.user.get(True)
    union = data.union.get()
    node_id = NodeInfo.generate_id(data.id, union.get_battle_mapping_node_basic_id())
    battle = data.battle_list.get(node_id)
    rival = data.rival_list.get(node_id)

    #获得战利品
    resource = data.resource.get()
    resource.update_current_resource(now)
    resource.gain_money(battle.reward_money)
    resource.gain_food(battle.reward_food)
    if not item_business.gain_item(data, battle.get_reward_items(), "win battle", log_formater.WIN_BATTLE):
        return False

    #根据杀敌，增加战功
    _gain_union_battle_individual_score_of_battle(union, enemy_soldier_info, score)

    #返还己方存活士兵
    if not battle_business._reclaim_soldier(data, battle, now, own_soldier_info):
        return False

    #用户获得经验
    if not user_business.level_upgrade(data, battle.reward_user_exp, now, "exp win union battle", log_formater.EXP_WIN_BATTLE):
        return False

    #参战英雄获得经验
    heroes_id = battle.get_battle_hero()
    exp = int(battle.reward_hero_exp / len(heroes_id))
    for hero_id in heroes_id:
        hero = data.hero_list.get(hero_id)
        if not hero_business.level_upgrade(data, hero, exp, now):
            return False

    #更新统计信息
    if not battle_business._update_statistics(data, battle, True, rival, None,
            enemy_soldier_info, own_soldier_info):
        return False

    #清除原有的敌人信息
    rival.clear()

    return battle.finish()


def lose_battle(data, enemy_soldier_info, own_soldier_info, score, now):
    """战斗失败
    """
    user = data.user.get(True)
    union = data.union.get()
    node_id = NodeInfo.generate_id(data.id, union.get_battle_mapping_node_basic_id())
    battle = data.battle_list.get(node_id)
    rival = data.rival_list.get(node_id)

    #根据杀敌，增加战功
    _gain_union_battle_individual_score_of_battle(union, enemy_soldier_info, score)

    #返还己方存活士兵
    if not battle_business._reclaim_soldier(data, battle, now, own_soldier_info):
        return False

    #更新统计信息
    if not battle_business._update_statistics(data, battle, False, rival, None,
            enemy_soldier_info, own_soldier_info):
        return False

    #清除原有的敌人信息
    rival.clear()

    return battle.finish()


def _gain_union_battle_individual_score_of_battle(union, enemy_soldier_info, score):
    """进行联盟战争，战功增加
    """
    kills = calc_kills(enemy_soldier_info)
    union.kills_for_union_battle(score, kills)


def accept_individual_step_award(data, target_step, now):
    """领取个人战功阶段奖励
    """
    user = data.user.get(True)

    award_index =data_loader.UnionBattleIndividualTargetInfo_dict[
            user.level].awardIndex[target_step - 1]
    award = data_loader.UnionBattleIndivStepAwardInfo_dict[award_index]

    #资源
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    resource.gain_gold(award.gold)
    log = log_formater.output_gold(data, award.gold, log_formater.INDIVIDUAL_STEP_GOLD,
                "Gain gold from individual step award", before_gold = original_gold)
    logger.notice(log)

    #物品
    items = []
    for i in range(len(award.itemsBasicId)):
        items.append((award.itemsBasicId[i], award.itemsNum[i]))
    assert item_business.gain_item(data, items, "individual award", log_formater.INDIVIDUAL_AWARD)

    #联盟荣誉
    union = data.union.get()
    union.gain_honor(award.honor)

    return (award.honor, items)


def calc_award_for_union(win):
    """计算联盟战争，联盟所得
    """
    if win:
        return data_loader.UnionBattleAwardInfo_dict[1].prosperity
    else:
        return data_loader.UnionBattleAwardInfo_dict[2].prosperity


def calc_season_award_for_union(ranking):
    """计算联盟赛季联盟排名，联盟奖励
    """
    return data_loader.UnionSeasonBattleAwardInfo_dict[ranking].prosperity


def calc_award_for_union_member(win, now):
    """计算联盟战争，联盟成员所得
    """
    if win:
        info = data_loader.UnionBattleAwardInfo_dict[1]
    else:
        info = data_loader.UnionBattleAwardInfo_dict[2]

    items = []
    for i in range(len(info.itemsBasicId)):
        items.append((info.itemsBasicId[i], info.itemsNum[i]))

    return (items, info.gold, info.honor)


def calc_award_for_individual(ranking, now):
    """计算联盟战争，个人战功奖励
    """
    info = data_loader.UnionBattleIndivAwardInfo_dict[ranking]
    items = []
    for i in range(len(info.itemsBasicId)):
        items.append((info.itemsBasicId[i], info.itemsNum[i]))

    return (items, info.gold, info.honor)


def calc_season_award_for_union_member(ranking, now):
    """计算联盟赛季联盟排名，联盟成员奖励
    """
    info = data_loader.UnionSeasonBattleAwardInfo_dict[ranking]
    items = []
    for i in range(len(info.itemsBasicId)):
        items.append((info.itemsBasicId[i], info.itemsNum[i]))

    return (items, info.gold, info.honor)


def calc_season_award_for_individual(ranking, now):
    """计算联盟赛季个人排名，个人奖励
    """
    info = data_loader.UnionSeasonBattleIndivAwardInfo_dict[ranking]
    items = []
    for i in range(len(info.itemsBasicId)):
        items.append((info.itemsBasicId[i], info.itemsNum[i]))

    return (items, info.gold, info.honor)


def _award(data, items, gold, honor, now):
    """发放奖励
    """
    #资源
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    resource.gain_gold(gold)
    log = log_formater.output_gold(data, gold, log_formater.AWARD_GOLD,
                "Gain gold from award", before_gold = original_gold)
    logger.notice(log)

    #物品
    assert item_business.gain_item(data, items, "award", log_formater.AWARD)

    #联盟荣誉
    union = data.union.get()
    union.gain_honor(honor)


