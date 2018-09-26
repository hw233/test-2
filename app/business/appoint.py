#coding:utf8
"""
Created on 2016-02-20
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief :
"""

import base64
import random
from scipy.stats import binom  #二项分布
from utils import logger
from utils import utils
from utils.ret import Ret
from datalib.data_loader import data_loader
from app.data.item import ItemInfo
from app.data.hero import HeroInfo
from app.data.team import TeamInfo
from app.data.node import NodeInfo
from app.data.soldier import SoldierInfo
from app.data.battle import BattleInfo
from app.core import technology as technology_module
from app.business import battle as battle_business
from app.business import mail as mail_business


def start_appoint(data, user, node, rival, teams, heroes, now, force = False):
    """开始委任(只有pve可以委任)
    1 检查委任功能是否已经开启
    2 检查是否是PVE的战斗
    3 检查委任部队是否在战斗中
    4 开始战斗
    5 标记委任状态
    +Args:
        data[UserData]
        user[UserInfo]: user信息
        node[NodeInfo]: node信息
        rival[RivalInfo]
        teams[list(TeamInfo)]
        heroes[list(HeroInfo)]
        now
        force
    Returns:
        True 开始委任成功
        False 开始委任失败
    """
    #检查委任功能是否已经开启
    if not BattleInfo.is_able_to_appoint(user):
        logger.warning("User is not able to appoint[user level=%d]" % user.level)
        return False

    #检查是否是PVE的战斗
    #if rival.is_real_player():
    #    logger.warning("Appoint is not pve[node id=%d][rival id=%d]" % (node.id, rival.id))
    #    return False

    #检查部队是否在战斗中
    for team in teams:
        if team.is_in_battle():
            logger.warning("Team is already in battle[team index=%d]" % team.index)
            return False

    #检查该节点是否已在战斗中
    if node.is_in_battle():
        logger.warning("Node is already in battle[node basic id=%d]" % node.basic_id)
        return False

    #开始委任战斗
    if not battle_business.start_battle(data, node, rival,
            None, teams, heroes, now, force, appoint = True):
        logger.warning("Start battle of appoint failed")
        return False

    #计算委任结果
    battle = data.battle_list.get(node.id)
    _calc_appoint_result(data, battle, rival, teams, heroes)

    #设置状态
    for team in teams:
        team.set_in_battle(node.basic_id)
    for hero in heroes:
        hero.set_in_battle(node.basic_id)

    return True

def calc_battle_result(data, battle, rival, teams, heroes):
    #己方阵容
    (self_teams, self_total_battle_score) = _init_self_teams(data, teams)
    self_team_num = len(self_teams)

    #敌方阵容
    (enemy_teams, enemy_total_battle_score) = _init_enemy_teams(data, rival)
    enemy_team_num = len(enemy_teams)

    self_soldier_info = []
    enemy_soldier_info = []

    while _is_all_dead(self_teams) != True and\
            _is_all_dead(enemy_teams) != True:
        team_num = min(self_team_num, enemy_team_num)

        for i in range(team_num):
            _calc_team_result(self_teams[i], enemy_teams[i], self_soldier_info, enemy_soldier_info)

        #删去已经阵亡的己方部队
        self_teams = _delete_dead_teams(self_teams)

        #删去已经阵亡的敌方部队
        enemy_teams = _delete_dead_teams(enemy_teams)

        self_team_num = len(self_teams)
        enemy_team_num = len(enemy_teams)

    if _is_all_dead(self_teams):
        is_win = False
        for team in enemy_teams:
            for army in team:
                enemy_soldier_info.append(
                        (army[ARMY_SOLDIER_BASIC_ID],
                         army[ARMY_SOLDIER_LEVEL],
                         army[ARMY_SOLDIER_NUM]))
    else:
        is_win = True
        for team in self_teams:
            for army in team:
                self_soldier_info.append(
                        (army[ARMY_SOLDIER_BASIC_ID],
                         army[ARMY_SOLDIER_LEVEL],
                         army[ARMY_SOLDIER_NUM]))
    
    #if (rival.type == NodeInfo.ENEMY_TYPE_PVP_CITY 
    #        or rival.type == NodeInfo.ENEMY_TYPE_PVP_RESOURCE):
    #    if self_total_battle_score < enemy_total_battle_score:
    #        is_win = False
    logger.debug("self_total_battle_score=%d, enemy_total_battle_score=%d" % 
                (self_total_battle_score, enemy_total_battle_score))

    return (is_win, self_soldier_info, enemy_soldier_info)

