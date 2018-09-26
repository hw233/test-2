#coding:utf8
"""
Created on 2016-08-26
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 试炼场相关逻辑
"""

import math
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.node import NodeInfo


class AnnealInfo(object):
    """试炼信息
    """

    NORMAL_MODE = 1
    HARD_MODE = 2

    SWEEP_DIRECTION_NONE = 0
    SWEEP_DIRECTION_WEAPON = 1
    SWEEP_DIRECTION_ARMOR = 2
    SWEEP_DIRECTION_TREASURE = 3

    LEVEL_NUM_PER_FLOOR = 6    #每层的关数

    ANNEAL_RIVAL_BASE_ID = 200000

    def __init__(self, user_id = 0,
            attack_num = 0, attack_num_capacity = 0, last_time = 0, 
            next_refresh_time = 0, buy_num = 0,
            normal_floor = 1, normal_level = 1, 
            normal_level_finished = False, normal_reward_received = False,
            hard_floor = 1, hard_level = 1, 
            hard_level_finished = False, hard_reward_received = False,
            current_type = 0, current_floor = 0, current_level = 0,
            current_start_time = 0,
            sweep_floor = 0, sweep_direction = 0,
            sweep_teams_index = '', sweep_heroes_id = '', 
            sweep_total_time = 0, sweep_start_time = 0):

        self.user_id = user_id

        #攻击次数
        self.attack_num = attack_num
        self.attack_num_capacity = attack_num_capacity #上限
        self.last_time = last_time #上次更新攻击次数的时间
        self.next_refresh_time = next_refresh_time  #下次刷新的时间
        self.buy_num = buy_num    #攻击购买次数

        #试炼进度
        self.normal_floor = normal_floor
        self.normal_level = normal_level
        self.normal_level_finished = normal_level_finished
        self.normal_reward_received = normal_reward_received    #过关奖励是否领取
        self.hard_floor = hard_floor
        self.hard_level = hard_level
        self.hard_level_finished = hard_level_finished
        self.hard_reward_received = hard_reward_received    #过关奖励是否领取

        #当前试炼攻击情况
        self.current_type = current_type
        self.current_floor = current_floor
        self.current_level = current_level
        self.current_start_time = current_start_time    #开打时间

        #扫荡
        self.sweep_floor = sweep_floor
        self.sweep_direction = sweep_direction
        self.sweep_teams_index = sweep_teams_index
        self.sweep_heroes_id = sweep_heroes_id
        self.sweep_total_time = sweep_total_time
        self.sweep_start_time = sweep_start_time
        self.sweep_mode = self.NORMAL_MODE #扫荡的难度,普通或是困难
        self.sweep_attack_num = 0
        self.sweep_at_least = False

        #困难模式的次数限制
        self.hard_attack_num = ""
        self.hard_reset_num = ""


    @staticmethod
    def create(user_id, now):
        """初始的试炼信息
        Args:
            user_id[int]: 用户 id
            now[int]: 当前时间戳
        Returns:
            anneal[AnnealInfo]
        """
        attack_num_capacity = int(float(data_loader.AnnealConfInfo_dict["limit_attack_Num"].value))
        attack_num = attack_num_capacity
        anneal = AnnealInfo(user_id, attack_num, attack_num_capacity, now)
        anneal.reset(now)

        anneal_max_floor = int(float(data_loader.AnnealConfInfo_dict['anneal_max_floor'].value))
        array = [0] * anneal_max_floor
        anneal.hard_attack_num = utils.join_to_string(array)
        anneal.hard_reset_num = utils.join_to_string(array)

        return anneal


    def generate_anneal_node_id(self):
        """试炼场发生战斗的node id (在node为0的主城发生战斗)
        """
        ID_ANNEAL = 0
        id = self.user_id << 32 | ID_ANNEAL
        return id


    def generate_anneal_rival_id(self, type):
        """生成rival id （简单模式和困难模式，各对应一个rival）
        """
        return self.user_id << 32 | (self.ANNEAL_RIVAL_BASE_ID + type)


    def get_anneal_enemy_level(self, type, floor, level):
        key = "%d_%d" % (floor, level)
        
        if type == self.NORMAL_MODE:
            enemy_id = data_loader.AnnealLevelInfo_dict[key].normalEnemyId
        elif type == self.HARD_MODE:
            enemy_id = data_loader.AnnealLevelInfo_dict[key].hardEnemyId

        return data_loader.AnnealEnemyBasicInfo_dict[enemy_id].level


    def reset(self, now):
        """重置anneal相关信息
        Returns:
            None
        """
        self.buy_num = 0
        
        anneal_max_floor = int(float(data_loader.AnnealConfInfo_dict['anneal_max_floor'].value))
        array = [0] * anneal_max_floor
        self.hard_attack_num = utils.join_to_string(array)
        self.hard_reset_num = utils.join_to_string(array)

        tomorrow = now + utils.SECONDS_OF_DAY
        self.next_refresh_time = utils.get_start_second(tomorrow)


    def update_current_attack_num(self, now):
        """更新当前攻击次数
        Args:
            now[int]: 当前时间戳
        Returns:
            None
        """
        interval = int(float(data_loader.AnnealConfInfo_dict["gain_attackNum_interval"].value))
        duration = now - self.last_time
        
        num = duration / interval

        if self.attack_num < self.attack_num_capacity:
            #attack_num未达上限，值才会增加
            attack_num = self.attack_num + num
            if attack_num < self.attack_num_capacity:
                self.attack_num = attack_num
                self.last_time += num * interval
            else:
                self.attack_num = self.attack_num_capacity
                self.last_time = now
        else:
            self.last_time = now


    def modify_progress(self, type, floor, level, is_finished):
        """修改进度
        """
        if type == self.NORMAL_MODE:
            self.normal_floor = floor
            self.normal_level = level
            self.normal_level_finished = is_finished
            self.normal_reward_received = False
        elif type == self.HARD_MODE:
            self.hard_floor = floor
            self.hard_level = level
            self.hard_level_finished = is_finished
            self.hard_reward_received = False


    def calc_gold_consume_of_buy_attack_num(self, vip_level):
        buy_num = self.buy_num + 1
        
        max_num = max(data_loader.AnnealAttackNumBuyData_dict.keys())
        num = min(max_num, buy_num)
        
        if vip_level < data_loader.AnnealAttackNumBuyData_dict[num].limitVipLevel:
            return -1
        else:
            return int(data_loader.AnnealAttackNumBuyData_dict[num].gold)


    def get_attack_num_of_buy(self):
        """获得一次购买的攻击次数
        """
        return int(float(data_loader.AnnealConfInfo_dict["attack_buy_num"].value))


    def buy_attack_num(self):
        """购买攻击次数
        """
        self.buy_num += 1
        
        buy_attack_num = self.get_attack_num_of_buy()
        self.attack_num += buy_attack_num


    def gain_attack_num(self, addition):
        """获得攻击次数
        Args:
            addition[int/float]: 获得攻击次数
        Returns:
            None
        """
        addition = int(addition)
        assert addition >= 0
        if addition == 0:
            return

        self.attack_num += addition


    def cost_attack_num(self, attack_num_cost):
        """消耗攻击次数
        Args:
            attack_num_cost[int]: 消耗数目
        Returns:
            True: 成功
            False: 失败
        """
        assert attack_num_cost >= 0

        if self.attack_num < attack_num_cost:
            logger.warning("Not enough attack num[own=%d][need=%d]" % (self.attack_num, attack_num_cost))
            return False

        self.attack_num -= attack_num_cost
        logger.debug("Cost attack num[cost=%d][remain=%d]" % (attack_num_cost, self.attack_num))

        return True


    def is_floor_finished(self, type, floor):
        """判断整层floor是否通关
        """
        if type == self.NORMAL_MODE:
            if self.normal_floor > floor:
                return True
            elif self.normal_floor < floor:
                return False
            else:
                if (self.normal_level == self.LEVEL_NUM_PER_FLOOR 
                        and self.normal_level_finished == True):
                    return True
                else:
                    return False
        elif type == self.HARD_MODE:
            if self.hard_floor > floor:
                return True
            elif self.hard_floor < floor:
                return False
            else:
                if (self.hard_level == self.LEVEL_NUM_PER_FLOOR 
                        and self.hard_level_finished == True):
                    return True
                else:
                    return False

        else:
            return False


    def start_battle(self, type, floor, level, now):
        if (type != self.NORMAL_MODE
                and type != self.HARD_MODE):
            return False

        if type == self.NORMAL_MODE:
            if floor <= self.normal_floor:
                pass
            elif floor == self.normal_floor  and level <= self.normal_level:
                pass
            else:
                logger.warning("cannot start battle[floor=%d][level=%d][normal_floor=%d][normal_level=%d]"
                        % (floor, level, self.normal_floor, self.normal_level))
                return False
        elif type == self.HARD_MODE:
            #先判断本层的简单模式是否已通关
            if not self.is_floor_finished(self.NORMAL_MODE, floor):
                logger.warning("cannot start battle, normal mode not finished[floor=%d]" % floor)
                return False

            if floor < self.hard_floor:
                pass
            elif floor == self.hard_floor and level <= self.hard_level:
                pass
            else:
                return False

        self.current_type = type
        self.current_floor = floor
        self.current_level = level
        self.current_start_time = now

        return True
    
    
    def finish_battle(self, win):
        if not win:
            self._clear_battle_info()
            return True

        if self.current_type == self.NORMAL_MODE:
            if (self.current_floor == self.normal_floor 
                    and self.current_level == self.normal_level):
                self.normal_level_finished = True

        elif self.current_type == self.HARD_MODE:
            if (self.current_floor == self.hard_floor 
                    and self.current_level == self.hard_level):
                self.hard_level_finished = True

        else:
            self._clear_battle_info()
            return False

        
        self._try_forward_one_level(self.current_type)
        self._clear_battle_info()
        return True


    def _clear_battle_info(self):
        self.current_type = 0
        self.current_floor = 0
        self.current_level = 0
        self.current_start_time = 0


    def is_need_to_update_first_record(self):
        """是否有必要更新首次通关记录
           （过了困难模式第六关才需要更新记录）
        """
        if self.current_type != self.HARD_MODE:
            return False

        if self.current_level != self.LEVEL_NUM_PER_FLOOR:
            return False

        return True


    def is_need_to_update_fast_record(self, user_level):
        """是否有必要更新最快通关记录
           （过了困难模式第六关才需要更新记录）
        """
        if self.current_type != self.HARD_MODE:
            return False

        if self.current_level != self.LEVEL_NUM_PER_FLOOR:
            return False

        enemy_level = self.get_anneal_enemy_level(self.current_type, 
                self.current_floor, self.current_level)
        
        LEVEL_DIFF = 5
        #超过boss等级5关，不记录
        if user_level - enemy_level > LEVEL_DIFF:
            return False

        return True


    def is_in_sweep(self):
        """是否试炼场当前正在扫荡
        """
        return self.sweep_floor != 0


    def is_able_to_sweep(self, floor):
        """判断是否可以扫荡
        """
        if self.is_in_sweep():
            return False

        if not self.is_floor_finished(self.NORMAL_MODE, floor):
            return False

        if not self.is_floor_finished(self.HARD_MODE, floor):
            return False

        return True


    def get_sweep_teams_index(self):
        return utils.split_to_int(self.sweep_teams_index)


    def get_sweep_heroes_id(self):
        return utils.split_to_int(self.sweep_heroes_id)
   

    def modify_sweep_start_time(self, back_time):
        self.sweep_start_time = self.sweep_start_time - back_time

    
    def start_sweep(self, floor, direction, total_time, attack_num, teams, heroes, now,
            mode = 1):
        """开始扫荡
        """
        if (direction != self.SWEEP_DIRECTION_NONE
                and direction != self.SWEEP_DIRECTION_WEAPON
                and direction != self.SWEEP_DIRECTION_ARMOR
                and direction != self.SWEEP_DIRECTION_TREASURE):
            return False

        #判断本层的简单模式是否已通关
        if not self.is_floor_finished(self.NORMAL_MODE, (floor-1)/6 + 1):
            logger.warning("cannot sweep, normal mode not finished[floor=%d]" % floor)
            return False

        #判断本层的困难模式是否已通关
        if not self.is_floor_finished(self.HARD_MODE, (floor-1)/6 +1):
            logger.warning("cannot sweep, hard mode not finished[floor=%d]" % floor)
            return False

        self.sweep_floor = floor
        self.sweep_direction = direction
        self.sweep_mode = mode

        teams_index = []
        for team in teams:
            teams_index.append(team.index)
        heroes_id = []
        for hero in heroes:
            heroes_id.append(hero.id)

        self.sweep_teams_index = utils.join_to_string(teams_index)
        self.sweep_heroes_id = utils.join_to_string(heroes_id)
        self.sweep_total_time = total_time
        self.sweep_attack_num = attack_num
        self.sweep_start_time = now

        return True


    def finish_sweep(self):
        """结束扫荡
        """
        self.sweep_floor = 0
        self.sweep_teams_index = ''
        self.sweep_heroes_id = ''
        self.sweep_total_time = 0
        self.sweep_start_time = 0
        self.sweep_mode = self.NORMAL_MODE
        self.sweep_attack_num = 0
        self.sweep_at_least = False

        return True


    def try_forward_floor(self):
        """处理某些层的进度没有更新的情况（例如，新开N层试炼）
        """
        self._try_forward_one_floor(self.NORMAL_MODE)
        self._try_forward_one_floor(self.HARD_MODE)


    def is_able_to_get_pass_reward(self, type):
        """判断是否可以领取通关奖励
        """
        if type == self.NORMAL_MODE:
            if (self.normal_level >= self.LEVEL_NUM_PER_FLOOR 
                and self.normal_level_finished 
                and not self.normal_reward_received):
                return True
            else:
                return False

        elif type == self.HARD_MODE:
            if (self.hard_level >= self.LEVEL_NUM_PER_FLOOR 
                and self.hard_level_finished 
                and not self.hard_reward_received):
                return True
            else:
                return False
        else:
            return False


    def calc_pass_reward(self,type):
        """计算当前的通关奖励是什么
        """
        items_info = []
        if type == self.NORMAL_MODE:
            floor_reward = data_loader.AnnealFloorReward_dict[self.normal_floor]

            for i in range(len(floor_reward.normalPassItemBasicId)):
                item_id = floor_reward.normalPassItemBasicId[i]
                item_num = floor_reward.normalPassItemNum[i]
                items_info.append((item_id, item_num))

        elif type == self.HARD_MODE:
            floor_reward = data_loader.AnnealFloorReward_dict[self.hard_floor]

            for i in range(len(floor_reward.hardPassItemBasicId)):
                item_id = floor_reward.hardPassItemBasicId[i]
                item_num = floor_reward.hardPassItemNum[i]
                items_info.append((item_id, item_num))
        
        return items_info


    def get_pass_reward(self, type):
        """获得通关奖励
        """
        items_info = []
        if type == self.NORMAL_MODE:
            self.normal_reward_received = True

        elif type == self.HARD_MODE:
            self.hard_reward_received = True

        return self._try_forward_one_floor(type)


    def _try_forward_one_level(self, type):
        """试炼进度往前推进一小关
        """

        if type == self.NORMAL_MODE:
            if not self.normal_level_finished:
                return True

            if self.normal_level >= self.LEVEL_NUM_PER_FLOOR:
                #已到最后一关，不往前推进
                pass
            else:
                self.normal_level += 1
                self.normal_level_finished = False

        elif type == self.HARD_MODE:
            if not self.hard_level_finished:
                return True

            if self.hard_level >= self.LEVEL_NUM_PER_FLOOR:
                #已到最后一关，不往前推进
                pass
            else:
                self.hard_level += 1
                self.hard_level_finished = False
        
        return True


    def _try_forward_one_floor(self, type):
        """试炼进度往前推荐一层
        """
        #最大层数
        max_floor_num = len(data_loader.AnnealLevelInfo_dict.keys()) / self.LEVEL_NUM_PER_FLOOR

        if type == self.NORMAL_MODE:
            if self.normal_level < self.LEVEL_NUM_PER_FLOOR:
                return False

            if not self.normal_level_finished:
                return False

            if self.normal_floor == max_floor_num:
                #已到最大层数
                pass
            else:
                self.normal_floor += 1
                self.normal_level = 1
                self.normal_level_finished = False
                self.normal_reward_received = False

        elif type == self.HARD_MODE:
            if self.hard_level < self.LEVEL_NUM_PER_FLOOR:
                return False

            if not self.hard_level_finished:
                return False

            if self.hard_floor == max_floor_num:
                #已到最大层数
                pass
            else:
                self.hard_floor += 1
                self.hard_level = 1
                self.hard_level_finished = False
                self.hard_reward_received = False

        return True

    def get_hard_attack_num(self, floor):
        array = utils.split_to_int(self.hard_attack_num)
        return array[floor - 1]

    def set_hard_attack_num(self, floor, num):
        array = utils.split_to_int(self.hard_attack_num)
        array[floor - 1] = num
        self.hard_attack_num = utils.join_to_string(array)

    def get_hrad_attack_remain_num(self, floor):
        hard_daily_attack_num = int(float(data_loader.AnnealConfInfo_dict['hard_attack_num_limit'].value))
        return hard_daily_attack_num - self.get_hard_attack_num(floor)

    def cost_hard_attack_num(self, floor, num):
        """消耗困难模式的攻击次数"""
        logger.notice("get_hard_attack_num =%d floor=%d"%(self.get_hrad_attack_remain_num(floor),floor))
        if self.get_hrad_attack_remain_num(floor) < num:
            return False

        attack_num = self.get_hard_attack_num(floor)
        attack_num += num
        self.set_hard_attack_num(floor, attack_num)

        return True

    def set_sweep_at_least(self):
        """设置保底扫荡"""
        self.sweep_at_least = True

    def get_hard_reset_num(self, floor):
        array = utils.split_to_int(self.hard_reset_num)
        return array[floor - 1]

    def set_hard_reset_num(self, floor, num):
        array = utils.split_to_int(self.hard_reset_num)
        array[floor - 1] = num
        self.hard_reset_num = utils.join_to_string(array)

    def reset_hard_attack_num(self, floor):
        self.set_hard_attack_num(floor, 0)
        reset_num = self.get_hard_reset_num(floor)
        self.set_hard_reset_num(floor, reset_num + 1)
