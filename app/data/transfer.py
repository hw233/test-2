#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场数据
"""

from utils import utils
from utils.ret import Ret
from app.data.transfer_record import TransferRecordInfo
from datalib.data_loader import data_loader

class UserTransferInfo(object):

    __slots__ = (
        "user_id",
        "match_ids",
        "is_robots",
        "attack_num",
        "last_attack_time",
        "record_next_index",
    )

    def __init__(self):
        self.user_id = 0
        self.match_ids = ""
        self.is_robots = ""
        self.attack_num = 0
        self.last_attack_time = 0
        self.record_next_index = 1

    @staticmethod
    def create(user_id):
        transfer = UserTransferInfo()
        transfer.user_id = user_id
        transfer.match_ids = "0#0#0"
        transfer.is_robots = "0#0#0"
        transfer.attack_num = 0
        transfer.last_attack_time = 0
        transfer.record_next_index = 1

        return transfer

    def reset(self):
        self.attack_num = 0

    def set_match_ids(self, match_ids):
        self.match_ids = utils.join_to_string(match_ids)

    def set_is_robots(self, is_robots):
        self.is_robots = utils.join_to_string(is_robots)

    def get_match_ids(self):
        return utils.split_to_int(self.match_ids)

    def get_is_robots(self):
        return utils.split_to_int(self.is_robots)

    def target_is_robot(self, target_id):
        match_ids = self.get_match_ids()
        assert target_id in match_ids
        
        return bool(self.get_is_robots()[match_ids.index(target_id)])

    def get_remain_times(self):
        total_times = int(float(data_loader.OtherBasicInfo_dict['transfer_arena_challenge_total_times'].value))
        return total_times - self.attack_num

    def get_cd_end_time(self, now):
        cd = int(float(data_loader.OtherBasicInfo_dict['transfer_arena_reset_cd_time'].value))
        return max(self.last_attack_time + cd - now, 0)

    def reduce_attack_num(self, num, ret=Ret()):
        if self.attack_num - num < 0:
            ret.setup("UPPER_LIMIT")
            return False

        self.attack_num -= num
        return True

    def reset_cd(self, now):
        cd = int(float(data_loader.OtherBasicInfo_dict['transfer_arena_reset_cd_time'].value))
        self.last_attack_time = now - cd

    def is_able_to_start_battle(self, target_id, now, ret=Ret()):
        if self.get_remain_times() <= 0:
            ret.setup("NO_CHALLENGE_TIMES")
            return False

        if self.get_cd_end_time(now) > 0:
            ret.setup("COOLING")
            return False
        
        if target_id not in self.get_match_ids():
            ret.setup("TARGET_ERROR")
            return False

        return True
        
    def start_battle(self, now):
        self.attack_num += 1
        #self.last_attack_time = now

    def finish_battle(self, now):
        self.last_attack_time = now

    def generate_record_index(self):
        index = self.record_next_index
        self.record_next_index += 1

        return index
