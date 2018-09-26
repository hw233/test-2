#coding:utf8
"""
Created on 2015-02-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : pack_xxx的作用是将data转化为proto的res返回
         info是data, message是proto
"""

import time
import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.building import BuildingInfo
from app.data.hero import HeroInfo
from app.data.team import TeamInfo
from app.data.item import ItemInfo
from app.data.mail import MailInfo
from app.data.battle import BattleInfo
from app.data.node import NodeInfo
from app.data.arena import ArenaInfo
from app.data.arena_record import ArenaRecordInfo
from app.data.melee import MeleeInfo
from app.data.anneal import AnnealInfo
from app.data.worldboss import WorldBossInfo
from app.data.expand_dungeon import ExpandDungeonInfo
from app.data.basic_activity import BasicActivityInfo
from app.business import account as account_business
from app.business import worldboss as worldboss_business
from app.business import union_boss as union_boss_business
from app.business import expand_dungeon as expand_dungeon_business
from app.data.basic_activity_hero_reward import BasicActivityHeroRewardInfo
import datetime


def pack_monarch_info(info, message):
    message.user_id = info.id
    message.name = info.get_readable_name()
    message.level = info.level
    message.exp = info.exp
    message.headicon_id = info.icon_id
    message.vip_level = info.vip_level
    message.vip_points = info.vip_points
    message.create_time = info.create_time
    message.invite_code = info.get_invite_code()
    message.inviter = info.inviter
    message.country = info.country
    message.coin = 0
    message.payment = 0


def pack_resource_info(resource, message):
    message.money = resource.money
    message.food = resource.food
    message.gold = resource.gold
    message.soul = resource.soul
    message.achievement = resource.achievement


def pack_item_info(info, message):
    message.basic_id = info.basic_id
    message.num = info.num


def pack_goods_info(goods, message):
    message.id = goods.id
    message.type = goods.type
    message.item.basic_id = goods.item_basic_id
    message.item.num = goods.item_num
    message.price = goods.price
    message.discount = goods.discount
    message.is_sold = goods.is_sold


def pack_city_info(info, message):
    message.basic_id = info.basic_id
    message.name = info.name


def pack_hero_info(info, message, now, with_skill = True, with_detail = True):
    message.basic_id = info.basic_id
    message.level = info.level
    message.evolution_level = info.evolution_level
    message.exp = info.exp
    message.star_level = info.star
    message.soldier_basic_id = info.soldier_basic_id
    message.soldier_level = info.soldier_level

    if with_detail == False:
        return 

    if with_skill:
        #与客户端约定，不传skill，客户端会按照当前英雄等级升满技能
        skills = utils.split_to_int(info.skills_id)
        message.first_skill_id = skills[0]
        message.second_skill_id = skills[1]
        message.third_skill_id = skills[2]
        message.fourth_skill_id = skills[3]

    message.equipment_weapon_id = info.get_equipment(info.EQUIPMENT_TYPE_WEAPON)
    message.equipment_armor_id = info.get_equipment(info.EQUIPMENT_TYPE_ARMOR)
    message.equipment_treasure_id = info.get_equipment(info.EQUIPMENT_TYPE_TREASURE)

    for stone in info.get_equipment_stones(info.EQUIPMENT_TYPE_WEAPON):
        message.stone_weapon.append(stone)
    for stone in info.get_equipment_stones(info.EQUIPMENT_TYPE_ARMOR):
        message.stone_armor.append(stone)
    for stone in info.get_equipment_stones(info.EQUIPMENT_TYPE_TREASURE):
        message.stone_treasure.append(stone)

    if info.place_type == info.PLACE_TYPE_BUILDING:
        message.building_basic_id = BuildingInfo.get_basic_id(info.place_id)
        message.city_basic_id = BuildingInfo.get_city_basic_id(info.place_id)
        message.location_index = BuildingInfo.get_location_index(info.place_id)
        message.garrison_passed_time = now - info.update_time
    elif info.place_type == info.PLACE_TYPE_NODE:
        message.node_id = NodeInfo.get_basic_id(info.place_id)
        message.garrison_passed_time = now - info.update_time

    message.battle_node_id = info.battle_node_basic_id

    for star_id in info.get_herostars():
        message.hero_star.append(star_id)
    
    message.hero_awakening = info.is_awaken
    
    refine_types = info.REFINE_TYPES
    refine_values = info.get_refine_values()
    _, refine_limits = info.refine_value_limits()
    
    assert len(refine_values) == len(refine_types)
    for i in xrange(len(refine_types)):
        attribute = message.hero_refine_attributes.add()
        attribute.type = getattr(attribute, refine_types[i])
        attribute.value = refine_values[i]

    assert len(refine_limits) == len(refine_types)
    for i in xrange(len(refine_types)):
        attribute = message.hero_refine_limits.add()
        attribute.type = getattr(attribute, refine_types[i])
        attribute.value = refine_limits[i]

    is_full = 1
    for i in xrange(len(refine_types)):
        if refine_values < refine_limits:
            is_full = 0

    message.hero_refine_info.refineLv = info.refine_level
    message.hero_refine_info.refineState = is_full

def pack_team_info(team, message):
    message.index = team.index
    #message.status = team.status

    heroes_id = team.get_heroes()
    assert len(heroes_id) == 3
    for hero_id in heroes_id:
        basic_id = HeroInfo.get_basic_id(hero_id)
        message.heroes.add().basic_id = basic_id

    message.battle_node_id = team.battle_node_basic_id
    message.union_battle_node_index = team.union_battle_node_index
    message.in_anneal_sweep = (team.anneal_sweep_floor != 0)


def pack_technology_info(info, message, now):
    message.basic_id = info.basic_id
    message.type = info.type
    message.is_upgrading = info.is_upgrade
    message.upgrade_start_time = info.start_time
    message.upgrade_consume_time = info.consume_time
    message.upgrade_passed_time = now - info.start_time
    message.building_basic_id = BuildingInfo.get_basic_id(info.building_id)
    message.city_basic_id = BuildingInfo.get_city_basic_id(info.building_id)
    message.location_index = BuildingInfo.get_location_index(info.building_id)


