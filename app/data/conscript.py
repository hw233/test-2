#coding:utf8
"""
Created on 2015-01-26
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 征兵相关数值计算
"""

import math
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class ConscriptInfo(object):
    def __init__(self, building_id = 0, user_id = 0,
            soldier_num = 0,
            lock_soldier_num = 0,
            soldier_capacity = 0,
            conscript_num = 0,
            already_conscript_num = 0,
            conscript_money = 0,
            start_time = 0,
            end_time = 0,
            last_update_time = 0,
            daily_conscript_soldier = 0,
            total_conscript_soldier = 0):
        self.building_id = building_id
        self.user_id = user_id

        self.soldier_num = soldier_num
        self.lock_soldier_num = lock_soldier_num
        self.soldier_capacity = soldier_capacity
        self.conscript_num = conscript_num
        self.already_conscript_num = already_conscript_num

        self.conscript_money = conscript_money
        self.start_time = start_time
        self.end_time = end_time

        self.last_update_time = last_update_time
        self.daily_conscript_soldier = daily_conscript_soldier
        self.total_conscript_soldier = total_conscript_soldier


    @staticmethod
    def create(building):
        """创建新的征兵信息，新建一个兵营后会创建
        """
        conscript = ConscriptInfo(building.id, building.user_id)
        return conscript


    def update_soldier_capacity(self, capacity):
        """更新士兵兵容
        """
        assert capacity >= 0
        self.soldier_capacity = capacity


    def update_current_soldier(self, now):
        """更新当前士兵数量
        """
        if self.conscript_num == 0:  #没在征兵，无需更新
            return 0

        #按照时间比例征兵
        if now >= self.end_time:
            total_num = self.conscript_num
        else:
            duration = now - self.start_time
            total_time = self.end_time - self.start_time
            total_num = int(float(duration) / total_time * self.conscript_num)

        add_num = total_num - self.already_conscript_num
        if add_num < 0:
            logger.warning("Invalid conscript num[num=%d]" % add_num)
            return -1

        self.soldier_num += add_num
        self.already_conscript_num += add_num
        self.last_update_time = now
        self.daily_conscript_soldier += add_num
        self.total_conscript_soldier += add_num
        return add_num


    def provide_soldier(self, num):
        """提供士兵
        """
        if num < 0:
            logger.warning("Soldier num error[num=%d]" % num)
            return False

        if num > self.soldier_num:
            logger.warning("Soldier not enough[own=%d][need=%d]" %
                    (self.soldier_num, num))
            return False

        self.soldier_num -= num
        return True


    def reclaim_soldier(self, num):
        """回收士兵
        """
        if num < 0:
            logger.warning("Soldier num error[num=%d]" % num)
            return False

        if num > self.get_available_conscript_num():
            logger.warning("Soldier over limit[own=%d][capacity=%d]"
                    "[conscript_target=%d][already_conscript=%d][reclaim=%d]" %
                    (self.soldier_num, self.soldier_capacity,
                        self.conscript_num, self.already_conscript_num, num))
            num = self.get_available_conscript_num()
            #return False

        self.soldier_num += num
        return True


    def lock_soldier(self, num):
        """锁住士兵
        """
        if num < 0:
            logger.warning("Soldier num error[num=%d]" % num)
            return False

        if num > self.soldier_num - self.lock_soldier_num:
            logger.warning("Soldier not enough[own=%d][lock=%d][need=%d]" %
                    (self.soldier_num, self.lock_soldier_num, num))
            return False

        self.lock_soldier_num += num
        return True
    
    
    def unlock_soldier(self, num):
        """解锁士兵
        """
        if num < 0:
            logger.warning("Soldier num error[num=%d]" % num)
            return False

        if self.lock_soldier_num - num < 0:
            logger.debug("Lock soldier num is less[own=%d][capacity=%d]"
                    "[lock=%d][unlock=%d]" %
                    (self.soldier_num, self.soldier_capacity,
                        self.lock_soldier_num, num))
            self.lock_soldier_num = 0
        else:
            self.lock_soldier_num -= num

        return True


    def clear_lock_soldier_num(self):
        self.lock_soldier_num = 0


    def get_available_conscript_num(self):
        """获取当前还可以征兵的数量
        """
        current_conscript_num = self.conscript_num - self.already_conscript_num
        num = self.soldier_capacity - self.soldier_num - current_conscript_num
        return num


    def start_conscript(self, num, cost_money, cost_time, now):
        """
        开始征兵
        """
        if num <= 0:
            logger.warning("Conscript num error[num=%d]" % num)
            return False

        #判读是否可以进行征兵
        if self.conscript_num > 0:
            logger.warning("Building is already in conscript")
            return False

        if self.soldier_num + num > self.soldier_capacity:
            logger.warning("Conscript num overflow[own=%d][lock=%d][capacity=%d][conscript=%d]"
                    % (self.soldier_num, self.lock_soldier_num, self.soldier_capacity, num))
            #return False
            #客户端与服务器计算不一致，此处容错
            num = max(0, self.soldier_capacity - self.soldier_num)

        #开始征兵
        self.conscript_num = num
        self.already_conscript_num = 0
        self.conscript_money = cost_money
        self.start_time = now
        self.end_time = now + cost_time
        self.last_update_time = now

        return True


    def add_conscript(self, num, cost_money, cost_time):
        """补充征兵
        """
        if num <= 0:
            logger.warning("Add conscript num error[add num=%d]" % num)
            return False

        if self.conscript_num == 0:
            logger.warning("Building is not in conscript")
            return False

        if num > self.get_available_conscript_num():
            logger.warning("Soldier over limit[own=%d][capacity=%d]"
                    "[conscript_target=%d][already_conscript=%d][add=%d]" %
                    (self.soldier_num, self.soldier_capacity,
                        self.conscript_num, self.already_conscript_num, num))
            return False

        self.conscript_num += num
        self.conscript_money += cost_money
        self.end_time += cost_time

        return True


    def calc_time_gap_to_finish(self, now):
        """计算完成征兵还需要多少时间
        """
        gap = max(0, self.end_time - now)
        return gap


    def finish_conscript(self):
        """结束征兵
        """
        if self.conscript_num == 0:
            logger.warning("Building is not in conscript")
            return False

        self.conscript_num = 0
        self.already_conscript_num = 0
        self.conscript_money = 0
        self.start_time = 0
        self.end_time = 0
        self.last_update_time = 0

        return True


    def reset_daily_statistics(self):
        """重置天粒度统计信息
        Returns:
            None
        """
        self.daily_conscript_soldier = 0


    def calc_money_supplement_of_add(self, num):
        """计算补充征兵，还需要多少金钱
        """
        ratio = float(num) / self.conscript_num
        need_money = self.conscript_money * ratio
        return utils.floor_to_int(need_money)


    def calc_time_supplement_of_add(self, num):
        """计算补充征兵，还需要多少时间
        """
        ratio = float(num) / self.conscript_num
        need_time = (self.end_time - self.start_time) *  ratio
        return utils.ceil_to_int(need_time)


    def calc_money_remittal_of_cancel(self):
        """计算取消征兵，可以返还多少金钱粮草
        """
        #按照未完成的征兵数量，返回部分资源
        remain_percentage = (
                (float(self.conscript_num) - self.already_conscript_num) /
                float(self.conscript_num))
        ratio = float(data_loader.OtherBasicInfo_dict['CancelResourceReturnCoefficient'].value)
        remittal_money = self.conscript_money * remain_percentage * ratio
        return utils.floor_to_int(remittal_money)


