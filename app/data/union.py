#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟
"""

from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UserUnionInfo(object):
    """玩家联盟相关信息
    """

    __slots__ = [
            "user_id",
            "union_id",
            "union_level",
            "update_time",
            "lock_time",
            "honor",
            "aid_start_time",
            "aid_lock_time",

            "season_score",             #赛季联盟战功
            "battle_attack_count_left",
            "battle_attack_refresh_num",
            "battle_drum_count",        #此次战争中擂鼓数目

            "donate_coldtime",          #捐献累积的冷却时间
            "last_donate_time",         #上次捐献的时间

            "last_update_daily_time",   #上次更新每日信息的时间

            "union_boss_last_update_time", #上次联盟boss更新的时间
            "union_boss_score",         #联盟boss战功
            "union_boss_attack_num",    #每日攻击联盟boss的次数
            "union_boss_reset_num",     #当日重置攻击次数的次数
            "union_boss_box_steps",     #领过的个人战功宝箱index
            ]

    def __init__(self):
        self.user_id = 0
        self.union_id = 0
        self.union_level = 1
        self.update_time = 0
        self.lock_time = 0
        self.honor = 0
        self.aid_start_time = 0
        self.aid_lock_time = 0

        self.season_score = 0
        self.battle_attack_count_left = 0
        self.battle_attack_refresh_num = 0
        self.battle_drum_count = 0

        self.donate_coldtime = 0
        self.last_donate_time = 0

        self.last_update_daily_time = 0

        self.union_boss_last_update_time = 0
        self.union_boss_score = 0
        self.union_boss_attack_num = 0
        self.union_boss_reset_num = 0
        self.union_boss_box_steps = ""

    @staticmethod
    def create(user_id):
        union = UserUnionInfo()
        union.user_id = user_id
        union.union_id = 0
        union.union_level = 1
        union.update_time = 0 #union 状态发生变动的时间
        union.lock_time = 0
        union.honor = 0
        union.aid_start_time = 0
        union.aid_lock_time = 0

        union.season_score = 0
        union.reset_battle_attack()
        union.battle_drum_count = 0

        union.donate_coldtime = 0
        union.last_donate_time = 0

        union.last_update_daily_time = 0

        union.union_boss_last_update_time = 0
        union.union_boss_score = 0
        union.union_boss_attack_num = 0
        union.union_boss_reset_num = 0
        union.union_boss_box_steps = ""
        return union


    def update_daily_info(self, now):
        """更新每日信息"""
        if not utils.is_same_day(self.last_update_daily_time, now):
            self.union_boss_attack_num = 0
            self.union_boss_reset_num = 0

            self.last_update_daily_time = now

    def is_belong_to_union(self):
        """是否属于某个联盟
        """
        return self.union_id != 0


    def is_belong_to_target_union(self, union_id):
        """是否属于指定联盟
        """
        return self.union_id == union_id


    def is_locked(self, now):
        """是否处于锁定状态
        """
        return now < self.lock_time


    def calc_create_cost_gold(self):
        return int(float(data_loader.UnionConfInfo_dict["create_cost_gold"].value))


    def calc_create_need_level(self):
        return int(float(data_loader.UnionConfInfo_dict["default_level_min"].value))


    def reset_lock_time(self, now):
        self.lock_time = now


    def is_application_valid(self, application_time):
        """申请是否有效
        1 申请需要在最近一次联盟变动之后发出
        2 申请需要在联盟锁定结束之后发出
        3 玩家当前不属于任何联盟
        """
        if self.is_belong_to_union():
            return False

        return application_time >= self.update_time and application_time >= self.lock_time


    def is_able_to_join(self, now):
        """是否可以加入联盟
        """
        if self.is_belong_to_union():
            return False

        return now >= self.lock_time


    def join_union(self, union_id, now):
        """加入联盟
        """
        assert self.is_able_to_join(now)
        self.union_id = union_id
        self.update_time = now

        self.forward_battle()


    def leave_union(self, union_id, now, initiative = True, force = False):
        """离开联盟
        Args:
            now
            initiative[bool]: 主动离开
        """
        if not force and self.union_id != union_id:
            logger.warning("Union not matched[union_id=%d][leave union_id=%d]" %
                    (self.union_id, union_id))
            return False

        self.union_id = 0
        self.aid_start_time = 0
        self.reset_battle_attack()
        self.battle_drum_count = 0

        #主动退出，有一个锁定时间，期间不允许加入其他联盟
        #if initiative:
        #    lock_time = int(float(data_loader.UnionConfInfo_dict["union_lock_time"].value))
        #    self.lock_time = now + lock_time
        lock_time = int(float(data_loader.UnionConfInfo_dict["union_lock_time"].value))
        self.lock_time = now + lock_time
        
        self.update_time = now
        return True


    def gain_honor(self, value):
        assert value >= 0
        self.honor += value
        logger.debug("Gain honor[value=%d]" % value)


    def consume_honor(self, value):
        assert value >= 0
        if value > self.honor:
            logger.warning("Honor is not enough[own=%d][need=%d]" % (self.honor, value))
            return False

        self.honor -= value
        logger.debug("Consume honor[value=%d]" % value)
        return True


    def is_able_to_start_aid(self, now):
        return self.aid_start_time == 0 and now >= self.aid_lock_time


    def start_aid(self, now):
        self.aid_start_time = now
        lock_time = int(float(data_loader.UnionConfInfo_dict["aid_lock_time"].value))
        self.aid_lock_time = now + lock_time


    def finish_aid(self):
        self.aid_start_time = 0


    def calc_update_cost_gold(self):
        cost_gold = int(float(data_loader.UnionConfInfo_dict["update_cost_gold"].value))
        return cost_gold


    def calc_aid_item_num(self, item_basic_id):
        item_level = data_loader.ItemBasicInfo_dict[item_basic_id].level
        return data_loader.UnionAidBasicInfo_dict[item_level].stoneNum


    def update_level(self, level):
        self.union_level = level


    def get_battle_mapping_node_basic_id(self):
        return int(float(
            data_loader.UnionConfInfo_dict["battle_mapping_node_basic_id"].value))

    @staticmethod
    def get_union_boss_node_basic_id():
        return int(float(
            data_loader.UnionConfInfo_dict["union_boss_node_basic_id"].value))

    def forward_season(self):
        """进入下一个赛季
        """
        self.season_score = 0
        self.reset_battle_attack()
        self.battle_drum_count = 0


    def forward_battle(self):
        """进入下一场战争
        """
        self.reset_battle_attack()
        self.battle_drum_count = 0


    def reset_battle_attack(self):
        """重置联盟战争信息
        """
        self.battle_attack_count_left = int(
                float(data_loader.UnionConfInfo_dict["battle_attack_count"].value))
        self.battle_attack_refresh_num = 0


    def refresh_battle_attack(self):
        """刷新联盟战争攻击次数
        """
        self.battle_attack_count_left = int(
                float(data_loader.UnionConfInfo_dict["battle_attack_count"].value))
        self.battle_attack_refresh_num += 1


    def calc_refresh_battle_requirement(self):
        """计算刷新联盟战争攻击次数的需求
        Returns:
            (cost_gold, vip_level): (消耗的元宝，需要的 vip 等级)
        """
        num = self.battle_attack_refresh_num + 1
        max_num = max(data_loader.UnionBattleAttackRefreshInfo_dict.keys())
        num = min(num, max_num)
        cost = data_loader.UnionBattleAttackRefreshInfo_dict[num].goldCost
        vip_level = data_loader.UnionBattleAttackRefreshInfo_dict[num].limitVipLevel
        return (cost, vip_level)


    def consume_battle_attack(self):
        """开始一场联盟战斗，消耗一次攻击次数
        """
        self.battle_attack_count_left -= 1
        assert self.battle_attack_count_left >= 0


    def gain_season_score_immediate(self, value):
        """获得赛季个人战功
        """
        assert value >= 0
        self.season_score += value


    def drum_for_union_battle(self, score, drum):
        """
        联盟战争中擂鼓
        """
        assert drum >= 0

        self.battle_drum_count += drum
        self.season_score += score


    def kills_for_union_battle(self, score, kills):
        """
        联盟战争中杀敌
        """
        assert kills >= 0
        assert score >= 0

        self.season_score += score


    def calc_drum_cost_gold(self, drum_count = 1):
        """计算擂鼓元宝消耗
        """
        max_count = max(data_loader.UnionBattleDrumCostInfo_dict.keys())
        gold = 0
        for i in range(drum_count):
            count = min(max_count, self.battle_drum_count + i + 1)
            gold += data_loader.UnionBattleDrumCostInfo_dict[count].goldCost
        return gold


    def attack_union_boss(self, score):
        """攻打联盟boss"""
        self.union_boss_attack_num += 1
        self.union_boss_score += score

    def get_union_boss_box_steps(self):
        """领过的个人战功宝箱index"""
        return utils.split_to_int(self.union_boss_box_steps)

    def accept_boss_score_box(self, step, honor):
        """领取个人战功宝箱"""
        acceptes_boxes = self.get_union_boss_box_steps()
        if step in acceptes_boxes:
            raise Exception("accepted union boss score box[step=%d]" % step)

        acceptes_boxes.append(step)
        self.union_boss_box_steps = utils.join_to_string(acceptes_boxes)
        self.gain_honor(honor)

    def get_remain_union_boss_attack_num(self):
        """获取剩下的攻击次数"""
        all_num = int(float(data_loader.UnionConfInfo_dict["union_boss_attack_count"].value))
        return all_num - self.union_boss_attack_num
        
    def reset_unionboss(self, last_update_time):
        """重置联盟boss"""
        self.union_boss_attack_num = 0
        self.union_boss_reset_num = 0
        self.union_boss_score = 0
        self.union_boss_box_steps = ""
        self.union_boss_last_update_time = last_update_time

    def reset_unionboss_attack(self):
        """重置攻击次数"""
        self.union_boss_attack_num = 0
        self.union_boss_reset_num += 1