def pack_building_info(info, message, now):
    message.basic_id = info.basic_id
    message.city_basic_id = BuildingInfo.get_city_basic_id(info.id)
    message.location_index = info.slot_index

    message.level = info.level
    message.garrision_num = info.garrison_num
    hero_ids = utils.split_to_int(info.hero_ids)
    for id in hero_ids:
        message.hero_basic_ids.append(HeroInfo.get_basic_id(id))

    message.is_upgrading = info.is_upgrade
    message.upgrade_start_time = info.upgrade_start_time
    message.upgrade_consume_time = info.upgrade_consume_time
    message.upgrade_passed_time = now - message.upgrade_start_time


def pack_mission_info(info, message):
    message.basic_id = info.basic_id
    #message.type = info.type
    message.current_num = info.current_num


def pack_conscript_info(info, message, now):
    message.building_basic_id = BuildingInfo.get_basic_id(info.building_id)
    message.city_basic_id = BuildingInfo.get_city_basic_id(info.building_id)
    message.location_index = BuildingInfo.get_location_index(info.building_id)
    message.current_soldier_num = info.soldier_num
    message.lock_soldier_num = info.lock_soldier_num
    message.conscript_num = info.conscript_num
    if info.conscript_num != 0:
        message.total_conscript_time = info.end_time - info.start_time
        message.conscript_passed_time = now - info.start_time


def pack_money_draw_info(draw, message, now):
    message.search_num = draw.money_draw_free_num
    message.next_left_time = max(0, draw.money_draw_free_time - now)


def pack_gold_draw_info(draw, message, now):
    message.search_num = draw.gold_draw_free_num
    message.next_left_time = max(0, draw.gold_draw_free_time - now)


def pack_mail_info(mail, message, now):
    message.index = MailInfo.get_index(mail.id)
    message.type = mail.type
    message.state = mail.status
    message.passed_time = now - mail.time
    message.delete_after_used = mail.delete_after_used

    message.reward_resource.money = mail.reward_money
    message.reward_resource.food = mail.reward_food
    message.reward_resource.gold = mail.reward_gold

    for (basic_id, num) in mail.get_reward_items():
        item_message = message.reward_items.add()
        item_message.basic_id = basic_id
        item_message.num = num

    message.lost_resource.money = mail.lost_money
    message.lost_resource.food = mail.lost_food
    message.lost_resource.gold = mail.lost_gold
    message.lost_resource.soldier = mail.lost_soldier

    if mail.related_node_id != 0:
        message.node_id = NodeInfo.get_basic_id(mail.related_node_id)

    if mail.related_exploitation_type != 0:
        message.exploitation_type = mail.related_exploitation_type
        message.exploitation_level = mail.related_exploitation_level
        message.exploitation_progress = mail.related_exploitation_progress

    if mail.related_enemy_type != 0:
        message.enemy_type = mail.related_enemy_type
        message.enemy_name = mail.get_readable_enemy_name()
        message.battle_win = mail.related_battle_win

    message.basic_id = mail.basic_id
    #if not mail.is_content_empty():
    #    message.subject = mail.subject
    #    message.sender = mail.sender
    #    message.content = mail.content
    if mail.subject != '':
        message.subject = mail.subject
    if mail.sender != '':
        message.sender = mail.sender
    if mail.content != '':
        message.content = mail.content

    if mail.arena_title_level != 0:
        message.arena_title_level = mail.arena_title_level
    if mail.arena_coin != 0:
        message.arena_coin = mail.arena_coin

    if mail.legendcity_id != 0:
        message.legendcity_id = mail.legendcity_id
        message.legendcity_position = mail.legendcity_position


def pack_sign_info(signin, message):
    """打包所有签到信息
    由于签到信息目前客户端不读
    所以服务器需要读取配置信息，打包返回给客户端
    """
    sign_info = data_loader.SignInGiftBasicInfo_dict
    keys = data_loader.SignInGiftBasicInfo_dict.keys()
    keys.sort()
    for index in keys:
        gift = message.gifts.add()
        if sign_info[index].itemBasicId != 0:
            gift.item.basic_id = sign_info[index].itemBasicId
            gift.item.num = sign_info[index].itemNum
        if sign_info[index].heroBasicId != 0:
            gift.hero.basic_id = sign_info[index].heroBasicId

    vip_info = data_loader.SignInVipAdditionBasicInfo_dict
    for index in vip_info:
        vip_add = message.vip_additions.add()
        vip_add.gift_index = index
        vip_add.vip_level = vip_info[index].vipLevel
        vip_add.vip_times = vip_info[index].vipTimes

    message.current_index = signin.index
    cur_time = int(time.time())
    is_same_day = utils.is_same_day(cur_time, signin.last_time)
    if is_same_day:
        message.available_index = signin.index
    else:
        message.available_index = signin.index + 1


def pack_rival_info(rival, message):
    """打包敌人信息
    Args:
        rival[RivalInfo]
        message[rival_pb2.RivalInfo]
    """
    message.node_id = 0 #TODO delete
    message.type = rival.type
    if rival.type == NodeInfo.ENEMY_TYPE_DUNGEON:
        message.rival_id = rival.dungeon_id
        message.level = rival.dungeon_level
    else:
        message.rival_id = rival.rival_id
        message.level = rival.level
    message.name = rival.get_readable_name()
    message.icon_id = rival.icon_id
    message.score = rival.score
    message.country = rival.country

    #阵容
    for (index, enemy) in enumerate(rival.get_enemy_detail()):
        team_index = index / 3
        if len(message.teams) == team_index:
            team = message.teams.add()
            team.index = team_index
        else:
            team = message.teams[team_index]

        _pack_rival_hero_info(enemy, team.heroes.add())

    for buff_id in rival.get_buff():
        message.buff_ids.append(buff_id)

    #科技
    tech_basic_ids = rival.get_technology_basic_ids()
    for basic_id in tech_basic_ids:
        message.battle_tech_ids.append(basic_id)

    #奖励
    message.reward_resource.money = rival.reward_money
    message.reward_resource.food = rival.reward_food
    for (basic_id, num) in rival.get_reward_items():
        item = message.reward_items.add()
        item.basic_id = basic_id
        item.num = num


