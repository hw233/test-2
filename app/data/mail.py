#coding:utf8
"""
Created on 2015-06-17
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 邮件相关
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


MAIL_STATUS_UNREAD = 1  #未读
MAIL_STATUS_READ = 2    #已读
MAIL_STATUS_USED = 3    #已使用

MAIL_TYPE_SYSTEM = 1        #系统邮件
MAIL_TYPE_BATTLE = 2        #战斗邮件
MAIL_TYPE_EXPLOITATION = 3  #采集邮件

MAIL_COUNT_ZERO = "0#0#0"


class PostofficeInfo(object):
    def __init__(self, user_id = 0, next_index = 1, count = MAIL_COUNT_ZERO):
        self.user_id = user_id
        self.next_index = next_index
        self.count = count


    @staticmethod
    def create(user_id):
        return PostofficeInfo(user_id)


    def get_mail_count(self, type):
        counts = utils.split_to_int(self.count)
        return counts[type-1]


    def delete_mail(self, type):
        counts = utils.split_to_int(self.count)
        counts[type-1] -= 1
        self.count = utils.join_to_string(counts)


    def create_mail(self, basic_id, now):
        """创建邮件
        """
        mail = MailInfo.create(self.user_id, self.next_index, basic_id, now)

        counts = utils.split_to_int(self.count)
        counts[mail.type-1] += 1
        self.count = utils.join_to_string(counts)
        self.next_index += 1
        return mail


    def create_mail_with_content(self, subject, sender, content):
        mail = MailInfo.create(self.user_id, self.next_index, basic_id, now)

        counts = utils.split_to_int(self.count)
        counts[mail.type - 1] += 1
        self.count = utils.join_to_string(counts)



class MailInfo(object):
    def __init__(self, id = 0, user_id = 0, basic_id = 0, type = 0,
            status = MAIL_STATUS_UNREAD, time = 0,
            delete_after_used = False, delete_time = 0,
            subject = '', sender = '', content = '',
            reward_money = 0, reward_food = 0, reward_gold = 0,
            reward_items_basic_id = '', reward_items_num = '',
            lost_money = 0, lost_food = 0, lost_gold = 0, lost_soldier = 0,
            lost_items_basic_id = '', lost_items_num = '',
            related_node_id = 0, related_exploitation_type = 0,
            related_exploitation_level = 0, related_exploitation_progress = 0.0,
            related_enemy_user_id = 0, related_enemy_name = '', related_enemy_type = 0,
            related_battle_win = True, arena_title_level = 0, arena_coin = 0,
            legendcity_position = 0, legendcity_id = 0):
        self.id = id
        self.user_id = user_id
        self.basic_id = basic_id
        self.type = type
        self.status = status
        self.time = time

        self.delete_after_used = delete_after_used
        self.delete_time = delete_time

        self.subject = subject
        self.sender = sender
        self.content = content

        self.reward_money = reward_money
        self.reward_food = reward_food
        self.reward_gold = reward_gold
        self.reward_items_basic_id = reward_items_basic_id
        self.reward_items_num = reward_items_num

        self.lost_money = lost_money
        self.lost_food = lost_food
        self.lost_gold = lost_gold
        self.lost_soldier = lost_soldier
        self.lost_items_basic_id = lost_items_basic_id
        self.lost_items_num = lost_items_num

        self.related_node_id = related_node_id
        self.related_exploitation_type = related_exploitation_type
        self.related_exploitation_level = related_exploitation_level
        self.related_exploitation_progress = related_exploitation_progress

        self.related_enemy_user_id = related_enemy_user_id
        self.related_enemy_name = related_enemy_name
        self.related_enemy_type = related_enemy_type

        self.related_battle_win = related_battle_win

        self.arena_title_level = arena_title_level
        self.arena_coin = arena_coin

        self.legendcity_position = legendcity_position
        self.legendcity_id = legendcity_id

    @staticmethod
    def generate_id(user_id, index):
        """
        user_id[int]: 用户 id
        index[int]: 邮件序号
        """
        return user_id << 32 | index


    @staticmethod
    def get_index(id):
        index = id & 0xFFFFFFFF
        return index


    @staticmethod
    def get_type_by_basic_id(basic_id):
        info = data_loader.MailKeyInfo_dict[basic_id]
        return info.type


    def is_system_mail(self):
        return self.type == MAIL_TYPE_SYSTEM


    def is_battle_mail(self):
        return self.type == MAIL_TYPE_BATTLE


    def is_exploitation_mail(self):
        return self.type == MAIL_TYPE_EXPLOITATION


    @staticmethod
    def create(user_id, index, basic_id, now):
        """
        新建一封邮件
        Args:
            basic_mail_id : 用户的下一个可用mail_id
            basic_id : 邮件类型
            user_id ：给谁发的邮件
        _forward_legendcity_mail()"""
        mail_id = MailInfo.generate_id(user_id, index)
        mail = MailInfo(mail_id, user_id, basic_id)
        mail.time = now

        info = data_loader.MailKeyInfo_dict[basic_id]
        mail.type = info.type

        if info.lastTime == 0:
            mail.delete_after_used = True
            mail.delete_time = 0
        else:
            mail.delete_after_used = False
            seconds_per_hour = 3600
            mail.delete_time =  now + info.lastTime * seconds_per_hour

        mail.reward_money = info.rewardMoney
        mail.reward_food = info.rewardFood
        mail.reward_gold = info.rewardGold

        items_basic_id = info.rewardItemBasicId
        items_num = info.rewardItemNum
        assert len(items_basic_id) == len(items_num)
        mail.reward_items_basic_id = utils.join_to_string(items_basic_id)
        mail.reward_items_num = utils.join_to_string(items_num)

        return mail


    def read(self):
        if self.status != MAIL_STATUS_UNREAD:
            logger.warning("Can not read mail[id=%d][status=%d]" %
                    (self.id, self.status))
            #return False

        self.status = MAIL_STATUS_READ
        return True


    def is_used(self):
        return self.status == MAIL_STATUS_USED


    def use(self):
        if self.status != MAIL_STATUS_READ:
            logger.warning("Can not use mail[id=%d][status=%d]" %
                    (self.id, self.status))
            return False

        self.status = MAIL_STATUS_USED
        return True


    def write(self, subject, sender, content):
        self.subject = subject
        self.sender = sender
        self.content = content


    def change_sender(self, sender):
        self.sender = sender


    def change_enemy_name(self, enemy_name):
        self.related_enemy_name = enemy_name


    def attach_reward(self, money, food, gold, items):
        self.reward_money = money
        self.reward_food = food
        self.reward_gold = gold

        #merge same items
        reward_items = {}
        for (basic_id, num) in items:
            if basic_id not in reward_items:
                reward_items[basic_id] = num
            else:
                reward_items[basic_id] += num

        self.reward_items_basic_id = utils.join_to_string(reward_items.keys())
        self.reward_items_num = utils.join_to_string(reward_items.values())


    def attach_lost(self, money = 0, food = 0, gold = 0, soldier = 0, items = []):
        self.lost_money = money
        self.lost_food = food
        self.lost_gold = gold
        self.lost_soldier = soldier

        #merge same items
        reward_items = {}
        for (basic_id, num) in items:
            if basic_id not in reward_items:
                reward_items[basic_id] = num
            else:
                reward_items[basic_id] += num

        self.lost_items_basic_id = utils.join_to_string(reward_items.keys())
        self.lost_items_num = utils.join_to_string(reward_items.values())


    def attach_node_info(self, node):
        self.related_node_id = node.id
        self.related_exploitation_type = node.exploit_type


    def attach_node_detail(self, node_id, exploit_type):
        self.related_node_id = node_id
        self.related_exploitation_type = exploit_type


    def attach_node_offline_exploitation(self, exploitation_level, exploitation_progress):
        self.related_exploitation_level = exploitation_level
        self.related_exploitation_progress = exploitation_progress


    def attach_enemy_info(self, enemy):
        self.related_enemy_name = enemy.name
        self.related_enemy_user_id = enemy.rival_id
        self.related_enemy_type = enemy.type


    def attach_enemy_detail(self, enemy_name, enemy_user_id, enemy_type):
        self.related_enemy_name = base64.b64encode(enemy_name)
        self.related_enemy_user_id = enemy_user_id
        self.related_enemy_type = enemy_type


    def attach_legendcity_detail(self, city_id, position):
        self.legendcity_id = city_id
        self.legendcity_position = position


    def get_readable_enemy_name(self):
        """获取可读的名字
        因为名字在内部是 base64 编码存储的
        """
        return base64.b64decode(self.related_enemy_name)


    def attach_battle_info(self, win):
        self.related_battle_win = win


    def attach_arena_info(self, arena_title_level, arena_coin):
        self.arena_title_level = arena_title_level
        self.arena_coin = arena_coin


    def is_need_delete(self, now):
        """判断邮件是否可以删除
        有两种邮件：
        1 阅读之后进行删除
        2 创建之后一段时间进行删除
        """
        if self.delete_after_used:
            #阅读之后需要删除的邮件
            return self.status == MAIL_STATUS_USED
        else:
            return now >= self.delete_time


    def get_reward_items(self):
        """
        """
        items = []

        logger.debug("get reward:%s" % self.reward_items_basic_id)
        items_basic_id = utils.split_to_int(self.reward_items_basic_id)
        items_num = utils.split_to_int(self.reward_items_num)
        assert len(items_basic_id) == len(items_num)

        for index in range(0, len(items_basic_id)):
            items.append((items_basic_id[index], items_num[index]))

        return items


    def is_content_empty(self):
        return self.subject == "" or self.sender == "" or self.content == ""


