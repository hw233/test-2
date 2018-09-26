#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 视图：公共数据
"""

from utils import logger
from datalib.base_view import BaseView
from datalib.data_element import UniqueData
from datalib.data_element import DataSet
from datalib.data_proxy4redis import DataProxy
from common.data.exchange import CommonExchangeInfo

COMMON_ID = 1

class CommonData(BaseView):
    """
    公共数据
    """

    __slots__ = [
            "console",
            "broadcast_list",
            "anneal_record_list",
            "worldboss",
            "exchange",
            "transfer_list",
            "country",
            "cat_list",
            ]

    def load_from_cache(self, id = COMMON_ID):
        """从 cache 中载入
        Args:
            id[int]: common数据目前只有一套
        """
        self.id = id
        proxy = DataProxy()

        proxy.search("commonconsole", id)
        proxy.search_by_index("commonbroadcast", "common_id", id)
        proxy.search_by_index("commonannealrecord", "common_id", id)
        proxy.search("commonworldboss", id)
        proxy.search("commonexchange", id)
        proxy.search_by_index("commontransfer", "common_id", id)
        proxy.search("commoncountry", id)
        #proxy.search("commoncat", id)
        proxy.search_by_index("commoncat", "common_id", id)
        
        defer = proxy.execute()
        defer.addCallback(self._post_load)
        return defer


    def _post_load(self, proxy):
        """从数据库读入数据之后的处理
        """
        if proxy.get_result("commonconsole", self.id) is None:
            return self._create_data()
        else:
            return self._init_data(proxy)


    def _init_data(self, proxy):
        """根据 proxy 的返回值，初始化本地城池数据
        """
        self.console = UniqueData("commonconsole",
                proxy.get_result("commonconsole", self.id))
        self.broadcast_list = DataSet("commonbroadcast",
                proxy.get_all_result("commonbroadcast"))
        self.anneal_record_list = DataSet("commonannealrecord",
                proxy.get_all_result("commonannealrecord"))
        self.worldboss = UniqueData("commonworldboss",
                proxy.get_result("commonworldboss", self.id))
        self.exchange = UniqueData("commonexchange",
                proxy.get_result("commonexchange", self.id))
        self.transfer_list = DataSet("commontransfer", 
                proxy.get_all_result("commontransfer"))
        self.country = UniqueData("commoncountry",
                proxy.get_result("commoncountry", self.id))
       # self.cat = UniqueData("commoncat",
       #         proxy.get_result("commoncat", self.id)) 
        self.cat_list = DataSet("commoncat",
                proxy.get_all_result("commoncat"))
        self.check_validation()
        assert self._valid
        return self


    def _create_data(self):
        """
        创建一份全新的数据
        """
        self.console = UniqueData("commonconsole")
        self.broadcast_list = DataSet("commonbroadcast")
        self.anneal_record_list = DataSet("commonannealrecord")
        self.worldboss = UniqueData("commonworldboss")
        self.exchange = UniqueData("commonexchange")
        self.transfer_list = DataSet("commontransfer")
        self.country = UniqueData("commoncountry")
        self.cat_list = DataSet("commoncat")

        self._valid = False
        return self


    def delete(self):
        """删除数据
        """
        for field_name in self.__slots__:
            field = getattr(self, field_name)
            if isinstance(field, UniqueData):
                field.delete()
            elif isinstance(field, DataSet):
                for item in field:
                    item.delete()

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


