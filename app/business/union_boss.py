#coding:utf8
"""
Created on 2017-03-01
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟boss处理逻辑
"""

from app.business import battle as battle_business
from app.data.battle import BattleInfo
from app.data.union import UserUnionInfo
from app.data.node import NodeInfo
from app.data.rival import RivalInfo
from app.data.unionboss import UserUnionBossInfo
from app.data.soldier import SoldierInfo
from app.data.hero import HeroInfo
from app.core import reward as reward_module
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from proto import union_pb2
from proto import battle_pb2
import copy

def start_battle(data, boss_id, array_index, teams, heroes, now, cost_gold):
    """开始联盟boss战"""
    boss = get_boss_by_id(data, boss_id)
    if boss is None:
        logger.warning("non-existent boss[user_id=%d][boss_id=%d]" % (
                data.id, boss_id))
        raise Exception("non-existent boss")

    if array_index > 3 or array_index < 1:
        logger.warning("boss team index out of range[user_id=%d][array_index=%d]" % (
                data.id, array_index))
        return (union_pb2.UNION_BOSS_TEAM_UNATTACKABLE, battle_pb2.BATTLE_OK)

    if boss.get_can_attack_arrays_index()[array_index - 1] != 1:
        logger.warning("boss team cannot attack[user_id=%d][array_index=%d]" % (
                data.id, array_index))
        return (union_pb2.UNION_BOSS_TEAM_UNATTACKABLE, battle_pb2.BATTLE_OK)

    node_id = NodeInfo.generate_id(data.id, UserUnionInfo.get_union_boss_node_basic_id())
    battle = data.battle_list.get(node_id)
    if battle is None:
        battle = BattleInfo.create(node_id, data.id)
        data.battle_list.add(battle)
    node = data.node_list.get(node_id)
    if node is None:
        node = NodeInfo.create(data.id, UserUnionInfo.get_union_boss_node_basic_id())
        data.node_list.add(node)
    rival = data.rival_list.get(node_id)
    if rival is None:
        rival = RivalInfo.create(node_id, data.id)
        data.rival_list.add(rival)

    rival.set_unionboss(boss_id)

    #消耗粮草
    resource = data.resource.get()
    resource.update_current_resource(now)
    need_food = battle_business._calc_food_consume(heroes)
    if not resource.cost_food(need_food):
        logger.warning("no enough food[user_id=%d]" % data.id)
        return (union_pb2.UNION_OK, battle_pb2.BATTLE_RESOURCE_SHORTAGE)
    battle.set_food_consume(need_food)

    #消耗兵力

    need_soldier_num = 0
    for hero in heroes:
        need_soldier_num += battle_business._calc_soldier_consume(
                hero.soldier_basic_id, hero.soldier_level)
    conscripts = data.conscript_list.get_all()
    total_soldier_num = 0
    for conscript in conscripts:
        conscript.update_current_soldier(now)
        total_soldier_num += (conscript.soldier_num - conscript.lock_soldier_num)

    if total_soldier_num < need_soldier_num:
        if cost_gold <= 0:
            logger.warning("no enough soldier[user_id=%d]" % data.id)
            return (union_pb2.UNION_OK, battle_pb2.BATTLE_RESOURCE_SHORTAGE)
        else:
            gold = resource.soldier_to_gold(need_soldier_num - total_soldier_num)
            if gold != cost_gold:
                logger.warning("exchange soldier gold error[user_id=%d][gold=%d][real_gold=%d]" % (
                    data.id, cost_gold, gold
                ))

    if not battle_business._consume_soldier(data, battle, now, heroes, cost_gold > 0):
        logger.warning("no enough soldier[user_id=%d]" % data.id)
        return (union_pb2.UNION_OK, battle_pb2.BATTLE_RESOURCE_SHORTAGE)

    #计算战利品
    user = data.user.get()
    reward_money = 0
    reward_food = 0
    reward_user_exp = 0
    reward_hero_exp = data_loader.MonarchLevelBasicInfo_dict[
                user.level].heroBattleExp
    reward_items = reward_module.random_battle_gift(user.level)
    battle.set_reward(reward_money, reward_food,
            reward_hero_exp, reward_user_exp, reward_items)

    boss.start_battle(array_index)
    battle.start(node, rival, None, teams, heroes, now, user.vip_level)

    return (union_pb2.UNION_OK, battle_pb2.BATTLE_OK)

