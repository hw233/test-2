#coding:utf8
"""
Created on 2016-05-24
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 祈福相关
"""

import random
import math
import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.core import reward as reward_module

CARD_NUM = 9

class PrayInfo(object):
    """祈福信息
    """
    PRAY_INVALID = 0
    PRAY_RESOURCE = 1
    PRAY_HERO = 2
    PRAY_MATERIAL = 3
    PRAY_ALL = 4

    def __init__(self, user_id = 0,
            current_pray_type = PRAY_INVALID,
            resource_pray_num = 0, hero_pray_num = 0, material_pray_num = 0,
            resource_refresh_num = 0, hero_refresh_num = 0, material_refresh_num = 0,
            next_refresh_time = 0,
            items_id = "", items_num = "",
            initial_list = "", choose_list = ""):

        self.user_id = user_id

        #祈福数据
        self.current_pray_type = current_pray_type
        self.resource_pray_num = resource_pray_num
        self.hero_pray_num = hero_pray_num
        self.material_pray_num = material_pray_num
         #原为起伏刷新的次数，后来刷新取消，改成使用元宝强制起伏。现意为强制起伏的次数
        self.resource_refresh_num = resource_refresh_num
        self.hero_refresh_num = hero_refresh_num
        self.material_refresh_num = material_refresh_num
        self.next_refresh_time = 0

        #祈福状态
        self.items_id = items_id
        self.items_num = items_num
        self.initial_list = initial_list
        self.choose_list = choose_list


    @staticmethod
    def create(user_id, now):
        """初始的祈福信息，创建一个新用户时调用
        Args:
            user_id[int]: 用户 id
            now[int]: 当前时间戳
        Returns:
            pray[PrayInfo]
        """
        pray = PrayInfo(user_id, now)
        pray.reset(now)

        return pray


    def reset(self, now):
        """重置energy相关信息
        Returns:
            None
        """
        self.resource_pray_num = 0
        self.hero_pray_num = 0
        self.material_pray_num = 0
        self.resource_refresh_num = 0
        self.hero_refresh_num = 0
        self.material_refresh_num = 0

        self.calc_next_refresh_time(now)

        return True


    def calc_next_refresh_time(self, now):
        tomorrow = now + utils.SECONDS_OF_DAY
        self.next_refresh_time = utils.get_start_second(tomorrow)


    def is_empty(self):
        """当前是否有祈福数据
        """
        return self.current_pray_type == self.PRAY_INVALID


    def is_able_to_reset(self, now):
        """判断当前是否可以重置
        """
        if self.next_refresh_time <= now:
            return True
        else:
            return False


    def is_able_to_pray(self, type, building_level):
        """判断祈福次数是否还够用
        """
        key = "%s_%s" % (type, building_level)
        pray_num_limit = int(data_loader.PrayNumBasicInfo_dict[key].prayNumLimit)

        if type == self.PRAY_RESOURCE:
            pray_num = self.resource_pray_num
        elif type == self.PRAY_HERO:
            pray_num = self.hero_pray_num
        elif type == self.PRAY_MATERIAL:
            pray_num = self.material_pray_num
        else:
            return False

        if pray_num < pray_num_limit:
            return True
        else:
            return False


    def calc_pray_food_cost(self, type, building_level):
        """计算祈福的粮草花费
        """
        #第一次祈福免费
        if type == self.PRAY_RESOURCE:
            if self.resource_pray_num == 0 and self.resource_refresh_num == 0:
                return 0
        elif type == self.PRAY_HERO:
            if self.hero_pray_num == 0 and self.hero_refresh_num == 0:
                return 0
        elif type == self.PRAY_MATERIAL:
            if self.material_pray_num == 0 and self.material_refresh_num == 0:
                return 0

        key = "%s_%s" % (type, building_level)
        return data_loader.PrayCostBasicInfo_dict[key].cost

    def calc_force_pray_gold_cost(self, type, vip_level):
        """计算使用元宝强制起伏的元宝消费"""
        return self.calc_refresh_gold_cost(type, vip_level)

    def calc_refresh_gold_cost(self, type, vip_level):
        """计算刷新祈福的元宝花费
        """
        max_refresh_num = self._get_refresh_max_num(type)

        if type == self.PRAY_RESOURCE:
            refresh_num = min(self.resource_refresh_num + 1, max_refresh_num)
        elif type == self.PRAY_HERO:
            refresh_num = min(self.hero_refresh_num + 1, max_refresh_num)
        elif type == self.PRAY_MATERIAL:
            refresh_num = min(self.material_refresh_num + 1, max_refresh_num)
        else:
            return None

        key = "%s_%s" % (type, refresh_num)
        if vip_level < data_loader.PrayRefreshCostBasicInfo_dict[key].limitVipLevel:
            return None
        else:
            return data_loader.PrayRefreshCostBasicInfo_dict[key].gold


    def calc_choose_card_use_item(self):
        """计算翻牌时的祈福令消耗
        """
        choose_list = utils.split_to_int(self.choose_list)
        index = len(choose_list) + 1
        return (int(data_loader.ChooseCardCostBasicInfo_dict[index].itemId),
                int(data_loader.ChooseCardCostBasicInfo_dict[index].costNum))


    def pray(self, type, items, cost_gold=0):
        """祈福
        Args:
            type(int) : 祈福类型
            building_level : 寺庙等级
            items(list(basic_id, num)) : 祈福的物品列表
        """
        assert len(items) == CARD_NUM

        self.current_pray_type = type
        if cost_gold > 0:
            if type == self.PRAY_RESOURCE:
                self.resource_refresh_num += 1
            elif type == self.PRAY_HERO:
                self.hero_refresh_num += 1
            elif type == self.PRAY_MATERIAL:
                self.material_refresh_num += 1
            else:
                return False
        else:
            if type == self.PRAY_RESOURCE:
                self.resource_pray_num += 1
            elif type == self.PRAY_HERO:
                self.hero_pray_num += 1
            elif type == self.PRAY_MATERIAL:
                self.material_pray_num += 1
            else:
                return False

        items_id = []
        items_num = []
        for item in items:
            items_id.append(item[0])
            items_num.append(item[1])
        self.items_id = utils.join_to_string(items_id)
        self.items_num = utils.join_to_string(items_num)

        index = [0,1,2,3,4,5,6,7,8]
        random.shuffle(index)
        self.initial_list = utils.join_to_string(index)
        self.choose_list = ""

        return True


    @staticmethod
    def is_item_pray_multi(basic_id):
        """判断物品是否是祈福翻倍物品
        """
        type = data_loader.ItemBasicInfo_dict[basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_pray_multi"].value)):
            return True
        else:
            return False


    def get_pre_multi_num(self):
        """获取之前紧邻的翻倍加倍物品
        """
        items_id = utils.split_to_int(self.items_id)
        choose_list = utils.split_to_int(self.choose_list)
        pre_index = len(choose_list) - 2

        multi_num = 0
        while pre_index >= 0:
            item_basic = data_loader.ItemBasicInfo_dict[items_id[pre_index]]
            if PrayInfo.is_item_pray_multi(item_basic.id):
                multi_num += int(item_basic.value)
            else:
                break

            pre_index -= 1

        if multi_num == 0:
            return 1
        else:
            return multi_num


    def get_choose_card_num(self):
        """获取已经翻牌子的次数
        """
        choose_list = utils.split_to_int(self.choose_list)
        return len(choose_list)


    def choose_card(self, choose_index):
        """翻牌
        """
        items_id = utils.split_to_int(self.items_id)
        items_num = utils.split_to_int(self.items_num)
        choose_list = utils.split_to_int(self.choose_list)

        if choose_index in choose_list:
            logger.warning("index has been choosed[index=%d]" % choose_index)
            return None

        current_index = len(choose_list) - 1
        next_item_index = current_index + 1
        choose_list.append(choose_index)
        self.choose_list = utils.join_to_string(choose_list)

        multi = self.get_pre_multi_num() #查找前述物品是否有祈福翻倍的
        return (items_id[next_item_index], items_num[next_item_index] * multi)


    def refresh(self, type):
        """刷新祈福次数
        """
        if type == self.PRAY_RESOURCE:
            self.resource_pray_num = 0
            self.resource_refresh_num += 1
        elif type == self.PRAY_HERO:
            self.hero_pray_num = 0
            self.hero_refresh_num += 1
        elif type == self.PRAY_MATERIAL:
            self.material_pray_num = 0
            self.material_refresh_num += 1
        else:
            return False

        return True


    def give_up(self):
        """放弃
        """
        self.current_pray_type = self.PRAY_INVALID

        self.items_id = ""
        self.items_num = ""
        self.initial_list = ""
        self.choose_list = ""

        return True


    def is_need_broadcast(self):
        """最后一次祈福结束，且前一次是翻倍时会触发广播
        """
        if (self.get_choose_card_num() == CARD_NUM and
                self.get_pre_multi_num() > 1):
            return True
        else:
            return False


    def create_broadcast_content(self, user):
        """创建广播信息
        """
        items_id = utils.split_to_int(self.items_id)
        items_num = utils.split_to_int(self.items_num)
        multi_num = self.get_pre_multi_num()
        num = items_num[-1] * multi_num

        broadcast_id = int(float(data_loader.OtherBasicInfo_dict["broadcast_id_pray"].value))
        mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
        life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
        template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
        priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

        content = template.replace("#str#", base64.b64decode(user.name), 1)
        content = content.replace("#str#", str(num), 1)
        content = content.replace("#str#", ("@%s@" %
            data_loader.ItemBasicInfo_dict[items_id[-1]].nameKey.encode("utf-8")), 1)

        return (mode_id, priority, life_time, content)


    def _get_refresh_max_num(self, type):
        """获得某一类祈福在表中配置的最大刷新次数
        """
        all_refresh_data = data_loader.PrayRefreshCostBasicInfo_dict
        refresh_nums = []
        for key in all_refresh_data:
            if type == data_loader.PrayRefreshCostBasicInfo_dict[key].type:
                refresh_nums.append(data_loader.PrayRefreshCostBasicInfo_dict[key].refreshNum)

        return max(refresh_nums)

