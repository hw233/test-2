#coding:utf8
"""
Created on 2015-10-24
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : PVE rival 匹配逻辑
         包括 pve 野怪、pve 副本
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.hero import HeroInfo
from app.data.soldier import SoldierInfo


class PVEEnemyPool(object):
    """PVE 敌人池
    """
    __metaclass__ = Singleton

    def __init__(self):
        self._rivals = {}
        for id in data_loader.PVEEnemyBasicInfo_dict:
            enemy = data_loader.PVEEnemyBasicInfo_dict[id]
            if enemy.score not in self._rivals:
                self._rivals[enemy.score] = [enemy]
            else:
                self._rivals[enemy.score].append(enemy)


    def get_by_id(self, id):
        return data_loader.PVEEnemyBasicInfo_dict[id]


    def get(self, score_min, score_max):
        random.seed()
        score = random.randint(score_min, score_max)
        if score in self._rivals:
            return random.choice(self._rivals[score])
        else:
            #for score in range(score_min, score_max):
            #    if score in self._rivals:
            #        return random.choice(self._rivals[score])
            #为避免总是从第一个开始随机，先从score往后寻找
            for score_tmp in range(score, score_max):
                if score_tmp in self._rivals:
                    return random.choice(self._rivals[score_tmp])
            #再从score往前寻找
            for score_tmp in range(score_min, score)[::-1]:
                if score_tmp in self._rivals:
                    return random.choice(self._rivals[score_tmp])

            logger.warning("Get pve enemy error[score=%d]" % score)
            return self._random_one()


    def _random_one(self):
        """随机返回
        """
        assert len(self._rivals) > 0

        for key in self._rivals:
            return self._rivals[key][0]


class HeroStat(object):

    def __init__(self, basic_id):
        self.basic_id = basic_id
        self.att = []
        self.level_min = 1
        self.level_max = int(float(
            data_loader.OtherBasicInfo_dict["MaxMonarchLevel"].value))
        self.star_min = 1
        self.star_max = data_loader.HeroBasicInfo_dict[basic_id].maxStarLevel

        #init 二维数组
        for star in range(0, self.star_max):
            self.att.append([0] * self.level_max)


    def get_range(self, star, level):
        return self.att[star-1][level-1]


    def _set_range(self, star, level, score_min, score_max):
        self.att[star-1][level-1] = (score_min, score_max)


    def add_record(self, info):
        self._set_range(info.star, info.level, info.scoreMin, info.scoreMax)


    def show(self):
        logger.debug("hero stat[basic id=%d]" % self.basic_id)
        for star in range(self.star_min, self.star_max+1):
            for level in range(self.level_min, self.level_max+1):
                (score_min, score_max) = self.get_range(star, level)
                logger.debug("[star=%d][level=%d][%d-%d]" %
                        (star, level, score_min, score_max))


class DungeonEnemyPool(object):
    """副本敌人池
    """
    __metaclass__ = Singleton

    def __init__(self):
        self._stat = {}

        for key in data_loader.DungeonEnemyStat_dict:
            (basic_id, level, star) = map(int, key.split('_'))
            if basic_id not in self._stat:
                stat = HeroStat(basic_id)
                self._stat[basic_id] = stat

            info = data_loader.DungeonEnemyStat_dict[key]
            self._stat[basic_id].add_record(info)

        logger.debug("[dungeon enemy stat count=%d]" % len(self._stat))


    def get(self, score, user_level, heroes_basic_id):
        """实时计算阵容
        Args:
            score[int]: 目标阵容评分
            user_level[int]: 玩家等级
            heroes_basic_id[list(hero_basic_id)]: 英雄 basic id 列表
        """
        count = len(heroes_basic_id)
        average_score = float(score) / count

        logger.debug("calc dungeon enemy[count=%d][average score=%f]" %
                (count, average_score))
        logger.debug("candidate heroes[%s]" % utils.join_to_string(heroes_basic_id))

        heroes = []
        for basic_id in heroes_basic_id:
            heroes.append(self._get_one(basic_id, average_score, user_level))

        return heroes


    def _get_one(self, basic_id, score, base_level):
        """实时计算英雄的属性，以满足 score 需求
        """
        logger.debug("calc dungeon hero[basic id=%d][expect score=%f]" % (basic_id, score))
        #确定等级和星级
        (star, level) = self._calc_base(basic_id, score, base_level)
        logger.debug("choose[star=%d][level=%d]" % (star, level))

        #模拟创建一个 hero
        hero = self._mock_hero(basic_id, star, level)

        #划分 soldier skill equipment 各个部分的目标分数
        key = "%d_%d_%d" % (basic_id, level, star)
        info = data_loader.DungeonEnemyStat_dict[key]

        score_gap = score - info.scoreMin

        score_soldier_range = info.soldierScoreMax - info.soldierScoreMin
        score_skill_range = info.skillScoreMax - info.skillScoreMin
        score_equipment_range = info.equipmentScoreMax - info.equipmentScoreMin

        score_soldier = random.uniform(0.0, min(score_soldier_range, score_gap))
        score_gap -= score_soldier
        score_skill = random.uniform(0.0, min(score_skill_range, score_gap))
        score_gap -= score_skill
        score_equipment = score_gap

        self._calc_soldier(hero, score_soldier)
        self._calc_skill(hero, score_skill)
        self._calc_equipment(hero, score_equipment)
        logger.debug("get dungeon hero[basic id=%d][expect score=%f][finnal score=%d]" %
                (basic_id, score, hero.battle_score))
        return hero


    def _calc_base(self, basic_id, score, base_level):
        """"
        计算英雄的等级和星级
        1 在此等级和星级，英雄的战力评分区间包含 score（目标战力）
        2 在次等级和星级，英雄的战力评分区间中值尽量和 score 接近
        3 需要提供一定的多样性
        这是一个启发式的算法
        拥有的数据是：对应的英雄，在不同的 star 和 level 的情况下的战力的范围
        算法就是在 star, level 两个维度上进行探索
        达到目标后停止，返回满足要求的 star 和 level
        """
        random.seed()
        data = self._stat[basic_id]
        # data.show()

        #选择一个基准等级和基准星级
        star = random.randint(data.star_min, data.star_max)
        level = random.randint(data.level_min, base_level)
        logger.debug("[base star=%d][base level=%d][target score=%d]" % (star, level, score))

        #在 star 和 level 两个维度上移动的概率
        bratio_star = data.star_max - data.star_min + 1
        bratio_level = data.level_max - data.level_min + 1
        # logger.debug("[star bratio=%d][level bratio=%d]" % (bratio_star, bratio_level))

        #score 误差容忍范围，百分比
        SCORE_TOR = 0.1

        #停止搜索的条件: 次数
        MAX_COUNT = 300
        MAX_MATCH_COUNT = 3
        loop_count = 0
        match_count = 0

        S_UP = 0
        S_DOWN = 1
        L_UP = 2
        L_DOWN = 3
        while True:
            if loop_count > MAX_COUNT:
                logger.warning("Match over max count[star=%d][level=%d]" % (star, level))
                return (star, level)

            loop_count += 1

            (lower, upper) = data.get_range(star, level)
            logger.debug("[try star=%d][try level=%d][%d-%d]" % (star, level, lower, upper))
            candidate = [0] * 4

            if score < lower:
                #区间段分数偏高
                if star > data.star_min:
                    candidate[S_DOWN] = bratio_star
                if level > data.level_min:
                    candidate[L_DOWN] = bratio_level

            elif score > upper:
                #区间段分数偏低
                if star < data.star_max:
                    candidate[S_UP] = bratio_star
                if level < data.level_max:
                    candidate[L_UP] = bratio_level

            else:
                #分数段匹配
                #如果在匹配的分数段中前进的次数达到上限，算法中止
                match_count += 1
                if match_count >= MAX_MATCH_COUNT:
                    return (star, level)

                average = (lower + upper) / 2.0
                gap = upper - lower
                #如果与分数段中值的差小于阈值，算法结束
                if abs(average - score) <= SCORE_TOR * gap:
                    return (star, level)

                if star < data.star_max:
                    (l, u) = data.get_range(star+1, level)
                    if score >= l and score <= u:
                        logger.debug("try star up[%d, %d][%d-%d][target=%d]"
                                % (star+1, level, l, u, score))
                        coe = (average - score) / gap + 1.0
                        candidate[S_UP] = bratio_star * coe
                if star > data.star_min:
                    (l, u) = data.get_range(star-1, level)
                    if score >= l and score <= u:
                        logger.debug("try star down[%d, %d][%d-%d][target=%d]"
                                % (star-1, level, l, u, score))
                        coe = (score - average) / gap + 1.0
                        candidate[S_DOWN] = bratio_star * coe
                if level < data.level_max:
                    (l, u) = data.get_range(star, level+1)
                    if score >= l and score <= u:
                        logger.debug("try level up[%d, %d][%d-%d][target=%d]"
                                % (star, level+1, l, u, score))
                        coe = (average - score) / gap + 1.0
                        candidate[L_UP] = bratio_level * coe
                if level > data.level_min:
                    (l, u) = data.get_range(star, level-1)
                    if score >= l and score <= u:
                        logger.debug("try level down[%d, %d][%d-%d][target=%d]"
                                % (star, level-1, l, u, score))
                        coe = (score - average) / gap + 1.0
                        candidate[L_DOWN] = bratio_level * coe

            d = self._roll(candidate)
            logger.debug("roll result[%d]" % d)
            if d == S_UP:
                star += 1
            elif d == S_DOWN:
                star -= 1
            elif d == L_UP:
                level += 1
            elif d == L_DOWN:
                level -= 1
            elif score <= upper and score >= lower:
                #当前分数段满足要求，但是周边的分数段不满足要求
                return (star, level)
            else:
                #达到极限，所有数据均不能满足要求
                logger.warning("Expect error[basic id=%d][score=%d]" % (basic_id, score))
                return (star, level)


    def _roll(self, candidate):
        total = sum(candidate)
        if total == 0:
            return -1

        r = random.uniform(0, total)
        a = 0
        for index, w in enumerate(candidate):
            a += w
            if r < a:
                return index
        raise Exception("Invalid roll")


    def _mock_hero(self, basic_id, star, level):
        USER_ID = 0
        USER_LEVEL = int(float(
            data_loader.OtherBasicInfo_dict["MaxMonarchLevel"].value))
        hero_id = HeroInfo.generate_id(USER_ID, basic_id)
        soldier_basic_id = HeroInfo.get_default_soldier_basic_id(basic_id)
        soldier = SoldierInfo.create(USER_ID, soldier_basic_id)

        hero = HeroInfo.create_special(USER_ID, USER_LEVEL,
                basic_id, level, star, soldier, [], technology_basic_ids = [])
        return hero


    def _calc_soldier(self, hero, score):
        """实时计算英雄的兵种信息
        """
        if score <= 0:
            return
        base = hero.battle_score
        logger.debug("try calc soldier[target delta=%f]" % score)

        #兵种 basic_id, level 合法取值范围
        soldier_range = {}

        for soldier_key in data_loader.SoldierBasicInfo_dict.keys():
            if (data_loader.SoldierBasicInfo_dict[soldier_key].type ==
                    data_loader.HeroBasicInfo_dict[hero.basic_id].soldierType and
                    data_loader.SoldierBasicInfo_dict[soldier_key].heroLevel <= hero.level):
                (soldier_basic_id, soldier_level) = map(int, soldier_key.split('_'))
                if soldier_basic_id not in soldier_range:
                    soldier_range[soldier_basic_id] = []
                soldier_range[soldier_basic_id].append(soldier_level)

        #随机选择一个兵种
        soldier_basic_id = random.sample(soldier_range.keys(), 1)[0]
        soldier_range[soldier_basic_id].sort()#从小到大排序
        for soldier_level in soldier_range[soldier_basic_id]:
            soldier = SoldierInfo.create(hero.user_id, soldier_basic_id, soldier_level)
            assert hero.update_soldier(soldier, technology_basic_ids = [])

            delta = hero.battle_score - base
            if delta >= score:
                logger.debug("update soldier[target delta=%d][finnal delta=%d]" %
                        (score, delta))
                return

        #理论上不该在此返回
        logger.warning("update soldier error[target delta=%d]" % score)


    def _calc_skill(self, hero, score):
        """实时计算英雄的技能信息
        """
        if score <= 0:
            return
        base = hero.battle_score
        logger.debug("try calc skill[target delta=%f]" % score)

        #尝试升级技能
        delta = 0
        loop = 0
        loop_max = 100
        while delta < score and loop < loop_max:
            loop += 1
            for index in range(0, 4):
                if hero.is_able_to_upgrade_skill(index):
                    (ret, cost) = hero.upgrade_skill(index, technology_basic_ids = [])
                    assert ret
                    delta = hero.battle_score - base

                    if delta >= score:
                        logger.debug("update skill[target delta=%d][finnal delta=%d]" %
                                (score, delta))
                        return

        #理论上不该在此返回，可能是数值错误
        logger.warning("update skill error[target delta=%d][finnal delta=%d]" %
                (score, delta))


    def _calc_equipment(self, hero, score):
        """实时计算英雄的装备信息
        """
        if score <= 0:
            return
        base = hero.battle_score
        logger.debug("try calc equipment[target delta=%f]" % score)

        #尝试进阶装备，精炼装备
        loop = 0
        loop_max = 100
        delta = 0
        while delta < score and loop < loop_max:
            loop += 1
            candidate = []
            for t in [HeroInfo.EQUIPMENT_TYPE_WEAPON,
                    HeroInfo.EQUIPMENT_TYPE_ARMOR,
                    HeroInfo.EQUIPMENT_TYPE_TREASURE]:

                origin_id = hero.get_equipment(t)

                #所有可能的进阶
                if origin_id in data_loader.EquipmentUpgradeBasicInfo_dict:
                    next_id = data_loader.EquipmentUpgradeBasicInfo_dict[
                            origin_id].nextEquipmentId
                    if hero.is_able_to_update_equipment(t, next_id):
                        candidate.append((t, next_id))

                #所有可能的精炼
                if origin_id in data_loader.EquipmentEnchantBasicInfo_dict:
                    nexts = data_loader.EquipmentEnchantBasicInfo_dict[
                            origin_id].nextEquipmentIds
                    for next_id in nexts:
                        if (data_loader.EquipmentBasicInfo_dict[next_id].enchantLevel >
                                data_loader.EquipmentBasicInfo_dict[origin_id].enchantLevel and
                                hero.is_able_to_update_equipment(t, next_id)):
                            candidate.append((t, next_id))

            if len(candidate) == 0:
                logger.debug("cannot update equipment any more")
                return

            #随机选择装备、随机选择进阶还是精炼
            (t, target_id) = random.sample(candidate, 1)[0]
            assert hero.update_equipment(t, target_id, technology_basic_ids = [])
            delta = hero.battle_score - base

            if delta >= score:
                logger.debug("update equipment[target delta=%d][finnal delta=%d]" %
                        (score, delta))
                return

        #理论上不该在此返回，可能是数值错误
        logger.warning("update equipment error[target delta=%d][finnal delta=%d]" %
                (score, delta))


