#coding:utf8
"""
Created on 2016-06-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 打包 protobuf
"""

import time
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.hero import HeroInfo
from gunion.business import donate as donate_business


def pack_union_info(union, message):
    message.id = union.id
    message.name = union.get_readable_name()
    message.icon_id = union.icon
    message.level = union.level
    message.current_number = union.current_number
    message.max_number = union.max_number
    message.join_status = union.join_status
    message.need_level = union.join_level_limit
    message.announcement = union.get_readable_announcement()
    message.prosperity = union.today_prosperity
    message.recent_prosperity = union.recent_prosperity


def pack_member_info(member, message):
    message.union_id = member.union_id
    message.user.user_id = member.user_id
    message.position = member.position
    message.total_honor = member.history_honor


def pack_application_info(application, message):
    message.union_id = application.union_id
    message.user.user_id = application.user_id
    message.user.name = application.get_readable_user_name()
    message.user.headicon_id = application.user_icon
    message.user.level = application.user_level
    message.battle_score = application.user_battle_score
    message.time = application.time


def pack_aid_info(aid, message, user_id, now):
    message.sender.user_id = aid.user_id
    message.time = aid.start_time
    message.need_item.basic_id = aid.item_basic_id
    message.need_item.num = aid.item_need_num
    message.receive_num = aid.item_current_num
    message.available = aid.is_available(user_id)
    message.finish = aid.is_able_to_finish(now)


def pack_battle_info(union, season, battle, message, now):
    message.union_id = union.id
    message.stage = battle.stage
    message.rival_union_id = battle.rival_union_id
    message.battle_left_time = battle.close_time - now
    message.begin_battle_left_time = battle.fight_time - now
    message.after_battle_left_time = battle.finish_time - now
    message.season_left_time = season.get_finish_time() - now

    message.big_box.id = 100
    reward_record = battle.get_reward_record()
    for user_id, user_name, icon_id, item_id, item_num, time in reward_record:
        member = message.big_box.members.add()
        member.user_id = user_id
        member.name = user_name
        member.headIconId = icon_id
        member.item_id = item_id
        member.item_num = item_num
        member.passedTime = now - time


def pack_battle_individual_info(member, message):
    message.user.user_id = member.user_id
    message.user.union_id = member.union_id
    message.battle_lock = not member.is_join_battle

    message.score = member.battle_score
    message.score_accept_step = member.battle_score_accept_step


def pack_battle_map_info(union, season, battle, nodes, message, now):
    message.union_id = union.id
    message.name = union.get_readable_name()
    message.icon_id = union.icon

    message.season_score = season.score
    message.score = battle.score
    message.score_individuals = battle.individuals_score

    message.attack_buff_count = battle.get_attack_buff_count()
    message.attack_buff_temporary_count = battle.get_attack_buff_temporary_count()
    if len(nodes) > 0:
        message.map_level = nodes[0].level
        message.defence_buff_count = nodes[0].get_defence_buff_count()
    else:
        message.map_level = 1
        message.defence_buff_count = 0

    if battle.is_at_war():
        for node in nodes:
            _pack_battle_map_node_info(node, message.nodes.add(), now)
            
            box = message.boxes.add()
            box.id = node.index
            reward_record = node.get_reward_record()
            for user_id, user_name, icon_id, item_id, item_num, time in reward_record:
                member = box.members.add()
                member.user_id = user_id
                member.name = user_name
                member.headIconId = icon_id
                member.item_id = item_id
                member.item_num = item_num
                member.passedTime = now - time


def _pack_battle_map_node_info(node, message, now):
    """打包战斗地图节点信息
    """
    message.index = node.index
    message.status = node.status
    message.defender.user_id = node.defender_user_id
    message.defender.name = node.get_readable_defender_name()
    message.defender.headicon_id = node.defender_user_icon
    message.defender.level = node.defender_user_level
    message.is_defender_robot = node.defender_is_robot

    #阵容
    (teams, heroes) = node.get_defender_team_detail()
    for (index, hero_basic_id) in enumerate(teams):
        team_index = index / 3
        if len(message.teams) == team_index:
            team = message.teams.add()
            team.index = team_index
        else:
            team = message.teams[team_index]

        if hero_basic_id != 0:
            _pack_battle_map_node_hero_info(heroes[hero_basic_id], team.heroes.add())

    #科技信息
    for tech_basic_id in node.get_defender_techs():
        message.battle_tech_ids.append(tech_basic_id)

    #message.battle_left_time = node.get_battle_left_time(now)
    message.city_level = node.city_level
    message.current_soldier_num = node.current_soldier_num
    message.total_soldier_num = node.total_soldier_num


