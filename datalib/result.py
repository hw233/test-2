#coding:utf8
"""
Created on 2015-12-05
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 存储访问 Redis 获得的结果
"""

from utils import logger


class DataResult(object):

    def __init__(self):
        """初始化
        """
        self._data = {}
        self._index = {}
        self._rank = {}
        self._set = {}


    def add(self, name, key, data):
        logger.debug("add result[name={0}][key={1}]".format(name, key))

        if data is None:
            logger.debug("add result none[name={0}][key={1}]".format(name, key))
            return
        if name not in self._data:
            self._data[name] = {}

        self._data[name][str(key)] = data


    def get(self, name, key):
        """根据主键值，获得结果
        如果结果不存在，返回 None
        """
        if name not in self._data:
            return None
        if str(key) not in self._data[name]:
            return None

        return self._data[name][str(key)]


    def get_all(self, name):
        if name not in self._data:
            return []
        return self._data[name].values()


    def add_set_result(self, name, set_name, keys):
        logger.debug("add set result[name={0}]".format(name))
        if name not in self._set:
            self._set[name] = {}
        self._set[name][set_name] = keys


    def get_set_result(self, name, set_name):
        return self._set[name][set_name]


    def add_value_exist(self, name, set_name, set_value, exist):
        logger.debug("add value exist[name={0}][{1}:{2}][exist={3}]".format(
            name, set_name, set_value, exist))
        set_key = "{0}:{1}".format(set_name, set_value)
        if name not in self._set:
            self._set[name] = {}
        self._set[name][set_key] = exist


    def get_value_exist(self, name, set_name, set_value):
        set_key = "{0}:{1}".format(set_name, set_value)
        return self._set[name][set_key]


    def add_index_result(self, name, index_name, index_value, keys):
        logger.debug("add index result"
                "[name={0}][index name={1}][index value={2}]".format(
            name, index_name, index_value))
        if name not in self._index:
            self._index[name] = {}

        index_key = "{0}:{1}".format(index_name, index_value)
        # assert index_key not in self._index[name]
        self._index[name][index_key] = keys


    def add_rank_result(self, name, rank_name, start, stop, keys):
        logger.debug("add rank result"
                "[name={0}][rank name={1}][start={2}][stop={3}]".format(
            name, rank_name, start, stop))
        if name not in self._rank:
            self._rank[name] = {}

        rank_key = "{0}|D:{1}-{2}".format(rank_name, start, stop)
        # assert rank_key not in self._rank[name]
        self._rank[name][rank_key] = keys


    def get_rank_result(self, name, rank_name, start, stop):
        rank_key = "{0}|D:{1}-{2}".format(rank_name, start, stop)
        keys = self._rank[name][rank_key]

        result = []
        for key in keys:
            result.append(self._data[name][key])
        return result


    def add_rank_score_result(self, name,
            rank_name, score_min, score_max, offset, count, keys):
        logger.debug("add rank score result"
                "[name={0}][rank name={1}][{2}-{3}][{4},{5}]".format(
            name, rank_name, score_min, score_max, offset, count))
        if name not in self._rank:
            self._rank[name] = {}

        rank_key = "{0}|S:{1}-{2}[{3}-{4}]".format(
                rank_name, score_min, score_max, offset, count)
        # assert rank_key not in self._rank[name]
        self._rank[name][rank_key] = keys


    def get_rank_score_result(self, name,
            rank_name, score_min, score_max, offset, count):
        rank_key = "{0}|S:{1}-{2}[{3}-{4}]".format(
                rank_name, score_min, score_max, offset, count)
        keys = self._rank[name][rank_key]

        result = []
        for key in keys:
            result.append(self._data[name][key])
        return result


    def add_rank_score_count(self, name, rank_name, score_min, score_max, count):
        logger.debug("add rank score count"
                "[name={0}][rank name={1}][{2}-{3}]".format(
            name, rank_name, score_min, score_max))
        if name not in self._rank:
            self._rank[name] = {}

        rank_key = "{0}|C:{1}-{2}".format(rank_name, score_min, score_max)
        # assert rank_key not in self._rank[name]
        self._rank[name][rank_key] = count


    def get_rank_score_count(self, name, rank_name, score_min, score_max):
        rank_key = "{0}|C:{1}-{2}".format(rank_name, score_min, score_max)
        return self._rank[name][rank_key]


    def add_ranking(self, name, rank_name, key, ranking):
        logger.debug("add ranking"
                "[name={0}][rank name={1}][key={2}]".format(name, rank_name, key))
        if name not in self._rank:
            self._rank[name] = {}

        rank_key = "{0}|R:{1}".format(rank_name, key)
        # assert rank_key not in self._rank[name]
        self._rank[name][rank_key] = ranking


    def get_ranking(self, name, rank_name, key):
        rank_key = "{0}|R:{1}".format(rank_name, key)
        return self._rank[name][rank_key]