def _calc_appoint_result(data, battle, rival, teams, heroes):
    (is_win, self_soldier_info, enemy_soldier_info) = \
            calc_battle_result(data, battle, rival, teams, heroes)
    battle.set_appoint_result(is_win, self_soldier_info, enemy_soldier_info)


def _calc_team_battle_score():
    """
    """

def _calc_team_result(self_team, enemy_team, self_soldier_info, enemy_soldier_info):
    """计算部队的对战结果（一个部队指一个team）
    args:
        self_team: [list(ArmyInfo)]
        enemy_team: [list(ArmyInfo)]

    Return:
    """
    #己方
    self_army_num = len(self_team)

    #敌方
    enemy_army_num = len(enemy_team)

    while _is_team_dead(self_team) != True and\
            _is_team_dead(enemy_team) != True:
        army_num = min(self_army_num, enemy_army_num)

        self_dead_armys = []
        enemy_dead_armys = []
        for i in range(army_num):
            _calc_army_result(self_team[i], enemy_team[i])
            if _is_army_dead(self_team[i]):
                self_soldier_info.append(
                        (self_team[i][ARMY_SOLDIER_BASIC_ID],
                         self_team[i][ARMY_SOLDIER_LEVEL],
                         self_team[i][ARMY_SOLDIER_NUM]))
                self_dead_armys.append(self_team[i])
            if _is_army_dead(enemy_team[i]):
                enemy_soldier_info.append(
                        (enemy_team[i][ARMY_SOLDIER_BASIC_ID],
                         enemy_team[i][ARMY_SOLDIER_LEVEL],
                         enemy_team[i][ARMY_SOLDIER_NUM]))
                enemy_dead_armys.append(enemy_team[i])

        #删去已经阵亡的己方队伍
        _delete_dead_armys(self_dead_armys, self_team)

        #删去已经阵亡的敌方队伍
        _delete_dead_armys(enemy_dead_armys, enemy_team)

        self_army_num = len(self_team)
        enemy_army_num = len(enemy_team)

    if _is_team_dead(self_team):
        return False
    else:
        return True


ARMY_HERO_BASIC_ID = 0
ARMY_HERO_LEVEL = 1
ARMY_HERO_STAR = 2
ARMY_HERO_BATTLE_SCORE = 3
ARMY_SOLDIER_BASIC_ID = 4
ARMY_SOLDIER_LEVEL = 5
ARMY_SOLDIER_NUM = 6
ARMY_ONE_SOLDIER_BATTLE_SCORE = 7
ARMY_IS_HERO_SURVIVAL = 8