def _pack_battle_map_node_hero_info(info, message):
    """
    打包防守阵容中的英雄信息
    Args:
        info:
        (basic_id, level, star,
        [skill_id1, skill_id2, skill_id3, skill_id4],
        soldier_basic_id, soldier_level,
        [equipment_id1, equipment_id2, equipment_id3],
        evolution_level,
        [stones])
    """
    if info is None:
        message.basic_id = 0
        return

    message.basic_id = info[0]
    message.level = info[1]
    message.star_level = info[2]
    message.soldier_basic_id = info[4]
    message.soldier_level = info[5]
    message.evolution_level = info[7]
    message.hero_awakening = info[10]
    message.hero_refine_info.refineLv = info[11]
    message.hero_refine_info.refineState = 0

    skills_id = info[3]
    if len(skills_id) > 0:
        message.first_skill_id = skills_id[0]
        message.second_skill_id = skills_id[1]
        message.third_skill_id = skills_id[2]
        message.fourth_skill_id = skills_id[3]

    equipments_id = info[6]
    if len(equipments_id) > 0:
        message.equipment_weapon_id = equipments_id[0]
        message.equipment_armor_id = equipments_id[1]
        message.equipment_treasure_id = equipments_id[2]

    stones = info[8]
    if len(stones) > 0:
        message.stone_weapon.extend(stones[0:4])
        message.stone_armor.extend(stones[4:8])
        message.stone_treasure.extend(stones[8:12])

    herostars_id = info[9]
    if len(herostars_id) > 0:
        for herostar_id in herostars_id:
            message.hero_star.append(herostar_id)

    refine_values = info[12]
    refine_types = HeroInfo.REFINE_TYPES
    if len(refine_values) > 0:
        assert len(refine_values) == len(refine_types)
        for i in xrange(len(refine_values)):
            attribute = message.hero_refine_attributes.add()
            attribute.type = getattr(attribute, refine_types[i])
            attribute.value = refine_values[i]


def pack_battle_record_info(record, message, now):
    if record.is_attacker_win:
        message.result = message.WIN
    else:
        message.result = message.LOSE
    message.attack_user.user_id = record.attacker_user_id
    message.attack_user.name = record.get_readable_attacker_name()
    message.attack_user.headicon_id = record.attacker_user_icon
    message.attack_user.union_id = record.attacker_union_id

    message.defence_user.user_id = record.defender_user_id
    message.defence_user.name = record.get_readable_defender_name()
    message.defence_user.headicon_id = record.defender_user_icon
    message.defence_user.union_id = record.defender_union_id

    message.passed_time = now - record.time

def pack_donate_box_info(data, user_id, donate_box, message, timer):
    """打包捐献箱"""
    message.treasurebox_id = donate_box.box_id

    for item_id in data_loader.UnionDonateTreasureBoxBasicInfo_dict[donate_box.box_id].reward.itemIds:
        message.reward.item_id.append(item_id)
    for item_num in data_loader.UnionDonateTreasureBoxBasicInfo_dict[donate_box.box_id].reward.itemNums:
        message.reward.item_num.append(item_num)
    message.reward.resource.gold = data_loader.UnionDonateTreasureBoxBasicInfo_dict[donate_box.box_id].reward.gold

    message.during_time = timer.now - donate_box.start_time
    message.donate_progress = donate_box.progress
    message.next_refresh_time#TODO:计算下次刷新的时间
    message.current_state = donate_box.status
    if donate_business.is_able_to_refresh_donate_box(data, donate_box.box_id, user_id, timer) == 0:
        message.is_refresh = True
    else:
        message.is_refresh = False

def pack_donate_record_info(record, message):
    """打包捐献记录"""
    message.user_id = record.user_id
    message.user_name = record.get_readable_name()
    message.box_id = record.box_id
    message.grade = record.grade
    message.add_honor = record.add_honor
    message.add_progress = record.add_progress
    message.add_prosperity = record.add_prosperity

def pack_donate_reward_info(item_list, resource_list, message):
    """打包宝箱奖励信息"""
    (id_list, num_list) = item_list
    (money, gold, food) = resource_list

    for id in id_list:
        message.item_id.append(id)
    for num in num_list:
        message.item_num.append(num)

    message.resource.money = money
    message.resource.gold = gold
    message.resource.food = food

def pack_union_battle_rival(battle_node, message):
    """打包联盟战对手信息"""
    message.teams = battle_node.defender_team
    message.heroes_basic_id = battle_node.heroes_basic_id
    message.heroes_level = battle_node.heroes_level
    message.heroes_star = battle_node.heroes_star
    message.heroes_skill_id = battle_node.heroes_skill_id
    message.heroes_soldier_basic_id = battle_node.heroes_soldier_basic_id
    message.heroes_soldier_level = battle_node.heroes_soldier_level
    message.heroes_equipment_id = battle_node.heroes_equipment_id
    message.heroes_evolution_level = battle_node.heroes_evolution_level
    message.heroes_stone = battle_node.heroes_stone_id
