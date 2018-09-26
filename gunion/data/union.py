#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟相关数据存储结构
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class UnionInfo(object):
    """联盟信息
    """

    JOIN_STATUS_ENABLE = 1 #允许任何人加入
    JOIN_STATUS_VERIFY = 2 #需要验证
    JOIN_STATUS_DISABLE = 3#不允许任何人加入

    __slots__ = [
            "id",
            "name",
            "icon",
            "level",

            "announcement",
            "current_number",
            "max_number",

            "leader_user_id",
            "vice_user_id",

            "join_status",
            "join_level_limit",

            "today_prosperity",
            "history_prosperity",
            "recent_prosperity",
            "recent_prosperity_record",
            "update_time",

            "chatroom",
            "chatpasswd",

            "create_time",
            "available",

            "donate_index",
            "donate_last_refresh_time",
            "donate_last_auto_time",

            "boss_group",       #当前的boss组, 为0表示当前无boss
            "boss_step",        #打到第几个boss, = 10表示全部打完
            "bosses_id",
            "boss_last_update_time",    #boss上次重置的时间
            "boss_last_change_time",    #boss上次换阵容的时间
            ]

    def __init__(self):
        self.id = id
        self.name = ''
        self.icon = 0

        self.level = 1

        self.announcement = ''

        self.current_number = 0
        self.max_number = 0
        self.join_status = UnionInfo.JOIN_STATUS_VERIFY
        self.join_level_limit = 0

        self.leader_user_id = 0
        self.vice_user_id = ''

        self.today_prosperity = 0
        self.history_prosperity = 0
        self.recent_prosperity = 0
        self.recent_prosperity_record = "0"
        self.update_time = 0

        self.chatroom = ""
        self.chatpasswd = ""

        self.create_time = 0
        self.available = True

        self.donate_index = 0
        self.donate_last_refresh_time = 0
        self.donate_last_auto_time = 0

        self.boss_group = 0
        self.boss_step = 0
        self.bosses_id = ""
        self.boss_last_update_time = 0
        self.boss_last_change_time = 0

    @staticmethod
    def create(id, name, icon, now):
        union = UnionInfo()
        union.id = id
        union.change_name(name)
        union.change_icon(icon)

        union.level = 1#TODO 目前默认1级

        union.change_announcement(
                data_loader.UnionConfInfo_dict["default_announcement"].value.encode("utf-8"))

        union.current_number = 0
        union.max_number = int(float(
            data_loader.UnionConfInfo_dict["default_max_number"].value))
        union.join_status = UnionInfo.JOIN_STATUS_VERIFY
        union.join_level_limit = int(float(
            data_loader.UnionConfInfo_dict["default_level_min"].value))

        union.leader_user_id = 0
        union.vice_user_id = ''

        #繁荣度
        union.today_prosperity = 0
        union.history_prosperity = 0
        union.recent_prosperity = 0
        union.recent_prosperity_record = "0"
        union.update_time = now

        #聊天
        union.chatroom = ""
        union.chatpasswd = ""

        union.create_time = now
        union.available = True

        #联盟捐献
        union.donate_index = 0
        union.donate_last_refresh_time = 0
        union.donate_last_auto_time = 0

        #联盟boss
        union.boss_group = 0
        union.boss_step = 0
        union.bosses_id = ""
        union.boss_last_update_time = 0
        union.boss_last_change_time = 0
        return union


    def calc_chatroom(self, server_id, roomprefix, chatservice):
        """计算聊天室信息
        """
        self.chatroom = "%s-%d-%d@%s" % (
                roomprefix, server_id, self.id, chatservice)
        self.chatpasswd = utils.random_alphanumeric()


    def dismiss(self):
        """解散
        """
        self.available = False


    def set_as_leader(self, user_id):
        """设置为盟主
        """
        #如果是副盟主
        ids = utils.split_to_int(self.vice_user_id)
        if user_id in ids:
            ids.remove(user_id)
        self.vice_user_id = utils.join_to_string(ids)

        self.leader_user_id = user_id
        logger.debug("Set leader[user_id=%d]" % user_id)


    def set_as_vice_leader(self, user_id):
        """设置为副盟主
        """
        max_num = int(float(data_loader.UnionConfInfo_dict["union_vice_leader_number"].value))

        ids = utils.split_to_int(self.vice_user_id)
        if user_id in ids or len(ids) >= max_num:
            #已经是副盟主，或者人数已满
            logger.warning("Unable to set vice leader[current vice leader=%s][user_id=%d]" %
                    (self.vice_user_id, user_id))
            return False

        ids.append(user_id)
        self.vice_user_id = utils.join_to_string(ids)
        logger.debug("Set vice leader[current vice leader=%s]" % self.vice_user_id)
        return True


    def clear_vice_leader(self, user_id):
        """解除副盟主职位
        """
        ids = utils.split_to_int(self.vice_user_id)
        if user_id not in ids:
            logger.warning("Unable to clear vice leader[current vice leader=%s][user_id=%d]" %
                    (self.vice_user_id, user_id))
            return False

        ids.remove(user_id)
        self.vice_user_id = utils.join_to_string(ids)
        logger.debug("Clear vice leader[user_id=%d][current vice leader=%s]" %
                (user_id, self.vice_user_id))
        return True


    def change_name(self, new_name):
        """更换名称
        """
        if not isinstance(new_name, str):
            logger.warning("Invalid type")
            return False

        if new_name == "":
            logger.warning("Empty name")
            return False

        #名字用 base64 编码存储，避免一些非法字符造成的问题
        self.name = base64.b64encode(new_name)
        return True


    @staticmethod
    def get_saved_name(name):
        """获取存储的名称
        base64 编码
        """
        return base64.b64encode(name)


    def get_readable_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.name)


    def change_icon(self, icon):
        self.icon = icon


    def change_announcement(self, announcement):
        """更新公告
        """
        if not isinstance(announcement, str):
            logger.warning("Invalid type")
            return False

        self.announcement = base64.b64encode(announcement)
        return True


    def get_readable_announcement(self):
        """获取可读的公告信息
        """
        return base64.b64decode(self.announcement)


    def change_level_limit(self, limit):
        if (limit < int(float(data_loader.UnionConfInfo_dict["default_level_min"].value)) or
                limit > int(float(data_loader.UnionConfInfo_dict["default_level_max"].value))):
            logger.warning("Level limit not invalid[limit=%d]" % limit)
            return False

        self.join_level_limit = limit
        return True


    def change_join_status(self, status):
        if (status == self.JOIN_STATUS_ENABLE or
                status == self.JOIN_STATUS_VERIFY or
                status == self.JOIN_STATUS_DISABLE):
            self.join_status = status
            return True

        return False


    def is_member_full(self):
        return self.current_number >= self.max_number


    def add_member(self):
        """添加成员
        """
        if self.is_member_full():
            logger.warning("Union is full[curremt number=%d][max_number=%d]" %
                    (self.current_number, self.max_number))
            return False

        self.current_number += 1
        return True


    def remove_member(self):
        """删除成员
        """
        assert self.current_number > 0
        self.current_number -= 1


    def update_prosperity(self, now):
        """刷新繁荣度
        """
        if not utils.is_same_day(now, self.update_time):
            #过了一天，刷新繁荣度
            recent = utils.split_to_int(self.recent_prosperity_record)
            num = int(float(data_loader.UnionConfInfo_dict["recent_prosperity_day_num"].value))
            while len(recent) > num - 1:
                recent.pop(0)
            recent.append(self.today_prosperity)
            self.recent_prosperity_record = utils.join_to_string(recent)
            self.recent_prosperity = sum(recent)
            self.today_prosperity = 0

            self.update_time = now


    def gain_prosperity(self, value, now):
        """获得繁荣度
        """
        assert value >= 0
        self.update_prosperity(now)

        self.today_prosperity += value
        self.history_prosperity += value

        self.update_time = now

    
    def get_donate_next_index(self):
        self.donate_index += 1
        return self.donate_index

    def get_bosses_id(self):
        """获取boss_id数组"""
        array = utils.split_to_int(self.bosses_id)
        if 0 in array:
            logger.warning("union boss id illegal[union_id=%d][bosses_id=%s]" % (self.id, array))
            raise Exception("union boss illegal")

        if len(array) != 10 and len(array) != 0:
            logger.warning("union boss num illegal[union_id=%d][bosses_id=%s]" % (self.id, array))
            raise Exception("union boss illegal") 

        return array

    def update_boss_group(self, group_id, bosses_id, now):
        """更新boss组"""
        self.boss_group = group_id
        self.boss_step = 0
        self.bosses_id = utils.join_to_string(bosses_id)

        self.boss_last_update_time = now
        self.boss_last_change_time = now

    def reset_boss(self, now):
        """重置联盟boss"""
        self.boss_step = 0
        self.boss_last_update_time = now

    def get_attacking_unionboss(self):
        """获取正在攻打的boss id"""
        bosses_id = self.get_bosses_id()
        if self.boss_step < len(bosses_id):
            return bosses_id[self.boss_step]
        return 0
