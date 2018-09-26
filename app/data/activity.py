#coding:utf8
"""
Created on 2016-03-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 活动相关数据存储结构
"""

import os
import re
import json
import socket
import random
from firefly.utils.singleton import Singleton
from urllib import urlencode
from utils import logger
from utils import utils
from app.data.basic_activity import BasicActivityInfo 
from datalib.data_loader import data_loader

class ActivityInfo(object):
    """活动
    """
    REWARD_LOCKED = 0
    REWARD_AVAILABLE = 1
    REWARD_ACCEPTED = 2


    __slots__ = [
            "id", "user_id", "basic_id",
            "start_time", "end_time", "forward_time",
            "progress", "target", "status", 
            ]


    def __init__(self, id = 0, user_id = 0, basic_id = 0,
            start_time = 0, end_time = 0, forward_time = 0,
            progress = '', target = '', status = ''):
        """初始化
        """
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id

        self.start_time = start_time
        self.end_time = end_time
        self.forward_time = forward_time
        self.progress = progress
        self.target = target
        self.status = status


    @staticmethod
    def create(user_id, basic_id, basic_activity, basic_steps, now):
        """创建
        """
        id = ActivityInfo.generate_id(user_id, basic_id)

        info = basic_activity

        if info.start_time == "":
            start_time = 0
        else:
            start_time = utils.get_start_second_by_timestring(info.start_time)
            #开始时间为5点 
            start_time = utils.get_start_second(start_time + 1)

        if info.end_time == "":
            end_time = 0
        else:
            end_time = utils.get_end_second_by_timestring(info.end_time)

        if now != 0 and info.start_day != 0:
            start_time = utils.get_start_second(now + 86400 * (info.start_day - 1))

            if info.end_day != 0:
                end_time = utils.get_end_second(now + 86400 * (info.end_day -1))

        progress = [0] * len(info.get_steps())
        progress = utils.join_to_string(progress)

        target = []
        for step_id in info.get_steps():
            for basic_step in basic_steps:
                if step_id == basic_step.id:
                    target.append(basic_step.target)
                    break
        target = utils.join_to_string(target)

        status = []
        for step_id in info.get_steps():
            default_lock = False
            for basic_step in basic_steps:
                if step_id == basic_step.id:
                    default_lock = basic_step.default_lock
                    break

            if default_lock:
                status.append(ActivityInfo.REWARD_LOCKED)
            else:
                status.append(ActivityInfo.REWARD_AVAILABLE)
        status = utils.join_to_string(status)

        activity = ActivityInfo(id, user_id, basic_id,
                start_time, end_time, 0,
                progress, target, status)
        return activity


    @staticmethod
    def generate_id(user_id, basic_id):
        id = user_id << 32 | basic_id
        return id


    @staticmethod
    def get_basic_id(id):
        basic_id = id & 0xFFFFFFFF
        return basic_id


    def set_time(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time


    def has_time_limit(self):
        """是否有时间限制
        """
        if self.start_time == 0 and self.end_time == 0:
            return False
        return True


    def is_timeout(self, now):
        """是否超时
        """
        if self.end_time == 0:
            return False

        return self.end_time < now


    def is_living(self, now, style, is_query = False):
        """时间是否合法
        """
        if self.start_time == 0 and self.end_time == 0:
            return True

        if is_query:
            if style == BasicActivityInfo.STYLE_SEVEN_DAY:
                return now + 86400 * 8 >= self.start_time and now <= self.end_time
            elif style == BasicActivityInfo.STYLE_FESTIVAL:
                return now + 86400 * 8 >= self.start_time and now <= self.end_time
            else:
                return now >= self.start_time and now <= self.end_time
        else:
            return now >= self.start_time and now <= self.end_time


    def is_style_suitable(self, basic_activity, style):
        """时间是否合法
        """
        if basic_activity.style_id == style:
            return True
        else:
            return False


    def forward_all(self, basic_activity, value, now):
        """提升完成度
        """
        step_progress = utils.split_to_int(self.progress)
        steps_id = basic_activity.get_steps()
        for step_index in range(0, len(step_progress)):
            step_id = steps_id[step_index]
            step_progress[step_index] = value

        self.progress = utils.join_to_string(step_progress)
        self.forward_time = now


    def forward(self, basic_activity, step_id, value, now):
        """提升活动步骤的完成度
        """
        steps_id = basic_activity.get_steps()
        step_index = steps_id.index(step_id)

        step_progress = utils.split_to_int(self.progress)
        step_progress[step_index] = value

        self.progress = utils.join_to_string(step_progress)
        self.forward_time = now


    def update_target(self, basic_activity, step_id, value):
        """更新完成的目标值
        """
        steps_id = basic_activity.get_steps()
        step_index = steps_id.index(step_id)

        target = utils.split_to_int(self.target)
        target[step_index] = value
        self.target = utils.join_to_string(target)


    def get_step_progress(self):
        """获得所有步骤的完成度
        """
        return utils.split_to_int(self.progress)


    def get_reward_status(self):
        """获得奖励状态
        """
        return utils.split_to_int(self.status)


    def get_step_target(self):
        """获得所有步骤的目标
        """
        return utils.split_to_int(self.target)


    def get_next_step_id_unfinished(self, basic_activity):
        """获得下一个未完成的 step id
        """
        step_progress = utils.split_to_int(self.progress)
        step_target = utils.split_to_int(self.target)
        steps_id = basic_activity.get_steps()

        for index in range(0, len(step_progress)):
            step_id = steps_id[index]
            if step_progress[index] < step_target[index]:
                return step_id
        return 0


    def get_next_step_id_unaccepted(self, basic_activity):
        """获得下一个未领奖的 step id
        """
        steps_id = basic_activity.get_steps()
        step_status = utils.split_to_int(self.status)
        for (index, progress) in enumerate(step_status):
            step_id = steps_id[index]
            if step_status[index] == self.REWARD_AVAILABLE:
                return step_id
        return 0


    def is_unlocked(self):
        """是否存在解锁的奖励
        """
        step_status = utils.split_to_int(self.status)
        for step_index in range(0, len(step_status)):
            if step_status[step_index] != self.REWARD_LOCKED:
                return True

        return False


    def unlock_all_reward(self):
        """解锁所有奖励
        """
        step_status = utils.split_to_int(self.status)
        for step_index in range(0, len(step_status)):
            if step_status[step_index] == self.REWARD_LOCKED:
                step_status[step_index] = self.REWARD_AVAILABLE

        self.status = utils.join_to_string(step_status)


    def reset(self, basic_activity, basic_steps):
        """重制活动进度和奖励
        """
        info = basic_activity

        progress = [0] * len(info.get_steps())
        self.progress = utils.join_to_string(progress)

        target = []
        for step_id in info.get_steps():
            for basic_step in basic_steps:
                if step_id == basic_step.id:
                    target.append(basic_step.target)
                    break
        self.target = utils.join_to_string(target)

        status = []
        for step_id in info.get_steps():
            default_lock = False
            for basic_step in basic_steps:
                if step_id == basic_step.id:
                    default_lock = basic_step.default_lock
                    break

            if default_lock:
                status.append(ActivityInfo.REWARD_LOCKED)
            else:
                status.append(ActivityInfo.REWARD_AVAILABLE)
        self.status = utils.join_to_string(status)


    def reset_reward(self, basic_activity, step_id):
        """重制活动奖励状态
        """
        steps_id = basic_activity.get_steps()
        step_index = steps_id.index(step_id)
        step_status = utils.split_to_int(self.status)

        step_status[step_index] = self.REWARD_AVAILABLE
        self.status = utils.join_to_string(step_status)



    def unlock_reward(self, basic_activity, step_id):
        """解锁奖励
        """
        steps_id = basic_activity.get_steps()
        step_index = steps_id.index(step_id)
        step_status = utils.split_to_int(self.status)

        assert step_status[step_index] == self.REWARD_LOCKED

        step_status[step_index] = self.REWARD_AVAILABLE
        self.status = utils.join_to_string(step_status)


    def can_accept_reward(self):
        """
        """
        step_progress = utils.split_to_int(self.progress)
        step_target = utils.split_to_int(self.target)
        step_status = utils.split_to_int(self.status)
        for i in range(len(step_progress)):
            if step_progress[i] >= step_target[i] and step_status[i] == self.REWARD_AVAILABLE:
                return True

        return False


    def accept_reward(self, basic_activity, step_id):
        """领取奖励
        """
        steps_id = basic_activity.get_steps()
        step_index = steps_id.index(step_id)
        step_progress = utils.split_to_int(self.progress)
        step_target = utils.split_to_int(self.target)
        step_status = utils.split_to_int(self.status)
        if (step_progress[step_index] < step_target[step_index] or
                step_status[step_index] != self.REWARD_AVAILABLE):
            logger.warning("Not able to accept reward[basic id=%d][step id=%d][step_index=%d][step_progress=%s][step_target=%s][step_status =%s]" %
                    (self.basic_id, step_id, step_index, step_progress, step_target, step_status))
            return False

        step_status[step_index] = self.REWARD_ACCEPTED
        self.status = utils.join_to_string(step_status)
        return True


    def is_accept_all(self):
        """是否领取完所有奖励
        """
        step_status = utils.split_to_int(self.status)
        for s in step_status:
            if s != self.REWARD_ACCEPTED:
                return False

        return True



