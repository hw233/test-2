#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 资源相关数值计算
         包括：金钱、粮草、兵力、技能点
"""

import math
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class ResourceInfo(object):
    """资源信息
    """

    def __init__(self, user_id = 0,
            money = 0, food = 0,
            money_output = 0, food_output = 0,
            money_capacity = 0, food_capacity = 0,
            update_time = 0,

            gold = 0, soul = 0, achievement = 0,
            daily_use_money = 0, daily_use_food = 0, daily_use_gold = 0, daily_use_soul = 0,
            daily_gain_money = 0, daily_gain_food = 0, daily_gain_gold = 0, daily_gain_soul = 0,
            six_days_ago_use_gold = '',
            total_use_money = 0, total_use_food = 0, total_use_gold = 0, total_use_soul = 0,
            total_gain_money = 0, total_gain_food = 0, total_gain_gold = 0, total_gain_soul = 0,
            total_gain_cat = 0 ):

        self.user_id = user_id

        #金钱、粮草
        self.money = money
        self.food = food
        self.money_output = money_output
        self.food_output = food_output
        self.money_capacity = money_capacity
        self.food_capacity = food_capacity
        self.update_time = update_time #结算金钱、粮草资源的时刻

        #元宝
        self.gold = gold

        #精魄
        self.soul = soul

        #成就值
        self.achievement = achievement

        #统计信息
        self.daily_use_money = daily_use_money
        self.daily_use_food = daily_use_food
        self.daily_use_gold = daily_use_gold
        self.daily_use_soul = daily_use_soul

        self.daily_gain_money = daily_gain_money
        self.daily_gain_food = daily_gain_food
        self.daily_gain_gold = daily_gain_gold
        self.six_days_ago_use_gold = six_days_ago_use_gold
        self.daily_gain_soul = daily_gain_soul

        self.total_use_money = total_use_money
        self.total_use_food = total_use_food
        self.total_use_gold = total_use_gold
        self.total_use_soul = total_use_soul

        self.total_gain_money = total_gain_money
        self.total_gain_food = total_gain_food
        self.total_gain_gold = total_gain_gold
        self.total_gain_soul = total_gain_soul
        self.total_gain_cat = total_gain_cat

    @staticmethod
    def create(user_id, vip_level, now):
        """初始的资源信息，创建一个新用户时调用
        Args:
            user_id[int]: 用户 id
            vip_level[int]: vip 等级
            now[int]: 当前时间戳
        Returns:
            resource[ResourceInfo]
        """
        resource = ResourceInfo(user_id)

        resource.update_time = now
        return resource


    def update_current_resource(self, now):
        """更新当前资源情况
        1 更新金钱、粮草当前总量
        Args:
            now[int]: 当前时间戳
        Returns:
            None
        """
        #更新金钱、粮草
        duration = now - self.update_time
        money_addition = int(self.money_output / 3600.0 * duration)
        food_addition = int(self.food_output / 3600.0 * duration)

        self.gain_money(money_addition)
        self.gain_food(food_addition)

        self.update_time = now


    def update_money_output(self, output):
        """更新金钱产量
        """
        logger.debug("update money output[output=%f]" % output)
        assert output >= 0
        self.money_output = output


    def update_food_output(self, output):
        """更新粮食产量
        """
        logger.debug("update food output[output=%f]" % output)
        assert output >= 0
        self.food_output = output


    def update_money_capacity(self, capacity):
        """更新金钱储量
        """
        logger.debug("update money capacity[capacity=%f]" % capacity)
        assert capacity >= 0
        self.money_capacity = capacity


    def update_food_capacity(self, capacity):
        """更新粮食储量
        """
        logger.debug("update food capacity[capacity=%f]" % capacity)
        assert capacity >= 0
        self.food_capacity = capacity


    def gain_money(self, addition, ignore_max = False):
        """获得金钱
        Args:
            addition[int/float]: 获得金钱数量
            ignore_max[bool]: 是否忽略储量上限
        Returns:
            None
        """
        addition = int(addition)
        #assert addition >= 0
        if addition <= 0:
            return

        origin = self.money

        if ignore_max:
            self.money += addition
        elif self.money < self.money_capacity:
            self.money += addition
            if self.money > self.money_capacity:
                self.money = self.money_capacity

        diff = self.money - origin
        self.daily_gain_money += diff
        self.total_gain_money += diff


    def gain_food(self, addition, ignore_max = False):
        """获得粮草
        Args:
            addition[int/float]: 获得粮草数量
            ignore_max[bool]: 是否忽略储量上限
        Returns:
            None
        """
        addition = int(addition)
        assert addition >= 0
        if addition == 0:
            return

        origin = self.food

        if ignore_max:
            self.food += addition
        elif self.food < self.food_capacity:
            self.food += addition
            if self.food > self.food_capacity:
                self.food = self.food_capacity

        diff = self.food - origin
        self.daily_gain_food += diff
        self.total_gain_food += diff


    def gain_gold(self, addition):
        """获得元宝
        Args:
            addition[int/float]: 获得元宝数量
        Returns:
            None
        """
        addition = int(addition)
        assert addition >= 0
        if addition == 0:
            return

        self.gold += addition
        self.daily_gain_gold += addition
        self.total_gain_gold += addition
    
    def gain_total_cat_gold(self, addition):
        """获得招财猫总计元宝"""
        addition = int(addition)
        assert addition >= 0
        self.total_gain_cat += addition
        

    def gain_soul(self, addition):
        """获得精魄"""
        addition = int(addition)
        assert addition >= 0
        
        self.soul += addition
        self.daily_gain_soul += addition
        self.total_gain_soul += addition

    def gain_achievement(self, addition):
        """获得成就值
        Args:
            addition[int/float]: 获得成就值
        Returns:
            None
        """
        addition = int(addition)
        assert addition >= 0
        if addition == 0:
            return

        self.achievement += addition
        logger.debug("Gain achievement[gain=%d][total=%d]" % (addition, self.achievement))


    def cost_money(self, money_cost, gold_cost = 0):
        """消费金钱
        Args:
            money_cost[int]: 消费数目
            gold_cost[bool]: 当金钱数量不足时，使用元宝兑换金钱，元宝的数目
        Returns:
            True: 成功
            False: 失败
        """
        assert money_cost >= 0

        if gold_cost > 0:
            gap = money_cost - self.money
            if gold_cost != self.gold_exchange_resource(money = gap):
                logger.warning("Gold exchange money failed[try cost gold=%d]" % gold_cost)
                return False

        if self.money < money_cost:
            logger.warning("Not enough money[own=%d][need=%d]" % (self.money, money_cost))
            #return False

        self.money = max(0, self.money - money_cost)
        self.daily_use_money += money_cost
        self.total_use_money += money_cost

        logger.debug("Cost money[cost=%d][remain=%d]" % (money_cost, self.money))
        return True


    def cost_food(self, food_cost, gold_cost = 0):
        """消费粮草
        Args:
            food_cost[int]: 消费数目
            gold_cost[bool]: 当金钱数量不足时，使用元宝兑换金钱，元宝的数目
        Returns:
            True: 成功
            False: 失败
        """
        assert food_cost >= 0

        if gold_cost > 0:
            gap = food_cost - self.food
            if gold_cost != self.gold_exchange_resource(food = gap):
                logger.warning("Gold exchange food failed[try cost gold=%d]" % gold_cost)
                return False

        if self.food < food_cost:
            logger.warning("Not enough food[own=%d][need=%d]" % (self.food, food_cost))
            #return False

        self.food = max(0, self.food - food_cost)
        self.daily_use_food += food_cost
        self.total_use_food += food_cost
        logger.debug("Cost food[cost=%d][remain=%d]" % (food_cost, self.food))
        return True


    def cost_gold(self, gold_cost):
        """消费元宝
        Args:
            gold_cost[int]: 消费数目
        Returns:
            True: 成功
            False: 失败
        """
        assert gold_cost >= 0
        if self.gold < gold_cost:
            logger.warning("Not enough gold[own=%d][need=%d]" % (self.gold, gold_cost))
            return False

        self.gold -= gold_cost
        self.daily_use_gold += gold_cost
        self.total_use_gold += gold_cost
        logger.debug("Cost gold[cost=%d][remain=%d]" % (gold_cost, self.gold))
        return True

    def cost_soul(self, soul_cost):
        """消耗精魄"""
        assert soul_cost >= 0
        if self.soul < soul_cost:
            logger.warning("Not enough soul[own=%d][need=%d]" % (self.soul, soul_cost))
            return False
        
        self.soul -= soul_cost
        self.daily_use_soul += soul_cost
        self.total_use_soul += soul_cost
        logger.debug("Cost soul[cost=%d][remain=%d]" % (soul_cost, self.soul))
        return True

    def cost_achievement(self, achievement_cost):
        """消费成就值
        Args:
            achievement_cost[int]: 消费数目
        Returns:
            True: 成功
            False: 失败
        """
        assert achievement_cost >= 0
        if self.achievement < achievement_cost:
            logger.warning("Not enough achievement[own=%d][need=%d]" %
                    (self.achievement, achievement_cost))
            return False

        self.achievement -= achievement_cost

        logger.debug("Cost achievement[cost=%d][remain=%d]" %
                (achievement_cost, self.achievement))
        return True


    def reset_daily_statistics(self, days_diff):
        """重置天粒度统计信息
        Returns:
            None
        """
        use_golds_before = utils.split_to_int(self.six_days_ago_use_gold)
        #将daily使用元宝个数保存下来，存到前六天的数组里
        day = 1
        while day <= days_diff:
            if len(use_golds_before) == 6:
                use_golds_before.pop()
            if day == 1:
                use_golds_before.insert(0, self.daily_use_gold)
            else:
                #如果隔了几天没登录，中间插入0
                use_golds_before.insert(0, 0)

            day += 1

        self.six_days_ago_use_gold = utils.join_to_string(use_golds_before)
        
        self.daily_use_money = 0
        self.daily_use_food = 0
        self.daily_use_gold = 0
        self.daily_use_soul = 0
        self.daily_gain_money = 0
        self.daily_gain_food = 0
        self.daily_gain_gold = 0
        self.daily_gain_soul = 0


    def gold_exchange_resource(self, money = 0, food = 0):
        """
        使用元宝兑换其他资源
        Args:
            money[int]: 希望获得的金钱数目
            food[int]: 希望获得的粮草数目
        Returns:
            消耗的元宝数量
            小于0，表示兑换失败
        """
        need_gold = self._money_to_gold(money)
        need_gold += self._food_to_gold(food)

        if not self.cost_gold(need_gold):
            return -1

        #这里可以超过上限
        self.gain_money(money, True)
        self.gain_food(food, True)

        logger.debug("Gold exchange resource"
                "[consume gold=%d][gain money=%d][gain food=%d]" %
                (need_gold, money, food))
        return need_gold


    def gold_exchange_enchant_point(self, point):
        """
        使用元宝兑换精炼 point
        Args:
            point[int]: 精炼 point
        Returns:
            消耗的元宝数量
            小于0，表示兑换失败
        """
        need_gold = self._enchant_point_to_gold(point)

        if not self.cost_gold(need_gold):
            return -1

        logger.debug("Gold exchange enchant point"
                "[consume gold=%d][gain point=%d]" %
                (need_gold, point))
        return need_gold


    def gold_exchange_soldier(self, soldier):
        """
        使用元宝兑换兵力
        Args:
            soldier[int]: 希望获得的士兵数量
        Returns:
            True: 兑换成功
            False: 兑换失败
        """
        need_gold = self.soldier_to_gold(soldier)

        if self.cost_gold(need_gold):
            return need_gold
        else:
            return -1


    def gold_exchange_time(self, seconds):
        """
        使用元宝兑换时间
        Args:
            seconds[int]: 希望节省的时间(s)
        Returns:
            True: 兑换成功
            False: 兑换失败
        """
        need_gold = self._time_to_gold(seconds)

        if self.cost_gold(need_gold):
            return need_gold
        else:
            return -1


    @staticmethod
    def _time_to_gold(seconds):
        """计算节省对应时间需要多少元宝
        """
        rate = float(data_loader.OtherBasicInfo_dict["Gold2Time"].value)
        need_gold = utils.ceil_to_int(seconds / rate)#向上取整
        return need_gold


    @staticmethod
    def _money_to_gold(money):
        """计算获得对应金钱需要多少元宝
        """
        rate = float(data_loader.OtherBasicInfo_dict["Gold2Money"].value)
        need_gold = utils.ceil_to_int(money / rate)
        return need_gold


    @staticmethod
    def _enchant_point_to_gold(point):
        """计算获得对应的精炼值需要多少元宝
        """
        rate = float(data_loader.OtherBasicInfo_dict["Gold2EnchantPoint"].value)
        need_gold = utils.ceil_to_int(point / rate)
        return need_gold


    @staticmethod
    def _food_to_gold(food):
        """计算获得对应粮草需要多少元宝
        """
        rate = float(data_loader.OtherBasicInfo_dict["Gold2Food"].value)
        need_gold = utils.ceil_to_int(food / rate)
        return need_gold


    @staticmethod
    def soldier_to_gold(soldier):
        """计算获得对应士兵需要多少元宝
        """
        rate = float(data_loader.OtherBasicInfo_dict["Gold2Soldier"].value)
        need_gold = utils.ceil_to_int(soldier / rate)
        return need_gold



