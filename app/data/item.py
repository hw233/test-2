#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 战斗相关计算逻辑
"""

import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app import log_formater

def enum(**enums):
    return type('Enum', (), enums)

ItemType = enum(VIP_POINT = 28,
                PACKAGE = 29,
                MONTH_CARD = 30,
                REFRESH_ITEM = 38,
                ANNEAL_ATTACK_NUM_ITEM = 39,
                SOUL_PACKAGE= 43,
                SPEED = 45)

class ItemInfo(object):
    def __init__(self, id = 0, user_id = 0, basic_id = 0, num = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id
        self.num = num


    @staticmethod
    def generate_id(user_id, basic_id):
        id = user_id << 32 | basic_id
        return id


    @staticmethod
    def get_basic_id(id):
        basic_id = id & 0xFFFFFFFF
        return basic_id


    @staticmethod
    def create(user_id, basic_id, num):
        """创建新物品
        Args:
            user_id[int]: 用户 id
            basic_id[int]: 物品的 basic id
            num[int]: 物品的数量
        Returns:
            item[ItemInfo]: 物品信息
        """
        id = ItemInfo.generate_id(user_id, basic_id)
        limit = int(float(data_loader.OtherBasicInfo_dict["MaxItemNum"].value))
        num = min(num, limit)

        item = ItemInfo(id, user_id, basic_id, num)
        return item


    @staticmethod
    def get_corresponding_value(basic_id):
        return data_loader.ItemBasicInfo_dict[basic_id].value


    def acquire(self, num):
        """获得物品（用户已经拥有相同物品）
        不能超过单个物品的数量上限
        Args:
            num[int]: 获得的物品数量
        Returns:
            None
        """
        limit = int(float(data_loader.OtherBasicInfo_dict["MaxItemNum"].value))
        self.num = max(0, min(self.num + num, limit))
        item = (self.basic_id, num, self.num )
        return item


    def consume(self, num):
        """消耗物品
        Args:
            num[int]: 获得的物品数量
        Returns:
            True: 成功
            False: 失败
        """
        if num < 1 or self.num < num:
            logger.warning("Consume item error[num=%d][own num=%d]" % (num, self.num))
            #return False
        self.num -= num
        self.num = max(0, self.num)
        output_items=(self.basic_id, -num, self.num)
        return True, output_items


    def is_starsoul_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_starsoul"].value)):
            return True
        return False


    def is_money_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_money"].value)):
            return True
        return False


    def is_food_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_food"].value)):
            return True
        return False


    def is_gold_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_gold"].value)):
            return True
        return False


    def is_resource_package(self):
        if self.is_gold_item() or self.is_food_item() or self.is_money_item():
            return True
        return False


    def is_monarch_exp(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_monarchExp"].value)):
            return True
        return False


    def is_hero_exp(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_exp"].value)):
            return True
        return False


    def is_herolist_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_herolist"].value)):
            return True
        return False

    def is_random_package_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_random_package"].value)):
            return True
        return False

    def is_equipment_enchant_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_equipment_enchant"].value)):
            return True
        return False


    def is_equipment_upgrade_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_equipment_upgrade"].value)):
            return True
        return False


    def is_equipment_scroll_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_equipment_scroll"].value)):
            return True
        return False


    def is_equipment_slice_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_equipment_slice"].value)):
            return True
        return False


    def is_equipment_stone_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if (type == int(float(data_loader.OtherBasicInfo_dict["item_stone_one"].value))
                or type == int(float(data_loader.OtherBasicInfo_dict["item_stone_two"].value))
                or type == int(float(data_loader.OtherBasicInfo_dict["item_stone_three"].value))
                or type == int(float(data_loader.OtherBasicInfo_dict["item_stone_four"].value))
                or type == int(float(data_loader.OtherBasicInfo_dict["item_stone_five"].value))
                or type == int(float(data_loader.OtherBasicInfo_dict["item_stone_six"].value))):
            return True

        return False
    
    
    def is_appoint_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_appoint"].value)):
            return True
        return False


    def is_draw_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_draw"].value)):
            return True
        return False


    def is_protect_city_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_protect_city"].value)):
            return True
        return False


    def is_protect_resource_node_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_protect_resource_node"].value)):
            return True
        return False


    def is_increase_node_money_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_increase_node_money"].value)):
            return True
        return False


    def is_increase_node_food_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_increase_node_food"].value)):
            return True
        return False


    def is_increase_node_material_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(
            data_loader.OtherBasicInfo_dict["item_increase_node_material"].value)):
            return True
        return False


    def is_legendcity_buff_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(
            data_loader.OtherBasicInfo_dict["item_legendcity_city_buff"].value)):
            return True
        return False


    def is_union_battle_drum_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(
            data_loader.OtherBasicInfo_dict["item_drum"].value)):
            return True
        return False


    def is_energy_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_energy"].value)):
            return True
        return False


    def is_evolution_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == int(float(data_loader.OtherBasicInfo_dict["item_evolution"].value)):
            return True
        return False

    def is_vip_point_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == ItemType.VIP_POINT:
            return True
        return False

    def is_package_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == ItemType.PACKAGE:
            return True
        return False

    def is_month_card_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == ItemType.MONTH_CARD:
            return True
        return False


    def is_refresh_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == ItemType.REFRESH_ITEM:
            return True
        return False


    def is_anneal_attack_num_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == ItemType.ANNEAL_ATTACK_NUM_ITEM:
            return True
        return False


    def is_soul_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == ItemType.SOUL_PACKAGE:
            return True
        return False


    def is_speed_item(self):
        type = data_loader.ItemBasicInfo_dict[self.basic_id].type
        if type == ItemType.SPEED:
            return True
        return False


    def sell(self, num):
        """出售物品，获取金钱
        Args:
            num[int] 使用的数量
        Returns:
            获得金钱数量
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return None
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "sell", log_formater.SELL, item)
        logger.notice(log)
        money = data_loader.ItemBasicInfo_dict[self.basic_id].sale_money_price * num
        return money


    def use_legendcity_buff_item(self):
        """使用史实城 buff 物品
        Returns:
            成功/失败
        """
        if not self.is_legendcity_buff_item():
            logger.warning("Not legendcity buff item[basic id=%d]" % self.basic_id)
            return False
        consume = self.consume(1)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)                                                                                                                                                      
        log = log_formater.output_item(self, "use legendcity buff", log_formater.LEGENDCITY_BUFF, item)
        logger.notice(log)

        return True


    def use_exp_item(self, consume_num):
        """使用英雄经验丹物品
        1 拥有的物品数量必须大于消耗的数量，消耗的数量必须大于0
        2 物品必须是经验丹
        3 消耗掉经验丹，计算可以获得的经验值
        Args:
            consume_num[int] 消耗的数量
        Returns:
            使用经验丹之后获得的经验值
            计算失败返回 None
        """
        if not self.is_hero_exp():
            logger.warning("Not hero exp item[basic id=%d]" % self.basic_id)
            return None
        consume = self.consume(consume_num)
        if not consume[0]:
            return None
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use exp item", log_formater.EXP_ITEM, item)
        logger.notice(log)

        exp = data_loader.ItemBasicInfo_dict[self.basic_id].value * consume_num
        return exp,consume[1]


    def use_monarch_exp_item(self, consume_num):
        """
        使用主公经验丹
        """
        if not self.is_monarch_exp():
            logger.warning("Not monarch exp item[basic id=%d]" % self.basic_id)
            return None
        consume = self.consume(consume_num)
        if not consume[0]:
            return None
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use monarch exp item", log_formater.MONARCH_EXP_ITEM, item)
        logger.notice(log)

        exp = data_loader.ItemBasicInfo_dict[self.basic_id].value * consume_num
        return exp


    def use_speed_item(self, consume_num):
        """
        使用加速物品
        """
        if not self.is_speed_item():
            logger.warning("Not speed item[basic id=%d]" % self.basic_id)
            return None
        consume = self.consume(consume_num)
        if not consume[0]:
            return None
	output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use speed item", log_formater.SPEED_ITEM, item)
        logger.notice(log)
        speed_time = data_loader.ItemBasicInfo_dict[self.basic_id].value * consume_num
        return speed_time


    def use_appoint_item(self, consume_num):
        """
        使用委任物品（虎符）
        """
        if not self.is_appoint_item():
            logger.warning("Not appoint item[basic id=%d]" % self.basic_id)
            return False
        consume = self.consume(consume_num)
        if not consume[0]:
            return False
	output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use appoint item", log_formater.APPOINT_ITEM, item)
        logger.notice(log)
        return True


    def use_draw_item(self, consume_num):
        """
        使用搜索券
        """
        if not self.is_draw_item():
            logger.warning("Not draw item[basic id=%d]" % self.basic_id)
            return False
        consume = self.consume(consume_num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use draw item", log_formater.DRAW_ITEM, item)
        logger.notice(log)

        return True


    def use_refresh_item(self, consume_num):
        """
        使用商铺刷新代币
        """
        if not self.is_refresh_item():
            logger.warning("Not refresh item[basic id=%d]" % self.basic_id)
            return False

        consume = self.consume(consume_num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use refresh item", log_formater.REFRESH_ITEM, item)
        logger.notice(log)
        return True


    def use_starsoul_item(self, consume_num):
        """使用将魂石物品
        1 判断物品是不是将魂石
        2 判断将魂石是不是和英雄对应，如果传入的 hero 为None，不进行此判断
        3 消耗掉将魂石，计算将魂石可以获得的将魂数量
        Args:
            consume_num[int] 消耗的数量
        Returns:
            使用将魂石之后可以获得的英雄的 basic id 和将魂数量，返回元组(basic_id, num)
            计算失败返回 None
        """
        if not self.is_starsoul_item():
            logger.warning("Not starsoul item[basic id=%d]" % self.basic_id)
            return None
        consume = self.consume(consume_num)
        if not consume[0]:
            return None
	    output_items = []
            output_items.append("[item=")
            output_items.append(utils.join_to_string(list(consume[1])))
            output_items.append("]")
            item = ''.join(output_items)
            log = log_formater.output_item(self, "use starsoul item", log_formater.STARSOUL_ITEM, item)
            logger.notice(log)

        corresponding_hero_basic_id = data_loader.ItemBasicInfo_dict[self.basic_id].value
        return (corresponding_hero_basic_id, consume_num)

    def resolve_starsoul_item(self, consume_num):
        """分解将魂石,返还精魄"""
        if not self.is_starsoul_item():
            logger.warning("Not starsoul item[basic_id=%d]" % self.basic_id)
            return None

        consume = self.consume(consume_num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "resolve starsoul item", log_formater.RESOLVE_STARSOUL_ITEM, item)
        logger.notice(log)
        soul = self.get_soul_num(self.basic_id) * consume_num
        return soul
        
    def use_evolution_item(self, consume_num):
        """使用突破石物品
        1 判断物品是不是突破石
        2 消耗掉将魂石，计算将魂石可以获得的将魂数量
        Args:
            consume_num[int] 消耗的数量
        Returns:
            计算失败返回 False
        """
        if not self.is_evolution_item():
            logger.warning("Not evolution item[basic id=%d]" % self.basic_id)
            return False

        consume = self.consume(consume_num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use evolution item", log_formater.EVOLUTION_ITEM, item)
        logger.notice(log)
        return True


    def use_money_item(self, num):
        """使用钱包物品
        Args:
            num[int] 使用的数量
        Returns:
            获得金钱数量
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use money item", log_formater.MONEY_ITEM, item)
        logger.notice(log)
        if not self.is_money_item():
            logger.warning("Not money item[basic id=%d]" % self.basic_id)
            return None

        money = data_loader.ItemBasicInfo_dict[self.basic_id].value * num
        return money


    def use_food_item(self, num):
        """使用粮包物品
        Args:
            item[ItemInfo out] 粮包物品
            num[int] 使用的数量
        Returns:
            获得粮草数量
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use food item", log_formater.FOOD_ITEM, item)
        logger.notice(log)
        if not self.is_food_item():
            logger.warning("Not food item[basic id=%d]" % self.basic_id)
            return None

        food = data_loader.ItemBasicInfo_dict[self.basic_id].value * num
        return food


    def use_gold_item(self, num):
        """使用元宝袋物品
        Args:
            num[int] 使用的数量
        Returns:
            获得元宝数量
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use gold item", log_formater.GOLD_ITEM, item)
        logger.notice(log)
        if not self.is_gold_item():
            logger.warning("Not gold item[basic id=%d]" % self.basic_id)
            return None

        gold = data_loader.ItemBasicInfo_dict[self.basic_id].value * num
        return gold

    def use_soul_item(self, num):
        """使用精魄包物品"""
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use soul item", log_formater.SOUL_ITEM, item)
        logger.notice(log)
        if not self.is_soul_item():
            logger.warning("Not soul item[basic id=%d]" % self.basic_id)
            return None

        soul = data_loader.ItemBasicInfo_dict[self.basic_id].value * num
        return soul

    def use_energy_item(self, num):
        """使用政令符物品
        Args:
            num[int] 使用的数量
        Returns:
            获得政令值
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use energy item", log_formater.ENERGY_ITEM, item)
        logger.notice(log)
        if not self.is_energy_item():
            logger.warning("Not energy item[basic id=%d]" % self.basic_id)
            return None

        energy = data_loader.ItemBasicInfo_dict[self.basic_id].value * num
        return energy


    def use_vip_point_item(self, num):
        """使用vip物品
        Args:
            num[int] 使用的数量
        Returns:
            获得vip点数 
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use vip item", log_formater.VIP_ITEM, item)
        logger.notice(log)
        if not self.is_vip_point_item():
            logger.warning("Not vip point item[basic id=%d]" % self.basic_id)
            return None

        vip_point = data_loader.ItemBasicInfo_dict[self.basic_id].value * num
        return vip_point


    def use_package_item(self, num):
        """使用vip物品
        Args:
            num[int] 使用的数量
        Returns:
            PackageBasicInfo 
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use package item", log_formater.PACKAGE_ITEM, item)
        logger.notice(log)
        if not self.is_package_item():
            logger.warning("Not package item[basic id=%d]" % self.basic_id)
            return None

        package_id = data_loader.ItemBasicInfo_dict[self.basic_id].value
        return data_loader.PackageBasicInfo_dict[package_id]


    def use_month_card_item(self, num):
        """使用vip物品
        Args:
            num[int] 使用的数量
        Returns:
            月卡类型
            计算失败返回 None
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use month card item", log_formater.MONTHCARD_ITEM, item)
        logger.notice(log)
        if not self.is_month_card_item():
            logger.warning("Not vip point item[basic id=%d]" % self.basic_id)
            return None

        return data_loader.ItemBasicInfo_dict[self.basic_id].value


    def use_equipment_enchant_item(self, num, enchant_type):
        """使用装备精炼物品
        Args:
            num[int]: 使用的数量
            enchant_type[int]: 需要的精炼值类型
        Returns:
            获得的精炼值
            <0, 表示失败
        """
        consume = self.consume(num)
        if not consume[0]:
            return False
        if not self.is_equipment_enchant_item():
            logger.warning("Not gold item[basic id=%d]" % self.basic_id)
            return -1

        etype = data_loader.ItemBasicInfo_dict[self.basic_id].value2
        if etype != enchant_type:
            logger.warning("Unmatch enchant type[type=%d][need type=%d]" %
                    (etype, enchant_type))
            return -1

        point = data_loader.ItemBasicInfo_dict[self.basic_id].value * num
        return point, consume[1]


    def use_herolist_item(self, hero_list, item_list, consume_num):
        """使用国士名册
        1 一次使用一个
        Args:
            item[ItemInfo out]: 国士名册
            hero_list[list((int, num)) out]: 获得的英雄 id 和数量
            item_list[list((int, num)) out]: 获得的物品 id 和数量
        Returns:
            使用成功返回 True
            失败返回 False
        """
        if not self.is_herolist_item() and not self.is_random_package_item():
            logger.warning("Not herolist or random package item[basic id=%d]" % self.basic_id)
            return False

        consume = self.consume(consume_num)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use herolist item", log_formater.HEROLIST_ITEM, item)
        logger.notice(log)
        herolist_id = data_loader.ItemBasicInfo_dict[self.basic_id].value

        min_point = data_loader.HerolistBasicInfo_dict[herolist_id].minPoints 
        max_point = data_loader.HerolistBasicInfo_dict[herolist_id].maxPoints
        ids = data_loader.HerolistBasicInfo_dict[herolist_id].idlist
        assert len(ids) >= 1

        for index in range(consume_num):
            roll_list = []
            for id in ids:
                weight = data_loader.HerolistDetails_dict[id].weight
                point = data_loader.HerolistDetails_dict[id].points
                roll_list.append((weight, point, id))

            win = ItemInfo._roll_herolist(roll_list, min_point, max_point)
            if win is None:
                logger.warning("Roll herolist failed[herolist id=%d]" % herolist_id)
                return False

            for id in win:
                hero_id = data_loader.HerolistDetails_dict[id].heroBasicId
                item_id = data_loader.HerolistDetails_dict[id].itemBasicId
                item_num = data_loader.HerolistDetails_dict[id].itemNum
                if hero_id != 0:
                    assert item_id == 0
                    hero_list.append((hero_id, win[id]))
                else:
                    assert item_id != 0
                    item_list.append((item_id, win[id] * item_num))

        return True


    def use_equipment_stone_item(self):
        """使用装备的宝石
        Returns:
            成功/失败
        """
        if not self.is_equipment_stone_item():
            logger.warning("Not equipment stone item[basic id=%d]" % self.basic_id)
            return False

        consume = self.consume(1)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use stone item", log_formater.STONE_ITEM, item)
        logger.notice(log)
        return True


    def use_anneal_attack_num_item(self):
        """使用试炼场攻击次数购买符
        Returns:
            成功/失败
        """
        if not self.is_anneal_attack_num_item():
            logger.warning("Not anneal attack num item[basic id=%d]" % self.basic_id)
            return False

        consume = self.consume(1)
        if not consume[0]:
            return False
        output_items = []
        output_items.append("[item=")
        output_items.append(utils.join_to_string(list(consume[1])))
        output_items.append("]")
        item = ''.join(output_items)
        log = log_formater.output_item(self, "use anneal item", log_formater.ANNEAL_ITEM, item)
        logger.notice(log)
        return True


    @staticmethod
    def _roll_herolist(candidate, min_point, max_point):
        """国士名册随机选择过程
        1 在 candidate 中随机选择
        2 最终选择的项，需要保证 point 之和在[min_point, max_point]之间
        3 选择分为多轮，每一轮中 candidate 被选择的概率 = weight / total_weight
        4 完成一轮选择后，去掉非法的 candidate（如果选中，会导致 points 之和超过 max_point）
          然后更新选中概率，在所有的 candidate 中继续进行选择
        Args:
            candidate[list((weight, point, id))]: 参与 roll 的候选项
            min_point[int]: 最小点数
            max_point[int]: 最大点数
        Returns:
            dict: {id, num} 赢得的项，相同 id 的项会合并
            计算失败返回 None
        """
        if not candidate:
            logger.warning("Invalid data: empty candidate")
            return None

        #检查数据合法性
        total_weight = 0
        total_point = 0
        item_min_point = max_point
        item_max_point = 0
        for item in candidate:
            total_weight += item[0]
            total_point += item[1]
            if item[1] < item_min_point:
                item_min_point = item[1]
            if item[1] > item_max_point:
                item_max_point = item[1]
            # logger.debug("candidate=%d|w(%d)|p(%d)" % (item[2], item[0], item[1]))

        #min_point <= max_point
        #total_point >= min_point 一定可以达到 point 要求
        #item_max_point <= max_point 所有的 item 都有被选中的机会
        if (min_point > max_point or
                total_point < min_point or
                item_max_point > max_point):
            logger.warning("Invalid data[range:%d-%d][total_point=%d][item point range:%d-%d]" %
                    (min_point, max_point, total_point, item_min_point, item_max_point))
            return None

        win = {}
        def add_win(id, win):
            if id in win:
                win[id] += 1
            else:
                win[id] = 1

        point_sum = 0

        #这里的 roll 相当于一个轮盘赌
        begin = 0 # roll start
        end = total_weight - 1 # roll end
        random.seed()
        while point_sum < min_point:
            roll = random.randint(begin, end)
            # logger.debug("[roll=%d][%d-%d]" % (roll, begin, end))

            weight_sum = 0
            choose = None
            for item in candidate:
                weight_sum += item[0]
                choose = item
                if roll < weight_sum:
                    break

            assert choose is not None
            add_win(choose[2], win)
            # logger.debug("[win=%d|w(%d)|p(%d)]" % (choose[2], choose[0], choose[1]))

            point_sum += choose[1]
            left_point = max_point - point_sum
            # logger.debug("[left_point=%d]" % left_point)
            del_list = []
            for item in candidate:
                #item[0] : item_weight.  item[1] : item point
                if item[1] > left_point:
                    end -= item[0]
                    del_list.append(item)

            for item in del_list:
                candidate.remove(item)
                if len(candidate) == 0:
                    # logger.debug("Candidate is empty")
                    assert len(win) > 0
                    return win

        assert len(win) > 0
        return win

    @staticmethod
    def get_soul_num(basic_id):
        """获取将魂石分解的精魄数量"""
        level_dict = {
            1:"hero_stone_to_souls_3",
            2:"hero_stone_to_souls_3",
            3:"hero_stone_to_souls_3",
            4:"hero_stone_to_souls_4",
            5:"hero_stone_to_souls_5"
        }
        item_level = data_loader.ItemBasicInfo_dict[basic_id].level
        return int(float(data_loader.OtherBasicInfo_dict[level_dict[item_level]].value))
