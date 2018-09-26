#coding:utf8
"""
Created on 2016-03-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 充值相关数据存储结构
"""

import os
import re
import json
import socket
import random
from urllib import urlencode
from firefly.server.globalobject import GlobalObject
from firefly.utils.singleton import Singleton
from utils.redis_agent import RedisAgent
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class PayPool(object):
    """充值商品池
    """
    __metaclass__ = Singleton

    ORDER_TYPE_NORMAL = 1  #普通
    ORDER_TYPE_CARD = 2    #月卡
    ORDER_TYPE_PACKAGE = 3 #礼包


    def __init__(self):
        self.package = []
        self.package_weight = []
        self.package_total_weight = 0

        for id in data_loader.PayBasicInfo_dict:
            order = data_loader.PayBasicInfo_dict[id]
            if order.type == self.ORDER_TYPE_PACKAGE:
                self.package.append(order.id)
                weight = order.weight
                self.package_weight.append(weight)
                self.package_total_weight += weight


    def get(self, id):
        """获得商品信息
        """
        return data_loader.PayBasicInfo_dict[id]


    def get_by_product_id(self, product_id, order_id = ''):
        """根据 product id 获取商品信息
        """
        #临时代码（应对酷派的支付问题）
        kupai_product_ids = {}
        kupai_product_ids['1'] = 'com.anqu.zwsgApp.zwsg10110101'
        kupai_product_ids['2'] = 'com.anqu.zwsgApp.zwsg10110102'
        kupai_product_ids['3'] = 'com.anqu.zwsgApp.zwsg10110103'
        kupai_product_ids['4'] = 'com.anqu.zwsgApp.zwsg10110104'
        kupai_product_ids['5'] = 'com.anqu.zwsgApp.zwsg10110105'
        kupai_product_ids['6'] = 'com.anqu.zwsgApp.zwsg10110106'
        kupai_product_ids['7'] = 'com.anqu.zwsgApp.zwsg10110201'
        kupai_product_ids['8'] = 'com.anqu.zwsgApp.zwsg10110202'
        kupai_product_ids['9'] = 'com.anqu.zwsgApp.zwsg10110203'
        kupai_product_ids['10'] = 'com.anqu.zwsgApp.zwsg10110204'
        kupai_product_ids['11'] = 'com.anqu.zwsgApp.zwsg10110205'
        kupai_product_ids['12'] = 'com.anqu.zwsgApp.zwsg10110206'
        kupai_product_ids['13'] = 'com.anqu.zwsgApp.zwsg10120103'
        kupai_product_ids['14'] = 'com.anqu.zwsgApp.zwsg10120102'
        kupai_product_ids['15'] = 'com.anqu.zwsgApp.zwsg10110200'
        kupai_product_ids['16'] = 'com.anqu.zwsgApp.zwsg10120104'
        
        if kupai_product_ids.has_key(product_id):
            product_id = kupai_product_ids[product_id]
            
        for id in data_loader.PayBasicInfo_dict:
            info = data_loader.PayBasicInfo_dict[id]
            if info.productId == product_id:
                if order_id != '' and info.productCount != 1: 
                    #只处理购买多份的情况
                    if str(info.id) == order_id:
                        return info
                else:
                    return info
        return None


    def random_package(self, count, test = False):
        """随机获得礼包类商品
        Args:
            count[int]: 选择的礼包个数，不允许重复
        Returns:
            list(id) 礼包商品 id 列表
        """
        if count <= 0:
            return []

        assert count <= len(self.package)

        #如果是测试环境，返回所有的礼包，便于测试
        if test:
            count = len(self.package)

        result = []
        random.seed()
        total_weight = self.package_total_weight

        while len(result) < count:
            c = random.uniform(0, total_weight)
            cur_weight = 0
            for index, weight in enumerate(self.package_weight):
                cur_weight += weight
                if c < cur_weight:
                    id = self.package.pop(index)
                    result.append(id)
                    self.package.append(id)
                    self.package_weight.pop(index)
                    self.package_weight.append(weight)
                    total_weight -= weight
                    break

        return result


