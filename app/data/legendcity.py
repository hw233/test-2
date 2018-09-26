#coding:utf8
"""
Created on 2016-05-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城官职相关数据存储结构
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class LegendCityInfo(object):
    """史实城匹配的对手信息
    """
    BUFF_MAX_NUM = 3

    __slots__ = [
            "id",
            "user_id",
            "city_id",
            "node_id",
            "attack_count",
            "reset_attack_num",
            "buffs",
            "buffs_start_time",
            "rivals_id",
            "rivals_is_robot",
            "rivals_position_level",
            "update_time",
            "record_index",
            ]


    def __init__(self):
        self.id = 0
        self.user_id = 0
        self.city_id = 0
        self.node_id = 0
        self.attack_count = 0
        self.reset_attack_num = 0
        self.buffs = ''
        self.buffs_start_time = ''
        self.rivals_id = ''
        self.rivals_is_robot = ''
        self.rivals_position_level = ''
        self.update_time = 0
        self.record_index = 0

    @staticmethod
    def create(user_id, city_id, node_id, now):
        """创建
        """
        info = LegendCityInfo()
        info.id = LegendCityInfo.generate_id(user_id, city_id)
        info.user_id = user_id
        info.city_id = city_id
        info.node_id = node_id
        info.attack_count = 0
        info.reset_attack_num = 0

        info.buffs = utils.join_to_string([0] * LegendCityInfo.BUFF_MAX_NUM)
        info.buffs_start_time = utils.join_to_string([0] * LegendCityInfo.BUFF_MAX_NUM)

        info.rivals_id = ""
        info.rivals_is_robot = ""
        info.rivals_position_level = ""

        info.update_time = now
        info.record_index = 0
        return info


    @staticmethod
    def generate_id(user_id, city_id):
        id = user_id << 32 | city_id
        return id


    def get_rivals_info(self):
        info = []
        rivals_id = utils.split_to_int(self.rivals_id)
        rivals_is_robot = utils.split_to_int(self.rivals_is_robot)
        rivals_position_level = utils.split_to_int(self.rivals_position_level)
        for index in range(0, len(rivals_id)):
            info.append((
                        rivals_id[index],
                        bool(rivals_is_robot[index]),
                        rivals_position_level[index]))

        return info


    def get_rival_info(self, rival_id):
        info = []
        rivals_id = utils.split_to_int(self.rivals_id)
        rivals_is_robot = utils.split_to_int(self.rivals_is_robot)
        rivals_position_level = utils.split_to_int(self.rivals_position_level)

        index = rivals_id.index(rival_id)
        return (rivals_id[index],
                bool(rivals_is_robot[index]),
                rivals_position_level[index])


    def change_rivals(self, delete_rivals_id, rivals_info, now):
        """更改对手
        """
        rivals_id = utils.split_to_int(self.rivals_id)
        rivals_is_robot = utils.split_to_int(self.rivals_is_robot)
        rivals_position_level = utils.split_to_int(self.rivals_position_level)

        for id in delete_rivals_id:
            if id not in rivals_id:
                continue
            index = rivals_id.index(id)
            rivals_position_level.pop(index)
            rivals_is_robot.pop(index)
            rivals_id.pop(index)

        for (id, is_robot, position) in rivals_info:
            rivals_id.append(id)
            rivals_is_robot.append(int(is_robot))
            rivals_position_level.append(position)

        self.rivals_id = utils.join_to_string(rivals_id)
        self.rivals_is_robot = utils.join_to_string(rivals_is_robot)
        self.rivals_position_level = utils.join_to_string(rivals_position_level)
        self.update_time = now

        logger.debug("change rivals[rivals_id=%s][is_robot=%s][position_level=%s]" %
                (self.rivals_id, self.rivals_is_robot, self.rivals_position_level))


    def get_next_record_index(self):
        self.record_index += 1
        return self.record_index


    def get_attack_count_left(self):
        max_count = int(float(
            data_loader.MapConfInfo_dict["legendcity_attack_count_max"].value))
        return max_count - self.attack_count


    def reset_attack_count_daily_auto(self):
        """每天自动重置攻击次数
        """
        self.attack_count = 0
        self.reset_attack_num = 0


    def reset_attack_count(self, cost_gold):
        num = self.reset_attack_num + 1
        if num not in data_loader.LegendCityAttackResetBasicInfo_dict:
            num = max(data_loader.LegendCityAttackResetBasicInfo_dict.keys())

        need = data_loader.LegendCityAttackResetBasicInfo_dict[num].costGold
        if need != cost_gold:
            logger.warning("Reset attack count failed[need gold=%d][cost gold=%d]" %
                    (need, cost_gold))
            return False

        self.reset_attack_num += 1
        self.attack_count = 0
        return True


    def add_attack_count(self):
        assert self.is_able_to_attack()
        self.attack_count += 1


    def is_able_to_attack(self):
        max_count = int(float(
            data_loader.MapConfInfo_dict["legendcity_attack_count_max"].value))
        return self.attack_count < max_count


    def get_buff_gold_cost(self, buff_id):
        """计算 buff 消耗的金钱
        """
        return data_loader.LegendCityBuffBasicInfo_dict[buff_id].costGold


    def add_default_buff(self, position_level, now):
        """添加官职默认 buff
        """
        key = "%d_%d" % (self.city_id, position_level)
        buff_id = data_loader.LegendCityPositionBasicInfo_dict[key].defaultCityBuffId
        if buff_id != 0:
            self.add_buff(buff_id, now)


    def check_buff_available(self, buff_id, item_basic_id):
        if data_loader.LegendCityBuffBasicInfo_dict[buff_id].itemBasicId != item_basic_id:
            logger.warning("Legendcity buff and item are not matched"
                    "[buff_id=%d][item_basic_id=%d]" %
                    (buff_id, item_basic_id))
            return False
        return True


    def add_buff(self, buff_id, now):
        """添加 buff
        """
        buffs = utils.split_to_int(self.buffs)
        buffs_start_time = utils.split_to_int(self.buffs_start_time)

        #清除已经过期的 buff
        for index in range(0, len(buffs)):
            id = buffs[index]
            if id == 0:
                continue
            end_time = (buffs_start_time[index] +
                    data_loader.LegendCityBuffBasicInfo_dict[id].duration)
            if now >= end_time:
                buffs[index] = 0

        ok = False
        for index in range(0, len(buffs)):
            if buffs[index] == 0:
                buffs[index] = buff_id
                buffs_start_time[index] = now
                ok = True
                break

        if not ok:
            logger.warning("Not able to add legendcity buff")
            return False

        self.buffs = utils.join_to_string(buffs)
        self.buffs_start_time = utils.join_to_string(buffs_start_time)
        return True


    def get_buffs(self, now):
        """获取所有 buff
        """
        info = []

        buffs = utils.split_to_int(self.buffs)
        buffs_start_time = utils.split_to_int(self.buffs_start_time)
        for index in range(0, len(buffs)):
            buff_id = buffs[index]
            if buff_id != 0:
                start_time = buffs_start_time[index]
                duration = data_loader.LegendCityBuffBasicInfo_dict[buff_id].duration
                left_time = start_time + duration - now
                if left_time > 0:
                    info.append((buff_id, left_time))

        return info


    def calc_rematch_cost(self, rival_position_level):
        """计算重新匹配对手的费用
        """
        key = "%d_%d" % (self.city_id, rival_position_level)
        info = data_loader.LegendCityPositionBasicInfo_dict[key]
        assert info.cityId == self.city_id
        return info.rematchCostGold


    def calc_challenge_cost(self, user_position_level, rival_position_level):
        """计算挑战费用
        """
        #如果玩家官职，比对手低一级，则不需要费用
        if user_position_level + 1 == rival_position_level:
            return 0

        key = "%d_%d" % (self.city_id, rival_position_level)
        rival_info = data_loader.LegendCityPositionBasicInfo_dict[key]
        return rival_info.challengeCostGold



class LegendCityRecordInfo(object):
    """史实城战斗记录信息
    """

    __slots__ = [
            "id",
            "user_id",
            "city_id",
            "index",
            "is_win",
            "is_attacker",
            "time",
            "user_name",
            "user_level",
            "user_position_level",
            "user_icon",
            "user_buffs",
            "user_battle_score",
            "rival_id",
            "rival_name",
            "rival_level",
            "rival_position_level",
            "rival_icon",
            "rival_buffs",
            "rival_battle_score",
            ]


    @staticmethod
    def create(user_id, city_id, index):
        info = LegendCityRecordInfo()
        info.id = LegendCityRecordInfo.generate_id(user_id, city_id, index)
        info.user_id = user_id
        info.city_id = city_id
        info.index = index
        return info


    @staticmethod
    def generate_id(user_id, city_id, index):
        id = user_id << 32 | city_id << 16 | index
        return id


    def set_result(self, is_win, is_attacker, time):
        self.is_win = is_win
        self.is_attacker = is_attacker
        self.time = time


    def set_user(self, user, battle_score, position_level, buffs):
        self.user_name = base64.b64encode(user.get_readable_name())
        self.user_level = user.level
        self.user_icon = user.icon_id
        self.user_position_level = position_level
        self.user_buffs = buffs
        self.user_battle_score = battle_score


    def set_rival(self, rival, position_level, buffs):
        self.rival_id = rival.rival_id
        self.rival_name = base64.b64encode(rival.get_readable_name())
        self.rival_level = rival.level
        self.rival_icon = rival.icon_id
        self.rival_position_level = position_level
        self.rival_buffs = buffs
        self.rival_battle_score = rival.score


    def set_rival_detail(self,
            rival_id, rival_name, rival_level, rival_icon, rival_battle_score,
            position_level, buffs):
        self.rival_id = rival_id
        self.rival_name = base64.b64encode(rival_name)
        self.rival_level = rival_level
        self.rival_icon = rival_icon
        self.rival_position_level = position_level
        self.rival_buffs = buffs
        self.rival_battle_score = rival_battle_score


    def get_readable_user_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.user_name)


    def get_readable_rival_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.rival_name)


    def get_user_buffs(self):
        return [buff_id for buff_id in utils.split_to_int(self.user_buffs)
                if buff_id != 0]


    def get_rival_buffs(self):
        return [buff_id for buff_id in utils.split_to_int(self.rival_buffs)
                if buff_id != 0]

