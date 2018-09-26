#coding:utf8
"""
Created on 2017-03-11
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 扩展副本逻辑
"""

from firefly.utils.singleton import Singleton
from datalib.data_loader import data_loader
from app.data.hero import HeroInfo
from app.data.expand_dungeon import ExpandDungeonInfo
from app.data.node import NodeInfo
from app.data.rival import RivalInfo
from app.data.soldier import SoldierInfo
from proto import dungeon_pb2
from app import log_formater
from utils import logger
class DungeonPool(object):
    
    __metaclass__ = Singleton

    def __init__(self):
        self._generate = {}
        self._start_battle = {}
        self._finish_battle = {}

        #注册生成阵容方法

        #注册开始战斗方法

        #注册结束战斗方法

    def generate(self, dungeon, battle_level, user, detail_type):
        id = dungeon.basic_id
        if self._generate.has_key(id) and self._generate[id] is not None:
            return self._generate[id](dungeon, battle_level, user, detail_type)
        else:
            return _default_generate_array_detail(dungeon, battle_level, user, detail_type)
    
    def start_battle(self, data, dungeon, battle_level, now, **kw):
        id = dungeon.basic_id
        if self._start_battle.has_key(id) and self._start_battle[id] is not None:
            return self._start_battle[id](data, dungeon, battle_level, now, **kw)
        else:
            return _default_start_battle(data, dungeon, battle_level, now)

    def finsh_battle(self, data, dungeon, now, **kw):
        id = dungeon.basic_id
        if self._finish_battle.has_key(id) and self._finish_battle[id] is not None:
            return self._finish_battle[id](data, dungeon, now, **kw)
        else:
            return _default_finish_battle(data, dungeon, now, **kw)

def init_expand_dungeon(data):
    """初始化扩展副本"""
    for dungeon_id in data_loader.ExpandDungeonBasicInfo_dict.keys():
        dungeon = ExpandDungeonInfo.create(data.id, dungeon_id)
        data.expand_dungeon_list.add(dungeon)

def generate_array_detail(dungeon, battle_level, user, detail_type):
    """生成阵容"""
    return DungeonPool().generate(dungeon, battle_level, user, detail_type)

def start_battle(data, dungeon, battle_level, now, **kw):
    """开始战斗"""
    return DungeonPool().start_battle(data, dungeon, battle_level, now, **kw)

def finish_battle(data, dungeon, now, **kw):
    """结束战斗"""
    return DungeonPool().finsh_battle(data, dungeon, now, **kw)

def _default_generate_array_detail(dungeon, battle_level, user, detail_type):
    """默认生成阵容方法"""
    if battle_level == 0:
        level = dungeon.level(user.level)
    else:
        battle_id = "%d_%d" % (dungeon.basic_id, battle_level)
        level = data_loader.ExpandDungeonBattleBasicInfo_dict[battle_id].enemyLevel

    array_id = "%d_%d" % (dungeon.basic_id, level)
    if detail_type == 'enemy':
        array = data_loader.ExpandDungeonEnemyBasicInfo_dict[array_id]
    else:
        array = data_loader.ExpandDungeonOwnBasicInfo_dict[array_id]

    buffs_id = array.buffIds
    techs_id = array.techIds
    heroes = []
    for i in range(len(array.heroIds)):
        basic_id = array.heroIds[i]
        hero_level = array.heroLevels[i]
        star = array.heroStarLevels[i]
        equipments_id = array.heroEquipmentIds[i*3 : i*3 + 3]
        evolution_level = array.heroEvolutionLevels[i]
        herostars_id = array.heroHeroStars[i*6 : i*6 + 6]
        soldier_basic_id = array.soldierBasicIds[i]
        soldier_level = array.soldierLevels[i]
        soldier = SoldierInfo.create(user.id, soldier_basic_id, soldier_level)

        if basic_id == 0:
            heroes.append(None)
        else:
            hero = HeroInfo.create_special(user.id, user.level, basic_id,
                    hero_level, star, soldier, [], techs_id, equipments_id,
                    buffs_id, False, evolution_level, False, herostars_id)
            heroes.append(hero)

    return heroes


def _default_start_battle(data, dungeon, battle_level, now):
    """默认开始战斗方法"""
    user = data.user.get(True)
    status = dungeon.status(user.level, now)
    if status != dungeon.ACTIVE:
        return dungeon_pb2.DUNGEON_NOT_OPEN
    if dungeon.get_remain_num() <= 0:
        return dungeon_pb2.DUNGEON_NO_ENTER_NUM

    node_basic_id = dungeon.node_basic_id()
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    node = data.node_list.get(node_id)
    if node is None:
        node = NodeInfo.create(data.id, node_basic_id)
        data.node_list.add(node)
    
    node.set_expand_dungeon()

    user = data.user.get(True)
    rival = data.rival_list.get(node_id)
    if rival is None:
        rival = RivalInfo.create(node_id, data.id)
        data.rival_list.add(rival)

    rival.set_expand_dungeon(dungeon.basic_id, dungeon.level(user.level), battle_level)

    return dungeon_pb2.DUNGEON_OK

def _default_finish_battle(data, dungeon, now, **kw):
    """默认结束战斗方法"""
    dungeon_level = kw['dungeon_level']     #完成的副本难度
    win = kw['win']                         #是否胜利
    if not win:
        dungeon.attack()
        return dungeon_pb2.DUNGEON_OK

    key = "%d_%d" % (dungeon.basic_id, dungeon_level)
    ratio = data_loader.ExpandDungeonLevelBasicInfo_dict[key].rewardRatio
    
    #修改battle中的奖励信息
    node_basic_id = dungeon.node_basic_id()
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    battle = data.battle_list.get(node_id)

    reward_money = battle.reward_money
    reward_food = battle.reward_food
    reward_hero_exp = battle.reward_hero_exp
    reward_user_exp = battle.reward_user_exp
    item_list = battle.get_reward_items()

    reward_money *= ratio
    reward_food *= ratio

    new_item_list = []
    for item_id, item_num in item_list:
        new_item_list.append((item_id, item_num * ratio))

    battle.set_reward(reward_money, reward_food, reward_hero_exp, reward_user_exp, new_item_list)
    dungeon.attack()

    return dungeon_pb2.DUNGEON_OK

def reset_attack_count(data, dungeon, now):
    """重置攻击次数"""
    reset_num = dungeon.reset_count + 1
    if reset_num not in data_loader.ExpandDungeonRefreshBasicInfo_dict:
        return dungeon_pb2.DUNGEON_NO_RESET_NUM

    gold_cost = data_loader.ExpandDungeonRefreshBasicInfo_dict[reset_num].goldCost
    limit_vip_level = data_loader.ExpandDungeonRefreshBasicInfo_dict[reset_num].limitVipLevel

    user = data.user.get(True)
    if user.vip_level < limit_vip_level:
        return dungeon_pb2.DUNGEON_NO_RESET_NUM

    resource = data.resource.get()
    original_gold = resource.gold
    if not resource.cost_gold(gold_cost):
        return dungeon_pb2.DUNGEON_GOLD_NOT_ENOUGH
    log = log_formater.output_gold(data, -gold_cost, log_formater.RESET_DUNGENON_ATTACK,
                "reset dungeon attact accout by gold", before_gold = original_gold)
    logger.notice(log)

    dungeon.reset_attack_count(now)
    return dungeon_pb2.DUNGEON_OK

def get_dungeon_by_id(data, basic_id, readonly = False):
    id = ExpandDungeonInfo.generate_id(data.id, basic_id)
    return data.expand_dungeon_list.get(id, readonly)