class PayInfo(object):
    """充值商店信息
    """
    TYPE_PAY_CARD = 1           #月卡
    TYPE_PAY_GREAT_CARD = 2     #尊享月卡
    TYPE_PAY_CARD_WEEK = 3      #周卡
    TYPE_PAY_CARD_FOREVER = 4         #福利卡（终身）
    TYPE_PAY_CARD_SMALL_WEEK = 5      #小周卡

    __slots__ = [
            "user_id",
            "refresh_time",
            "card_deadline",
            "great_card_deadline",
            "week_card_deadline",
            "forever_card_deadline",
            "small_week_card_deadline",
            "order_normal_ids",
            "order_card_ids",
            "order_package_ids",
            "pre_order_number",
            "pay_count",
            "pay_amount",
            ]


    @staticmethod
    def create(user_id, pattern, now, test = False, multi_count = False):
        """创建
        """
        pay = PayInfo(user_id)

        #初始化第一次购买的物品
        normal = []
        card = []
        for id in data_loader.InitUserBasicInfo_dict[pattern].payBasicId:
            order = PayPool().get(id)
            if order.type == PayPool.ORDER_TYPE_NORMAL:
                normal.append(id)
            elif order.type == PayPool.ORDER_TYPE_CARD:
                card.append(id)

        pay.order_normal_ids = utils.join_to_string(normal)
        pay.order_card_ids = utils.join_to_string(card)
        pay.refresh(now, test, multi_count, pattern)

        return pay


    def __init__(self, user_id = 0, refresh_time = 0,
            card_deadline = 0, great_card_deadline = 0, week_card_deadline = 0,
            forever_card_deadline = 0, small_week_card_deadline = 0,
            order_normal_ids = '', order_card_ids = '', order_package_ids = '',
            pre_order_number = '', pay_count = 0, pay_amount = 0.0):
        """初始化
        """
        self.user_id = user_id
        self.refresh_time = refresh_time

        self.card_deadline = card_deadline
        self.great_card_deadline = great_card_deadline
        self.week_card_deadline = week_card_deadline
        self.forever_card_deadline = forever_card_deadline
        self.small_week_card_deadline = small_week_card_deadline

        self.order_normal_ids = order_normal_ids
        self.order_card_ids = order_card_ids
        self.order_package_ids = order_package_ids

        self.pre_order_number = pre_order_number

        self.pay_count = pay_count      #尝试付费次数
        self.pay_amount = pay_amount    #付费金额


    def is_able_to_refresh(self, now):
        """是否可以刷新
        """
        return now >= self.refresh_time


    def refresh(self, now, test = False, multi_count = False, pattern = 1):
        """刷新
        只会刷新礼包类商品
        """
        package_count = int(float(
            data_loader.OtherBasicInfo_dict["pay_package_count"].value))
        package_ids = PayPool().random_package(package_count, test)
        self.order_package_ids = utils.join_to_string(package_ids)

        refresh_gap = int(float(
            data_loader.OtherBasicInfo_dict["pay_refresh_gap"].value))
        self.refresh_time = now + refresh_gap

        #重新刷新月卡（中途添加了新月卡）
        card = []
        for id in data_loader.InitUserBasicInfo_dict[pattern].payBasicId:
            order = PayPool().get(id)
            if order.type == PayPool.ORDER_TYPE_CARD:
                card.append(id)
        self.order_card_ids = utils.join_to_string(card)

        #如果需要支持购买多份同一个product_id但order_id不同的物品
        if multi_count:
            normal_ids = utils.split_to_int(self.order_normal_ids) 
            #如果已有多份的order,先删掉
            multi_count_ids = []
            for id in normal_ids:
                if data_loader.PayBasicInfo_dict[id].productCount > 1:
                    multi_count_ids.append(id)
            for id in multi_count_ids:
                normal_ids.remove(id)

            for id in data_loader.PayBasicInfo_dict:
                info = data_loader.PayBasicInfo_dict[id]
                if info.productCount > 1:
                    normal_ids.append(id)
            
            self.order_normal_ids = utils.join_to_string(normal_ids)

        if test:
            normal = []
            for id in data_loader.PayBasicInfo_dict:
                info = data_loader.PayBasicInfo_dict[id]
                if info.type == PayPool.ORDER_TYPE_NORMAL:
                    if info.productId == 'com.anqu.zwsgApp.zwsg99999999':
                        continue
                    normal.append(id)
                    
            self.order_normal_ids = utils.join_to_string(normal)

        return True


    def try_refresh(self, now, test, multi_count, pattern = 1):
        """尝试刷新
        """
        if self.is_able_to_refresh(now):
            return self.refresh(now, test, multi_count, pattern)
        return True


    def refresh_card(self, now):
        """刷新月卡/周卡
        """
        if now > self.card_deadline:
            self.card_deadline = 0

        if now > self.great_card_deadline:
            self.great_card_deadline = 0

        if now > self.week_card_deadline:
            self.week_card_deadline = 0

        if now > self.forever_card_deadline:
            self.forever_card_deadline = 0

        if now > self.small_week_card_deadline:
            self.small_week_card_deadline = 0


    def add_card(self, card_type, now):
        """添加月卡/周卡
        """
        if card_type == self.TYPE_PAY_CARD:
            day = 30
            self.card_deadline = self._calc_card_deadline(
                    self.card_deadline, day, now)
        elif card_type == self.TYPE_PAY_GREAT_CARD:
            day = 30
            self.great_card_deadline = self._calc_card_deadline(
                    self.great_card_deadline, day, now)
        elif card_type == self.TYPE_PAY_CARD_WEEK:
            day = 7
            self.week_card_deadline = self._calc_card_deadline(
                    self.week_card_deadline, day, now)
        elif card_type == self.TYPE_PAY_CARD_FOREVER:
            day = 3000
            self.forever_card_deadline = self._calc_card_deadline(
                    self.forever_card_deadline, day, now)
        elif card_type == self.TYPE_PAY_CARD_SMALL_WEEK:
            day = 7
            self.small_week_card_deadline = self._calc_card_deadline(
                    self.small_week_card_deadline, day, now)
        else:
            raise Exception("Invalid card type[type=%d]" % card_type)


    def _calc_card_deadline(self, deadline, duration_day, now):
        """计算月卡截止期
        """
        seconds = duration_day * 86400

        if deadline == 0:
            #当前用户无月卡，从今天起始（5点）开始计时
            start = utils.get_start_second(now)
            return start + seconds
        else:
            #当前用户有月卡，延长相应时间
            return deadline + seconds


    def has_card(self, card_type):
        """是否拥有月卡
        Returns:
            True/False: 是否
        """
        if card_type == self.TYPE_PAY_CARD and self.card_deadline > 0:
            return True
        elif card_type == self.TYPE_PAY_GREAT_CARD and self.great_card_deadline > 0:
            return True
        elif card_type == self.TYPE_PAY_CARD_WEEK and self.week_card_deadline > 0:
            return True
        elif card_type == self.TYPE_PAY_CARD_FOREVER and self.forever_card_deadline > 0:
            return True
        elif card_type == self.TYPE_PAY_CARD_SMALL_WEEK and self.small_week_card_deadline > 0:
            return True
        return False


    def get_card_left_day(self, card_type, now):
        """获得月卡剩余天数
        Returns: int 天数
        """
        if card_type == self.TYPE_PAY_CARD:
            return max(0, utils.count_days_diff(now, self.card_deadline))
        elif card_type == self.TYPE_PAY_GREAT_CARD:
            return max(0, utils.count_days_diff(now, self.great_card_deadline))
        elif card_type == self.TYPE_PAY_CARD_WEEK:
            return max(0, utils.count_days_diff(now, self.week_card_deadline))
        elif card_type == self.TYPE_PAY_CARD_FOREVER:
            return max(0, utils.count_days_diff(now, self.forever_card_deadline))
        elif card_type == self.TYPE_PAY_CARD_SMALL_WEEK:
            return max(0, utils.count_days_diff(now, self.small_week_card_deadline))
        return False


    def get_all(self):
        """获得所有可以购买的商品 id
        """
        ids = utils.split_to_int(self.order_normal_ids)
        ids.extend(utils.split_to_int(self.order_card_ids))
        ids.extend(utils.split_to_int(self.order_package_ids))
        return ids


    def pre_order(self, order_number):
        """预订商品
        """
        self.pre_order_number = order_number
        self.pay_count += 1 #尝试付费次数+1


    def pay_order(self, order):
        """完成支付，修改商店中下一件商品信息，支付金额信息
        """
        if order.type == PayPool.ORDER_TYPE_NORMAL:
            store = utils.split_to_int(self.order_normal_ids)
        elif order.type == PayPool.ORDER_TYPE_CARD:
            store = utils.split_to_int(self.order_card_ids)
        elif order.type == PayPool.ORDER_TYPE_PACKAGE:
            store = utils.split_to_int(self.order_package_ids)

        self.pre_order_number = ""
        self.pay_amount += order.truePrice

        #计算下一个可以购买的商品
        id = order.id
        if id in store:
            index = store.index(id)
            if order.nextId == 0:
                store.remove(id)
            else:
                store[index] = order.nextId

            if order.type == PayPool.ORDER_TYPE_NORMAL:
                self.order_normal_ids = utils.join_to_string(store)
            elif order.type == PayPool.ORDER_TYPE_CARD:
                self.order_card_ids = utils.join_to_string(store)
            elif order.type == PayPool.ORDER_TYPE_PACKAGE:
                self.order_package_ids = utils.join_to_string(store)


