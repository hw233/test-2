#coding:utf8
"""
Created on 2017-03-01
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟boss
"""
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
import base64

class UnionBossInfo(object):
    """联盟boss信息"""

    INACTIVE = 1
    BATTLE = 2
    KILLED = 3

    __slots__ = [
        "id",
        "union_id",
        "boss_id",

        "status",
        "total_soldier_num",
        "current_soldier_num",

        "killer_id",
        "killer_name",

        "accepted_members",
        "accepted_names",
        "accepted_icons",
        "reward_items",
        "reward_nums",
        "accept_times",
    ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.boss_id = 0

        self.status = 1
        self.total_soldier_num = 0
        self.current_soldier_num = 0

        self.killer_id = 0
        self.killer_name = ""
        
        self.accepted_members = ""
        self.accepted_names = ""
        self.accepted_icons = ""
        self.reward_items = ""
        self.reward_nums = ""
        self.accept_times = ""

    @staticmethod
    def create(union_id, boss_id, status = INACTIVE,
            total_soldier_num = 0, current_soldier_num = 0):
        boss = UnionBossInfo()
        boss.id = UnionBossInfo.generate_id(union_id, boss_id)
        boss.union_id = union_id
        boss.boss_id = boss_id

        boss.status = status
        boss.total_soldier_num = total_soldier_num
        boss.current_soldier_num = current_soldier_num  #boss当前血量

        boss.killer_id = 0
        boss.killer_name = ""
        
        boss.accepted_members = ""  #奖励箱领取
        boss.accepted_names = ""
        boss.accepted_icons = ""
        boss.reward_items = ""
        boss.reward_nums = ""
        boss.accept_times = ""

        return boss
    
    @staticmethod
    def generate_id(union_id, boss_id):
        return union_id << 32 | boss_id

    def is_able_to_attack(self):
        """是否可以攻击boss"""
        return self.status == self.BATTLE

    def reset(self):
        """重置"""
        self.status = self.INACTIVE
        self.total_soldier_num = data_loader.UnionBossBasicInfo_dict[self.boss_id].totalSoldierNum
        self.current_soldier_num = self.total_soldier_num
        self.killer_id = 0
        self.killer_name = ""
        self.accepted_members = ""
        self.accepted_names = ""
        self.accepted_icons = ""
        self.reward_items = ""
        self.reward_nums = ""
        self.accept_times = ""

    def attack(self, kill_soldier_num, user_id, user_name):
        """攻击boss"""
        if self.status != self.BATTLE:
            logger.warning("union boss status error[status=%s]", self.status)
            assert self.status == self.BATTLE

        self.current_soldier_num -= kill_soldier_num
        if self.current_soldier_num <= 0:
            self.current_soldier_num = 0
            self.status = self.KILLED
            self.killer_id = user_id
            self.killer_name = user_name

    def get_accepted_members(self):
        """获取领取过奖励的成员"""
        return utils.split_to_int(self.accepted_members)

    def get_reward_record(self):
        """获取奖励领取记录"""
        members = utils.split_to_int(self.accepted_members)
        names = utils.split_to_string(self.accepted_names)
        icons = utils.split_to_int(self.accepted_icons) 
        items_id = utils.split_to_int(self.reward_items)
        items_num = utils.split_to_int(self.reward_nums)
        times = utils.split_to_int(self.accept_times)

        names = [base64.b64decode(name) for name in names]
        return map(None, members, names, icons, items_id, items_num, times)

    def add_reward_record(self, user_id, user_name, icon_id, item_id, item_num, now):
        """添加领奖记录"""
        members = utils.split_to_int(self.accepted_members)
        names = utils.split_to_string(self.accepted_names)
        icons = utils.split_to_int(self.accepted_icons) 
        items_id = utils.split_to_int(self.reward_items)
        items_num = utils.split_to_int(self.reward_nums)
        times = utils.split_to_int(self.accept_times)

        members.append(user_id)
        names.append(user_name)
        icons.append(icon_id)
        items_id.append(item_id)
        items_num.append(item_num)
        times.append(now)

        self.accepted_members = utils.join_to_string(members)
        self.accepted_names = utils.join_to_string(names)
        self.accepted_icons = utils.join_to_string(icons)
        self.reward_items = utils.join_to_string(items_id)
        self.reward_nums = utils.join_to_string(items_num)
        self.accept_times = utils.join_to_string(times)

    def set_activity(self):
        """置为可攻击的状态"""
        if self.status != self.INACTIVE:
            logger.warning("union boss status error[id=%d][status=%d]" % (self.id, self.status))
            raise Exception("union boss status error")

        self.status = self.BATTLE
