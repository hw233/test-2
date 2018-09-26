#coding:utf8
"""
Created on 2016-07-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnionBattleInfo(object):
    """一场联盟战争
    """

    BATTLE_STAGE_INVALID = 0    #非法
    BATTLE_STAGE_IDLE = 1       #无战争
    BATTLE_STAGE_PREPARE = 2    #备战阶段
    BATTLE_STAGE_FIGHT = 3      #战斗阶段
    BATTLE_STAGE_CLOSE = 4      #结束

    __slots__ = [
            "id",
            "union_id",
            "index",
            "stage",
            "rival_union_id",
            "rival_battle_id",
            "is_initiator",         #是否战争发起方

            "launch_time",          #战争发起时间
            "fight_time",           #战争开战时间
            "close_time",           #战争结束时间
            "finish_time",          #战争生命周期终止时间，可以开始下一场战争

            "is_deployed",          #是否已经完成防御部署
            "battle_count",         #战斗的数量
            "score",                #胜场积分
            "individuals_score",    #成员战功之和
            "drum",

            "attack_level",
            "attack_win_count_this_level",  #本轮战斗中攻击胜利次数
            "attack_lose_count_this_level", #本轮战斗中攻击失败次数
            "defend_nodes_level",   #防守方的节点level

            "record_index",

            "accepted_members",   #大宝箱领取的记录
            "accepted_names",
            "accepted_icons",
            "reward_items",
            "reward_nums",
            "accept_times"
            ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.index = 0

        self.stage = UnionBattleInfo.BATTLE_STAGE_INVALID
        self.rival_union_id = 0
        self.rival_battle_id = 0
        self.is_initiator = False
        self.launch_time = 0
        self.fight_time = 0
        self.close_time = 0
        self.finish_time = 0

        self.is_deployed = False
        self.battle_count = 0
        self.score = 0
        self.individuals_score = 0
        self.drum = 0

        self.attack_level = 1
        self.attack_win_count_this_level = 0
        self.attack_lose_count_this_level = 0
        self.defend_nodes_level = ""

        self.record_index = 0

    @staticmethod
    def generate_id(union_id, index):
        id = union_id << 32 | index
        return id


    @staticmethod
    def create(union_id, index, invalid):
        battle = UnionBattleInfo()
        battle.id = UnionBattleInfo.generate_id(union_id, index)
        battle.union_id = union_id
        battle.index = index

        if invalid:
            battle.stage = UnionBattleInfo.BATTLE_STAGE_INVALID #无法发起战争
        else:
            battle.stage = UnionBattleInfo.BATTLE_STAGE_IDLE
        battle.rival_union_id = 0
        battle.rival_battle_id = 0
        battle.is_initiator = False
        battle.launch_time = 0
        battle.fight_time = 0
        battle.close_time = 0
        battle.finish_time = 0

        battle.is_deployed = False
        battle.battle_count = 0
        battle.score = 0
        battle.individuals_score = 0
        battle.drum = 0

        battle.attack_level = 1
        battle.attack_win_count_this_level = 0
        battle.attack_lose_count_this_level = 0
        battle.defend_nodes_level = ""

        battle.record_index = 0

        battle.accepted_members = ""  #奖励箱领取
        battle.accepted_names = ""
        battle.accepted_icons = ""
        battle.reward_items = ""
        battle.reward_nums = ""
        battle.accept_times = ""

        return battle


    def force_update_fight_time(self, time):
        """强制改变开战时间（内部接口）
        """
        assert self.stage == self.BATTLE_STAGE_PREPARE
        self.fight_time = time


    def force_update_close_time(self, time):
        """强制改变结束战斗时间（内部接口）
        """
        assert self.stage == self.BATTLE_STAGE_FIGHT
        self.close_time = time


    def force_update_finish_time(self, time):
        """强制改变结束时间（内部接口）
        """
        assert self.stage == self.BATTLE_STAGE_CLOSE
        self.finish_time = time


    def is_able_to_join(self):
        """是否可以参战
        """
        return self.stage == self.BATTLE_STAGE_IDLE


    def is_able_to_deploy(self):
        """是否可以部署防御
        """
        return self.stage == self.BATTLE_STAGE_PREPARE


    def is_able_to_drum(self):
        """是否可以擂鼓
        """
        return self.stage == self.BATTLE_STAGE_FIGHT


    def is_at_war(self):
        """是否在交战中
        """
        return (self.stage == self.BATTLE_STAGE_PREPARE or
                self.stage == self.BATTLE_STAGE_FIGHT or
                self.stage == self.BATTLE_STAGE_CLOSE)


    def launch(self, now, rival_union_id, rival_battle_id, initiative = True):
        """发起战争
        """
        assert self.stage == self.BATTLE_STAGE_IDLE

        self.stage = self.BATTLE_STAGE_PREPARE
        self.rival_union_id = rival_union_id
        self.rival_battle_id = rival_battle_id
        self.is_initiator = initiative

        self.launch_time = now
        #self.fight_time = utils.get_spec_second(
        #        self.launch_time, "22:30") + utils.SECONDS_OF_DAY   #launch time 次日22:30
        #self.close_time = self.fight_time + utils.SECONDS_OF_DAY    #fight time 次日22:30
        #self.finish_time = utils.get_spec_second(
        #        self.close_time, "05:00" ) + utils.SECONDS_OF_DAY   #close time 次日05:00

        self.fight_time = utils.get_spec_second(self.launch_time, "21:00")      #fight time 当日21:00
        self.close_time = utils.get_spec_second(self.launch_time, "23:00")      #close time 当日23:00
        self.finish_time = utils.get_spec_second(self.launch_time, "05:00"
                ) + utils.SECONDS_OF_DAY                                        #finish time 次日05:00

        self.is_deployed = False

        self.accepted_members = ""
        self.accepted_names = ""
        self.accepted_icons = ""
        self.reward_items = ""
        self.reward_nums = ""
        self.accept_times = ""


    def start_fight(self, now):
        """进入开战阶段
        """
        assert self.stage == self.BATTLE_STAGE_PREPARE
        self.stage = self.BATTLE_STAGE_FIGHT
        self.is_deployed = True
        self.attack_level = 1


    def is_fight_closed(self, now):
        """战斗结算是否结束
        """
        return self.launch_time != 0 and now >= self.close_time


    def close_fight(self):
        """战争结束
        """
        #assert self.stage == self.BATTLE_STAGE_FIGHT
        self.stage = self.BATTLE_STAGE_CLOSE


    def is_finished(self, now):
        """战争是否结束
        """
        return self.launch_time != 0 and now >= self.finish_time and now >= self.close_time


    def is_able_to_start(self):
        """是否可以开战
        """
        return self.stage == self.BATTLE_STAGE_FIGHT


    def beat_drum(self, value = 1):
        """擂鼓
        """
        assert value >= 0
        self.drum += value


    def get_attack_buff_count(self):
        """获取当前攻击 buff 加成
        """
        drum_ratio = int(float(
            data_loader.UnionConfInfo_dict["attack_buff_count_per_drum"].value))
        lose_ratio = int(float(
            data_loader.UnionConfInfo_dict["attack_buff_count_per_lose"].value))
        return self.drum * drum_ratio + self.attack_lose_count_this_level * lose_ratio


    def get_attack_buff_temporary_count(self):
        """获取当前轮次临时攻击 buff 加成
        """
        lose_ratio = int(float(
            data_loader.UnionConfInfo_dict["attack_buff_count_per_lose"].value))
        return self.attack_lose_count_this_level * lose_ratio


    def mark_attack_result(self, win):
        """记录攻击结果
        """
        if win:
            self.attack_win_count_this_level += 1
        #else:
        #    self.attack_lose_count_this_level += 1

        #攻击进入下一轮
        count = int(float(data_loader.UnionConfInfo_dict["battle_map_node_count"].value))
        if self.attack_win_count_this_level >= count:
            self.attack_level += 1
            self.attack_win_count_this_level = 0
            self.attack_lose_count_this_level = 0


    def gain_union_score(self, value = 1):
        """增加联盟胜场积分
        """
        assert value >= 0
        self.score += value


    def gain_individuals_score(self, value):
        """增加成员战功点数
        """
        assert value >= 0
        self.individuals_score += value


    def get_next_record_index(self):
        """获取下一个战斗记录 index
        """
        self.record_index += 1
        return self.record_index


    def is_able_to_accept_box(self):
        """是否可以领取大宝箱/
        """
        if self.stage != self.BATTLE_STAGE_CLOSE:
            return False

        level = int(float(data_loader.UnionConfInfo_dict["battle_map_total_level"].value))
        count = int(float(data_loader.UnionConfInfo_dict["battle_map_node_count"].value))
        if level * count > self.score:
            return False

        return True


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



