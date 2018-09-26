#coding:utf8
"""
Created on 2016-1-8
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 抽奖
"""

import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class DrawInfo(object):

    DRAW_TYPE_MONEY = 1
    DRAW_TYPE_MONEY_MULTI = 2
    DRAW_TYPE_GOLD = 3
    DRAW_TYPE_GOLD_MULTI = 4
    DRAW_TYPE_MONEY_FIRST = 5
    DRAW_TYPE_GOLD_FIRST = 6

    def __init__(self, user_id = 0,
            money_draw_free_time = 0, money_draw_free_num = 0,
            gold_draw_free_time = 0, gold_draw_free_num = 0,
            reset_time = 0, daily_money_draw_num = 0, total_money_draw_num = 0,
            last_gold_draw_time = 0, activity_scores = 0,treasure_scores = 0,
            daily_gold_draw_num = 0, total_gold_draw_num = 0,
            total_treasure_draw_num = 0):
        self.user_id = user_id

        self.money_draw_free_time = money_draw_free_time #下一次可以免费抽奖的时间
        self.money_draw_free_num = money_draw_free_num #免费抽奖剩余次数
        self.gold_draw_free_time = gold_draw_free_time
        self.gold_draw_free_num = gold_draw_free_num
        self.reset_time = reset_time
        self.daily_money_draw_num = daily_money_draw_num    #记录每天抽奖次数
        self.total_money_draw_num = total_money_draw_num    #记录抽奖次数
        self.last_gold_draw_time = last_gold_draw_time    #上一次元宝抽奖的时间
        self.activity_scores = activity_scores       #活动积分（拍卖英雄活动）
        self.treasure_scores = treasure_scores       #夺宝积分
        self.daily_gold_draw_num = daily_gold_draw_num    #记录每天抽奖次数
        self.total_gold_draw_num = total_gold_draw_num    #记录抽奖次数
        self.total_treasure_draw_num = total_treasure_draw_num #夺宝次数
    @staticmethod
    def create(user_id):
        """
        """
        draw = DrawInfo(user_id)
        return draw


    def try_money_draw_free(self, now):
        """尝试免费金钱抽奖
        """
        if now >= self.money_draw_free_time and self.money_draw_free_num > 0:
            interval = int(float(
                data_loader.OtherBasicInfo_dict["WineshopFreeMoneySearchTimeInterval"].value))
            self.money_draw_free_time = now + interval
            self.money_draw_free_num -= 1
            return True

        return False


    def try_gold_draw_free(self, now):
        """尝试免费元宝抽奖
        """
        if now >= self.gold_draw_free_time and self.gold_draw_free_num > 0:
            interval = int(float(
                data_loader.OtherBasicInfo_dict["WineshopFreeGoldSearchTimeInterval"].value))
            self.gold_draw_free_time = now + interval
            self.gold_draw_free_num -= 1
            return True

        return False


    def reset_daily_statistics(self):
        """重置天粒度统计信息
        Returns:
            None
        """
        self.daily_money_draw_num = 0
        self.daily_gold_draw_num = 0


    def add_money_draw_num(self, num):
        """记录抽奖次数
        """
        self.daily_money_draw_num += num
        self.total_money_draw_num += num


    def add_gold_draw_num(self, num):
        """记录抽奖次数
        """
        self.daily_gold_draw_num += num
        self.total_gold_draw_num += num

    def add_treasure_draw_num(self, num):
        """记录抽奖次数
        """
        self.total_treasure_draw_num += num



    def try_reset_draw(self, now):
        """尝试重置抽奖信息
        如果是新的一天，需要重置
        重置 金钱抽、元宝抽次数
        """
        if not utils.is_same_day(self.reset_time, now):
            self.money_draw_free_num = int(float(
                data_loader.OtherBasicInfo_dict["WineshopFreeMoneySearchNum"].value))
            self.gold_draw_free_num = int(float(
                data_loader.OtherBasicInfo_dict["WineshopFreeGoldSearchNum"].value))
            self.reset_time = now


    def set_last_gold_draw_time(self, now):
        """
        """
        self.last_gold_draw_time = now


    def add_activity_scores(self, score):
        """
        """
        self.activity_scores += score

    def add_treasure_scores(self, score):
        """
        """
        self.treasure_scores += score

    def clear_activity_scores(self):
        """
        """
        self.activity_scores = 0


    def calc_draw_cost(self, type, now, free = False):
        """
        计算抽奖的花费
        Args:
            type[int]: 抽奖的类型
            free[bool]: 是否是免费抽奖
            now[int]: 时间戳
        Returns:
            花费的金钱或元宝
            -1 计算失败
        """
        if type == self.DRAW_TYPE_MONEY or type == self.DRAW_TYPE_MONEY_FIRST:
            if free and not self.try_money_draw_free(now):
                logger.warning("Can not free money draw now")
                return -1

            if free:
                return 0
            else:
                return int(float(
                    data_loader.OtherBasicInfo_dict["WineshopMoneySearchOneCost"].value))

        elif type == self.DRAW_TYPE_MONEY_MULTI:
            if free:
                logger.warning("Can not free multi money draw")
                return -1

            return int(float(
                data_loader.OtherBasicInfo_dict["WineshopMoneySearchTenCost"].value))

        elif type == self.DRAW_TYPE_GOLD or type == self.DRAW_TYPE_GOLD_FIRST:
            if free and not self.try_gold_draw_free(now):
                logger.warning("Can not free gold draw now")
                return -1

            if free:
                return 0
            else:
                return int(float(
                    data_loader.OtherBasicInfo_dict["WineshopGoldSearchOneCost"].value))

        elif type == self.DRAW_TYPE_GOLD_MULTI:
            if free:
                logger.warning("Can not free multi gold draw")
                return -1

            return int(float(
                data_loader.OtherBasicInfo_dict["WineshopGoldSearchTenCost"].value))

        logger.warning("Invalid draw type[type=%d]" % type)
        return -1

    def calc_treasure_draw_reward(self, basic_data, user, req, item_list):
        candidate = []
        count = req.times
        pool = basic_data.activity_hero_reward_list.get_all()
        for i in range(len(pool)):
            candidate.append((int(pool[i].items_id), pool[i].weight, True))
        self.add_treasure_draw_num(count)
        win_list = DrawInfo._draw(candidate, count)

        #for info in win_list:
        #    level = info[0]
        #    item_id = int(pool[level].items_id)
        #    num = int(pool[level].items_num)
        #    assert item_id != 0
        #    assert num > 0
        #    logger.warning("item_id = %d num = %d"% (item_id,num))
        #    item_list.append((item_id, num))
        
        for i in range(len(win_list)):
            for j in range(len(pool)):
                if (int(pool[j].items_id) == win_list[i][0] and pool[j].weight == win_list[i][1]):
                    item_list.append((int(pool[j].items_id), int(pool[j].items_num)))
                    break
        
        return True




    def calc_draw_reward(self, user, type, hero_list, item_list):
        """抽奖
        """
        candidate = []

        if type == self.DRAW_TYPE_MONEY_FIRST:
            #第一次金钱抽
            count = 1
            pool = data_loader.FirstMoneyDrawBasicInfo_dict
            for id in pool:
                candidate.append((id, pool[id].weight, True))
            self.add_money_draw_num(count)

        elif type == self.DRAW_TYPE_GOLD_FIRST:
            #第一次元宝抽
            count = 1
            pool = data_loader.FirstGoldDrawBasicInfo_dict
            for id in pool:
                candidate.append((id, pool[id].weight, True))
            self.add_gold_draw_num(count)

        elif type == self.DRAW_TYPE_MONEY:
            #金钱抽
            count = 1
            pool_name = data_loader.DrawPoolMatchBasicInfo_dict[user.level].moneyPoolName
            pool_name = "%s_dict" % pool_name
            pool = getattr(data_loader, pool_name)
            for id in pool:
                candidate.append((id, pool[id].weight, True))
            self.add_money_draw_num(count)

        elif type == self.DRAW_TYPE_MONEY_MULTI:
            #金钱十连抽
            count = 10
            pool_name = data_loader.DrawPoolMatchBasicInfo_dict[user.level].multiMoneyPoolName
            pool_name = "%s_dict" % pool_name
            pool = getattr(data_loader, pool_name)

            need_level = int(float(data_loader.OtherBasicInfo_dict["BlueItemLevel"].value))
            for id in pool:
                hero_id = pool[id].heroBasicId
                item_id = pool[id].itemBasicId
                #需要抽到英雄，或者抽到蓝色等级的物品
                include = (hero_id != 0 or
                        data_loader.ItemBasicInfo_dict[item_id].level >= need_level)
                candidate.append((id, pool[id].weight, include))
            self.add_money_draw_num(count)

        elif type == self.DRAW_TYPE_GOLD:
            #元宝抽
            count = 1
            pool_name = data_loader.DrawPoolMatchBasicInfo_dict[user.level].goldPoolName
            pool_name = "%s_dict" % pool_name
            pool = getattr(data_loader, pool_name)
            for id in pool:
                candidate.append((id, pool[id].weight, True))
            self.add_gold_draw_num(count)

        elif type == self.DRAW_TYPE_GOLD_MULTI:
            #元宝十连抽
            count = 10
            pool_name = data_loader.DrawPoolMatchBasicInfo_dict[user.level].multiGoldPoolName
            pool_name = "%s_dict" % pool_name
            pool = getattr(data_loader, pool_name)

            need_level = int(float(data_loader.OtherBasicInfo_dict["OrangeHeroLevel"].value))
            for id in pool:
                hero_id = pool[id].heroBasicId
                #需要抽到橙色英雄
                include = (hero_id != 0 and 
                        data_loader.HeroBasicInfo_dict[hero_id].potentialLevel >= need_level)
                candidate.append((id, pool[id].weight, include))
            self.add_gold_draw_num(count)

        win_list = DrawInfo._draw(candidate, count)

        for info in win_list:
            id = info[0]
            hero_id = pool[id].heroBasicId
            item_id = pool[id].itemBasicId
            num = pool[id].itemNum
            if hero_id != 0:
                assert item_id == 0
                hero_list.append((hero_id, 1))
            else:
                assert item_id != 0
                assert num > 0
                item_list.append((item_id, num))

        return True


    @staticmethod
    def _draw(candidate, num):
        """抽奖，在 candidate 中抽取 num 个项
           物品抽取的概率 = weight / total_weight
           必须满足：至少包含一个必须项（include = True）
           可以包含相同的项
        Args:
            candidate[list((id, weight, include)]: 候选项
            num: 最终选出的项的个数
        Returns:
            list((id, weight, include)) 最终选出的项，相同 id 的项并不合并
        """
        def is_satisfy(list):
            include = [info for info in list if info[2]]
            if include:
                return True
            return False

        assert num > 0
        assert is_satisfy(candidate)

        total_weight = 0
        for item in candidate:
            # logger.debug("candidate=%d, %d, %r" % (item[0], item[1], item[2]))
            total_weight += item[1]

        win = []
        win_num = 0
        random.seed()
        while win_num < num:
            #最后一个名额，一定要确保包含了必须 include 的项
            if win_num == num-1 and not is_satisfy(win):
                logger.debug("not satisfy until last round")
                sat_candidate = []
                for item in candidate:
                    if not item[2]:
                        total_weight -= item[1]
                    else:
                        sat_candidate.append(item)
                candidate = sat_candidate
            roll = random.randint(0, total_weight-1)
            # logger.debug("roll=%d[%d-%d]" % (roll, 0, total_weight-1))

            sum = 0
            choose = None
            for item in candidate:
                sum += item[1]
                # logger.debug("sum=%d add=%d" % (sum, item[1]))
                if roll < sum:
                    choose = item
                    logger.debug("choose=%d, %d, %r" % (item[0], item[1], item[2]))
                    break
            assert choose is not None

            win.append(choose)
            win_num += 1

        return win


