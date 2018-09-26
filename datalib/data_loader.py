#coding:utf8
"""
Created on 2015-01-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 读 Excel 文件（basic info），生成 dict，提供访问接口
"""

import os
import sys
import json
import xlrd
import time
from utils import logger
from firefly.server.globalobject import GlobalObject
from datalib.cdata_loader import cdata_loader

class DataLoader:
    """读入 Excel 文件
    每个 sheet 生成一个 dict
    """
    def __init__(self):
        self.factory = DataFactory()


    def get(self, name):
        dict_name = self.map_dict_name(name)
        d = getattr(self, dict_name)
        return d


    def load(self, path, file_conf):
        """读入一个文件，生成对应的 dict
        @param path: 文件路径
        @param file_conf: 文件配置
        """
        file_name = "%s%s" % (path, file_conf.get("name"))
        dicts_conf = file_conf.get("dicts")

        data = xlrd.open_workbook(file_name)
        start = time.time()

        for conf in dicts_conf:
            self._gen_dict(data, conf)

        duration = int((time.time() - start) * 1000)
        logger.trace("Finish load file[file=%s][consume=%d ms]" %
                (file_name, duration))


    def _gen_dict(self, data, dict_conf):
        sheets_name = dict_conf.get("sheets")
        if len(sheets_name) == 1:
            name = sheets_name[0]
        else:
            name = dict_conf.get("name")
        keys = dict_conf.get("key")

        dict_name = self.map_dict_name(name)
        setattr(self, dict_name, {})
        sheet_dict = getattr(self, dict_name)

        for sheet_name in sheets_name:
            try:
                self._load_sheet(data, sheet_name, sheet_dict, keys)
            except Exception as e:
                logger.warning("Gen dict failed[sheet name=%s][dict name=%s]" %
                        (sheet_name, dict_name))
                raise e

        # logger.debug("Finish gen dict[gen dict=%s]" % dict_name)


    def _load_sheet(self, data, sheet_name, sheet_dict ,keys):
        """读入 Excel 中的一个 Sheet，一个 Sheet 生成一个 dict"""
        sheet = data.sheet_by_name(sheet_name)
        assert sheet.nrows >= 2
        assert sheet.ncols >= 1

        type_row = sheet.row_values(0)
        name_row = sheet.row_values(1)

        for key in keys:
            if key not in name_row:
                raise Exception("Data file invalid, "
                        "key not found in sheet[key=%s][sheet=%s]" % (key, sheet_name))

        for index in range(2, sheet.nrows):
            row = self.factory.create(sheet, type_row, name_row, sheet.row_values(index))
            if len(keys) == 1:
                key = getattr(row, keys[0])
                sheet_dict[key] = row
            else:
                key = ""
                for name in keys:
                    if key != "":
                        key += "_"
                    value = getattr(row, name)
                    key += str(value)
                sheet_dict[key] = row

        # logger.debug("Finish load sheet[sheet=%s]" % sheet_name)


    def map_dict_name(self, name):
        return "%s_dict" % str(name)


class DataFactory:
    """创建 Data 实例
    根据输入，动态定义类的变量，生成类的定义
    """
    def _parse_data_by_type(self, data, type):
        if type == "System.Int32":
            return self._parse_int(data)
        elif type == "System.Single":
            return self._parse_float(data)
        elif type == "System.String":
            return self._parse_string(data)
        elif type == "System.Int32[]":
            return self._parse_int_array(data)
        elif type == "System.Single[]":
            return self._parse_float_array(data)
        elif type == "System.String[]":
            return self._parse_string_array(data)
        elif type == "System.Boolean":
            return self._parse_bool(data)
        else:
            raise Exception("Invalid Type[type=%s]" % type)


    def _parse_int(self, data):
        """解析整型
        如果数值配置中留空，默认为0
        """
        if data == "":
            return 0
        else:
            return int(data)


    def _parse_int_array(self, data):
        """解析整型数组
        如果数值配置中留空，默认为空数组
        """
        items = []
        if data == "":
            return items

        if not isinstance(data, unicode):
            items.append(int(data))
            return items

        fields = data.split('#')
        for field in fields:
            if field == "":
                items.append(0)
            else:
                items.append(int(field))
        return items


    def _parse_float(self, data):
        """解析浮点类型
        如果数值配置中留空，默认为0.0
        """
        if data == "":
            return 0.0
        else:
            return float(data)


    def _parse_float_array(self, data):
        """解析浮点类型数组
        如果数值配置中留空，默认为空数组
        """
        items = []
        if data == "":
            return items

        if not isinstance(data, unicode):
            items.append(float(data))
            return items

        fields = data.split('#')
        for field in fields:
            if field == "":
                items.append(0.0)
            else:
                items.append(float(field))
        return items


    def _parse_string(self, data):
        """解析字符串
        """
        if isinstance(data, unicode):
            return data
        else:
            return str(data)


    def _parse_string_array(self, data):
        """解析字符串数组
        """
        items = []
        fields = data.split('#')
        for field in fields:
            if isinstance(data, unicode):
                items.append(field)
            else:
                items.append(str(field))
        return items


    def _parse_bool(self, data):
        """解析布尔类型
        不允许留空
        """
        if data.lower() == "false":
            return False
        elif data.lower() == "true":
            return True
        else:
            raise Exception("Unexpected bool data[data=%s]" % data)


    def create(self, name, type_row, name_row, data_row):
        assert len(type_row) == len(name_row) == len(data_row)

        attribute = {}

        sub = False
        sub_class = ""
        sub_type_row = []
        sub_name_row = []
        sub_data_row = []

        for index in range(len(type_row)):

            fields = name_row[index].split('.', 2)
            if len(fields) == 1:
                if sub:
                    DataClass = self.create(
                            sub_class, sub_type_row, sub_name_row, sub_data_row)
                    attribute[sub_class] = DataClass()

                    sub = False
                    sub_class = ""
                    sub_type_row = []
                    sub_name_row = []
                    sub_data_row = []

                attribute[str(name_row[index])] = self._parse_data_by_type(
                        data_row[index], type_row[index])

            elif len(fields) == 2:
                if not sub:
                    sub_type_row = []
                    sub_name_row = []
                    sub_data_row = []

                    sub_class = fields[0]
                    sub_type_row.append(type_row[index])
                    sub_name_row.append(fields[1])
                    sub_data_row.append(data_row[index])
                    sub = True
                elif sub and fields[0] == sub_class:
                    sub_type_row.append(type_row[index])
                    sub_name_row.append(fields[1])
                    sub_data_row.append(data_row[index])
                else:
                    DataClass = self.create(sub_class, sub_type_row, sub_name_row, sub_data_row)
                    attribute[sub_class] = DataClass()

                    sub_type_row = []
                    sub_name_row = []
                    sub_data_row = []
                    sub_class = fields[0]
                    sub_type_row.append(type_row[index])
                    sub_name_row.append(fields[1])
                    sub_data_row.append(data_row[index])

        return type(str(name), (), attribute)


