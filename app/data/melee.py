#coding:utf8
"""
Created on 2016-12-29
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 乱斗场相关
"""

import time
import random
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


INVALID_ARENA_NEXT_TIME = -1

FIRST_TITLE_LEVEL = 1    #段位的初始等级
INVALID_TITLE_LEVEL = 0

TOTAL_WIN_NUM_BY_REWARD = 15   #胜场奖励一天最多可以领多少场
MAX_RIVALS_NUM = 3      #演武场匹配对手的个数
DIFF_BATTLE_SCORE_RATIO = 0.25
CONTINUS_WIN_NUM = 10



class MeleeInfo(object):
    """乱斗场信息  (与ArenaInfo基本保持一致，以后可以考虑共用数据结构)
    """

    MELEE_RIVAL_BASE_ID = 110000
    MELEE_INDEX = 2

    def __init__(self, user_id = 0, node_id = 0,
            index = MELEE_INDEX,
            title_level = FIRST_TITLE_LEVEL, score = 0,
            coin = 0, round = 0, next_time = 0,
            rivals_user_id = '',
            choose_rival_index = 0,
            refresh_num = 0,
            continuous_win_num = 0,
            daily_win_num = 0,
            total_num = 0,
            highest_title_level = FIRST_TITLE_LEVEL,
            last_battle_win = False,
            current_win_num = 0,
            win_num_reward_basic_id = 0,
            chest_basic_id = 0,
            heroes_basic_id = '',
            heroes_position = ''):

        self.user_id = user_id
        self.node_id = node_id
        self.index = index      #房间号
        self.title_level = title_level    #段位(并不是实时更新，只用来计算是否升段位)
        self.score = score      #由房间号、积分拼成
        self.coin = coin        #演武场的代币
        self.round = round      #场次号
        self.next_time = next_time    #下一次状态变更的时间（演武场开启、关闭的时间）

        #匹配的对手
        self.rivals_user_id = rivals_user_id #存的是对手的user_id
        self.choose_rival_index = choose_rival_index    #系统选中的对手序号

        #统计项
        self.refresh_num = refresh_num
        self.continuous_win_num = continuous_win_num     #连胜
        self.daily_win_num = daily_win_num     #当天已胜场次
        self.total_num = total_num                       #战斗的场数
        self.highest_title_level = highest_title_level   #最高段位
        self.last_battle_win = last_battle_win    #上一场竞技场战斗是否胜利

        #胜场奖励
        self.current_win_num = current_win_num           #当前已胜几场
        self.win_num_reward_basic_id = win_num_reward_basic_id    #当前胜场数对应的奖励basic id
        self.chest_basic_id = chest_basic_id

        #保存乱斗的攻击阵容
        self.heroes_basic_id = heroes_basic_id
        self.heroes_position = heroes_position


    @staticmethod
    def create(user_id):
        """创建竞技场信息
        """
        melee = MeleeInfo(user_id)
        melee._set_score(0)      #由房间号、积分拼成
        melee._generate_win_num_reward()
        return melee


    @staticmethod
    def get_index_score_range(index):
        """获得竞技场某房间号对应的积分区间
        """
        min_score = 0
        max_score = 131071  #2^17 - 1
        return (index<<17 | min_score, index<<17 | max_score)


    @staticmethod
    def get_real_score(score):
        """获得实际的积分值
        """
        return score & 0x1FFFF


    def need_query_rank(self):
        """是否需要查询排名
          （当积分高于某一值后，排名会影响段位）
        """
        real_score = MeleeInfo.get_real_score(self.score)
        if real_score >= int(float(data_loader.OtherBasicInfo_dict["NeedQueryRankScore"].value)):
            return True
        else:
            return False


    def generate_arena_rivals_id(self):
        """为竞技场匹配的对手生成rival id
          每个玩家的演武场对手固定为3个rival id
        """
        return [self.user_id << 32 | MeleeInfo.MELEE_RIVAL_BASE_ID,
                self.user_id << 32 | (MeleeInfo.MELEE_RIVAL_BASE_ID + 1),
                self.user_id << 32 | (MeleeInfo.MELEE_RIVAL_BASE_ID + 2)]


    def get_arena_rival_id(self, rival_user_id):
        """返回匹配对手的rival id
        """
        rivals_user_id = utils.split_to_int(self.rivals_user_id)
        index = rivals_user_id.index(rival_user_id)
        return self.user_id << 32 | (MeleeInfo.MELEE_RIVAL_BASE_ID + index)


    def is_arena_rival_pve(self, rival_user_id):
        """pve对手的user_id范围为[0,1,2]
        """
        pve_user_ids = [0, 1, 2]
        if rival_user_id in pve_user_ids:
            return True
        else:
            return False


    def set_arena_rivals_user_id(self, rivals_user_id):
        """设置匹配对手的id
        """
        self.rivals_user_id = utils.join_to_string(rivals_user_id)


    def calc_gold_consume_of_refresh(self):
        """计算刷新对手的元宝消耗
        """
        refresh_num = self.refresh_num + 1

        max_num = max(data_loader.RefreshConsume_dict.keys())
        num = min(max_num, refresh_num)
        return int(data_loader.RefreshConsume_dict[num].goldNum)


    def _set_score(self, score):
        self.score = self.index << 17 | score


    def set_heroes_position(self, heroes_basic_id, heroes_position):
        """设置乱斗场攻击阵容
        """
        self.heroes_basic_id = utils.join_to_string(heroes_basic_id)
        self.heroes_position = utils.join_to_string(heroes_position)


    def get_heroes_position(self):
        """获取乱斗场攻击阵容
        """
        return (utils.split_to_int(self.heroes_basic_id), utils.split_to_int(self.heroes_position))


    def is_able_to_unlock(self, user):
        """
        """
        if user.level >= int(
                float(data_loader.OtherBasicInfo_dict["melee_arena_unlock_level"].value)):
            if user.allow_pvp_arena:
                return True
            else:
                return False
        else:
            return False


    def is_able_to_open(self, user, now):
        """副本是否能够打开
        """
        #if self.is_arena_open():
        #    return False

        if not self.is_able_to_unlock(user):
            return False

        if self._is_in_arena_open_duration(now):
            return True
        else:
            if not self._is_in_arena_open_day(now):
                return False
            else:
                server_first_hour = int(float(
                    data_loader.OtherBasicInfo_dict["ServerFirstHourEveryDay"].value))

                #活动数据
                open_time = data_loader.EventOpenTime_dict["melee"]
                arena_start_hour = open_time.startHour
                #当前时间
                local_time = time.localtime(now)
                hour = local_time.tm_hour
                if hour >= server_first_hour and hour < arena_start_hour:
                    return True
                else:
                    return False


    def is_arena_open(self):
        """副本是否存在（即随机事件是否开启）
        """
        return self.node_id != 0


    def is_arena_active(self, now):
        """演武场是否激活（即活动本身是否已启动）
        """
        if self._is_in_arena_open_duration(now):
            return True
        else:
            return False


    def is_arena_round_overdue(self, now):
        """竞技场轮次是否过时
        """
        if self._calc_arena_round(now) > self.round:
            return True
        else:
            return False


    def update_index(self, user_level):
        """升级房间号
        """
        self.index = self._calc_arena_index(user_level)
        real_score = MeleeInfo.get_real_score(self.score)
        self._set_score(real_score)


    def update_round(self, now):
        """更新竞技场轮次
        """
        self.round = self._calc_arena_round(now)


    def add_score(self, delta):
        """加积分（delta可为负）
        """
        real_score = MeleeInfo.get_real_score(self.score)
        real_score += delta

        if real_score < 0:
            real_score = 0   #积分最低扣到0分
        self._set_score(real_score)


    def gain_coin(self, addition):
        """获得代币
        """
        self.coin += addition
        self.coin = max(0, self.coin)


    def cost_coin(self, coin_cost):
        """消耗代币
        """
        assert coin_cost >= 0

        if self.coin < coin_cost:
            logger.warning("Not enough coin[own=%d][need=%d]" % (self.coin, coin_cost))
            return False

        self.coin -= coin_cost
        return True


    def update_title_level(self, new_title_level):
        """变更段位相关
        Returns:
            True:升段位   False:段位没有变化
        """

        if new_title_level == INVALID_TITLE_LEVEL:
            logger.warning("Calc arena title level error")
            return False

        self.title_level = new_title_level
        if self.highest_title_level < new_title_level:
            #升段位
            self.highest_title_level = new_title_level
            return True
        else:
            return False


    def calc_arena_buff_id(self, rank):
        """计算buff basic id
        """
        title_level = self.calc_arena_title_level(rank)
        new_key = "%s_%s" % (self.index, title_level)
        return data_loader.GradeBasicInfo_dict[new_key].buffId


    def calc_arena_title_level(self, rank):
        """计算段位
        """
        score = MeleeInfo.get_real_score(self.score)
        index = self.index

        for key in data_loader.GradeBasicInfo_dict:
            grade_basic_info = data_loader.GradeBasicInfo_dict[key]
            if index != int(float(grade_basic_info.arenaIndex)):
                continue

            limit_score = int(float(grade_basic_info.limitScore))
            limit_max_score = int(float(grade_basic_info.limitMaxScore))
            limit_rank = int(float(grade_basic_info.limitRank))
            limit_max_rank = int(float(grade_basic_info.limitMaxRank))
            title_level = int(float(grade_basic_info.titleLevel))
            if limit_rank == 0:
                #只看积分范围，不管排名
                if score >= limit_score and score <= limit_max_score:
                    return title_level
            else:
                #积分范围和排名都要管
                if (score >= limit_score and score <= limit_max_score and
                        rank <= limit_rank and rank >= limit_max_rank):
                    return title_level

        return INVALID_TITLE_LEVEL


    def calc_decay_score(self):
        """计算积分衰减（退一档，低于等于1600就不再衰减） 
        """
        SCORE_LIMIT = 1600
        index = self.index
        real_score = MeleeInfo.get_real_score(self.score)
        
        if real_score < SCORE_LIMIT:
            return real_score

        key = "%d_%d" % (index, self.title_level)
        limit_score = data_loader.GradeBasicInfo_dict[key].limitScore
        new_score = limit_score
        new_title_level = self.title_level

        while True:
            if new_score < limit_score:
                break

            new_title_level = new_title_level - 1
            new_key = "%d_%d" % (index, new_title_level)
            if new_key not in data_loader.GradeBasicInfo_dict: 
                break

            new_score = data_loader.GradeBasicInfo_dict[new_key].limitScore

        if real_score > SCORE_LIMIT and new_score < SCORE_LIMIT:
            return (0, SCORE_LIMIT)
        else:
            return max(0, new_score)


    def update_next_time(self, now):
        """更新下一次竞技场查询请求的时间
        """
        self.next_time = self._calc_next_time(now)


    def refresh(self):
        """
        """
        self.refresh_num += 1


    def is_able_to_get_win_num_reward(self):
        """判断是否还有胜场奖励领
        """
        if self.daily_win_num > TOTAL_WIN_NUM_BY_REWARD or self.chest_basic_id == 0:
            return False
        else:
            return True


    def get_win_num_reward(self):
        """领取胜场奖励
        """
        win_num_reward = data_loader.ArenaWinNumRewardBasicInfo_dict[
                self.win_num_reward_basic_id]
        need_win_num = int(float(win_num_reward.needWinNum))
        if self.current_win_num < need_win_num:
            logger.warning("Cannot get win num reward[win_num=%d]" % self.win_num_reward_basic_id)
            return False

        self.current_win_num -= need_win_num
        #生成新的胜场奖励数据
        if self.daily_win_num <= TOTAL_WIN_NUM_BY_REWARD:
            self._generate_win_num_reward()
        else:
            self.win_num_reward_basic_id = 0
            self.chest_basic_id = 0


        return True


    def _generate_win_num_reward(self):
        """生成新的胜场奖励
        """
        key = "%s_%s" % (self.index, self.title_level)
        self.win_num_reward_basic_id = random.sample(data_loader.GradeBasicInfo_dict[key].winNumRewardIds, 1)[0]
        self.chest_basic_id = random.sample(data_loader.ArenaWinNumRewardBasicInfo_dict[
            self.win_num_reward_basic_id].chestIds, 1)[0]


    def get_round_end_time(self):
        """获取当前round轮的end_time
        """
        #活动数据
        open_time = data_loader.EventOpenTime_dict["melee"]
        arena_days = open_time.weekday
        arena_start_hour = open_time.startHour
        arena_duration = open_time.duration
        #开服的时间
        first_time = int(float(data_loader.OtherBasicInfo_dict["ArenaFirstDate"].value))
        tmp = str(first_time)
        first_timestamp = int(time.mktime(time.strptime(tmp, "%Y%m%d")))

        div_num = self.round / len(arena_days) #距离开服已经经过了几周
        mod_num = self.round % len(arena_days)

        if mod_num == 0:
            round_end_time = (first_timestamp + (div_num - 1) * 604800
                    + (arena_days[-1] - 1) * 86400 + (arena_start_hour + arena_duration) * 3600)
        else:
            round_end_time = (first_timestamp + div_num * 604800
                    + (arena_days[mod_num - 1] - 1) * 86400 + (arena_start_hour + arena_duration) * 3600)

        return round_end_time


    def open(self, node, user, now):
        """开启副本
        """
        if not self.is_able_to_open(user, now):
            logger.warning("Arena can not open")
            return False

        self.node_id = node.id

        return True


    def close(self):
        """关闭副本
        """
        self.node_id = 0


    def clear(self):
        """活动结束,结算奖励后须清理数据
        """
        self.refresh_num = 0
        self.continuous_win_num = 0
        self.daily_win_num = 0
        self.current_win_num = 0
        self.win_num_reward_basic_id = 0
        self.chest_basic_id = 0
        self.last_battle_win = False
        self._generate_win_num_reward()


    def reset_highest_title_level(self):
        """
        """
        self.highest_title_level = FIRST_TITLE_LEVEL



    def battle_finish(self, is_win, diff_score):
        """对战后结算
        """
        if is_win:
            if self.continuous_win_num < 0:
                #停止连败的记录
                self.continuous_win_num = 1
            else:
                #继续连胜的记录
                self.continuous_win_num += 1
            self.current_win_num += 1
            self.daily_win_num += 1
            self.last_battle_win = True
        else:
            if self.continuous_win_num > 0:
                #停止连胜的记录
                self.continuous_win_num = -1
            else:
                #继续连败的记录
                self.continuous_win_num -= 1
            self.last_battle_win = False

        self.add_score(diff_score)
        self.total_num += 1


    def reset_last_battle_win(self):
        """重置last_battle_win
        """
        self.last_battle_win = False


    def _is_in_arena_open_day(self, now):
        """当前时间是否处在活动开放的当天
        """
        local_time = time.localtime(now)
        wday = local_time.tm_wday + 1     #localtime的星期一是0

        open_time = data_loader.EventOpenTime_dict["melee"]
        arena_days = open_time.weekday
        if wday in arena_days:
            return True
        else:
            return False


    def _is_in_arena_open_duration(self, now):
        """当前时间是否处在活动期间内
        （tips:某一天活动的起始时间+持续时间，不能和下一次活动开启的时间有重叠）
        """
        #配置
        open_time = data_loader.EventOpenTime_dict["melee"]
        arena_days = open_time.weekday
        arena_start_hour = open_time.startHour
        arena_duration = open_time.duration

        #算出活动开启的小时区间集合
        duration_hours = []
        for day in arena_days:
            start = (day - 1) * 24 + arena_start_hour
            end = start + arena_duration
            if end > 168:
                duration_hours.append((start, 168))
                duration_hours.append((0, end - 168))
            else:
                duration_hours.append((start, end))

        #当前时间
        local_time = time.localtime(now)
        wday = local_time.tm_wday + 1     #localtime的星期一是0
        hour = local_time.tm_hour

        arena_hour = (wday - 1) * 24 + hour

        for duration in duration_hours:
            if arena_hour >= duration[0] and arena_hour < duration[1]:
                return True

        return False


    def _calc_arena_index(self, user_level):
        """计算乱斗场的房间号
        """
        #for key in data_loader.ArenaBasicInfo_dict:
        #    arena_basic_info = data_loader.ArenaBasicInfo_dict[key]
        #    minLevel = arena_basic_info.minLevel
        #    maxLevel = arena_basic_info.maxLevel
        #    if user_level >= minLevel and user_level <= maxLevel:
        #        return int(float(arena_basic_info.index))
        #return INVALID_ARENA_INDEX

        #以前根据level等级分房间，现在不分了
        return MeleeInfo.MELEE_INDEX


    def _calc_arena_round(self, now):
        """计算竞技场的轮次(tips:此计算逻辑暂时不能处理跨天情况)
        """
        #活动数据
        open_time = data_loader.EventOpenTime_dict["melee"]
        arena_days = open_time.weekday
        arena_start_hour = open_time.startHour
        arena_end_hour = open_time.startHour + open_time.duration
        #当前时间
        local_time = time.localtime(now)
        wday = local_time.tm_wday + 1
        hour = local_time.tm_hour
        min = local_time.tm_min
        sec = local_time.tm_sec
        #开服的时间(目前逻辑是计算起始时间必须是周一，否则会错)
        first_time = int(float(data_loader.OtherBasicInfo_dict["ArenaFirstDate"].value))
        tmp = str(first_time)
        first_timestamp = int(time.mktime(time.strptime(tmp, "%Y%m%d")))

        #距离开服已经经过了几周
        week_num = (int(now) - first_timestamp) / 604800

        round = 0
        last_day = 0
        for day in arena_days:
            if wday >= day:
                round += 1
                last_day = day

        if wday > last_day:
            round += 1    #对应的是下一轮开启活动的round
        elif wday == last_day:
            if hour >= arena_end_hour and (min >= 0 or sec >= 0):
                round += 1    #对应的是下一轮开启活动的round

        return week_num * len(arena_days) + round


    def _calc_next_time(self, now):
        """
        """
        #配置
        open_time = data_loader.EventOpenTime_dict["melee"]
        arena_days = open_time.weekday
        arena_start_hour = open_time.startHour
        arena_duration = open_time.duration

        #时间区间
        duration_hours = []
        last_end = 0
        for day in arena_days:
            start = (day - 1) * 24 + arena_start_hour
            end = start + arena_duration

            duration_hours.append((last_end, start))
            duration_hours.append((start, end))

            last_end = end
        if last_end < 168:
            duration_hours.append((last_end, 168 + (arena_days[0] - 1)*24 + arena_start_hour))

        #当前时间
        local_time = time.localtime(now)
        wday = local_time.tm_wday + 1
        hour = local_time.tm_hour
        min = local_time.tm_min
        sec = local_time.tm_sec

        arena_hour = (wday - 1) * 24 + hour

        hour_diff = 0
        min_diff = 0 - min
        sec_diff = 0 - sec

        for duration in duration_hours:
            if arena_hour >= duration[0] and arena_hour < duration[1]:
                hour_diff = duration[1] - arena_hour
                break

        next_time = now + hour_diff * 3600 + min_diff * 60 + sec_diff
        logger.debug("next_time is %d" % next_time)
        return next_time


    def get_node_basic_id(self):
        return int(float(data_loader.MapConfInfo_dict['arena_node_basic_id'].value))
