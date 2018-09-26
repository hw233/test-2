#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief
"""

import base64
from utils import logger
from utils import utils


class CommonMailInfo(object):
    """邮件
    """

    __slots__ = [
            "id",
            "common_id",
            "mail_basic_id",
            "subject",
            "sender",
            "content",
            "reward_money",
            "reward_food",
            "reward_gold",
            "reward_items_basic_id",
            "reward_items_num",
            ]

    def __init__(self):
        self.id = 0
        self.common_id = 0
        self.mail_basic_id = 0

        self.subject = ''
        self.sender = ''
        self.content = ''
        self.reward_money = 0
        self.reward_food = 0
        self.reward_gold = 0
        self.reward_items_basic_id = ''
        self.reward_items_num = ''

    @staticmethod
    def create(id, common_id, mail_basic_id):
        """新建一条广播信息
        """
        mail = CommonMailInfo()
        mail.id = id
        mail.common_id = common_id
        mail.mail_basic_id = mail_basic_id

        mail.subject = ''
        mail.sender = ''
        mail.content = ''
        mail.reward_money = 0
        mail.reward_food = 0
        mail.reward_gold = 0
        mail.reward_items_basic_id = ''
        mail.reward_items_num = ''
        return mail


    def write(self, subject, sender, content):
        mail.subject = subject
        mail.sender = sender
        mail.content = content


    def attach_reward(self, money = 0, food = 0, gold = 0, items = []):
        self.reward_money = money
        self.reward_food = food
        self.reward_gold = gold

        items_basic_id = []
        items_num = []
        for (basic_id, num) in items:
            items_basic_id.append(basci_id)
            items_num.append(num)
        self.reward_items_basic_id = utils.join_to_string(items_basic_id)
        self.reward_items_num = utils.join_to_string(items_num)

