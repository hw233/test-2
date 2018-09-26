#coding:utf8
"""
Created on 2015-10-17
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 世界地图全局信息
"""

import random
from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader


class MapGraph(object):
    """世界地图：节点连通关系
    单例
    """
    __metaclass__ = Singleton

    def __init__(self):
        """根据配置数据初始化连通关系
        """
        self._nodes = {}
        self._parent = {}

        for basic_id in data_loader.MapNodeBasicInfo_dict:
            self._nodes[basic_id] = data_loader.MapNodeBasicInfo_dict[basic_id]

        for parent_basic_id in self._nodes:
            for child_basic_id in self._nodes[parent_basic_id].children:
                self._parent[child_basic_id] = parent_basic_id

    def __iter__(self):
        return iter(self._nodes)


    def get_neighbors(self, basic_id):
        return self._nodes[basic_id].neighbors


    def get_children(self, basic_id):
        return self._nodes[basic_id].children


    def get_parent(self, basic_id):
        return self._parent[basic_id]


class MapInfo(object):
    def __init__(self, user_id = 0,
            next_war_time = 0,
            next_luck_time = 0,
            own_key_lost_weight = 0.0,
            own_key_weight = 0.0,
            own_exploit_money_amount = 0,
            own_exploit_food_amount = 0,
            own_exploit_material_amount = 0,
            own_exploit_gold_amount = 0,
            total_key_exploit_money_weight = 0.0,
            total_key_exploit_food_weight = 0.0,
            total_key_exploit_material_weight = 0.0,
            total_key_enemy_pve_weight = 0.0,
            total_key_enemy_pvp_city_weight = 0.0,
            total_key_enemy_pvp_resource_weight = 0.0,
            event_visit_daily_count = 0,
            event_question_daily_count = 0,
            event_daily_count = 0,
            event_update_time = 0,
            current_occupy_node_num = 0,
            occupy_node_num_mansion = 0,
            occupy_node_num_watchtower = 0,
            occupy_node_num_technology = 0):

        self.user_id = user_id
        self.next_war_time = next_war_time
        self.next_luck_time = next_luck_time

        #己方占领的关键点信息
        self.own_key_lost_weight = own_key_lost_weight
        self.own_key_weight = own_key_weight

        #所有己方资源信息
        self.own_exploit_money_amount = own_exploit_money_amount
        self.own_exploit_food_amount = own_exploit_food_amount
        self.own_exploit_material_amount = own_exploit_material_amount
        self.own_exploit_gold_amount = own_exploit_gold_amount

        #所有可见的关键点信息
        self.total_key_exploit_money_weight = total_key_exploit_money_weight
        self.total_key_exploit_food_weight = total_key_exploit_food_weight
        self.total_key_exploit_material_weight = total_key_exploit_material_weight

        #所有关键点上的敌人信息
        self.total_key_enemy_pve_weight = total_key_enemy_pve_weight
        self.total_key_enemy_pvp_city_weight = total_key_enemy_pvp_city_weight
        self.total_key_enemy_pvp_resource_weight = total_key_enemy_pvp_resource_weight

        #随机事件信息
        self.event_visit_daily_count = event_visit_daily_count
        self.event_question_daily_count = event_question_daily_count
        self.event_daily_count = event_daily_count
        self.event_update_time = event_update_time

        #领地信息
        self.current_occupy_node_num = current_occupy_node_num
        self.occupy_node_num_mansion = occupy_node_num_mansion
        self.occupy_node_num_watchtower = occupy_node_num_watchtower
        self.occupy_node_num_technology = occupy_node_num_technology

    @staticmethod
    def create(user_id):
        """创建
        """
        return MapInfo(user_id)


    def is_able_to_trigger_war_event(self, now):
        """是否可以触发战争事件
        """
        return now >= self.next_war_time


    def is_able_to_trigger_lucky_event(self, now):
        """是否可以触发随机事件
        """
        return now >= self.next_luck_time


    def calc_war_time(self, now):
        """计算战争发生的时间
        """
        if self.next_war_time >= now:
            return now

        #平均概率随机
        random.seed()
        war_time = random.randint(self.next_war_time, now)
        return war_time


    def update_next_war_time(self, now):
        """计算下一次触发战争事件的时间
        """
        gap_mu = float(data_loader.MapConfInfo_dict["war_gap_mu"].value)
        gap_sigma = float(data_loader.MapConfInfo_dict["war_gap_sigma"].value)
        gap_min = int(float(data_loader.MapConfInfo_dict["war_gap_min"].value))
        gap_max = int(float(data_loader.MapConfInfo_dict["war_gap_max"].value))

        random.seed()
        gap = int(random.gauss(gap_mu, gap_sigma))
        gap = min(gap, gap_max)
        gap = max(gap, gap_min)
        self.next_war_time = gap + now


    def update_next_luck_time(self, now, count = 1, reduce_gap = False):
        """计算下一次触发随机事件的时间
        Args:
            now[int]: 时间戳
            count[int]: 触发计数增加多少
            reduce_gap[bool]: 是否减少下次触发间隔
        """
        if reduce_gap:
            gap = int(float(data_loader.MapConfInfo_dict["luck_gap_if_none"].value))
        else:
            gap_mu = float(data_loader.MapConfInfo_dict["luck_gap_mu"].value)
            gap_sigma = float(data_loader.MapConfInfo_dict["luck_gap_sigma"].value)
            #gap_min = int(float(data_loader.MapConfInfo_dict["luck_gap_min"].value))
            #gap_max = int(float(data_loader.MapConfInfo_dict["luck_gap_max"].value))

            #暂时硬编码，后面再修改
            passed_time = now - self.event_update_time
            if passed_time >=0 and passed_time < 1800:
                gap_mu = 3600
            elif passed_time >= 1800 and passed_time < 3600:
                gap_mu = 3000
            elif passed_time >= 3600 and passed_time < 7200:
                gap_mu = 2400
            elif passed_time > 7200:
                gap_mu = 1200
            gap_min = int(gap_mu * 0.8)
            gap_max = int(gap_mu * 1.2)

            random.seed()
            gap = int(random.gauss(gap_mu, gap_sigma))
            gap = min(gap, gap_max)
            gap = max(gap, gap_min)

            logger.debug("Update next luck time[last_time=%d][passed_time=%d][mu=%d][gap=%d]"
                    % (self.event_update_time, passed_time, gap_mu, gap))

        self.next_luck_time = gap + now
        self.event_daily_count += count
        self.event_update_time = now


    def update_for_own_key_node(self, node, add = True):
        """更新己方占领的关键点信息
        """
        assert node.is_key_node()
        match_info = node.get_key_node_match_info()

        if add:
            self.own_key_weight += match_info.appearWeight
            self.own_key_lost_weight += match_info.lostWeight
        else:
            self.own_key_weight -= match_info.appearWeight
            self.own_key_lost_weight -= match_info.lostWeight


    def update_for_own_exploit_amount(self, node, add = True):
        """更新所有己方资源信息
        """
        assert node.is_own_side()

        if add:
            amount = node.exploit_reserve
        else:
            amount = 0 - node.exploit_reserve

        if node.is_exploit_money():
            self.own_exploit_money_amount += amount
            logger.debug("own exploit money amount[diff=%d][current=%d]" %
                    (amount, self.own_exploit_money_amount))
        elif node.is_exploit_food():
            self.own_exploit_food_amount += amount
            logger.debug("own exploit food amount[diff=%d][current=%d]" %
                    (amount, self.own_exploit_food_amount))
        elif node.is_exploit_material():
            self.own_exploit_material_amount += amount
            logger.debug("own exploit material amount[diff=%d][current=%d]" %
                    (amount, self.own_exploit_material_amount))

        #金矿是附属点产出，依附与所有其他所有资源
        gold_amount = data_loader.GoldExploitationBasicInfo_dict[node.exploit_level].reserves
        if not add:
            gold_amount = 0 - gold_amount
        gold_count = len(MapGraph().get_children(node.basic_id))
        self.own_exploit_gold_amount += (gold_amount * gold_count)
        logger.debug("own exploit gold amount[diff=%d][current=%d]" %
                (gold_amount * gold_count, self.own_exploit_gold_amount))


    def update_for_key_node_type(self, node, add = True):
        """更新可见关键点类型信息
        """
        assert node.is_key_node()

        match_info = node.get_key_node_match_info()
        if add:
            weight = match_info.appearWeight
        else:
            weight = 0 - match_info.appearWeight

        if node.is_exploit_money():
            self.total_key_exploit_money_weight += weight
        elif node.is_exploit_food():
            self.total_key_exploit_food_weight += weight
        elif node.is_exploit_material():
            self.total_key_exploit_material_weight += weight


    def update_for_key_node_enemy_type(self, node, add = True):
        """更新可见的关键点敌人类型信息
        """
        assert node.is_key_node()

        #不统计副本类型
        if node.is_rival_dungeon():
            return

        match_info = node.get_key_node_enemy_match_info()
        if add:
            weight = match_info.weight
        else:
            weight = 0 - match_info.weight

        if node.rival_type == node.ENEMY_TYPE_PVE_RESOURCE:
            self.total_key_enemy_pve_weight += weight
        elif node.rival_type == node.ENEMY_TYPE_PVP_CITY:
            self.total_key_enemy_pvp_city_weight += weight
        elif node.rival_type == node.ENEMY_TYPE_PVP_RESOURCE:
            self.total_key_enemy_pvp_resource_weight += weight


    def update_for_visit_event(self):
        """更新探访随机事件信息
        """
        self.event_visit_daily_count += 1


    def update_for_question_event(self):
        """更新问答随机事件信息
        """
        self.event_question_daily_count += 1


    def reset_daily_statistics(self, now):
        """重置每天统计数据
        """
        if not utils.is_same_day(self.event_update_time, now):
            self.event_daily_count = 0
            self.event_visit_daily_count = 0
            self.event_question_daily_count = 0


    def update_occupy_node_num_mansion(self, num):
        """更新官邸带来的领地城池数
        """
        assert num >= 0
        self.occupy_node_num_mansion = num


    def update_occupy_node_num_watchtower(self, num):
        """更新瞭望塔带来的领地城池数
        """
        assert num >= 0
        self.occupy_node_num_watchtower = num


    def update_occupy_node_num_technology(self, num):
        """更新科技带来的领地城池数
        """
        assert num >= 0
        self.occupy_node_num_technology = num


    def get_all_occupy_nodes_num(self):
        """获得总领地城池上限
        """
        all_occupy_nodes_num = (
                self.occupy_node_num_mansion
                + self.occupy_node_num_watchtower
                + self.occupy_node_num_technology)
        return all_occupy_nodes_num


    def is_able_to_occupy_more(self):
        """是否可以占领更多node
        """
        all_occupy_nodes_num = self.get_all_occupy_nodes_num()
        if self.current_occupy_node_num < all_occupy_nodes_num:
            return True
        else:
            return False


    def occupy_node(self, num):
        """占领节点
        """
        self.current_occupy_node_num += num


    def lost_node(self, num):
        """丢失占领的节点
        """
        self.current_occupy_node_num -= num

