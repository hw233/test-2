#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 封装和 db-agent 的通信逻辑
"""

import time
import types
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.const_value import const_value
from proto.db_pb2 import DBRequest
from proto.db_pb2 import DBResponse
from proto.db_pb2 import Query
from proto.db_pb2 import Item
from app import data


class DataProxy(object):
    def __init__(self):
        #远征匹配到的对手的排名
        self.rivals_rank = []
        self.player = None
        self.players = []
        self._multi_player = False

        self.user = None
        self.users = []
        self._multi_user = None

        self.resource = None
        self.resources = []
        self._multi_resource = None

        self.hero = None
        self.heroes = []
        self._multi_hero = None

        self.city = None
        self.citys = []
        self._multi_city = None

        self.item = None
        self.items = []
        self._multi_item = None

        self.battle = None

        self.shop = None

        self.soldier = None
        self.soldiers = []
        self._multi_soldier = None

        self.building = None
        self.buildings = []
        self._multi_building = None

        self.defense = None
        self.defenses = []
        self._multi_defense = None

        self.pve = None
        self.pves = []
        self._multi_pve = None

        self.rival = None
        self.rivals = []
        self._multi_rival = None

        self.expedition = None
        self.expeditions = []
        self._multi_expedition = None

        self.plunder = None
        self.plunders = []
        self._multi_plunder = None

        self.arena = None
        self.arenas = []
        self._multi_arena = None

        self.reward = None
        self.rewards = []
        self._multi_reward = None

        self.formation = None
        self.formations = []
        self._multi_formation = None

        self.technology = None
        self.technologys = []
        self._multi_technology = None

        self.mission = None
        self.missions = []
        self._multi_mission = None

        self._req = DBRequest()
        self._req.seq_id = 1#目前随便填
        self._query_len = 0

        self.status = -1
        self._call = False

        self.now = None


    def search(self):
        """进行查询"""
        assert not self._call

        if len(self._req.query) == 0:
            raise Exception("Invalid db-agent request, empty query")

        self._call = True

        # print self._req

        request = self._req.SerializeToString()
        defer = GlobalObject().remote['db_agent'].callRemote("query", request)
        defer.addCallback(self._parse_search)
        return defer


    def _parse_search(self, dbstring):
        self.now = int(time.time())
        res = DBResponse()
        res.ParseFromString(dbstring)

        self.status = res.status
        if self.status != 0:
            raise Exception("Select upgrade level info failde[status=%d]" % res.status)

        #assert len(res.result) == self._query_len

        for result in res.result:
            if result.table.name == "user":
                self._parse_user(result)
            elif result.table.name == "hero":
                self._parse_hero(result)
            elif result.table.name == "item":
                self._parse_item(result)
            elif result.table.name == "resource":
                self._parse_resource(result)
            elif result.table.name == "soldier":
                self._parse_soldier(result)
            elif result.table.name == "pve":
                self._parse_pve(result)
            elif result.table.name == "city":
                self._parse_city(result)
            elif result.table.name == "technology":
                self._parse_technology(result)
            elif result.table.name == "formation":
                self._parse_formation(result)
            elif result.table.name == "mission":
                self._parse_mission(result)
            elif result.table.name == "building":
                self._parse_building(result)
            elif result.table.name == "battle":
                self._parse_battle(result)
            elif result.table.name == "reward":
                self._parse_reward(result)
            elif result.table.name == "shop":
                self._parse_shop(result)
            elif result.table.name == "player":
                self._parse_player(result)
            elif result.table.name == "expedition":
                self._parse_expedition(result)
            elif result.table.name == "plunder":
                self._parse_plunder(result)
            elif result.table.name == "rival":
                self._parse_rival(result)
            elif result.table.name == "defense":
                self._parse_defense(result)
            elif result.table.name == "arena":
                self._parse_arena(result)
            else:
                raise Exception("Unknown table name[name=%s]" % result.table.name)

        return self


    def _parse_one_search(self, row, info):
        assert len(row.cols) == len(info.__dict__)

        def get_value(type, data):
            if type == Item.INT:
                return int(data)
            elif type == Item.BOOL:
                if data == "1":
                    return True
                else:
                    return False
            elif type == Item.STRING:
                return data
            elif type == Item.FLOAT:
                return float(data)

        for col in row.cols:
            value = get_value(col.type, col.value)
            setattr(info, col.key, value)


    """
    方便填写sql请求的expr字段
    要求数据库里的字段和xxxInfo里名字一样
    要求xxxInfo里的字段必须有默认值，以表示其类型
    """
    def _fill_one_search(self, query, data_info):
        for key in data_info.__dict__:
            expr = query.expr.add()
            expr.key = key
            value = data_info.__dict__[key]
            if (type(value) is types.StringType):
                expr.type = Item.STRING
            else:
                expr.type = Item.INT


    def _fill_one_insert(self, query, data_info):
        for key in data_info.__dict__:
            expr = query.expr.add()
            expr.key = key
            value = data_info.__dict__[key]
            if (type(value) is types.StringType):
                expr.type = Item.STRING
            else:
                expr.type = Item.INT
            expr.value = str(value)


    """注意有更新为空的需求, 此方法有问题，暂不使用"""
    def _fill_one_update(self, query, data_info):
        for key in data_info.__dict__:
            value = data_info.__dict__[key]
            if (type(value) is types.StringType) and len(value) == 0:
                continue
            if (type(value) is not types.StringType) and value == 0:
                continue
            expr = query.expr.add()
            expr.key = "user_id"
            if (type(value) is types.StringType):
                expr.type = Item.STRING
            else:
                expr.type = Item.INT
            expr.value = str(value)
            

    def update(self):
        """进行更新：包括增删改"""
        assert not self._call

        if len(self._req.query) == 0:
            raise Exception("Invalid db-agent request, no query")

        self._call = True

        request = self._req.SerializeToString()
        defer = GlobalObject().remote['db_agent'].callRemote("query", request)
        defer.addCallback(self._parse_update)
        return defer


    def _parse_update(self, dbstring):
        self.now = int(time.time())
        res = DBResponse()
        res.ParseFromString(dbstring)

        assert len(res.result) == self._query_len

        self.status = res.status
        if self.status != 0:
            raise Exception("Select upgrade level info failde[status]" % res.status)

        return self


    def search_player(self, name, region):
        if self._multi_player is None:
            self._multi_player = False
        else:
            self._multi_player = True
        self._pack_search_player(name, region)

    
    def traversal_all_player(self):
        self._multi_player = True
        self._pack_search_player(None, None)


    def _pack_search_player(self, name, region):
        query = self._req.query.add()
        self._query_len += 1

        query.user_id = 0
        query.type = Query.SELECT
        query.table_name = "player"
        if name is not None:
            condition = query.condition.add()
            condition.key = "name"
            condition.type = Item.STRING
            condition.value = name
        if region is not None:
            condition = query.condition.add()
            condition.key = "region"
            condition.type = Item.INT
            condition.value = str(region)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "name"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "password"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "region"
        expr.type = Item.INT


    def _parse_player(self, result):
        assert result.table.name == "player"
        assert self._multi_player is not None
        if len(result.table.rows) == 0:
            return None
        
        if self._multi_player:
            for row in result.table.rows:
                player = data.PlayerInfo(None)
                self.players.append(player)
                self._parse_one_search(row, player)
        else:
            assert len(result.table.rows) == 1
            self.player = data.playerInfo(None)
            self._parse_one_search(result.table.rows[0], self.player)


    def search_user(self, user_id):
        if self._multi_user is None:
            self._multi_user = False
        else:
            self._multi_user = True
        self._pack_search_user(user_id)


    def _pack_search_user(self, user_id):
        """查询用户信息
        根据 user id 查找一个用户的信息
        """
        query = self._req.query.add()
        self._query_len += 1

        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "user"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "name"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "vip_level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "icon_id"
        expr.type = Item.INT


    def _parse_user(self, result):
        """解析用户信息"""
        assert result.table.name == "user"
        assert self._multi_user is not None
        if len(result.table.rows) == 0:
            return None
        
        if self._multi_user:
            for row in result.table.rows:
                user = data.UserInfo(None)
                self.users.append(user)
                self._parse_one_search(row, user)
        else:
            assert len(result.table.rows) == 1
            self.user = data.UserInfo(None)
            self._parse_one_search(result.table.rows[0], self.user)


    def search_resource(self, user_id):
        """查询资源信息
        根据 user id 查找用户的资源情况
        """
        if self._multi_resource is None: 
            self._multi_resource = False
        else:
            self._multi_resource = True
        self._pack_search_resource(user_id)


    def _pack_search_resource(self, user_id):
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "resource"

        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "money"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "food"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "soldier"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "money_output"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "food_output"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "soldier_output"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "money_capacity"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "food_capacity"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "soldier_capacity"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "skill_point"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "skill_point_incr_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "skill_point_ceiling"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "gold"
        expr.type = Item.INT


    def _parse_resource(self, result):
        """解析资源信息"""
        assert result.table.name == "resource"
        assert self._multi_resource is not None
        if len(result.table.rows) == 0:
            return None

        #需要计算资源最新的情况
        from app.core import resource as resource_module
        if self._multi_resource:
            for row in result.table.rows:
                resource = data.ResourceInfo(None, None)
                self.resources.append(resource)
                self._parse_one_search(row, resource)
                resource_module.update_current_resource(resource, self.now)
        else:
            assert len(result.table.rows) == 1
            self.resource = data.ResourceInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.resource)
            resource_module.update_current_resource(self.resource, self.now)


    def search_reward(self, reward_id, user_id):
        if self._multi_reward is None:
            self._multi_reward = False
        else:
            self._multi_reward = True

        self._pack_search_reward(reward_id, user_id)


    def search_all_reward(self, user_id):
        assert self._multi_reward is None
        self._multi_reward = True
        self._pack_search_reward(None, user_id)


    def _pack_search_reward(self, reward_id, user_id):
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "reward"

        if reward_id:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(reward_id)
        if user_id:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "money"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "food"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "gold"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "soldier"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "hero_exp"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "exploit"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "item_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "item_basic_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "item_nums"
        expr.type = Item.STRING


    def _parse_reward(self, result):
        assert result.table.name == "reward"
        if len(result.table.rows) == 0:
            return None

        if self._multi_reward:
            for row in result.table.rows:
                reward = data.RewardInfo(None, None)
                self.rewards.append(reward)
                self._parse_one_search(row, reward)
        else:
            assert len(result.table.rows) == 1
            self.reward = data.RewardInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.reward)


    def search_hero(self, hero_id, user_id):
        """查询英雄信息
        根据 user id 和 hero id 查找该 hero 信息
        """
        if self._multi_hero is None:
            self._multi_hero = False
        else:
            self._multi_hero = True

        self._pack_search_hero(hero_id, user_id)


    def search_hero_with_soldier(self, soldier_id, user_id):
        assert self._multi_hero is None
        self._multi_hero = True
        self._pack_search_hero(None, user_id, soldier_id)


    def search_all_hero(self, user_id):
        assert self._multi_hero is None
        self._multi_hero = True
        self._pack_search_hero(None, user_id)


    def _pack_search_hero(self, hero_id, user_id, soldier_id = None):
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "hero"

        if hero_id is not None:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(hero_id)
        if user_id is not None:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)
        if soldier_id is not None:
            condition = query.condition.add()
            condition.key = "soldier_id"
            condition.type = Item.INT
            condition.value = str(soldier_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "star"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "soldier_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "soldier_basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "soldier_level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "first_skill_id"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "second_skill_id"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "third_skill_id"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "fourth_skill_id"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "battle_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "battle_base_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "battle_soldier_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "battle_skill_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "research_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "interior_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "defense_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "building_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT


    def _parse_hero(self, result):
        """
        解析英雄信息
        """
        assert result.table.name == "hero"
        if len(result.table.rows) == 0:#没有在 DB 中找到
            return None

        if self._multi_hero:
            for row in result.table.rows:
                hero = data.HeroInfo(None, None)
                self.heroes.append(hero)
                self._parse_one_search(row, hero)
        else:
            assert len(result.table.rows) == 1
            self.hero = data.HeroInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.hero)


    def search_city(self, city_id, user_id):
        if self._multi_city is None:
            self._multi_city = False
        else:
            self._multi_city = True

        self._pack_search_city(city_id, user_id)


    def search_all_city(self, user_id):
        assert self._multi_city is None
        self._multi_city = True
        self._pack_search_city(None, user_id)


    def _pack_search_city(self, city_id, user_id):
        """
        查询城市信息
        """
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "city"

        if city_id:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(city_id)
        if user_id:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "name"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "building_num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "building_ids"
        expr.type = Item.STRING


    def _parse_city(self, result):
        """
        解析城市信息
        """
        assert result.table.name == "city"
        if len(result.table.rows) == 0:#没有在 DB 中找到
            return None

        if self._multi_city:
            for row in result.table.rows:
                city = data.CityInfo(None, None)
                self.citys.append(city)
                self._parse_one_search(row, city)
        else:
            assert len(result.table.rows) == 1
            self.city = data.CityInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.city)


    def search_technology(self, technology_id, user_id):
        if self._multi_technology is None:
            self._multi_technology = False
        else:
            self._multi_technology = True

        self._pack_search_technology(technology_id, user_id)


    def search_technology_by_basic_id(self, basic_id, user_id):
        if self._multi_technology is None:
            self._multi_technology = False
        else:
            self._multi_technology = True

        self._pack_search_technology(None, user_id, basic_id = basic_id)


    def search_active_non_battle_technology(self, user_id):
        self._multi_technology = True
        self._pack_search_technology(None, user_id,
                active = True, is_for_battle = False)


    def search_active_battle_technology(self, user_id):
        self._multi_technology = True
        self._pack_search_technology(None, user_id,
                active = True, is_for_battle = True)


    def search_active_technology(self, user_id):
        self._multi_technology = True
        self._pack_search_technology(None, user_id, active = True)


    def search_all_technology(self, user_id):
        assert self._multi_technology is None
        self._multi_technology = True
        self._pack_search_technology(None, user_id)


    def _pack_search_technology(self, technology_id, user_id,
            basic_id = None, active = None, is_for_battle = None):
        """
        查询城市信息
        """
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "technology"

        if technology_id is not None:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(technology_id)
        if user_id is not None:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)
        if active is not None:
            condition = query.condition.add()
            condition.key = "active"
            condition.type = Item.BOOL
            condition.value = str(active)
        if is_for_battle is not None:
            condition = query.condition.add()
            condition.key = "is_for_battle"
            condition.type = Item.BOOL
            condition.value = str(is_for_battle)
        if basic_id is not None:
            condition = query.condition.add()
            condition.key = "basic_id"
            condition.type = Item.INT
            condition.value = str(basic_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "active"
        expr.type = Item.BOOL
        expr = query.expr.add()
        expr.key = "is_for_battle"
        expr.type = Item.BOOL
        expr = query.expr.add()
        expr.key = "is_upgrade"
        expr.type = Item.BOOL
        expr = query.expr.add()
        expr.key = "building_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "upgrade_start_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "upgrade_consume_time"
        expr.type = Item.INT


    def _parse_technology(self, result):
        """
        解析城市信息
        """
        assert result.table.name == "technology"
        if len(result.table.rows) == 0:#没有在 DB 中找到
            return None

        if self._multi_technology:
            for row in result.table.rows:
                technology = data.TechnologyInfo(None, None)
                self.technologys.append(technology)
                self._parse_one_search(row, technology)
        else:
            assert len(result.table.rows) == 1
            self.technology = data.TechnologyInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.technology)


    def search_item(self, hero_id, user_id):
        if self._multi_item is None:
            self._multi_item = False
        else:
            self._multi_item = True

        self._pack_search_item(hero_id, user_id)


    def search_all_item(self, user_id):
        assert self._multi_item is None
        self._multi_item = True
        self._pack_search_item(None, user_id)


    def _pack_search_item(self, item_id, user_id):
        """
        查询物品信息
        """
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "item"

        if item_id:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(item_id)
        if user_id:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "used_num"
        expr.type = Item.INT


    def _parse_item(self, result):
        """
        解析物品信息
        """
        assert result.table.name == "item"
        if len(result.table.rows) == 0:#没有在 DB 中找到
            return None

        if self._multi_item:
            for row in result.table.rows:
                item = data.ItemInfo(None, None)
                self.items.append(item)
                self._parse_one_search(row, item)
        else:
            assert len(result.table.rows) == 1
            self.item = data.ItemInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.item)


    def search_battle(self, user_id):
        self._pack_search_battle(user_id)


    def _pack_search_battle(self, user_id):
        """
        查询战斗信息
        """
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "battle"

        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "type"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "info"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "money"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "food"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "hero_exp"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "exploit"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "item_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "item_basic_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "item_nums"
        expr.type = Item.STRING


    def _parse_battle(self, result):
        """
        解析战斗信息
        """
        assert result.table.name == "battle"
        if len(result.table.rows) == 0:
            return None

        assert len(result.table.rows) == 1
        row = result.table.rows[0]
        self.battle = data.BattleInfo(None)
        self._parse_one_search(row, self.battle)


    def search_shop(self, user_id):
        self._pack_search_shop(user_id)


    def _pack_search_shop(self, user_id):
        """
        查询酒肆信息
        """
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "shop"

        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "goods_refresh_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "goods_refresh_num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "money_goods_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "money_goods_status"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "gold_goods_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "gold_goods_status"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "money_draw_free_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "money_draw_free_num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "gold_draw_free_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "gold_draw_free_num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT


    def _parse_shop(self, result):
        """
        解析酒肆信息
        """
        assert result.table.name == "shop"
        if len(result.table.rows) == 0:
            return None

        assert len(result.table.rows) == 1
        row = result.table.rows[0]
        self.shop = data.ShopInfo(None)
        self._parse_one_search(row, self.shop)


    def search_all_formation(self, user_id):
        assert self._multi_formation is None
        self._multi_formation = True
        self._pack_search_formation(None, user_id)


    def search_formation(self, formation_id, user_id):
        if self._multi_formation is None:
            self._multi_formation = False
        else:
            self._multi_formation = True

        self._pack_search_formation(formation_id, user_id)


    def _pack_search_formation(self, formation_id, user_id):
        """
        查询阵型信息
        """
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "formation"

        if formation_id is not None:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(formation_id)
        if user_id is not None:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT


    def _parse_formation(self, result):
        """
        解析阵型信息
        """
        assert result.table.name == "formation"
        if len(result.table.rows) == 0:#没有在 DB 中找到
            return None

        if self._multi_formation:
            for row in result.table.rows:
                formation = data.FormationInfo(None, None)
                self.formations.append(formation)
                self._parse_one_search(row, formation)
        else:
            assert len(result.table.rows) == 1
            self.formation = data.FormationInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.formation)


    def search_soldier(self, soldier_id, user_id):
        if self._multi_soldier is None:
            self._multi_soldier = False
        else:
            self._multi_soldier = True

        self._pack_search_soldier(soldier_id, user_id)


    def search_all_soldier(self, user_id):
        assert self._multi_soldier is None
        self._multi_soldier = True
        self._pack_search_soldier(None, user_id)


    def _pack_search_soldier(self, soldier_id, user_id):
        #查询兵种信息
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "soldier"

        if soldier_id:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(soldier_id)
        if user_id:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "battle_score"
        expr.type = Item.INT


    def _parse_soldier(self, result):
        """解析兵种信息"""
        assert result.table.name == "soldier"
        if len(result.table.rows) == 0:#没有在 DB 中找到
            return None

        if self._multi_soldier:
            for row in result.table.rows:
                soldier = data.SoldierInfo(None, None)
                self.soldiers.append(soldier)
                self._parse_one_search(row, soldier)
        else:
            assert len(result.table.rows) == 1
            self.soldier = data.SoldierInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.soldier)


    def search_building(self, building_id, user_id):
        if self._multi_building is None:
            self._multi_building = False
        else:
            self._multi_building = True

        self._pack_search_building(building_id, user_id, None)


    def search_building_by_type(self, basic_id, user_id):
        self._multi_building = True
        self._pack_search_building(None, user_id, basic_id)


    def search_all_building(self, user_id):
        assert self._multi_building is None
        self._multi_building = True
        self._pack_search_building(None, user_id, None)


    def _pack_search_building(self, building_id, user_id, basic_id):
        #查询建筑信息
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "building"

        if building_id:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(building_id)
        if user_id:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)
        if basic_id:
            condition = query.condition.add()
            condition.key = "basic_id"
            condition.type = Item.INT
            condition.value = str(basic_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "garrison_num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "hero_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "is_upgrade"
        expr.type = Item.BOOL
        expr = query.expr.add()
        expr.key = "upgrade_start_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "upgrade_consume_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "value"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "city_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "slot_index"
        expr.type = Item.INT


    def _parse_building(self, result):
        #解析建筑信息
        assert result.table.name == "building"
        if len(result.table.rows) == 0:#没有在 DB 中找到
            return None

        if self._multi_building:
            for row in result.table.rows:
                building = data.BuildingInfo(None, None)
                self.buildings.append(building)
                self._parse_one_search(row, building)
        else:
            assert len(result.table.rows) == 1
            self.building = data.BuildingInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.building)


    def search_all_pve(self, user_id):
        """查询一个用户的所有 pve 信息"""
        assert self._multi_pve is None
        self._multi_pve = True
        self._pack_search_pve(None, user_id)

    def search_pve(self, pve_id, user_id):
        """查询 pve 信息
        多次调用，相当于查询多条信息
        """
        if self._multi_pve is None:
            self._multi_pve = False
        else:
            self._multi_pve = True

        self._pack_search_pve(pve_id, user_id)

    def _pack_search_pve(self, pve_id, user_id):
        self._query_len += 1

        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "pve"

        if pve_id:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(pve_id)
        if user_id:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "is_open"
        expr.type = Item.BOOL
        expr = query.expr.add()
        expr.key = "finish_status"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "finish_num"
        expr.type = Item.STRING

    def _parse_pve(self, result):
        """
        解析pve信息
        """
        assert result.table.name == "pve"
        assert self._multi_pve is not None

        if len(result.table.rows) == 0:
            return None

        if self._multi_pve:
            for row in result.table.rows:
                pve = data.PVEInfo(None, None)
                self.pves.append(pve)
                self._parse_one_search(row, pve)
        else:
            assert len(result.table.rows) == 1
            self.pve = data.PVEInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.pve)


    def search_all_expedition_rival(self, user_id):
        for level_id in range(const_value.expedition_level_num):
            id = ((user_id << 32) | (1 << 16) | (level_id))
            self.search_rival(id)


    def search_all_plunder_rival(self, user_id):
        for level_id in range(const_value.plunder_level_num):
            id = ((user_id << 32) | (2 << 16) | (level_id))
            self.search_rival(id)


    def search_all_arena_rival(self, user_id):
        for level_id in range(const_value.arena_level_num):
            id = ((user_id << 32) | (3 << 16) | (level_id))
            self.search_rival(id)


    def search_rival(self, id):
        if self._multi_rival is None:
            self._multi_rival = False
        else:
            self._multi_rival = True
        self._pack_search_rival(id)


    def _pack_search_rival(self, id):
        self._query_len += 1
        query = self._req.query.add()
        query.user_id = (id >> 32)
        query.type = Query.SELECT
        query.table_name = "rival"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(id)
        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "rival_user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "rival_defense_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "rival_ranking"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "rival_level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "rival_name"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "formation_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "hero_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "hero_levels"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "hero_stars"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "hero_skill_levels"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "hero_soldier_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "hero_soldier_levels"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "reward_food"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "reward_money"
        expr.type = Item.INT


    def _parse_rival(self, result):
        assert result.table.name == "rival"
        assert self._multi_rival is not None
        if len(result.table.rows) == 0:
            return None
        if self._multi_rival:
            for row in result.table.rows:
                pvp_rival = data.PVPRivalInfo(None, None)
                self.rivals.append(pvp_rival)
                self._parse_one_search(row, pvp_rival)
        else:
            assert len(result.table.rows) == 1
            self.rival = data.PVPRivalInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.rival)
   

    def insert_rival(self, rival):
        self._query_len += 1
        self.rival = rival
        query = self._req.query.add()
        query.user_id = rival.user_id
        query.type = Query.INSERT
        query.table_name = "rival"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(rival.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(rival.user_id)
        expr = query.expr.add()
        expr.key = "rival_user_id"
        expr.type = Item.INT
        expr.value = str(rival.rival_user_id)
        expr = query.expr.add()
        expr.key = "rival_defense_id"
        expr.type = Item.INT
        expr.value = str(rival.rival_defense_id)
        expr = query.expr.add()
        expr.key = "rival_ranking"
        expr.type = Item.INT
        expr.value = str(rival.rival_ranking)
        expr = query.expr.add()
        expr.key = "rival_level"
        expr.type = Item.INT
        expr.value = str(rival.rival_level)
        expr = query.expr.add()
        expr.key = "rival_name"
        expr.type = Item.STRING
        expr.value = str(rival.rival_name)
        expr = query.expr.add()
        expr.key = "formation_id"
        expr.type = Item.INT
        expr.value = str(rival.formation_id)
        expr = query.expr.add()
        expr.key = "hero_ids"
        expr.type = Item.STRING
        expr.value = str(rival.hero_ids)
        expr = query.expr.add()
        expr.key = "hero_levels"
        expr.type = Item.STRING
        expr.value = str(rival.hero_levels)
        expr = query.expr.add()
        expr.key = "hero_stars"
        expr.type = Item.STRING
        expr.value = str(rival.hero_stars)
        expr = query.expr.add()
        expr.key = "hero_skill_levels"
        expr.type = Item.STRING
        expr.value = str(rival.hero_skill_levels)
        expr = query.expr.add()
        expr.key = "hero_soldier_ids"
        expr.type = Item.STRING
        expr.value = str(rival.hero_soldier_ids)
        expr = query.expr.add()
        expr.key = "hero_soldier_levels"
        expr.type = Item.STRING
        expr.value = str(rival.hero_soldier_levels)
        expr = query.expr.add()
        expr.key = "reward_food"
        expr.type = Item.INT
        expr.value = str(rival.reward_food)
        expr = query.expr.add()
        expr.key = "reward_money"
        expr.type = Item.INT
        expr.value = str(rival.reward_money)


    def update_rival(self, rival):
        self._query_len += 1
        self.rival = rival

        query = self._req.query.add()
        query.user_id = rival.user_id
        query.type = Query.UPDATE
        query.table_name = "rival"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(rival.id)
        if rival.user_id is not None:
            expr = query.expr.add()
            expr.key = "user_id"
            expr.type = Item.INT
            expr.value = str(rival.user_id)
        if rival.rival_user_id is not None:
            expr = query.expr.add()
            expr.key = "rival_user_id"
            expr.type = Item.INT
            expr.value = str(rival.rival_user_id)
        if rival.rival_defense_id is not None:
            expr = query.expr.add()
            expr.key = "rival_defense_id"
            expr.type = Item.INT
            expr.value = str(rival.rival_defense_id)
        if rival.rival_ranking is not None:
            expr = query.expr.add()
            expr.key = "rival_ranking"
            expr.type = Item.INT
            expr.value = str(rival.rival_ranking)
        if rival.rival_level is not None:
            expr = query.expr.add()
            expr.key = "rival_level"
            expr.type = Item.INT
            expr.value = str(rival.rival_level)
        if rival.rival_name is not None:
            expr = query.expr.add()
            expr.key = "rival_name"
            expr.type = Item.STRING
            expr.value = str(rival.rival_name)
        if rival.formation_id is not None:
            expr = query.expr.add()
            expr.key = "formation_id"
            expr.type = Item.INT
            expr.value = str(rival.formation_id)
        if rival.hero_ids is not None:
            expr = query.expr.add()
            expr.key = "hero_ids"
            expr.type = Item.STRING
            expr.value = str(rival.hero_ids)
        if rival.hero_levels is not None:
            expr = query.expr.add()
            expr.key = "hero_levels"
            expr.type = Item.STRING
            expr.value = str(rival.hero_levels)
        if rival.hero_stars is not None:
            expr = query.expr.add()
            expr.key = "hero_stars"
            expr.type = Item.STRING
            expr.value = str(rival.hero_stars)
        if rival.hero_skill_levels is not None:
            expr = query.expr.add()
            expr.key = "hero_skill_levels"
            expr.type = Item.STRING
            expr.value = str(rival.hero_skill_levels)
        if rival.hero_soldier_ids is not None:
            expr = query.expr.add()
            expr.key = "hero_soldier_ids"
            expr.type = Item.STRING
            expr.value = str(rival.hero_soldier_ids)
        if rival.hero_soldier_levels is not None:
            expr = query.expr.add()
            expr.key = "hero_soldier_levels"
            expr.type = Item.STRING
            expr.value = str(rival.hero_soldier_levels)
        if rival.reward_food is not None:
            expr = query.expr.add()
            expr.key = "reward_food"
            expr.type = Item.INT
            expr.value = str(rival.reward_food)
        if rival.reward_money is not None:
            expr = query.expr.add()
            expr.key = "reward_money"
            expr.type = Item.INT
            expr.value = str(rival.reward_money)


    def search_expedition(self, user_id):
        """查询远征信息"""
        if self._multi_expedition is None:
            self._multi_expedition = False
        else:
            self._multi_expedition = True
        self._pack_search_expedition(user_id)

    def _pack_search_expedition(self, user_id):
        self._query_len += 1
        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "expedition"
        
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "level_results"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "level_rival_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "reset_num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "reset_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "surviving_hero_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "dead_hero_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "attack_team"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "attack_formation_id"
        expr.type = Item.INT

    def _parse_expedition(self, result):
        assert result.table.name == "expedition"
        assert self._multi_expedition is not None
        if len(result.table.rows) == 0:
            return None

        if self._multi_expedition:
            for row in result.table.rows:
                pvp_expedition = data.PVPExpeditionInfo(None, None)
                self.expeditions.append(pvp_expedition)
                self._parse_one_search(row, pvp_expedition)
        else:
            assert len(result.table.rows) == 1
            self.expedition = data.PVPExpeditionInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.expedition)
    

    def insert_expedition(self, expedition):
        self._query_len += 1
        self.expedition = expedition

        query = self._req.query.add()
        query.user_id = expedition.user_id
        query.type = Query.INSERT
        query.table_name = "expedition"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(expedition.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(expedition.user_id)
        expr = query.expr.add()
        expr.key = "level_results"
        expr.type = Item.STRING
        expr.value = expedition.level_results
        expr = query.expr.add()
        expr.key = "level_rival_ids"
        expr.type = Item.STRING
        expr.value = expedition.level_rival_ids
        expr = query.expr.add()
        expr.key = "reset_num"
        expr.type = Item.INT
        expr.value = str(expedition.reset_num)
        expr = query.expr.add()
        expr.key = "reset_time"
        expr.type = Item.INT
        expr.value = str(expedition.reset_time)
        expr = query.expr.add()
        expr.key = "surviving_hero_ids"
        expr.type = Item.STRING
        expr.value = expedition.surviving_hero_ids
        expr = query.expr.add()
        expr.key = "dead_hero_ids"
        expr.type = Item.STRING
        expr.value = expedition.dead_hero_ids
        expr = query.expr.add()
        expr.key = "attack_team"
        expr.type = Item.STRING
        expr.value = expedition.attack_team
        expr = query.expr.add()
        expr.key = "attack_formation_id"
        expr.type = Item.INT
        expr.value = str(expedition.attack_formation_id)


    def update_expedition(self, expedition):
        self._query_len += 1
        self.expedition = expedition

        query = self._req.query.add()
        query.user_id = expedition.user_id
        query.type = Query.UPDATE
        query.table_name = "expedition"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(expedition.id)
        if expedition.user_id is not None:
            expr = query.expr.add()
            expr.key = "user_id"
            expr.type = Item.INT
            expr.value = str(expedition.user_id)
        if expedition.level_results is not None:
            expr = query.expr.add()
            expr.key = "level_results"
            expr.type = Item.STRING
            expr.value = expedition.level_results
        if expedition.level_rival_ids is not None:
            expr = query.expr.add()
            expr.key = "level_rival_ids"
            expr.type = Item.STRING
            expr.value = expedition.level_rival_ids
        if expedition.reset_num is not None:
            expr = query.expr.add()
            expr.key = "reset_num"
            expr.type = Item.INT
            expr.value = str(expedition.reset_num)
        if expedition.reset_time is not None:
            expr = query.expr.add()
            expr.key = "reset_time"
            expr.type = Item.INT
            expr.value = str(expedition.reset_time)
        if expedition.surviving_hero_ids is not None:
            expr = query.expr.add()
            expr.key = "surviving_hero_ids"
            expr.type = Item.STRING
            expr.value = expedition.surviving_hero_ids
        if expedition.dead_hero_ids is not None:
            expr = query.expr.add()
            expr.key = "dead_hero_ids"
            expr.type = Item.STRING
            expr.value = expedition.dead_hero_ids
        if expedition.attack_team is not None:
            expr = query.expr.add()
            expr.key = "attack_team"
            expr.type = Item.STRING
            expr.value = expedition.attack_team
        if expedition.attack_formation_id is not None:
            expr = query.expr.add()
            expr.key = "attack_formation_id"
            expr.type = Item.INT
            expr.value = str(expedition.attack_formation_id)

    def search_plunder(self, user_id):
        """查询掠夺信息"""
        if self._multi_plunder is None:
            self._multi_plunder = False
        else:
            self._multi_plunder = True
        self._pack_search_plunder(user_id)

    def _pack_search_plunder(self, user_id):
        self._query_len += 1
        query = self._req.query.add()
        query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "plunder"
        
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(user_id)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "level_results"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "level_rival_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "attack_team"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "attack_formation_id"
        expr.type = Item.INT

    def _parse_plunder(self, result):
        assert result.table.name == "plunder"
        assert self._multi_plunder is not None
        if len(result.table.rows) == 0:
            return None

        if self._multi_plunder:
            for row in result.table.rows:
                pvp_plunder = data.PVPPlunderInfo(None, None)
                self.plunders.append(pvp_plunder)
                self._parse_one_search(row, pvp_plunder)
        else:
            assert len(result.table.rows) == 1
            self.plunder = data.PVPPlunderInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.plunder)
    

    def insert_plunder(self, plunder):
        self._query_len += 1
        self.plunder = plunder

        query = self._req.query.add()
        query.user_id = plunder.user_id
        query.type = Query.INSERT
        query.table_name = "plunder"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(plunder.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(plunder.user_id)
        expr = query.expr.add()
        expr.key = "level_results"
        expr.type = Item.STRING
        expr.value = plunder.level_results
        expr = query.expr.add()
        expr.key = "level_rival_ids"
        expr.type = Item.STRING
        expr.value = plunder.level_rival_ids
        expr = query.expr.add()
        expr.key = "attack_team"
        expr.type = Item.STRING
        expr.value = plunder.attack_team
        expr = query.expr.add()
        expr.key = "attack_formation_id"
        expr.type = Item.INT
        expr.value = str(plunder.attack_formation_id)


    def update_plunder(self, plunder):
        self._query_len += 1
        self.plunder = plunder

        query = self._req.query.add()
        query.user_id = plunder.user_id
        query.type = Query.UPDATE
        query.table_name = "plunder"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(plunder.id)
        if plunder.user_id is not None:
            expr = query.expr.add()
            expr.key = "user_id"
            expr.type = Item.INT
            expr.value = str(plunder.user_id)
        if plunder.level_results is not None:
            expr = query.expr.add()
            expr.key = "level_results"
            expr.type = Item.STRING
            expr.value = plunder.level_results
        if plunder.level_rival_ids is not None:
            expr = query.expr.add()
            expr.key = "level_rival_ids"
            expr.type = Item.STRING
            expr.value = plunder.level_rival_ids
        if plunder.attack_team is not None:
            expr = query.expr.add()
            expr.key = "attack_team"
            expr.type = Item.STRING
            expr.value = plunder.attack_team
        if plunder.attack_formation_id is not None:
            expr = query.expr.add()
            expr.key = "attack_formation_id"
            expr.type = Item.INT
            expr.value = str(plunder.attack_formation_id)


    def search_arena(self, user_id):
        """查询竞技场信息"""
        if self._multi_arena is None:
            self._multi_arena = False
        else:
            self._multi_arena = True
        self._pack_search_arena(user_id, user_id, None)

    def search_arena_by_ranking(self, calling_user_id, ranking):
        if self._multi_arena is None:
            self._multi_arena = False
        else:
            self._multi_arena = True
        self._pack_search_arena(calling_user_id, None, ranking)

    def _pack_search_arena(self, calling_user_id, user_id, ranking):
        self._query_len += 1
        query = self._req.query.add()
        query.user_id = calling_user_id
        query.type = Query.SELECT
        query.table_name = "arena"
        
        if user_id is not None:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)
        if ranking is not None:
            condition = query.condition.add()
            condition.key = "arena_ranking"
            condition.type = Item.INT
            condition.value = str(ranking)

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "level_rival_ids"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "attack_team"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "attack_formation_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "attack_battle_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "arena_ranking"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "attack_num"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "cd_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "last_fight_time"
        expr.type = Item.INT


    def _parse_arena(self, result):
        assert result.table.name == "arena"
        assert self._multi_arena is not None
        if len(result.table.rows) == 0:
            return None

        from app.core import battle as battle_module
        if self._multi_arena:
            for row in result.table.rows:
                pvp_arena = data.PVPArenaInfo(None, None)
                self.arenas.append(pvp_arena)
                self._parse_one_search(row, pvp_arena)
                battle_module.update_cur_arena(pvp_arena)
        else:
            assert len(result.table.rows) == 1
            self.arena = data.PVPArenaInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.arena)
            battle_module.update_cur_arena(self.arena)
    

    def insert_arena(self, arena):
        self._query_len += 1
        self.arena = arena

        query = self._req.query.add()
        query.user_id = arena.user_id
        query.type = Query.INSERT
        query.table_name = "arena"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(arena.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(arena.user_id)
        expr = query.expr.add()
        expr.key = "level_rival_ids"
        expr.type = Item.STRING
        expr.value = arena.level_rival_ids
        expr = query.expr.add()
        expr.key = "attack_team"
        expr.type = Item.STRING
        expr.value = arena.attack_team
        expr = query.expr.add()
        expr.key = "attack_formation_id"
        expr.type = Item.INT
        expr.value = str(arena.attack_formation_id)
        expr = query.expr.add()
        expr.key = "attack_battle_score"
        expr.type = Item.INT
        expr.value = str(arena.attack_battle_score)
        expr = query.expr.add()
        expr.key = "arena_ranking"
        expr.type = Item.INT
        expr.value = str(arena.arena_ranking)
        expr = query.expr.add()
        expr.key = "attack_num"
        expr.type = Item.INT
        expr.value = str(arena.attack_num)
        expr = query.expr.add()
        expr.key = "cd_time"
        expr.type = Item.INT
        expr.value = str(arena.cd_time)
        expr = query.expr.add()
        expr.key = "last_fight_time"
        expr.type = Item.INT
        expr.value = str(arena.last_fight_time)


    def update_arena(self, arena):
        self._query_len += 1
        self.arena = arena

        query = self._req.query.add()
        query.user_id = arena.user_id
        query.type = Query.UPDATE
        query.table_name = "arena"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(arena.id)
        if arena.user_id is not None:
            expr = query.expr.add()
            expr.key = "user_id"
            expr.type = Item.INT
            expr.value = str(arena.user_id)
        if arena.level_rival_ids is not None:
            expr = query.expr.add()
            expr.key = "level_rival_ids"
            expr.type = Item.STRING
            expr.value = arena.level_rival_ids
        if arena.attack_team is not None:
            expr = query.expr.add()
            expr.key = "attack_team"
            expr.type = Item.STRING
            expr.value = arena.attack_team
        if arena.attack_formation_id is not None:
            expr = query.expr.add()
            expr.key = "attack_formation_id"
            expr.type = Item.INT
            expr.value = str(arena.attack_formation_id)
        if arena.attack_battle_score is not None:
            expr = query.expr.add()
            expr.key = "attack_battle_score"
            expr.type = Item.INT
            expr.value = str(arena.attack_battle_score)
        if arena.arena_ranking is not None:
            expr = query.expr.add()
            expr.key = "arena_ranking"
            expr.type = Item.INT
            expr.value = str(arena.arena_ranking)
        if arena.attack_num is not None:    
            expr = query.expr.add()
            expr.key = "attack_num"
            expr.type = Item.INT
            expr.value = str(arena.attack_num)
        if arena.cd_time is not None:
            expr = query.expr.add()
            expr.key = "cd_time"
            expr.type = Item.INT
            expr.value = str(arena.cd_time)
        if arena.last_fight_time is not None:
            expr = query.expr.add()
            expr.key = "last_fight_time"
            expr.type = Item.INT
            expr.value = str(arena.last_fight_time)


    def insert_user(self, user):
        self._query_len += 1
        self.user = user

        query = self._req.query.add()
        query.user_id = user.id
        query.type = Query.INSERT
        query.table_name = "user"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(user.id)
        expr = query.expr.add()
        expr.key = "name"
        expr.type = Item.STRING
        expr.value = user.name
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr.value = str(user.level)
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr.value = str(user.exp)
        expr = query.expr.add()
        expr.key = "vip_level"
        expr.type = Item.INT
        expr.value = str(user.vip_level)
        expr = query.expr.add()
        expr.key = "icon_id"
        expr.type = Item.INT
        expr.value = str(user.icon_id)


    def update_user(self, user):
        self._query_len += 1
        self.user = user

        query = self._req.query.add()
        query.user_id = user.id
        query.type = Query.UPDATE
        query.table_name = "user"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(user.id)
        if user.name is not None:
            expr = query.expr.add()
            expr.key = "name"
            expr.type = Item.STRING
            expr.value = user.name
        if user.level is not None:
            expr = query.expr.add()
            expr.key = "level"
            expr.type = Item.INT
            expr.value = str(user.level)
        if user.exp is not None:
            expr = query.expr.add()
            expr.key = "exp"
            expr.type = Item.INT
            expr.value = str(user.exp)
        if user.vip_level is not None:
            expr = query.expr.add()
            expr.key = "vip_level"
            expr.type = Item.INT
            expr.value = str(user.vip_level)
        if user.icon_id is not None:
            expr = query.expr.add()
            expr.key = "icon_id"
            expr.type = Item.INT
            expr.value = str(user.icon_id)


    def insert_resource(self, resource):
        self._query_len += 1
        self.resource = resource

        query = self._req.query.add()
        query.user_id = resource.user_id
        query.type = Query.INSERT
        query.table_name = "resource"

        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(resource.user_id)
        expr = query.expr.add()
        expr.key = "money"
        expr.type = Item.INT
        expr.value = str(resource.money)
        expr = query.expr.add()
        expr.key = "food"
        expr.type = Item.INT
        expr.value = str(resource.food)
        expr = query.expr.add()
        expr.key = "soldier"
        expr.type = Item.INT
        expr.value = str(resource.soldier)
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT
        expr.value = str(resource.update_time)
        expr = query.expr.add()
        expr.key = "money_output"
        expr.type = Item.INT
        expr.value = str(resource.money_output)
        expr = query.expr.add()
        expr.key = "food_output"
        expr.type = Item.INT
        expr.value = str(resource.food_output)
        expr = query.expr.add()
        expr.key = "soldier_output"
        expr.type = Item.INT
        expr.value = str(resource.soldier_output)
        expr = query.expr.add()
        expr.key = "money_capacity"
        expr.type = Item.INT
        expr.value = str(resource.money_capacity)
        expr = query.expr.add()
        expr.key = "food_capacity"
        expr.type = Item.INT
        expr.value = str(resource.food_capacity)
        expr = query.expr.add()
        expr.key = "soldier_capacity"
        expr.type = Item.INT
        expr.value = str(resource.soldier_capacity)
        expr = query.expr.add()
        expr.key = "skill_point"
        expr.type = Item.INT
        expr.value = str(resource.skill_point)
        expr = query.expr.add()
        expr.key = "skill_point_incr_time"
        expr.type = Item.INT
        expr.value = str(resource.skill_point_incr_time)
        expr = query.expr.add()
        expr.key = "skill_point_ceiling"
        expr.type = Item.INT
        expr.value = str(resource.skill_point_ceiling)
        expr = query.expr.add()
        expr.key = "gold"
        expr.type = Item.INT
        expr.value = str(resource.gold)


    def update_resource(self, resource):
        self._query_len += 1
        self.resource = resource

        query = self._req.query.add()
        query.user_id = resource.user_id
        query.type = Query.UPDATE
        query.table_name = "resource"
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(resource.user_id)

        if resource.money is not None:
            expr = query.expr.add()
            expr.key = "money"
            expr.type = Item.INT
            expr.value = str(resource.money)
        if resource.food is not None:
            expr = query.expr.add()
            expr.key = "food"
            expr.type = Item.INT
            expr.value = str(resource.food)
        if resource.soldier is not None:
            expr = query.expr.add()
            expr.key = "soldier"
            expr.type = Item.INT
            expr.value = str(resource.soldier)
        if resource.update_time is not None:
            expr = query.expr.add()
            expr.key = "update_time"
            expr.type = Item.INT
            expr.value = str(resource.update_time)
        if resource.money_output is not None:
            expr = query.expr.add()
            expr.key = "money_output"
            expr.type = Item.INT
            expr.value = str(resource.money_output)
        if resource.food_output is not None:
            expr = query.expr.add()
            expr.key = "food_output"
            expr.type = Item.INT
            expr.value = str(resource.food_output)
        if resource.soldier_output is not None:
            expr = query.expr.add()
            expr.key = "soldier_output"
            expr.type = Item.INT
            expr.value = str(resource.soldier_output)
        if resource.money_capacity is not None:
            expr = query.expr.add()
            expr.key = "money_capacity"
            expr.type = Item.INT
            expr.value = str(resource.money_capacity)
        if resource.food_capacity is not None:
            expr = query.expr.add()
            expr.key = "food_capacity"
            expr.type = Item.INT
            expr.value = str(resource.food_capacity)
        if resource.soldier_capacity is not None:
            expr = query.expr.add()
            expr.key = "soldier_capacity"
            expr.type = Item.INT
            expr.value = str(resource.soldier_capacity)
        if resource.skill_point is not None:
            expr = query.expr.add()
            expr.key = "skill_point"
            expr.type = Item.INT
            expr.value = str(resource.skill_point)
        if resource.skill_point_incr_time is not None:
            expr = query.expr.add()
            expr.key = "skill_point_incr_time"
            expr.type = Item.INT
            expr.value = str(resource.skill_point_incr_time)
        if resource.skill_point_ceiling is not None:
            expr = query.expr.add()
            expr.key = "skill_point_ceiling"
            expr.type = Item.INT
            expr.value = str(resource.skill_point_ceiling)
        if resource.gold is not None:
            expr = query.expr.add()
            expr.key = "gold"
            expr.type = Item.INT
            expr.value = str(resource.gold)


    def insert_battle(self, battle):
        self._query_len += 1
        self.battle = battle

        query = self._req.query.add()
        query.user_id = battle.user_id
        query.type = Query.INSERT
        query.table_name = "battle"

        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(battle.user_id)
        expr = query.expr.add()
        expr.key = "type"
        expr.type = Item.INT
        expr.value = str(battle.type)
        expr = query.expr.add()
        expr.key = "info"
        expr.type = Item.STRING
        expr.value = str(battle.info)
        expr = query.expr.add()
        expr.key = "money"
        expr.type = Item.INT
        expr.value = str(battle.money)
        expr = query.expr.add()
        expr.key = "food"
        expr.type = Item.INT
        expr.value = str(battle.food)
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr.value = str(battle.exp)
        expr = query.expr.add()
        expr.key = "hero_exp"
        expr.type = Item.INT
        expr.value = str(battle.hero_exp)
        expr = query.expr.add()
        expr.key = "exploit"
        expr.type = Item.INT
        expr.value = str(battle.exploit)
        expr = query.expr.add()
        expr.key = "item_ids"
        expr.type = Item.STRING
        expr.value = str(battle.item_ids)
        expr = query.expr.add()
        expr.key = "item_basic_ids"
        expr.type = Item.STRING
        expr.value = str(battle.item_basic_ids)
        expr = query.expr.add()
        expr.key = "item_nums"
        expr.type = Item.STRING
        expr.value = str(battle.item_nums)


    def delete_battle(self, battle):
        self._query_len += 1
        self.battle = battle

        query = self._req.query.add()
        query.user_id = battle.user_id
        query.type = Query.DELETE
        query.table_name = "battle"
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(battle.user_id)


    def update_battle(self, battle):
        self._query_len += 1
        self.battle = battle

        query = self._req.query.add()
        query.user_id = battle.user_id
        query.type = Query.UPDATE
        query.table_name = "battle"
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(battle.user_id)

        if battle.type is not None:
            expr = query.expr.add()
            expr.key = "type"
            expr.type = Item.INT
            expr.value = str(battle.type)
        if battle.info is not None:
            expr = query.expr.add()
            expr.key = "info"
            expr.type = Item.STRING
            expr.value = str(battle.info)
        if battle.money is not None:
            expr = query.expr.add()
            expr.key = "money"
            expr.type = Item.INT
            expr.value = str(battle.money)
        if battle.food is not None:
            expr = query.expr.add()
            expr.key = "food"
            expr.type = Item.INT
            expr.value = str(battle.food)
        if battle.exp is not None:
            expr = query.expr.add()
            expr.key = "exp"
            expr.type = Item.INT
            expr.value = str(battle.exp)
        if battle.hero_exp is not None:
            expr = query.expr.add()
            expr.key = "hero_exp"
            expr.type = Item.INT
            expr.value = str(battle.hero_exp)
        if battle.exploit is not None:
            expr = query.expr.add()
            expr.key = "exploit"
            expr.type = Item.INT
            expr.value = str(battle.exploit)
        if battle.item_ids is not None:
            expr = query.expr.add()
            expr.key = "item_ids"
            expr.type = Item.STRING
            expr.value = str(battle.item_ids)
        if battle.item_basic_ids is not None:
            expr = query.expr.add()
            expr.key = "item_basic_ids"
            expr.type = Item.STRING
            expr.value = str(battle.item_basic_ids)
        if battle.item_nums is not None:
            expr = query.expr.add()
            expr.key = "item_nums"
            expr.type = Item.STRING
            expr.value = str(battle.item_nums)


    def insert_shop(self, shop):
        """
        插入酒肆信息
        """
        self._query_len += 1
        self.shop = shop

        query = self._req.query.add()
        query.user_id = shop.user_id
        query.type = Query.INSERT
        query.table_name = "shop"

        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(shop.user_id)
        expr = query.expr.add()
        expr.key = "goods_refresh_time"
        expr.type = Item.INT
        expr.value = str(shop.goods_refresh_time)
        expr = query.expr.add()
        expr.key = "goods_refresh_num"
        expr.type = Item.INT
        expr.value = str(shop.goods_refresh_num)
        expr = query.expr.add()
        expr.key = "money_goods_ids"
        expr.type = Item.STRING
        expr.value = shop.money_goods_ids
        expr = query.expr.add()
        expr.key = "money_goods_status"
        expr.type = Item.STRING
        expr.value = shop.money_goods_status
        expr = query.expr.add()
        expr.key = "gold_goods_ids"
        expr.type = Item.STRING
        expr.value = shop.gold_goods_ids
        expr = query.expr.add()
        expr.key = "gold_goods_status"
        expr.type = Item.STRING
        expr.value = shop.gold_goods_status
        expr = query.expr.add()
        expr.key = "money_draw_free_time"
        expr.type = Item.INT
        expr.value = str(shop.money_draw_free_time)
        expr = query.expr.add()
        expr.key = "money_draw_free_num"
        expr.type = Item.INT
        expr.value = str(shop.money_draw_free_num)
        expr = query.expr.add()
        expr.key = "gold_draw_free_time"
        expr.type = Item.INT
        expr.value = str(shop.gold_draw_free_time)
        expr = query.expr.add()
        expr.key = "gold_draw_free_num"
        expr.type = Item.INT
        expr.value = str(shop.gold_draw_free_num)
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT
        expr.value = str(shop.update_time)


    def update_shop(self, shop):
        """
        更新酒肆信息
        """
        self._query_len += 1
        self.shop = shop

        query = self._req.query.add()
        query.user_id = shop.user_id
        query.type = Query.UPDATE
        query.table_name = "shop"

        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(shop.user_id)

        expr = query.expr.add()
        expr.key = "goods_refresh_time"
        expr.type = Item.INT
        expr.value = str(shop.goods_refresh_time)
        expr = query.expr.add()
        expr.key = "goods_refresh_num"
        expr.type = Item.INT
        expr.value = str(shop.goods_refresh_num)
        expr = query.expr.add()
        expr.key = "money_goods_ids"
        expr.type = Item.STRING
        expr.value = shop.money_goods_ids
        expr = query.expr.add()
        expr.key = "money_goods_status"
        expr.type = Item.STRING
        expr.value = shop.money_goods_status
        expr = query.expr.add()
        expr.key = "gold_goods_ids"
        expr.type = Item.STRING
        expr.value = shop.gold_goods_ids
        expr = query.expr.add()
        expr.key = "gold_goods_status"
        expr.type = Item.STRING
        expr.value = shop.gold_goods_status
        expr = query.expr.add()
        expr.key = "money_draw_free_time"
        expr.type = Item.INT
        expr.value = str(shop.money_draw_free_time)
        expr = query.expr.add()
        expr.key = "money_draw_free_num"
        expr.type = Item.INT
        expr.value = str(shop.money_draw_free_num)
        expr = query.expr.add()
        expr.key = "gold_draw_free_time"
        expr.type = Item.INT
        expr.value = str(shop.gold_draw_free_time)
        expr = query.expr.add()
        expr.key = "gold_draw_free_num"
        expr.type = Item.INT
        expr.value = str(shop.gold_draw_free_num)
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT
        expr.value = str(shop.update_time)


    def insert_reward(self, reward):
        self._query_len += 1
        if self._multi_reward is None:
            self._multi_reward = False
            self.reward = reward
        elif not self._multi_reward:
            self._multi_reward = True
            self.rewards.append(self.reward)
            self.reward = None
        else:
            self.rewards.append(reward)

        query = self._req.query.add()
        query.user_id = reward.user_id
        query.type = Query.INSERT
        query.table_name = "reward"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(reward.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(reward.user_id)
        expr = query.expr.add()
        expr.key = "money"
        expr.type = Item.INT
        expr.value = str(reward.money)
        expr = query.expr.add()
        expr.key = "food"
        expr.type = Item.INT
        expr.value = str(reward.food)
        expr = query.expr.add()
        expr.key = "gold"
        expr.type = Item.INT
        expr.value = str(reward.gold)
        from app import pack
        expr = query.expr.add()
        expr.key = "soldier"
        expr.type = Item.INT
        expr.value = str(reward.soldier)
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr.value = str(reward.exp)
        expr = query.expr.add()
        expr.key = "hero_exp"
        expr.type = Item.INT
        expr.value = str(reward.hero_exp)
        expr = query.expr.add()
        expr.key = "exploit"
        expr.type = Item.INT
        expr.value = str(reward.exploit)
        expr = query.expr.add()
        expr.key = "item_ids"
        expr.type = Item.STRING
        expr.value = reward.item_ids
        expr = query.expr.add()
        expr.key = "item_basic_ids"
        expr.type = Item.STRING
        expr.value = reward.item_basic_ids
        expr = query.expr.add()
        expr.key = "item_nums"
        expr.type = Item.STRING
        expr.value = reward.item_nums


    def delete_reward(self, reward):
        self._query_len += 1
        if self._multi_reward is None:
            self._multi_reward = False
            self.reward = reward
        elif not self._multi_reward:
            self._multi_reward = True
            self.rewards.append(self.reward)
            self.reward = None
        else:
            self.rewards.append(reward)

        query = self._req.query.add()
        query.user_id = reward.user_id
        query.type = Query.DELETE
        query.table_name = "reward"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(reward.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(reward.user_id)


    def update_reward(self, reward):
        self._query_len += 1
        if self._multi_reward is None:
            self._multi_reward = False
            self.reward = reward
        elif not self._multi_reward:
            self._multi_reward = True
            self.rewards.append(self.reward)
            self.reward = None
        else:
            self.rewards.append(reward)

        query = self._req.query.add()
        query.user_id = reward.user_id
        query.type = Query.INSERT
        query.table_name = "reward"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(reward.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(reward.user_id)

        expr = query.expr.add()
        expr.key = "money"
        expr.type = Item.INT
        expr.value = str(reward.money)
        expr = query.expr.add()
        expr.key = "food"
        expr.type = Item.INT
        expr.value = str(reward.food)
        expr = query.expr.add()
        expr.key = "gold"
        expr.type = Item.INT
        expr.value = str(reward.gold)
        expr = query.expr.add()
        expr.key = "soldier"
        expr.type = Item.INT
        expr.value = str(reward.soldier)
        expr = query.expr.add()
        expr.key = "soldier"
        expr.type = Item.INT
        expr.value = str(reward.soldier)
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr.value = str(reward.exp)
        expr = query.expr.add()
        expr.key = "hero_exp"
        expr.type = Item.INT
        expr.value = str(reward.hero_exp)
        expr = query.expr.add()
        expr.key = "exploit"
        expr.type = Item.INT
        expr.value = str(reward.exploit)
        expr = query.expr.add()
        expr.key = "item_ids"
        expr.type = Item.STRING
        expr.value = reward.item_ids
        expr = query.expr.add()
        expr.key = "item_basic_ids"
        expr.type = Item.STRING
        expr.value = reward.item_basic_ids
        expr = query.expr.add()
        expr.key = "item_nums"
        expr.type = Item.STRING
        expr.value = reward.item_nums



    def insert_item(self, item):
        self._query_len += 1
        if self._multi_item is None:
            self._multi_item = False
            self.item = item
        elif not self._multi_item:
            self._multi_item = True
            self.items.append(self.item)
            self.item = None
        else:
            self.items.append(item)

        query = self._req.query.add()
        query.user_id = item.user_id
        query.type = Query.INSERT
        query.table_name = "item"
        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(item.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(item.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(item.basic_id)
        expr = query.expr.add()
        expr.key = "num"
        expr.type = Item.INT
        expr.value = str(item.num)
        expr = query.expr.add()
        expr.key = "used_num"
        expr.type = Item.INT
        expr.value = str(item.used_num)

    def update_item(self, item):
        self._query_len += 1
        if self._multi_item is None:
            self._multi_item = False
            self.item = item
        elif not self._multi_item:
            self._multi_item = True
            self.items.append(self.item)
            self.item = None
        else:
            self.items.append(item)

        query = self._req.query.add()
        query.user_id = item.user_id
        query.type = Query.UPDATE
        query.table_name = "item"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(item.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(item.user_id)

        if item.basic_id is not None:
            expr = query.expr.add()
            expr.key = "basic_id"
            expr.type = Item.INT
            expr.value = str(item.basic_id)
        if item.num is not None:
            expr = query.expr.add()
            expr.key = "num"
            expr.type = Item.INT
            expr.value = str(item.num)
        if item.used_num is not None:
            expr = query.expr.add()
            expr.key = "used_num"
            expr.type = Item.INT
            expr.value = str(item.used_num)

    def insert_hero(self, hero):
        self._query_len += 1
        if self._multi_hero is None:
            self._multi_hero = False
            self.hero = hero
        elif not self._multi_hero:
            self._multi_hero = True
            self.heroes.append(self.hero)
            self.hero = None
        else:
            self.heroes.append(hero)

        query = self._req.query.add()
        query.user_id = hero.user_id
        query.type = Query.INSERT
        query.table_name = "hero"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(hero.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(hero.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(hero.basic_id)
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr.value = str(hero.level)
        expr = query.expr.add()
        expr.key = "exp"
        expr.type = Item.INT
        expr.value = str(hero.exp)
        expr = query.expr.add()
        expr.key = "star"
        expr.type = Item.INT
        expr.value = str(hero.star)
        expr = query.expr.add()
        expr.key = "soldier_id"
        expr.type = Item.INT
        expr.value = str(hero.soldier_id)
        expr = query.expr.add()
        expr.key = "soldier_basic_id"
        expr.type = Item.INT
        expr.value = str(hero.soldier_basic_id)
        expr = query.expr.add()
        expr.key = "soldier_level"
        expr.type = Item.INT
        expr.value = str(hero.soldier_level)
        expr = query.expr.add()
        expr.key = "first_skill_id"
        expr.type = Item.STRING
        expr.value = hero.first_skill_id
        expr = query.expr.add()
        expr.key = "second_skill_id"
        expr.type = Item.STRING
        expr.value = hero.second_skill_id
        expr = query.expr.add()
        expr.key = "third_skill_id"
        expr.type = Item.STRING
        expr.value = hero.third_skill_id
        expr = query.expr.add()
        expr.key = "fourth_skill_id"
        expr.type = Item.STRING
        expr.value = hero.fourth_skill_id
        expr = query.expr.add()
        expr.key = "battle_score"
        expr.type = Item.INT
        expr.value = str(hero.battle_score)
        expr = query.expr.add()
        expr.key = "battle_base_score"
        expr.type = Item.INT
        expr.value = str(hero.battle_base_score)
        expr = query.expr.add()
        expr.key = "battle_soldier_score"
        expr.type = Item.INT
        expr.value = str(hero.battle_soldier_score)
        expr = query.expr.add()
        expr.key = "battle_skill_score"
        expr.type = Item.INT
        expr.value = str(hero.battle_skill_score)
        expr = query.expr.add()
        expr.key = "research_score"
        expr.type = Item.INT
        expr.value = str(hero.research_score)
        expr = query.expr.add()
        expr.key = "interior_score"
        expr.type = Item.INT
        expr.value = str(hero.interior_score)
        expr = query.expr.add()
        expr.key = "defense_score"
        expr.type = Item.INT
        expr.value = str(hero.defense_score)
        expr = query.expr.add()
        expr.key = "building_id"
        expr.type = Item.INT
        expr.value = str(hero.building_id)
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT
        expr.value = str(hero.update_time)


    def update_hero(self, hero):
        self._query_len += 1
        if self._multi_hero is None:
            self._multi_hero = False
            self.hero = hero
        elif not self._multi_hero:
            self._multi_hero = True
            self.heroes.append(self.hero)
            self.hero = None
        else:
            self.heroes.append(hero)

        query = self._req.query.add()
        query.user_id = hero.user_id
        query.type = Query.UPDATE
        query.table_name = "hero"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(hero.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(hero.user_id)

        if hero.basic_id is not None:
            expr = query.expr.add()
            expr.key = "basic_id"
            expr.type = Item.INT
            expr.value = str(hero.basic_id)
        if hero.level is not None:
            expr = query.expr.add()
            expr.key = "level"
            expr.type = Item.INT
            expr.value = str(hero.level)
        if hero.exp is not None:
            expr = query.expr.add()
            expr.key = "exp"
            expr.type = Item.INT
            expr.value = str(hero.exp)
        if hero.star is not None:
            expr = query.expr.add()
            expr.key = "star"
            expr.type = Item.INT
            expr.value = str(hero.star)
        if hero.soldier_id is not None:
            expr = query.expr.add()
            expr.key = "soldier_id"
            expr.type = Item.INT
            expr.value = str(hero.soldier_id)
        if hero.soldier_basic_id is not None:
            expr = query.expr.add()
            expr.key = "soldier_basic_id"
            expr.type = Item.INT
            expr.value = str(hero.soldier_basic_id)
        if hero.soldier_level is not None:
            expr = query.expr.add()
            expr.key = "soldier_level"
            expr.type = Item.INT
            expr.value = str(hero.soldier_level)
        if hero.first_skill_id is not None:
            expr = query.expr.add()
            expr.key = "first_skill_id"
            expr.type = Item.STRING
            expr.value = hero.first_skill_id
        if hero.second_skill_id is not None:
            expr = query.expr.add()
            expr.key = "second_skill_id"
            expr.type = Item.STRING
            expr.value = hero.second_skill_id
        if hero.third_skill_id is not None:
            expr = query.expr.add()
            expr.key = "third_skill_id"
            expr.type = Item.STRING
            expr.value = hero.third_skill_id
        if hero.fourth_skill_id is not None:
            expr = query.expr.add()
            expr.key = "fourth_skill_id"
            expr.type = Item.STRING
            expr.value = hero.fourth_skill_id
        if hero.battle_score is not None:
            expr = query.expr.add()
            expr.key = "battle_score"
            expr.type = Item.INT
            expr.value = str(hero.battle_score)
        if hero.battle_base_score is not None:
            expr = query.expr.add()
            expr.key = "battle_base_score"
            expr.type = Item.INT
            expr.value = str(hero.battle_base_score)
        if hero.battle_soldier_score is not None:
            expr = query.expr.add()
            expr.key = "battle_soldier_score"
            expr.type = Item.INT
            expr.value = str(hero.battle_soldier_score)
        if hero.battle_skill_score is not None:
            expr = query.expr.add()
            expr.key = "battle_skill_score"
            expr.type = Item.INT
            expr.value = str(hero.battle_skill_score)
        if hero.research_score is not None:
            expr = query.expr.add()
            expr.key = "research_score"
            expr.type = Item.INT
            expr.value = str(hero.research_score)
        if hero.interior_score is not None:
            expr = query.expr.add()
            expr.key = "interior_score"
            expr.type = Item.INT
            expr.value = str(hero.interior_score)
        if hero.defense_score is not None:
            expr = query.expr.add()
            expr.key = "defense_score"
            expr.type = Item.INT
            expr.value = str(hero.defense_score)
        if hero.building_id is not None:
            expr = query.expr.add()
            expr.key = "building_id"
            expr.type = Item.INT
            expr.value = str(hero.building_id)
        if hero.update_time is not None:
            expr = query.expr.add()
            expr.key = "update_time"
            expr.type = Item.INT
            expr.value = str(hero.update_time)


    def insert_soldier(self, soldier):
        self._query_len += 1
        if self._multi_soldier is None:
            self._multi_soldier = False
            self.soldier = soldier 
        elif not self._multi_soldier:
            self._multi_soldier = True
            self.soldiers.append(self.soldier)
            self.soldier = None
        else:
            self.soldiers.append(soldier)

        query = self._req.query.add()
        query.user_id = soldier.user_id
        query.type = Query.INSERT
        query.table_name = "soldier"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(soldier.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(soldier.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(soldier.basic_id)
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr.value = str(soldier.level)
        expr = query.expr.add()
        expr.key = "battle_score"
        expr.type = Item.INT
        expr.value = str(soldier.battle_score)


    def update_soldier(self, soldier):
        self._query_len += 1
        if self._multi_soldier is None:
            self._multi_soldier = False
            self.soldier = soldier 
        elif not self._multi_soldier:
            self._multi_soldier = True
            self.soldiers.append(self.soldier)
            self.soldier = None
        else:
            self.soldiers.append(soldier)

        self.soldier = soldier
        query = self._req.query.add()
        query.user_id = soldier.user_id
        query.type = Query.UPDATE
        query.table_name = "soldier"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(soldier.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(soldier.user_id)

        if soldier.basic_id is not None:
            expr = query.expr.add()
            expr.key = "basic_id"
            expr.type = Item.INT
            expr.value = str(soldier.basic_id)
        if soldier.level is not None:
            expr = query.expr.add()
            expr.key = "level"
            expr.type = Item.INT
            expr.value = str(soldier.level)
        if soldier.battle_score is not None:
            expr = query.expr.add()
            expr.key = "battle_score"
            expr.type = Item.INT
            expr.value = str(soldier.battle_score)


    def insert_building(self, building):
        self._query_len += 1
        if self._multi_building is None:
            self._multi_building = False
            self.building = building 
        elif not self._multi_building:
            self._multi_building = True
            self.buildings.append(self.building)
            self.building = None
        else:
            self.buildings.append(building)

        query = self._req.query.add()
        query.user_id = building.user_id
        query.type = Query.INSERT
        query.table_name = "building"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(building.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(building.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(building.basic_id)
        expr = query.expr.add()
        expr.key = "level"
        expr.type = Item.INT
        expr.value = str(building.level)
        expr = query.expr.add()
        expr.key = "garrison_num"
        expr.type = Item.INT
        expr.value = str(building.garrison_num)
        expr = query.expr.add()
        expr.key = "hero_ids"
        expr.type = Item.STRING
        expr.value = building.hero_ids
        expr = query.expr.add()
        expr.key = "is_upgrade"
        expr.type = Item.BOOL
        if building.is_upgrade == True:
            expr.value = "True"
        else:
            expr.value = "False"
        expr = query.expr.add()
        expr.key = "upgrade_start_time"
        expr.type = Item.INT
        expr.value = str(building.upgrade_start_time)
        expr = query.expr.add()
        expr.key = "upgrade_consume_time"
        expr.type = Item.INT
        expr.value = str(building.upgrade_consume_time)
        expr = query.expr.add()
        expr.key = "value"
        expr.type = Item.INT
        expr.value = str(building.value)
        expr = query.expr.add()
        expr.key = "city_id"
        expr.type = Item.INT
        expr.value = str(building.city_id)
        expr = query.expr.add()
        expr.key = "slot_index"
        expr.type = Item.INT
        expr.value = str(building.slot_index)


    def update_building(self, building):
        self._query_len += 1
        if self._multi_building is None:
            self._multi_building = False
            self.building = building 
        elif not self._multi_building:
            self._multi_building = True
            self.buildings.append(self.building)
            self.building = None
        else:
            self.buildings.append(building)

        query = self._req.query.add()
        query.user_id = building.user_id
        query.type = Query.UPDATE
        query.table_name = "building"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(building.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(building.user_id)

        if building.basic_id is not None:
            expr = query.expr.add()
            expr.key = "basic_id"
            expr.type = Item.INT
            expr.value = str(building.basic_id)
        if building.level is not None:
            expr = query.expr.add()
            expr.key = "level"
            expr.type = Item.INT
            expr.value = str(building.level)
        if building.garrison_num is not None:
            expr = query.expr.add()
            expr.key = "garrison_num"
            expr.type = Item.INT
            expr.value = str(building.garrison_num)
        if building.hero_ids is not None:
            expr = query.expr.add()
            expr.key = "hero_ids"
            expr.type = Item.STRING
            expr.value = building.hero_ids
        if building.is_upgrade is not None:
            expr = query.expr.add()
            expr.key = "is_upgrade"
            expr.type = Item.BOOL
            if building.is_upgrade == True:
                expr.value = "True"
            else:
                expr.value = "False"
        if building.upgrade_start_time is not None:
            expr = query.expr.add()
            expr.key = "upgrade_start_time"
            expr.type = Item.INT
            expr.value = str(building.upgrade_start_time)
        if building.upgrade_consume_time is not None:
            expr = query.expr.add()
            expr.key = "upgrade_consume_time"
            expr.type = Item.INT
            expr.value = str(building.upgrade_consume_time)
        if building.value is not None:
            expr = query.expr.add()
            expr.key = "value"
            expr.type = Item.INT
            expr.value = str(building.value)
        if building.city_id is not None:
            expr = query.expr.add()
            expr.key = "city_id"
            expr.type = Item.INT
            expr.value = str(building.city_id)
        if building.slot_index is not None:
            expr = query.expr.add()
            expr.key = "slot_index"
            expr.type = Item.INT
            expr.value = str(building.slot_index)


    def search_user_all_defense(self, user_id):
        self._multi_defense = True
        self._pack_search_defense(None, user_id)


    def search_defense(self, id):
        if self._multi_defense is None:
            self._multi_defense = False
        else:
            self._multi_defense = True
        self._pack_search_defense(id, None)


    def _pack_search_defense(self, id, user_id):
        self._query_len += 1
        query = self._req.query.add()
        if id is not None:
            query.user_id = (id >> 32)
        if user_id is not None:
            query.user_id = user_id
        query.type = Query.SELECT
        query.table_name = "defense"
        if id is not None:
            condition = query.condition.add()
            condition.key = "id"
            condition.type = Item.INT
            condition.value = str(id)
        if user_id is not None:
            condition = query.condition.add()
            condition.key = "user_id"
            condition.type = Item.INT
            condition.value = str(user_id)
        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "city_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "building_level"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "defense_team"
        expr.type = Item.STRING
        expr = query.expr.add()
        expr.key = "defense_battle_score"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "money_capacity"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "food_capacity"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "durability"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "restore_speed"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "first_hero_value"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "second_hero_value"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "third_hero_value"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "formation_id"
        expr.type = Item.INT
        expr = query.expr.add()
        expr.key = "defeat_time"
        expr.type = Item.INT
 
 
    def _parse_defense(self, result):
        assert result.table.name == "defense"
        assert self._multi_defense is not None
        if len(result.table.rows) == 0:
            return None
        
        from app.core import defense as defense_module
        if self._multi_defense:
            for row in result.table.rows:
                defense = data.DefenseInfo(None, None)
                self.defenses.append(defense)
                self._parse_one_search(row, defense)
                defense_module.update_cur_defense(defense)
        else:
            assert len(result.table.rows) == 1
            self.defense = data.DefenseInfo(None, None)
            self._parse_one_search(result.table.rows[0], self.defense)
            defense_module.update_cur_defense(self.defense)
        

    def insert_defense(self, defense):
        self._query_len += 1
        self.defense = defense
        query = self._req.query.add()
        query.user_id = defense.user_id
        query.type = Query.INSERT
        query.table_name = "defense"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(defense.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(defense.user_id)
        expr = query.expr.add()
        expr.key = "city_id"
        expr.type = Item.INT
        expr.value = str(defense.city_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(defense.basic_id)
        expr = query.expr.add()
        expr.key = "building_level"
        expr.type = Item.INT
        expr.value = str(defense.building_level)
        expr = query.expr.add()
        expr.key = "defense_team"
        expr.type = Item.STRING
        expr.value = str(defense.defense_team)
        expr = query.expr.add()
        expr.key = "defense_battle_score"
        expr.type = Item.INT
        expr.value = str(defense.defense_battle_score)
        expr = query.expr.add()
        expr.key = "money_capacity"
        expr.type = Item.INT
        expr.value = str(defense.money_capacity)
        expr = query.expr.add()
        expr.key = "food_capacity"
        expr.type = Item.INT
        expr.value = str(defense.food_capacity)
        expr = query.expr.add()
        expr.key = "durability"
        expr.type = Item.INT
        expr.value = str(defense.durability)
        expr = query.expr.add()
        expr.key = "restore_speed"
        expr.type = Item.INT
        expr.value = str(defense.restore_speed)
        expr = query.expr.add()
        expr.key = "update_time"
        expr.type = Item.INT
        expr.value = str(defense.update_time)
        expr = query.expr.add()
        expr.key = "first_hero_value"
        expr.type = Item.INT
        expr.value = str(defense.first_hero_value)
        expr = query.expr.add()
        expr.key = "second_hero_value"
        expr.type = Item.INT
        expr.value = str(defense.second_hero_value)
        expr = query.expr.add()
        expr.key = "third_hero_value"
        expr.type = Item.INT
        expr.value = str(defense.third_hero_value)
        expr = query.expr.add()
        expr.key = "formation_id"
        expr.type = Item.INT
        expr.value = str(defense.formation_id)
        expr = query.expr.add()
        expr.key = "defeat_time"
        expr.type = Item.INT
        expr.value = str(defense.defeat_time)


    def update_defense(self, defense):
        self._query_len += 1
        self.defense = defense

        query = self._req.query.add()
        query.user_id = defense.user_id
        query.type = Query.UPDATE
        query.table_name = "defense"
        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(defense.id)
        if defense.user_id is not None:
            expr = query.expr.add()
            expr.key = "user_id"
            expr.type = Item.INT
            expr.value = str(defense.user_id)
        if defense.city_id is not None:
            expr = query.expr.add()
            expr.key = "city_id"
            expr.type = Item.INT
            expr.value = str(defense.city_id)
        if defense.basic_id is not None:
            expr = query.expr.add()
            expr.key = "basic_id"
            expr.type = Item.INT
            expr.value = str(defense.basic_id)
        if defense.building_level is not None:
            expr = query.expr.add()
            expr.key = "building_level"
            expr.type = Item.INT
            expr.value = str(defense.building_level)
        if defense.defense_team is not None:
            expr = query.expr.add()
            expr.key = "defense_team"
            expr.type = Item.STRING
            expr.value = str(defense.defense_team)
        if defense.defense_battle_score is not None:
            expr = query.expr.add()
            expr.key = "defense_battle_score"
            expr.type = Item.INT
            expr.value = str(defense.defense_battle_score)
        if defense.money_capacity is not None:
            expr = query.expr.add()
            expr.key = "money_capacity"
            expr.type = Item.INT
            expr.value = str(defense.money_capacity)
        if defense.food_capacity is not None:
            expr = query.expr.add()
            expr.key = "food_capacity"
            expr.type = Item.INT
            expr.value = str(defense.food_capacity)
        if defense.durability is not None:
            expr = query.expr.add()
            expr.key = "durability"
            expr.type = Item.INT
            expr.value = str(defense.durability)
        if defense.restore_speed is not None:
            expr = query.expr.add()
            expr.key = "restore_speed"
            expr.type = Item.INT
            expr.value = str(defense.restore_speed)
        if defense.update_time is not None:
            expr = query.expr.add()
            expr.key = "update_time"
            expr.type = Item.INT
            expr.value = str(defense.update_time)
        if defense.first_hero_value is not None:
            expr = query.expr.add()
            expr.key = "first_hero_value"
            expr.type = Item.INT
            expr.value = str(defense.first_hero_value)
        if defense.second_hero_value is not None:
            expr = query.expr.add()
            expr.key = "second_hero_value"
            expr.type = Item.INT
            expr.value = str(defense.second_hero_value)
        if defense.third_hero_value is not None:
            expr = query.expr.add()
            expr.key = "third_hero_value"
            expr.type = Item.INT
            expr.value = str(defense.third_hero_value)
        if defense.formation_id is not None:
            expr = query.expr.add()
            expr.key = "formation_id"
            expr.type = Item.INT
            expr.value = str(defense.formation_id)
        if defense.defeat_time is not None:
            expr = query.expr.add()
            expr.key = "defeat_time"
            expr.type = Item.INT
            expr.value = str(defense.defeat_time)

 
    def insert_pve(self, pve):
        self._query_len += 1
        if self._multi_pve is None:
            self._multi_pve = False
            self.pve = pve 
        elif not self._multi_pve:
            self._multi_pve = True
            self.pves.append(self.pve)
            self.pve = None
        else:
            self.pves.append(pve)

        query = self._req.query.add()
        query.user_id = pve.user_id
        query.type = Query.INSERT
        query.table_name = "pve"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(pve.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(pve.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(pve.basic_id)
        expr = query.expr.add()
        expr.key = "is_open"
        expr.type = Item.BOOL
        if pve.is_open == True:
            expr.value = "True"
        else:
            expr.value = "False"
        expr = query.expr.add()
        expr.key = "finish_status"
        expr.type = Item.STRING
        expr.value = pve.finish_status
        expr = query.expr.add()
        expr.key = "finish_num"
        expr.type = Item.STRING
        expr.value = pve.finish_num


    def update_pve(self, pve):
        self._query_len += 1
        if self._multi_pve is None:
            self._multi_pve = False
            self.pve = pve 
        elif not self._multi_pve:
            self._multi_pve = True
            self.pves.append(self.pve)
            self.pve = None
        else:
            self.pves.append(pve)

        query = self._req.query.add()
        query.user_id = pve.user_id
        query.type = Query.UPDATE
        query.table_name = "pve"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(pve.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(pve.user_id)

        if pve.basic_id is not None:
            expr = query.expr.add()
            expr.key = "basic_id"
            expr.type = Item.INT
            expr.value = str(pve.basic_id)
        if pve.is_open is not None:
            expr = query.expr.add()
            expr.key = "is_open"
            expr.type = Item.BOOL
            if pve.is_open == True:
                expr.value = "True"
            else:
                expr.value = "False"
        if pve.finish_status is not None:
            expr = query.expr.add()
            expr.key = "finish_status"
            expr.type = Item.STRING
            expr.value = pve.finish_status
        if pve.finish_num is not None:
            expr = query.expr.add()
            expr.key = "finish_num"
            expr.type = Item.STRING
            expr.value = pve.finish_num


    def insert_city(self, city):
        self._query_len += 1
        if self._multi_city is None:
            self._multi_city = False
            self.city = city
        elif not self._multi_city:
            self._multi_city = True
            self.citys.append(self.city)
            self.city = None
        else:
            self.citys.append(city)

        query = self._req.query.add()
        query.user_id = city.user_id
        query.type = Query.INSERT
        query.table_name = "city"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(city.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(city.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(city.basic_id)
        expr = query.expr.add()
        expr.key = "name"
        expr.type = Item.STRING
        expr.value = city.name
        expr = query.expr.add()
        expr.key = "building_num"
        expr.type = Item.INT
        expr.value = str(city.building_num)
        expr = query.expr.add()
        expr.key = "building_ids"
        expr.type = Item.STRING
        expr.value = city.building_ids


    def update_city(self, city):
        self._query_len += 1
        if self._multi_city is None:
            self._multi_city = False
            self.city = city
        elif not self._multi_city:
            self._multi_city = True
            self.citys.append(self.city)
            self.city = None
        else:
            self.citys.append(city)

        query = self._req.query.add()
        query.user_id = city.user_id
        query.type = Query.UPDATE
        query.table_name = "city"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(city.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(city.user_id)

        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(city.basic_id)
        expr = query.expr.add()
        expr.key = "name"
        expr.type = Item.STRING
        expr.value = city.name
        expr = query.expr.add()
        expr.key = "building_num"
        expr.type = Item.INT
        expr.value = str(city.building_num)
        expr = query.expr.add()
        expr.key = "building_ids"
        expr.type = Item.STRING
        expr.value = city.building_ids


    def insert_formation(self, formation):
        self._query_len += 1
        if self._multi_formation is None:
            self._multi_formation = False
            self.formation = formation
        elif not self._multi_formation:
            self._multi_formation = True
            self.formations.append(self.formation)
            self.formation = None
        else:
            self.formations.append(formation)

        query = self._req.query.add()
        query.user_id = formation.user_id
        query.type = Query.INSERT
        query.table_name = "formation"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(formation.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(formation.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(formation.basic_id)


    def insert_technology(self, technology):
        self._query_len += 1
        if self._multi_technology is None:
            self._multi_technology = False
            self.technology = technology
        elif not self._multi_technology:
            self._multi_technology = True
            self.technologys.append(self.technology)
            self.technology = None
        else:
            self.technologys.append(technology)

        query = self._req.query.add()
        query.user_id = technology.user_id
        query.type = Query.INSERT
        query.table_name = "technology"

        expr = query.expr.add()
        expr.key = "id"
        expr.type = Item.INT
        expr.value = str(technology.id)
        expr = query.expr.add()
        expr.key = "user_id"
        expr.type = Item.INT
        expr.value = str(technology.user_id)
        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(technology.basic_id)
        expr = query.expr.add()
        expr.key = "active"
        expr.type = Item.BOOL
        expr.value = str(technology.active)
        expr = query.expr.add()
        expr.key = "is_for_battle"
        expr.type = Item.BOOL
        expr.value = str(technology.is_for_battle)
        expr = query.expr.add()
        expr.key = "is_upgrade"
        expr.type = Item.BOOL
        expr.value = str(technology.is_upgrade)
        expr = query.expr.add()
        expr.key = "building_id"
        expr.type = Item.INT
        expr.value = str(technology.building_id)
        expr = query.expr.add()
        expr.key = "upgrade_start_time"
        expr.type = Item.INT
        expr.value = str(technology.upgrade_start_time)
        expr = query.expr.add()
        expr.key = "upgrade_consume_time"
        expr.type = Item.INT
        expr.value = str(technology.upgrade_consume_time)


    def update_technology(self, technology):
        self._query_len += 1
        if self._multi_technology is None:
            self._multi_technology = False
            self.technology = technology
        elif not self._multi_technology:
            self._multi_technology = True
            self.technologys.append(self.technology)
            self.technology = None
        else:
            self.technologys.append(technology)

        query = self._req.query.add()
        query.user_id = technology.user_id
        query.type = Query.UPDATE
        query.table_name = "technology"

        condition = query.condition.add()
        condition.key = "id"
        condition.type = Item.INT
        condition.value = str(technology.id)
        condition = query.condition.add()
        condition.key = "user_id"
        condition.type = Item.INT
        condition.value = str(technology.user_id)

        expr = query.expr.add()
        expr.key = "basic_id"
        expr.type = Item.INT
        expr.value = str(technology.basic_id)
        expr = query.expr.add()
        expr.key = "active"
        expr.type = Item.BOOL
        expr.value = str(technology.active)
        expr = query.expr.add()
        expr.key = "is_for_battle"
        expr.type = Item.BOOL
        expr.value = str(technology.is_for_battle)
        expr = query.expr.add()
        expr.key = "is_upgrade"
        expr.type = Item.BOOL
        expr.value = str(technology.is_upgrade)
        expr = query.expr.add()
        expr.key = "building_id"
        expr.type = Item.INT
        expr.value = str(technology.building_id)
        expr = query.expr.add()
        expr.key = "upgrade_start_time"
        expr.type = Item.INT
        expr.value = str(technology.upgrade_start_time)
        expr = query.expr.add()
        expr.key = "upgrade_consume_time"
        expr.type = Item.INT
        expr.value = str(technology.upgrade_consume_time)


