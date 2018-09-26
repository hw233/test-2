#coding:utf8
"""
Created on 2015-04-25
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief : 封装和 redis 的通信逻辑
"""

from twisted.internet.defer import Deferred
from firefly.utils.singleton import Singleton
from utils import logger
from utils.redis_agent import RedisAgent
from datalib.accessor import AccessorFactory
from datalib.result import DataResult


class DataRedisAgent(object):
    """访问数据 redis
    """
    __metaclass__ = Singleton


    def connect(self, ip, port, db = '0', password = None, timeout = 1):
        """初始化
        Args:
            timeout : 连接超时事件，单位 s
        """
        self.redis = RedisAgent()
        self.redis.connect(ip, port, db, password, timeout)


    def pipeline(self):
        return self.redis.pipeline()


class DataProxy(object):

    def __init__(self):
        """初始化访问代理
        """
        #Redis 访问器
        self._ac = AccessorFactory().accessors

        #存储 Redis 访问结果
        self._result = DataResult()

        #是否需要两次访问，先处理 prepipe，再处理 pipe
        self._twice = False
        #Redis 访问 pipeline（批处理接口）
        self._prepipe = DataRedisAgent().pipeline() #预访问 pipeline
        self._pipe = DataRedisAgent().pipeline()

        #回调
        self._precallback = []
        self._callback = []

        self._call = False
        self.status = -1


    def search(self, name, data_key_value):
        """通过主键查询数据
        table_name, data_key_value -> data
        结果可以通过 get_result / get_all_result 查询
        """
        key = self._ac[name].table.generate_key(data_key_value)
        self._pipe.get(key)
        self._set_callback(self._parse, name, data_key_value)


    def _parse(self, name, response, args):
        """解析查询结果，存储结果
        Args:
            name: 表名
            response: redis 的返回，data 序列化后的结果
            args: (data_key_value)
        """
        (data_key_value, ) = args
        data = self._ac[name].table.parse(response)
        self._result.add(name, data_key_value, data)


    def get_result(self, name, data_key_value):
        """获取查询结果
        """
        assert self._call and self.status == 0
        return self._result.get(name, data_key_value)


    def get_all_result(self, name):
        """获取查询结果，得到批处理过程中对一张表的所有查询结果
        """
        assert self._call and self.status == 0
        return self._result.get_all(name)


    def update(self, name, data, old_data):
        """更新数据
        table_name, data -> None
        """
        key = self._ac[name].table.generate_key_by_data(data)
        value = self._ac[name].table.generate_value(data)
        self._pipe.set(key, value) #TODO 目前 redis api 中无 'XX' 选项
        self._set_callback(self._check_true, name)

        #需要根据变化，来进行索引字段更新
        self._update_all_index(name, data, old_data)
        self._update_all_rank(name, data)
        #需要根据变化，来进行集合字段更新
        self._update_all_set(name, data, old_data)


    def add(self, name, data):
        """添加数据
        table_name, data -> None
        """
        key = self._ac[name].table.generate_key_by_data(data)
        value = self._ac[name].table.generate_value(data)
        self._pipe.setnx(key, value)
        self._set_callback(self._check_true, name)

        self._add_all_index(name, data)
        self._add_all_rank(name, data)
        self._add_all_set(name, data)


    def delete(self, name, data):
        """删除数据
        table_name, data -> None
        """
        key = self._ac[name].table.generate_key_by_data(data)
        self._pipe.delete(key)
        self._set_callback(self._check_one, name)

        self._delete_all_index(name, data)
        self._delete_all_rank(name, data)
        self._delete_all_set(name, data)


    def get_all_values(self, name, data_set_name):
        """获取表中某字段所有值
        """
        key = self._ac[name].set.generate_key(data_set_name)
        self._pipe.smembers(key)
        self._set_callback(self._parse_set, name, data_set_name, False)


    def get_all_values_result(self, name, data_set_name):
        """获取所有字段值
        """
        return self._result.get_set_result(name, data_set_name)


    def is_value_exist(self, name, data_set_name, data_set_value):
        """判断字段是否已经存在某值
        """
        key = self._ac[name].set.generate_key(data_set_name)
        self._pipe.sismember(key, data_set_value)
        self._set_callback(self._parse_value_exist, name, data_set_name, data_set_value)


    def _parse_value_exist(self, name, response, args):
        """判断字段是否已经存在某值
        """
        (data_set_name, data_set_value, ) = args
        self._result.add_value_exist(name, data_set_name, data_set_value, response)


    def get_value_exist(self, name, data_set_name, data_set_value):
        return self._result.get_value_exist(name, data_set_name, data_set_value)


    def get_all(self, name, data_set_name):
        """获取数据全集
        """
        self._twice = True

        key = self._ac[name].set.generate_key(data_set_name)
        self._prepipe.smembers(key)
        self._set_precallback(self._parse_set, name, data_set_name, True)


    def _parse_set(self, name, response, args):
        """解析查询 set 的返回，存储结果，并且（可能）发起第二次查询
        Args:
            name: 表名
            response: redis 的返回，对应的数据的主键值
            data_set_name: set 字段名
            search_data: 是否继续查询数据
        """
        (data_set_name, search_data, ) = args

        values = self._ac[name].set.parse(data_set_name, response)
        self._result.add_set_result(name, data_set_name, values)

        if search_data:
            for data_key_value in values:
                self.search(name, data_key_value)


    def _add_all_set(self, name, data):
        """将数据添加到集合中
        """
        for data_set_name in self._ac[name].set.all():
            key = self._ac[name].set.generate_key(data_set_name)
            value = self._ac[name].set.generate_member(data, data_set_name)
            self._pipe.sadd(key, value)
            self._set_callback(self._check_one, name)#重复的 member 会报错


    def _delete_all_set(self, name, data):
        """将数据从集合中移除
        """
        for data_set_name in self._ac[name].set.all():
            key = self._ac[name].set.generate_key(data_set_name)
            value = self._ac[name].set.generate_member(data, data_set_name)
            self._pipe.srem(key, value)
            # logger.debug("Delete set %r %r" % (key, value))
            self._set_callback(self._check_one, name)


    def _update_all_set(self, name, data, old_data):
        """更新数据集合
        Args:
            name: 表名
            data: 数据（新）
            old_data: 数据（旧）
        """
        for data_set_name in self._ac[name].set.all():
            #当集合字段值发生变更时，才进行更新
            value = getattr(data, data_set_name)
            old_value = getattr(old_data, data_set_name)
            if value != old_value:
                key = self._ac[name].set.generate_key(data_set_name)
                self._pipe.srem(key, old_value)
                self._set_callback(self._check_one, name)
                self._pipe.sadd(key, value)
                self._set_callback(self._check_one, name)


    def search_by_index(self, name, data_index_name, data_index_value):
        """通过 index 查找
        table_name, data_index_name, data_index_value -> list(data)
        需要两次访问
        """
        self._twice = True

        key = self._ac[name].index.generate_key(data_index_name, data_index_value)
        self._prepipe.smembers(key)
        self._set_precallback(self._parse_index, name, data_index_name, data_index_value)


    def _parse_index(self, name, response, args):
        """解析查询 index 的返回，存储结果，并且发起第二次查询（通过主键值查找）
        Args:
            name: 表名
            response: redis 的返回，对应的数据的主键值
            args: (data_index_name, data_index_value)
        """
        (data_index_name, data_index_value, ) = args
        self._result.add_index_result(name, data_index_name, data_index_value, response)

        for data_key_value in response:
            self.search(name, data_key_value)


    def _add_all_index(self, name, data):
        """将数据添加到所有关联的索引中
        """
        for data_index_name in self._ac[name].index.all():
            self._add_index(name, data_index_name, data)


    def _add_index(self, name, data_index_name, data):
        """将数据添加到对应的索引中
        table_name, data_index_name, data -> None
        """
        key = self._ac[name].index.generate_key_by_data(data_index_name, data)
        value = self._ac[name].index.generate_member(data)
        self._pipe.sadd(key, value)
        self._set_callback(self._check_one, name)


    def _delete_all_index(self, name, data):
        """将数据从所有关联的索引中移除
        """
        for data_index_name in self._ac[name].index.all():
            self._delete_index(name, data_index_name, data)


    def _delete_index(self, name, data_index_name, data):
        """将数据从索引中删除
        table_name, data_index_name, data -> None
        """
        key = self._ac[name].index.generate_key_by_data(data_index_name, data)
        value = self._ac[name].index.generate_member(data)
        self._pipe.srem(key, value)
        # logger.debug("Delete index %r %r" % (key, value))
        self._set_callback(self._check_one, name)

    def _update_all_index(self, name, data, old_data):
        """更新索引"""
        for data_index_name in self._ac[name].index.all():
            index_member = self._ac[name].index.generate_member(data)
            old_index_member = self._ac[name].index.generate_member(old_data)

            index_key = self._ac[name].index.generate_key_by_data(data_index_name, data)
            old_index_key = self._ac[name].index.generate_key_by_data(data_index_name, old_data)

            if index_member != old_index_member or index_key != old_index_key:
                self._pipe.srem(old_index_key, old_index_member)
                self._set_callback(self._check_one, name)
                self._pipe.sadd(index_key, index_member)
                self._set_callback(self._check_one, name)

    def search_by_rank(self, name, data_rank_name, ranking_start, ranking_stop):
        """通过排名在排名表中查找数据
        table_name, data_rank_name, ranking_start, ranking_stop -> list(data)
        需要两次访问
        """
        self._twice = True

        key = self._ac[name].rank.generate_key(data_rank_name)
        self._prepipe.zrevrange(key, ranking_start, ranking_stop)
        self._set_precallback(self._parse_rank, name,
                data_rank_name, ranking_start, ranking_stop)


    def _parse_rank(self, name, response, args):
        """解析查询 rank 的返回，存储结果，并且发起第二次查询（通过主键值查找）
        Args:
            name: 表名
            response: redis 的返回，对应的数据的主键值
            args: (data_rank_name, ranking_start, ranking_stop)
        """
        (data_rank_name, ranking_start, ranking_stop) = args
        self._result.add_rank_result(
                name, data_rank_name, ranking_start, ranking_stop, response)

        for data_key_value in response:
            self.search(name, data_key_value)


    def get_rank_result(self, name, data_rank_name, ranking_start, ranking_stop):
        """获取排名查询结果
        """
        assert self._call and self.status == 0
        return self._result.get_rank_result(
                name, data_rank_name, ranking_start, ranking_stop)


    def search_by_rank_score(self, name, data_rank_name, score_min, score_max, offset, count):
        """通过分数区间在排名表中查找数据
        table_name, data_rank_name, score_min, score_max, offset, count -> list(data)
        需要两次访问
        """
        self._twice = True

        key = self._ac[name].rank.generate_key(data_rank_name)
        self._prepipe.zrevrangebyscore(
                key, score_max, score_min, start = offset, num = count)
        self._set_precallback(self._parse_rank_score, name,
                data_rank_name, score_min, score_max, offset, count)


    def _parse_rank_score(self, name, response, args):
        """解析通过分数区间查询 rank 的返回，存储结果，并且发起第二次查询（通过主键值查找）
        Args:
            name: 表名
            response: redis 的返回，对应的数据的主键值
            args: (data_rank_name, score_min, score_max, offset, count)
        """
        (data_rank_name, score_min, score_max, offset, count) = args
        self._result.add_rank_score_result(
                name, data_rank_name, score_min, score_max, offset, count, response)

        for data_key_value in response:
            self.search(name, data_key_value)


    def get_rank_score_result(self, name, data_rank_name, score_min, score_max, offset, count):
        """获取通过分数区间查询数据的结果
        """
        assert self._call and self.status == 0
        return self._result.get_rank_score_result(
                name, data_rank_name, score_min, score_max, offset, count)


    def search_rank_score_count(self, name, data_rank_name, score_min, score_max):
        """查询 rank 分数区间范围内的数据个数
        table_name, data_rank_name, score_min, score_max -> count
        """
        key = self._ac[name].rank.generate_key(data_rank_name)
        self._pipe.zcount(key, score_min, score_max)
        self._set_callback(self._parse_rank_score_count, name,
                data_rank_name, score_min, score_max)


    def _parse_rank_score_count(self, name, response, args):
        """解析查询 rank 分数区间范围元素个数的结果，存储结果
        Args:
            name: 表名
            response: redis 的返回，元素个数 count
            args: (data_rank_name, score_min, score_max)
        """
        (data_rank_name, score_min, score_max) = args
        self._result.add_rank_score_count(
                name, data_rank_name, score_min, score_max, response)


    def get_rank_score_count(self, name, data_rank_name, score_min, score_max):
        """获取有序集某分数范围内成员个数
        """
        assert self._call and self.status == 0
        return self._result.get_rank_score_count(name, data_rank_name, score_min, score_max)


    def search_ranking(self, name, data_rank_name, data_key_value):
        """根据数据主键查询数据排名
        table_name, data_rank_name, data_key_value -> ranking
        """
        key = self._ac[name].rank.generate_key(data_rank_name)
        self._pipe.zrevrank(key, data_key_value)
        self._set_callback(self._parse_ranking, name,
                data_rank_name, data_key_value)


    def _parse_ranking(self, name, response, args):
        """解析排名查询的返回，存储结果
        Args:
            name: 表名
            response: redis 的返回，数据排名 ranking
            args: (data_rank_name, data_key_value)
        """
        (data_rank_name, data_key_value) = args
        self._result.add_ranking(name, data_rank_name, data_key_value, response)


    def get_ranking(self, name, data_rank_name, data_key_value):
        """获得数据排名结果
        """
        assert self._call and self.status == 0
        return self._result.get_ranking(name, data_rank_name, data_key_value)


    def _add_all_rank(self, name, data):
        """将数据添加到所有排序表中
        """
        for data_rank_name in self._ac[name].rank.all():
            self._add_rank(name, data_rank_name, data)


    def _add_rank(self, name, data_rank_name, data):
        """将数据添加到排序表中
        """
        key = self._ac[name].rank.generate_key(data_rank_name)
        score = self._ac[name].rank.generate_score(data_rank_name, data)
        member = self._ac[name].rank.generate_member(data)
        self._pipe.zadd(key, score, member)
        self._set_callback(self._check_one, name)


    def _update_all_rank(self, name, data):
        """将数据在所有排序表中更新
        """
        for data_rank_name in self._ac[name].rank.all():
            self._update_rank(name, data_rank_name, data)


    def _update_rank(self, name, data_rank_name, data):
        """在排序表中更新数据
        """
        key = self._ac[name].rank.generate_key(data_rank_name)
        score = self._ac[name].rank.generate_score(data_rank_name, data)
        member = self._ac[name].rank.generate_member(data)
        self._pipe.zadd(key, score, member)
        self._set_callback(self._check_zero, name)


    def _delete_all_rank(self, name, data):
        """将数据从排序表中删除
        """
        for data_rank_name in self._ac[name].rank.all():
            self._delete_rank(name, data_rank_name, data)


    def _delete_rank(self, name, data_rank_name, data):
        """从排序表中删除数据
        """
        key = self._ac[name].rank.generate_key(data_rank_name)
        member = self._ac[name].rank.generate_member(data)
        self._pipe.zrem(key, member)
        # logger.debug("delete rank %r %r" % (key, member))
        self._set_callback(self._check_one, name)


    def _check_true(self, name, response):
        """检查 Redis 返回：期待结果为 True
        """
        # logger.debug("check true[response={0}]".format(response))
        assert response is True


    def _check_one(self, name, response):
        """检查 Redis 返回：期待结果为 1
        """
        # logger.debug("check %r %r" % (name, response))
        assert response == 1


    def _check_zero(self, name, response):
        """检查 Redis 返回：期待结果为 0
        """
        assert response == 0


    def _set_precallback(self, method, name, *args):
        """设置回调，针对 prepipe 的处理
        Args:
            method: 回调方法
            name: 表名
            *args: 可变参数
        """
        self._precallback.append((method, name, args))


    def _set_callback(self, method, name, *args):
        """设置回调
        Args:
            method: 回调方法
            name: 表名
            *args: 可变参数
        """
        self._callback.append((method, name, args))


    def execute(self, asyn = True):
        """执行访问 reids
        """
        assert not self._call
        self._call = True

        if asyn:
            return self._execute_asyn()
        else:
            return self._execute_sync()


    def _execute_sync(self):
        """同步访问 Redis 实现
        """
        if self._twice:
            res = self._do_pre_execute()
            self._parse_pre_execute(res)

        res = self._do_execute()
        return self._parse_execute(res)


    def _execute_asyn(self):
        """异步访问 Redis 实现
        通过 twisted Deferred 实现
        """
        defer = Deferred()
        if self._twice:
            defer.addCallback(self._do_pre_execute)
            defer.addCallback(self._parse_pre_execute)

        defer.addCallback(self._do_execute)
        defer.addCallback(self._parse_execute)
        defer.callback(0)
        return defer


    def _do_pre_execute(self, status = 0):
        """需要两次访问时，执行第一次访问 Redis
        """
        return self._prepipe.execute()


    def _parse_pre_execute(self, res):
        """解析 pre 访问的结果
        Args:
            res: redis 返回的结果
        """
        assert len(res) == len(self._precallback)

        for i, response in enumerate(res):
            (callback, name, args) = self._precallback[i]
            if len(args) > 0:
                callback(name, response, args)
            else:
                callback(name, response)

        return 0


    def _do_execute(self, status = 0):
        """访问 Redis
        """
        return self._pipe.execute()


    def _parse_execute(self, res):
        """解析访问 Redis 的结果
        调用对应的回调函数，处理结果
        Args:
            res: redis 返回的结果
        """
        assert len(res) == len(self._callback)

        for i, response in enumerate(res):
            (callback, name, args) = self._callback[i]
            if len(args) > 0:
                callback(name, response, args)
            else:
                callback(name, response)

        self.status = 0
        return self

