#coding:utf8
"""
Created on 2015-09-06
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 科技相关逻辑
"""

import base64
from utils import logger
from utils.ret import Ret
from datalib.data_loader import data_loader
from app import data


HERO_COUNT = 3
BROADCAST_LEVEL_LIMIT = 2


class TechnologyInfo(object):
    """科技信息
    """
    BATTLE_TECH_TYPE = 0
    INTERIOR_TECH_TYPE = 1
    SOLDIER_TECH_TYPE = 2

    def __init__(self, id = 0, user_id = 0, basic_id = 0, type = 0,
            is_upgrade = False, building_id = 0,
            start_time = 0, consume_time = 0,
            cost_money = 0, cost_food = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id
        self.type = type

        self.is_upgrade = is_upgrade
        self.building_id = building_id

        self.start_time = start_time
        self.consume_time = consume_time
        self.cost_money = cost_money
        self.cost_food = cost_food


    @staticmethod
    def generate_id(user_id, basic_id, type):
        id = user_id << 32 | type << 24 | basic_id
        return id


    @staticmethod
    def get_basic_id(id):
        return id & 0x00FFFFFF


    @staticmethod
    def create(user_id, basic_id, type):
        """创建科技信息
        """
        if (type != TechnologyInfo.BATTLE_TECH_TYPE and
                type != TechnologyInfo.INTERIOR_TECH_TYPE and
                type != TechnologyInfo.SOLDIER_TECH_TYPE):
            logger.warning("Invalid Technology type[basic_id=%d][type=%d]" %
                    (basid_id, type))
            return None

        id = TechnologyInfo.generate_id(user_id, basic_id, type)
        tech = TechnologyInfo(id, user_id, basic_id, type)
        return tech


    @staticmethod
    def create_soldier_technology(user_id, basic_id):
        """创建兵种科技信息
        """
        return TechnologyInfo.create(user_id, basic_id, TechnologyInfo.SOLDIER_TECH_TYPE)


    @staticmethod
    def create_battle_technology(user_id, basic_id):
        """创建战斗科技信息
        """
        return TechnologyInfo.create(user_id, basic_id, TechnologyInfo.BATTLE_TECH_TYPE)


    @staticmethod
    def create_interior_technology(user_id, basic_id):
        """创建内政科技信息
        """
        return TechnologyInfo.create(user_id, basic_id, TechnologyInfo.INTERIOR_TECH_TYPE)


    def is_soldier_technology(self):
        """是否兵种科技
        """
        return self.type == self.SOLDIER_TECH_TYPE


    def is_battle_technology(self):
        """是否战斗科技
        """
        return self.type == self.BATTLE_TECH_TYPE


    def is_interior_technology(self):
        """是否内政科技
        """
        return self.type == self.INTERIOR_TECH_TYPE


    @staticmethod
    def get_pre_basic_id(basic_id, type):
        """获得前置科技的 basic id
        """
        if type == TechnologyInfo.BATTLE_TECH_TYPE:
            all_techs = data_loader.BattleTechnologyBasicInfo_dict
        elif type == TechnologyInfo.INTERIOR_TECH_TYPE:
            all_techs = data_loader.InteriorTechnologyBasicInfo_dict
        elif type == TechnologyInfo.SOLDIER_TECH_TYPE:
            all_techs = data_loader.SoldierTechnologyBasicInfo_dict

        for tech_id in all_techs:
            if basic_id == all_techs[tech_id].nextId:
                logger.debug("Get pre technology[basic id=%d][pre basic id=%d]" %
                        (basic_id, tech_id))
                return tech_id

        logger.debug("No pre technology[basic id=%d]" % basic_id)
        return 0


    def get_all_pre_basic_id(self):
        """获得所有前置路径上的科技
        """
        all_pre = []

        pre_basic_id = TechnologyInfo.get_pre_basic_id(self.basic_id, self.type)
        if pre_basic_id != 0:
            all_pre.append(pre_basic_id)
            all_pre.extend(self.get_all_pre_basic_id())

        return all_pre

    def is_pre_tech(self, tech_basic_id):
        """判断是否是该科技的前置科技
        """
        all_pre = self.get_all_pre_basic_id()

        for basic_id in all_pre:
            if basic_id == tech_basic_id:
                return True

        return False


    def create_next(self):
        """创建后置科技
        """
        if technology.type == self.BATTLE_TECH_TYPE:
            next_id = data_loader.BattleTechnologyBasicInfo_dict[self.basic_id].next_id
        elif new_tech.type == self.INTERIOR_TECH_TYPE:
            next_id = data_loader.InteriorTechnologyBasicInfo_dict[self.basic_id].next_id
        elif new_tech.type == self.SOLDIER_TECH_TYPE:
            next_id = data_loader.SoldierTechnologyBasicInfo_dict[self.basic_id].next_id

        return self.create(self.user_id, next_id, self.type)


    def is_able_to_research(self, building, pre_technology, heroes):
        """判断科技是否可以研究
        1 研究建筑类型和等级满足要求
        2 前置依赖科技已经研究过了
        Args:
            building[BuildingInfo]: 研究建筑
            pre_technology[TechnologyInfo]: 前置科技
            heroes[list(HeroInfo)]: 参与英雄列表，元素可能为 None，表示此位置无英雄
        """
        #建筑物满足要求
        if self.type == self.BATTLE_TECH_TYPE:
            all_techs = data_loader.BattleTechnologyBasicInfo_dict
        elif self.type == self.INTERIOR_TECH_TYPE:
            all_techs = data_loader.InteriorTechnologyBasicInfo_dict
        elif self.type == self.SOLDIER_TECH_TYPE:
            all_techs = data_loader.SoldierTechnologyBasicInfo_dict
        else:
            logger.warning("Invalid Technology type[basic id=%d][type=%d]" %
                    (self.basid_id, self.type))
            return False

        limit_building_basic_id = all_techs[self.basic_id].limitBuildingId
        limit_building_level = all_techs[self.basic_id].limitBuildingLevel
        if (building.basic_id != limit_building_basic_id or
                building.level < limit_building_level):
            logger.warning("Building error"
                    "[basic id=%d][level=%d][exp basic id=%d][exp level=%d]" %
                    (building.basic_id, building.level,
                        limit_building_basic_id, limit_building_level))
            return False

        #前置科技已经研究过
        pre_basic_id = TechnologyInfo.get_pre_basic_id(self.basic_id, self.type)
        if pre_basic_id != 0:
            if pre_technology.basic_id != pre_basic_id or pre_technology.is_upgrade:
                logger.warning("Pre technology is not ready")
                return False

        return True


    def start_research(self, building, cost_money, cost_food, cost_time, now):
        """开始研究
        """
        self.building_id = building.id
        self.cost_money = cost_money
        self.cost_food = cost_food
        self.consume_time = cost_time
        self.start_time = now

        self.is_upgrade = True
        return True


    def is_able_to_finish_research(self, now, force = False, ret = Ret()):
        """
        是否可以完成研究
        1 科技正在研究中
        2 时间条件满足，或者强制完成
        """
        #科技正在研究中
        if not self.is_upgrade:
            logger.warning("Technology is not upgrading")
            ret.setup("NOT_UPGRADING")
            return False

        if force:
            return True
        else:
            #非强制完成，时间需要满足要求
            if self.calc_time_gap_of_finish_research(now) > 0:
                ret.setup("CANNT_FINISH")
                return False
            else:
                return True


    def finish_research(self):
        """结束研究
        """
        self.building_id = 0
        self.cost_money = 0
        self.cost_food = 0
        self.consume_time = 0
        self.start_time = 0

        self.is_upgrade = False
        return True


    def reduce_research_time(self, speed_time):
        """结束研究
        """
        if self.is_upgrade:
            if speed_time > 0:
                self.consume_time -= speed_time

            if self.consume_time < 0:
                self.consume_time = 0
        
        return True


    def is_able_to_cancel_research(self):
        """是否可以取消研究
        """
        #科技正在研究中
        if not self.is_upgrade:
            logger.warning("Technology is not upgrading")
            return False

        return True


    def calc_time_gap_of_finish_research(self, now):
        """计算完成研究还需要多少时间
        """
        finish_time = self.start_time + self.consume_time
        gap = max(0, finish_time - now)
        return gap


    def calc_resource_remittal_of_cancel_research(self):
        """计算取消研究，可以返还多少金钱粮草
        """
        ratio = float(data_loader.OtherBasicInfo_dict[
            'CancelResourceReturnCoefficient'].value)
        remittal_money = int(self.cost_money * ratio)
        remittal_food = int(self.cost_food * ratio)
        return (remittal_money, remittal_food)


    def create_broadcast_content(self, user):
        """创建广播信息
        """
        level = 1
        tech_name_key = ""
        if self.is_soldier_technology():
            level = data_loader.SoldierTechnologyBasicInfo_dict[self.basic_id].level
            tech_name_key = data_loader.SoldierTechnologyBasicInfo_dict[self.basic_id].nameKey
        elif self.is_battle_technology():
            level = data_loader.BattleTechnologyBasicInfo_dict[self.basic_id].level
            tech_name_key = data_loader.BattleTechnologyBasicInfo_dict[self.basic_id].nameKey
        elif self.is_interior_technology():
            level = data_loader.InteriorTechnologyBasicInfo_dict[self.basic_id].level
            tech_name_key = data_loader.InteriorTechnologyBasicInfo_dict[self.basic_id].nameKey
        
        if level <= BROADCAST_LEVEL_LIMIT:
            #科技等级太低不需要广播
            return (0,0,0, "")

        key = "broadcast_id_technology"
        broadcast_id = int(float(data_loader.OtherBasicInfo_dict[key].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(user.name), 1)
        content = content.replace("#str#", ("@%s@" % tech_name_key.encode("utf-8")), 1)
        content = content.replace("#str#", str(level), 1)

        return (mode_id, priority, life_time, content)