def _calc_army_result(self_army, enemy_army):
    """计算队伍的对战结果（一个army是指一个hero加上几个兵）
    args:
        self_army[ArmyInfo out]:    己方army
        enemy_army[ArmyInfo out]:   敌方army

        ArmyInfo:  army信息的列表 列表表示
        [hero_basic_id, hero_level, hero_star_level, hero_battle_score,
            soldier_basic_id, soldier_level, soldier_num,
            one_soldier_battle_score, is_hero_survival]

    Return:
        is_self_win[bool]
    """
    self_hero_level = self_army[ARMY_HERO_LEVEL]
    self_hero_star_level = self_army[ARMY_HERO_STAR]
    self_hero_battle_score = self_army[ARMY_HERO_BATTLE_SCORE]
    self_soldier_basic_id = self_army[ARMY_SOLDIER_BASIC_ID]
    self_soldier_num = self_army[ARMY_SOLDIER_NUM]
    self_one_soldier_battle_score = self_army[ARMY_ONE_SOLDIER_BATTLE_SCORE]

    enemy_hero_level = enemy_army[ARMY_HERO_LEVEL]
    enemy_hero_star_level = enemy_army[ARMY_HERO_STAR]
    enemy_hero_battle_score = enemy_army[ARMY_HERO_BATTLE_SCORE]
    enemy_soldier_basic_id = enemy_army[ARMY_SOLDIER_BASIC_ID]
    enemy_soldier_num = enemy_army[ARMY_SOLDIER_NUM]
    enemy_one_soldier_battle_score = enemy_army[ARMY_ONE_SOLDIER_BATTLE_SCORE]

    self_hero_repair_factor = float(data_loader.AppointHeroScoreRepairFactor_dict[self_hero_star_level].factor)
    enemy_hero_repair_factor = float(data_loader.AppointHeroScoreRepairFactor_dict[enemy_hero_star_level].factor)

    key = "%s_%s" % (self_soldier_basic_id, enemy_soldier_basic_id)
    self_soldier_repair_factor = float(data_loader.AppointSoldierScoreRepairFactor_dict[key].factor)
    key = "%s_%s" % (enemy_soldier_basic_id, self_soldier_basic_id)
    enemy_soldier_repair_factor = float(data_loader.AppointSoldierScoreRepairFactor_dict[key].factor)

    self_level_gap_factor = float(data_loader.AppointHeroLevelGapRepairFactor_dict[self_hero_level - enemy_hero_level].factor)
    enemy_level_gap_factor = float(data_loader.AppointHeroLevelGapRepairFactor_dict[enemy_hero_level - self_hero_level].factor)

    #队伍战力
    self_battle_score = float((self_hero_battle_score * self_hero_repair_factor +
            self_soldier_num * self_one_soldier_battle_score * self_soldier_repair_factor) *
            self_level_gap_factor)

    enemy_battle_score = float((enemy_hero_battle_score * enemy_hero_repair_factor +
            enemy_soldier_num * enemy_one_soldier_battle_score * enemy_soldier_repair_factor) *
            enemy_level_gap_factor)

    #计算胜利概率
    a = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_a"].value)
    b = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_b"].value)
    c = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_c"].value)
    d = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_d"].value)
    e = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_e"].value)
    f = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_f"].value)
    g = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_g"].value)
    h = float(data_loader.MapConfInfo_dict["AppointJudgeCoefficient_h"].value)
    if self_battle_score >= enemy_battle_score:
        self_win_rate = min(1, a * (enemy_battle_score / self_battle_score - b) ** c + d)
    else:
        self_win_rate = max(0, e * (enemy_battle_score / self_battle_score - f) ** g + h)

    #判定胜负
    random.seed()
    if random.random() <= self_win_rate:
        is_self_win = True
    else:
        is_self_win = False

    hero_survival_factor = float(data_loader.MapConfInfo_dict["AppointHeroSurviveCoefficient"].value)
    soldier_survival_factor = float(data_loader.MapConfInfo_dict["AppointSoldierSurviveCoefficient"].value)
    if is_self_win:
        #已胜，计算存活
        self_hero_survival_rate = self_win_rate * hero_survival_factor
        self_soldier_survival_rate = self_win_rate * soldier_survival_factor

        if self_army[ARMY_IS_HERO_SURVIVAL]:
            self_army[ARMY_IS_HERO_SURVIVAL] = _calc_hero_survival(self_hero_survival_rate)
            if self_army[ARMY_IS_HERO_SURVIVAL] == False:
                self_army[ARMY_HERO_BATTLE_SCORE] = 0

        if self_army[ARMY_SOLDIER_NUM] > 0:
            self_army[ARMY_SOLDIER_NUM] = _calc_soldier_survival(
                    self_soldier_survival_rate, self_army[ARMY_SOLDIER_NUM])

        enemy_army[ARMY_IS_HERO_SURVIVAL] = False
        enemy_army[ARMY_SOLDIER_NUM] = 0

    else:
        #己败，计算存活
        enemy_win_rate = 1 - self_win_rate
        enemy_hero_survival_rate = enemy_win_rate * hero_survival_factor
        enemy_soldier_survival_rate = enemy_win_rate * soldier_survival_factor

        if enemy_army[ARMY_IS_HERO_SURVIVAL]:
            enemy_army[ARMY_IS_HERO_SURVIVAL] = _calc_hero_survival(enemy_hero_survival_rate)
            if enemy_army[ARMY_IS_HERO_SURVIVAL] == False:
                enemy_army[ARMY_HERO_BATTLE_SCORE] = 0

        if enemy_army[ARMY_SOLDIER_NUM] > 0:
            enemy_army[ARMY_SOLDIER_NUM] = _calc_soldier_survival(
                    enemy_soldier_survival_rate, enemy_army[ARMY_SOLDIER_NUM])

        self_army[ARMY_IS_HERO_SURVIVAL] = False
        self_army[ARMY_SOLDIER_NUM] = 0

    logger.debug("[self_is_win=%d][self_win_rate=%f]: Self army[hero basic id=%d] VS Enemy army[hero basic id=%d]"
            % (is_self_win, self_win_rate, self_army[ARMY_HERO_BASIC_ID], enemy_army[ARMY_HERO_BASIC_ID]))
    #logger.debug("self army[soldier num=%d][is_hero_survival=%d]"
    #        % (self_army[ARMY_SOLDIER_NUM], self_army[ARMY_IS_HERO_SURVIVAL]))
    #logger.debug("enemy army[soldier num=%d][is_hero_survival=%d]"
    #        % (enemy_army[ARMY_SOLDIER_NUM], enemy_army[ARMY_IS_HERO_SURVIVAL]))


