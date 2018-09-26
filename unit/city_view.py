#coding:utf8
"""
Created on 2016-05-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 视图：史实城数据
"""

from utils import logger
from datalib.base_view import BaseView
from datalib.data_element import UniqueData
from datalib.data_element import DataSet
from datalib.data_proxy4redis import DataProxy



class CityData(BaseView):
    """
    史实城的所有数据
    """

    __slots__ = [
            "city",
            "position_list",
            ]

    def load_from_cache(self, id):
        """从 cache 中载入城池数据
        Args:
            id[int]: 城池 id
        """
        self.id = id
        proxy = DataProxy()

        proxy.search("unitcity", id)
        proxy.search_by_index("unitposition", "city_id", id)

        defer = proxy.execute()
        defer.addCallback(self._post_load)
        return defer


    def _post_load(self, proxy):
        """从数据库读入数据之后的处理
        """
        if proxy.get_result("unitcity", self.id) is None:
            return self._create_data()
        else:
            return self._init_data(proxy)


    def _init_data(self, proxy):
        """根据 proxy 的返回值，初始化本地城池数据
        """
        self.city = UniqueData("unitcity", proxy.get_result("unitcity", self.id))
        self.position_list = DataSet("unitposition", proxy.get_all_result("unitposition"))

        self.check_validation()
        assert self._valid
        return self


    def _create_data(self):
        """
        创建一份全新的数据
        """
        self.city = UniqueData("unitcity")
        self.position_list = DataSet("unitposition")

        self._valid = False
        return self


    def delete(self):
        """删除数据
        """
        self.city.delete()
        for position in self.position_list:
            position.delete()

        self._valid = False


    def check_validation(self):
        """检查数据是否合法
        """
        self._valid = True
        for field_name in self.__slots__:
            field = getattr(self, field_name)
            self._valid &= field.is_valid()
            if not self._valid:
                break


    def rollback(self, right):
        """回滚数据
        将自身的数据恢复到和 right 一致
        Args:
            right[UserData]: 正确的数据
        """
        for field_name in self.__slots__:
            lfield = getattr(self, field_name)
            rfield = getattr(right, field_name)
            lfield.rollback(rfield)


    def commit(self, right):
        """确认修改
        将自身的数据修改到和 right 一致，并同步到 DB 中
        """
        proxy = DataProxy()

        for field_name in self.__slots__:
            lfield = getattr(self, field_name)
            rfield = getattr(right, field_name)
            lfield.commit(rfield, proxy)

        defer = proxy.execute()
        defer.addCallback(self._check_commit)
        return defer


    def _check_commit(self, proxy):
        assert proxy.status == 0
        return self


