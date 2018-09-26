#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Hero 数值相关计算
        《武将数值折算设计》MRD
"""

import copy
import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.herostar import HeroStarInfo
from scipy.stats import binom
import random
import pdb


class HeroInfo(object):
    """英雄信息
    """
    PLACE_TYPE_INVALID = 0
    PLACE_TYPE_BUILDING = 1
    PLACE_TYPE_NODE = 2

    EQUIPMENT_COUNT = 3
    EQUIPMENT_INVALID_ID = -1
    EQUIPMENT_TYPE_WEAPON = 1
    EQUIPMENT_TYPE_ARMOR = 2
    EQUIPMENT_TYPE_TREASURE = 3

    EQUIPMENT_STONE_NUM = 4    #一件装备可镶嵌宝石数

    SOLDIER_TYPE_FOOTMAN = 1
    SOLDIER_TYPE_CAVALRY = 2
    SOLDIER_TYPE_ARCHER = 3

    HERO_TYPE_STRENGTH = 1
    HERO_TYPE_AGILE = 2
    HERO_TYPE_INTELLIGENCE = 3
    HERO_TYPE_POLITICS = 4

    BROADCAST_EVOLUTION_LEVELS = [7, 11]
    
    BROADCAST_STAR_LEVELS = [20, 30, 40, 50, 60]
    
    #(生命, 功速, 攻强, 护甲, 爆击, 闪避, 招架, 计谋, 阵法, 内务, 研究)
    REFINE_TYPES = ("LIFE", "ATTACKSPEED", "POWER", "ARMOR", "CRITRATING", "DODGERATING", 
            "PARRYRATING", "STRATAGEM", "TACTICS", "INTERNALAFFAIRS", "RESEARCH")


    def __init__(self, id = 0, user_id = 0,
            basic_id = 0, level = 0, exp = 0, evolution_level = 1, star = 0,
            soldier_id = 0, soldier_basic_id = 0, soldier_level = 0,
            skills_id = '', equipments_id = '',
            weapon_stones_id = '0#0#0#0', armor_stones_id = '0#0#0#0', treasure_stones_id = '0#0#0#0',
            buffs_id = '', place_type = PLACE_TYPE_INVALID, place_id = 0, update_time = 0,
            battle_node_basic_id = 0, anneal_sweep_floor = 0,
            battle_score = 0, research_score = 0,
            interior_score = 0, defense_score = 0,
            herostar_id = '0#0#0#0#0#0', is_awaken = 0,
            refine_level = 1, refine_value = "", refine_count = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id

        #等级
        self.level = level
        self.exp = exp

        #进化等级
        self.evolution_level = evolution_level

        #星级
        self.star = star

        #配置兵种
        self.soldier_basic_id = soldier_basic_id
        self.soldier_level = soldier_level

        #技能
        self.skills_id = skills_id

        #装备
        self.equipments_id = equipments_id
        self.weapon_stones_id = weapon_stones_id
        self.armor_stones_id = armor_stones_id
        self.treasure_stones_id = treasure_stones_id

        #羁绊带来的buff
        self.buffs_id = buffs_id

        #工作
        self.place_type = place_type
        self.place_id = place_id
        self.update_time = update_time

        #战斗
        self.battle_node_basic_id = battle_node_basic_id

        #试炼扫荡
        self.anneal_sweep_floor = anneal_sweep_floor

        #相关属性评分
        self.battle_score = battle_score
        self.research_score = research_score
        self.interior_score = interior_score
        self.defense_score = defense_score

        #将星盘
        self.herostar_id = herostar_id

        #觉醒
        self.is_awaken = is_awaken

        #洗髓
        self.refine_level = refine_level
        #生命#功速#攻强#护甲#爆击#闪避#招架#计谋#阵法#内务#研究
        self.refine_value = refine_value
        self.refine_count = refine_count


    @staticmethod
    def generate_id(user_id, basic_id):
        id = user_id << 32 | basic_id
        return id


    @staticmethod
    def get_basic_id(id):
        basic_id = id & 0xFFFFFFFF
        return basic_id


    @staticmethod
    def create(user_id, basic_id, soldier, technology_basic_ids):
        """生成新英雄
        Args:
            user_id[int]: 用户 id
            basic_id[int]: 英雄的 basic id
            soldier[SoldierInfo]: 英雄所带配置的信息
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            HeroInfo 英雄信息
        """
        id = HeroInfo.generate_id(user_id, basic_id)

        #计算技能等级
        def calc_skill(skill_id, level):
            if skill_id == 0:
                return 0

            i = 1
            while i < level:
                skill_id = data_loader.SkillBasicInfo_dict[skill_id].nextId
                assert data_loader.SkillBasicInfo_dict[skill_id].level == i+1
                i = i+1
            return skill_id

        #英雄一共4个技能
        skills = []
        skills.append(data_loader.HeroBasicInfo_dict[basic_id].firstSkillId)
        skills.append(data_loader.HeroBasicInfo_dict[basic_id].secondSkillId)
        skills.append(data_loader.HeroBasicInfo_dict[basic_id].thirdSkillId)
        skills.append(data_loader.HeroBasicInfo_dict[basic_id].fourthSkillId)

        for index in range(0, len(skills)):
            skills[index] = calc_skill(
                    skills[index], HeroInfo._get_skill_unlock_level(index))

        skills_id = utils.join_to_string(skills)

        #初始装备
        default_equipments_id = data_loader.HeroBasicInfo_dict[basic_id].equipmentIds
        assert len(default_equipments_id) == HeroInfo.EQUIPMENT_COUNT
        equipments_id = utils.join_to_string(default_equipments_id)

        #初始星级
        star_level = HeroInfo.get_initial_star_level(basic_id)

        hero = HeroInfo(id, user_id, basic_id = basic_id,
                level = 1, exp = 0, star = star_level,
                soldier_id = soldier.id,
                soldier_basic_id = soldier.basic_id,
                soldier_level = 1,
                skills_id = skills_id,
                equipments_id = equipments_id)

        assert hero.update_soldier(soldier, technology_basic_ids)
        return hero


    @staticmethod
    def create_special(user_id, user_level, basic_id, level, star,
            soldier, skills_id, technology_basic_ids, equipments_id = [], 
            buffs_id = [], level_limit = True, evolution_level = 1, 
            soldier_level_limit = True, herostars_id = [], is_awaken = 0,
            refine_level = 1, refine_value = [], stones_weapon_id = [],
            stones_armor_id = [], stones_treasure_id = []):
        """特别的创建英雄接口
        可以指定英雄的等级、星级、兵种、技能等级、装备、buff
        """
        hero = HeroInfo.create(user_id, basic_id, soldier, technology_basic_ids)

        max_level = data_loader.MonarchLevelBasicInfo_dict[user_level].heroLevelLimit
        if level > max_level and level_limit:
            logger.warning('Hero level error[level=%d][max=%d][user level=%d]' %
                    (level, max_level, user_level))
            return None

        hero.level = level
        star_level = HeroInfo.get_initial_star_level(basic_id)
        if star_level == 10 and star < 10: #为了兼容有些配的旧的英雄星级数据导致的错误
            hero.star = star * star_level
        hero.evolution_level = evolution_level
        if not soldier_level_limit:
            hero.soldier_level = soldier.level

        hero.update_soldier(soldier, technology_basic_ids)

        for (index, skill_id) in enumerate(skills_id):
            if skill_id == 0:
                continue
            if not hero.upgrade_skill_special(index, skill_id, technology_basic_ids):
                logger.warning("Upgrade skill failed[target skill id=%d]" % skill_id)
                return None

        if len(equipments_id) != 0:
            assert len(equipments_id) == 3
            hero.equipments_id = utils.join_to_string(equipments_id)

        if len(buffs_id) != 0:
            hero.buffs_id = utils.join_to_string(buffs_id)

        if len(herostars_id) != 0:
            hero.herostar_id = utils.join_to_string(herostars_id)

        hero.is_awaken = is_awaken

        hero.refine_level = refine_level
        if len(refine_value) == len(HeroInfo.REFINE_TYPES):
            hero.refine_value = utils.join_to_string(refine_value)

        if len(stones_weapon_id) == 4:
            hero.weapon_stones_id = utils.join_to_string(stones_weapon_id)
        if len(stones_armor_id) == 4:
            hero.armor_stones_id = utils.join_to_string(stones_armor_id)
        if len(stones_treasure_id) == 4:
            hero.treasure_stones_id = utils.join_to_string(stones_treasure_id)

        hero._update_scores(technology_basic_ids)
        return hero


    @staticmethod
    def create_by_starsoul(user_id, basic_id, num, soldier, technology_basic_ids):
        """用将魂合成英雄
        1 将魂的数量必须正好满足要求
        2 生成一个对应星级的英雄
        Args:
            user_id[int]: 用户的 id
            basic_id[int]: 英雄的 basic id
            num[int]: 将魂数量
            soldier[SoldierInfo]: 英雄所配置兵种的信息
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            合成成功返回 hero[HeroInfo]信息
            失败返回 None
        """
        star_level = HeroInfo.get_initial_star_level(basic_id)
        num_starsoul = 0
        while star_level >= HeroInfo.get_min_star_level():
            num_starsoul += data_loader.HeroStarLevelBasicInfo_dict[star_level].perceptivity
            star_level -= 1

        if num_starsoul != num:
            logger.warning("Not enough starsoul[need=%d][consume=%d]" % (num_starsoul, num))
            return None

        return HeroInfo.create(user_id, basic_id, soldier, technology_basic_ids)

    @staticmethod
    def get_initial_star_level(basic_id):
        """获取英雄的初始星级"""
        return data_loader.HeroBasicInfo_dict[basic_id].initialStarLevel

    def reborn(self, technology_basic_ids):
        """重生"""
        self.level = 1
        self.exp = 0
        self.evolution_level = 1
        self.star = HeroInfo.get_initial_star_level(self.basic_id)
        self.soldier_basic_id = HeroInfo.get_default_soldier_basic_id(self.basic_id)

        def calc_skill(skill_id, level):
            if skill_id == 0:
                return 0

            i = 1
            while i < level:
                skill_id = data_loader.SkillBasicInfo_dict[skill_id].nextId
                assert data_loader.SkillBasicInfo_dict[skill_id].level == i+1
                i = i+1
            return skill_id

        skills = []
        skills.append(data_loader.HeroBasicInfo_dict[self.basic_id].firstSkillId)
        skills.append(data_loader.HeroBasicInfo_dict[self.basic_id].secondSkillId)
        skills.append(data_loader.HeroBasicInfo_dict[self.basic_id].thirdSkillId)
        skills.append(data_loader.HeroBasicInfo_dict[self.basic_id].fourthSkillId)

        for index in range(0, len(skills)):
            skills[index] = calc_skill(
                    skills[index], HeroInfo._get_skill_unlock_level(index))

        self.skills_id = utils.join_to_string(skills)

        #初始装备
        default_equipments_id = data_loader.HeroBasicInfo_dict[self.basic_id].equipmentIds
        self.equipments_id = utils.join_to_string(default_equipments_id)
        self.weapon_stones_id = "0#0#0#0"
        self.armor_stones_id = "0#0#0#0"
        self.treasure_stones_id = "0#0#0#0"

        self.herostar_id = "0#0#0#0#0#0"

        self._update_scores(technology_basic_ids)

    def get_soldier_type(self):
        """获得英雄所带兵系（步、骑、弓）
        """
        key = "%s_%s" % (self.soldier_basic_id, self.soldier_level)
        soldier_type = int(data_loader.SoldierBasicInfo_dict[key].type)
        return soldier_type


    def level_up(self, exp, user_level, technology_basic_ids):
        """计算英雄获得经验值之后的等级状态
        1 英雄等级不会超过上限
        2 英雄等级达到上限后，exp 最大为0
        3 会更新英雄的数值：战斗力、内务、研究、防守评价值
        Args:
            exp[int]: 英雄增加的经验值
            user_level[int]: 此时玩家等级
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            -1: 失败
            0 : 成功，英雄未升级
            >0: 成功，英雄升级，返回升了多少级
        """
        if exp < 0:
            logger.warning("Invalid exp value[exp=%d]" % exp)
            exp = 0
            #return -1

        max_level = data_loader.MonarchLevelBasicInfo_dict[user_level].heroLevelLimit
        if self.level > max_level:
            logger.warning('Hero level reach max[level=%d][max=%d][user level=%d]' %
                    (self.level, max_level, user_level))
            return -1

        exp = int(self.exp + exp)
        level = self.level

        exp_levelup = data_loader.HeroLevelBasicInfo_dict[level+1].exp
        while exp >= exp_levelup:
            if level + 1 > max_level:
                exp = exp_levelup
                logger.debug("Hero can not continue upgrade level due to limit"
                        "[limit=%d][level=%d][exp=%d]" %
                        (max_level, level, exp))
                break

            exp -= exp_levelup
            level += 1
            exp_levelup = data_loader.HeroLevelBasicInfo_dict[level+1].exp

        diff = level - self.level

        self.exp = exp
        self.level = level

        if diff > 0:
            self._update_scores(technology_basic_ids)
        return diff


    def star_level_up(self, num, technology_basic_ids):
        """计算英雄获得灵魂石后的状态：升星英雄
        1 灵魂石的数量正好满足要求时，英雄星级上升一级；否则，英雄不发生变化
        2 英雄星级不能超过上限
        3 会更新英雄的数值：战斗力、内务、研究、防守评价值
        Args:
        Args:
            hero[HeroInfo out]: 英雄的信息
            num[int]: 将魂数量
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            是否升星成功
        """
        star_level = self.star + 1

        max_star_level = data_loader.HeroBasicInfo_dict[self.basic_id].maxStarLevel
        if star_level > max_star_level:
            logger.warning("Invalid star level[level=%d]" % star_level)
            return False

        star_need = data_loader.HeroStarLevelBasicInfo_dict[star_level].perceptivity
        if star_need != num:
            logger.warning("Unexpect starsoul num[num=%d][need=%d]" % (num, star_need))
            return False

        self.star = star_level

        self._update_scores(technology_basic_ids)
        return True


    def evolution_level_up(self, item_id, item_num, technology_basic_ids):
        """计算英雄使用突破石后的状态：进化英雄
        1 突破石的类型、数量正好满足要求时，英雄进化升一级；否则，英雄不发生变化
        2 英雄进化等级不能超过上限
        3 会更新英雄的数值：战斗力、内务、研究、防守评价值
        Args:
        Args:
            hero[HeroInfo out]: 英雄的信息
            num[int]: 将魂数量
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            是否升星成功
        """
        evolution_ids = data_loader.HeroBasicInfo_dict[self.basic_id].evolutionIds
        max_evolution_level = len(evolution_ids) + 1

        next_evolution_level = self.evolution_level + 1
        next_evolution_id = evolution_ids[next_evolution_level - 2]

        if next_evolution_level > max_evolution_level:
            logger.warning("Invalid evolution level[level=%d]" % next_evolution_level)
            return False

        evolution_basic = data_loader.HeroEvolutionLevelBasicInfo_dict[next_evolution_id]

        #检查进化的物品是否正确
        evolution_item_num = int(evolution_basic.evolvePoints)
        soldier_type = self.get_soldier_type()
        if soldier_type == self.SOLDIER_TYPE_FOOTMAN:
            evolution_item_id = int(evolution_basic.evolutionItemBasicIds[0])
        elif soldier_type == self.SOLDIER_TYPE_CAVALRY:
            evolution_item_id = int(evolution_basic.evolutionItemBasicIds[1])
        elif soldier_type == self.SOLDIER_TYPE_ARCHER:
            evolution_item_id = int(evolution_basic.evolutionItemBasicIds[2])
        else:
            return False

        if evolution_item_id != item_id:# or evolution_item_num != item_num:
            logger.warning("Unexpect evolution item[id=%d][num=%d][need_id=%d][need_num=%d]"
                    % (item_id, item_num, evolution_item_id, evolution_item_num))
            return False

        #检查英雄等级是否符合
        limit_hero_level = int(evolution_basic.limitHeroLevel)
        if self.level < limit_hero_level:
            logger.warning("Unexpect hero level[level=%d][need_level=%d]"
                    % (self.level, limit_hero_level))
            return False

        self.evolution_level = next_evolution_level

        self._update_scores(technology_basic_ids)
        return True


    def _get_evolution_buff_id(self):
        """获得当前进化等级对应的buff id
        """
        if self.evolution_level < 2:
            return []

        evolution_ids = data_loader.HeroBasicInfo_dict[self.basic_id].evolutionIds
        buff_ids = []
        for i in range(2, self.evolution_level + 1):
            evolution_id = evolution_ids[i - 2]
            buff_ids.append(data_loader.HeroEvolutionLevelBasicInfo_dict[evolution_id].buffId)

        return buff_ids


    def _get_stone_buff_id(self):
        """获得当前镶嵌宝石对应的buff id
        """
        stones_id = []
        stones_id.extend(utils.split_to_int(self.weapon_stones_id))
        stones_id.extend(utils.split_to_int(self.armor_stones_id))
        stones_id.extend(utils.split_to_int(self.treasure_stones_id))

        buffs_id = []
        for stone in stones_id:
            if stone == 0:
                continue
            buffs_id.append(data_loader.ItemBasicInfo_dict[stone].value)

        return buffs_id


    @staticmethod
    def get_default_soldier_basic_id(basic_id):
        """获取初始状态下，英雄所带兵种的 basic id
        Args:
            basic_id[int]: 英雄的基础 id
        Returns:
            英雄默认所带兵种的 basic id
            失败返回 None
        """
        type = data_loader.HeroBasicInfo_dict[basic_id].soldierType
        if type == int(float(data_loader.OtherBasicInfo_dict["soldier_footman"].value)):
            return int(float(data_loader.OtherBasicInfo_dict["footman_base_id"].value))
        elif type == int(float(data_loader.OtherBasicInfo_dict["soldier_cavalry"].value)):
            return int(float(data_loader.OtherBasicInfo_dict["cavalry_base_id"].value))
        elif type == int(float(data_loader.OtherBasicInfo_dict["soldier_archer"].value)):
            return int(float(data_loader.OtherBasicInfo_dict["archer_base_id"].value))


    def update_soldier(self, soldier, technology_basic_ids):
        """计算英雄更换兵种之后的状态
        1 英雄达到等级限制
        2 会更新英雄的数值：战斗力
        Args:
            soldierd[SoldierInfo]: 新兵种的信息
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            是否成功
        """
        level = soldier.level
        #计算英雄可以配置该兵种的等级
        while level > 1:
            key = "%s_%s" % (soldier.basic_id, level)
            need_level = data_loader.SoldierBasicInfo_dict[key].heroLevel
            if self.level >= need_level:
                break
            level -= 1

        key = "%s_%s" % (soldier.basic_id, level)
        soldier_type = data_loader.SoldierBasicInfo_dict[key].type

        if data_loader.HeroBasicInfo_dict[self.basic_id].soldierType != soldier_type:
            logger.warning("Invalid soldier type[type=%d][hero soldier basic id=%d]" %
                    (soldier_type, self.basic_id))
            #return False

        self.soldier_basic_id = soldier.basic_id
        self.soldier_level = level

        logger.debug("Hero update soldier"
                "[hero basic id=%d][soldier basic id=%d][soldier level=%d]" %
                (self.basic_id, self.soldier_basic_id, self.soldier_level))

        self._update_scores(technology_basic_ids)
        return True


    def get_equipment(self, type):
        """获得英雄装备的 id
        Args:
            type[int]: 装备的类型
        Returns:
            equipment_id
            如果小于0，表示失败
        """
        equipments_id = utils.split_to_int(self.equipments_id)

        if (type == self.EQUIPMENT_TYPE_WEAPON or
                type == self.EQUIPMENT_TYPE_ARMOR or
                type == self.EQUIPMENT_TYPE_TREASURE):
            return equipments_id[type - 1]

        logger.warning("Invalid equipment type[type=%d]" % type)
        return self.EQUIPMENT_INVALID_ID


    def get_equipments(self):
        """获得英雄装备的 id
        """
        return utils.split_to_int(self.equipments_id)


    def get_equipment_stones(self, type):
        """获得装备上镶嵌的宝石
        """
        if type == self.EQUIPMENT_TYPE_WEAPON:
            return utils.split_to_int(self.weapon_stones_id)
        elif type == self.EQUIPMENT_TYPE_ARMOR:
            return utils.split_to_int(self.armor_stones_id)
        elif type == self.EQUIPMENT_TYPE_TREASURE:
            return utils.split_to_int(self.treasure_stones_id)
        else:
            return None


    def is_able_to_update_equipment(self, type, target_equipment_id):
        """判断英雄是否可以更新到目标的装备
        """
        if (type != self.EQUIPMENT_TYPE_WEAPON and
                type != self.EQUIPMENT_TYPE_ARMOR and
                type == self.EQUIPMENT_TYPE_TREASURE):
            return False

        if data_loader.EquipmentBasicInfo_dict[target_equipment_id].type != type:
            return False

        #英雄等级、星级满足要求
        need_level = data_loader.EquipmentBasicInfo_dict[target_equipment_id].levelLimit
        need_star = data_loader.EquipmentBasicInfo_dict[target_equipment_id].starLevelLimit
        if self.level < need_level or self.star < need_star:
            return False

        return True


    def calc_hero_and_soldier_battle_score(self, technology_basic_ids):
        """获得英雄战力、英雄所带兵种的战力
        """
        attribute = HeroInfo._calc_base_attribute(self.basic_id, self.level, self.star)

        base_score = self._calc_battle_base_score(attribute)
        skill_score = self._calc_all_battle_skill_score()
        soldier_score = self._calc_battle_soldier_score(technology_basic_ids)
        equipment_score = self._calc_battle_equipment_score()
        herostar_score = self._calc_battle_herostar_score()
        awaken_score = self._calc_awaken_score()
        refine_score = self._calc_refine_score()

        hero_battle_score = int(
                base_score + skill_score + equipment_score + herostar_score
                + awaken_score + refine_score)

        return (hero_battle_score, soldier_score)


    def update_equipment(self, type, target_equipment_id, technology_basic_ids):
        """英雄更新装备
        同时会更新评分
        Args:
            type[int]: 装备的类型
            equipment_id[int]: 装备的 id
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            True: 更新装备成功
            False: 更新装备失败
        """
        if data_loader.EquipmentBasicInfo_dict[target_equipment_id].type != type:
            logger.warning("Unmatch equipment[equipment id=%d][expect type=%d]" %
                    (target_equipment_id, type))
            return False

        #英雄等级、星级满足要求
        need_level = data_loader.EquipmentBasicInfo_dict[target_equipment_id].levelLimit
        need_star = data_loader.EquipmentBasicInfo_dict[target_equipment_id].starLevelLimit
        if self.level < need_level or self.star < need_star:
            logger.warning("Level or star not satisfied equipment"
                    "[equipment id=%d][level=%d][star=%d][need level=%d][need star=%d]" %
                    (target_equipment_id, self.level, self.star, need_level, need_star))
            return False

        equipments_id = utils.split_to_int(self.equipments_id)
        if (type == self.EQUIPMENT_TYPE_WEAPON or
                type == self.EQUIPMENT_TYPE_ARMOR or
                type == self.EQUIPMENT_TYPE_TREASURE):
            equipments_id[type - 1] = target_equipment_id
            self.equipments_id = utils.join_to_string(equipments_id)
            self._update_scores(technology_basic_ids)
            return True

        logger.warning("Invalid equipment type[type=%d]" % type)
        return False


    def update_equipment_stones(self, type, stone_basic_ids, technology_basic_ids):
        """更新宝石镶嵌
        """
        if len(stone_basic_ids) > self.EQUIPMENT_STONE_NUM:
            return False

        if type == self.EQUIPMENT_TYPE_WEAPON:
            self.weapon_stones_id = utils.join_to_string(stone_basic_ids)
        elif type == self.EQUIPMENT_TYPE_ARMOR:
            self.armor_stones_id = utils.join_to_string(stone_basic_ids)
        elif type == self.EQUIPMENT_TYPE_TREASURE:
            self.treasure_stones_id = utils.join_to_string(stone_basic_ids)
        else:
            return False

        self._update_scores(technology_basic_ids)
        return True


    def get_skill(self, index):
        """获得英雄对应技能 id
        """
        if index < 0 or index > 3:
            logger.warning("Invalid skill index[index=%d]" % index)
            return -1

        skills = utils.split_to_int(self.skills_id)
        return skills[index]


    def is_able_to_upgrade_skill(self, index):
        """判断技能是否可以升级
        """
        if index < 0 or index > 3:
            logger.warning("Invalid skill index[index=%d]" % index)
            return False

        #技能未配置
        skill_id = self.get_skill(index)
        if skill_id == 0:
            return False

        #已经升到顶级
        next_id = data_loader.SkillBasicInfo_dict[skill_id].nextId
        if next_id == 0:
            return False

        #技能等级不能超过英雄等级
        next_level = data_loader.SkillBasicInfo_dict[next_id].level
        return next_level <= self.level


    def upgrade_skill(self, index, technology_basic_ids):
        """英雄技能升级
        1 一次只能升级一个技能
        2 技能一次只能升一级
        3 消耗金钱和一个技能点数
        4 英雄可以有四个技能：技能在英雄达到一定级别后开启
        5 技能升级速度不能超过英雄升级速度
        6 会更新英雄的数值：战斗力
        Args:
            index[int]: 指定升级第几个技能，[0, 3]
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            (ret, cost_money)
            ret: 是否升级技能成功
            cost_money: 升级花费的金钱
        """
        cost_money = 0

        if not self.is_able_to_upgrade_skill(index):
            logger.warning("Not able to upgrade skill[index=%d]" % index)
            return (False, cost_money)

        skills = utils.split_to_int(self.skills_id)
        skill_id = skills[index]

        next_id = data_loader.SkillBasicInfo_dict[skill_id].nextId
        next_level = data_loader.SkillBasicInfo_dict[next_id].level
        cost_money = data_loader.SkillLevelBasicInfo_dict[next_level].money

        skills[index] = next_id
        self.skills_id = "#".join(map(str, skills))

        self._update_scores(technology_basic_ids)

        return (True, cost_money)


    def upgrade_skill_special(self, index, target_skill_id, technology_basic_ids):
        """英雄技能升级：特殊版
        Args:
            index[int]: 指定升级第几个技能，[0, 3]
            target_skill_id[int]: 目标的技能 id
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            是否升级成功
        """
        if index < 0 or index > 3:
            logger.warning("Invalid skill index[index=%d]" % index)
            return False

        skills = utils.split_to_int(self.skills_id)
        skill_id = skills[index]

        while skill_id != target_skill_id:
            skill_id = data_loader.SkillBasicInfo_dict[skill_id].nextId
            if skill_id == 0:
                logger.warning("Skill is reach max level"
                        "[index=%d][skill id=%d][origin skill id=%d]" %
                        (index, skill_id, skills[index]))
                #return False
                skill_id = target_skill_id
                break

        skills[index] = skill_id
        self.skills_id = "#".join(map(str, skills))

        self._update_scores(technology_basic_ids)
        return True


    @staticmethod
    def _get_skill_unlock_level(index):
        """计算技能解锁等级
        Args:
            index[int]: 是英雄的第几个技能 [0, 3]
        Returns:
            需要的英雄等级
        """
        key = "UnlockSkillLevel%d" % (index + 1)
        level = int(float(data_loader.OtherBasicInfo_dict[key].value))
        return level


    def _is_skill_available(self, index):
        """计算技能是否开启
        Args:
            index[int]: 是英雄的第几个技能 [0, 3]
        Returns:
            是否开启
        """
        base_limit = HeroInfo._get_skill_unlock_level(index)
        return self.level >= base_limit


    def is_working_in_building(self):
        """英雄是否在建筑物中工作
        """
        return self.place_type == self.PLACE_TYPE_BUILDING


    def is_working_in_node(self):
        """英雄是否在地图节点上进行采集工作
        """
        return self.place_type == self.PLACE_TYPE_NODE


    def assign_working_in_building(self, building_id, now):
        """指派英雄进行工作：建造、研究、采集等等
        """
        if self.place_type != self.PLACE_TYPE_INVALID:
            logger.warning("Hero is working[basic id=%d][place type=%d][place id=%d]" %
                    (self.basic_id, self.place_type, self.place_id))
            return False

        self.place_type = self.PLACE_TYPE_BUILDING
        self.place_id = building_id
        self.update_time = now
        return True


    def assign_working_in_node(self, node_id, now):
        """指派英雄进行工作：建造、研究、采集等等
        """
        if self.place_type != self.PLACE_TYPE_INVALID:
            logger.warning("Hero is working[basic id=%d][place type=%d][place id=%d]" %
                    (self.basic_id, self.place_type, self.place_id))
            return False

        self.place_type = self.PLACE_TYPE_NODE
        self.place_id = node_id
        self.update_time = now
        return True


    def finish_working(self):
        """结束工作
        """
        if self.place_type == self.PLACE_TYPE_INVALID:
            logger.warning("Hero is not working[basic id=%d]" % self.basic_id)
            #return False

        self.place_type = self.PLACE_TYPE_INVALID
        self.place_id = 0
        self.update_time = 0
        return True


    def update_working_exp(self, exp_per_hour, end_time, user_level, technology_basic_ids):
        """
        结算英雄工作经验
        Args:
            exp_per_hour[int]: 每个小时可获得的经验
            end_time[int]: 结算时间
            technology_basic_ids[int[]]:影响英雄所带兵种战力的科技
        Returns:
            -1: 失败
            0 : 成功，英雄未升级
            >0: 成功，英雄升级，返回升了多少级
        """
        if self.place_type == self.PLACE_TYPE_INVALID:
            logger.warning("Hero is not working[basic id=%d]" % self.basic_id)
            #return (False, False)
            return 0

        seconds = end_time - self.update_time
        seconds_of_one_hour = 3600.00

        exp = int(exp_per_hour * seconds / seconds_of_one_hour)
        need_seconds = int(exp * seconds_of_one_hour / exp_per_hour)

        self.update_time += need_seconds
        return self.level_up(exp, user_level, technology_basic_ids)


    def set_in_battle(self, node_basic_id):
        self.battle_node_basic_id = node_basic_id


    def clear_in_battle(self):
        self.battle_node_basic_id = 0


    def set_in_anneal_sweep(self, floor):
        self.anneal_sweep_floor = floor


    def clear_in_anneal_sweep(self):
        self.anneal_sweep_floor = 0


    def update_buffs(self, buffs_id, technology_basic_ids):
        """更新buff,影响战力
        """
        self.buffs_id = utils.join_to_string(buffs_id)

        self._update_scores(technology_basic_ids)
        return True


    def clear_buffs(self, technology_basic_ids):
        """清除羁绊buff
        """
        self.buffs_id = ''

        self._update_scores(technology_basic_ids)
        return True


    def _update_scores(self, technology_basic_ids):
        """当英雄变化（升级、升星、更新装备等）时更新英雄属性评分
        """
        attribute = HeroInfo._calc_base_attribute(self.basic_id, self.level, self.star)

        self._update_research_score(attribute)
        self._update_interior_score(attribute)
        self._update_defence_score(attribute)
        self._update_battle_score(attribute, technology_basic_ids)


    @staticmethod
    def _calc_base_attribute(basic_id, level, star):
        """根据等级和星级折算英雄的基础属性
        Retures:
            基础属性，包括力量、敏捷、智力、政治数值
            均为浮点数类型
        """
        hero_type = data_loader.HeroBasicInfo_dict[basic_id].type
        attribute = data_loader.HeroBasicInfo_dict[basic_id].baseAttribute
        delta = data_loader.HeroBasicInfo_dict[basic_id].baseAttributeDelta
        coefficient = data_loader.HeroStarLevelBasicInfo_dict[star].coefficient

        result = copy.deepcopy(attribute)
        result.strength += delta.strength * (level - 1)
        result.strength *= coefficient
        result.agile += delta.agile * (level - 1)
        result.agile *= coefficient
        result.intelligence += delta.intelligence * (level - 1)
        result.intelligence *= coefficient
        result.politics += delta.politics * (level - 1)
        result.politics *= coefficient

        result.strength = utils.ceil_to_int(result.strength)
        result.agile= utils.ceil_to_int(result.agile)
        result.intelligence = utils.ceil_to_int(result.intelligence)
        result.politics = utils.ceil_to_int(result.politics)

        logger.debug("Calc hero main attribute[basic_id=%d][level=%d][star=%d]"
                "[strength=%d][agile=%d][intelligence=%d][politics=%d]" % 
                (basic_id, level, star,
                result.strength, result.agile, result.intelligence, result.politics))
        return result

    @staticmethod
    def _calc_detailed_attribute(basic_id, level, star):
        """计算英雄的详细属性值
        Returns:
            (生命, 功速, 攻强, 护甲, 爆击, 闪避, 招架, 计谋, 阵法, 内务, 研究)
        """
        base = HeroInfo._calc_base_attribute(basic_id, level, star)
        hero_type = data_loader.HeroBasicInfo_dict[basic_id].type

        if hero_type == HeroInfo.HERO_TYPE_STRENGTH:
            life = utils.floor_to_int(base.strength * 29)
            #attack_speed = utils.floor_to_int(base.agile * 2.5 - 5.0)
            attack_speed = base.agile * 2.5 - 5.0
            power = utils.floor_to_int(base.strength * 2.4 + base.agile * 1.6)
            armor = utils.floor_to_int(base.strength * 3.4 + base.agile * 2.1)
            crit = utils.floor_to_int(base.strength * 0.7 + base.agile * 1)
            dodge = utils.floor_to_int(base.agile * 2)
            parry = utils.floor_to_int(base.strength * 4.9 + 5.7)
            stratagem = utils.floor_to_int(base.intelligence * 4)
            tactics = utils.floor_to_int(base.intelligence * 2 + base.politics * 2)

        elif hero_type == HeroInfo.HERO_TYPE_AGILE:
            life = utils.floor_to_int(base.strength * 29)
            #attack_speed = utils.floor_to_int(base.agile * 1.5)
            attack_speed = base.agile * 1.5
            power = utils.floor_to_int(base.strength * 1.8 + base.agile * 1.7)
            armor = utils.floor_to_int(base.strength * 3 + base.agile)
            crit = utils.floor_to_int(base.strength * 1.3 + base.agile * 3)
            dodge = utils.floor_to_int(base.agile * 5.74 + 19.5)
            parry = utils.floor_to_int(base.strength * 2.1)
            stratagem = utils.floor_to_int(base.intelligence * 4)
            tactics = utils.floor_to_int(base.intelligence * 2 + base.politics * 2)

        elif hero_type == HeroInfo.HERO_TYPE_INTELLIGENCE:
            life = utils.floor_to_int(base.strength * 29)
            #attack_speed = utils.floor_to_int(base.agile * 1.5)
            attack_speed = base.agile * 1.5
            power = utils.floor_to_int(base.strength * 1.8 + base.agile * 1.7)
            armor = utils.floor_to_int(base.strength * 3 + base.agile)
            crit = utils.floor_to_int(base.intelligence * 0.9 + 16.7)
            dodge = utils.floor_to_int(base.agile * 5.74 + 19.5)
            parry = utils.floor_to_int(base.strength * 2.1)
            stratagem = utils.floor_to_int(base.intelligence * 4)
            tactics = utils.floor_to_int(base.intelligence * 2 + base.politics * 2)

        elif hero_type == HeroInfo.HERO_TYPE_POLITICS:
            life = utils.floor_to_int(base.strength * 29)
            #attack_speed = utils.floor_to_int(base.agile * 1.5)
            attack_speed = base.agile * 1.5
            power = utils.floor_to_int(base.strength * 1.8 + base.agile * 1.7)
            armor = utils.floor_to_int(base.strength * 3 + base.agile)
            crit = utils.floor_to_int(base.intelligence * 0.9 + 16.7)
            dodge = utils.floor_to_int(base.agile * 5.74 + 19.5)
            parry = utils.floor_to_int(base.strength * 2.1)
            stratagem = utils.floor_to_int(base.intelligence * 4)
            tactics = utils.floor_to_int(base.intelligence * 2 + base.politics * 2)
        
        else:
            raise Exception("hero type invalid[basic_id=%d][type=%s]" % basic_id, hero_type)

        interior = utils.floor_to_int(base.politics * 4)
        research = utils.floor_to_int(base.intelligence * 2 + base.politics * 2)

        logger.debug("Calc hero detailed attribute[basic_id=%d][level=%d][star=%d]"
                "[life=%d][attack_speed=%s][power=%d][armor=%d][crit=%d][dodge=%d][parry=%d]"
                "[stratagem=%d][tactics=%d][interior=%d][research=%d]" % 
                (basic_id, level, star,
                life, attack_speed, power, armor, crit, dodge, parry, stratagem, tactics,
                interior, research))

        return (life, attack_speed, power, armor, crit, dodge, parry, stratagem, tactics,
                interior, research)


    def _update_interior_score(self, attribute):
        """
        更新内务评分：影响计算资源产出速度
        1 受政治数值影响
        2 受洗髓影响
        3 受装备影响
        Args:
            attribute: 英雄基础属性值，包括力量、敏捷、智力、政治数值
        """
        self.interior_score = int(attribute.politics) * 4

        unlock_level = self.refine_unlock_level()
        refine_attribute = self._calc_base_attribute(self.basic_id, unlock_level, HeroInfo.get_min_star_level())
        refine_score = int(refine_attribute.politics) * 4
        rate = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].scoreRate / 100.0
        refine_score *= rate

        self.interior_score += int(refine_score)

        equipments_id = utils.split_to_int(self.equipments_id)
        for id in equipments_id:
            self.interior_score += data_loader.EquipmentBasicInfo_dict[
                    id].politicsAttribute.internalAffairs
            self.interior_score += data_loader.EquipmentBasicInfo_dict[
                    id].additionPoliticsAttribute.internalAffairs

        self.interior_score += self._calc_interior_herostar_score()

    def _update_research_score(self, attribute):
        """
        更新研究评分：影响建筑建造/科技升级时间
        1 受敏捷和政治数值影响
        2 受洗髓影响
        3 受装备影响
        Args:
            attribute: 英雄基础属性值，包括力量、敏捷、智力、政治数值
        """
        self.research_score = int(attribute.intelligence * 2 + attribute.politics * 2)

        unlock_level = self.refine_unlock_level()
        refine_attribute = self._calc_base_attribute(self.basic_id, unlock_level, HeroInfo.get_min_star_level())
        refine_score = int(refine_attribute.intelligence * 2 + refine_attribute.politics * 2)
        rate = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].scoreRate / 100.0
        refine_score *= rate

        self.research_score += int(refine_score)

        equipments_id = utils.split_to_int(self.equipments_id)
        for id in equipments_id:
            self.research_score += data_loader.EquipmentBasicInfo_dict[
                    id].politicsAttribute.research
            self.research_score += data_loader.EquipmentBasicInfo_dict[
                    id].additionPoliticsAttribute.research


    def _update_defence_score(self, attribute):
        """
        更新城防贡献值，影响城防
        Args:
            attribute: 英雄基础属性值，包括力量、敏捷、智力、政治数值
        """
        self.defense_score = int(attribute.strength + attribute.agile)

        unlock_level = self.refine_unlock_level()
        refine_attribute = self._calc_base_attribute(self.basic_id, unlock_level, HeroInfo.get_min_star_level())
        refine_score = int(refine_attribute.strength + refine_attribute.agile)
        rate = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].scoreRate / 100.0
        refine_score *= rate

        self.defense_score += int(refine_score)


    def _update_battle_score(self, attribute, technology_basic_ids):
        """更新英雄战斗力评分
        由 基础属性评分 + 战斗技能评分 + 兵种评分 + 装备评分 组成
        Args:
            attribute: 英雄基础属性值，包括力量、敏捷、智力、政治数值
        """
        base_score = self._calc_battle_base_score(attribute)
        skill_score = self._calc_all_battle_skill_score()
        soldier_score = self._calc_battle_soldier_score(technology_basic_ids)
        equipment_score = self._calc_battle_equipment_score()
        herostar_score = self._calc_battle_herostar_score()
        awaken_score = self._calc_awaken_score()
        refine_score = self._calc_refine_score()

        battle_score = int(
                base_score + skill_score + soldier_score + equipment_score + herostar_score
                + awaken_score + refine_score)
        buff_score = self._calc_battle_buff_score(soldier_score)

        self.battle_score = battle_score + buff_score

        logger.debug("hero battle score[basic id=%d][score=%d]"
                "[base=%d][skill=%d][soldier=%d][equipment=%d][buff=%d]" %
                (self.basic_id, self.battle_score, base_score,
                    skill_score, soldier_score, equipment_score, buff_score))


    def _calc_battle_base_score(self, attribute):
        """计算基础战斗力评分
        Args:
            attribute: 英雄基础属性值，包括力量、敏捷、智力、政治数值
        """
        type = data_loader.HeroBasicInfo_dict[self.basic_id].type

        #TODO 优化计算
        if type == int(float(data_loader.OtherBasicInfo_dict["hero_strength"].value)):
            return utils.floor_to_int(attribute.strength / 4.5 * 9 +
                    attribute.agile / 1.5 * 3)
        elif type == int(float(data_loader.OtherBasicInfo_dict["hero_agile"].value)):
            return utils.floor_to_int(attribute.strength / 3.5 * 3 +
                    attribute.agile / 2.5 * 9)
        elif type == int(float(data_loader.OtherBasicInfo_dict["hero_intelligence"].value)):
            return utils.floor_to_int(attribute.strength / 2.6 * 3 +
                    attribute.intelligence / 3.4 * 9)
        elif type == int(float(data_loader.OtherBasicInfo_dict["hero_politics"].value)):
            return utils.floor_to_int(attribute.strength / 2.6 * 3 +
                    attribute.intelligence / 3.4 * 4.5 +
                    attribute.politics / 3.4 * 4.5)


    def _calc_all_battle_skill_score(self):
        """计算英雄技能战斗力评分
        """
        skills = utils.split_to_int(self.skills_id)
        score = 0

        for (index, skill_id) in enumerate(skills):
            if skill_id == 0:
                continue
            if self._is_skill_available(index):
                score += self._calc_battle_skill_score(skill_id)

        return score


    def _calc_battle_skill_score(self, skill_id):
        """计算技能战斗力评分
        Args:
            skill_id[int]: 技能 id
        Retures:
            技能战斗力评分
        """
        if data_loader.SkillBasicInfo_dict[skill_id].isAttackSkill:
            return data_loader.SkillBasicInfo_dict[skill_id].score
        return 0


    def _calc_battle_soldier_score(self, technology_basic_ids):
        """计算兵种战斗力评分
        Retures:
            兵种战斗力评分
        """
        key = "%s_%s" % (self.soldier_basic_id, self.soldier_level)
        score = data_loader.SoldierBasicInfo_dict[key].battleScore
        score *= float(data_loader.OtherBasicInfo_dict["soldierNumOfHero"].value)

        #战斗科技加成
        total_rate = 1.0
        for basic_id in technology_basic_ids:
            total_rate += (data_loader.BattleTechnologyBasicInfo_dict[basic_id].battleScoreRate - 1.0)

        score *= total_rate
        return utils.floor_to_int(score)


    def _calc_battle_equipment_score(self):
        """计算装备战斗力评分
        Returns:
            装备战斗力评分
        """
        equipments_id = utils.split_to_int(self.equipments_id)
        score = 0
        for id in equipments_id:
            score += data_loader.EquipmentBasicInfo_dict[id].battleScore
        return int(score)


    def _calc_battle_buff_score(self, battle_score):
        """计算英雄buff的战力
          1. 羁绊的buff
          2. 进化等级对应的buff
        """
        buffs_id = utils.split_to_int(self.buffs_id)        #羁绊buff id
        evolution_buff_ids = self._get_evolution_buff_id()   #进化buff id
        stone_buff_ids = self._get_stone_buff_id()    #宝石buff id
        if len(evolution_buff_ids) != 0:
            buffs_id.extend(evolution_buff_ids)
        if len(stone_buff_ids) != 0:
            buffs_id.extend(stone_buff_ids)

        logger.debug("calc battle buff score[buff_ids=%s]" % utils.join_to_string(buffs_id))

        coefficient = 0.0
        score = 0

        BUFF_TYPE_ADD = 1    #buff加法
        BUFF_TYPE_MULTI = 2  #buff乘法
        for id in buffs_id:
            type = int(data_loader.BuffBasicInfo_dict[id].type)
            if type == BUFF_TYPE_ADD:
                coefficient = int(float(data_loader.BuffBasicInfo_dict[id].battleScoreCoefficient))
                score += coefficient
            elif type == BUFF_TYPE_MULTI:
                coefficient = float(data_loader.BuffBasicInfo_dict[id].battleScoreCoefficient) - 1.0
                score += utils.floor_to_int(battle_score * coefficient)

        return score

    def _calc_battle_herostar_score(self):
        """计算将星的战力"""
        herostar_list = self.get_herostars_set()
        score = 0
        for star_id in herostar_list:
            score += HeroStarInfo.get_battle_score(star_id)
        
        #计算套装技能带来的战力
        cons_list = [
            HeroStarInfo.get_constellation_id(star_id)
            for star_id in herostar_list]
        cons_list.sort()

        last_cons = -1
        cons_count = 1
        for cons in cons_list:
            if cons == last_cons:
                cons_count += 1
            else:
                score += self._calc_herostar_skill_score(last_cons, cons_count)
                cons_count = 1
            last_cons = cons
        score += self._calc_herostar_skill_score(last_cons, cons_count)
        return score

    def _calc_herostar_skill_score(self, constellation_id, constellation_num):
        """计算套装技能带来的战力"""
        if constellation_id <= 0:
            return 0

        skills_id = []
        num_list = copy.deepcopy(data_loader.ConstellationBasicInfo_dict[constellation_id].limitNum)
        num_list.append(999)
        for i, num in enumerate(num_list):
            if i != 0:
                skills_id.append(
                    data_loader.ConstellationBasicInfo_dict[constellation_id].suitSkillID[i-1])
            if constellation_num < num:
                break
        
        score = 0
        for skill_id in skills_id:
            score += data_loader.SkillBasicInfo_dict[skill_id].score
        return score
        

    def _calc_interior_herostar_score(self):
        """计算将星的内政分"""
        herostar_list = self.get_herostars_set()
        score = 0
        for star_id in herostar_list:
            score += HeroStarInfo.get_interior_score(star_id)
        return score

    def _calc_awaken_score(self):
        """计算觉醒带来的战力"""
        if self.is_awaken == 1:
            skill_id = data_loader.HeroAwakeningBasicInfo_dict[self.basic_id].skillID
            return data_loader.SkillBasicInfo_dict[skill_id].score
        else:
            return 0

    def _calc_refine_score(self):
        """计算洗髓带来的战力"""
        unlock_level = self.refine_unlock_level()
        attribute = self._calc_base_attribute(self.basic_id, unlock_level, HeroInfo.get_min_star_level())
        rate = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].scoreRate / 100.0
        return self._calc_battle_base_score(attribute) * rate

    def split(self):
        """分解英雄得到将魂石
        Args:
            basic_id[int]: 英雄的 basic id
        Returns:
            (item_basic id, num): 可获得的将魂石的 basic id 和数量
        """
        num_starsoul = 0
        star_level = self.star

        while star_level >= HeroInfo.get_min_star_level():
            num_starsoul += data_loader.HeroStarLevelBasicInfo_dict[star_level].perceptivity
            star_level -= 1

        item_basic_id = data_loader.HeroBasicInfo_dict[self.basic_id].starSoulBasicId
        return (item_basic_id, num_starsoul)


    def is_need_broadcast(self):
        """突破到高等级时触发广播
        """
        for level in HeroInfo.BROADCAST_EVOLUTION_LEVELS:
            if self.evolution_level == level:
                return True

        return False


    def create_broadcast_content(self, user):
        """创建广播信息
        """
        key = "broadcast_id_hero_evolution_%d" % self.evolution_level

        broadcast_id = int(float(data_loader.OtherBasicInfo_dict[key].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(user.name), 1)
        content = content.replace("#str#", ("@%s@" %
            data_loader.HeroBasicInfo_dict[self.basic_id].nameKey.encode("utf-8")), 1)

        return (mode_id, priority, life_time, content)


    def is_need_broadcast_star_level(self):
        """突破到高等级时触发广播
        """
        for star in HeroInfo.BROADCAST_STAR_LEVELS:
            if self.star == star:
                return True

        return False


    def create_broadcast_content_star_level(self, user):
        """创建广播信息
        """
        key = "broadcast_id_hero_star_level"

        broadcast_id = int(float(data_loader.OtherBasicInfo_dict[key].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(user.name), 1)
        content = content.replace("#str#", ("@%s@" %
            data_loader.HeroBasicInfo_dict[self.basic_id].nameKey.encode("utf-8")), 1)
        content = content.replace("#str#", str(int(self.star / 10)), 1)

        return (mode_id, priority, life_time, content)


    def get_herostars(self):
        return utils.split_to_int(self.herostar_id)

    def get_herostars_set(self):
        return set([
            star_id
            for star_id in self.get_herostars()
            if star_id != 0
        ])

    def wear_herostar(self, star_id, index, technology_basic_ids):
        """装备将星"""
        herostar_list = self.get_herostars()
        herostar_list[index] = star_id
        self.herostar_id = utils.join_to_string(herostar_list)
        
        self._update_scores(technology_basic_ids)

    def update_herostar(self, old_star_id, new_star_id, technology_basic_ids):
        """更新将星"""
        assert old_star_id in self.get_herostars_set()
        index = self.unload_herostar(old_star_id, technology_basic_ids)
        self.wear_herostar(new_star_id, index, technology_basic_ids)

    def unload_herostar(self, star_id, technology_basic_ids):
        """卸下将星"""
        herostar_list = self.get_herostars()
        index = herostar_list.index(star_id)
        herostar_list[index] = 0
        self.herostar_id = utils.join_to_string(herostar_list)

        self._update_scores(technology_basic_ids)

        return index

    def awaken_hero(self, technology_basic_ids):
        """武将觉醒"""
        self.is_awaken = 1
        self._update_scores(technology_basic_ids)


    def get_refine_values(self):
        """获取洗髓所有属性值"""
        values = utils.split_to_int(self.refine_value)
        if len(values) != len(self.REFINE_TYPES) and len(values) != 0:
            raise Exception("hero refine value invalid[user_id=%d][id=%d][value=%s]" %
                    (self.user_id, self.id, self.refine_value))

        if len(values) == 0:
            return (0,) * len(self.REFINE_TYPES)
        else:
            return tuple(values)


    def set_refine_value(self, value, refine_type=None, refine_index=None):
        """设置洗髓属性值"""
        assert refine_type is not None or refine_index is not None
        values = list(self.get_refine_values())
        if refine_index is None:
            values[self.REFINE_TYPES.index(refine_type)] = value
        else:
            values[refine_index] = value
        self.refine_value = utils.join_to_string(values)

    def refine_unlock_level(self, level=None):
        if level is None:
            return data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].heroUnlockLv
        else:
            return data_loader.RefineHeroAttributeBasicInfo_dict[level].heroUnlockLv

    def _refine_value_max(self, level):
        """洗髓属性的最大值"""
        unlock_level = self.refine_unlock_level(level=level)
        (life, attack_speed, power, armor, crit, dodge, parry, stratagem, tactics, 
            interior, research) = self._calc_detailed_attribute(self.basic_id, unlock_level, HeroInfo.get_min_star_level())

        info = data_loader.RefineHeroAttributeBasicInfo_dict[level]
        life = utils.round46(life * info.battleAttribute.life / 100.0)
        attack_speed = utils.round46(attack_speed * info.battleAttribute.attackSpeed / 100.0)
        power = utils.round46(power * info.battleAttribute.power / 100.0)
        armor = utils.round46(armor * info.battleAttribute.armor / 100.0)
        crit = utils.round46(crit * info.battleAttribute.critRating / 100.0)
        dodge = utils.round46(dodge * info.battleAttribute.dodgeRating / 100.0)
        parry = utils.round46(parry * info.battleAttribute.parryRating / 100.0)
        stratagem = utils.round46(stratagem * info.battleAttribute.stratagem / 100.0)
        tactics = utils.round46(tactics * info.battleAttribute.tactics / 100.0)
        interior = utils.round46(interior * info.politicsAttribute.internalAffairs / 100.0)
        research = utils.round46(research * info.politicsAttribute.research / 100.0)

        logger.debug("Calc hero refine max value[basic_id=%d][refine_level=%d]"
                "[life=%d][attack_speed=%d][power=%d][armor=%d][crit=%d][dodge=%d][parry=%d]"
                "[stratagem=%d][tactics=%d][interior=%d][research=%d]" % 
                (self.basic_id, level,
                life, attack_speed, power, armor, crit, dodge, parry, stratagem, tactics,
                interior, research))

        return (life, attack_speed, power, armor, crit, dodge, parry, stratagem, tactics,
                interior, research)

    def refine_value_limits(self):
        """获取洗髓属性值上下限"""
        if self.refine_level <= 1:
            lower_limit = (0,) * len(self.REFINE_TYPES)
        else:
            lower_limit = self._refine_value_max(self.refine_level-1)

        upper_limit = self._refine_value_max(self.refine_level)
        return (lower_limit, upper_limit)


    def refine_item(self):
        """获取当前洗髓所需的物品"""
        item_id = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].needItem
        item_num = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].itemNum

        return (item_id, item_num)

    def refine_full_attribute_num(self):
        """获取洗髓满的属性数量"""
        num = 0
        _, limits = self.refine_value_limits()
        values = self.get_refine_values()
        assert len(values) == len(limits)

        for i in xrange(len(limits)):
            if limits[i] <= values[i]:
                num += 1

        return num

    def _refine_unfull_index(self):
        """未满的属性索引"""
        values = self.get_refine_values()
        _, limits = self.refine_value_limits()
        assert len(values) == len(limits)

        unfull = []
        for i in xrange(len(limits)):
            if limits[i] > values[i]:
                unfull.append(i)

        return unfull

    def refine(self):
        """洗髓"""
        full_min = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].fullMinNum
        full_max = data_loader.RefineHeroAttributeBasicInfo_dict[self.refine_level].fullMaxNum

        full_count = random.randint(max(full_min, self.refine_count), full_max) #洗满需要的次数

        if full_count - self.refine_count > 1:
            n = len(self.REFINE_TYPES) - self.refine_full_attribute_num() - 1
            p = 1.0 / (full_count - self.refine_count)
            full_num = binom.rvs(n, p) if n != 0 else 0
        else:
            full_num = len(self.REFINE_TYPES) - self.refine_full_attribute_num()
            
        unfull = self._refine_unfull_index()
        full_index = utils.random_choose_n(unfull, full_num)
        lower_limit, upper_limit = self.refine_value_limits()

        #其他属性随机变化
        for index in unfull:
            value = random.randint(lower_limit[index], upper_limit[index])
            self.set_refine_value(value, refine_index=index)

        #选中的属性打满
        for index in full_index:
            self.set_refine_value(upper_limit[index], refine_index=index)

        self.refine_count += 1

    def refine_upgrade(self, technology_basic_ids):
        """洗髓进阶"""
        if self.refine_level + 1 not in data_loader.RefineHeroAttributeBasicInfo_dict:
            logger.warning("refine level full[user_id=%d][hero_id=%d][refine_level=%d]" % (
                self.user_id, self.id, self.refine_level))
            return False

        self.refine_level += 1
        self.refine_count = 0
        self._update_scores(technology_basic_ids)
        return True


    @staticmethod
    def get_min_star_level():
        """获取最小星级
        """
        star_levels = sorted(data_loader.HeroStarLevelBasicInfo_dict.keys())
        return star_levels[0]