def _calc_hero_survival(survival_rate):
    random.seed()
    if random.random() <= survival_rate:
        return True
    else:
        return False


def _calc_soldier_survival(survival_rate, soldier_num):
    return binom.rvs(soldier_num, survival_rate, size=1)[0]


def _init_self_teams(data, teams):
    self_teams = []
    total_battle_score = 0

    for team in teams:
        hero_ids = team.get_heroes()

        team = []
        for hero_id in hero_ids:
            if hero_id != 0:
                hero = data.hero_list.get(hero_id, True)

                #找到会影响该英雄所带兵种的战斗科技
                battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
                    data.technology_list.get_all(True), hero.soldier_basic_id)

                hero_and_soldier_battle_score = hero\
                        .calc_hero_and_soldier_battle_score(battle_technology_basic_id)
                hero_battle_score = hero_and_soldier_battle_score[0]
                soldier_num = int(float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value))
                one_soldier_battle_score = hero_and_soldier_battle_score[1] / soldier_num

                #累加总战力
                total_battle_score += hero_and_soldier_battle_score[0] + hero_and_soldier_battle_score[1]

                team.append([hero.basic_id, hero.level, hero.star, hero_battle_score,
                    hero.soldier_basic_id, hero.soldier_level, soldier_num, one_soldier_battle_score, True])
                logger.debug("self army[hero basic id=%d][hero level=%d]"
                        "[hero star=%d][hero battlescore=%d][soldier basic id=%d]"
                        "[soldier_level=%d][soldier num=%d][one soldier battlescore=%d]"
                        % (hero.basic_id, hero.level, hero.star, hero_battle_score,
                            hero.soldier_basic_id, hero.soldier_level, soldier_num, one_soldier_battle_score))

        self_teams.append(team)

    return (self_teams, total_battle_score)


