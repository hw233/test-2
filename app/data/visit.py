#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 探访随机事件
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class VisitPool(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._ids = []
        self._weight = []
        for id in data_loader.EventVisitBasicInfo_dict:
            weight = data_loader.EventVisitBasicInfo_dict[id].weight
            self._ids.append(id)
            self._weight.append(weight)


    def choose(self, count):
        """随机选择
        Args:
            count[int]: 选择的条目个数，不允许重复
        """
        assert len(self._ids) >= count

        result = []
        random.seed()

        total_weight = 0
        for weight in self._weight:
            total_weight += weight

        while len(result) < count:
            c = random.uniform(0, total_weight)
            cur_weight = 0
            for index, weight in enumerate(self._weight):
                cur_weight += weight
                if c < cur_weight:
                    id = self._ids.pop(index)
                    result.append(id)
                    self._ids.append(id)
                    self._weight.pop(index)
                    self._weight.append(weight)
                    total_weight -= weight
                    break

        return result


class VisitInfo(object):
    """探访流程
    """
    def __init__(self, node_id = 0, user_id = 0, candidate = '', time = 0):
        self.node_id = node_id
        self.user_id = user_id
        self.candidate = candidate
        self.time = time


    @staticmethod
    def create(user_id, node_id):
        """生成一个新的探访信息
        """
        visit = VisitInfo(node_id, user_id)
        return visit


    def start(self, now):
        """开始探访
        获得三个选项
        """
        COUNT = 3
        ids = VisitPool().choose(COUNT)
        self.candidate = utils.join_to_string(ids)
        self.time = now


    def is_started(self):
        return self.time != 0


    def get_candidate(self):
        """获得候选项
        """
        ids = utils.split_to_int(self.candidate)
        return ids


    def is_candidate_valid(self, visit_id):
        """判断候选项是否合法
        """
        if not self.is_started():
            logger.warning("Visit not started")
            return False

        if not visit_id in self.get_candidate():
            logger.warning("Visit id not vaild[visit id=%d][candidate=%s]" %
                    (visit_id, self.candidate))
            return False
        return True


    def finish(self):
        self.time = 0
        self.candidate = ''