class Data(object):
    """假装自己是row-object"""

    def __init__(self, d):
        self._dict = d
    
    def __getattribute__(self, *args, **kw):
        name = args[0]
        if name == "_dict":
            try:
                d = object.__getattribute__(self, *args, **kw)
            except:
                return {}
            return d
        if name in self._dict:
            value = self._dict[name]
            if isinstance(value, dict):
                return Data(value)
            elif isinstance(value, str):
                return unicode(value, "utf8")
            else:
                return value
        else:
            return object.__getattribute__(self, *args, **kw)

    def __setattr__(self, *args, **kw):
        name = args[0]
        value = args[1]

        if name in self._dict:
            self._dict[name] = value
            return value
        else:
            return object.__setattr__(self, *args, **kw)

class Sheet(object):
    """假装自己是dict"""

    def __init__(self, name):
        self._name = name
        self._keys = None

    def _get_keys(self):
        if self._keys == None:
            self._keys = cdata_loader.get_keys(self._name)
        return self._keys

    def __getitem__(self, key):
        data = cdata_loader.get(self._name, str(key))
        if data == {}:
            raise KeyError("%s not in %s" % (key, self._name))
        return Data(data)

    def __iter__(self):
        return self._get_keys().__iter__()

    def keys(self):
        return self._get_keys()

    def has_key(self, key):
        return key in self

    def values(self):
        """效率低下尽量不要使用"""
        values = []
        for key in self:
            values.append(self[key])
        return values

    def items(self):
        """效率低下尽量不要使用"""
        items = []
        for key in self:
            items.append((key, self[key]))
        return items

    def __len__(self):
        return len(self._get_keys())

class CDataloader(object):
    """调用C++实现的dataloader"""

    def load(self, conf_path, version):
        cdata_loader.init(conf_path, version)
        cdata_loader.load()

    def __getattribute__(self, *args, **kw):
        name = args[0]
        array = name.split("_")
        if len(array) == 2 and array[1] == "dict":
            return self.get(array[0])
        else:
            return object.__getattribute__(self, *args, **kw)

    def get(self, name):
        return Sheet(name)

#data_loader = DataLoader()
data_loader = CDataloader()

def load_data(conf_path):
    if isinstance(data_loader, DataLoader):
        config = json.load(open(conf_path, 'r'))
        path = config.get("path")[GlobalObject().version]
        files_name = os.listdir(path)
        files_conf = config.get("files")

        for conf in files_conf:
            name = conf.get("name")
            if name  not in files_name:
                logger.warning("Data file not exist[name=%s]" % name)
                continue

            # try:
            data_loader.load(path, conf)
            # except Exception as e:
            #     logger.fatal("Load data file failed[file=%s][exception=%s]" % (name, e))
            #     sys.exit(-1)
    else:
        start = time.time()
        data_loader.load(conf_path, GlobalObject().version)
        duration = int((time.time() - start) * 1000)
        logger.trace("cdata_loader load succeed[consume=%d]" % duration)


def load_specific_data(conf_path, file_name):
    config = json.load(open(conf_path, 'r'))
    path = config.get("path")
    files_name = os.listdir(path)
    files_conf = config.get("files")

    for conf in files_conf:
        name = conf.get("name")
        if name in files_name and name == file_name:
            data_loader.load(path, conf)
            return

    raise Exception("Data file not exist[name=%s]" % file_name)

