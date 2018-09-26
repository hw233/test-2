#coding:utf8
"""
Created on 2015-09-07
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 兵种科技相关逻辑
"""

from utils import logger
from utils.ret import Ret
from datalib.data_loader import data_loader
from app.data.technology import TechnologyInfo
from app.data.soldier import SoldierInfo
from app.data.hero import HeroInfo
from app.data.trainer import TrainerInfo
from app.core import technology as technology_module
from app.business import hero as hero_business
from app.business import team as team_business
from app import log_formater

def get_pre_technology_id(user_id, basic_id, type):
    pre_basic_id = TechnologyInfo.get_pre_basic_id(basic_id, type)
    if pre_basic_id != 0:
        return TechnologyInfo.generate_id(user_id, pre_basic_id, type)
    return 0


def get_related_soldier_id(user_id, technology_basic_id):
    soldier_basic_id = data_loader.SoldierTechnologyBasicInfo_dict[
            technology_basic_id].soldierBasicInfoId
    return SoldierInfo.generate_id(user_id, soldier_basic_id)


def start_research(basic_id, type, user, building, heroes, resource,
        pre_technology, interior_technology, now):
    """
    开始研究科技
    """
    technology = TechnologyInfo.create(user.id, basic_id, type)
    if technology is None:
        return None

    #判断是否达到了研究条件
    if not technology.is_able_to_research(building, pre_technology, heroes):
        return None

    #消耗金钱粮草
    (need_money, need_food) = technology_module.calc_consume_resource(
            basic_id, type, heroes, interior_technology)
    if not resource.cost_money(need_money):
        return None
    if not resource.cost_food(need_food):
        return None

    #消耗时间
    need_time = technology_module.calc_consume_time(
            basic_id, type, heroes, interior_technology, user)

    #派驻英雄
    for hero in heroes:
        if hero is not None and not hero.assign_working_in_building(building.id, now):
            return None
    if not building.start_working(heroes, technology.id):
        return None

    #开始研究
    if not technology.start_research(building, need_money, need_food, need_time, now):
        return None

    logger.debug("Technology need money=%d, food=%d, consume time=%d" 
            % (need_money, need_food, need_time))
    return technology


def finish_research(data, technology, user, building, heroes, resource, now, force = False, ret = Ret()):
    """
    结束研究
    Args:
        technology
        force[bool]: 是否强制结束，需要消耗元宝
    """
    #查看是否开启了支持剩余时间不多时研究立即完成的功能
    open_flags = get_flags()
    can_finish_immediately = False
    if "is_open_buildinglist" in open_flags:
        can_finish_immediately = True
    
    if (technology.calc_time_gap_of_finish_research(now) > 
        data_loader.VipBasicInfo_dict[user.vip_level].finishImediatelyTime):
        can_finish_immediately = False

    if can_finish_immediately:
        force = True

    #判断是否可以结束研究
    if not technology.is_able_to_finish_research(now, force, ret):
        logger.warning("Research is not able to finish")
        return False

    #如果强制完成（未满足研究时间条件），需要额外耗费金钱
    gap = 0
    original_gold = resource.gold
    need_gold = 0
    if force:
        gap = technology.calc_time_gap_of_finish_research(now)

        if can_finish_immediately:
            need_gold = 0
        else:
            need_gold = resource.gold_exchange_time(gap)
            if need_gold < 0:
                return False

    #结算英雄获得的经验
    if not _calc_research_exp(data, technology, heroes, user, now):
        return False

    #结束研究
    if not technology.finish_research():
        return False

    #移除参与升级的英雄
    if not building.stop_working(heroes, 0):
        return False
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False

    #记录升级次数
    trainer = data.trainer.get()
    if technology.is_soldier_technology():
        trainer.add_soldier_tech_upgrade_num(1)
    elif technology.is_battle_technology():
        trainer.add_battle_tech_upgrade_num(1)
    else:
        trainer.add_interior_tech_upgrade_num(1)

    #内政科技可能影响领地占领个数
    if technology.is_interior_technology():
        occupy_num = int(data_loader.InteriorTechnologyBasicInfo_dict[
                technology.basic_id].interiorAttributeIncrease.occupyNodeNum)
        if occupy_num != 0:
            map = data.map.get()
            map.update_occupy_node_num_technology(occupy_num)

    if force and not can_finish_immediately:
        log = log_formater.output_gold(data, -need_gold, log_formater.FINISH_TECHNOLOGY,
                "Finish technology by gold", before_gold = original_gold, reduce_time = gap)
        logger.notice(log)

    return True


