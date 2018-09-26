#coding:utf8
"""
Created on 2016-05-17
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 政令值相关逻辑
"""

import math
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.node import NodeInfo


class EnergyInfo(object):
    """政令信息
    """

    def __init__(self, user_id = 0,
            energy = 0, energy_capacity = 0, last_time = 0, 
            next_refresh_time = 0, buy_num = 0, 
            trigger_scout_num = 0, trigger_tax_num = 0, trigger_farm_num = 0,
            trigger_mining_num = 0, trigger_gold_num = 0, trigger_jungle_num = 0,
            trigger_dungeon_num = 0, trigger_visit_num = 0, trigger_search_num = 0, 
            trigger_deep_mining_num = 0, trigger_hermit_num = 0,
            total_trigger_scout_num = 0, daily_use_energy = 0):

        self.user_id = user_id

        #政令值
        self.energy = energy
        self.energy_capacity = energy_capacity #上限
        self.last_time = last_time #上次更新政令值的时间
        self.next_refresh_time = next_refresh_time  #下次刷新的时间

        self.buy_num = buy_num

        self.trigger_scout_num = trigger_scout_num
        self.trigger_tax_num = trigger_tax_num
        self.trigger_farm_num = trigger_farm_num
        self.trigger_mining_num = trigger_mining_num
        self.trigger_gold_num = trigger_gold_num
        self.trigger_jungle_num = trigger_jungle_num
        self.trigger_dungeon_num = trigger_dungeon_num
        self.trigger_visit_num = trigger_visit_num
        self.trigger_search_num = trigger_search_num
        self.trigger_deep_mining_num = trigger_deep_mining_num
        self.trigger_hermit_num = trigger_hermit_num

        #统计
        self.total_trigger_scout_num = total_trigger_scout_num
        self.daily_use_energy = daily_use_energy


    @staticmethod
    def create(user_id, user_level, vip_level, now):
        """初始的政令信息，创建一个新用户时调用
        Args:
            user_id[int]: 用户 id
            user_level[int]: 用户等级
            vip_level[int]: vip 等级
            now[int]: 当前时间戳
        Returns:
            energy[EnergyInfo]
        """
        energy_capacity = int(data_loader.MonarchLevelBasicInfo_dict[user_level].energyLimit)
        energy = energy_capacity
        energy = EnergyInfo(user_id, energy, energy_capacity, now)
        energy.reset(now)

        return energy


    def reset(self, now):
        """重置energy相关信息
        Returns:
            None
        """
        self.buy_num = 0
        self.trigger_scout_num = 0
        self.trigger_tax_num = 0
        self.trigger_farm_num = 0
        self.trigger_mining_num = 0
        self.trigger_gold_num = 0
        self.trigger_jungle_num = 0
        self.trigger_dungeon_num = 0
        self.trigger_visit_num = 0
        self.trigger_search_num = 0
        self.trigger_deep_mining_num = 0
        self.trigger_hermit_num = 0

        tomorrow = now + utils.SECONDS_OF_DAY
        self.next_refresh_time = utils.get_start_second(tomorrow)


    def reset_daily_use_energy(self):
        self.daily_use_energy = 0


    def update_current_energy(self, now):
        """更新当前政令值
        Args:
            now[int]: 当前时间戳
        Returns:
            None
        """
        interval = int(float(data_loader.OtherBasicInfo_dict["gain_energy_interval"].value))
        duration = now - self.last_time
        
        num = duration / interval

        if self.energy < self.energy_capacity:
            #energy未达上限，值才会增加
            energy = self.energy + num
            if energy < self.energy_capacity:
                self.energy = energy
                self.last_time += num * interval
            else:
                self.energy = self.energy_capacity
                self.last_time = now
        else:
            self.last_time = now



    def update_energy_and_capacity(self, user_level):
        """主公升级后，更新政令值和上限值
        """
        energy_capacity = data_loader.MonarchLevelBasicInfo_dict[user_level].energyLimit
        energy_addition = data_loader.MonarchLevelBasicInfo_dict[user_level].energyIncrement

        self.energy_capacity = energy_capacity
        self.energy += energy_addition


    def calc_gold_consume_of_buy_energy(self, vip_level):
        buy_num = self.buy_num + 1
        
        max_num = max(data_loader.EnergyBuyData_dict.keys())
        num = min(max_num, buy_num)
        
        if vip_level < data_loader.EnergyBuyData_dict[num].limitVipLevel:
            return -1
        else:
            return int(data_loader.EnergyBuyData_dict[num].gold)


    def get_energy_num_of_buy(self):
        """获得一次购买的政令值
        """
        return int(float(data_loader.OtherBasicInfo_dict["energy_buy_num"].value))


    def buy_energy(self):
        """购买政令值
        """
        self.buy_num += 1
        
        energy_num = self.get_energy_num_of_buy()
        self.energy += energy_num


    def gain_energy(self, addition):
        """获得政令值
        Args:
            addition[int/float]: 获得政令值
        Returns:
            None
        """
        addition = int(addition)
        assert addition >= 0
        if addition == 0:
            return

        self.energy += addition


    def cost_energy(self, energy_cost, event_type, now):
        """消耗政令值
        Args:
            energy_cost[int]: 消耗数目
        Returns:
            True: 成功
            False: 失败
        """
        assert energy_cost >= 0
        #self.update_current_energy(now)

        if self.energy < energy_cost:
            logger.warning("Not enough energy[own=%d][need=%d]" % (self.energy, energy_cost))
            return False

        self.energy -= energy_cost
        logger.debug("Cost energy[cost=%d][remain=%d]" % (energy_cost, self.energy))
        self.daily_use_energy += energy_cost

        if event_type == NodeInfo.EVENT_TYPE_TAX:
            self.trigger_tax_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_FARM:
            self.trigger_farm_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_MINING:
            self.trigger_mining_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_GOLD:
            self.trigger_gold_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_VISIT:
            self.trigger_visit_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_JUNGLE:
            self.trigger_jungle_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_DUNGEON:
            self.trigger_dungeon_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_SCOUT:
            self.trigger_scout_num += 1
            self.total_trigger_scout_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_SEARCH:
            self.trigger_search_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_DEEP_MINING:
            self.trigger_deep_mining_num += 1
        elif event_type == NodeInfo.EVENT_TYPE_HERMIT:
            self.trigger_hermit_num += 1

        return True


    def calc_energy_consume_of_event(self, event_type):
        """计算事件触发消耗的政令值
        """
        max_num = self._get_event_type_max_index(event_type)
        
        if event_type == NodeInfo.EVENT_TYPE_TAX:
            num = min(max_num, self.trigger_tax_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_FARM:
            num = min(max_num, self.trigger_farm_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_MINING:
            num = min(max_num, self.trigger_mining_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_GOLD:
            num = min(max_num, self.trigger_gold_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_VISIT:
            num = min(max_num, self.trigger_visit_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_JUNGLE:
            num = min(max_num, self.trigger_jungle_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_DUNGEON:
            num = min(max_num, self.trigger_dungeon_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_SCOUT:
            num = min(max_num, self.trigger_scout_num + 1)
 
        elif event_type == NodeInfo.EVENT_TYPE_SEARCH:
            num = min(max_num, self.trigger_search_num + 1)
 
        elif event_type == NodeInfo.EVENT_TYPE_DEEP_MINING:
            num = min(max_num, self.trigger_deep_mining_num + 1)
        
        elif event_type == NodeInfo.EVENT_TYPE_HERMIT:
            num = min(max_num, self.trigger_hermit_num + 1)       
               
        else:
            logger.warning("Wrong event type[type=%d]" % energy_type)
            return None

        key = "%s_%s" % (event_type, num)
        return data_loader.EnergyConsumeData_dict[key].energyCost


    def _get_event_type_max_index(self, event_type):
        """获得某一类事件在EnergyConsumeData表中的最大次数配置
        """
        all_consume_data = data_loader.EnergyConsumeData_dict
        indexes = []
        for key in all_consume_data:
            if event_type == data_loader.EnergyConsumeData_dict[key].eventType:
                indexes.append(data_loader.EnergyConsumeData_dict[key].index)

        return max(indexes)








