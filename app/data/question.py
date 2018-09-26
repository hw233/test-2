#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 问答随机事件
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class QuestionPool(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._ids = []
        self._weight = []
        for id in data_loader.EventQuestionBasicInfo_dict:
            weight = data_loader.EventQuestionBasicInfo_dict[id].weight
            if len(self._weight) > 0:
                weight += self._weight[-1]
            self._ids.append(id)
            self._weight.append(weight)


    def choose(self):
        """随机选择
        """
        assert len(self._ids) >= 1

        random.seed()
        c = random.uniform(0, self._weight[-1])
        for index, weight in enumerate(self._weight):
            if c < weight:
                return self._ids[index]


class QuestionInfo(object):
    """问答流程
    """
    def __init__(self, user_id = 0, question_id = 0, node_id = 0, time = 0):
        self.user_id = user_id
        self.question_id = question_id
        self.node_id = node_id
        self.time = time


    @staticmethod
    def create(user_id):
        """生成一个新的问题信息
        """
        question = QuestionInfo(user_id)
        return question


    def start(self, node, now):
        """开始问答
        """
        self.question_id = QuestionPool().choose()
        logger.debug("choose question[id=%d]" % self.question_id)
        self.node_id = node.id
        self.time = now


    def answer(self, question_id, answer):
        """回答问题
        Args:
            question_id[int]: 问题 id
            answer[list(int)]: 回答
        Returns:
            Ture/False: 回答是否正确
        """
        assert self.question_id == question_id

        question_index = data_loader.EventQuestionBasicInfo_dict[question_id].questionIndex

        #答题数目少，回答错误
        if len(question_index) != len(answer):
            return False

        for i in range(0, len(answer)):
            index = question_index[i]
            correct = data_loader.ChoiceQuestionBasicInfo_dict[index].answer
            if correct != answer[i]:
                return False

        return True


    def finish(self):
        self.question = 0
        self.node_id = 0
        self.time = 0