def finish_battle(data, boss, win, kill_soldier_num):
    """结束boss战"""
    #1.计算战功
    #2.重新计算可攻击的队伍
    union = data.union.get()

    key = "%s_%s_%s" % (boss.boss_id, boss.level, boss.attack_array_index)
    merit_ratio = data_loader.UnionBossArrayBasicInfo_dict[key].meritRatio
    merit = utils.floor_to_int(merit_ratio * kill_soldier_num)
    union.attack_union_boss(merit)

    boss.finish_battle(win)

def is_able_to_accept_score_box(data, step):
    """是否可以领取个人战功宝箱"""
    union = data.union.get()
    user = data.user.get()

    targets = copy.deepcopy(data_loader.UnionBossIndividualTargetInfo_dict[user.level].target)
    targets.append(999999999)
    real_step = 0
    for i, score in enumerate(targets):
        if score > union.union_boss_score:
            real_step = i
            break
    if step > real_step:
        #TODO:未达到该战功
        return False

    accepted_boxes = union.get_union_boss_box_steps()
    if step in accepted_boxes:
        #TODO:宝箱已经领取过了
        return False
    return True
    
def get_score_box_reward(data, step):
    """获取个人战功宝箱奖励"""
    user = data.user.get(True)

    award_index = data_loader.UnionBossIndividualTargetInfo_dict[user.level].awardIndex[step - 1]
    items_id = data_loader.UnionBossIndivStepAwardInfo_dict[award_index].itemsBasicId
    items_num = data_loader.UnionBossIndivStepAwardInfo_dict[award_index].itemsNum
    honor = data_loader.UnionBossIndivStepAwardInfo_dict[award_index].honor

    return (items_id, items_num, honor)

def get_reset_attack_gold(data):
    """获取重置攻击消耗的元宝"""
    union = data.union.get(True)
    reset_num = min(16, union.union_boss_reset_num+1)
    return data_loader.UnionBossAttackRefreshInfo_dict[reset_num].goldCost

def get_boss_by_id(data, boss_id, readonly=False):
    id = UserUnionBossInfo.generate_id(data.id, boss_id)
    return data.unionboss_list.get(id, readonly)

def update_union_boss(data, bosses_id, last_update_time):
    """更新联盟boss"""
    user = data.user.get(True)
    for boss_id in bosses_id:
        new_boss = UserUnionBossInfo.create(data.id, boss_id)
        new_boss.init(user.level)
        old_boss = data.unionboss_list.get(new_boss.id)
        if old_boss is None:
            data.unionboss_list.add(new_boss)
        else:
            old_boss.reset(user.level)

    union = data.union.get()
    union.reset_unionboss(last_update_time)

def try_update_union_boss(data, bosses_id, last_update_time):
    """尝试更新联盟boss"""
    old_bosses = data.unionboss_list.get_all()
    union = data.union.get()
    if union.union_boss_last_update_time != last_update_time:
        update_union_boss(data, bosses_id, last_update_time)

def generate_array_detail(unionboss, user):
    """生成阵容详情返回
    """
    teams = []
    for array_id in unionboss.get_arrays_id():
        array = data_loader.UnionBossArrayBasicInfo_dict[array_id]
        #buff和tech是针对整个阵容生效的
        buffs_id = array.buffIds
        techs_id = array.techIds

        heroes = []
        for i in range(len(array.heroIds)):
            basic_id = array.heroIds[i]
            star = array.heroStars[i]
            equipments_id = []
            equipments_id.append(array.heroEquipmentIds[i * 3])
            equipments_id.append(array.heroEquipmentIds[i * 3 + 1])
            equipments_id.append(array.heroEquipmentIds[i * 3 + 2])
            evolution_level = array.heroEvolutionLevels[i]
            soldier_basic_id = array.soldierBasicIds[i]
            soldier_level = array.soldierLevels[i]
            soldier = SoldierInfo.create(user.id, soldier_basic_id, soldier_level)

            hero = HeroInfo.create_special(user.id, user.level, basic_id, 
                    user.level, star, soldier, [], techs_id, equipments_id, 
                    buffs_id, False, evolution_level, False)
            heroes.append(hero)

        teams.append(heroes)

    return teams
