#coding:utf8
"""
Created on 2015-02-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 用户（monarch）数值相关计算
"""
import random
import math
import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app import log_formater

TEAM_COUNT_MAX = 3

class UserInfo(object):

    __slots__ = [
            "id",
            "level",
            "exp",
            "vip_level",
            "vip_points",
            "name",
            "icon_id",
            "create_time",
            "last_login_time",
            "is_first_money_draw",
            "is_first_gold_draw",
            "guide",
            "cdkey",
            "team_count",
            "allow_pvp",
            "allow_pvp_arena",
            "chat_available",
            "chat_lock_time",
            "exchange_num",
            "last_refresh_exchange_time",
            "inviter",
            "invitee",
            "invitee_level",
            "country",
            "in_protect",
            "friends_apply",
            "friends",
            ]

    def __init__(self, id = 0,
            level = 1, exp = 0, vip_level = 0, vip_points = 0,
            name = '', icon_id = 0, create_time = 0, last_login_time = 0,
            is_first_money_draw = True,
            is_first_gold_draw = True,
            guide = '',
            cdkey = '',
            team_count = 0,
            allow_pvp = False,
            allow_pvp_arena = False,
            exchange_num = 0, last_refresh_exchange_time = 0,
            inviter = 0, invitee = '', invitee_level = '',
            country = 0, in_protect = False, friends_apply = '', friends = ''):
        self.id = id
        self.level = level
        self.exp = exp
        self.vip_level = vip_level
        self.vip_points = vip_points
        self.name = name
        self.icon_id = icon_id

        self.create_time = create_time
        self.last_login_time = last_login_time
        self.is_first_money_draw = is_first_money_draw
        self.is_first_gold_draw = is_first_gold_draw

        self.guide = guide
        self.cdkey = cdkey #玩家领取的 CDkey 类型（同一种类型只允许领取一次）

        self.team_count = team_count #主公可上阵队伍数量

        self.allow_pvp = allow_pvp
        self.allow_pvp_arena = allow_pvp_arena

        self.chat_available = True
        self.chat_lock_time = 0

        self.exchange_num = exchange_num
        self.last_refresh_exchange_time = last_refresh_exchange_time
        self.inviter = inviter
        self.invitee = invitee
        self.invitee_level = invitee_level
        self.country = random.randint(1, 3)
        self.in_protect = in_protect
        self.friends_apply = friends_apply
        self.friends = friends


    @staticmethod
    def create(id, now):
        """生成一个新的用户信息
        Args:
            id[int]: 用户 id
        Returns:
            user[UserInfo]
        """
        user = UserInfo(id)
        user.create_time = now

        #从vip表里挑出buyGold为0且level最大的作为初始vip_level:
        vip_level = 0
        for level in data_loader.VipBasicInfo_dict:
            info = data_loader.VipBasicInfo_dict[level]
            if info.buyGold == 0 and info.level > vip_level:
                vip_level = info.level
        user.vip_level = vip_level

        return user

    @staticmethod
    def get_day_exchange_num(vip_level):
        """获取每日兑换的次数"""
        return data_loader.VipBasicInfo_dict[vip_level].resourceExchangeNumLimit

    def day_exchange_num(self):
        return self.get_day_exchange_num(self.vip_level)


    def level_up(self, exp, str, type):
        """计算主公获得经验值之后的等级状态
        1 等级不会超过上限
        2 等级达到上限后，exp 最大为到达下一等级所需的经验
        Args:
            user[UserInfo out]: 用户（monarch）的信息
            exp[int]: 增加的经验值
        Returns:
            True: 升级成功
            False: 升级失败
        """
        max_level = int(float(data_loader.OtherBasicInfo_dict["MaxMonarchLevel"].value))
        exp_levelup = data_loader.MonarchLevelBasicInfo_dict[self.level+1].exp
        if self.level == max_level and self.exp == exp_levelup:
            #等级达到满级，经验值也无法增加，则升级失败
            logger.warning("User level reach ceiling[level=%d][exp=%d]" %
                    (self.level, self.exp))
            log = log_formater.output_exp(self, str, type, exp, self.level, self.exp)
            logger.notice(log)
            return False

        self.exp += exp
        while self.exp >= exp_levelup:#可以升级
            if self.level == max_level:
                self.exp += exp
                if self.exp > exp_levelup:
                    self.exp = exp_levelup
                return True

            self.exp -= exp_levelup
            self.level += 1
            exp_levelup = data_loader.MonarchLevelBasicInfo_dict[self.level+1].exp
        log = log_formater.output_exp(self, str, type, exp, self.level, self.exp)                                                            
        logger.notice(log)

        return True


    def calc_change_name_gold_cost(self):
        """改名字的元宝花费
        """
        return int(float(data_loader.OtherBasicInfo_dict["change_name_cost_gold"].value))


    def change_name(self, new_name):
        """更换名称
        """
        if not isinstance(new_name, str):
            logger.warning("Invalid type")
            return False

        #名字用 base64 编码存储，避免一些非法字符造成的问题
        self.name = base64.b64encode(new_name)
        return True


    def get_readable_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.name)


    def change_icon(self, new_icon_id):
        """更换显示图标
        """
        if not isinstance(new_icon_id, int):
            logger.warning("Invalid type")
            return False

        self.icon_id = new_icon_id
        return True


    def login(self, now):
        self.last_login_time = now


    def unlock_pvp(self):
        assert self.allow_pvp is False
        self.allow_pvp = True


    def unlock_pvp_arena(self):
        assert self.allow_pvp_arena is False
        self.allow_pvp_arena = True


    #TODO 放到新手引导流程中
    def mark_gold_draw(self):
        self.is_first_gold_draw = False


    def mark_money_draw(self):
        self.is_first_money_draw = False


    def get_guide_progress(self):
        return utils.split_to_int(self.guide)


    def reset_guide_stage(self, stage):
        finish = self.get_guide_progress()
        if stage not in finish:
            logger.warning("Guide stage is finished[stage=%d]" % stage)
            return False

        finish.remove(stage)
        self.guide = utils.join_to_string(finish)
        logger.debug("Reset guide stage[stage=%d]" % stage)
        return True


    def finish_guide_stage(self, stage):
        finish = self.get_guide_progress()
        if stage in finish:
            logger.warning("Guide stage is finished[stage=%d]" % stage)
            return False

        finish.append(stage)
        self.guide = utils.join_to_string(finish)
        logger.debug("Finish guide stage[stage=%d]" % stage)
        return True


    def is_cdkey_valid(self, bag_id):
        """用户是否可以使用激活码
        同一种类型的激活码，只允许使用一次
        """
        ids = utils.split_to_int(self.cdkey)
        if bag_id in ids:
            return False
        return True


    def use_cdkey(self, bag_id):
        """使用激活码
        """
        ids = utils.split_to_int(self.cdkey)
        assert bag_id not in ids
        ids.append(bag_id)
        self.cdkey = utils.join_to_string(ids)


    def is_basic_guide_finish(self):
        LAST_BASIC_STAGE = 100
        stages = self.get_guide_progress()
        return LAST_BASIC_STAGE in stages


    def update_team_count(self, count):
        """更新可上阵的队伍数量
        Returns:
            True: 发生了更新
            False: 未发生更新
        """
        assert count >= 0 and count <= TEAM_COUNT_MAX
        if count > self.team_count:
            self.team_count = count
            logger.debug("update team count[count=%d]" % self.team_count)
            return True
        return False


    def gain_vip_points(self, pay_price):
        """
        """
        old_exchange_num = self.day_exchange_num()

        #针对韩国地区的临时处理（韩币数值很大，浮点数算出来有误差）
        price2gold = {}
        price2gold[1100] = 60 
        price2gold[5500] = 300
        price2gold[11000] = 600
        price2gold[33000] = 1800
        price2gold[55000] = 3000
        price2gold[110000] = 6000
        price2gold[4400] = 300
        price2gold[12100] = 700

        if price2gold.has_key(pay_price):
            gain_points = price2gold[pay_price]
        else:
            ratio = float(
                data_loader.OtherBasicInfo_dict["ratio_pay_price_to_vip_points"].value)
            gain_points = int(pay_price * ratio)

        self.vip_points += gain_points

        max_vip_level = max(data_loader.VipBasicInfo_dict.keys())

        while self.vip_level < max_vip_level:
            next_level_points = data_loader.VipBasicInfo_dict[self.vip_level + 1].buyGold
            if self.vip_points >= next_level_points:
                self.vip_level += 1
            else:
                break

        new_exchange_num = self.day_exchange_num()
        self.exchange_num += new_exchange_num - old_exchange_num

        return True


    def is_chat_available(self, now):
        """当前聊天是否可用
        """
        if self.chat_available:
            return True
        else:
            if self.chat_lock_time == 0:
                return False
            else:
                return now >= self.chat_lock_time


    def disable_chat(self, now, lock_min = 0):
        """禁止聊天
        """
        self.chat_available = False
        if lock_min == 0:
            self.chat_lock_time = 0
        else:
            self.chat_lock_time = now + lock_min * 60


    def enable_chat(self):
        """允许聊天
        """
        self.chat_available = True

    def get_invite_code(self):
        """获取分享code
        """
        return utils.encode(str(self.id), utils.INVITE_CODE_KEY)

    def is_invited(self):
        """是否被邀请过
        """
        return self.inviter > 0

    def set_inviter(self, inviter_id):
        """被邀请
        """
        self.inviter = inviter_id


    def add_invitee(self, invitee_id, level):
        """增加受请人,若受请数量已达上限则返回False,成功返回True
        """
        invitees = utils.split_to_int(self.invitee)
        if len(invitees) >= 15:
            return False
        invitees.append(invitee_id)
        self.invitee = utils.join_to_string(invitees)
        invitee_levels = utils.split_to_int(self.invitee_level)
        invitee_levels.append(level)
        self.invitee_level = utils.join_to_string(invitee_levels)
        return True


    def update_invitee(self, invitee_id, level):
        """更新受请人等级"""
        invitees = utils.split_to_int(self.invitee)
        invitee_levels = utils.split_to_int(self.invitee_level)
        for i in range(0, len(invitees)):
            if invitees[i] == invitee_id:
                invitee_levels[i] = level
        self.invitee_level = utils.join_to_string(invitee_levels)

   
    def update_country(self, new_country):
       """更新国家势力
       """
       if new_country != 1 and new_country != 2 and new_country != 3:
           logger.warning("Error country")
           return 

       self.country = new_country

   
    def set_in_protect(self, status):
       """设置主城是否处于保护状态
       """
       self.in_protect = status


