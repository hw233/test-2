#coding:utf8
"""
Created on 2015-04-08
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 解析数据表定义
"""

import os
import json
from firefly.utils.singleton import Singleton
from utils import logger


class Table(object):
    """数据格式
    """

    def __init__(self, name):
        self.name = name #表名
        self.data = None #关联的数据结构名

        #所有字段
        self.fields = {}
        self.field_set = []

        #主键字段
        self.key = None
        #索引字段
        self.index = []
        #排序字段
        self.rank = []
        #集合字段（集合字段必须全不相同，unique 含义）
        self.set = []
        #外键字段
        self.foreign = {}


    def show(self):
        output = "===[table=%s]===\n" % self.name
        for key in self.fields:
            output += "\t[field=%s]\n" % self.fields[key]
        output += "[key=%s]\n" % self.key
        output += "[index=%s]\n" % self.index
        output += "[rank=%s]\n" % self.rank
        output += "[set=%s]\n" % self.set
        logger.debug(output)



class TableDescription(object):
    """数据格式描述
    """

    def __init__(self):
        self.tables = {}


    def parse(self, file_name):
        conf = json.load(open(file_name, 'r'))
        tables_conf = conf.get("tables")

        for table_conf in tables_conf:
            table = self._parse_table(table_conf)
            if table is None:
                logger.warning("Parse table conf failed[file=%s]" % file_name)
                return False
            self.tables[table.name] = table
        
        for table_conf in tables_conf:
            self._parse_table_foreign(table_conf)

        # for name in self.tables:
        #     self.tables[name].show()

        return True


    def _parse_table(self, conf):
        """解析一张表
        Args:
            conf[json]: json 格式，数据表定义
        Returns:
            table[Table]: Table 定义
        """
        #解析 表名
        name = str(conf.get("name"))
        table = Table(name)

        #解析 关联的数据结构名称
        data = conf.get("data")
        assert data is not None
        table.data = data

        #解析 字段 name + type
        fields = conf.get("fields")
        assert fields is not None
        for field in fields:
            field_name = str(field.get("name"))
            if field_name in table.field_set:
                logger.warning("Duplicate field[table=%s][field=%s]" %
                        (table.name, field_name))
            table.field_set.append(field_name)
            field_type = str(field.get("type"))
            table.fields[field_name] = field_type

        #解析 主键 (唯一)
        key_name = str(conf.get("key"))
        assert key_name is not None
        if key_name not in table.fields:
            logger.warning("Invalid key[table=%s][key=%s]" % (table.name, key_name))
            return None
        table.key = key_name

        #解析 索引字段
        index = conf.get("index")
        if index is not None:
            for item in index:
                if item not in table.fields:
                    logger.warning("Invalid index[table=%s][index=%s]" % (table.name, item))
                    return None
                table.index.append(str(item))

        #解析 排序字段
        rank = conf.get("rank")
        if rank is not None:
            for item in rank:
                if item not in table.fields:
                    logger.warning("Invalid rank[table=%s][rank=%s]" % (table.name, item))
                    return None
                table.rank.append(str(item))

        #解析 集合字段
        set = conf.get("set")
        if set is not None:
            for item in set:
                if item not in table.fields:
                    logger.warning("Invalid set[table=%s][set=%s]" % (table.name, item))
                    return None
                table.set.append(str(item))

        return table

    def _parse_table_foreign(self, conf):
        """解析一张表的外键约束"""
        name = conf.get("name")
        assert name in self.tables.keys()

        foreign = conf.get("foreign")
        if foreign is not None:
            for item in foreign:
                table = str(item["table"])
                if table not in self.tables.keys():
                    logger.warning("Invalid foreign[table=%s][foreign=%s]" % (name, item))
                    return False
                field = str(item["field"])
                if field not in self.tables[name].field_set:
                    logger.warning("Invalid foreign[table=%s][foreign=%s]" % (name, item))
                    return False
                self.tables[name].foreign[field] = table
                
        return True