#coding:utf8
"""
Created on 2015-10-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 全局数据
"""

import copy
import time
import random
from twisted.internet.defer import Deferred
from firefly.utils.singleton import Singleton
from utils import logger


class RedundantData(object):
    """
    冗余数据
    一份 data，提供给外界访问修改使用
    一份 backup，保证正确性，保证和 DB 同步

    外接获得 data，进行修改后，
    确认修改时，必须调用 commit() 方法，此时会将修改同步到 backup，同时同步到 DB
    如果不调用 commit() 方法，相当于放弃修改，此时 data 会被重置（和 backup 保持一致）
    """

    __slots__ = ["_data", "_backup", "active_time", "_datatype"]


    def __init__(self, datatype):
        self._datatype = datatype
        self._data = None
        self._backup = None
        self._set_active()


    def is_valid(self):
        if self._data is None:
            return False

        return self._data.is_valid()


    def _set_active(self):
        """置活跃
        """
        self.active_time = int(time.time())


    def load(self, user_id):
        """
        从 DB 中载入 User（user_id） 的数据
        """
        data = self._datatype()
        defer = data.load_from_cache(user_id)
        defer.addCallback(self._post_load)
        return defer


    def _post_load(self, data):
        """
        初始化 data、backup 两份数据
        """
        self._data = data
        self._backup = copy.deepcopy(self._data)

        return self.get()


    def get(self, d = None):
        """
        获取数据
        需要保证 data 数据是正确的（和 backup 一致）
        """
        self._set_active()

        if self.is_valid():
            self._rollback()
        return self._data


    def _rollback(self):
        """
        回滚 data 数据
        将 data 数据重置（和 backup 一致）
        """
        self._data.rollback(self._backup)
        self._data.check_validation()
        assert self._data.is_valid()


    def commit(self):
        """
        确认 data 更新
        将 data 的更新同步到 backup 和 DB
        """
        defer = self._backup.commit(self._data)
        self._data.check_validation()
        self._backup.check_validation()
        # assert self._data.is_valid()
        # assert self._backup.is_valid()

        defer.addCallback(self.get)
        return defer


class DataBase(object):
    """
    本地内存中的数据
    包含本地处理的在线用户的数据

    cache 一般的功能
    """
    __metaclass__ = Singleton

    #缓存策略：超过数量警戒线后，淘汰失效的项目
    _BUFFER_MAX_NUM = 200      #缓存数量上限
    _BUFFER_WARNING_NUM = 150   #缓存数量警戒线，超过警戒线，开始执行淘汰策略
    _BUFFER_EXPIRE_TIME = 700   #缓存失效时间，单位秒
    _BUFFER_ELIMINATE_NUM = 10  #缓存淘汰一次最多淘汰的数量，避免淘汰占用太多时间


    def __init__(self):
        self.db = {}
        self.datatype = None
        self.basic_db = {}
        self.basic_datatype = None


    def register_datatype(self, datatype):
        self.datatype = datatype


    def _eliminate(self):
        """执行淘汰策略
        """
        if len(self.db) > self._BUFFER_MAX_NUM:
            self._force_eliminate()
        elif len(self.db) > self._BUFFER_WARNING_NUM:
            self._replacement()


    def _force_eliminate(self):
        """强制淘汰
        当缓存储量超过上限时执行
        """
        #随机选择3个 item，淘汰其中最久不活跃的
        CANDIDATES_NUM = 3
        candidates = random.sample(self.db.keys(), CANDIDATES_NUM)

        now = int(time.time())
        max_inactive_duration = 0
        for id in candidates:
            duration = now - self.db[id].active_time
            if duration >= max_inactive_duration:
                choice = id

        del self.db[choice]
        logger.warning("Database force eliminate[key=%d][inactive duration=%d]" %
                (choice, duration))


    def _replacement(self):
        """进行换入换出
        在缓存储量超过警戒线，未达上限时执行
        """
        now = int(time.time())
        to_eliminate = []
        for id in self.db:
            if now - self.db[id].active_time >= self._BUFFER_EXPIRE_TIME:
                #淘汰不活跃的数据
                to_eliminate.append(id)

            #一次淘汰，最多淘汰一个固定个数，避免耗时过多
            if len(to_eliminate) >= self._BUFFER_ELIMINATE_NUM:
                break

        for id in to_eliminate:
            del self.db[id]

        count = len(to_eliminate)
        if count == 0:
            logger.warning("Database replacement failed, no inactive item[active num=%d]" %
                    len(self.db))
        else:
            logger.trace("Database replacement succeed[active num=%d][eliminate num=%d]" %
                    (len(self.db), count))


    def get_data(self, id):
        """
        根据 id 获取数据
        1 如果在内存中，直接返回
        2 如果不在，去 DB 中读取
        Returns:
            Deferred: 返回参数即是 Data
        """
        self._eliminate()

        #如果用户数据在内存中，且合法
        if id in self.db and self.db[id].is_valid():
            logger.debug("get data from memory[id=%d]" % int(id))
            return self._return_data(id)
        else:
            logger.debug("get data from db[id=%d]" % int(id))
            return self._load_data(id)


    def _load_data(self, id):
        """
        从 DB 中加载数据
        """
        data = RedundantData(self.datatype)
        self.db[id] = data
        return data.load(id)


    def _return_data(self, id):
        """
        从内存中读入数据
        """
        defer = Deferred()
        defer.callback(self.db[id].get())
        return defer


    def commit(self, data):
        """
        确认修改
        """
        return self.db[data.id].commit()


    def clear(self):
        """清空所有数据
        清空缓存
        """
        self.db.clear()


    def clear_data(self, data):
        """清除指定数据
        """
        if data.id in self.db:
            del self.db[data.id]


    def clear_data_by_id(self, id):
        """清除指定数据
        """
        if id in self.db:
            logger.notice("clear data from memory[id=%d]" % int(id))
            del self.db[id]


    def register_basic_datatype(self, datatype):
        self.basic_datatype = datatype


    def get_basic_data(self, id):
        """
        获取basic数据
        1 去 DB 中读取(每次都去db读，不缓存)
        Returns:
            Deferred: 返回参数即是 Data
        """
        logger.debug("get basic data from db")
        return self._load_basic_data(id)


    def _load_basic_data(self, id):
        """
        从 DB 中加载数据
        """
        data = RedundantData(self.basic_datatype)
        self.basic_db[id] = data
        return data.load(id)


    def commit_basic(self, basic_data):
        """
        确认basic数据
        """
        return self.basic_db[basic_data.id].commit()


