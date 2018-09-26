#coding:utf8
"""
Created on 2015-09-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 军队 相关业务逻辑
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.team import TeamInfo
from app.data.hero import HeroInfo
from app.data.battlescore import BattleScoreInfo
from app.core import battle as battle_module
from app.core import technology as technology_module


def update_team(data, team_index, heroes_basic_id):
    """更新队伍阵容
    """
    team_id = TeamInfo.generate_id(data.id, team_index)
    team = data.team_list.get(team_id)
    if team is None:
        team = TeamInfo.create(data.id, team_index)
        data.team_list.add(team)

    if not team.is_able_to_update():
        logger.warning("Team is not able to update[index=%d]" % team_index)
        return False

    #计算羁绊
    relationships_id = _calc_relationship(heroes_basic_id)
    array_heroes = []
    for basic_id in heroes_basic_id:
        if basic_id == 0:
            array_heroes.append(None)
        else:
            hero_id = HeroInfo.generate_id(data.id, basic_id)
            hero = data.hero_list.get(hero_id)
            if hero is None:
                logger.warning("Hero not exist[basic id=%d]" % basic_id)
                return False

            _update_hero_buffs(data, hero, relationships_id)
            array_heroes.append(hero)

    #更换英雄
    if not team.update(array_heroes, relationships_id):
        logger.warning("Update team failed")
        return False

    logger.debug("new team[heroes_basic_id=%s][relationships_id=%s]"
            % (utils.join_to_string(heroes_basic_id), utils.join_to_string(relationships_id)))

    return _post_update_team(data)


def refresh_team(data, team):
    """刷新队伍
    队伍英雄阵容没有变化，但是英雄可能升级了
    """
    heroes_basic_id = []
    for hero_id in team.get_heroes():
        hero = data.hero_list.get(hero_id)
        if hero is not None:
            heroes_basic_id.append(hero.basic_id)

    #计算羁绊
    relationships_id = _calc_relationship(heroes_basic_id)
    array_heroes = []
    for hero_id in team.get_heroes():
        if hero_id == 0:
            array_heroes.append(None)
        else:
            hero = data.hero_list.get(hero_id)
            _update_hero_buffs(data, hero, relationships_id)
            array_heroes.append(hero)

    if not team.update(array_heroes, relationships_id):
        logger.warning("Update team failed")
        return False

    return _post_update_team(data)


def _post_update_team(data):
    """更新了队伍阵容的后续处理
    1 可能需要更新战力排行榜
    2 可能需要更新防守阵容
    """
    all_teams = data.team_list.get_all() #获得所有的 team 信息

    battle_score = data.battle_score.get()
    battle_score.update(all_teams)

    user = data.user.get(True)
    count = user.team_count
    for guard in data.guard_list.get_all():
        if not guard.update_team(all_teams, count):
            return False

    return True


def validation(data):
    """
    验证是否合法
    1 user 是否可以拥有这么多数量的 team
    2 同一个英雄不能重复出现在不同的 team 中
    3 不允许所有的队伍为空
    """
    user = data.user.get(True)
    all_teams = data.team_list.get_all(True)

    max_num = TeamInfo.calc_max_num(user.level, user.vip_level)

    if len(all_teams) == 0:
        logger.warning("User has no team")
        return False

    index_set = set()
    hero_set = set()
    for team in all_teams:
        #检查 team 数量是否超过上限
        if team.index <= 0 or team.index > max_num:
            logger.warning("Invalid team index[index=%d][max=%d]" % (team.index, max_num))
            return False

        #检查 team index 是否重复
        if team.index in index_set:
            logger.warning("Duplicate team index[index=%d]" % team.index)
            return False
        index_set.add(team.index)

        #检查英雄是否出现在不同的 team 中
        ids = team.get_heroes()
        for id in ids:
            if id == 0:
                continue
            if id in hero_set:
                logger.warning("Duplicate hero[hero id=%d]" % id)
                return False
            hero_set.add(id)

    #不允许没有英雄在队伍中
    if len(hero_set) == 0:
        logger.warning("No hero in teams")
        return False

    return True


def _calc_relationship(heroes_id):
    """计算英雄中存在的羁绊关系
    """
    relationships_id = []

    all_relationships = data_loader.RelationshipBasicInfo_dict
    for id in all_relationships:
        if _is_relationship_active(all_relationships[id], heroes_id):
            relationships_id.append(id)

    return relationships_id


def _is_relationship_active(relationship, heroes_id):
    """判断该羁绊是否被激活
    """
    count = 0
    for hero_id in heroes_id:
        if hero_id in relationship.heroBasicIds:
            count += 1

    if count >= relationship.limitNum:
        return True
    else:
        return False


def _update_hero_buffs(data, hero, relationships_id):
    """更新有羁绊英雄的buff
    """
    #影响英雄所带兵种战力的科技
    battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
            data.technology_list.get_all(True), hero.soldier_basic_id)

    #英雄是否有羁绊
    buffs_id = _calc_hero_buffs_in_relationship(hero.basic_id, relationships_id)
    if len(buffs_id) != 0:
        #英雄有羁绊，需要重新计算战力
        hero.update_buffs(buffs_id, battle_technology_basic_id)


def _calc_hero_buffs_in_relationship(hero_id, relationships_id):
    """计算英雄在羁绊关系中的buff
    """
    buffs_id = []
    for relationship_id in relationships_id:
        relationship = data_loader.RelationshipBasicInfo_dict[relationship_id]
        if hero_id in relationship.heroBasicIds:
            buffs_id.append(relationship.buffBasicId)

    return buffs_id


