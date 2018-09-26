#coding:utf8
"""
Created on 2015-12-25
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 敌人信息
"""

import base64
from utils import logger
from utils import utils
from app.data.node import NodeInfo
from app.data.hero import HeroInfo
from app.data.expand_dungeon import ExpandDungeonInfo
from datalib.data_loader import data_loader


ARENA_TYPE_ARENA = 1
ARENA_TYPE_MELEE = 2

class RivalInfo(object):

    __slots__ = [
            "id", "user_id", "real",
            "type", "score_min", "score_max",
            "rival_id", "defense_id",
            "level", "name", "icon_id", "score",
            "dungeon_id", "dungeon_level",
            "buffs", "technology", "pray",
            "team", "heroes_basic_id",
            "heroes_level", "heroes_star", "heroes_skill_id",
            "heroes_soldier_basic_id", "heroes_soldier_level",
            "heroes_equipment_id", "heroes_evolution_level",
            "heroes_weapon_stones_id","heroes_armor_stones_id", "heroes_treasure_stones_id",
            "heroes_herostar_id", "heroes_awaken",
            "heroes_refine_level", "heroes_refine_value",
            "heroes_position",
            "technology_basic_ids",
            "reward_money", "reward_food",
            "reward_user_exp", "reward_hero_exp",
            "reward_items_basic_id", "reward_items_num",
            "arena", "arena_score", "arena_ranking", "arena_buff",
            "win_score", "lose_score",
            "anneal", "anneal_type",
            "is_legendcity_rival", "legendcity_position_level", "legendcity_buffs",
            "country", "union_id", "in_protect",#TODO

            "is_rob", "offset", "count", "heroes_id"
            ]

    def __init__(self, id = 0, user_id = 0, real = False,
            type = 0, score_min = 0, score_max = 0,
            rival_id = 0, defense_id = 0,
            level = 0, name = '', icon_id = 0, score = 0,
            dungeon_id = 0, dungeon_level = 0,
            buffs = '', technology = '', pray = '',
            team = '', heroes_basic_id = '',
            heroes_level = '', heroes_star = '', heroes_skill_id = '',
            heroes_soldier_basic_id = '', heroes_soldier_level = '',
            heroes_equipment_id = '', heroes_evolution_level = '',
            heroes_weapon_stones_id = '', heroes_armor_stones_id = '', heroes_treasure_stones_id = '',
            heroes_herostar_id = '', heroes_awaken = '',
            heroes_refine_level = '', heroes_refine_value = '',
            heroes_position = '',
            technology_basic_ids = '',
            reward_money = 0, reward_food = 0,
            reward_user_exp = 0, reward_hero_exp = 0,
            reward_items_basic_id = '', reward_items_num = '',
            arena = 0, arena_score = 0, arena_ranking = 0, arena_buff = 0,
            win_score = 0, lose_score = 0,
            anneal = False, anneal_type = 0, country = 0, union_id = 0, in_protect = False):

        self.id = id
        self.user_id = user_id
        self.real = real

        #匹配条件
        self.type = type
        self.score_min = score_min
        self.score_max = score_max

        #敌人基本信息
        self.rival_id = rival_id
        self.level = level
        self.defense_id = defense_id
        self.name = name
        self.icon_id = icon_id
        self.score = score
        self.dungeon_id = dungeon_id
        self.dungeon_level = dungeon_level

        #敌人状态
        self.buffs = buffs
        self.technology = technology
        self.pray = pray

        #敌人阵容信息
        self.team = team
        self.heroes_basic_id = heroes_basic_id
        self.heroes_level = heroes_level
        self.heroes_star = heroes_star
        self.heroes_skill_id = heroes_skill_id
        self.heroes_soldier_basic_id = heroes_soldier_basic_id
        self.heroes_soldier_level = heroes_soldier_level
        self.heroes_equipment_id = heroes_equipment_id
        self.heroes_evolution_level = heroes_evolution_level
        self.heroes_weapon_stones_id = heroes_weapon_stones_id
        self.heroes_armor_stones_id = heroes_armor_stones_id
        self.heroes_treasure_stones_id = heroes_treasure_stones_id
        self.heroes_herostar_id = heroes_herostar_id
        self.heroes_awaken = heroes_awaken
        self.heroes_refine_level = heroes_refine_level
        self.heroes_refine_value = heroes_refine_value
        self.heroes_position = heroes_position
        self.technology_basic_ids = technology_basic_ids

        #击败敌人的奖励信息
        self.reward_money = reward_money
        self.reward_food = reward_food
        self.reward_user_exp = reward_user_exp
        self.reward_hero_exp = reward_hero_exp
        self.reward_items_basic_id = reward_items_basic_id
        self.reward_items_num = reward_items_num

        #演武场信息
        self.arena = arena
        self.arena_score = arena_score
        self.arena_ranking = arena_ranking
        self.arena_buff = arena_buff
        self.win_score = win_score                #赢了获得积分
        self.lose_score = lose_score              #输了扣减积分

        #史实城对手信息
        self.is_legendcity_rival = False
        self.legendcity_position_level = 0
        self.legendcity_buffs = ""

        #试炼场信息
        self.anneal = anneal
        self.anneal_type = anneal_type

        self.country = country
        self.union_id = union_id
        self.in_protect = in_protect

        self.is_rob = False


    @staticmethod
    def create(node_id, user_id):
        """创建
        """
        rival = RivalInfo(node_id, user_id)
        return rival


    @staticmethod
    def generate_revenge_id(user_id):
        ID_REVENGE = 0
        id = user_id << 32 | ID_REVENGE
        return id


    def get_readable_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.name)


    def set_buff(self, buff_id):
        """设置敌人 buff 加成，可能是增益，也可能是减益
        """
        buffs = utils.split_to_int(self.buffs)
        buffs.append(buff_id)
        self.buffs = utils.join_to_string(buffs)


    def get_buff(self):
        buffs = utils.split_to_int(self.buffs)
        return buffs


    def clear_buff(self):
        """消除敌人的 buff 加成
        """
        self.buffs = ''


    def clear(self):
        """清除敌人信息
        """
        self.type = 0
        self.rival_id = 0
        self.buffs = ''
        self.union_id = 0
        self.in_protect = False


    def is_real_player(self):
        return self.real


    def is_revenge_rival(self):
        """
        """
        return self.id == RivalInfo.generate_revenge_id(self.user_id)


    def is_arena_player(self):
        return self.arena == ARENA_TYPE_ARENA

    def is_melee_player(self):
        return self.arena == ARENA_TYPE_MELEE


    def is_anneal_rival(self):
        return self.anneal


    def is_worldboss_rival(self):
        return self.type == NodeInfo.ENEMY_TYPE_WORLDBOSS

    def is_expand_dungeon(self):
        return self.type == NodeInfo.ENEMY_TYPE_EXPAND_DUNGEON

    def set_pve_matching_condition(self, rival_type, score_min, score_max):
        """设置匹配条件
        """
        self.type = rival_type
        self.real = False
        self.score_min = score_min
        self.score_max = score_max


    def set_pve_enemy(self, enemy, name, spoils, rival_id = 0, icon_id = 1, country = 0):
        """设置 PVE 敌人信息
        """
        #基本信息
        self.rival_id = rival_id
        self.level = enemy.level
        self.defense_id = 0
        self.name = base64.b64encode(name)
        self.icon_id = icon_id
        self.score = enemy.score
        if country == 0:
            self.country = rival_id % 3 + 1
        else:
            self.country = country

        #阵容
        self.team = utils.join_to_string(enemy.teamInfo)
        self.heroes_basic_id = utils.join_to_string(enemy.heroBasicId)
        self.heroes_level = utils.join_to_string(enemy.heroLevel)
        self.heroes_star = utils.join_to_string(enemy.heroStarLevel)
        self.heroes_skill_id = '' #客户端自行根据等级填写
        self.heroes_soldier_basic_id = utils.join_to_string(enemy.soldierBasicId)
        self.heroes_soldier_level = utils.join_to_string(enemy.soldierLevel)
        self.heroes_equipment_id = utils.join_to_string(enemy.heroEquipmentId)
        self.heroes_evolution_level = utils.join_to_string(enemy.heroEvolutionLevel)
        self.heroes_weapon_stones_id = ''
        self.heroes_armor_stones_id = ''
        self.heroes_treasure_stones_id = ''
        self.heroes_herostar_id = ''
        self.heroes_awaken = ''
        self.heroes_refine_level = ''
        self.heroes_refine_value = ''

        #战斗奖励
        self.reward_money = 0
        self.reward_food = 0
        self.reward_user_exp = int(
                float(data_loader.OtherBasicInfo_dict["BattleMonarchGetExp"].value))
        self.reward_hero_exp = data_loader.MonarchLevelBasicInfo_dict[
                self.level].heroBattleExp

        #PVE 战利品
        self.reward_items_basic_id = utils.join_to_string([info[0] for info in spoils])
        self.reward_items_num = utils.join_to_string([info[1] for info in spoils])

        #PVE没有科技
        self.technology_basic_ids = ''


    def set_pvp_matching_condition(self, rival_type, score_min, score_max, is_rob = False):
        """设置匹配条件
        """
        self.type = rival_type
        self.real = True
        self.score_min = score_min
        self.score_max = score_max

        self.is_rob = is_rob
        self.offset = 0
        self.count = 0


    def pvp_convert_to_pve(self, rival_type, user_level):
        """PVP 退化成 PVE
        """
        if self.type != NodeInfo.ENEMY_TYPE_DUNGEON:
            self.type = rival_type

        self.score_min = data_loader.KeyNodeMatchBasicInfo_dict[user_level].enemyScoreMin
        self.score_max = data_loader.KeyNodeMatchBasicInfo_dict[user_level].enemyScoreMax
        self.real = False
        self.is_rob = False


    def set_pvp_filter_range(self, offset, count):
        self.offset = offset
        self.count = count


    def set_pvp_enemy_guard(self, guard):
        """设置 PVP 敌人的防守阵容信息
        """
        #得到 对手 id、对手防守阵容 id、对手战力、对手队伍中所有英雄
        if guard == None:
            self.rival_id = 0
            self.defense_id = 0
            self.score = 0
            self.heroes_id = ''
        else:
            self.rival_id = guard.user_id
            self.defense_id = guard.defense_id
            self.score = guard.get_team_score()
            self.heroes_id = guard.teams_hero


    def get_heroes_id(self):
        """
        """
        heroes_id = utils.split_to_int(self.heroes_id)
        return heroes_id


    def get_technology_basic_ids(self):
        """
        """
        basic_ids = utils.split_to_int(self.technology_basic_ids)
        return basic_ids


    def set_pvp_enemy_detail(self, user, heroes, money = 0, food = 0,
            items = [], technology_basic_ids = []):
        """设置 PVP 敌人的详细信息
        """
        #基础信息
        self.level = user.level
        self.name = user.name
        self.icon_id = user.icon_id
        self.country = user.country

        #阵容中英雄信息
        teams = []
        heroes_basic_id = []
        heroes_level = []
        heroes_star = []
        heroes_skill_id = []
        heroes_soldier_basic_id = []
        heroes_soldier_level = []
        heroes_equipment_id = []
        heroes_evolution_level = []
        heroes_weapon_stones_id = []
        heroes_armor_stones_id = []
        heroes_treasure_stones_id = []
        heroes_herostar_id = []
        heroes_awaken = []
        heroes_refine_level = []
        heroes_refine_value = []

        for hero in heroes:
            if hero is None:
                teams.append(0)
                continue

            teams.append(hero.basic_id)
            heroes_basic_id.append(hero.basic_id)
            heroes_level.append(hero.level)
            heroes_star.append(hero.star)
            heroes_skill_id.append(hero.skills_id)
            heroes_soldier_basic_id.append(hero.soldier_basic_id)
            heroes_soldier_level.append(hero.soldier_level)
            heroes_equipment_id.append(hero.equipments_id)
            heroes_evolution_level.append(hero.evolution_level)
            heroes_weapon_stones_id.append(hero.weapon_stones_id)
            heroes_armor_stones_id.append(hero.armor_stones_id)
            heroes_treasure_stones_id.append(hero.treasure_stones_id)
            heroes_herostar_id.append(hero.herostar_id)
            heroes_awaken.append(hero.is_awaken)
            heroes_refine_level.append(hero.refine_level)
            heroes_refine_value.extend(hero.get_refine_values())

        self.team = utils.join_to_string(teams)
        self.heroes_basic_id = utils.join_to_string(heroes_basic_id)
        self.heroes_level = utils.join_to_string(heroes_level)
        self.heroes_star = utils.join_to_string(heroes_star)
        self.heroes_skill_id = utils.join_to_string(heroes_skill_id)
        self.heroes_soldier_basic_id = utils.join_to_string(heroes_soldier_basic_id)
        self.heroes_soldier_level = utils.join_to_string(heroes_soldier_level)
        self.heroes_equipment_id = utils.join_to_string(heroes_equipment_id)
        self.heroes_evolution_level = utils.join_to_string(heroes_evolution_level)
        self.heroes_weapon_stones_id = utils.join_to_string(heroes_weapon_stones_id)
        self.heroes_armor_stones_id = utils.join_to_string(heroes_armor_stones_id)
        self.heroes_treasure_stones_id = utils.join_to_string(heroes_treasure_stones_id)
        self.heroes_herostar_id = utils.join_to_string(heroes_herostar_id)
        self.heroes_awaken = utils.join_to_string(heroes_awaken)
        self.heroes_refine_level = utils.join_to_string(heroes_refine_level)
        self.heroes_refine_value = utils.join_to_string(heroes_refine_value)

        #战斗获胜奖励
        self.reward_user_exp = int(
                float(data_loader.OtherBasicInfo_dict["BattleMonarchGetExp"].value))
        self.reward_hero_exp = data_loader.MonarchLevelBasicInfo_dict[
                self.level].heroBattleExp

        self.reward_money = money
        self.reward_food = food
        self.reward_items_basic_id = utils.join_to_string(info[0] for info in items)
        self.reward_items_num = utils.join_to_string(info[1] for info in items)

        #敌人的科技
        self.technology_basic_ids = utils.join_to_string(technology_basic_ids)


    def set_legendcity_detail(self, rival_id, buffs, position_level):
        """设置史实城信息
        """
        self.rival_id = rival_id
        self.type = 8#TODO
        self.is_legendcity_rival = True
        self.legendcity_position_level = position_level

        legendcity_buffs = [info[0] for info in buffs]
        self.legendcity_buffs = utils.join_to_string(legendcity_buffs)

        self.clear_buff()
        for city_buff_id in legendcity_buffs:
            buff_id = data_loader.LegendCityBuffBasicInfo_dict[city_buff_id].buffId
            self.set_buff(buff_id)


    def set_arena(self, user_id, team_score, heroes_id,
            arena_score, arena_ranking, arena_buff,
            win_score, lose_score):
        """设置PVP演武场敌人的信息
        """
        #得到 对手 id、对手战力、对手队伍中所有英雄
        self.rival_id = user_id
        self.type = 7#TODO
        self.score = team_score
        self.heroes_id = heroes_id
        self.arena = ARENA_TYPE_ARENA
        self.arena_score = arena_score
        self.arena_ranking = arena_ranking
        self.arena_buff = arena_buff
        self.win_score = win_score
        self.lose_score = lose_score


    def set_melee(self, user_id, team_score, heroes_id,
            arena_score, arena_ranking, arena_buff,
            win_score, lose_score, heroes_position):
        """设置PVP乱斗场敌人的信息
        """
        #得到 对手 id、对手战力、对手队伍中所有英雄
        self.rival_id = user_id
        self.type = 10#TODO
        self.score = team_score
        self.heroes_id = heroes_id
        self.arena = ARENA_TYPE_MELEE
        self.arena_score = arena_score
        self.arena_ranking = arena_ranking
        self.arena_buff = arena_buff
        self.win_score = win_score
        self.lose_score = lose_score
        self.heroes_position = heroes_position


    def set_anneal(self, level, money, food, spoils):
        """设置anneal敌人信息
        """
        #基本信息
        self.rival_id = 0
        self.level = level
        self.anneal = True

        #战斗奖励
        self.reward_money = money
        self.reward_food = food
        self.reward_user_exp = 0
        self.reward_hero_exp = data_loader.MonarchLevelBasicInfo_dict[
                self.level].heroBattleExp

        #PVE 战利品
        self.reward_items_basic_id = utils.join_to_string([info[0] for info in spoils])
        self.reward_items_num = utils.join_to_string([info[1] for info in spoils])


    def set_worldboss(self, level, spoils):
        """设置世界boss敌人信息
        """
        #基本信息
        self.rival_id = 0
        self.level = level
        self.type = NodeInfo.ENEMY_TYPE_WORLDBOSS

        #战斗奖励
        self.reward_money = 0
        self.reward_food = 0
        self.reward_user_exp = int(
                float(data_loader.OtherBasicInfo_dict["BattleMonarchGetExp"].value))
        self.reward_hero_exp = data_loader.MonarchLevelBasicInfo_dict[
                self.level].heroBattleExp

        #PVE 战利品
        self.reward_items_basic_id = utils.join_to_string([info[0] for info in spoils])
        self.reward_items_num = utils.join_to_string([info[1] for info in spoils])

        #PVE没有科技
        self.technology_basic_ids = ''


    def set_unionboss(self, boss_id):
        """设置联盟boss敌人信息"""
        self.rival_id = boss_id
        self.real = False
        self.type = NodeInfo.ENEMY_TYPE_UNIONBOSS


    def set_expand_dungeon(self, dungeon_id, level, battle_level):
        """设置扩展副本敌人信息"""
        self.rival_id = 0
        self.level = level
        self.type = NodeInfo.ENEMY_TYPE_EXPAND_DUNGEON

        #设置战斗奖励
        items_id, items_num = ExpandDungeonInfo.generate_award(dungeon_id, battle_level)
        self.reward_money = 0
        self.reward_food = 0
        self.reward_user_exp = int(
                float(data_loader.OtherBasicInfo_dict["BattleMonarchGetExp"].value))
        self.reward_hero_exp = data_loader.MonarchLevelBasicInfo_dict[
                self.level].heroBattleExp

        self.reward_items_basic_id = utils.join_to_string(items_id)
        self.reward_items_num = utils.join_to_string(items_num)


    def set_plunder(self, union_id, in_protect):
        self.union_id = union_id
        self.in_protect = in_protect
        self.type = NodeInfo.ENEMY_TYPE_PLUNDER


    def set_dungeon_matching_condition(self, rival_type, dungeon_id, score_min, score_max, dungeon_level):
        """设置匹配条件
        """
        self.type = rival_type
        self.real = True
        self.dungeon_id = dungeon_id
        self.dungeon_level = dungeon_level
        self.score_min = score_min
        self.score_max = score_max
        self.is_rob = False
        self.offset = 0
        self.count = 0


    def set_dungeon_spoils(self, spoils):
        """设置dungeon副本的奖励
        """
        #战利品
        self.reward_items_basic_id = utils.join_to_string([info[0] for info in spoils])
        self.reward_items_num = utils.join_to_string([info[1] for info in spoils])


    def get_enemy_detail(self):
        """获得敌人信息
        Returns:
            list(EnemyInfo) 敌人信息的列表
            EnemyInfo: 元组表示
            (basic_id, 
            level, 
            star,
            [skill_id1, skill_id2, skill_id3, skill_id4],
            soldier_basic_id, 
            soldier_level,
            [equipment_id1, equipment_id2, equipment_id3],
            evolution_level,
            [stone_weapon_id1, stone_weapon_id2, stone_weapon_id3, stone_weapon_id4],
            [stone_armor_id1, stone_armor_id2, stone_armor_id3, stone_armor_id4],
            [stone_treasure_id1, stone_treasure_id2, stone_treasure_id3, stone_treasure_id4],
            [herostar_id1, herostar_id2, herostar_id3, herostar_id4, herostar_id5, herostar_id6],
            is_awaken, 
            refine_level,
            [refine_value1, refine_value2, ... , refine_value9])
        """
        if self.team == '':
            return []
        
        team = []
        array = utils.split_to_int(self.team)
        while True:
            if array[-1] == 0:
                array.pop()
            else:
                break

        basic_ids = utils.split_to_int(self.heroes_basic_id)
        levels = utils.split_to_int(self.heroes_level)
        stars = utils.split_to_int(self.heroes_star)
        skills_id = utils.split_to_int(self.heroes_skill_id)
        soldiers_basic_id = utils.split_to_int(self.heroes_soldier_basic_id)
        soldiers_level = utils.split_to_int(self.heroes_soldier_level)
        equipments_id = utils.split_to_int(self.heroes_equipment_id)
        evolution_levels = utils.split_to_int(self.heroes_evolution_level)
        stone_weapons_id = utils.split_to_int(self.heroes_weapon_stones_id)
        stone_armors_id = utils.split_to_int(self.heroes_armor_stones_id)
        stone_treasures_id = utils.split_to_int(self.heroes_treasure_stones_id)
        herostars_id = utils.split_to_int(self.heroes_herostar_id)
        awakens = utils.split_to_int(self.heroes_awaken)
        refine_levels = utils.split_to_int(self.heroes_refine_level)
        refine_values = utils.split_to_int(self.heroes_refine_value)

        for basic_id in array:
            if basic_id == 0:
                team.append(None)
            else:
                index = basic_ids.index(basic_id)
                skills = []
                if len(skills_id) > 0:
                    skills.extend(skills_id[index * 4: index * 4 + 4])
                equipments = []
                if len(equipments_id) > 0:
                    equipments.extend(equipments_id[index * 3: index * 3 + 3])

                stone_weapons = []
                if len(stone_weapons_id) > 0:
                    stone_weapons.extend(stone_weapons_id[index * 4: index * 4 + 4])

                stone_armors = []
                if len(stone_armors_id) > 0:
                    stone_armors.extend(stone_armors_id[index * 4: index * 4 + 4])

                stone_treasures = []
                if len(stone_treasures_id) > 0:
                    stone_treasures.extend(stone_treasures_id[index * 4: index * 4 + 4])

                herostars = []
                if len(herostars_id) > 0:
                    herostars.extend(herostars_id[index * 6: index * 6 + 6])

                is_awaken = 0
                if len(awakens) > 0:
                    is_awaken = awakens[index]

                refine_level = 1
                if len(refine_levels) > 0:
                    refine_level = refine_levels[index]

                refine_value = []
                refine_len = len(HeroInfo.REFINE_TYPES)
                if len(refine_values) > 0:
                    refine_value.extend(
                            refine_values[index * refine_len: index * refine_len + refine_len])

                team.append((basic_id, levels[index], stars[index], skills,
                        soldiers_basic_id[index], soldiers_level[index],
                        equipments, evolution_levels[index], stone_weapons, 
                        stone_armors, stone_treasures, herostars, is_awaken,
                        refine_level, refine_value))

        return team


    def get_heroes_position(self):
        """获得敌人英雄站位信息（乱斗场专用）
        Returns:
            list(int) 敌人站位信息的列表
        """
        if self.heroes_position == '':
            PVE_DEFAULT_POSITION = [1,2,4,5,6,7,8,9,12]
            heros_position = []
            basic_ids = utils.split_to_int(self.heroes_basic_id)
            for i in range(len(basic_ids)):
                heros_position.append(PVE_DEFAULT_POSITION[i])

            return heros_position
        
        else:
            return utils.split_to_int(self.heroes_position)


    def get_reward_items(self):
        """战胜可以获得的物品奖励
        """
        items_basic_id = utils.split_to_int(self.reward_items_basic_id)
        items_num = utils.split_to_int(self.reward_items_num)
        assert len(items_basic_id) == len(items_num)
        items_count = len(items_basic_id)

        items = []
        for i in range(0, items_count):
            items.append((items_basic_id[i], items_num[i]))
        return items


    def set_union_battle_enemy_detail(self, user_id, rival_message):
        """设置联盟战争敌人的信息
        """
        self.rival_id = user_id
        
        self.team = rival_message.teams
        self.heroes_basic_id = rival_message.heroes_basic_id
        self.heroes_level = rival_message.heroes_level
        self.heroes_star = rival_message.heroes_star
        self.heroes_skill_id = rival_message.heroes_skill_id
        self.heroes_soldier_basic_id = rival_message.heroes_soldier_basic_id
        self.heroes_soldier_level = rival_message.heroes_soldier_level
        self.heroes_equipment_id = rival_message.heroes_equipment_id
        self.heroes_evolution_level = rival_message.heroes_evolution_level
        #TODO:heroes_stone
