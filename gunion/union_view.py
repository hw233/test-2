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


class UnionData(BaseView):
    """联盟所有数据
    """

    __slots__ = [
            "union",
            "member_list",
            "application_list",
            "aid_list",

            "season",
            "battle_list",
            "battle_node_list",
            "battle_record_list",

            "donate_box_list",
            "donate_record_list",

            "union_boss_list",
            ]


    def load_from_cache(self, id):
        """从 cache 中载入联盟数据
        Args:
            id[int]: 联盟 id
        """
        self.id = id
        proxy = DataProxy()

        proxy.search("unionunion", id)
        proxy.search_by_index("unionmember", "union_id", id)
        proxy.search_by_index("unionapplication", "union_id", id)
        proxy.search_by_index("unionaid", "union_id", id)

        proxy.search("unionseason", id)
        proxy.search_by_index("unionbattle", "union_id", id)
        proxy.search_by_index("unionbattle_node", "union_id", id)
        proxy.search_by_index("unionbattle_record", "union_id", id)

        proxy.search_by_index("uniondonatebox", "union_id", id)
        proxy.search_by_index("uniondonaterecord", "union_id", id)

        proxy.search_by_index("unionboss", "union_id", id)

        defer = proxy.execute()
        defer.addCallback(self._post_load)
        return defer


    def _post_load(self, proxy):
        """从数据库读入数据之后的处理
        """
        if proxy.get_result("unionunion", self.id) is None:
            return self._create_data()
        else:
            return self._init_data(proxy)


    def _init_data(self, proxy):
        """根据 proxy 的返回值，初始化本地城池数据
        """
        self.union = UniqueData("unionunion", proxy.get_result("unionunion", self.id))
        self.member_list = DataSet("unionmember", proxy.get_all_result("unionmember"))
        self.application_list = DataSet("unionapplication",
                proxy.get_all_result("unionapplication"))
        self.aid_list = DataSet("unionaid", proxy.get_all_result("unionaid"))

        self.season = UniqueData("unionseason", proxy.get_result("unionseason", self.id))
        self.battle_list = DataSet("unionbattle", proxy.get_all_result("unionbattle"))
        self.battle_node_list = DataSet("unionbattle_node",
                proxy.get_all_result("unionbattle_node"))
        self.battle_record_list = DataSet("unionbattle_record",
                proxy.get_all_result("unionbattle_record"))

        self.donate_box_list = DataSet("uniondonatebox",
                proxy.get_all_result("uniondonatebox"))
        self.donate_record_list = DataSet("uniondonaterecord",
                proxy.get_all_result("uniondonaterecord"))

        self.union_boss_list = DataSet("unionboss", proxy.get_all_result("unionboss"))

        self.check_validation()
        assert self._valid
        return self


    def _create_data(self):
        """
        创建一份全新的数据
        """
        self.union = UniqueData("unionunion")
        self.member_list = DataSet("unionmember")
        self.application_list = DataSet("unionapplication")
        self.aid_list = DataSet("unionaid")

        self.season = UniqueData("unionseason")
        self.battle_list = DataSet("unionbattle")
        self.battle_node_list = DataSet("unionbattle_node")
        self.battle_record_list = DataSet("unionbattle_record")

        self.donate_box_list = DataSet("uniondonatebox")
        self.donate_record_list = DataSet("uniondonaterecord")

        self.union_boss_list = DataSet("unionboss")

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


