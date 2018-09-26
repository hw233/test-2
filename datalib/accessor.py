#coding:utf8
"""
Created on 2015-12-05
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 封装 Redis 的存储和访问细节 (schema 信息)
"""

from firefly.utils.singleton import Singleton
from firefly.server.globalobject import GlobalObject
from utils import logger

#导入所有相关的数据结构
from app.data.all import *
from unit.data.all import *
from gunion.data.all import *
from common.data.all import *


class TableAccessor(object):
    """封装数据表的存储和访问细节
    使用 Redis String 存储数据表
    key : 数据表名 & 数据主键值
    value : 数据序列化
    """
    SEP = '&'


    def __init__(self, desc):
        self._desc = desc


    def generate_key_prefix(self):
        """生成 Redis String key prefix
        """
        prefix = "%s%s" % (self._desc.name, self.SEP)
        return prefix


    def generate_key(self, data_key_value):
        """生成 Redis String key
        """
        key_string = "%s%s%s" % (self._desc.name, self.SEP, str(data_key_value))
        return key_string


    def generate_key_by_data(self, data):
        """生成 Redis String key
        """
        data_key_value = str(getattr(data, self._desc.key))
        return self.generate_key(data_key_value)


    def generate_value(self, data):
        """生成 Redis String value
        序列化 serialization
        """
        assert data is not None

        value_list = []
        for field_name in self._desc.field_set:
            value_list.append(str(getattr(data, field_name)))
        return self.SEP.join(value_list)


    def parse(self, response):
        """解析 Redis 的返回值，生成数据
        反序列化 deserialization
        """
        if response is None:
            return None

        data = self._create_data()

        field_list = response.split(self.SEP)
        for i, field_name in enumerate(self._desc.field_set):
            field_type = self._desc.fields[field_name]
            # logger.debug("[field_name=%s][field_value=%s]" % (field_name, field_list[i]))
            value = self._parse_field(field_type, field_list[i])
            setattr(data, field_name, value)
            # logger.debug("[%s=%s]" % (field_name, value))

        return data


    def _create_data(self):
        """根据对象名称，创建对象实例
        """
        # logger.debug("create %s" % self._desc.data)
        return globals()[self._desc.data]()


    def _parse_field(self, field_type, value):
        """根据字段类型，解析字段
        """
        if field_type == "bigint" or field_type == "int":
            return int(value)
        elif field_type == "bool":
            if value == "False":
                return False
            else:
                return True
        elif field_type.startswith("char"):
            return value
        elif field_type == "float":
            return float(value)
        else:
            raise Exception("Invalid type[type=%s]" % field_type)


class SetAccessor(object):
    """封装 Set 的存储和访问细节
    使用 Redis Set 存储索引信息
    key : SET数据表名
    """
    SEP = '&'


    def __init__(self, desc):
        self._desc = desc


    def all(self):
        return self._desc.set


    def generate_key(self, set_name):
        """生成 Redis Set key
        """
        assert set_name in self._desc.set
        #集合表名：INDEX tablename&set_name
        set_string = "SET%s%s%s" % (self._desc.name, self.SEP, set_name)
        return set_string


    def generate_member(self, data, set_name):
        """生成 Redis Set member
        对应字段的值
        """
        assert set_name in self._desc.set
        data_key_value = str(getattr(data, set_name))
        return data_key_value


    def parse(self, set_name, response):
        """解析 Redis 返回，得到 members
        """
        values = []
        for r in response:
            field_type = self._desc.fields[set_name]
            values.append(self._parse_field(field_type, r))

        return values


    def _parse_field(self, field_type, value):
        """根据字段类型，解析字段
        """
        if field_type == "bigint" or field_type == "int":
            return int(value)
        elif field_type == "bool":
            if value == "False":
                return False
            else:
                return True
        elif field_type.startswith("char"):
            return value
        elif field_type == "float":
            return float(value)
        else:
            raise Exception("Invalid type[type=%s]" % field_type)



class IndexAccessor(object):
    """封装 Index 的存储和访问细节
    使用 Redis Set 存储索引信息
    key : INDEX数据表名 & 数据索引列名 & 数据索引列值
    member: 数据主键值
    """
    SEP = '&'


    def __init__(self, desc):
        self._desc = desc


    def _get_data_index_value(self, data, index_name):
        """获取 data 的索引列值
        """
        assert index_name in self._desc.index
        index_value = getattr(data, index_name)
        return index_value


    def all(self):
        return self._desc.index

    def generate_key_prefix(self, index_name):
        """生成 Redis Set key prefix"""
        assert index_name in self._desc.index
        prefix = "INDEX%s%s%s%s" % (
                self._desc.name, self.SEP, index_name, self.SEP)
        return prefix

    def generate_key(self, index_name, index_value):
        """生成 Redis Set key
        """
        # logger.debug("[name=%s][index_name=%s]" % (self.name, index_name))
        assert index_name in self._desc.index

        #索引表名：INDEX tablename & indexname & indexvalue
        index_string = "INDEX%s%s%s%s%s" % (
                self._desc.name, self.SEP, index_name, self.SEP, str(index_value))
        return index_string


    def generate_key_by_data(self, index_name, data):
        """生成 Redis Set key
        """
        index_value = self._get_data_index_value(data, index_name)
        return self.generate_key(index_name, index_value)


    def generate_member(self, data):
        """生成 Redis Set member
        数据的主键值
        """
        data_key_value = str(getattr(data, self._desc.key))
        return data_key_value


    def parse(self, response):
        """解析 Redis 返回，得到 members
        """
        return response


class RankAccessor(object):
    """封装 Rank 的存储和访问细节
    使用 Redis SortedSet 存储排序信息
    key : RANK数据表名 & 数据排序列名
    score : 数据排序列值
    member : 数据主键值
    """
    SEP = '&'


    def __init__(self, desc):
        self._desc = desc


    def all(self):
        return self._desc.rank


    def generate_key(self, rank_name):
        """获取排序表的名称
        """
        assert rank_name in self._desc.rank
        return "RANK%s%s" % (self._desc.name, rank_name)


    def generate_score(self, rank_name, data):
        """生成 Redis SortedSet score
        数据的排序列值
        """
        assert rank_name in self._desc.rank
        data_rank_value = getattr(data, rank_name)
        return data_rank_value


    def generate_member(self, data):
        """生成 Redis Set member
        数据的主键值
        """
        data_key_value = str(getattr(data, self._desc.key))
        return data_key_value


    def parse(self, response):
        """解析 Redis 返回，得到 members
        """
        return response


class RedisAccessor(object):

    def __init__(self, data_desc):
        """
        """
        self.table = TableAccessor(data_desc)
        self.index = IndexAccessor(data_desc)
        self.rank = RankAccessor(data_desc)
        self.set = SetAccessor(data_desc)


class AccessorFactory(object):
    """
    """
    __metaclass__ = Singleton

    def __init__(self):
        self.load(GlobalObject().table_desc)


    def load(self, table_desc):
        self.accessors = {}
        for table_name in table_desc.tables:
            self.accessors[table_name] = RedisAccessor(table_desc.tables[table_name])