def _pack_rival_hero_info(info, message):
    """
    打包敌人阵容中的英雄信息
    Args:
        info:
        (basic_id, level, star,
        [skill_id1, skill_id2, skill_id3, skill_id4],
        soldier_basic_id, soldier_level,
        [equipment_id1, equipment_id2, equipment_id3],
        [stone_weapon_id1, stone_weapon_id2, stone_weapon_id3, stone_weapon_id4],
        [stone_armor_id1, stone_armor_id2, stone_armor_id3, stone_armor_id4],
        [stone_treasure_id1, stone_treasure_id2, stone_treasure_id3, stone_treasure_id4],
        [herostar_id1, herostar_id2, herostar_id3, herostar_id4, herostar_id5, herostar_id6])
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

    stone_weapons_id = info[8]
    if len(stone_weapons_id) > 0:
        for stone_id in stone_weapons_id:
            message.stone_weapon.append(stone_id)

    stone_armors_id = info[9]
    if len(stone_armors_id) > 0:
        for stone_id in stone_armors_id:
            message.stone_armor.append(stone_id)

    stone_treasures_id = info[10]
    if len(stone_treasures_id) > 0:
        for stone_id in stone_treasures_id:
            message.stone_treasure.append(stone_id)

    herostars_id = info[11]
    if len(herostars_id) > 0:
        for herostar_id in herostars_id:
            message.hero_star.append(herostar_id)

    message.hero_awakening = info[12]
    message.hero_refine_info.refineLv = info[13]
    message.hero_refine_info.refineState = 0

    refine_values = info[14]
    refine_types = HeroInfo.REFINE_TYPES
    if len(refine_values) > 0:
        assert len(refine_values) == len(refine_types)
        for i in xrange(len(refine_values)):
            attribute = message.hero_refine_attributes.add()
            attribute.type = getattr(attribute, refine_types[i])
            attribute.value = refine_values[i]

def _pack_node_exploitation_info(data, node, message, now):
    message.node_id = node.basic_id #TODO delete
    message.type = node.exploit_type

    message.gather_speed = node.gather_speed
    message.gather_duration = now - node.gather_start_time

    message.total_time = node.exploit_total_time
    message.duration = now - node.exploit_start_time
    if node.is_exploit_money():
        message.total_money = node.exploit_reserve
        message.level = node.exploit_level

    elif node.is_exploit_food():
        message.total_food = node.exploit_reserve
        message.level = node.exploit_level

    elif node.is_exploit_gold():
        message.total_gold = node.exploit_reserve
        message.level = node.exploit_level

    elif node.is_exploit_material():
        message.level = node.exploit_level

    elif node.is_exploit_random_item():
        exploitation = data.exploitation.get()
        if node.is_exploit_exist():
            message.level = node.exploit_level
        else:
            message.level = exploitation.search_level
        message.progress = exploitation.get_search_progress()

    elif node.is_exploit_enchant_material():
        exploitation = data.exploitation.get()
        if node.is_exploit_exist():
            message.level = node.exploit_level
        else:
            message.level = exploitation.deep_mining_level
        message.progress = exploitation.get_deep_mining_progress()

    elif node.is_exploit_hero_star_soul():
        exploitation = data.exploitation.get()
        if node.is_exploit_exist():
            message.level = node.exploit_level
        else:
            message.level = exploitation.hermit_level
        message.progress = exploitation.get_hermit_progress()

    for hero_id in node.get_exploit_hero():
        message.hero_basic_ids.append(HeroInfo.get_basic_id(hero_id))


def _pack_node_lucky_event_info(node, message, now):
    message.type = node.event_type
    message.arise_duration = now - node.event_arise_time
    if node.is_event_launched():
        message.is_launched = True
        message.launch_duration = now - node.event_launch_time


def _pack_node_appoint_info(battle, message, now):
    team_indexes = utils.split_to_int(battle.teams_index)
    for team_index in team_indexes:
        message.team_indexes.append(team_index)

    message.total_time = battle.appoint_total_time
    message.passed_time = now - battle.time


def _pack_node_protection_info(node, message, now):
    if node.is_own_city():
        message.type = 1
    else:
        message.type = 2

    message.total_time = node.protect_total_time
    message.passed_time = now - node.protect_start_time


def _pack_node_increase_info(node, message, now):
    message.rate = node.increase_rate
    message.total_time = node.increase_total_time
    message.passed_time = now - node.increase_start_time


def pack_node_info(data, node, message, now):
    """打包单个节点信息
    """
    message.basic_id = node.basic_id
    message.type = node.type
    message.status = node.status
    message.hold_duration = now - node.hold_time

    if node.is_rival_exist():
        rival_id = node.rival_id
        rival = data.rival_list.get(rival_id, True)
        if rival is not None:
            pack_rival_info(rival, message.rival)

    if node.is_exploit_exist():
        _pack_node_exploitation_info(data, node, message.exploitation, now)

    if node.is_event_arised():
        _pack_node_lucky_event_info(node, message.lucky_event, now)

    battle = data.battle_list.get(node.id)
    if battle is not None and battle.is_appoint:
        _pack_node_appoint_info(battle, message.appoint, now)

    if node.is_in_protect(now):
        _pack_node_protection_info(node, message.protect, now)

    if node.is_in_increase(now):
        _pack_node_increase_info(node, message.increase, now)


def pack_map_info(data, map, message, now):
    """打包世界地图信息
    不打包不可见节点
    Args:
        message[node_pb2.MapInfo]
    """
    for node in data.node_list.get_all(True):
        if node.is_visible():
            pack_node_info(data, node, message.nodes.add(), now)

    #message.next_war_gap = map.next_war_time - now    #war事件已取消
    message.next_luck_gap = map.next_luck_time - now


def pack_battle_reward_info(info, message):
    message.resource.money = info.reward_money
    message.resource.food = info.reward_food

    for (basic_id, num) in info.get_reward_items():
        item = message.items.add()
        item.basic_id = basic_id
        item.num = num

    message.hero_exp = info.reward_hero_exp
    message.monarch_exp = info.reward_user_exp


def pack_guide_info(user, message):
    stages = user.get_guide_progress()
    for s in stages:
        message.stages.append(s)


def pack_activity_info(activity, basic_activity, basic_steps, message, now, basic_data, data, cat_list ):
    message.id = activity.basic_id
    message.type_id = basic_activity.type_id
    
    if len(basic_activity.description) > 0:
        message.description = base64.b64decode(basic_activity.description)#.encode('utf-8')
    if len(basic_activity.icon_name) > 0:
        message.icon_name = base64.b64decode(basic_activity.icon_name)#.encode('utf-8')
    if len(basic_activity.name) > 0:
        message.title = base64.b64decode(basic_activity.name)#.encode('utf-8')
    for value in activity.get_step_progress():
        message.step_progress.append(value)
    for status in activity.get_reward_status():
        message.reward_status.append(status)
    for target in activity.get_step_target():
        message.step_target.append(target)

    if activity.has_time_limit():
        message.duration = activity.end_time - now

    if activity.start_time != 0:
        ltime = time.localtime(activity.start_time)
        message.begin_date = time.strftime("%Y-%m-%d", ltime)#.encode('utf-8')
        if activity.end_time != 0:
            #结束时间是0点，需要减1s，否则日期错误
            ltime = time.localtime(activity.end_time - 1)
            message.end_date = time.strftime("%Y-%m-%d", ltime)#.encode('utf-8') 

    step_status = activity.get_reward_status()
    for step_index in range(0, len(step_status)):
        step_id = basic_activity.get_steps()[step_index]
        step_info_proto = message.step_infos.add()
        step_info_proto.id = step_id

        for basic_step in basic_steps:
            if step_id == basic_step.id:
                stepInfo = basic_step
                break;

        for hero_basic_id in stepInfo.get_heroes_basic_id():
            step_info_proto.reward_hero_basic_ids.append(hero_basic_id)

        items = stepInfo.get_items()
        items_id = []
        items_num = []
        for item in items:
            items_id.append(item[0])
            items_num.append(item[1])

        for i in range(0, len(items_id)):
            item = step_info_proto.reward_items.add()
            item.basic_id = items_id[i]
            item.num = items_num[i]

        if stepInfo.gold > 0:
            step_info_proto.reward_gold = stepInfo.gold

        if stepInfo.value1 > 0:
            step_info_proto.value1 = stepInfo.value1

        if stepInfo.value2 > 0:
            step_info_proto.value2 = stepInfo.value2
        if len(stepInfo.description) > 0:
            step_info_proto.description = base64.b64decode(stepInfo.description)#.encode('utf-8')

    resource = data.resource.get()
    if (basic_activity.type_id == 
            int(float(data_loader.OtherBasicInfo_dict["activity_hero_type_id"].value))):
        message.hero_basic_id = basic_activity.hero_basic_id
    elif basic_activity.type_id == 30 :
        message.hero_basic_id = resource.total_gain_cat
        for cat in cat_list:
            msg_cat = message.cats.add()
            msg_cat.name = cat.name
            msg_cat.gold = cat.gold

    if basic_activity.type_id == 29 :
        rewards_id = BasicActivityHeroRewardInfo.generate_all_ids(basic_activity.id)
        for reward_id in rewards_id:
            reward_info_proto = message.rewards_info.add()
            
            reward = basic_data.activity_hero_reward_list.get(reward_id)
            if reward is None:
                logger.warning("not exist activity treasure reward[id=%d]" % reward_id)
                continue
            reward_info_proto.id = reward_id
            reward_info_proto.level = reward.level
            item = reward.get_items()
            reward_info_proto.reward_item.basic_id = item[0][0]
            reward_info_proto.reward_item.num = item[0][1]
               

    message.weight = basic_activity.weight


def pack_arena_info(user, arena, message, now, ranking = 0, with_own = True):
    """ranking [int] 0表示不需要排名信息
    """
    message.index = arena.index

    #描述
    message.open_time_des = data_loader.ServerDescKeyInfo_dict["arena_open_time"].value.encode("utf-8")

    if not user.allow_pvp_arena:
        message.status = 3    #锁定
        message.end_time = 0
        return

    if arena.is_arena_active(now):
        message.status = 2     #激活
    else:
        message.status = 1     #未激活

    message.coin = arena.coin
    message.end_time = arena.next_time - now
    message.refresh_num = arena.refresh_num

    if with_own:
        message.own.ranking_index = ranking
        message.own.score = ArenaInfo.get_real_score(arena.score)


def pack_melee_info(user, melee, message, now, ranking = 0, with_own = True):
    """ranking [int] 0表示不需要排名信息
    """
    message.index = melee.index

    #描述
    message.open_time_des = data_loader.ServerDescKeyInfo_dict["melee_open_time"].value.encode("utf-8")

    if not melee.is_able_to_unlock(user):
        message.status = 3    #锁定
        message.end_time = 0
        return

    if melee.is_arena_active(now):
        message.status = 2     #激活
    else:
        message.status = 1     #未激活

    message.end_time = melee.next_time - now
    message.refresh_num = melee.refresh_num

    if with_own:
        message.own.ranking_index = ranking
        message.own.score = MeleeInfo.get_real_score(melee.score)


def pack_arena_reward_info(arena, message):
    """胜场奖励
    """
    message.current_win_num = arena.current_win_num
    message.need_win_num = data_loader.ArenaWinNumRewardBasicInfo_dict[
            arena.win_num_reward_basic_id].needWinNum

    chest = data_loader.ChestInfo_dict[arena.chest_basic_id]
    message.chest_level = chest.level
    message.reward_resource.money = chest.reward.money
    message.reward_resource.food = chest.reward.food
    message.reward_resource.gold = chest.reward.gold
    for i in range(len(chest.reward.itemBasicIds)):
        item = message.reward_items.add()
        item.basic_id = chest.reward.itemBasicIds[i]
        item.num = chest.reward.itemNums[i]


def pack_arena_player(rival, message):
    """对手阵容
    """
    message.user_id = rival.rival_id
    message.level = rival.level
    message.name = rival.get_readable_name()
    message.icon_id = rival.icon_id
    message.score = rival.arena_score
    message.win_score = rival.win_score
    if rival.arena_buff != 0:
        message.buff_id = rival.arena_buff
    message.ranking_index = rival.arena_ranking

    #阵容
    for (index, enemy) in enumerate(rival.get_enemy_detail()):
        team_index = index / 3
        if len(message.teams) == team_index:
            team = message.teams.add()
            team.index = team_index
        else:
            team = message.teams[team_index]

        _pack_rival_hero_info(enemy, team.heroes.add())

    #科技
    tech_basic_ids = rival.get_technology_basic_ids()
    for basic_id in tech_basic_ids:
        message.battle_tech_ids.append(basic_id)


def pack_melee_player(rival, message):
    """对手阵容
    """
    message.user_id = rival.rival_id
    message.level = rival.level
    message.name = rival.get_readable_name()
    message.icon_id = rival.icon_id
    message.score = rival.arena_score
    message.win_score = rival.win_score
    if rival.arena_buff != 0:
        message.buff_id = rival.arena_buff
    message.ranking_index = rival.arena_ranking

    #阵容
    team = message.teams.add()
    team.index = 0
    for (index, enemy) in enumerate(rival.get_enemy_detail()):
        _pack_rival_hero_info(enemy, team.heroes.add())

    for position in rival.get_heroes_position():
        team.hero_positions.append(position)

    #科技
    tech_basic_ids = rival.get_technology_basic_ids()
    for basic_id in tech_basic_ids:
        message.battle_tech_ids.append(basic_id)


def pack_arena_record(record, message):
    """对战记录
    """
    message.index = ArenaRecordInfo.get_index(record.id)
    message.user_id = record.player_id
    message.name = record.get_readable_name()
    message.level = record.level
    message.icon_id = record.icon_id
    message.status = record.status
    message.score_delta = record.score_delta


def pack_legendcity_record(record, message):
    """史实城对战记录
    """
    if record.is_win:
        message.result = message.WIN
    else:
        message.result = message.LOSE

    if record.is_attacker:
        message.side = message.ATTACKER
    else:
        message.side = message.DEFENDER

    message.user.city_id = record.city_id
    message.user.level = record.user_position_level
    message.user.user.user_id = record.user_id
    message.user.user.name = record.get_readable_user_name()
    message.user.user.level = record.user_level
    message.user.user.headicon_id = record.user_icon
    for buff_id in record.get_user_buffs():
        message.user.buffs.add().city_buff_id = buff_id

    message.rival.city_id = record.city_id
    message.rival.level = record.rival_position_level
    message.rival.user.user_id = record.rival_id
    message.rival.user.name = record.get_readable_rival_name()
    message.rival.user.level = record.rival_level
    message.rival.user.headicon_id = record.rival_icon
    for buff_id in record.get_rival_buffs():
        message.rival.buffs.add().city_buff_id = buff_id

    message.user_battle_score = record.user_battle_score
    message.rival_battle_score = record.rival_battle_score
    message.time = record.time


def pack_energy_info(energy, message, now):
    """打包政令信息
    """
    message.current_energy = energy.energy
    message.passed_time = now - energy.last_time
    message.buy_num = energy.buy_num
    message.next_refresh_gap = energy.next_refresh_time - now

    message.event_types.append(NodeInfo.EVENT_TYPE_TAX)
    message.event_indexes.append(energy.trigger_tax_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_FARM)
    message.event_indexes.append(energy.trigger_farm_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_MINING)
    message.event_indexes.append(energy.trigger_mining_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_GOLD)
    message.event_indexes.append(energy.trigger_gold_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_JUNGLE)
    message.event_indexes.append(energy.trigger_jungle_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_DUNGEON)
    message.event_indexes.append(energy.trigger_dungeon_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_VISIT)
    message.event_indexes.append(energy.trigger_visit_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_SCOUT)
    message.event_indexes.append(energy.trigger_scout_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_SEARCH)
    message.event_indexes.append(energy.trigger_search_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_DEEP_MINING)
    message.event_indexes.append(energy.trigger_deep_mining_num)

    message.event_types.append(NodeInfo.EVENT_TYPE_HERMIT)
    message.event_indexes.append(energy.trigger_hermit_num)


def pack_pray_info(pray, message, now):
    """打包祈福信息
    """
    #resource祈福的data
    pray_data = message.prays.add()
    pray_data.pray_type = 1
    pray_data.current_pray_num = pray.resource_pray_num
    pray_data.refresh_num = pray.resource_refresh_num
    #hero祈福的data
    pray_data = message.prays.add()
    pray_data.pray_type = 2
    pray_data.current_pray_num = pray.hero_pray_num
    pray_data.refresh_num = pray.hero_refresh_num
    #material祈福的data
    pray_data = message.prays.add()
    pray_data.pray_type = 3
    pray_data.current_pray_num = pray.material_pray_num
    pray_data.refresh_num = pray.material_refresh_num

    if not pray.is_empty():
        _pack_pray_status(pray, message.pray_status)

    message.next_refresh_gap = pray.next_refresh_time - now


def _pack_pray_status(pray, message):
    items_id = utils.split_to_int(pray.items_id)
    items_num = utils.split_to_int(pray.items_num)
    choose_list = utils.split_to_int(pray.choose_list)
    initial_list = utils.split_to_int(pray.initial_list)

    for i in range(0, len(items_id)):
        item = message.items.add()
        item.basic_id = items_id[i]
        item.num = items_num[i]

    for index in choose_list:
        message.choose_list.append(index)

    for index in initial_list:
        message.initial_list.append(index)


def pack_chest_info(chest, message, now):
    """打包红包信息
    """
    message.next_gap_time = chest.next_start_time - now
    message.retain_time = chest.next_end_time - chest.next_start_time

    message.resource.money = chest.money
    message.resource.food = chest.food
    message.resource.gold = chest.gold

    items_info = chest.get_items_info()
    for (basic_id, num) in items_info:
        item_data = message.reward_items.add()
        item_data.basic_id = basic_id
        item_data.num = num


def pack_union_battle_individual_info(member, user, message):
    message.user.user_id = user.id
    message.user.name = user.get_readable_name()
    message.user.level = user.level
    message.user.headicon_id = user.icon_id
    message.user.union_id = member.union_id
    message.score = member.battle_score


def pack_ranking_info_of_user(user, value, ranking, message):
    message.ranking = ranking
    message.value = value

    message.id = user.id
    message.name = user.get_readable_name()
    message.level = user.level
    message.icon_id = user.icon_id


def pack_ranking_info_of_union(union, value, ranking, message):
    message.ranking = ranking
    message.value = value

    message.id = union.id
    message.name = union.get_readable_name()
    message.level = union.level
    message.icon_id = union.icon


def pack_anneal_info(data, anneal, message, now):
    """打包试炼场信息
    """
    message.attack_num = anneal.attack_num
    message.passed_time = now - anneal.last_time
    message.buy_num = anneal.buy_num
    message.next_refresh_gap = anneal.next_refresh_time - now

    #简单模式
    message.normal_mode.type = 1
    message.normal_mode.floor = anneal.normal_floor
    message.normal_mode.level = anneal.normal_level
    message.normal_mode.is_floor_finished = (anneal.normal_level == AnnealInfo.LEVEL_NUM_PER_FLOOR
            and anneal.normal_level_finished == True)
    message.normal_mode.is_reward_received = anneal.normal_reward_received
    items_info = anneal.calc_pass_reward(AnnealInfo.NORMAL_MODE)
    for (basic_id, num) in items_info:
        item_data = message.normal_mode.reward_items.add()
        item_data.basic_id = basic_id
        item_data.num = num

    #复杂模式
    message.hard_mode.type = 2
    message.hard_mode.floor = anneal.hard_floor
    message.hard_mode.level = anneal.hard_level
    message.hard_mode.is_floor_finished = (anneal.hard_level == AnnealInfo.LEVEL_NUM_PER_FLOOR
            and anneal.hard_level_finished == True)
    message.hard_mode.is_reward_received = anneal.hard_reward_received
    items_info = anneal.calc_pass_reward(AnnealInfo.HARD_MODE)
    for (basic_id, num) in items_info:
        item_data = message.hard_mode.reward_items.add()
        item_data.basic_id = basic_id
        item_data.num = num

    #扫荡信息
    if anneal.is_in_sweep():
        message.sweep.direction = anneal.sweep_direction
        message.sweep.floor = anneal.sweep_floor
        message.sweep.total_time = anneal.sweep_total_time
        message.sweep.passed_time = now - anneal.sweep_start_time

        teams_index = anneal.get_sweep_teams_index()
        for team_index in teams_index:
            team_id = TeamInfo.generate_id(data.id, team_index)
            team = data.team_list.get(team_id)
            pack_team_info(team, message.sweep.teams.add())

    anneal_max_floor = int(float(data_loader.AnnealConfInfo_dict['anneal_max_floor'].value))
    for i in xrange(anneal_max_floor):
        message.hard_attack_num.append(anneal.get_hrad_attack_remain_num(i+1))
        message.hard_reset_num.append(anneal.get_hard_reset_num(i+1))


def pack_basic_activity_info(basic_activity, message, now):
    """打包活动基本信息
    """
    message.id = basic_activity.id
    message.type_id = basic_activity.type_id
    message.start_time = basic_activity.start_time
    message.end_time = basic_activity.end_time
    message.start_day = basic_activity.start_day
    message.end_day = basic_activity.end_day
    message.icon_name = base64.b64decode(basic_activity.icon_name)
    message.name = base64.b64decode(basic_activity.name)
    message.description = base64.b64decode(basic_activity.description)
    message.hero_basic_id = basic_activity.hero_basic_id
    for step_id in basic_activity.get_steps():
        message.steps_id.append(step_id)


def pack_basic_activity_step_info(basic_step, message, now):
    """打包活动step基本信息
    """
    message.id = basic_step.id
    message.target = basic_step.target
    message.default_lock = basic_step.default_lock
    for hero_id in basic_step.get_heroes_basic_id():
        message.heroes_basic_id.append(hero_id)

    for (item_id, item_num) in basic_step.get_items():
        item_msg = message.reward_items.add()
        item_msg.basic_id = item_id
        item_msg.num = item_num

    message.gold = basic_step.gold
    message.description = base64.b64decode(basic_step.description)
    message.value1 = basic_step.value1
    message.value2 = basic_step.value2


def pack_basic_hero_reward_info(basic_reward, message, now):
    """打包限时英雄活动奖励基本信息
    """
    message.id = basic_reward.original_id
    message.level = basic_reward.level
 
    for (item_id, item_num) in basic_reward.get_items():
        item_msg = message.reward_items.add()
        item_msg.basic_id = item_id
        item_msg.num = item_num

def pack_basic_reward_info(basic_reward, message, now):
    """转盘奖励基本信息
    """
    message.id = basic_reward.original_id
    message.level = basic_reward.level

    (item_id, item_num) = basic_reward.get_items()
    item_msg = message.reward_items
    item_msg.basic_id = item_id
    item_msg.num = item_num



def pack_basic_worldboss_info(basic_worldboss, message, now):
    """打包世界boss基本信息
    """
    message.id = basic_worldboss.id
    message.date = basic_worldboss.date
    message.start_time = basic_worldboss.start_time
    message.end_time = basic_worldboss.end_time
    message.description = base64.b64decode(basic_worldboss.description)
    message.total_soldier_num = basic_worldboss.total_soldier_num


def pack_worldboss_info(worldboss, user, message, now):
    """打包世界boss信息
    """
    open_flags = account_business.get_flags()
    if "is_server_open_worldboss" not in open_flags:
        message.status = WorldBossInfo.DISABLE
        return True

    if not worldboss.is_unlock():
        message.status = WorldBossInfo.LOCKED
        message.limit_level = int(float(data_loader.OtherBasicInfo_dict["unlock_worldboss_level"].value))
        return

    message.kill_user_name = base64.b64decode(worldboss.kill_user_name)
    message.kill_user_id = worldboss.kill_user_id

    if not worldboss.is_arised():
        message.status = WorldBossInfo.INACTIVE
        message.end_time = 3600  #当前没有boss，一小时后再访问，以免当天更新了boss
        return
    else:
        if now < worldboss.start_time:
            message.status = WorldBossInfo.BEFORE_BATTLE
            message.end_time = worldboss.start_time - now + (user.id % 220)
        elif now > worldboss.end_time:
            message.status = WorldBossInfo.AFTER_BATTLE
            message.end_time = utils.get_start_second(now) + 86400 - now#第二天的开始时间即为当天的结束时间
        else:
            message.status = WorldBossInfo.IN_BATTLE
            message.end_time = worldboss.end_time - now + (user.id % 220)
        
        message.total_soldier_num = worldboss.total_soldier_num
        message.current_soldier_num = worldboss.current_soldier_num
        message.description = base64.b64decode(worldboss.description)

        #若未开启，不需要传其他内容
        if message.status == WorldBossInfo.BEFORE_BATTLE:
            return

        with_detail = True
        if message.status == WorldBossInfo.AFTER_BATTLE:
            with_detail = False

        #if worldboss.is_killed():
        #    return 

        #阵容
        teams = worldboss_business.generate_array_detail(worldboss, user)
        for i in range(3):
            team = message.first_teams.add()
            team.index = i 
            team = message.second_teams.add()
            team.index = i
            team = message.third_teams.add()
            team.index = i

        for i in range(len(teams[0])):
            team = message.first_teams[i/3]
            pack_hero_info(teams[0][i], team.heroes.add(), now, False, with_detail)
        for i in range(len(teams[1])):
            team = message.second_teams[i/3]
            pack_hero_info(teams[1][i], team.heroes.add(), now, False, with_detail)
        for i in range(len(teams[2])):
            team = message.third_teams[i/3]
            pack_hero_info(teams[2][i], team.heroes.add(), now, False, with_detail)

        #阵容是否可被攻击
        for can_attack in worldboss.get_can_attack_arrays_index():
            message.can_attack_teams_index.append(can_attack)

        #阵容的战功系数
        for ratio in worldboss.get_arrays_merit_ratio():
            message.teams_coefficient.append(ratio)

def pack_unionboss_info(unionboss, user, status, total_soldier_num, current_soldier_num, 
        message, now):
    """打包联盟boss"""
    message.total_soldier_num = total_soldier_num
    message.current_soldier_num = current_soldier_num
    message.description = unionboss.description()

    teams = union_boss_business.generate_array_detail(unionboss, user)
    for i in range(3):
        team = message.first_teams.add()
        team.index = i 
        team = message.second_teams.add()
        team.index = i
        team = message.third_teams.add()
        team.index = i

    for i in range(len(teams[0])):
        team = message.first_teams[i/3]
        pack_hero_info(teams[0][i], team.heroes.add(), now, False)
    for i in range(len(teams[1])):
        team = message.second_teams[i/3]
        pack_hero_info(teams[1][i], team.heroes.add(), now, False)
    for i in range(len(teams[2])):
        team = message.third_teams[i/3]
        pack_hero_info(teams[2][i], team.heroes.add(), now, False)

    for index in unionboss.get_can_attack_arrays_index():
        message.can_attack_teams_index.append(index)

    for ratio in unionboss.get_arrays_merit_ratio():
        message.teams_coefficient.append(ratio)

def pack_user_basic_info(user, message):
    """打包用户基本信息"""
    message.user_id = user.id
    message.level = user.level
    message.exp = user.exp
    message.vip_level = user.vip_level
    message.vip_points = user.vip_points
    message.name = user.get_readable_name()
    message.create_time = user.create_time
    message.last_login_time = user.last_login_time
    message.team_count = user.team_count
    message.country = user.country

def pack_flag_info(flags, message):
    """打包功能开关"""
    for flag in flags:
        m = message.add()
        m.flag_name = flag
        m.is_open = True

def pack_expand_dungeon_info(dungeon, user, message, battle_level, now, brief=False):
    """打包扩展副本信息"""
    message.id = dungeon.basic_id
    message.status = dungeon.status(user.level, now)
    message.end_time = dungeon.end_time(user.level, now)

    if not brief:
        enemy_team = expand_dungeon_business.generate_array_detail(dungeon, battle_level, user, "enemy")
        own_team = expand_dungeon_business.generate_array_detail(dungeon, battle_level, user, "own")

        for i in xrange(3):
            team = message.enemy_teams.add()
            team.index = i
            team = message.own_teams.add()
            team.index = i

        for i in xrange(len(enemy_team)):
            team = message.enemy_teams[i/3]
            hero = enemy_team[i]
            if hero is None:
                hero = team.heroes.add()
                hero.basic_id = 0
            else:
                pack_hero_info(hero, team.heroes.add(), now, False)

        for i in xrange(len(own_team)):
            team = message.own_teams[i/3]
            hero = own_team[i]
            if hero is None:
                hero = team.heroes.add()
                hero.basic_id = 0
            else:
                pack_hero_info(own_team[i], team.heroes.add(), now, False)

        #客户端需要显示的奖励
        items_id, items_num = ExpandDungeonInfo.generate_award(dungeon.basic_id, battle_level)
        for id in items_id:
            message.display_reward_item_ids.append(id)

    message.remain_num = dungeon.get_remain_num()
    message.reset_num = dungeon.reset_count

    ##客户端需要显示的奖励
    #items_id, items_num = ExpandDungeonInfo.generate_award(dungeon.basic_id, battle_level)
    #for id in items_id:
    #    message.display_reward_item_ids.append(id)


def pack_transfer_record(info, message):
    message.index = info.index
    message.user_id = info.rival_user_id
    message.name = info.get_rival_user_name()
    message.level = info.rival_level
    message.icon_id = info.rival_icon
    message.status = info.status
    message.self_rank = info.self_rank
    message.rival_rank = info.rival_rank


def pack_plunder_player(rival, message):
    """掠夺阵容
    """
    message.user_id = rival.rival_id
    message.level = rival.level
    message.name = rival.get_readable_name()
    message.icon_id = rival.icon_id
    message.battle_score = rival.score
    message.country = rival.country


def pack_plunder_record(plunder_record, message):
    """掠夺仇人阵容
    """
    message.user_id = plunder_record.rival_user_id
    message.level = plunder_record.level
    message.name = plunder_record.get_readable_name()
    message.icon_id = plunder_record.icon_id
    message.battle_score = plunder_record.score
    message.country = plunder_record.country
    message.hatred = plunder_record.hatred


def pack_plunder_player_with_detail(rival, message, union_info, 
        hatred, been_attacked_num, today_attack_money, today_attack_food,
        today_robbed_money, today_robbed_food): 
    """union_info: (union_id, union_name, union_icon_id)
       
    """
    message.user_id = rival.rival_id
    message.level = rival.level
    message.name = rival.get_readable_name()
    message.icon_id = rival.icon_id
    message.battle_score = rival.score
    message.country = rival.country
    message.in_protect = rival.in_protect
  
    if union_info != None:
        message.union_id = union_info[0]
        message.union_name = union_info[1]
        message.union_icon_id = union_info[2]

    message.hatred = hatred
    message.been_attacked_num = been_attacked_num
    message.today_attack_resource.money = today_attack_money
    message.today_attack_resource.food = today_attack_food
    message.today_robbed_resource.money = today_robbed_money
    message.today_robbed_resource.food = today_robbed_food

    #阵容
    for (index, enemy) in enumerate(rival.get_enemy_detail()):
        team_index = index / 3
        if len(message.teams) == team_index:
            team = message.teams.add()
            team.index = team_index
        else:
            team = message.teams[team_index]

        _pack_rival_hero_info(enemy, team.heroes.add())

    #科技
    tech_basic_ids = rival.get_technology_basic_ids()
    for basic_id in tech_basic_ids:
        message.battle_tech_ids.append(basic_id)

    message.reward_resource.money = rival.reward_money
    message.reward_resource.food = rival.reward_food
    for (basic_id, num) in rival.get_reward_items():
        item = message.reward_items.add()
        item.basic_id = basic_id
        item.num = num


def pack_button_tips(basic_data, data, message, now):
    """
    """
    user = data.user.get(True)
    #活动
    if_seven_day = False
    if_first_pay = False
    if_daily = False
    if_shop = False
    if_normal = True  #默认至少有普通活动
    if_festival = False
    #活动的红点提示
    if_seven_day_redpoint = False
    if_first_pay_redpoint = True
    if_daily_redpoint = False
    if_shop_redpoint = False
    if_normal_redpoint = False
    if_festival_redpoint = False

    for activity in data.activity_list.get_all():
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        if (basic_activity is not None and 
                activity.is_living(now, basic_activity.style_id, True)):
            if basic_activity.style_id == BasicActivityInfo.STYLE_SEVEN_DAY:
                if_seven_day = True
                if activity.can_accept_reward():
                    if_seven_day_redpoint = True
            elif basic_activity.style_id == BasicActivityInfo.STYLE_FIRST_PAY:
                if_first_pay = True
            elif basic_activity.style_id == BasicActivityInfo.STYLE_DAILY:
                if_daily = True
                if activity.can_accept_reward():
                    if_daily_redpoint = True
            elif basic_activity.style_id == BasicActivityInfo.STYLE_SHOP:
                if_shop = True
                if activity.can_accept_reward():
                    if_shop_redpoint = True               
            elif basic_activity.style_id == BasicActivityInfo.STYLE_NORMAL:
                if_normal = True
                if activity.can_accept_reward():
                    if_normal_redpoint = True
            elif basic_activity.style_id == BasicActivityInfo.STYLE_FESTIVAL:
                if_festival = True
                if activity.can_accept_reward():
                    if_festival_redpoint = True

    #临时：七天任务代替了七天活动
    for mission in data.mission_list.get_all():
        if mission.is_day7_type():
            if_seven_day = True
            if mission.is_finish(user.level):
                if_seven_day_redpoint = True
                break
    #开服七天活动按钮
    tip = message.button_tips.add()
    tip.index = 1
    if if_seven_day:
        tip.status = 1
    else:
        tip.status = 0
    if if_seven_day_redpoint:
        tip.redpoint = 1

    #首冲活动按钮
    tip = message.button_tips.add()
    tip.index = 2
    if if_first_pay:
        tip.status = 1
    else:
        tip.status = 0
    if if_first_pay_redpoint:
        tip.redpoint = 1

    #每日活动按钮
    tip = message.button_tips.add()
    tip.index = 3
    if if_daily:
        tip.status = 1
    else:
        tip.status = 0
    if if_daily_redpoint:
        tip.redpoint = 1

    #神秘商店活动按钮
    tip = message.button_tips.add()
    tip.index = 4
    if if_shop:
        tip.status = 1
    else:
        tip.status = 0
    if if_shop_redpoint:
        tip.redpoint = 1

    #普通活动按钮
    if not if_normal_redpoint:
        for mission in data.mission_list.get_all():
            if mission.is_activity_type():
                if_normal = True
                if mission.is_finish(user.level):
                    if_normal_redpoint = True
                    break

    tip = message.button_tips.add()
    tip.index = 5
    if if_normal:
        tip.status = 1
    else:
        tip.status = 0
    if if_normal_redpoint:
        tip.redpoint = 1

    #节日活动
    tip = message.button_tips.add()
    tip.index = 6
    if if_festival:
        tip.status = 1
    else:
        tip.status = 0
    if if_festival_redpoint:
        tip.redpoint = 1

    #联盟战按钮
    tip = message.button_tips.add()
    tip.index = 7
    #todo
    tip.status = 1

    #评定按钮
    tip = message.button_tips.add()
    tip.index = 8
    #todo
    tip.status = 1


def pack_luas(message):
    m = "xlua.hotfix(CS.MainWidgetElements, 'OnButtonClick', function(self)\n\
            CS.San.PanelMessageBox.Instance:Open('卧槽')\n\
    end)"
    message.append(m)


