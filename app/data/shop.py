#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 商店相关计算逻辑
"""

import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class GoodsInfo(object):
    def __init__(self, id = 0, user_id = 0, type = 0,
            item_basic_id = 0, item_num = 0, price = 0, discount = 10, is_sold = False):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.item_basic_id = item_basic_id
        self.item_num = item_num
        self.price = price
        self.discount = discount
        self.is_sold = is_sold


    def get_real_price(self):
        """获取实际价格（乘上折扣之后的价格）
        """
        return utils.floor_to_int(self.price * self.discount * 1.0 / 10.0)



class ShopInfo(object):
    """商店信息
    """
    GOODS_TYPE_MONEY = 1
    GOODS_TYPE_GOLD = 2
    GOODS_TYPE_ACHIEVEMENT = 3
    GOODS_TYPE_LEGENDCITY = 4
    GOODS_TYPE_UNION = 5
    GOODS_TYPE_ARENA = 6
    GOODS_TYPE_SOUL_SOUL = 7
    GOODS_TYPE_SOUL_GOLD = 8

    ONSALE = 0
    SOLDOUT = 1

    __slots__ = [
            "id", "user_id", "type", "index",
            "goods_pool", "goods_ids", "goods_status", "goods_discount",
            "next_free_time", "refresh_num", "reset_time",
            ]

    def __init__(self, id = 0, user_id = 0, type = GOODS_TYPE_MONEY, index = 1,
            goods_pool = '', goods_ids = '', goods_status = '',
            goods_discount = '',
            next_free_time = 0, refresh_num = 0, reset_time = 0):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.index = index

        self.goods_pool = goods_pool
        self.goods_ids = goods_ids
        self.goods_status = goods_status
        self.goods_discount = goods_discount

        self.next_free_time = next_free_time#下一次免费刷新商品的时间戳
        self.refresh_num = refresh_num

        self.reset_time = reset_time


    @staticmethod
    def generate_id(user_id, type, index = 1):
        id = user_id << 32 | type << 16 | index
        return id


    @staticmethod
    def create(user_id, type, index = 1):
        """
        """
        id = ShopInfo.generate_id(user_id, type, index)
        shop = ShopInfo(id, user_id, type, index)
        return shop


    def _create_goods(self, pool_name, id, status, discount):
        """创建商品信息
        """
        pool = getattr(data_loader, pool_name)

        goods = GoodsInfo(id, self.user_id, self.type)
        goods.item_basic_id = pool[id].itemBasicId
        goods.item_num = pool[id].itemNum
        goods.price = pool[id].price
        goods.discount = discount
        goods.is_sold = (status == self.SOLDOUT)

        return goods


    def try_reset_shop(self, now):
        """尝试重置商店信息
        如果是新的一天，需要重置商店信息
        重置 刷新货物的次数
        """
        if not utils.is_same_day(self.reset_time, now):
            self.refresh_num = 0
            self.reset_time = now


    def is_able_to_refresh_free(self, now):
        """是否可以免费刷新
        Args:
            now: 当前的时间戳
        """
        return now >= self.next_free_time


    def calc_next_free_refresh_time(self, now):
        """计算下次免费刷新的时间
          每天固定时间有免费刷新的机会
        """
        if now < self.next_free_time:
            #下次刷新时间未到，不需要计算
            return True

        times = data_loader.GoodsRefreshTimeInfo_dict.values()

        for info in times:
            free_ts = utils.get_spec_second(now, info.time)
            if self.next_free_time < free_ts and now < free_ts:
                self.next_free_time = free_ts
                return True

        tomorrow = now + utils.SECONDS_OF_DAY
        self.next_free_time = utils.get_spec_second(tomorrow, times[0].time)
        return True


    def calc_gold_consume_of_refresh_goods(self, vip_level):
        """计算刷新商店货物的消耗
        """
        refresh_num = self.refresh_num + 1

        max_num = max(data_loader.GoodsRefreshCostInfo_dict.keys())
        num = min(max_num, refresh_num)
        if vip_level < data_loader.GoodsRefreshCostInfo_dict[num].limitVipLevel:
            logger.debug("vip level error[vip=%d]" % vip_level)
            return -1
        else:
            gold_cost = data_loader.GoodsRefreshCostInfo_dict[num].goldCost
            if (self.type == self.GOODS_TYPE_MONEY
                    or self.type == self.GOODS_TYPE_GOLD
                    or self.type == self.GOODS_TYPE_SOUL_SOUL
                    or self.type == self.GOODS_TYPE_SOUL_GOLD):
                return gold_cost / 2
            else:
                return gold_cost


    def refresh_goods(self,
            pool_name, goods_num, discount_num, discount, goods_list, now, free):
        """刷新酒肆中可以购买的货物
        Args:
            pool_name[string]: 货物池名称
            goods_num[int]: 选出的货物数量
            discount_num[int]: 有折扣的货物数量
            discount[int]: 折扣 [1-10]
            goods_list[list(GoodsInfo) out]: 可以购买的货物列表
            now[int]: 当前时间戳
            free[bool]: 是否免费刷新
        """
        pool_name = "%s_dict" % pool_name
        pool = getattr(data_loader, pool_name)
        self.goods_pool = pool_name

        logger.debug("refresh goods[type=%d][index=%d][pool=%s]" %
                (self.type, self.index, self.goods_pool))

        #在货物池中随机选择可以购买的货物
        candidate = []
        for id in pool:
            candidate.append((id, pool[id].weight))
        goods_num = min(len(candidate), goods_num)
        results = ShopInfo._roll(candidate, goods_num)
        if len(results) == 0:
            logger.warning("Roll goods failed")
            return False

        #计算出所有商品的折扣
        MAX_DISCOUNT = 10#不打折
        goods_discount = []
        for i in range(0, discount_num):
            goods_discount.append(discount)
        for i in range(discount_num, len(results)):
            goods_discount.append(MAX_DISCOUNT)
        random.shuffle(goods_discount)

        #更新货物状态
        self.goods_ids = utils.join_to_string([id for (id, weight) in results])
        self.goods_status = utils.join_to_string([self.ONSALE] * len(results))
        self.goods_discount = utils.join_to_string(goods_discount)

        i = 0
        for (id, weight) in results:
            goods = self._create_goods(self.goods_pool, id, self.ONSALE, goods_discount[i])
            goods_list.append(goods)
            i += 1

        #如果免费刷新，不更新刷新次数
        if not free:
            self.refresh_num += 1

        #更新下次免费刷新的时间
        self.calc_next_free_refresh_time(now)

        return True


    def seek_goods(self, goods_list):
        """查询酒肆中可以购买的货物
        Args:
            goods_list[list(GoodsInfo) out]: 可以购买的货物列表
        """
        ids = utils.split_to_int(self.goods_ids)
        status = utils.split_to_int(self.goods_status)
        discount = utils.split_to_int(self.goods_discount)
        assert len(ids) == len(status)

        for index in range(0, len(ids)):
            goods = self._create_goods(
                    self.goods_pool, ids[index], status[index], discount[index])
            goods_list.append(goods)

        return True


    def check_goods(self):
        """检查之前的商品有没有问题，以防goods表中删了物品
        """
        pool = getattr(data_loader, self.goods_pool)
        ids = utils.split_to_int(self.goods_ids)
        for index in range(0, len(ids)):
            if ids[index] not in pool:
                return False

        return True


    def buy_goods(self, id):
        """购买货物
        Returns:
            GoodsInfo: 购买到的货物信息
            None: 购买失败
        """
        goods_ids = utils.split_to_int(self.goods_ids)
        goods_status = utils.split_to_int(self.goods_status)
        goods_discount = utils.split_to_int(self.goods_discount)

        if id not in goods_ids:
            logger.warning("Goods not exist[id=%d]" % id)
            return None

        index = goods_ids.index(id)
        status = goods_status[index]
        discount = goods_discount[index]
        goods = self._create_goods(self.goods_pool, id, status, discount)

        if goods.is_sold:
            logger.warning("Goods is sold out")
            return None

        goods.is_sold = True
        if self.type != self.GOODS_TYPE_GOLD: #元宝商店物品不会售空
            goods_status[index] = self.SOLDOUT

        self.goods_status = utils.join_to_string(goods_status)

        return goods


    def calc_goods_price(self, id):
        """查询货物原价
        """
        goods_ids = utils.split_to_int(self.goods_ids)
        goods_status = utils.split_to_int(self.goods_status)
        goods_discount = utils.split_to_int(self.goods_discount)
        if id not in goods_ids:
            logger.warning("Goods not exist[id=%d]" % id)
            return -1

        index = goods_ids.index(id)
        status = goods_status[index]
        discount = goods_discount[index]
        goods = self._create_goods(self.goods_pool, id, status, discount)
        return goods.price


    @staticmethod
    def _roll(candidate, num):
        """随机选择，在 candidate 中抽取 num 个项
           物品抽取的概率 = weight / total_weight
           选中的项不允许重复
        Args:
            candidate[list((id, weight) out]: 候选项
            num: 最终选出的项的个数
        Returns:
            list((id, weight)) 最终选出的项，不允许出现相同 id 的项
        """
        assert num > 0
        if len(candidate) < num:
            logger.warning("Candidate num error[want choose num=%d]" % num)
            return []

        total_weight = 0
        for item in candidate:
            # logger.debug("candidate=%d, %d" % (item[0], item[1]))
            total_weight += item[1]

        win_num = 0
        begin = 0
        end = total_weight - 1
        random.seed()
        while win_num < num:
            roll = random.randint(begin, end)
            # logger.debug("roll=%d[%d=%d]" % (roll, begin, end))

            sum = begin
            choose = None
            for item in candidate[win_num:]:
                sum += item[1]
                if roll < sum:
                    choose = item
                    # logger.debug("choose=%d, %d" % (item[0], item[1]))
                    break
            assert choose is not None

            win_num += 1
            begin += item[1]
            candidate.remove(choose)
            candidate.insert(0, choose)#插入最前端

        return candidate[:win_num]


