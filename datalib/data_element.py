#coding:utf8
"""
Created on 2015-01-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 本地缓存数据封装
"""

import copy
from firefly.server.globalobject import GlobalObject
from utils import logger


STATE_INVALID = 0
STATE_ADD = 1
STATE_DEL = 2
STATE_MOD = 3
STATE_OK = 4


class UniqueData(object):
    """
    单个数据
    """

    def __init__(self, name, data = None):
        self._name = name
        self._key = GlobalObject().table_desc.tables[self._name].key
        self._data = data
        if self._data == None:
            self._state = STATE_INVALID
        else:
            self._state = STATE_OK


    def get(self, readonly = False):
        assert self._state == STATE_OK or self._state == STATE_MOD or self._state == STATE_ADD

        if not readonly:
            if self._state != STATE_ADD:
                self._state = STATE_MOD

        return self._data


    def add(self, data):
        assert self._state == STATE_INVALID
        self._data = data
        self._state = STATE_ADD


    def delete(self):
        assert self._state == STATE_OK or self._state == STATE_MOD
        self._state = STATE_DEL


    def ok(self):
        assert self._state != STATE_INVALID

        if self._state == STATE_DEL:
            self._data = None
            self._state = STATE_INVALID
        else:
            self._state = STATE_OK


    def is_exist(self):
        return self._state == STATE_OK or self._state == STATE_MOD or self._state == STATE_ADD


    def is_dirty(self):
        return self._state != STATE_OK


    def is_valid(self):
        return self._state != STATE_INVALID


    def _deepcopy(self, right):
        """深拷贝
        """
        self._data = copy.deepcopy(right._data)
        self._state = right._state


    def rollback(self, right):
        """回滚数据
        将自身的数据恢复到和 right 一致
        Args:
            right[UserData]: 正确的数据
        """
        assert self._name == right._name
        if self.is_dirty():
            assert not right.is_dirty()
            self._deepcopy(right)


    def commit(self, right, proxy):
        """确认修改
        将自身数据修改到和 right 一致，并同步到 DB 中
        """
        assert self._name == right._name
        if right.is_dirty():
            assert not self.is_dirty() or not self.is_valid()

            #同步到 DB
            self._sync(proxy, right._state, right._data, self._data)

            #用 right 的数据覆盖自己的数据
            self._deepcopy(right)
            right.ok()
            self.ok()


    def _sync(self, proxy, state, new_data, old_data):
        """
        同步到 DB
        Args:
            proxy[DataProxy]: 和 DB 通信的代理
        """
        if state == STATE_MOD:
            proxy.update(self._name, new_data, old_data)
        elif state == STATE_ADD:
            proxy.add(self._name, new_data)
        elif state == STATE_DEL:
            proxy.delete(self._name, new_data)
        else:
            raise Exception("Invalid state[name=%s][state=%d]" %
                    (self._name, state))


class DataSet(object):
    """
    多个数据的集合
    """
    def __init__(self, name, data_list = []):
        self._name = name
        self._set = {}
        self._key = GlobalObject().table_desc.tables[name].key

        for data in data_list:
            key = getattr(data, self._key)
            self._set[key] = UniqueData(self._name, data)


    def __iter__(self):
        return iter(self._set.values())


    def __len__(self):
        return len(self._set)


    def is_valid(self):
        for key in self._set:
            if not self._set[key].is_valid():
                return False

        return True


    def get(self, key, readonly = False):
        if key not in self._set:
            return None

        return self._set[key].get(readonly)


    def get_all(self, readonly = False):
        all_data = []
        for key in self._set:
            if self._set[key].is_exist():
                all_data.append(self._set[key].get(readonly))

        return all_data


    def add(self, data):
        key = getattr(data, self._key)
        assert key not in self._set

        element = UniqueData(self._name)
        element.add(data)
        self._set[key] = element


    def delete(self, key):
        assert key in self._set

        element = self._set[key]
        element.delete()


    def rollback(self, right):
        delete_key = []
        for key in self._set:
            if key in right._set:
                right_element = right._set[key]
                element = self._set[key]
                element.rollback(right_element)
            else:
                delete_key.append(key)

        for key in delete_key:
            del self._set[key]


    def commit(self, right, proxy):
        delete_key = []

        for key in right._set:
            right_element = right._set[key]

            if not right_element.is_dirty():
                continue

            if key in self._set:
                element = self._set[key]
                element.commit(right_element, proxy)

                #进行删除操作之后，会留下 INVALID 状态的脏数据，需要删除掉
                if not element.is_valid():
                    delete_key.append(key)
            else:
                assert right_element._state == STATE_ADD
                element = UniqueData(self._name)
                self._set[key] = element
                element.commit(right_element, proxy)

        for key in delete_key:
            del self._set[key]
            del right._set[key]




