#coding:utf8
"""
Created on 2016-08-26
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 世界boss相关逻辑
"""
import time
import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class WorldBossInfo(object):
    """世界boss信息
    """

    INACTIVE = 1	     #未激活
    BEFORE_BATTLE = 2    #今天有世界boss，还没开始
    IN_BATTLE = 3        #今天有世界boss，已经开始
    AFTER_BATTLE = 4     #今天有世界boss，已经结束
    LOCKED = 5	         #锁定状态，主公等级没有达到
    DISABLE = 6	         #锁定状态，主公等级没有达到

    BOSS_OK = 0
    BOSS_KILLED = 1	     #boss已被击杀
    BOSS_EXPIRED = 2     #可以战斗的时间区间已过
    BOSS_OVERTIME = 3    #单场战斗超时

    ARRAY_LEVEL_DIFF_MAX = 5
    ARRAY_NUM = 3

    FINISH_TIME_BUFF = 1000    #延长的战斗结束buff

    def __init__(self, user_id = 0, node_id = 0, boss_id = 0, level = 0,
            is_locked = True, arise_time = 0, start_time = 0, end_time = 0,
            arrays_id = '', can_attack_arrays_index = '',
            description = '', total_soldier_num = 0, current_soldier_num = 0,
            kill_user_id = 0, kill_user_name = '',
            kills_num = 0, merit = 0, attack_time = 0, attack_array_index = 0):

        self.user_id = user_id
        
        self.node_id = node_id
        self.boss_id = boss_id
        self.level = level              #boss的等级
        self.is_locked = is_locked
        self.arise_time = arise_time    #boss出现的时间
        self.start_time = start_time    #boss战斗开打时间
        self.end_time = end_time      #boss战斗结束时间
        
        self.arrays_id = arrays_id    #阵容
        #对应3个阵容是否可攻击 如1#0#0代表只有第一个阵容可以攻击
        self.can_attack_arrays_index = can_attack_arrays_index  

        self.description = description
        self.total_soldier_num = total_soldier_num      #boss总兵力
        self.current_soldier_num = current_soldier_num  #boss当前兵力
        self.kill_user_id = kill_user_id                #击杀boss的user_id
        self.kill_user_name = kill_user_name            #击杀boss的user_name

        self.kills_num = kills_num                  #玩家的杀敌数
        self.merit = merit                #玩家的战功
        self.attack_time = attack_time    #战斗开始时间
        self.attack_array_index = 0       #战斗选择的阵容， 1、2、3


    @staticmethod
    def create(user_id, now):
        """初始信息
        Args:
            user_id[int]: 用户 id
        Returns:
            anneal[AnnealInfo]
        """
        world_boss = WorldBossInfo(user_id)
        return world_boss


    def is_unlock(self):
        """世界boss功能是否已经解锁
        """
        return not self.is_locked


    def unlock(self):
        """解锁世界boss
        """
        self.is_locked = False

    
    def is_arised(self):
        """当前是否有世界boss
        """
        if self.arise_time == 0:
            return False
        else:
            return True


    def is_node_exist(self):
        """大地图上是否已经触发了node点
        """
        if self.node_id == 0:
            return False
        else:
            return True


    def is_killed(self):
        """boss是否已被击杀
        """
        if self.current_soldier_num <= 0:
            return True
        else:
            return False


    def is_overdue(self, now):
        """当前世界boss是否已经过期
        """
        is_same_day = utils.is_same_day(now, self.arise_time)
        if is_same_day:
            return False
        else:
            return True


    def is_in_battle_time(self, now, need_buff = False):
        """是否处于战斗时间
        """
        if need_buff == True:
            addition = self.FINISH_TIME_BUFF
        else:
            addition = 0

        if now >= self.start_time and now <= self.end_time + addition:
            return True
        else:
            return False


    def is_battle_time_passed(self, now):
        """战斗时间已经过去
        """
        return now >= self.end_time + self.FINISH_TIME_BUFF


    def is_able_to_attack(self, now):
        """是否可以开始战斗
        """
        #if self.is_arised() and self.is_node_exist() and self.is_in_battle_time(now) and not self.is_killed():
        #    return True
        #else:
        #    return False
        return self.is_arised() and self.is_in_battle_time(now) and not self.is_killed()


    def is_able_to_finish_attack(self, now):
        """是否可以结束战斗
        """
        if self.attack_time != 0:
            return True
        else:
            return False


    def is_attack_overtime(self, now):
        """单场战斗是否超时
        """
        OVERTIME_LIMIT = 480
        if now - self.attack_time > OVERTIME_LIMIT:
            return True
        else:
            return False


    def is_killer(self, user_id):
        """是不是最后一击的玩家
        """
        return self.kill_user_id == user_id


    def get_arrays_id(self):
        return self.arrays_id.split('#')


    def get_can_attack_arrays_index(self):
        return utils.split_to_int(self.can_attack_arrays_index)


    def get_arrays_merit_ratio(self):
        arrays = self.arrays_id.split('#')
        merit_ratios = []

        for array in arrays:
            merit_ratios.append(data_loader.WorldBossArrayBasicInfo_dict[array].meritRatio)

        return merit_ratios


    def arise(self, now, boss_id, start_time, end_time, total_soldier_num, 
            description, user_level):
        """世界boss触发了
        """
        self.kills_num = 0
        self.merit = 0

        self.boss_id = boss_id
        self.arise_time = utils.get_start_second(now)
        self.start_time = start_time
        self.end_time = end_time
        self.total_soldier_num = total_soldier_num
        self.current_soldier_num = total_soldier_num

        arrays = []
        mod = user_level % 5
        self.level = user_level - mod
        #阵容key的形式为bossId_level_index
        arrays.append("%s_%s_%s" % (self.boss_id, self.level, 1))
        arrays.append("%s_%s_%s" % (self.boss_id, self.level, 2))
        arrays.append("%s_%s_%s" % (self.boss_id, self.level, 3))

        self.arrays_id = utils.join_to_string(arrays)
        self.description = description

        self.calc_can_attack_array_index(0, 0)
        logger.debug("Arise worldboss[boss_id=%d][arise_time=%d][start_time=%d][end_time=%d][user_level=%d]"\
                % (self.boss_id, self.arise_time, self.start_time, self.end_time, user_level))
        return True


    def clear(self):
        """清空世界boss信息
        """
        self.node_id = 0
        self.boss_id = 0
        self.arise_time = 0
        self.start_time = 0
        self.end_time = 0
        self.arrays_id = ''
        self.can_attack_arrays_index = ''
        self.total_soldier_num
        self.kill_user_id = 0
        self.kill_user_name = ''
        #clear时不清除，以免活动奖励出错时还可以查询
        #self.kills_num = 0   
        #self.merit = 0
        return True


    def clear_merit(self):
        """清空战功
        """
        self.merit = 0


    def trigger_node(self, node_id):
        """大地图上刷出世界boss的点
        """
        self.node_id = node_id

    
    def clear_node(self):
        """清除node点
        """
        self.node_id = 0


    def update_basic_info(self, start_time, end_time, total_soldier_num, description):
        """更新基础信息
        """
        self.start_time = start_time
        self.end_time = end_time
        self.total_soldier_num = total_soldier_num
        self.description = description


    def update(self, current_soldier_num, kill_user_id, kill_user_name):
        """更新boss信息
        """
        self.current_soldier_num = current_soldier_num
        self.kill_user_id = kill_user_id
        self.kill_user_name = kill_user_name

        return True

    
    def start_battle(self, array_index, now):
        can_attack_arrays_index = utils.split_to_int(self.can_attack_arrays_index)
        if can_attack_arrays_index[array_index - 1] != 1:
            logger.warning("Can not attack this array[array_index=%d]" % array_index)
            return False

        self.attack_time = now
        self.attack_array_index = array_index
        return True

    
    def finish_battle(self, result, kill_soldier_num, now):
        #根据胜负情况重新计算阵容可攻击的概率
        if result == True:
             self.calc_can_attack_array_index(self.attack_array_index, 1)
        else:
            self.calc_can_attack_array_index(self.attack_array_index, 0)

        self.kills_num += kill_soldier_num
        if self.is_in_battle_time(now, True):
            #计算战功
            key = "%s_%s_%s" % (self.boss_id, self.level, self.attack_array_index)
            merit_ratio = data_loader.WorldBossArrayBasicInfo_dict[key].meritRatio
            self.merit += int(kill_soldier_num * merit_ratio)

        self.attack_time = 0
        self.attack_array_index = 0

        return True


    def calc_can_attack_array_index(self, array_index, win):
        """计算出可以被攻击的阵容
        Args:
            array_index : 上一场攻击的阵容
            is_win : 上一场是否胜利  1代表胜利， 0代表失败
        """
        can_attack_index = []

        key = "%s_%s" % (array_index, win)
        probabilities = data_loader.ArrayAttackRatio_dict[key]

        array_one_probability = 1.0 * probabilities.arrayOneAvailableProbability / 100.0
        array_two_probability = 1.0 * probabilities.arrayTwoAvailableProbability / 100.0
        array_three_probability = 1.0 * probabilities.arrayThreeAvailableProbability / 100.0

        random.seed()
        c = random.random()
        if c < array_one_probability:
            can_attack_index.append(1)
        else:
            can_attack_index.append(0)

        c = random.random()
        if c < array_two_probability:
            can_attack_index.append(1)
        else:
            can_attack_index.append(0)

        c = random.random()
        if c < array_three_probability:
            can_attack_index.append(1)
        else:
            can_attack_index.append(0)

        self.can_attack_arrays_index = utils.join_to_string(can_attack_index) 

    def get_node_basic_id(self):
        return int(float(data_loader.MapConfInfo_dict['worldboss_node_basic_id'].value))
