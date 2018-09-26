#coding:utf8
"""
Created on 2015-01-26
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 建筑物相关数值计算
"""

from utils import logger
from utils import utils
from utils.ret import Ret
from datalib.data_loader import data_loader


HERO_COUNT = 3
NONE_HERO = 0
EMPTY_HEROES = "0#0#0"


class BuildingInfo(object):
    """建筑物信息
    """
    def __init__(self, id = 0, user_id = 0, basic_id = 0,
            level = 0, garrison_num = 0, hero_ids = EMPTY_HEROES,
            city_id = 0, slot_index = 0,
            is_upgrade = False, upgrade_start_time = 0, upgrade_consume_time = 0,
            money_cost = 0, food_cost = 0,
            value = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id

        self.level = level
        self.garrison_num = garrison_num

        self.hero_ids = hero_ids

        self.city_id = city_id
        self.slot_index = slot_index

        self.is_upgrade = is_upgrade
        self.upgrade_start_time = upgrade_start_time
        self.upgrade_consume_time = upgrade_consume_time
        self.money_cost = money_cost
        self.food_cost = food_cost

        self.value = value


    @staticmethod
    def generate_id(user_id, city_basic_id, slot_index, building_basic_id):
        id = city_basic_id * 1000 + slot_index
        id = id * 1000 + building_basic_id
        id = user_id << 32 | id
        return id


    @staticmethod
    def get_basic_id(id):
        basic_id = id & 0xFFFFFFFF
        basic_id = basic_id % 1000
        return basic_id


    @staticmethod
    def get_city_basic_id(id):
        city_basic_id = (id & 0xFFFFFFFF) / 1000000
        return city_basic_id


    @staticmethod
    def get_location_index(id):
        location_index = (id & 0xFFFFFFFF) / 1000 % 1000
        return location_index


    @staticmethod
    def get_mansion_id(user_id, city_basic_id):
        """
        官邸固定放在城池的第一个位置
        """
        mansion_basic_id = int(float(
            data_loader.OtherBasicInfo_dict["building_mansion"].value))
        mansion_slot_index = 1
        return generate_id(user_id, city_basic_id, mansion_slot_index, mansion_basic_id)


    @staticmethod
    def create(user_id, building_basic_id, city, slot_index,
            level = 0, garrison_num = 1):
        """新建一个建筑
        user_id[int] : 用户 id
        building_basic_id[int] : 建筑物 basic id
        city_basic_id[int] : 城池 basic id
        slot_index[int] : 在城池中的索引位置
        level[int] : 建筑物等级
        garrison_num[int] : 建筑物驻守位数量
        """
        id = BuildingInfo.generate_id(
                user_id, city.basic_id, slot_index, building_basic_id)
        building = BuildingInfo(
                id, user_id, building_basic_id, level, garrison_num, EMPTY_HEROES)
        building.city_id = city.id
        building.slot_index = slot_index

        return building


    def is_active(self, user_level, mansion_level):
        """判断建筑物是否处于活跃状态
        初始赠送给帐号的建筑物，由于玩家等级和官邸等级的限制，可能处于不活跃状态
        """
        if self.level <= 0:
            return False

        key = "%d_%d" % (self.basic_id, self.level)
        need_user_level = data_loader.BuildingLevelBasicInfo_dict[key].limitMonarchLevel
        need_mansion_level = data_loader.BuildingLevelBasicInfo_dict[key].limitMansionLevel

        if user_level < need_user_level or mansion_level < need_mansion_level:
            return False
        return True


    def is_able_to_upgrade(self, user_level, mansion_level):
        """判断建筑物是否满足了升级条件
        1 当前不处于升级状态
        2 建筑物可以升级
        3 建筑物不处于工作状态：其中没有正在工作的英雄
        3 玩家等级达到要求
        4 官邸建筑等级达到要求
        Args:
            user_level[int]: 玩家等级
            mansion_level[int]: 官邸建筑等级
        Returns:
            True
            False
        """
        if self.is_upgrade:
            logger.warning("Building is upgrading")
            return False

        if not self.is_able_to_build():
            logger.warning("Building is not able to build")
            return False

        if self.has_working_hero():
            logger.warning("Building is wroking")
            return False

        next_level = self.level + 1
        key = "%d_%d" % (self.basic_id, next_level)
        need_user_level = data_loader.BuildingLevelBasicInfo_dict[key].limitMonarchLevel
        need_mansion_level = data_loader.BuildingLevelBasicInfo_dict[key].limitMansionLevel

        if user_level < need_user_level or mansion_level < need_mansion_level:
            logger.warning("Can not upgrade due to level limit"
                    "[need user level=%d][current user level=%d]"
                    "[need mansion level=%d][current mansion level=%d]" %
                    (need_user_level, user_level, need_mansion_level, mansion_level))
            return False

        return True


    def is_able_to_finish_upgrade(self, heroes, now, force, ret=Ret()):
        """
        是否可以完成升级
        1 建筑物处于升级状态
        2 对应英雄在建筑物中参与升级
        3 升级时间满足要求，或者强制结束
        """
        if not self.is_upgrade:
            logger.warning("Building is not upgrading")
            ret.setup("NOT_UPGRADING")
            return False

        if not self.is_hero_in_building(heroes):
            return False

        if force:
            return True
        else:
            if self.calc_time_gap_of_finish_upgrade(now) > 0:
                ret.setup("CANNT_FINISH")
                return False
            else:
                return True


    def is_able_to_cancel_upgrade(self, heroes):
        """建筑物是否可以取消升级
        1 正在升级的建筑，可以取消升级
        2 对应英雄在建筑物中参与升级
        """
        if not self.is_upgrade:
            logger.warning("Building is not upgrading")
            return False

        if not self.is_hero_in_building(heroes):
            return False

        return True


    def calc_time_gap_of_finish_upgrade(self, now):
        """计算完成升级还需要多少时间
        """
        finish_time = self.upgrade_start_time + self.upgrade_consume_time
        gap = max(0, finish_time - now)
        return gap


    def calc_resource_remittal_of_cancel_upgrade(self):
        """计算取消升级，可以返还多少金钱粮草
        """
        ratio = float(data_loader.OtherBasicInfo_dict[
            'CancelResourceReturnCoefficient'].value)
        remittal_money = int(self.money_cost * ratio)
        remittal_food = int(self.food_cost * ratio)
        return (remittal_money, remittal_food)


    def start_upgrade(self, money_cost, food_cost, time_cost, heroes, now):
        """
        建筑物开始升级
        """
        if not self.set_working_hero(heroes):
            return False

        if not self.has_working_hero():
            logger.warning("Upgrade need heroes")
            return False

        self.money_cost = money_cost
        self.food_cost = food_cost
        self.upgrade_start_time = now
        self.upgrade_consume_time = time_cost

        self.is_upgrade = True
        return True


    def finish_upgrade(self, heroes):
        """建筑物结束升级
        """
        self.level += 1

        self.money_cost = 0
        self.food_cost = 0
        self.upgrade_start_time = 0
        self.upgrade_consume_time = 0

        self.is_upgrade = False

        if not self.clear_working_hero(heroes):
            return False

        return True


    def cancel_upgrade(self, heroes):
        """建筑物取消升级
        """
        self.money_cost = 0
        self.food_cost = 0
        self.upgrade_start_time = 0
        self.upgrade_consume_time = 0

        self.is_upgrade = False

        if not self.clear_working_hero(heroes):
            return False

        return True


    def reduce_upgrade_time(self, speed_time):
        """减少建筑升级时间
        """
        if self.is_upgrade:
            if speed_time > 0:
                self.upgrade_consume_time -= speed_time

            if self.upgrade_consume_time < 0:
                self.upgrade_consume_time = 0

        return True


    def is_hero_in_building(self, heroes):
        """英雄是否在建筑物中
        Args:
            heroes[list(HeroInfo)]
        """
        working_heroes = self.get_working_hero()

        for hero in heroes:
            if hero is not None and hero.id not in working_heroes:
                    return False

        return True


    def update_value(self, value):
        self.value = value
        logger.debug("Update building value[building id=%d][value=%d]" %
                (self.id, self.value))


    def start_working(self, heroes, value = 0, need_hero = True):
        """派驻英雄，建筑物开始工作：发挥自身功能
        Args:
            heroes[list(HeroInfo)]: 英雄信息列表
            value[int]: 特殊值，记录在 building.value 里
            need_hero[bool]: 是否必须要 hero 参加
        必须要派驻英雄
        """
        if not self.set_working_hero(heroes):
            return False

        if need_hero and not self.has_working_hero():
            logger.warning("No working hero")
            return False

        self.value = value
        return True


    def stop_working(self, heroes, value = 0):
        """撤出英雄，建筑物停止工作
        """
        if not self.clear_working_hero(heroes):
            return False

        self.value = value
        return True


    def update_working_by_remove_hero(self, heroes, value = 0):
        """撤出英雄，建筑物功能收到影响
        """
        if not self.remove_working_hero(heroes):
            return False

        self.value = value
        return True


    def has_working_hero(self):
        """是否有工作的英雄
        """
        return self.hero_ids != EMPTY_HEROES


    def get_working_hero(self):
        """获取工作的英雄 id
        """
        heroes_id = utils.split_to_int(self.hero_ids)
        return heroes_id


    def is_heroes_working(self, heroes):
        heroes_id = utils.split_to_int(self.hero_ids)

        for hero in heroes:
            if hero is None:
                continue

            if hero.id not in heroes_id:
                return False

        return True


    def get_working_hero_position(self, hero):
        """获取工作的英雄所在的位置
        """
        heroes_id = utils.split_to_int(self.hero_ids)
        if hero.id in heroes_id:
            return heroes_id.index(hero.id)
        else:
            return -1


    def set_working_hero(self, heroes):
        """指派参与建筑功能的武将
        不允许建筑在升级过程中指派
        只能向空位置指派英雄
        Args:
            heroes[list(HeroInfo) in/out]: 英雄列表
                    必须指派3人，其中元素允许为 None，表示对应位置为空
        Returns:
            True - 成功
            False - 失败
        """
        if self.is_upgrade:
            logger.warning("Building is upgrading")
            return False

        if len(heroes) != HERO_COUNT: #固定3个位置
            logger.warning("Error participate hero length[len=%s]" % len(heroes))
            return False

        heroes_id = utils.split_to_int(self.hero_ids)

        for index in range(0, HERO_COUNT):
            hero = heroes[index]
            if hero is None:
                continue

            if index >= self.garrison_num:
                logger.warning("Not enough garrison num[num=%d]" % self.garrison_num)
                return False
            if heroes_id[index] != NONE_HERO:
                logger.warning("Building has participate hero[index=%d][hero id=%d]" %
                        (index, heroes_id[index]))
                return False

            heroes_id[index] = hero.id

        self.hero_ids = utils.join_to_string(heroes_id)
        return True


    def clear_working_hero(self, heroes):
        """清空参与建筑功能的武将
        Args:
            heroes[list(HeroInfo)]: 英雄列表
        Returns:
            True - 成功
            False - 失败
        """
        assert len(heroes) == HERO_COUNT

        if not self.remove_working_hero(heroes):
            return False

        if self.has_working_hero():
            logger.warning("Clear working hero error[working hero=%s]" % self.hero_ids)
            return False

        return True


    def remove_working_hero(self, heroes):
        """
        移除在建筑物中工作的英雄
        不允许建筑在升级过程中指派
        如果英雄不工作在此建筑物中，返回错误
        Args:
            heroes[list(HeroInfo) in/out]: 需要移除的英雄，其中元素允许为 None，不对其进行处理
                                            并不需要按照位置排列
        Returns:
            True: 成功
            False: 失败
        """
        if self.is_upgrade:
            logger.warning("Building is upgrading")
            return False

        heroes_id = utils.split_to_int(self.hero_ids)

        for hero in heroes:
            if hero is None:
                continue

            if hero.id not in heroes_id:
                logger.warning("Hero not working in building"
                        "[building hero ids=%s][hero id=%d]" %
                        (building.hero_ids, hero.id))
                return False

            index = heroes_id.index(hero.id)
            heroes_id[index] = NONE_HERO

        self.hero_ids = utils.join_to_string(heroes_id)
        return True


    def unlock_garrison_position(self, vip_level):
        """解锁建筑驻守位
        """
        num = self.garrison_num + 1
        key = "%s_%s" % (self.basic_id, num)
        if key not in data_loader.BuildingGarrisonNumBasicInfo_dict:
            #没有更多驻守位了
            logger.debug("Invalid garrison num[building basic id=%d][garrison num=%d]" %
                    (self.basic_id, num))
            return False

        need_level = data_loader.BuildingGarrisonNumBasicInfo_dict[key].limitBuildingLevel
        if self.level < need_level:
            #建筑物没达到等级要求
            logger.debug("Building level error[need level=%d][current level=%d]" %
                    (need_level, self.level))
            return False

        need_vip = data_loader.BuildingGarrisonNumBasicInfo_dict[key].limitVipLevel
        if vip_level < need_vip:
            #vip 等级不满足要求
            logger.debug("VIP level error[need level=%d][current level=%d]" %
                    (need_vip, vip_level))
            return False

        #成功解锁
        self.garrison_num = num
        return True


    @staticmethod
    def get_mansion_basic_id():
        """获得官邸建筑的 basic id
        """
        return int(float(
                data_loader.OtherBasicInfo_dict["building_mansion"].value))


    def is_mansion(self):
        """是否是官邸
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_mansion"].value))


    def is_farmland(self):
        """是否是农场
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_farmland"].value))


    def is_market(self):
        """是否是市场
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_market"].value))


    def is_barrack(self):
        """是否是兵营
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_barrack"].value))


    def is_defense(self):
        """是否是城防建筑
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_citydefence"].value))


    def is_generalhouse(self):
        """是否是将军府
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_generalhouse"].value))


    def is_wineshop(self):
        """是否是酒肆
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_wineshop"].value))


    def is_ministerhouse(self):
        """是否是丞相府
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_ministerhouse"].value))


    def is_temple(self):
        """是否是寺庙
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_temple"].value))


    def is_moneyhouse(self):
        """是否是钱库
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_moneyhouse"].value))


    def is_foodhouse(self):
        """是否是粮仓
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_foodhouse"].value))


    def is_blacksmith(self):
        """是否是铁匠铺
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_blacksmith"].value))


    def is_watchtower(self):
        """是否是瞭望塔
        """
        return self.basic_id == int(float(
            data_loader.OtherBasicInfo_dict["building_watchtower"].value))


    def is_able_to_garrison(self):
        """判断建筑是否可以驻守
        市场、农田可以驻守
        """
        return self.is_market() or self.is_farmland()


    def is_able_to_build(self):
        """判断建筑是否可以建造升级
        只有酒肆不能升级
        """
        return not self.is_wineshop()


    def is_able_to_conscript(self):
        """判断建筑是否可以征兵
        只有兵营可以
        """
        return self.is_barrack()


    def is_able_to_research(self):
        """判断建筑是否可以进行研究
        将军府、丞相府、寺庙可以进行研究
        """
        return self.is_generalhouse() or self.is_ministerhouse() or self.is_temple()


