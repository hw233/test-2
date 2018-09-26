#coding:utf8
"""
Created on 2016-07-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争地图节点
"""

import base64
from utils import logger
from utils import utils
from app.data.hero import HeroInfo
from datalib.data_loader import data_loader


class UnionBattleMapNodeInfo(object):
    """一场联盟战争地图节点信息
    """
    NODE_STATUS_EMPTY = 1       #未部署
    NODE_STATUS_DEPLOYED = 2    #已部署
    NODE_STATUS_ENGAGED = 3     #交战中
    NODE_STATUS_BEATEN = 4      #被攻占

    CITY_LEVEL_MEMBER = 0   #普通成员城池等级
    CITY_LEVEL_VICE = 1     #副盟主城池等级
    CITY_LEVEL_LEADER = 2   #盟主城池等级

    __slots__ = [
            "id",
            "union_id",
            "index",
            "level",
            "status",

            "battle_start_time",    #进攻该节点的开始时间
            "attacker_user_id",     #进攻该节点的用户id
            "attacker_user_name",
            "attacker_user_icon",
            "attacker_soldier_num", #攻击方进攻时投入的总兵力
            "attacker_num",         #正在进攻该节点的玩家数量

            "defender_user_id",
            "defender_user_name",
            "defender_user_icon",
            "defender_user_level",
            "defender_is_robot",

            "defender_team",
            "heroes_basic_id",
            "heroes_level",
            "heroes_star",
            "heroes_skill_id",
            "heroes_soldier_basic_id",
            "heroes_soldier_level",
            "heroes_equipment_id",
            "heroes_evolution_level",
            "heroes_stone_id",
            "heroes_herostar_id",
            "heroes_awaken",
            "heroes_refine_level",
            "heroes_refine_value",
            "techs_basic_id",

            "city_level",
            "current_soldier_num",
            "total_soldier_num",

            "accepted_members",
            "accepted_names",
            "accepted_icons",
            "reward_items",
            "reward_nums",
            "accept_times"
            ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.index = 0

        self.level = 1
        self.status = UnionBattleMapNodeInfo.NODE_STATUS_EMPTY

        self.battle_start_time = ""
        self.attacker_user_id = ""
        self.attacker_user_name = ""    #废弃
        self.attacker_user_icon = 0     #废弃
        self.attacker_soldier_num = 0   #废弃
        self.attacker_num = 0

        self.defender_user_id = 0
        self.defender_user_name = ""
        self.defender_user_icon = 0
        self.defender_user_level = 0
        self.defender_is_robot = False

        self.defender_team = ""
        self.heroes_basic_id = ""
        self.heroes_level = ""
        self.heroes_star = ""
        self.heroes_skill_id = ""
        self.heroes_soldier_basic_id = ""
        self.heroes_soldier_level = ""
        self.heroes_equipment_id = ""
        self.heroes_evolution_level = ""
        self.heroes_stone_id = ""
        self.heroes_herostar_id = ""
        self.heroes_awaken = ""
        self.heroes_refine_level = ""
        self.heroes_refine_value = ""
        self.techs_basic_id = ""
        
        self.city_level = 0
        self.current_soldier_num = 0
        self.total_soldier_num = 0

    @staticmethod
    def generate_id(union_id, index):
        id = union_id << 32 | index
        return id


    @staticmethod
    def create(union_id, index):
        node = UnionBattleMapNodeInfo()
        node.id = UnionBattleMapNodeInfo.generate_id(union_id, index)
        node.union_id = union_id
        node.index = index

        node.level = 1
        node.status = UnionBattleMapNodeInfo.NODE_STATUS_EMPTY

        node.battle_start_time = ""
        node.attacker_user_id = ""
        node.attacker_user_name = ""
        node.attacker_user_icon = 0
        node.attacker_soldier_num = 0
        node.attacker_num = 0 

        node.defender_user_id = 0
        node.defender_user_name = ""
        node.defender_user_icon = 0
        node.defender_user_level = 0
        node.defender_is_robot = False

        node.defender_team = ""
        node.heroes_basic_id = ""
        node.heroes_level = ""
        node.heroes_star = ""
        node.heroes_skill_id = ""
        node.heroes_soldier_basic_id = ""
        node.heroes_soldier_level = ""
        node.heroes_equipment_id = ""
        node.heroes_evolution_level = ""
        node.heroes_stone_id = ""
        node.heroes_herostar_id = ""
        node.heroes_awaken = ""
        node.heroes_refine_level = ""
        node.heroes_refine_value = ""
        node.techs_basic_id = ""
        
        node.city_level = 0
        node.current_soldier_num = 0
        node.total_soldier_num = 0

        node.accepted_members = ""  #奖励箱领取
        node.accepted_names = ""
        node.accepted_icons = ""
        node.reward_items = ""
        node.reward_nums = ""
        node.accept_times = ""

        return node


    def reset(self):
        """重置
        """
        self.level = 1
        self.status = self.NODE_STATUS_EMPTY

        self.battle_start_time = ""
        self.attacker_user_id = ""
        self.attacker_user_name = ""
        self.attacker_user_icon = 0
        self.attacker_soldier_num = 0
        self.attacker_num = 0 

        self.defender_user_id = 0
        self.defender_user_name = ""
        self.defender_user_icon = 0
        self.defender_user_level = 0
        self.defender_is_robot = False

        self.defender_team = ""
        self.heroes_basic_id = ""
        self.heroes_level = ""
        self.heroes_star = ""
        self.heroes_skill_id = ""
        self.heroes_soldier_basic_id = ""
        self.heroes_soldier_level = ""
        self.heroes_equipment_id = ""
        self.heroes_evolution_level = ""
        self.heroes_stone_id = ""
        self.heroes_herostar_id = ""
        self.heroes_awaken = ""
        self.heroes_refine_level = ""
        self.heroes_refine_value = ""
        self.techs_basic_id = ""

        self.city_level = 0
        self.current_soldier_num = 0
        self.total_soldier_num = 0

        self.accepted_members = ""
        self.accepted_names = ""
        self.accepted_icons = ""
        self.reward_items = ""
        self.reward_nums = ""
        self.accept_times = ""


    def get_readable_defender_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.defender_user_name)


    def is_able_to_deploy(self):
        """是否能够进行防御部署
        """
        return self.status == self.NODE_STATUS_EMPTY


    def is_deployed(self, user_id = 0):
        """是否已经完成部署
        """
        if self.status != self.NODE_STATUS_DEPLOYED:
            return False

        if user_id == 0:
            return True
        else:
            return user_id == self.defender_user_id


    def deploy(self, user_id, user_name, user_icon, user_level, team, heroes, techs, city_level):
        """部署节点防御
        """
        assert self.status == self.NODE_STATUS_EMPTY
        self.status = self.NODE_STATUS_DEPLOYED

        self.defender_user_id = user_id
        self.defender_user_name = base64.b64encode(user_name)
        self.defender_user_icon = user_icon
        self.defender_user_level = user_level
        self.defender_is_robot = False

        skills = []
        equipments = []
        stones = []
        herostar_id = []
        awaken = []
        refine_level = []
        refine_value = []

        for hero in heroes:
            skills.append(hero.first_skill_id)
            skills.append(hero.second_skill_id)
            skills.append(hero.third_skill_id)
            skills.append(hero.fourth_skill_id)
            equipments.append(hero.equipment_weapon_id)
            equipments.append(hero.equipment_armor_id)
            equipments.append(hero.equipment_treasure_id)
            stones.extend(hero.stone_weapon)
            stones.extend(hero.stone_armor)
            stones.extend(hero.stone_treasure)
            herostar_id.extend(hero.hero_star)
            awaken.append(hero.hero_awakening)
            refine_level.append(hero.hero_refine_info.refineLv)

            value = [0] * len(HeroInfo.REFINE_TYPES)
            for attribute in hero.hero_refine_attributes:
                value[attribute.type] = attribute.value
            refine_value.extend(value)

        self.defender_team = utils.join_to_string(team)
        self.heroes_basic_id = utils.join_to_string(
                [hero.basic_id for hero in heroes])
        self.heroes_level = utils.join_to_string(
                [hero.level for hero in heroes])
        self.heroes_star = utils.join_to_string(
                [hero.star_level for hero in heroes])
        self.heroes_skill_id = utils.join_to_string(skills)
        self.heroes_soldier_basic_id = utils.join_to_string(
                [hero.soldier_basic_id for hero in heroes])
        self.heroes_soldier_level = utils.join_to_string(
                [hero.soldier_level for hero in heroes])
        self.heroes_equipment_id = utils.join_to_string(equipments)
        self.heroes_evolution_level = utils.join_to_string(
                [hero.evolution_level for hero in heroes])
        self.heroes_stone_id = utils.join_to_string(stones)
        self.heroes_herostar_id = utils.join_to_string(herostar_id)
        self.heroes_awaken = utils.join_to_string(awaken)
        self.heroes_refine_level = utils.join_to_string(refine_level)
        self.heroes_refine_value = utils.join_to_string(refine_value)

        self.techs_basic_id = utils.join_to_string(techs)
        self.city_level = city_level

        #计算总兵量
        need_soldier_num = 0
        for hero in heroes:
            need_soldier_num += self._calc_soldier_consume(
                    hero.soldier_basic_id, hero.soldier_level)

        if city_level == 2:
            ratio = int(float(data_loader.UnionConfInfo_dict["union_battle_city3"].value))
        elif city_level == 1:
            ratio = int(float(data_loader.UnionConfInfo_dict["union_battle_city2"].value))
        else:
            ratio = int(float(data_loader.UnionConfInfo_dict["union_battle_city1"].value))
        need_soldier_num = need_soldier_num * ratio
        self.current_soldier_num = need_soldier_num
        self.total_soldier_num = need_soldier_num
            

    def deploy_auto(self, enemy, name, icon):
        """自动部署节点防御，使用 PVE 阵容
        """
        assert self.status == self.NODE_STATUS_EMPTY
        self.status = self.NODE_STATUS_DEPLOYED

        self.defender_user_id = enemy.id
        self.defender_user_name = base64.b64encode(name)
        self.defender_user_icon = icon
        self.defender_user_level = enemy.level
        self.defender_is_robot = True

        self.defender_team = utils.join_to_string(enemy.teamInfo)
        self.heroes_basic_id = utils.join_to_string(enemy.heroBasicId)
        self.heroes_level = utils.join_to_string(enemy.heroLevel)
        self.heroes_star = utils.join_to_string(enemy.heroStarLevel)
        self.heroes_skill_id = utils.join_to_string(enemy.heroSkillLevel)
        self.heroes_soldier_basic_id = utils.join_to_string(enemy.soldierBasicId)
        self.heroes_soldier_level = utils.join_to_string(enemy.soldierLevel)
        self.heroes_equipment_id = utils.join_to_string(enemy.heroEquipmentId)
        self.heroes_evolution_level = utils.join_to_string(enemy.heroEvolutionLevel)
        self.heroes_stone_id = ""
        self.heroes_herostar_id = ""
        self.heroes_awaken = ""
        self.heroes_refine_level = ""
        self.heroes_refine_value = ""
        self.techs_basic_id = ""
        self.city_level = 0
        #计算总兵力
        need_soldier_num = 0
        for index in range(len(enemy.soldierBasicId)):
            need_soldier_num += self._calc_soldier_consume(
                    enemy.soldierLevel[index], enemy.soldierLevel[index])

        #ratio = int(float(data_loader.UnionConfInfo_dict["union_battle_city1"].value))
        ratio = 2   #pve的血量降低
        need_soldier_num = need_soldier_num * ratio
        self.current_soldier_num = need_soldier_num
        self.total_soldier_num = need_soldier_num


    def _calc_soldier_consume(self, soldier_basic_id, soldier_level):
        """计算一个英雄方阵（固定人数）的士兵数消耗
        """
        need_soldier_num = 0
        count_per_array = int(float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value))
        key = "%s_%s" % (soldier_basic_id, soldier_level)
        need_soldier_num += int(data_loader.SoldierBasicInfo_dict[key].soldierCost * count_per_array)
        return need_soldier_num


    def get_defender_team_detail(self):
        """获取防守阵容
        """
        teams = utils.split_to_int(self.defender_team)

        heroes = {}
        heroes_basic_id = utils.split_to_int(self.heroes_basic_id)
        heroes_level = utils.split_to_int(self.heroes_level)
        heroes_star = utils.split_to_int(self.heroes_star)
        heroes_skill_id = utils.split_to_int(self.heroes_skill_id)
        heroes_soldier_basic_id = utils.split_to_int(self.heroes_soldier_basic_id)
        heroes_soldier_level = utils.split_to_int(self.heroes_soldier_level)
        heroes_equipment_id = utils.split_to_int(self.heroes_equipment_id)
        heroes_evolution_level = utils.split_to_int(self.heroes_evolution_level)
        heroes_stone = utils.split_to_int(self.heroes_stone_id)
        heroes_herostar = utils.split_to_int(self.heroes_herostar_id)
        heroes_awaken = utils.split_to_int(self.heroes_awaken)
        heroes_refine_level = utils.split_to_int(self.heroes_refine_level)
        heroes_refine_value = utils.split_to_int(self.heroes_refine_value)

        for index, basic_id in enumerate(heroes_basic_id):
            if basic_id == 0:
                continue

            skills = []
            if len(heroes_skill_id) > 0:
                skills = heroes_skill_id[index * 4 : index * 4 + 4]
            equipments = []
            if len(heroes_equipment_id) > 0:
                equipments = heroes_equipment_id[index * 3 : index * 3 + 3]
            stones = []
            if len(heroes_stone) > 0:
                stones = heroes_stone[index * 12 : index * index * 12 + 12]

            herostars = []
            if len(heroes_herostar) > 0:
                herostars = heroes_herostar[index * 6: index * 6 + 6]

            is_awaken = 0
            if len(heroes_awaken) > 0:
                is_awaken = heroes_awaken[index]

            refine_level = 1
            if len(heroes_refine_level) > 0:
                refine_level = heroes_refine_level[index]

            refine_value = []
            refine_len = len(HeroInfo.REFINE_TYPES)
            if len(heroes_refine_value) > 0:
                refine_value = \
                    heroes_refine_value[index * refine_len: index * refine_len + refine_len]

            info = (basic_id, heroes_level[index], heroes_star[index],
                    skills, heroes_soldier_basic_id[index], heroes_soldier_level[index],
                    equipments, heroes_evolution_level[index], stones, herostars, is_awaken,
                    refine_level, refine_value)
            heroes[basic_id] = info

        return (teams, heroes)


    def get_defender_techs(self):
        """获取防守阵容科技
        """
        return utils.split_to_int(self.techs_basic_id)


    def is_able_to_cancel_deploy(self, user_id):
        """是否可以取消部署，需要防守者 user id 匹配
        """
        return self.status == self.NODE_STATUS_DEPLOYED and self.defender_user_id == user_id


    def cancel_deploy(self):
        """清除防御部署
        """
        assert self.status == self.NODE_STATUS_DEPLOYED
        self.status = self.NODE_STATUS_EMPTY

        self.defender_user_id = 0
        self.defender_user_name = ""
        self.defender_user_icon = 0
        self.defender_user_level = 0

        self.defender_team = ""
        self.heroes_basic_id = ""
        self.heroes_level = ""
        self.heroes_star = ""
        self.heroes_skill_id = ""
        self.heroes_soldier_basic_id = ""
        self.heroes_soldier_level = ""
        self.heroes_equipment_id = ""
        self.heroes_evolution_level = ""
        self.heroes_stone_id = ""
        self.techs_basic_id = ""


    def is_able_to_start_battle(self):
        """是否可以开始战斗
        """
        #return self.status == self.NODE_STATUS_DEPLOYED
        return self.status != self.NODE_STATUS_BEATEN


    def is_able_to_finish_battle(self, attacker_user_id, now):
        """是否可以结束战斗
        1 处于交战状态
        2 战斗未超时
        3 进攻玩家的正确
        """
        return (not self.is_battle_timeout(attacker_user_id, now) and
                attacker_user_id in utils.split_to_int(self.attacker_user_id))


    def get_battle_timeout_num(self, now):
        """是否有战斗超时
        """
        if self.status != self.NODE_STATUS_ENGAGED:
            return 0

        users_id = utils.split_to_int(self.attacker_user_id)
        num = 0
        for user_id in users_id:
            if self.is_battle_timeout(user_id, now):
                num += 1

        return num


    def is_battle_timeout(self, attacker_user_id, now):
        """战斗是否超时
        """
        if self.status != self.NODE_STATUS_ENGAGED:
            return False

        users_id = utils.split_to_int(self.attacker_user_id)
        start_times = utils.split_to_int(self.battle_start_time)
        index = users_id.index(attacker_user_id)

        if self.get_battle_left_time(start_times[index], now) <= 0:
            return True
        else:
            return False


    def get_battle_left_time(self, start_time, now):
        """获取战斗剩余时间
        """
        if self.status == self.NODE_STATUS_ENGAGED:
            #战斗中
            duration = int(float(data_loader.UnionConfInfo_dict["battle_max_time"].value))
            battle_end_time = start_time + duration
            if now >= battle_end_time:
                return 0
            else:
                return battle_end_time - now 
        else:
            return 0


    def start_battle(self, attacker_user_id, now):
        """开始战斗
        """
        #assert self.status == self.NODE_STATUS_DEPLOYED
        self.status = self.NODE_STATUS_ENGAGED
        self.attacker_num += 1

        start_times = utils.split_to_int(self.battle_start_time)
        start_times.append(now)
        users_id = utils.split_to_int(self.attacker_user_id)
        users_id.append(attacker_user_id)

        self.battle_start_time = utils.join_to_string(start_times)
        self.attacker_user_id = utils.join_to_string(users_id)


    def finish_battle(self, attacker_user_id, kills_num):
        """结束战斗
        """
        #assert self.status == self.NODE_STATUS_ENGAGED
        if self.status != self.NODE_STATUS_ENGAGED:
            return
        else:
            self.current_soldier_num = max(0, self.current_soldier_num - kills_num)

        self.attacker_num = max(0, self.attacker_num - 1)

        #删除记录的user_id和他的开始战斗时间
        users_id = utils.split_to_int(self.attacker_user_id)
        start_times = utils.split_to_int(self.battle_start_time)
        del_index = users_id.index(attacker_user_id)
        del(users_id[del_index])
        del(start_times[del_index])
        self.attacker_user_id = utils.join_to_string(users_id)
        self.battle_start_time = utils.join_to_string(start_times)

        if self.current_soldier_num == 0:
            self.status = self.NODE_STATUS_BEATEN
            self.attacker_num = 0
            return

        if self.attacker_num == 0:
            self.status = self.NODE_STATUS_DEPLOYED


    def finish_battles_timeout(self, now):
        """结束在该节点上发起的超时的战斗
        """
        start_times = utils.split_to_int(self.battle_start_time)
        users_id = utils.split_to_int(self.attacker_user_id)

        delete_users_id = []
        for user_id in users_id:
            if self.is_battle_timeout(user_id, now):
                delete_users_id.append(user_id)

        #删除
        for delete_id in delete_users_id:
            del_index = users_id.index(delete_id)
            del(users_id[del_index])
            del(start_times[del_index])

            self.attacker_num = max(0, self.attacker_num - 1)
            if self.attacker_num == 0:
                self.status = self.NODE_STATUS_DEPLOYED

        self.attacker_user_id = utils.join_to_string(users_id)
        self.battle_start_time = utils.join_to_string(start_times)


    def is_able_to_forward(self):
        """是否可以进入下一等级
        """
        if not self.is_beaten():
            return False

        max_level = int(float(data_loader.UnionConfInfo_dict["battle_map_total_level"].value))
        return self.level < max_level


    def forward(self):
        """进入下一等级
        """
        assert self.is_able_to_forward()
        self.level += 1
        self.status = self.NODE_STATUS_DEPLOYED


    def get_defence_buff_count(self):
        return self.level - 1


    def is_beaten(self):
        return self.status == self.NODE_STATUS_BEATEN


    def get_accepted_members(self):
        """获取领取过奖励的成员"""
        return utils.split_to_int(self.accepted_members)

    def get_reward_record(self):
        """获取奖励领取记录"""
        members = utils.split_to_int(self.accepted_members)
        names = utils.split_to_string(self.accepted_names)
        icons = utils.split_to_int(self.accepted_icons) 
        items_id = utils.split_to_int(self.reward_items)
        items_num = utils.split_to_int(self.reward_nums)
        times = utils.split_to_int(self.accept_times)

        names = [base64.b64decode(name) for name in names]
        return map(None, members, names, icons, items_id, items_num, times)

    def add_reward_record(self, user_id, user_name, icon_id, item_id, item_num, now):
        """添加领奖记录"""
        members = utils.split_to_int(self.accepted_members)
        names = utils.split_to_string(self.accepted_names)
        icons = utils.split_to_int(self.accepted_icons) 
        items_id = utils.split_to_int(self.reward_items)
        items_num = utils.split_to_int(self.reward_nums)
        times = utils.split_to_int(self.accept_times)

        members.append(user_id)
        names.append(user_name)
        icons.append(icon_id)
        items_id.append(item_id)
        items_num.append(item_num)
        times.append(now)

        self.accepted_members = utils.join_to_string(members)
        self.accepted_names = utils.join_to_string(names)
        self.accepted_icons = utils.join_to_string(icons)
        self.reward_items = utils.join_to_string(items_id)
        self.reward_nums = utils.join_to_string(items_num)
        self.accept_times = utils.join_to_string(times)