def _init_enemy_teams(data, rival):
    #委任节点上随机事件的buff影响
    battle_score_coefficient = 1.0
    buffs = rival.get_buff()
    for buff_id in buffs:
        battle_score_coefficient *= float(
                data_loader.BuffBasicInfo_dict[buff_id].battleScoreCoefficient)

    enemy_teams = []
    total_battle_score = 0
    for (index, enemy) in enumerate(rival.get_enemy_detail()):
        if index % 3 == 0:
            team = []

        if enemy == None:
            continue

        hero_basic_id = enemy[0]
        hero_level = enemy[1]
        hero_star = enemy[2]
        skills = enemy[3]
        soldier_basic_id = enemy[4]
        soldier_level = enemy[5]
        equipment_id = enemy[6]
        evolution_level = enemy[7]
        stone_weapon = enemy[8]
        stone_armor = enemy[9]
        stone_treasure = enemy[10]
        herostars = enemy[11]
        is_awaken = enemy[12]
        refine_level = enemy[13]
        refine_value = enemy[14]
        soldier = SoldierInfo.create(rival.user_id, soldier_basic_id, soldier_level)
        rival_technology_basic_ids = rival.get_technology_basic_ids()
        #找到会影响该英雄所带兵种的战斗科技
        battle_technology_basic_id = technology_module.get_battle_technology_for_soldier_by_ids(
                rival_technology_basic_ids, soldier_basic_id)

        hero = HeroInfo.create_special(rival.user_id, rival.level, hero_basic_id,
                hero_level, hero_star, soldier, skills, battle_technology_basic_id,
                equipment_id, [], False, evolution_level, True, herostars, is_awaken,
                refine_level, refine_value)

        hero_and_soldier_battle_score = hero\
                .calc_hero_and_soldier_battle_score(battle_technology_basic_id)
        hero_battle_score = int(hero_and_soldier_battle_score[0] * battle_score_coefficient)
        soldier_num = int(float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value))
        one_soldier_battle_score = int(hero_and_soldier_battle_score[1] / soldier_num * battle_score_coefficient)

        #累加总战力
        total_battle_score += hero_and_soldier_battle_score[0] + hero_and_soldier_battle_score[1]
        
        team.append([hero_basic_id, hero_level, hero_star, hero_battle_score,
                    soldier_basic_id, soldier_level, soldier_num, one_soldier_battle_score, True])
        logger.debug("enemy army[coefficient=%f][hero basic id=%d][hero level=%d]"
                "[hero star=%d][hero battlescore=%d][soldier basic id=%d]"
                "[soldier_level=%d][soldier num=%d][one soldier battlescore=%d]"
                % (battle_score_coefficient, hero_basic_id, hero_level, hero_star, hero_battle_score,
                    soldier_basic_id, soldier_level, soldier_num, one_soldier_battle_score))

        if index % 3 == 2:
            enemy_teams.append(team)

    return (enemy_teams, total_battle_score)


def _is_army_dead(army):
    is_hero_survival = army[ARMY_IS_HERO_SURVIVAL]
    soldier_num = army[ARMY_SOLDIER_NUM]

    if is_hero_survival == False and soldier_num == 0:
        return True
    else:
        return False


def _is_team_dead(team):
    is_team_dead = True

    for army in team:
        if _is_army_dead(army) == False:
            is_team_dead = False
            break

    return is_team_dead


def _is_all_dead(teams):
    is_all_dead = True

    for team in teams:
        if _is_team_dead(team) == False:
            is_all_dead = False
            break

    return is_all_dead


def _delete_dead_armys(dead_armys, all_armys):
    for dead_army in dead_armys:
        for (index, army) in enumerate(all_armys):
            if army[ARMY_HERO_BASIC_ID] == dead_army[ARMY_HERO_BASIC_ID]:
                all_armys.pop(index)
                break


def _delete_dead_teams(all_teams):
    new_all_teams = [ team for team in all_teams if len(team) != 0]
    return new_all_teams


