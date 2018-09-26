#coding:utf8
"""
Created on 2016-09-21
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 视图：玩家数据
"""

from utils import logger
from datalib.base_view import BaseView
from datalib.data_element import UniqueData
from datalib.data_element import DataSet
from datalib.data_proxy4redis import DataProxy


BASIC_ID = 111111111

class BasicData(BaseView):
    """
    存在redis中的基础数据，作为字典用途
    """

    #和数据库中的字段对应
    __slots__ = [
            "init",
            "activity_list",
            "activity_step_list",
            "activity_hero_reward_list",
            "worldboss_list",
            ]


    def load_from_cache(self, id):
        """从 cache 中载入基础数据
        Args:
            id[int]: 
        """
        self.id = id
        proxy = DataProxy()

        proxy.search("basicinit", self.id)

        proxy.search_by_index("basicactivity", "basic_id", self.id)
        proxy.search_by_index("basicactivitystep", "basic_id", self.id)
        proxy.search_by_index("basicactivityheroreward", "basic_id", self.id)
        proxy.search_by_index("basicworldboss", "basic_id", self.id)
        
        defer = proxy.execute()
        defer.addCallback(self._post_load)
        return defer


    def _post_load(self, proxy):
        """从数据库读入数据之后的处理
        """
        if proxy.get_result("basicinit", self.id) is None:
            return self._create_data()
        else:
            return self._init_data(proxy)


    def _init_data(self, proxy):
        """根据 proxy 的返回值，初始化数据
        """
        self.init = UniqueData("basicinit", proxy.get_result("basicinit", self.id))

        self.activity_list = DataSet("basicactivity", 
                proxy.get_all_result("basicactivity"))
        self.activity_step_list = DataSet("basicactivitystep", 
                proxy.get_all_result("basicactivitystep"))
        self.activity_hero_reward_list = DataSet("basicactivityheroreward",
                proxy.get_all_result("basicactivityheroreward"))
 
        self.worldboss_list = DataSet("basicworldboss", 
                proxy.get_all_result("basicworldboss"))

        self.check_validation()
        assert self._valid
        return self


    def _create_data(self):
        """
        创建一份全新的数据
        """
        self.init = UniqueData("basicinit")
        self.activity_list = DataSet("basicactivity")
        self.activity_step_list = DataSet("basicactivitystep")
        self.activity_hero_reward_list = DataSet("basicactivityheroreward")
        self.worldboss_list = DataSet("basicworldboss")

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


