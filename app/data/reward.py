#coding:utf8
"""
Created on 2015-12-23
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 奖励品
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from app.data.node import NodeInfo
from datalib.data_loader import data_loader


class DungeonReward(object):

    def __init__(self, dungeon_id, level):
        self.dungeon_id = dungeon_id
        self.level = level
        self.unit = []
        self.contain = []


    def add(self, item_basic_id, item_num, weight, contain):
        if contain:
            self.contain.append((item_basic_id, item_num))
        else:
            if len(self.unit) > 0:
                weight += self.unit[-1][2]
            self.unit.append((item_basic_id, item_num, weight))


    def get(self, count):
        result = []

        random.seed()
        while len(result) < count:
            r = random.uniform(0.0, self.unit[-1][2])
            for (item_basic_id, item_num, weight) in self.unit:
                if r < weight:
                    result.append((item_basic_id, item_num))
                    break

        result.extend(self.contain)
        return result


class DungeonRewardPool(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._pool = {}

        data = data_loader.PVEDungeonRewardBasicInfo_dict
        for key in data:
            (dungeon_id, level, item_basic_id) = map(int, key.split('_'))
            if dungeon_id not in self._pool:
                self._pool[dungeon_id] = {}
            if level not in self._pool[dungeon_id]:
                self._pool[dungeon_id][level] = DungeonReward(dungeon_id, level)
                # logger.debug("init dungeon reward[id=%d][level=%d]" %
                #         (dungeon_id, level))

            self._pool[dungeon_id][level].add(
                    data[key].itemBasicId, data[key].itemNum,
                    data[key].weight, data[key].contain)


    def random(self, dungeon_id, level, count):
        return self._pool[dungeon_id][level].get(count)




class OfflineExploitReward(object):

    def __init__(self, type, level):
        self.type = type
        self.level = level
        self.unit = []


    def add(self, item_basic_id, item_num, weight):
            if len(self.unit) > 0:
                weight += self.unit[-1][2]
            self.unit.append((item_basic_id, item_num, weight))


    def get(self, count):
        result = []

        random.seed()
        while len(result) < count:
            r = random.uniform(0.0, self.unit[-1][2])
            for (item_basic_id, item_num, weight) in self.unit:
                if r < weight:
                    result.append((item_basic_id, item_num))
                    break

        return result


class OfflineExploitRewardPool(object):

    __metaclass__ = Singleton

    def __init__(self):
        self._pool = {}

        data = {}
        data[NodeInfo.EVENT_TYPE_SEARCH] = data_loader.EventSearchReward_dict
        data[NodeInfo.EVENT_TYPE_DEEP_MINING] = data_loader.EventDeepMiningReward_dict
        data[NodeInfo.EVENT_TYPE_HERMIT] = data_loader.EventHermitReward_dict

        for type in data.keys():
            if type not in self._pool:
                self._pool[type] = {}

            for key in data[type]:
                (id, level) = map(int, key.split('_'))
                if level not in self._pool[type]:
                    self._pool[type][level] = OfflineExploitReward(type, level)
                    logger.debug("init offline exploit reward[type=%d][level=%d]" 
                            % (type, level))

                self._pool[type][level].add(
                        data[type][key].itemBasicId,
                        data[type][key].itemNum,
                        data[type][key].weight)


    def random(self, event_type, level, count):
        return self._pool[event_type][level].get(count)