def finish_appoint(data, node, battle, change_nodes, items, heroes, mails, now, ret = Ret()):
    """开始委任
    1 检查该node是否正处于战斗中，且委任间隔是否已到
    2 委任战斗计算
    3 生成战报
    4 解除委任状态
    +Args:
        data[UserData]
        node[NodeInfo]
        battle[BattleInfo]
        change_nodes[list(NodeInfo)]
        items[list((ItemInfo)  out]
        heroes[list((basic_id, level, exp, battle_node_basic_id )元组)  out]
        mails[list(HeroInfo)]
        now
    Returns:
        True 开始委任成功
        False 开始委任失败
    """
    battle = data.battle_list.get(node.id)
    if battle.is_appoint == False:
        logger.warning("Node is not be appointed.[node basic id=%d]" % node.basic_id)
        ret.setup("FINISHED")
        return False

    #存活兵力信息
    own_soldier_info = battle.get_own_soldier_info()
    enemy_soldier_info = battle.get_enemy_soldier_info()

    #创建邮件
    _create_finish_appoint_mail(data, battle, node, mails, now)

    hero_ids = battle.get_battle_hero()
    teams_index = battle.get_battle_team()
    new_items = []
    new_mails = []
    #战斗结算
    if battle.appoint_result:
        #奖励中涉及的物品
        reward_items = battle.get_reward_items()

        if not battle_business.win_battle(data, node, enemy_soldier_info,
                own_soldier_info, change_nodes, now):
            raise Exception("Win battle failed")

        for reward_item in reward_items:
            item_id = ItemInfo.generate_id(data.id, reward_item[0])
            item = data.item_list.get(item_id)
            items.append(item)

    else:
        if not battle_business.lose_battle(
                data, node, now, enemy_soldier_info, own_soldier_info,
                change_nodes, new_items, new_mails):
            raise Exception("Lost battle failed")

        #据点丢失后可能获得的物品
        for new_item in new_items:
            item_id = ItemInfo.generate_id(data.id, new_item[1])
            item = data.item_list.get(item_id)
            items.append(item)

    #结束委任
    for team_index in teams_index:
        team_id = TeamInfo.generate_id(data.id, team_index)
        team = data.team_list.get(team_id)
        #解除队伍的战斗状态
        team.clear_in_battle()

    for hero_id in hero_ids:
        hero = data.hero_list.get(hero_id)
        #解除英雄的战斗状态
        hero.clear_in_battle()
        heroes.append((hero.basic_id, hero.level, hero.exp, hero.battle_node_basic_id))

    node.clear_in_battle()

    return True


def _create_finish_appoint_mail(data, battle, node, mails, now):
    """创建邮件
    """
    mail = mail_business.create_appoint_mail(data, node.basic_id, now)

    try:
        #计算损失的兵数
        soldier_survival_num = 0
        for (soldier_basic_id, soldier_level, count) in battle.get_own_soldier_info():
            soldier_survival_num += battle_business._calc_soldier_consume_with_count(
                    soldier_basic_id, soldier_level, count)
        lost_soldier_num = battle.soldier_num - soldier_survival_num
        if lost_soldier_num < 0:
            lost_soldier_num = 0

        #胜利有奖励
        if battle.appoint_result:
            reward_money = battle.reward_money
            reward_food = battle.reward_food
            reward_gold = 0
            reward_item_list = battle.get_reward_items()
            mail.attach_reward(reward_money, reward_food, reward_gold, reward_item_list)

        rival = data.rival_list.get(battle.rival_id)
        mail.attach_enemy_info(rival)

        #随机sender名字
        sender_hero_id = random.sample(battle.get_battle_hero(), 1)[0]
        sender_hero = data.hero_list.get(sender_hero_id)
        hero_name = data_loader.HeroBasicInfo_dict[sender_hero.basic_id].name
        mail.change_sender(hero_name.encode("utf-8"))

        #随机enemy_name名字
        enemy_heroes_basic_id = [enemy[0] for enemy in rival.get_enemy_detail()]
        enemy_hero_basic_id = random.sample(enemy_heroes_basic_id, 1)[0]
        enemy_name = base64.b64encode(
                data_loader.HeroBasicInfo_dict[enemy_hero_basic_id].name.encode("utf-8"))
        mail.change_enemy_name(enemy_name)

        #战斗损失
        #mail.attach_lost(0, battle.food, 0, lost_soldier_num)
        mail.attach_lost(0, 0, 0, lost_soldier_num)

        #keynode需要有node id
        #if node.is_key_node():
        mail.attach_node_info(node)

        mail.attach_battle_info(battle.appoint_result)
    except:
        logger.warning("create_finish_appoint_mail fail")
        return

    mails.append(mail)


