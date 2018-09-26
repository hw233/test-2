#coding:utf8
"""
Created on 2015-12-25
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 副本随机事件
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class DungeonInstance(object):
    """副本
    """

    BOSS_COUNT_MAX = 3
    BOSS_POS = [-2, -3, -1]


    def __init__(self, id):
        self._id = id
        self._level = {}
        self.final = 0


    def add_level(self, level, info):
        assert level not in self._level
        self._level[level] = info
        if level > self.final:
            self.final = level


    def get_heroes(self, level, count):
        """随机计算对应关卡的敌人英雄阵容
        不允许重复
        """
        info = self._level[level]
        heroes = [0] * count

        #设置 boss
        assert len(info.bossBasicId) <= self.BOSS_COUNT_MAX
        for i, boss_id in enumerate(info.bossBasicId):
            pos = self.BOSS_POS[i]
            heroes[pos] = boss_id

        #随机计算其余阵容
        gap = count - len(info.bossBasicId)
        if gap > 0:
            random.seed()
            choose = random.sample(info.heroBasicId, gap)
            for id in choose:
                for pos in range(0, count):
                    if heroes[pos] == 0:
                        heroes[pos] = id
                        break
        return heroes


class DungeonPool(object):
    """副本池
    """

    __metaclass__ = Singleton

    MAX_LEVEL = 6

    def __init__(self):
        self._instance = {}
        self._difficulty_lower = [0.6, 0.7, 0.75, 0.8, 0.9, 0.9]#TODO 配置
        self._difficulty_upper = [0.7, 0.8, 0.85, 0.9, 1, 1]#TODO 配置

        for key in data_loader.PVEDungeonBasicInfo_dict:
            (id, level) = key.split('_')
            id = int(id)
            level = int(level)
            assert level <= self.MAX_LEVEL
            info = data_loader.PVEDungeonBasicInfo_dict[key]

            if id not in self._instance:
                instance = DungeonInstance(id)
                instance.add_level(level, info)
                self._instance[id] = instance
            else:
                self._instance[id].add_level(level, info)

        assert len(self._instance) > 0


    def is_final_level(self, id, level):
        """判断是否是副本的最后一关
        """
        if level == self._instance[id].final:
            return True
        return False


    def get_difficulty(self, level):
        """获取难度系数
        """
        assert level > 0 and level <= self.MAX_LEVEL
        return (self._difficulty_lower[level - 1], self._difficulty_upper[level - 1])


    def get_instance(self):
        """随机选择
        """
        random.seed()
        return random.sample(self._instance.keys(), 1)[0]


    def get_heroes(self, id, level, count):
        """随机确定阵容
        """
        assert level > 0 and level <= self.MAX_LEVEL
        return self._instance[id].get_heroes(level, count)


class DungeonInfo(object):
    """副本信息
    """
    TEAM_COUNT_MAX = 3
    HEROES_PER_TEAM = 3

    def __init__(self, user_id = 0, node_id = 0, heroes_count = 0, base_score = 0,
            dungeon_id = 0, level = 0, start_time = 0, forward_time = 0, finish = False):
        self.user_id = user_id
        self.node_id = node_id
        self.heroes_count = heroes_count
        self.base_score = base_score
        self.dungeon_id = dungeon_id
        self.level = level
        self.start_time = start_time
        self.forward_time = forward_time
        self.finish = finish


    @staticmethod
    def create(user_id):
        """生成一个新的副本信息
        """
        dungeon = DungeonInfo(user_id)
        return dungeon


    def is_able_to_open(self, now):
        """副本是否能够打开
        """
        if self.is_dungeon_open():
            return False

        #和上次出现是同一天，不允许打开
        seconds_of_one_day = 86400
        if now - self.start_time <= seconds_of_one_day:
            return False
        return True


    def is_dungeon_open(self):
        """副本是否存在
        """
        return self.node_id != 0


    def open(self, node, team_count, base_score, now):
        """开启副本
        """
        if self.is_dungeon_open():
            logger.warning("Dungeon is already open")
            return False

        self.node_id = node.id

        #随机一个副本
        self.dungeon_id = self._random_dungeon_id()

        #决定一个关卡敌人阵容英雄数量
        self.heroes_count = team_count * self.HEROES_PER_TEAM

        self.base_score = base_score
        self.level = 1
        self.start_time = now
        self.forward_time = now
        self.finish = False
        return True


    def close(self):
        """关闭副本
        """
        self.node_id = 0


    def forward(self, node, team_count, now):
        """进度前进
        """
        if self.node_id != node.id:
            logger.warning("Dungeon node error[%d!=%d]" % (self.node_id, node.id))
            return False

        if self.finish:
            logger.warning("Dungeon is finished[final level=%d]" % self.level)
            return False

        self.forward_time = now
        self.heroes_count = team_count * self.HEROES_PER_TEAM

        if self.is_final_level():
            self.finish = True
        else:
            self.level += 1

        return True


    def get_level_scores(self):
        """获取当前关卡战力区间
        """
        (difficulty_lower, difficulty_upper) = DungeonPool().get_difficulty(self.level)
        return (int(difficulty_lower * self.base_score), int(difficulty_upper * self.base_score))


    def get_heroes(self):
        """获取当前关卡的英雄阵容 hero basic id
        """
        return DungeonPool().get_heroes(self.dungeon_id, self.level, self.heroes_count)


    def _random_dungeon_id(self):
        """随机生成一个副本
        """
        return DungeonPool().get_instance()


    def is_final_level(self):
        """是否最后一关
        """
        return DungeonPool().is_final_level(self.dungeon_id, self.level)