def cancel_research(data, technology, user, building, heroes, resource, now):
    """取消研究
    """
    #判断是否可以取消研究
    if not technology.is_able_to_cancel_research():
        return False

    #回收部分金钱、粮草
    (remittal_money, remittal_food) = technology.calc_resource_remittal_of_cancel_research()
    resource.gain_money(remittal_money)
    resource.gain_food(remittal_food)

    #结算研究科技获得的经验
    if not _calc_research_exp(data, technology, heroes, user, now):
        return False

    #结束研究
    if not technology.finish_research():
        return False

    #移除参与升级的英雄
    if not building.stop_working(heroes, 0):
        return False
    for hero in heroes:
        if hero is not None and not hero.finish_working():
            return False

    return True


def _calc_research_exp(data, technology, heroes, user, now):
    """进行研究，英雄可以获得经验
    """
    #英雄经验
    #如果使用『立即完成』，英雄也只会获得到到当前时间为止的经验
    end_time = min(technology.start_time + technology.consume_time, now)
    exp_per_hour = data_loader.MonarchLevelBasicInfo_dict[user.level].researchExpPerHour
    for hero in heroes:
        if hero is None:
            continue

        if not hero_business.level_upgrade_by_working(
                data, hero, exp_per_hour, end_time, now):
            logger.warning("Hero upgrade failed[hero basic id=%d]" % hero.basic_id)
            return False

    return True


def post_research_for_soldier_technology(
        data, user_id, technology, now, soldier = None, heroes = [], new = False):
    """
    兵种科技完成研究的影响
    1 解锁兵种
    2 或者升级兵种
    Args:
        user_id[int]: 用户 id
        technology[TechnologyInfo]: 兵种科技信息
        soldier[SoldierInfo in/out]: 兵种信息
        heroes[list(HeroInfo) in/out]: 配置了对应兵种的英雄信息，可能需要更新英雄的兵种信息
        new[bool]: 是否是解锁新兵种
    Returns:
        None: 失败
        SoldierInfo: 处理成功，返回兵种信息
    """
    #一定是已经完成研究的科技
    assert not technology.is_upgrade

    if not technology.is_soldier_technology():
        logger.warning("Not soldier technology")
        return None

    (soldier_basic_id, soldier_level) = technology_module.generate_soldier(technology)

    if new:
        #解锁新兵种
        assert soldier is None
        assert len(heroes) == 0

        soldier = SoldierInfo.create(user_id, soldier_basic_id, soldier_level)
        return soldier

    else:
        #原有兵种升级
        assert soldier is not None

        if not soldier.upgrade():
            return None

        if soldier.basic_id != soldier_basic_id or soldier.level != soldier_level:
            logger.warning("Soldier error[gen basic id=%d][gen level=%d]"
                    "[soldier basic id=%d][soldier level=%d]" %
                    (soldier_basic_id, soldier_level,
                        soldier.basic_id, soldier.level))
            return None

        #配置该兵种的武将，更新兵种信息（有可能升级）
        for hero in heroes:
            if not hero_business.soldier_update(data, hero, soldier, now):
                return None

        return soldier


def post_research_for_battle_technology(data, technology, heroes = []):
    """
    战斗科技完成研究的影响
    更新英雄战力、部队战力、总战力
    Args:
        data[UserInfo]: 玩家数据
        technology[TechnologyInfo]: 新研究的战斗科技
        heroes[list(HeroInfo) in/out]: 需要更新战力的英雄

    Returns:
        False: 失败
        True: 处理成功，返回兵种信息
    """
    #一定是已经完成研究的科技
    assert not technology.is_upgrade

    if not technology.is_battle_technology():
        logger.warning("Not battle technology")
        return False

    new_technologys = [technology.basic_id]

    for hero in heroes:
        #影响英雄所带兵种战力的科技
        battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
                data.technology_list.get_all(True), hero.soldier_basic_id)
        
        soldier_id = SoldierInfo.generate_id(data.id, hero.soldier_basic_id)
        soldier = data.soldier_list.get(soldier_id)
        if not hero.update_soldier(soldier, battle_technology_basic_id):
            return False

        #如果英雄在队伍中，更新队伍信息
        for team in data.team_list.get_all():
            if team.is_hero_in_team(hero.id):
                if not team_business.refresh_team(data, team):
                    logger.warning("Try to refresh team failed")
                    return False

    #更新 top 阵容
    user = data.user.get(True)
    guard_list = data.guard_list.get_all()
    for guard in guard_list:
        if not guard.try_update_top_score(heroes, user.team_count):
            logger.warning("Try to update guard top score failed")
            return False

    return True


def get_flags():
    open_flags = set()
    for key, value in data_loader.Flag_dict.items():
        if int(float(value.value)) == 1:
            open_flags.add(str(key))
    
    return open_flags


