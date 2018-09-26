#coding:utf8
"""
Created on 2016-05-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 视图：玩家数据
"""

from utils import logger
from datalib.base_view import BaseView
from datalib.data_element import UniqueData
from datalib.data_element import DataSet
from datalib.data_proxy4redis import DataProxy


class UserData(BaseView):
    """
    一个用户的所有数据
    """

    #和数据库中的字段对应
    __slots__ = [
            "user",
            "resource",

            "hero_list",
            "team_list",
            #FIXME:guard实际上是单个数据, 却保存在集合里?
            "guard_list",
            "item_list",
            "soldier_list",
            "technology_list",
            "herostar_list",

            "city_list",
            "building_list",
            "conscript_list",
            "defense_list",

            "map",
            "energy",
            "node_list",
            "battle_list",
            "rival_list",
            "visit_list",
            "question",
            "dungeon",
            "arena",
            "arena_record_list",
            "melee",
            "melee_record_list",
            "exploitation",
            "transfer",
            "transfer_record_list",

            "pray",

            "legendcity_list",
            "legendcity_record_list",

            "union",
            "userdonatebox_list",
            "unionboss_list",

            "draw",
            "pay",
            "pay_record_list",
            "shop_list",
            "activity_list",

            "sign",
            "mission_list",
            "postoffice",
            "mail_list",
            "statistics",
            "battle_score",
            "trainer",
            "chest",
            
            "anneal",
            "worldboss",
            "expand_dungeon_list",

            "plunder",
            "plunder_record_list",

            "friend_list",
            "message_list",
            
            ]


    def load_from_cache(self, id):
        """从 cache 中载入用户数据
        Args:
            id[int]: 用户 id
        """
        self.id = id
        proxy = DataProxy()

        proxy.search("user", id)
        proxy.search("resource",id)

        proxy.search_by_index("hero", "user_id", id)
        proxy.search_by_index("team", "user_id", id)
        proxy.search("guard", id)
        proxy.search_by_index("item", "user_id", id)
        proxy.search_by_index("soldier", "user_id", id)
        proxy.search_by_index("technology", "user_id", id)
        proxy.search_by_index("herostar", "user_id", id)

        proxy.search_by_index("city", "user_id", id)
        proxy.search_by_index("building", "user_id", id)
        proxy.search_by_index("conscript", "user_id", id)
        proxy.search_by_index("defense", "user_id", id)

        proxy.search("map", id)
        proxy.search("energy", id)
        proxy.search_by_index("node", "user_id", id)
        proxy.search_by_index("battle", "user_id", id)
        proxy.search_by_index("rival", "user_id", id)
        proxy.search_by_index("visit", "user_id", id)
        proxy.search("question", id)
        proxy.search("dungeon", id)
        proxy.search("arena", id)
        proxy.search_by_index("arena_record", "user_id", id)
        proxy.search("melee", id)
        proxy.search_by_index("melee_record", "user_id", id)
        proxy.search("exploitation", id)
        proxy.search("transfer", id)
        proxy.search_by_index("transfer_record", "user_id", id)

        proxy.search("pray", id)

        proxy.search_by_index("legendcity", "user_id", id)
        proxy.search_by_index("legendcity_record", "user_id", id)

        proxy.search("union", id)
        proxy.search_by_index("userdonatebox", "user_id", id)
        proxy.search_by_index("userunionboss", "user_id", id)

        proxy.search("draw", id)
        proxy.search("pay", id)
        proxy.search_by_index("pay_record", "user_id", id)
        proxy.search_by_index("activity", "user_id", id)
        proxy.search_by_index("shop", "user_id", id)

        proxy.search("sign", id)
        proxy.search_by_index("mission", "user_id", id)
        proxy.search("postoffice", id)
        proxy.search_by_index("mail", "user_id", id)
        proxy.search("battle_score", id)
        proxy.search("statistics", id)
        proxy.search("trainer", id)
        proxy.search("chest", id)
        
        proxy.search("anneal", id)
        proxy.search("worldboss", id)
        proxy.search_by_index("expand_dungeon", "user_id", id)
        
        proxy.search("plunder", id)
        proxy.search_by_index("plunder_record", "user_id", id)

        proxy.search_by_index("friend", "user_id", id)
        proxy.search_by_index("message", "user_id", id)
        defer = proxy.execute()
        defer.addCallback(self._post_load)
        return defer


    def _post_load(self, proxy):
        """从数据库读入数据之后的处理
        """
        if proxy.get_result("user", self.id) is None:
            return self._create_data()
        else:
            return self._init_data(proxy)


    def _init_data(self, proxy):
        """根据 proxy 的返回值，初始化本地用户数据
        """
        self.user = UniqueData("user", proxy.get_result("user", self.id))
        self.resource = UniqueData("resource", proxy.get_result("resource", self.id))

        self.hero_list = DataSet("hero", proxy.get_all_result("hero"))
        self.team_list = DataSet("team", proxy.get_all_result("team"))
        self.guard_list = DataSet("guard", proxy.get_all_result("guard"))
        self.item_list = DataSet("item", proxy.get_all_result("item"))
        self.soldier_list = DataSet("soldier", proxy.get_all_result("soldier"))
        self.technology_list = DataSet("technology", proxy.get_all_result("technology"))
        self.herostar_list = DataSet("herostar", proxy.get_all_result("herostar"))

        self.city_list = DataSet("city", proxy.get_all_result("city"))
        self.building_list = DataSet("building", proxy.get_all_result("building"))
        self.conscript_list = DataSet("conscript", proxy.get_all_result("conscript"))
        self.defense_list = DataSet("defense", proxy.get_all_result("defense"))

        self.map = UniqueData("map", proxy.get_result("map", self.id))
        self.energy = UniqueData("energy", proxy.get_result("energy", self.id))
        self.node_list = DataSet("node", proxy.get_all_result("node"))
        self.rival_list = DataSet("rival", proxy.get_all_result("rival"))
        self.visit_list = DataSet("visit", proxy.get_all_result("visit"))
        self.question = UniqueData("question", proxy.get_result("question", self.id))
        self.dungeon = UniqueData("dungeon", proxy.get_result("dungeon", self.id))
        self.battle_list = DataSet("battle", proxy.get_all_result("battle"))
        self.arena = UniqueData("arena", proxy.get_result("arena", self.id))
        self.arena_record_list = DataSet("arena_record", proxy.get_all_result("arena_record"))
        self.melee = UniqueData("melee", proxy.get_result("melee", self.id))
        self.melee_record_list = DataSet("melee_record", proxy.get_all_result("melee_record"))
        self.exploitation = UniqueData("exploitation", proxy.get_result("exploitation", self.id))
        self.transfer = UniqueData("transfer", proxy.get_result("transfer", self.id))
        self.transfer_record_list = DataSet("transfer_record", proxy.get_all_result("transfer_record"))

        self.pray = UniqueData("pray", proxy.get_result("pray", self.id))

        self.legendcity_list = DataSet(
                "legendcity", proxy.get_all_result("legendcity"))
        self.legendcity_record_list = DataSet(
                "legendcity_record", proxy.get_all_result("legendcity_record"))

        self.union = UniqueData("union", proxy.get_result("union", self.id))
        self.userdonatebox_list = DataSet("userdonatebox", proxy.get_all_result("userdonatebox"))
        self.unionboss_list = DataSet("userunionboss", proxy.get_all_result("userunionboss"))

        self.draw = UniqueData("draw", proxy.get_result("draw", self.id))
        self.pay = UniqueData("pay", proxy.get_result("pay", self.id))
        self.pay_record_list = DataSet("pay_record", proxy.get_all_result("pay_record"))
        self.shop_list = DataSet("shop", proxy.get_all_result("shop"))
        self.activity_list = DataSet("activity", proxy.get_all_result("activity"))

        self.sign = UniqueData("sign", proxy.get_result("sign", self.id))
        self.statistics = UniqueData("statistics", proxy.get_result("statistics", self.id))
        self.mission_list = DataSet("mission", proxy.get_all_result("mission"))
        self.postoffice = UniqueData("postoffice", proxy.get_result("postoffice", self.id))
        self.mail_list = DataSet("mail", proxy.get_all_result("mail"))
        self.battle_score = UniqueData("battle_score",
                proxy.get_result("battle_score", self.id))
        self.trainer = UniqueData("trainer", proxy.get_result("trainer", self.id))
        self.chest = UniqueData("chest", proxy.get_result("chest", self.id))
        
        self.anneal = UniqueData("anneal", proxy.get_result("anneal", self.id))
        self.worldboss = UniqueData("worldboss", proxy.get_result("worldboss", self.id))
        self.expand_dungeon_list = DataSet("expand_dungeon",
                proxy.get_all_result("expand_dungeon"))
        
        self.plunder = UniqueData("plunder", proxy.get_result("plunder", self.id))
        self.plunder_record_list = DataSet("plunder_record", proxy.get_all_result("plunder_record"))
        

        self.friend_list = DataSet("friend", proxy.get_all_result("friend"))
        self.message_list = DataSet("message", proxy.get_all_result("message"))
        self.check_validation()
        assert self._valid
        return self


    def _create_data(self):
        """
        创建一份全新的数据
        """
        self.user = UniqueData("user")
        self.resource = UniqueData("resource")

        self.hero_list = DataSet("hero")
        self.team_list = DataSet("team")
        self.guard_list = DataSet("guard")
        self.item_list = DataSet("item")
        self.soldier_list = DataSet("soldier")
        self.technology_list = DataSet("technology")
        self.herostar_list = DataSet("herostar")

        self.city_list = DataSet("city")
        self.building_list = DataSet("building")
        self.conscript_list = DataSet("conscript")
        self.defense_list = DataSet("defense")

        self.map = UniqueData("map")
        self.energy = UniqueData("energy")
        self.node_list = DataSet("node")
        self.battle_list = DataSet("battle")
        self.rival_list = DataSet("rival")
        self.visit_list = DataSet("visit")
        self.question = UniqueData("question")
        self.dungeon = UniqueData("dungeon")
        self.arena = UniqueData("arena")
        self.arena_record_list = DataSet("arena_record")
        self.melee = UniqueData("melee")
        self.melee_record_list = DataSet("melee_record")
        self.exploitation = UniqueData("exploitation")
        self.transfer = UniqueData("transfer")
        self.transfer_record_list = DataSet("transfer_record")

        self.pray = UniqueData("pray")

        self.legendcity_list = DataSet("legendcity")
        self.legendcity_record_list = DataSet("legendcity_record")

        self.union = UniqueData("union")
        self.userdonatebox_list = DataSet("userdonatebox")
        self.unionboss_list = DataSet("userunionboss")

        self.draw = UniqueData("draw")
        self.pay = UniqueData("pay")
        self.pay_record_list = DataSet("pay_record")
        self.shop_list = DataSet("shop")
        self.activity_list = DataSet("activity")

        self.sign = UniqueData("sign")
        self.mission_list = DataSet("mission")
        self.postoffice = UniqueData("postoffice")
        self.mail_list = DataSet("mail")
        self.statistics = UniqueData("statistics")
        self.battle_score = UniqueData("battle_score")
        self.trainer = UniqueData("trainer")
        self.chest = UniqueData("chest")
        
        self.anneal = UniqueData("anneal")
        self.worldboss = UniqueData("worldboss")
        self.expand_dungeon_list = DataSet("expand_dungeon")
        
        self.plunder = UniqueData("plunder")
        self.plunder_record_list = DataSet("plunder_record")

        self.friend_list = DataSet("friend")
        self.message_list = DataSet("message")
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


