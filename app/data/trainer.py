#coding:utf8
"""
Created on 2015-12-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 记录一些统计数据
"""

import math
from utils import logger
from datalib.data_loader import data_loader
from app.data.node import NodeInfo


class TrainerInfo(object):
    """一些统计数据
    """

    def __init__(self, user_id = 0,
            kills = 0,
            daily_deads = 0, total_deads = 0,
            dnode_daily_win = 0, dnode_total_win = 0,
            dnode_highest_level = 0, knode_daily_win = 0,
            knode_total_win = 0, knode_highest_level = 0,
            defense_win = 0, rival_highest_battlescore = 0,
            daily_skill_upgrade = 0,
            daily_equipment_upgrade = 0,
            daily_equipment_enchant = 0,
            total_login_num = 0,
            total_skill_upgrade = 0,
            total_equipment_upgrade = 0,
            total_equipment_enchant = 0,
            total_soldier_tech_upgrade = 0,
            total_battle_tech_upgrade = 0,
            total_interior_tech_upgrade = 0,
            daily_share = 0,
            daily_cast_num = 0,
            daily_pray_num = 0,
            daily_buy_goods_in_wineshop = 0,
            daily_tech_upgrade_num = 0,
            daily_arena_num = 0,
            daily_event_tax_num = 0,
            daily_event_farm_num = 0,
            daily_event_mining_num = 0,
            daily_event_gold_num = 0,
            daily_event_visit_num = 0,
            daily_event_jungle_num = 0,
            daily_event_dungeon_num = 0,
            daily_event_search_num = 0,
            daily_event_deep_mining_num = 0,
            daily_event_hermit_num = 0,
            daily_finish_tax_num = 0,
            daily_finish_farm_num = 0,
            daily_finish_mining_num = 0,
            daily_finish_gold_num = 0,
            daily_finish_search_num = 0,
            daily_finish_deep_mining_num = 0,
            daily_finish_hermit_num = 0,
            daily_buy_energy_num = 0,
            daily_increase_item_num = 0,
            daily_vitality = 0,
            daily_choose_card_num = 0,
            daily_buy_goods_in_achievement_shop = 0,
            daily_buy_goods_in_legendcity_shop = 0,
            daily_buy_goods_in_union_shop = 0,
            daily_buy_goods_in_soul_shop = 0,
            daily_start_union_aid = 0,
            daily_respond_union_aid = 0,
            daily_start_union_donate = 0,
            daily_battle_legendcity = 0,
            daily_battle_anneal_normal = 0,
            daily_battle_anneal_hard = 0,
            daily_battle_expand_one = 0,
            daily_battle_expand_two = 0,
            daily_battle_expand_three = 0,
            daily_battle_transfer = 0,
            total_buy_energy_num = 0,
            total_pray_num = 0,
            total_buy_goods_in_wineshop = 0,
            total_tech_upgrade_num = 0,
            total_start_union_donate = 0,
            total_respond_union_aid = 0,
            total_event_tax_num = 0,
            total_event_farm_num = 0,
            total_event_mining_num = 0,
            total_event_gold_num = 0,
            total_event_visit_num = 0,
            total_event_jungle_num = 0,
            total_event_dungeon_num = 0,
            total_event_search_num = 0,
            total_event_deep_mining_num = 0,
            total_event_hermit_num = 0,
            day7_vitality = 0,
            total_battle_legendcity = 0,
            total_battle_anneal_normal = 0,
            total_battle_anneal_hard = 0,
            total_battle_expand_one = 0,
            total_battle_expand_two = 0,
            total_battle_expand_three = 0,
            total_battle_transfer = 0,
            buy_daily_discount = 0):

        self.user_id = user_id

        #统计信息
        self.kills = kills #杀敌数
        self.daily_deads = daily_deads #今天死兵数
        self.total_deads = total_deads #总死兵数

        self.dnode_daily_win = dnode_daily_win          #附属点总胜利次数
        self.dnode_total_win = dnode_total_win          #附属点今天胜利次数
        self.dnode_highest_level = dnode_highest_level  #附属点战胜过的最高等级
        self.knode_daily_win = knode_daily_win          #关键点总胜利次数
        self.knode_total_win = knode_total_win          #关键点今天胜利次数
        self.knode_highest_level = knode_highest_level  #关键点攻陷过的城池最高等级
        self.defense_win = defense_win                  #防御入侵成功的次数
        self.rival_highest_battlescore = rival_highest_battlescore    #击败过的敌人最高战力

        self.daily_skill_upgrade = daily_skill_upgrade  #今天技能升级次数
        self.daily_equipment_upgrade = daily_equipment_upgrade  #今天装备进阶次数
        self.daily_equipment_enchant = daily_equipment_enchant  #今天装备精炼次数
        self.total_login_num = total_login_num                  #登陆次数
        self.total_skill_upgrade = total_skill_upgrade          #技能升级次数
        self.total_equipment_upgrade = total_equipment_upgrade  #装备进阶次数
        self.total_equipment_enchant = total_equipment_enchant  #装备精炼次数
        self.total_soldier_tech_upgrade = total_soldier_tech_upgrade      #兵种科技升级次数
        self.total_battle_tech_upgrade = total_battle_tech_upgrade        #战斗科技升级次数
        self.total_interior_tech_upgrade = total_interior_tech_upgrade    #内政科技升级次数

        self.daily_share = daily_share        #记录用户分享游戏的次数

        self.daily_cast_item_num = daily_cast_num     #今天熔铸的次数
        self.daily_pray_num = daily_pray_num      #今天祈福的次数
        self.daily_buy_goods_in_wineshop = daily_buy_goods_in_wineshop #今天商铺购买次数
        self.daily_tech_upgrade_num = daily_tech_upgrade_num  #今日科技升级次数
        self.daily_arena_num = daily_arena_num  #今天演武场战斗次数
        self.daily_event_tax_num = daily_event_tax_num  #今天征税次数
        self.daily_event_farm_num = daily_event_farm_num   #今日屯田次数
        self.daily_event_mining_num = daily_event_mining_num   #今天挖矿次数
        self.daily_event_gold_num = daily_event_gold_num    #今日挖金矿次数
        self.daily_event_visit_num = daily_event_visit_num  #今日探访次数
        self.daily_event_jungle_num = daily_event_jungle_num   #今日山贼次数
        self.daily_event_dungeon_num = daily_event_dungeon_num #今日外敌入侵次数
        self.daily_event_search_num = daily_event_search_num   #今日废墟次数
        self.daily_event_deep_mining_num = daily_event_deep_mining_num #今日秘矿次数
        self.daily_event_hermit_num = daily_event_hermit_num  #今日探访隐士次数

        self.daily_finish_tax_num = daily_finish_tax_num  #今日完成探访隐士次数
        self.daily_finish_farm_num = daily_finish_farm_num  #今日完成探访隐士次数
        self.daily_finish_mining_num = daily_finish_mining_num  #今日完成探访隐士次数
        self.daily_finish_gold_num = daily_finish_gold_num  #今日完成探访隐士次数
        self.daily_finish_search_num = daily_finish_search_num  #今日完成探访隐士次数
        self.daily_finish_deep_mining_num = daily_finish_deep_mining_num  #今日完成探访隐士次数
        self.daily_finish_hermit_num = daily_finish_hermit_num  #今日完成探访隐士次数

        self.daily_buy_energy_num = daily_buy_energy_num  #今日购买政令次数
        self.daily_increase_item_num = daily_increase_item_num   #今日使用增产次数
        self.daily_vitality = daily_vitality   #活跃度
        self.daily_choose_card_num = daily_choose_card_num  #每日祈福翻牌子的数量
        self.daily_buy_goods_in_achievement_shop = daily_buy_goods_in_achievement_shop  #每日技巧值商店购买次数
        self.daily_buy_goods_in_legendcity_shop = daily_buy_goods_in_legendcity_shop   #每日史实城商店购买次数
        self.daily_buy_goods_in_union_shop = daily_buy_goods_in_union_shop  #每日联盟商店购买次数
        self.daily_buy_goods_in_soul_shop = daily_buy_goods_in_soul_shop    #每日精魄商店购买次数

        self.daily_start_union_aid = daily_start_union_aid          #每日发起联盟援助次数
        self.daily_respond_union_aid = daily_respond_union_aid       #每日响应联盟援助的次数
        self.daily_start_union_donate = daily_start_union_donate     #每日进行联盟捐献的次数

        self.daily_battle_legendcity = daily_battle_legendcity        #每日进行史实城攻击次数
        self.daily_battle_anneal_normal = daily_battle_anneal_normal  #每日进行试炼场简单模式的次数
        self.daily_battle_anneal_hard = daily_battle_anneal_hard      #每日进行试炼场困难模式的次数
        self.daily_battle_expand_one = daily_battle_expand_one        #每日进行争分夺秒副本的次数
        self.daily_battle_expand_two = daily_battle_expand_two        #每日进行斩尽杀绝副本的次数
        self.daily_battle_expand_three = daily_battle_expand_three    #每日进行毫发无伤副本的次数
        self.daily_battle_transfer = daily_battle_transfer            #每日进行实力榜战斗的次数
        self.buy_daily_discount = buy_daily_discount    #购买每日特惠
        
        self.total_buy_energy_num = total_buy_energy_num               #购买政令次数
        self.total_pray_num = total_pray_num                           #祈福的次数
        self.total_buy_goods_in_wineshop = total_buy_goods_in_wineshop #商铺购买次数
        self.total_tech_upgrade_num = total_tech_upgrade_num           #科技升级次数
        self.total_start_union_donate = total_start_union_donate       #进行联盟捐献的次数
        self.total_respond_union_aid = total_respond_union_aid         #响应联盟援助的次数
        self.total_event_tax_num = total_event_tax_num                 #征税次数
        self.total_event_farm_num = total_event_farm_num               #屯田次数
        self.total_event_mining_num = total_event_mining_num           #挖矿次数
        self.total_event_gold_num = total_event_gold_num               #挖金矿次数
        self.total_event_visit_num = total_event_visit_num             #探访次数
        self.total_event_jungle_num = total_event_jungle_num           #山贼次数
        self.total_event_dungeon_num = total_event_dungeon_num         #外敌入侵次数
        self.total_event_search_num = total_event_search_num           #废墟次数
        self.total_event_deep_mining_num = total_event_deep_mining_num #秘矿次数
        self.total_event_hermit_num = total_event_hermit_num           #探访隐士次数
        self.day7_vitality = day7_vitality                           #活跃度
        self.total_battle_legendcity = total_battle_legendcity         #进行史实城攻击次数
        self.total_battle_anneal_normal = total_battle_anneal_normal   #进行试炼场简单模式的次数
        self.total_battle_anneal_hard = total_battle_anneal_hard       #进行试炼场困难模式的次数
        self.total_battle_expand_one = total_battle_expand_one         #进行争分夺秒副本的次数
        self.total_battle_expand_two = total_battle_expand_two         #进行斩尽杀绝副本的次数
        self.total_battle_expand_three = total_battle_expand_three     #进行毫发无伤副本的次数
        self.total_battle_transfer = total_battle_transfer             #进行实力榜战斗的次数


    @staticmethod
    def create(user_id):
        """生成TrainerInfo
        Args:
            user_id[int]: 用户 id
        Returns:
            trainer[TrainerInfo]
        """
        trainer = TrainerInfo(user_id)

        return trainer


    def reset_daily_statistics(self):
        """重置天粒度统计信息
        Returns:
            None
        """
        self.daily_deads = 0
        self.dnode_daily_win = 0
        self.knode_daily_win = 0
        self.daily_skill_upgrade = 0
        self.daily_equipment_upgrade = 0
        self.daily_equipment_enchant = 0
        self.daily_share = 0
        self.daily_cast_item_num = 0
        self.daily_pray_num = 0
        self.daily_buy_goods_in_wineshop = 0
        self.daily_tech_upgrade_num = 0
        self.daily_arena_num = 0
        self.daily_event_tax_num = 0
        self.daily_event_farm_num = 0
        self.daily_event_mining_num = 0
        self.daily_event_gold_num = 0
        self.daily_event_visit_num = 0
        self.daily_event_jungle_num = 0
        self.daily_event_dungeon_num  = 0
        self.daily_event_search_num = 0
        self.daily_event_deep_mining_num = 0
        self.daily_event_hermit_num = 0

        self.daily_buy_energy_num = 0
        self.daily_increase_item_num = 0
        self.daily_vitality = 0
        self.daily_choose_card_num = 0
        self.daily_buy_goods_in_achievement_shop = 0
        self.daily_buy_goods_in_legendcity_shop = 0
        self.daily_buy_goods_in_union_shop = 0
        self.daily_buy_goods_in_soul_shop = 0

        self.daily_finish_tax_num = 0
        self.daily_finish_farm_num = 0
        self.daily_finish_mining_num = 0
        self.daily_finish_gold_num = 0
        self.daily_finish_search_num = 0
        self.daily_finish_deep_mining_num = 0
        self.daily_finish_hermit_num = 0

        self.daily_start_union_aid = 0
        self.daily_respond_union_aid = 0
        self.daily_start_union_donate = 0

        self.daily_battle_legendcity = 0 
        self.daily_battle_anneal_normal = 0
        self.daily_battle_anneal_hard = 0
        self.daily_battle_expand_one = 0
        self.daily_battle_expand_two = 0
        self.daily_battle_expand_three = 0
        self.daily_battle_transfer = 0
        self.buy_daily_discount = 0


    def add_daily_cast_item_num(self, num):
        assert num >= 0
        self.daily_cast_item_num += num

    def add_daily_pray_num(self, num):
        assert num >= 0
        self.daily_pray_num += num
        self.total_pray_num += num

    def add_daily_buy_goods_in_wineshop(self, num):
        assert num >= 0
        self.daily_buy_goods_in_wineshop += num
        self.total_buy_goods_in_wineshop += num

    def add_daily_buy_goods_in_achievement_shop(self, num):
        assert num >= 0
        self.daily_buy_goods_in_achievement_shop += num

    def add_daily_buy_goods_in_legendcity_shop(self, num):
        assert num >= 0
        self.daily_buy_goods_in_legendcity_shop += num

    def add_daily_buy_goods_in_union_shop(self, num):
        assert num >= 0
        self.daily_buy_goods_in_union_shop += num

    def add_daily_buy_goods_in_soul_shop(self, num):
        assert num >= 0
        self.daily_buy_goods_in_soul_shop += num

    def add_daily_tech_upgrade_num(self, num):
        assert num >= 0
        self.daily_tech_upgrade_num += num
        self.total_tech_upgrade_num += num

    def add_daily_arena_num(self, num):
        assert num >= 0
        self.daily_arena_num += num

    def add_daily_buy_energy_num(self, num):
        assert num >= 0
        self.daily_buy_energy_num += num
        self.total_buy_energy_num += num

    def add_daily_increase_item_num(self, num):
        assert num >= 0
        self.daily_increase_item_num += num

    def add_daily_event_num(self, event_type, num):
        assert num >= 0
        if event_type == NodeInfo.EVENT_TYPE_TAX:
            self.daily_event_tax_num += num
            self.total_event_tax_num += num
        elif event_type == NodeInfo.EVENT_TYPE_FARM:
            self.daily_event_farm_num += num
            self.total_event_farm_num += num
        elif event_type == NodeInfo.EVENT_TYPE_MINING:
            self.daily_event_mining_num += num
            self.total_event_mining_num += num
        elif event_type == NodeInfo.EVENT_TYPE_GOLD:
            self.daily_event_gold_num += num
            self.total_event_gold_num += num
        elif event_type == NodeInfo.EVENT_TYPE_VISIT:
            self.daily_event_visit_num += num
            self.total_event_visit_num += num
        elif event_type == NodeInfo.EVENT_TYPE_JUNGLE:
            self.daily_event_jungle_num += num
            self.total_event_jungle_num += num
        elif event_type == NodeInfo.EVENT_TYPE_DUNGEON:
            self.daily_event_dungeon_num += num
            self.total_event_dungeon_num += num
        elif event_type == NodeInfo.EVENT_TYPE_SEARCH:
            self.daily_event_search_num += num
            self.total_event_search_num += num
        elif event_type == NodeInfo.EVENT_TYPE_DEEP_MINING:
            self.daily_event_deep_mining_num += num
            self.total_event_deep_mining_num += num
        elif event_type == NodeInfo.EVENT_TYPE_HERMIT:
            self.daily_event_hermit_num += num
            self.total_event_hermit_num += num

    def add_daily_finish_event_num(self, event_type, num):
        assert num >= 0
        if event_type == NodeInfo.EVENT_TYPE_TAX:
            self.daily_finish_tax_num += num
        elif event_type == NodeInfo.EVENT_TYPE_FARM:
            self.daily_finish_farm_num += num
        elif event_type == NodeInfo.EVENT_TYPE_MINING:
            self.daily_finish_mining_num += num
        elif event_type == NodeInfo.EVENT_TYPE_GOLD:
            self.daily_finish_gold_num += num
        elif event_type == NodeInfo.EVENT_TYPE_SEARCH:
            self.daily_finish_search_num += num
        elif event_type == NodeInfo.EVENT_TYPE_DEEP_MINING:
            self.daily_finish_deep_mining_num += num
        elif event_type == NodeInfo.EVENT_TYPE_HERMIT:
            self.daily_finish_hermit_num += num


    def add_daily_vitality(self, num):
        assert num >= 0
        self.daily_vitality += num

    def add_day7_vitality(self, num):
        self.day7_vitality += num

    def get_daily_event_num(self, event_type):
        if event_type == NodeInfo.EVENT_TYPE_TAX:
            return self.daily_event_tax_num
        elif event_type == NodeInfo.EVENT_TYPE_FARM:
            return self.daily_event_farm_num
        elif event_type == NodeInfo.EVENT_TYPE_MINING:
            return self.daily_event_mining_num
        elif event_type == NodeInfo.EVENT_TYPE_GOLD:
            return self.daily_event_gold_num
        elif event_type == NodeInfo.EVENT_TYPE_VISIT:
            return self.daily_event_visit_num
        elif event_type == NodeInfo.EVENT_TYPE_JUNGLE:
            return self.daily_event_jungle_num
        elif event_type == NodeInfo.EVENT_TYPE_DUNGEON:
            return self.daily_event_dungeon_num
        elif event_type == NodeInfo.EVENT_TYPE_SEARCH:
            return self.daily_event_search_num
        elif event_type == NodeInfo.EVENT_TYPE_DEEP_MINING:
            return self.daily_event_deep_mining_num
        elif event_type == NodeInfo.EVENT_TYPE_HERMIT:
            return self.daily_event_hermit_num


    def get_total_event_num(self, event_type):
        if event_type == NodeInfo.EVENT_TYPE_TAX:
            return self.total_event_tax_num
        elif event_type == NodeInfo.EVENT_TYPE_FARM:
            return self.total_event_farm_num
        elif event_type == NodeInfo.EVENT_TYPE_MINING:
            return self.total_event_mining_num
        elif event_type == NodeInfo.EVENT_TYPE_GOLD:
            return self.total_event_gold_num
        elif event_type == NodeInfo.EVENT_TYPE_VISIT:
            return self.total_event_visit_num
        elif event_type == NodeInfo.EVENT_TYPE_JUNGLE:
            return self.total_event_jungle_num
        elif event_type == NodeInfo.EVENT_TYPE_DUNGEON:
            return self.total_event_dungeon_num
        elif event_type == NodeInfo.EVENT_TYPE_SEARCH:
            return self.total_event_search_num
        elif event_type == NodeInfo.EVENT_TYPE_DEEP_MINING:
            return self.total_event_deep_mining_num
        elif event_type == NodeInfo.EVENT_TYPE_HERMIT:
            return self.total_event_hermit_num


    def add_daily_choose_card_num(self, num):
        assert num >= 0
        self.daily_choose_card_num += num


    def add_kills(self, num):
        """增加杀敌数
        """
        #assert num >= 0
        self.kills += num
        self.kills = max(0, self.kills)


    def add_deads(self, num):
        """累加死兵数
        """
        assert num >= 0
        self.daily_deads += num
        self.total_deads += num


    def add_defense_win(self, num):
        """累加防御成功次数
        """
        assert num >= 0
        self.defense_win += num


    def update_rival_highest_battlescore(self, battlescore):
        """更新击败过的敌人的最高战力
        """
        if self.rival_highest_battlescore < battlescore:
            self.rival_highest_battlescore = battlescore


    def update_knode_statistic_data(self, win_num, rival_level):
        """更新关键点的统计信息
        """
        assert win_num >= 0
        self.knode_daily_win += win_num
        self.knode_total_win += win_num

        if self.knode_highest_level < rival_level:
            self.knode_highest_level = rival_level


    def update_dnode_statistic_data(self, win_num, rival_level):
        """更新附属点的统计信息
        """
        assert win_num >= 0
        self.dnode_daily_win += win_num
        self.dnode_total_win += win_num

        if self.dnode_highest_level < rival_level:
            self.dnode_highest_level = rival_level


    def add_login_num(self, num):
        """记录登陆次数
        Returns:
            None
        """
        self.total_login_num += num



    def add_skill_upgrade_num(self, num):
        """记录技能升级次数
        Returns:
            None
        """
        self.daily_skill_upgrade += num
        self.total_skill_upgrade += num


    def add_equipment_upgrade_num(self, num):
        """记录装备进阶次数
        Returns:
            None
        """
        self.daily_equipment_upgrade += num
        self.total_equipment_upgrade += num


    def add_equipment_enchant_num(self, num):
        """记录装备精炼次数
        Returns:
            None
        """
        self.daily_equipment_enchant += num
        self.total_equipment_enchant += num


    def add_soldier_tech_upgrade_num(self, num):
        """记录兵种科技升级次数
        Returns:
            None
        """
        self.total_soldier_tech_upgrade += num


    def add_battle_tech_upgrade_num(self, num):
        """记录战斗科技升级次数
        Returns:
            None
        """
        self.total_battle_tech_upgrade += num


    def add_interior_tech_upgrade_num(self, num):
        """记录内政科技升级次数
        Returns:
            None
        """
        self.total_interior_tech_upgrade += num


    def add_share_num(self, num):
        """记录客户端分享的的次数
        """
        self.daily_share += num

    def add_daily_start_aid(self, num):
        """每日发起联盟援助次数"""
        self.daily_start_union_aid += num

    def add_daily_respond_aid(self, num):
        """每日响应联盟援助的次数"""
        self.daily_respond_union_aid += num
        self.total_respond_union_aid += num

    def add_daily_start_donate(self, num):
        """每日进行联盟捐献的次数"""
        self.daily_start_union_donate += num
        self.total_start_union_donate += num

    def add_daily_battle_legendcity(self, num):
        """每日进行史实城战斗的次数"""
        self.daily_battle_legendcity += num
        self.total_battle_legendcity += num

    def add_daily_battle_anneal_normal(self, num):
        """每日进行试炼场简单模式战斗的次数"""
        self.daily_battle_anneal_normal += num
        self.total_battle_anneal_normal += num

    def add_daily_battle_anneal_hard(self, num):
        """每日进行试炼场困难模式战斗的次数"""
        self.daily_battle_anneal_hard += num
        self.total_battle_anneal_hard += num

    def add_daily_battle_expand_one(self, num):
        """每日进行争分夺秒副本战斗的次数"""
        self.daily_battle_expand_one += num
        self.total_battle_expand_one += num

    def add_daily_battle_expand_two(self, num):
        """每日进行斩尽杀绝副本战斗的次数"""
        self.daily_battle_expand_two += num
        self.total_battle_expand_two += num

    def add_daily_battle_expand_three(self, num):
        """每日进行毫发无伤副本战斗的次数"""
        self.daily_battle_expand_three += num
        self.total_battle_expand_three += num

    def add_daily_battle_transfer(self, num):
        """每日进行实力榜战斗的次数"""
        self.daily_battle_transfer += num
        self.total_battle_transfer += num

    def add_buy_daily_discount(self, num):
        """每日特惠购买次数"""
        self.buy_daily_discount += num


