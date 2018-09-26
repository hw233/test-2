#coding:utf8
"""
Created on 2015-12-22
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 世界地图上的节点信息
"""

import math
import random
from utils import logger
from utils import utils
from utils.ret import Ret
from datalib.data_loader import data_loader


EXPLOIT_HERO_COUNT = 3
EMPTY_HEROES = "0#0#0"
NONE_HERO = 0


class NodeInfo(object):
    NODE_TYPE_OWN = 1
    NODE_TYPE_KEY = 2
    NODE_TYPE_DEPENDENCY = 3

    NODE_STATUS_ENEMY = 1
    NODE_STATUS_DOMINATE = 2
    NODE_STATUS_INVISIBLE = 3

    EXPLOITATION_TYPE_INVALID = 0
    EXPLOITATION_TYPE_MONEY = 1
    EXPLOITATION_TYPE_FOOD = 2
    EXPLOITATION_TYPE_GOLD = 3
    EXPLOITATION_TYPE_MATERIAL = 4
    EXPLOITATION_TYPE_RANDOM_ITEM = 5
    EXPLOITATION_TYPE_ENCHANT_MATERIAL = 6
    EXPLOITATION_TYPE_HERO_STAR_SOUL = 7

    ENEMY_TYPE_INVALID = 0
    ENEMY_TYPE_PVE_RESOURCE = 1
    ENEMY_TYPE_PVP_CITY = 2
    ENEMY_TYPE_PVP_RESOURCE = 3
    ENEMY_TYPE_PVE_BANDIT = 4
    ENEMY_TYPE_PVE_REBEL = 5
    ENEMY_TYPE_DUNGEON = 6 #副本
    ENEMY_TYPE_ARENA = 7 #演武场对手
    ENEMY_TYPE_LEGENDCITY = 8 #史实城对手
    ENEMY_TYPE_WORLDBOSS = 9 #世界boss
    ENEMY_TYPE_MELEE = 10    #乱斗场对手
    ENEMY_TYPE_UNIONBOSS = 11 #联盟boss
    ENEMY_TYPE_EXPAND_DUNGEON = 12 #扩展副本
    ENEMY_TYPE_PLUNDER = 13         #掠夺
    ENEMY_TYPE_PLUNDER_ENEMY = 14   #掠夺复仇/指定查询对手

    EVENT_TYPE_INVALID = 0
    EVENT_TYPE_TAX = 1
    EVENT_TYPE_FARM = 2
    EVENT_TYPE_MINING = 3
    EVENT_TYPE_GOLD = 4
    EVENT_TYPE_UPGRADE = 5
    EVENT_TYPE_DEFEND = 6
    EVENT_TYPE_QUESTION = 7
    EVENT_TYPE_VISIT = 8
    EVENT_TYPE_SPY = 9
    EVENT_TYPE_JUNGLE = 10
    EVENT_TYPE_DUNGEON = 11
    EVENT_TYPE_ARENA = 12
    EVENT_TYPE_SCOUT = 13
    EVENT_TYPE_SEARCH = 14          #搜索废墟
    EVENT_TYPE_DEEP_MINING = 15     #勘探秘矿
    EVENT_TYPE_HERMIT = 16          #探访隐士
    EVENT_TYPE_WORLDBOSS = 17       #世界boss
    EVENT_TYPE_EXPAND_DUNGEON = 18  #扩展副本

    PROTECT_TYPE_CITY = 1
    PROTECT_TYPE_RESOURCE_NODE = 2


    def __init__(self, id = 0, user_id = 0, basic_id = 0, type = 0,
            status = NODE_STATUS_INVISIBLE, level = 0, hold_time = 0,
            exploit_type = 0, exploit_level = 0,
            gather_speed = 0.0, gather_storage = 0, gather_start_time = 0,
            exploit_reserve = 0, exploit_total_time = 0, exploit_start_time = 0,
            exploit_team = EMPTY_HEROES,
            in_battle = False,
            rival_type = ENEMY_TYPE_INVALID,
            rival_score_min = 0, rival_score_max = 0, rival_id = 0,
            event_type = EVENT_TYPE_INVALID,
            event_arise_time = 0, event_launch_time = 0,
            protect_total_time = 0, protect_start_time = 0,
            increase_total_time = 0, increase_start_time = 0,
            increase_rate = 0.0):

        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id
        self.type = type

        self.status = status
        self.level = level
        self.hold_time = hold_time #占领时间点

        #资源信息
        self.exploit_type = exploit_type
        self.exploit_level = exploit_level
        self.gather_speed = gather_speed
        self.gather_storage = gather_storage
        self.gather_start_time = gather_start_time
        self.exploit_reserve = exploit_reserve #开发资源储量
        self.exploit_total_time = exploit_total_time
        self.exploit_start_time = exploit_start_time
        self.exploit_team = exploit_team

        #战斗信息
        self.in_battle = in_battle   #是否在战斗中

        #敌人匹配信息
        self.rival_type = rival_type
        self.rival_score_min = rival_score_min
        self.rival_score_max = rival_score_max
        self.rival_id = rival_id

        #随机事件
        self.event_type = event_type
        self.event_arise_time = event_arise_time
        self.event_launch_time = event_launch_time

        #保护信息
        self.protect_total_time = protect_total_time
        self.protect_start_time = protect_start_time

        #增产信息
        self.increase_total_time = increase_total_time
        self.increase_start_time = increase_start_time
        self.increase_rate = increase_rate


    @staticmethod
    def generate_id(user_id, basic_id):
        id = user_id << 32 | basic_id
        return id


    @staticmethod
    def get_basic_id(id):
        basic_id = id & 0xFFFFFFFF
        return basic_id


    @staticmethod
    def create(user_id, basic_id):
        """创建 Node 信息
        """
        id = NodeInfo.generate_id(user_id, basic_id)
        type = data_loader.MapNodeBasicInfo_dict[basic_id].type
        node = NodeInfo(id, user_id, basic_id, type)

        if node.is_own_city():
            node.status = NodeInfo.NODE_STATUS_DOMINATE

        return node


    @staticmethod
    def get_own_node_basic_id():
        return 0


    def is_own_city(self):
        """是否是我方主城
        """
        return self.type == self.NODE_TYPE_OWN


    def is_key_node(self):
        """是否是关键节点
        """
        return self.type == self.NODE_TYPE_KEY


    def is_dependency(self):
        """是否是附属点
        """
        return self.type == self.NODE_TYPE_DEPENDENCY


    def is_visible(self):
        """节点是否可见
        """
        return self.status != self.NODE_STATUS_INVISIBLE


    def is_own_side(self):
        """节点是否是我方占据
        """
        return self.status == self.NODE_STATUS_DOMINATE


    def is_enemy_side(self):
        """节点是否是敌方占据
        """
        return self.status == self.NODE_STATUS_ENEMY


    def is_event_arised(self):
        """节点上是否出现了事件
        """
        return self.event_type != self.EVENT_TYPE_INVALID


    def is_event_launched(self):
        """节点上随机事件是否启动了
        """
        return self.event_launch_time != 0


    def is_arena_event_arised(self):
        """节点上是否出现了演武场事件
        """
        return self.event_type == self.EVENT_TYPE_ARENA


    def is_worldboss_event_arised(self):
        """节点上是否出现了世界boss事件
        """
        return self.event_type == self.EVENT_TYPE_WORLDBOSS


    def is_rival_exist(self):
        """节点上是否有敌人
        """
        return self.rival_type != self.ENEMY_TYPE_INVALID


    def is_rival_pve(self):
        """节点敌人是否是 PVE
        """
        return (self.rival_type == self.ENEMY_TYPE_PVE_RESOURCE or
                self.rival_type == self.ENEMY_TYPE_PVE_BANDIT or
                self.rival_type == self.ENEMY_TYPE_PVE_REBEL)


    def is_rival_pvp(self):
        """节点敌人是否是 PVP
        """
        return (self.rival_type == self.ENEMY_TYPE_PVP_CITY or
                self.rival_type == self.ENEMY_TYPE_PVP_RESOURCE)


    def is_rival_dungeon(self):
        """节点敌人是否是 PVE 副本
        """
        return self.rival_type == self.ENEMY_TYPE_DUNGEON


    def is_rival_pvp_city(self):
        """节点敌人是否是 PVP 主城
        """
        return self.rival_type == self.ENEMY_TYPE_PVP_CITY


    def is_rival_pvp_resource(self):
        """节点敌人是否是 PVP 资源点
        """
        return self.rival_type == self.ENEMY_TYPE_PVP_RESOURCE


    def is_exploit_exist(self):
        """节点是否有资源信息
        """
        return self.exploit_type != self.EXPLOITATION_TYPE_INVALID


    def is_exploit_money(self):
        """资源类型是否是金钱
        """
        return self.exploit_type == self.EXPLOITATION_TYPE_MONEY


    def is_exploit_food(self):
        """资源类型是否是粮草
        """
        return self.exploit_type == self.EXPLOITATION_TYPE_FOOD


    def is_exploit_material(self):
        """资源类型是否是物品
        """
        return self.exploit_type == self.EXPLOITATION_TYPE_MATERIAL


    def is_exploit_gold(self):
        """资源类型是否是元宝
        """
        return self.exploit_type == self.EXPLOITATION_TYPE_GOLD


    def is_exploit_offline(self):
        """资源类型是否是离线产出相关的
        """
        return (self.exploit_type == self.EXPLOITATION_TYPE_RANDOM_ITEM
                or self.exploit_type == self.EXPLOITATION_TYPE_ENCHANT_MATERIAL
                or self.exploit_type == self.EXPLOITATION_TYPE_HERO_STAR_SOUL)


    def is_exploit_random_item(self):
        """资源类型是否随机物品
        """
        return self.exploit_type == self.EXPLOITATION_TYPE_RANDOM_ITEM


    def is_exploit_enchant_material(self):
        """资源类型是否材料
        """
        return self.exploit_type == self.EXPLOITATION_TYPE_ENCHANT_MATERIAL


    def is_exploit_hero_star_soul(self):
        """资源类型是否将魂
        """
        return self.exploit_type == self.EXPLOITATION_TYPE_HERO_STAR_SOUL


    def is_in_battle(self):
        """节点是否在战斗中
        """
        return self.in_battle


    def is_dependency_active(self):
        """附属点是否活跃
        """
        assert self.is_dependency()
        return self.is_visible()


    def is_in_protect(self, now):
        """是否处在保护中
        """
        if now < self.protect_start_time + self.protect_total_time:
            return True
        else:
            return False


    def is_in_increase(self, now):
        """是否处在增产中
        """
        if now < self.increase_start_time + self.increase_total_time:
            return True
        else:
            return False


    def get_key_node_match_info(self, user_level = 0):
        """获得关键点类型匹配信息
          (若user_level不为0，按照主公等级匹配； 否则按照节点等级匹配)
        Args:
            user_level[int]
        """
        if user_level != 0:
            level = user_level
        else:
            level = self.level
        return data_loader.KeyNodeMatchBasicInfo_dict[level]


    def get_key_node_enemy_match_info(self):
        """获得关键点敌人匹配信息
        """
        key = "%s_%s" % (self.rival_type, self.level)
        return data_loader.EnemyMatchBasicInfo_dict[key]


    def update_own_city_level(self, level):
        """更新等级
        只能对己方主城操作
        """
        assert self.is_own_city()
        self.level = level


    def upgrade_key_node(self, user, now, level_add):
        """升级关键节点
        资源等级提升
        只能对己方关键点操作
        """
        assert self.is_key_node() and self.is_own_side()

        #等级不允许高于用户等级
        next_level = self.level + level_add
        if next_level > user.level:
            logger.warning("Key node upgrade error[level limit=%d]" % user.level)
            return False

        self.level = next_level
        self.upgrade_key_node_exploitation(next_level, now)
        return True


    def lost_key_node_of_invasion(self, now):
        """关键点丢失，由于被入侵，防御失败
        我方关键点 -> 敌方关键点
        当前节点已经存在敌人信息
        资源信息、敌人信息均不变，仅仅改变控制权
        """
        assert self.is_key_node() and self.is_own_side() and self.is_rival_exist()

        self.status = self.NODE_STATUS_ENEMY
        self.hold_time = now
        self.reset_key_node_exploitation(now)
        self.clear_event()
        self.clear_in_increase()

        return True


    def clear_key_node(self):
        """
        清除关键点
        敌方/我方关键点 -> 视野外关键点
        1 清除资源信息
        2 清除敌人信息
        3 清除随机事件信息
        """
        assert self.is_key_node()

        self.clear_key_node_exploitation()
        self.clear_enemy()
        self.clear_event()
        self.clear_in_battle()
        self.clear_in_protect()
        self.clear_in_increase()

        self.status = self.NODE_STATUS_INVISIBLE
        return True


    def respawn_key_node(self, map, user, now, allow_pvp, dungeon = None):
        """
        重新生成敌方关键点
        视野外关键点 -> 敌方关键点
        1 重新生成资源信息: 资源类型、资源等级、资源开采情况
        2 重新生成敌人信息：敌人类型、敌人战力范围
        3 并不生成详细的敌人阵容信息
        """
        assert self.is_key_node() and not self.is_visible()

        self.respawn_key_node_exploitation(map, user, now)
        self.level = self.exploit_level #节点等级等于资源等级
        self.respawn_key_node_enemy(map, now, allow_pvp, dungeon)
        self.clear_event()
        self.clear_in_battle()
        self.clear_in_protect()
        self.clear_in_increase()

        self.status = self.NODE_STATUS_ENEMY
        self.hold_time = now
        return True


    def respawn_key_node_custom(self, exploit_type, exploit_level,
            rival_type, rival_score_min, rival_score_max, now):
        """
        重新生成指定的敌方关键点
        视野外关键点 -> 敌方关键点
        """
        assert self.is_key_node() and not self.is_visible()

        #指定资源信息
        self.exploit_type = exploit_type
        self.exploit_level = exploit_level
        self._calc_exploitation_reserves()
        self.reset_key_node_exploitation(now)

        self.level = self.exploit_level #节点等级等于资源等级

        #指定敌人信息
        self.rival_type = rival_type
        self.rival_score_min = rival_score_min
        self.rival_score_max = rival_score_max
        self.clear_enemy_detail()

        self.clear_event()
        self.clear_in_battle()
        self.clear_in_protect()
        self.clear_in_increase()

        self.status = self.NODE_STATUS_ENEMY
        self.hold_time = now
        return True


    def dominate_key_node(self, map, now):
        """
        占领关键节点
        敌方占据关键点 -> 我方占据关键点
        1 不重新生成资源信息
        2 敌人信息消失
        """
        assert self.is_key_node() and self.is_enemy_side()

        self.status = self.NODE_STATUS_DOMINATE
        self.hold_time = now
        self.reset_key_node_exploitation(now)
        self.clear_enemy()
        self.clear_event()
        self.clear_in_battle()
        self.clear_in_protect()
        self.clear_in_increase()

        return True


    def is_able_to_rematch(self, now, force = False):
        """
        是否可以重新匹配节点信息
        1 只针对 pvp 敌人占据的关键点
        2 需要敌人占据节点超过一定时间
        3 节点上不存在随机事件
        """
        if not self.is_key_node():
            logger.warning("Invalid node to rematch enemy[type=%d]" % self.type)
            return False

        if not self.is_enemy_side():
            logger.warning("Invalid node to rematch enemy[status=%d]" % self.status)
            return False

        if not self.is_rival_pvp():
            logger.warning("Invalid node to rematch enemy[rival type=%d]" % self.rival_type)
            return False

        if self.is_event_arised():
            logger.warning("Invalid node to rematch enemy[event type=%d]" % self.event_type)
            return False

        if force:
            return True

        gap = float(data_loader.MapConfInfo_dict["manual_refresh_gap"].value)
        if now - self.hold_time < gap:
            logger.warning("Invalid rematch gap[hold time=%d][now=%d][need gap=%d]" %
                    (self.hold_time, now, gap))
            return False

        return True


    def rematch_key_node(self, map, user, now):
        """
        重新匹配 key node
        1 重新生成资源信息
        2 （不改变敌人类型）重新生成敌人信息
        """
        assert self.is_key_node()
        assert self.is_enemy_side()
        logger.debug("rematch node[basic id=%d]" % self.basic_id)

        self.clear_key_node_exploitation()
        self.respawn_key_node_exploitation(map, user, now)
        self.level = self.exploit_level #节点等级等于资源等级
        #仅仅重置敌人阵容，不重新计算敌人类型和战力范围
        self.clear_enemy_detail()

        self.hold_time = now
        return True


    def is_able_to_abandon(self, now):
        """
        是否可以丢弃节点信息
        1 只针对我方占据的关键点
        2 节点上不存在随机事件
        """
        if not self.is_key_node():
            logger.warning("Invalid node to abandon[type=%d]" % self.type)
            return False

        if not self.is_own_side():
            logger.warning("Invalid node to abandon[status=%d]" % self.status)
            return False

        if self.is_event_arised():
            logger.warning("Invalid node to abandon[event type=%d]" % self.event_type)
            return False

        return True


    def abandon_key_node(self, map, user, now):
        """
        丢弃key node，重新匹配敌方 key node
        1 重新生成资源信息
        2 （不改变敌人类型）重新生成敌人信息
        """
        assert self.is_key_node()
        assert self.is_own_side()
        logger.debug("abandon node[basic id=%d]" % self.basic_id)

        self.clear_key_node_exploitation()
        self.respawn_key_node_exploitation(map, user, now)
        self.level = self.exploit_level #节点等级等于资源等级
        #仅仅重置敌人阵容，不重新计算敌人类型和战力范围
        self.clear_enemy_detail()

        self.hold_time = now
        return True



    def reset_dependency(self, map):
        """
        重置附属点，使附属点不活跃
        活跃附属点 -> 不活跃附属点（不可见）
        """
        logger.debug("reset dependency[basic id=%d]" % self.basic_id)

        #assert self.is_dependency_active()

        #清除附属点的资源信息和敌人信息
        self.status = self.NODE_STATUS_INVISIBLE
        self.exploit_type = self.EXPLOITATION_TYPE_INVALID
        self.clear_enemy()
        self.clear_event()
        self.clear_in_battle()


    def respawn_dependency_with_enemy(self, map, key_node, user, now):
        """
        生成新的 PVE 附属点: 敌人类型、战力范围（并不生成详细的敌人阵容信息）
        不活跃附属点 -> 活跃的附属点
        """
        assert not self.is_dependency_active()

        logger.debug("respawn dependency with pve[basic id=%d]" % self.basic_id)

        self.level = key_node.level
        self.status = self.NODE_STATUS_ENEMY
        self.exploit_type = self.EXPLOITATION_TYPE_INVALID
        self.hold_time = now
        self.clear_event()

        #生成敌人信息
        random.seed()
        if random.random() < 0.5:
            self.rival_type = self.ENEMY_TYPE_PVE_BANDIT
        else:
            self.rival_type = self.ENEMY_TYPE_PVE_REBEL
        match_info = key_node.get_key_node_match_info(max(1, user.level - 3))
        self.rival_score_min = match_info.dependencyEnemyScoreMin
        self.rival_score_max = match_info.dependencyEnemyScoreMax
        self.clear_enemy_detail()


    def respawn_dependency_with_gold(self, map, key_node, now):
        """
        生成新的金矿附属点: 资源类型、资源等级
        不活跃附属点 -> 活跃的附属点
        """
        assert not self.is_dependency_active()

        logger.debug("respawn dependency with gold[basic id=%d]" % self.basic_id)

        self.level = key_node.level
        self.status = self.NODE_STATUS_DOMINATE
        self.rival_type = self.ENEMY_TYPE_INVALID
        self.hold_time = now
        self.clear_event()

        #生成资源信息
        self.exploit_type = self.EXPLOITATION_TYPE_GOLD
        self.exploit_level = self.level
        self._calc_exploitation_reserves()
        self.reset_key_node_exploitation(now)


    def respawn_dependency_with_worldboss(self, map, key_node, user, now):
        """
        生成新的世界boss
        不活跃附属点 -> 活跃的附属点
        """
        assert not self.is_dependency_active()

        logger.debug("respawn dependency with worldboss[basic id=%d]" % self.basic_id)

        self.level = key_node.level
        self.status = self.NODE_STATUS_ENEMY
        self.exploit_type = self.EXPLOITATION_TYPE_INVALID
        self.hold_time = now
        self.clear_event()


    def is_able_to_gather(self, now):
        """是否可以进行采集
        """
        #己方关键点
        if not self.is_key_node() and not self.is_own_side():
            logger.warning("Not able to gather[reason=status]")
            return False

        #没有出现随机事件
        if self.is_event_arised():
            logger.warning("Not able to gather[reason=event]")
            return False

        #资源类型合法
        if (not self.is_exploit_money() and
                not self.is_exploit_food() and
                not self.is_exploit_material()):
            logger.warning("Not able to gather[reason=exploit type:%d, basic_id:%d]" 
                    % (self.exploit_type, self.basic_id))
            return False

        #采集间隔满足要求
        need_gap = int(float(data_loader.MapConfInfo_dict["gather_gap"].value))
        if now < self.gather_start_time + need_gap:
            logger.warning("Not able to gather[reason=gap]")
            return False

        return True


    def gather(self, now):
        """采集，获取采集收益
        Returns:
            (money, food, item_count)
        """

        gather_speed = self.gather_speed
        if self.is_in_increase(now):
            gather_speed = gather_speed * self.increase_rate

        seconds = now - self.gather_start_time
        seconds_per_hour = 3600.0
        gain = int(gather_speed * seconds / seconds_per_hour)
        gain = min(self.gather_storage, gain)

        self.gather_start_time = now
        logger.debug("Gather[gain=%d]" % gain)

        money = 0
        food = 0
        item_count = 0

        if self.is_exploit_money():
            money = gain
        elif self.is_exploit_food():
            food = gain
        elif self.is_exploit_material():
            item_count = gain

        return (money, food, item_count)


    def is_able_to_exploit(self):
        """是否可以进行开发
        """
        #资源类型合法
        return self.is_exploit_exist()


    def is_exploit_over(self, end_time):
        """获取开发是否结束
        """
        return end_time >= self.exploit_start_time + self.exploit_total_time


    def is_able_to_finish_exploit(self, end_time, force = False, ret = Ret()):
        """是否可以结束开采
        """
        if self.exploit_type == self.EXPLOITATION_TYPE_INVALID:
            logger.debug("Not able to finish exploit[reason=exploit type]")
            return False

        if self.exploit_start_time == 0:
            logger.debug("Not able to finish exploit[reason=not during exploiting]")
            return False

        if force:
            return True

        if not self.is_exploit_over(end_time):
            logger.debug("Not able to finish exploit[reason=time]")
            ret.setup("CANNT_FINISH")
            return False

        return True


    def start_exploit(self, heroes, now, consume_time = 0, exploit_reserve = 0, offline = False):
        """开始资源开发
        1 派驻英雄
        2 开始计时，更新实际可开采量,进行开发工作
        """
        if not self._set_exploit_hero(heroes):
            return False

        self.exploit_start_time = now
        if not offline:
            self.exploit_total_time = consume_time
            self.exploit_reserve = exploit_reserve
        return True


    def finish_exploit(self, heroes, offline = False):
        """结束资源开发
        """
        if not self._clear_exploit_hero(heroes):
            return False

        self.exploit_start_time = 0
        if not offline:
            self._calc_exploitation_reserves() #恢复初始的产量和耗时
        return True


    def set_exploit_total_time(self, time):
        """修改开采总时间
        """
        self.exploit_total_time = time


    def set_exploit_level(self, level):
        """修改开采的level
        """
        self.exploit_level = level


    def get_exploit_hero(self):
        """获取参与开发的英雄
        """
        ids = utils.split_to_int(self.exploit_team)
        return ids


    def _set_exploit_hero(self, heroes):
        """派驻英雄进行开发
        """
        assert len(heroes) == EXPLOIT_HERO_COUNT

        if self.exploit_team != EMPTY_HEROES:
            logger.warning("Node has exploit heroes")
            return False

        heroes_id = []
        for hero in heroes:
            if hero is None:
                heroes_id.append(NONE_HERO)
            else:
                heroes_id.append(hero.id)

        self.exploit_team = utils.join_to_string(heroes_id)
        return True


    def _clear_exploit_hero(self, heroes):
        """清除参与开发的英雄
        """
        assert len(heroes) == EXPLOIT_HERO_COUNT

        heroes_id = utils.split_to_int(self.exploit_team)

        for hero in heroes:
            if hero is None:
                continue

            if hero.id not in heroes_id:
                logger.warning("Hero not match exploitation"
                        "[hero id=%d][node exploit heroes=%s]" %
                        (hero.id, node.exploit_team))
                return False

            index = heroes_id.index(hero.id)
            heroes_id[index] = NONE_HERO

        self.exploit_team = utils.join_to_string(heroes_id)

        if self.exploit_team != EMPTY_HEROES:
            logger.warning("Exploit heroes not clear")
            return False

        return True


    def get_exploit_progress(self, end_time):
        """获取开发进度 [0-1]
        """
        ratio = (end_time - self.exploit_start_time) / self.exploit_total_time
        ratio = max(0.0, ratio)
        ratio = min(1.0, ratio)
        return ratio


    def calc_exploit_income(self, end_time):
        """
        计算资源开发收益
        Returns:
            (采集获得的金钱、粮草、元宝、物品个数)
        """
        money = 0
        food = 0
        gold = 0
        item_count = 0

        #按照进度，获取收益
        ratio = self.get_exploit_progress(end_time)
        gain = int(ratio * self.exploit_reserve)

        if self.is_exploit_money():
            money = gain
        elif self.is_exploit_food():
            food = gain
        elif self.is_exploit_gold():
            gold = gain
        elif self.is_exploit_material():
            item_count = gain

        return (money, food, gold, item_count)


    def calc_grab_income(self):
        """计算战胜后抢夺到的资源
        Returns:
            (掠夺到的金钱、粮草、物品个数)
        """
        money = 0
        food = 0
        item_count = 0

        #如果是我方节点，无法获得资源奖励
        if self.is_own_side():
            return (money, food, item_count)

        #可以抢夺部分资源
        grab_ratio_min = float(data_loader.MapConfInfo_dict["grab_ratio_min"].value)
        grab_ratio_max = float(data_loader.MapConfInfo_dict["grab_ratio_max"].value)
        random.seed()
        grab_ratio = random.uniform(grab_ratio_min, grab_ratio_max)

        gain = int(self.exploit_reserve * grab_ratio)

        if self.is_exploit_money():
            money = gain
        elif self.is_exploit_food():
            food = gain
        elif self.is_exploit_material():
            item_count = gain

        logger.debug("Grab income[money=%d][food=%d][item count=%d]" %
                (money, food, item_count))
        return (money, food, item_count)


    def calc_jungle_income(self):
        """计算野怪战胜后的资源奖励
        Returns:
            (奖励的金钱、粮草)
        """
        base_money = data_loader.MoneyExploitationBasicInfo_dict[self.level].reserves
        base_food = data_loader.FoodExploitationBasicInfo_dict[self.level].reserves

        ratio_mu = float(data_loader.MapConfInfo_dict["jungle_income_ratio_mu"].value)
        ratio_sigma = float(data_loader.MapConfInfo_dict["jungle_income_ratio_sigma"].value)
        ratio_min = float(data_loader.MapConfInfo_dict["jungle_income_ratio_min"].value)
        ratio_max = float(data_loader.MapConfInfo_dict["jungle_income_ratio_max"].value)

        random.seed()
        ratio_money = random.gauss(ratio_mu, ratio_sigma)
        ratio_money = max(ratio_money, ratio_min)
        ratio_money = min(ratio_money, ratio_max)
        ratio_food = random.gauss(ratio_mu, ratio_sigma)
        ratio_food = max(ratio_food, ratio_min)
        ratio_food = min(ratio_food, ratio_max)

        money = int(base_money * ratio_money)
        food = int(base_food * ratio_food)
        return (money, food)


    def is_event_over_idletime(self, now, overtime = False):
        """随机事件是否超过了 idletime
        Args:
            now[int]: 现在时间戳
            overtime[bool]: 是否允许超时
        """
        #assert self.is_event_arised() and not self.is_event_launched()
        if not self.is_event_arised():
            return True

        if overtime:#允许超时
            return False

        idletime = data_loader.LuckyEventBasicInfo_dict[self.event_type].idletime
        if idletime == 0 or now <= idletime + self.event_arise_time:
            return False
        return True


    def is_event_over_lifetime(self, now, overtime = False):
        """随机事件是否超过了 lifetime
        Args:
            now[int]: 现在时间戳
            overtime[bool]: 是否允许超时
        """
        assert self.is_event_arised() and self.is_event_launched()
        if overtime:#允许超时
            return False

        lifetime = data_loader.LuckyEventBasicInfo_dict[self.event_type].lifetime
        if lifetime == 0 or now <= lifetime + self.event_launch_time:
            return False
        return True


    def arise_event(self, event_type, event_arise_time):
        """节点上出现了随机事件
        """
        assert not self.is_event_arised()
        logger.debug("arise event[type=%d]" % event_type)

        if event_type == self.EVENT_TYPE_INVALID:
            logger.warning("Invalid event type[type=%d]" % event_type)
            return False
        elif event_type == self.EVENT_TYPE_SCOUT:
            self.status = self.NODE_STATUS_ENEMY
        else:
            if (event_type == self.EVENT_TYPE_ARENA
                    or event_type == self.EVENT_TYPE_DUNGEON
                    or event_type == self.EVENT_TYPE_WORLDBOSS):
                self.status = self.NODE_STATUS_ENEMY
            elif event_type == self.EVENT_TYPE_SEARCH:
                self.status = self.NODE_STATUS_ENEMY
                self.exploit_type = self.EXPLOITATION_TYPE_RANDOM_ITEM
            elif event_type == self.EVENT_TYPE_DEEP_MINING:
                self.status = self.NODE_STATUS_ENEMY
                self.exploit_type = self.EXPLOITATION_TYPE_ENCHANT_MATERIAL
            elif event_type == self.EVENT_TYPE_HERMIT:
                self.status = self.NODE_STATUS_ENEMY
                self.exploit_type = self.EXPLOITATION_TYPE_HERO_STAR_SOUL

            self.event_type = event_type
            self.event_arise_time = event_arise_time
            self.event_launch_time = 0

        return True


    def launch_event(self, now, overtime = False):
        """启动随机事件
        Args:
            now[int]: 现在时间戳
            overtime[bool]: 是否允许超时
        """
        if self.is_event_over_idletime(now, overtime):
            logger.warning("Not able to launch event[reason=over idletime]")
            return False
        self.event_launch_time = now

        return True


    def finish_event(self, now, overtime = False):
        """结束随机事件
        Args:
            now[int]: 现在时间戳
            overtime[bool]: 是否允许超时
        """
        if self.is_event_over_lifetime(now, overtime):
            logger.warning("Not able to finish event[reason=over lifetime]")
            return False

        return self.clear_event()


    def clear_event(self):
        """清除随机事件
        """
        logger.debug("clear event[type=%d]" % self.event_type)
        self.event_type = self.EVENT_TYPE_INVALID
        self.event_arise_time = 0
        self.event_launch_time = 0
        return True


    def respawn_key_node_exploitation(self, map, user, now):
        """
        重新生成关键点的资源信息: 类型、等级、采集信息、开发信息
        """
        assert not self.is_exploit_exist()

        self._calc_key_node_exploitation_type(map)
        self._calc_key_exploitation_level(map, user)
        self._calc_exploitation_reserves()
        self.reset_key_node_exploitation(now)


    def _calc_key_node_exploitation_type(self, map):
        """计算关键节点资源类型
        根据所有可见的关键点计算
        """
        money_type_weight = 100.0
        food_type_weight = 100.0
        material_type_weight = 100.0

        if map.total_key_exploit_money_weight > 0:
            money_type_weight = 100.0 / map.total_key_exploit_money_weight
        if map.total_key_exploit_food_weight > 0:
            food_type_weight = 100.0 / map.total_key_exploit_food_weight
        if map.total_key_exploit_material_weight > 0:
            material_type_weight = 100.0 / map.total_key_exploit_material_weight

        flags = self.get_flags()
        #判断是否需要触发矿点
        if 'is_trigger_material_node' not in flags:
            material_type_weight = 0

        weight = money_type_weight + food_type_weight + material_type_weight

        random.seed()
        r = random.uniform(0.0, weight)
        if r <= money_type_weight:
            self.exploit_type = self.EXPLOITATION_TYPE_MONEY
        elif r <= money_type_weight + food_type_weight:
            self.exploit_type = self.EXPLOITATION_TYPE_FOOD
        else:
            self.exploit_type = self.EXPLOITATION_TYPE_MATERIAL
        logger.debug("calc exploit type[type=%d]" % self.exploit_type)


    def _calc_key_exploitation_level(self, map, user):
        """计算资源等级
        根据所有可见的关键点计算
        """
        #level_radix = float(data_loader.MapConfInfo_dict["resource_level_radix"].value)
        #level_power = float(data_loader.MapConfInfo_dict["resource_level_power"].value)
        #level_power2 = float(data_loader.MapConfInfo_dict["resource_level_power2"].value)

        #level_weight = data_loader.KeyNodeMatchBasicInfoOfMonarch_dict[user.level].levelWeight
        #level_base = data_loader.KeyNodeMatchBasicInfoOfMonarch_dict[user.level].levelBase
        #total_type_weight = (map.total_key_exploit_money_weight +
        #        map.total_key_exploit_food_weight +
        #        map.total_key_exploit_material_weight)#所有可见的关键点

        #level = int(level_base * level_radix * math.pow(
        #            total_type_weight / level_weight, level_power))
        #level2 = int(level_base * level_radix * math.pow(
        #            total_type_weight / level_weight, level_power2))
        #self.exploit_level = max(1, level, level2)
        #self.exploit_level = min(70, self.exploit_level)  #临时代码，to fix

        self.exploit_level = user.level
        logger.debug("calc exploit level[level=%d]" % self.exploit_level)


    def _calc_exploitation_reserves(self):
        """
        计算资源采集情况：产出速度
        计算资源开采情况：总量、总时间
        """
        if self.is_exploit_money():
            self.gather_speed = data_loader.MoneyExploitationBasicInfo_dict[
                    self.exploit_level].gatherSpeed
            self.gather_storage = data_loader.MoneyExploitationBasicInfo_dict[
                    self.exploit_level].gatherStorage
            self.exploit_total_time = data_loader.MoneyExploitationBasicInfo_dict[
                    self.exploit_level].time
            self.exploit_reserve = data_loader.MoneyExploitationBasicInfo_dict[
                    self.exploit_level].reserves

        elif self.is_exploit_food():
            self.gather_speed = data_loader.FoodExploitationBasicInfo_dict[
                    self.exploit_level].gatherSpeed
            self.gather_storage = data_loader.FoodExploitationBasicInfo_dict[
                    self.exploit_level].gatherStorage
            self.exploit_total_time = data_loader.FoodExploitationBasicInfo_dict[
                    self.exploit_level].time
            self.exploit_reserve = data_loader.FoodExploitationBasicInfo_dict[
                    self.exploit_level].reserves

        elif self.is_exploit_gold():
            self.exploit_total_time = data_loader.GoldExploitationBasicInfo_dict[
                    self.exploit_level].time
            self.exploit_reserve = data_loader.GoldExploitationBasicInfo_dict[
                    self.exploit_level].reserves

        elif self.is_exploit_material():
            self.gather_speed = data_loader.MaterialExploitationBasicInfo_dict[
                    self.exploit_level].gatherSpeed
            self.gather_storage = data_loader.MaterialExploitationBasicInfo_dict[
                    self.exploit_level].gatherStorage

            exploit_info = data_loader.MaterialExploitationBasicInfo_dict[self.exploit_level]
            self.exploit_total_time = exploit_info.time
            random.seed()
            num = int(math.floor(random.gauss(exploit_info.numMu, exploit_info.numSigma)))
            logger.debug("exploit material num[%f,%f][num=%d]" %
                    (exploit_info.numMu, exploit_info.numSigma, num))
            num = max(exploit_info.numMin, num)
            num = min(exploit_info.numMax, num)
            self.exploit_reserve = num

        logger.debug("calc exploit reserves[total_time=%d][total_resource=%d]" %
                (self.exploit_total_time, self.exploit_reserve))


    def upgrade_key_node_exploitation(self, next_level, now):
        """升级关键节点的资源等级
        """
        assert self.is_exploit_exist()

        #不改变资源类型
        self.exploit_level = next_level
        self._calc_exploitation_reserves()
        self.reset_key_node_exploitation(now)


    def reset_key_node_exploitation(self, now):
        """重置关键节点的资源信息
        """
        self.exploit_start_time = 0
        self.gather_start_time = now


    def clear_key_node_exploitation(self):
        """清除关键节点资源信息
        """
        assert self.is_exploit_exist()
        self.exploit_type = self.EXPLOITATION_TYPE_INVALID


    def respawn_key_node_enemy(self, map, now, allow_pvp, dungeon = None):
        """
        重新生成关键点的敌人信息
        1 计算敌人类型
        2 计算敌人战力范围
        """
        if dungeon is not None:
            self.rival_type = self.ENEMY_TYPE_DUNGEON
        else:
            self._calc_key_node_enemy_type(map, now, allow_pvp)

        self._calc_key_node_enemy_score(dungeon)

        self.clear_enemy_detail()


    def _calc_key_node_enemy_type(self, map, now, allow_pvp):
        """
        计算关键点敌人类型
        根据所有可见的关键点计算
        """
        #如果不允许 PVP
        if not allow_pvp:
            self.rival_type = self.ENEMY_TYPE_PVE_RESOURCE
            return

        #如果允许 PVP，按照权重随机选择
        pve_resource_type_weight = 100.0
        pvp_city_type_weight = 100.0
        pvp_resource_type_weight = 100.0

        if map.total_key_enemy_pve_weight > 0:
            pve_resource_type_weight = 100.0 / map.total_key_enemy_pve_weight
        if map.total_key_enemy_pvp_city_weight > 0:
            pvp_city_type_weight = 100.0 / map.total_key_enemy_pvp_city_weight * 2 #提高出pvp主城的概率
        if map.total_key_enemy_pvp_resource_weight > 0:
            pvp_resource_type_weight = 100.0 / map.total_key_enemy_pvp_resource_weight

        weight = pve_resource_type_weight + pvp_city_type_weight + pvp_resource_type_weight

        random.seed()
        r = random.uniform(0.0, weight)
        if r < pve_resource_type_weight:
            self.rival_type = self.ENEMY_TYPE_PVE_RESOURCE
        elif r < pve_resource_type_weight + pvp_city_type_weight:
            self.rival_type = self.ENEMY_TYPE_PVP_CITY
        else:
            self.rival_type = self.ENEMY_TYPE_PVP_RESOURCE


    def _calc_key_node_enemy_score(self, dungeon = None):
        """
        计算关键点敌人的战力范围
        根据当前关键点等级匹配
        """
        if dungeon is not None:
            (score_min, score_max) = dungeon.get_level_scores()
            self.rival_score_min = score_min
            self.rival_score_max = score_max
        else:
            match_info = self.get_key_node_match_info()
            self.rival_score_min = match_info.enemyScoreMin
            self.rival_score_max = match_info.enemyScoreMax


    def is_lack_enemy_detail(self):
        """是否缺少敌人阵容信息
        生成敌人信息，需要两步：
        1 生成敌人类型和战力区间
        2 生成敌人阵容
        当只完成了第一阶段，还没有完成第二阶段时，返回 True
        否则返回 False
        """
        if self.rival_type == self.ENEMY_TYPE_INVALID:
            return False
        if self.rival_id == 0:
            return True
        return False


    def is_enemy_complete(self):
        """敌人信息是否完整
        """
        return self.rival_type != self.ENEMY_TYPE_INVALID and self.rival_id != 0


    def set_enemy_detail(self, rival_id):
        """设置敌人信息
        """
        self.rival_id = rival_id


    def clear_enemy(self):
        """清除敌人信息
        """
        self.rival_type = self.ENEMY_TYPE_INVALID
        self.rival_id = 0


    def clear_enemy_detail(self):
        """清除敌人阵容信息
        """
        self.rival_id = 0


    def set_in_battle(self):
        logger.debug("set in battle[id=%d][basic_id=%d]" % (self.id, self.basic_id))
        self.in_battle = True


    def clear_in_battle(self):
        logger.debug("clear in battle[id=%d][basic_id=%d]" % (self.id, self.basic_id))
        self.in_battle = False


    def is_able_to_battle_in_protect(self):
        """是否可以在开保护的状态下战斗
        """
        if self.is_enemy_side():
            if (self.rival_type == self.ENEMY_TYPE_PVE_RESOURCE
                    or self.rival_type == self.ENEMY_TYPE_PVP_CITY
                    or self.rival_type == self.ENEMY_TYPE_PVP_RESOURCE)\
                and (self.event_type != self.EVENT_TYPE_ARENA):
                return False
            else:
                return True
        else:
            return True

    
    def protect(self, now, duration):
        self.protect_start_time = now
        self.protect_total_time = duration


    def clear_in_protect(self):
        logger.debug("clear in protect[id=%d][basic_id=%d]" % (self.id, self.basic_id))
        self.protect_start_time = 0
        self.protect_total_time = 0

    
    def increase(self, rate, now, duration):
        self.increase_rate = rate
        self.increase_start_time = now
        self.increase_total_time = duration


    def clear_in_increase(self):
        logger.debug("clear in increase[id=%d][basic_id=%d]" % (self.id, self.basic_id))
        self.increase_rate = 0.0
        self.increase_start_time = 0
        self.increase_total_time = 0

    def set_expand_dungeon(self):
        self.event_type = self.EVENT_TYPE_EXPAND_DUNGEON

    def set_arena(self):
        self.event_type = self.EVENT_TYPE_ARENA

    def set_melee(self):
        self.event_type = self.EVENT_TYPE_ARENA

    def set_world_boss(self):
        self.event_type = self.EVENT_TYPE_WORLDBOSS


    def get_flags(self):
        open_flags = set()
        for key, value in data_loader.Flag_dict.items():
            if int(float(value.value)) == 1:
                open_flags.add(str(key))

        return open_flags


