#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : App 模块提供的服务，供 Portal 模块使用
"""

from firefly.server.globalobject import rootserviceHandle
from app.processor.account_process import AccountProcessor
from app.processor.user_process import UserProcessor
from app.processor.city_process import CityProcessor
from app.processor.shop_process import ShopProcessor
from app.processor.union_shop_processor import UnionShopProcessor
from app.processor.draw_process import DrawProcessor
from app.processor.signin_process import SigninProcessor
from app.processor.hero_process import HeroProcessor
from app.processor.item_process import ItemProcessor
from app.processor.building_process import BuildingProcessor
from app.processor.technology_process import TechnologyProcessor
from app.processor.resource_process import ResourceProcessor
from app.processor.conscript_process import ConscriptProcessor
from app.processor.team_process import TeamProcessor
from app.processor.map_process import MapProcessor
from app.processor.event_process import EventProcessor
from app.processor.appoint_process import AppointProcessor
from app.processor.pay_process import PayProcessor
from app.processor.activity_process import ActivityProcessor
from app.processor.arena_process import ArenaProcessor
from app.processor.melee_process import MeleeProcessor
from app.processor.protection_process import ProtectionProcessor
from app.processor.increase_process import IncreaseProcessor
from app.processor.cdkey_process import CDkeyProcessor
from app.processor.legendcity_processor import LegendCityProcessor
from app.processor.notice_processor import NoticeProcessor
from app.processor.energy_process import EnergyProcessor
from app.processor.pray_process import PrayProcessor
from app.processor.union_processor import UnionProcessor
from app.processor.union_manage_processor import UnionManageProcessor
from app.processor.union_aid_processor import UnionAidProcessor
from app.processor.union_battle_processor import UnionBattleProcessor
from app.processor.union_battle_assist_processor import UnionBattleAssistProcessor
from app.processor.chat_processor import ChatProcessor
from app.processor.common_processor import CommonProcessor
from app.processor.chest_process import ChestProcessor
from app.processor.trainer_process import TrainerProcessor
from app.processor.anneal_process import AnnealProcessor
from app.processor.basic_process import BasicProcessor
from app.processor.herostar_process import HeroStarProcessor
from app.processor.union_donate_processor import UnionDonateProcessor
from app.processor.worldboss_process import WorldBossProcessor
from app.processor.exchange_process import ExchangeProcessor
from app.processor.union_boss_processor import UnionBossProcessor
from app.processor.expand_dungeon_processor import ExpandDungeonProcessor
from app.processor.speed_process import SpeedProcessor
from app.processor.transfer_processor import TransferProcessor
from app.processor.plunder_processor import PlunderProcessor
from app.processor.friend_process import FriendProcessor

from app.guard_process import GuardProcessor
from app.mission_process import MissionProcessor
from app.ranking_process import RankingProcessor
from app.equipment_process import EquipmentProcess
from app.mail_process import MailProcessor
from app.battle_process import BattleProcessor
from app.exploit_process import ExploitationProcessor


_account_processor = AccountProcessor()

@rootserviceHandle
def user_init(user_id, data):
    """初始化用户数据"""
    return _account_processor.init(user_id, data)

@rootserviceHandle
def user_delete(user_id, data):
    """删除用户数据"""
    return _account_processor.delete(user_id, data)

@rootserviceHandle
def clear_cache(user_id, data):
    """清除用户数据缓存"""
    return _account_processor.clear_cache(user_id, data)

@rootserviceHandle
def clear_users_cache(user_id, data):
    """清除用户数据缓存"""
    return _account_processor.clear_users_cache(user_id, data)


@rootserviceHandle
def get_all(user_id, data):
    """获取所有玩家 user id"""
    return _account_processor.get_all(user_id, data)

@rootserviceHandle
def get_user_basic_info(user_id, data):
    """获取用户基本信息"""
    return _account_processor.basic_info(user_id, data)

@rootserviceHandle
def update_user_basic_info(user_id, data):
    """更新用户基本信息"""
    return _account_processor.update_basic_info(user_id, data)

@rootserviceHandle
def update_user_info_offline(user_id, data):
    """离线更新用户的数据（如资源重算）"""
    return _account_processor.update_user_info_offline(user_id, data)

@rootserviceHandle
def receive_update_user_info_offline(user_id, data):
    """接收离线更新用户的数据"""
    return _account_processor.receive_update_user_info_offline(user_id, data)

@rootserviceHandle
def delete_inactivity_user(user_id, data):
    return _account_processor.delete_inactivity_user(user_id, data)

_user_processor = UserProcessor()

@rootserviceHandle
def user_update_name(user_id, data):
    return _user_processor.update_name(user_id, data)

@rootserviceHandle
def user_update_icon(user_id, data):
    return _user_processor.update_icon(user_id, data)

@rootserviceHandle
def forward_guide(user_id, data):
    return _user_processor.forward_guide(user_id, data)

@rootserviceHandle
def manage_guide(user_id, data):
    return _user_processor.manage_guide(user_id, data)

@rootserviceHandle
def add_vip_points(user_id, data):
    return _user_processor.add_vip_points(user_id, data)

@rootserviceHandle
def be_invited(user_id, data):
    return _user_processor.be_invited(user_id, data)

@rootserviceHandle
def receive_from_invitee(user_id, data):
    return _user_processor.receive_from_invitee(user_id, data)

@rootserviceHandle
def receive_invitee_upgrade(user_id, data):
    return _user_processor.receive_invitee_upgrade(user_id, data)

@rootserviceHandle
def query_suggested_country(user_id, data):
    return _user_processor.query_suggested_country(user_id, data)

@rootserviceHandle
def update_country(user_id, data):
    return _user_processor.update_country(user_id, data)


_chat_processor = ChatProcessor()
@rootserviceHandle
def start_chat(user_id, data):
    return _chat_processor.start_chat(user_id, data)

@rootserviceHandle
def manage_chat(user_id, data):
    return _chat_processor.manage(user_id, data)

@rootserviceHandle
def receive_chat_operation(user_id, data):
    return _chat_processor.receive_operation(user_id, data)


_cdkey_processor = CDkeyProcessor()
@rootserviceHandle
def use_cdkey(user_id, data):
    return _cdkey_processor.use_cdkey(user_id, data)


_hero_processor = HeroProcessor()

@rootserviceHandle
def add_hero(user_id, data):
    return _hero_processor.add_hero(user_id, data)

@rootserviceHandle
def upgrade_hero_level(user_id, data):
    return _hero_processor.upgrade_level(user_id, data)

@rootserviceHandle
def upgrade_hero_star(user_id, data):
    return _hero_processor.upgrade_star(user_id, data)

@rootserviceHandle
def upgrade_hero_skill(user_id, data):
    return _hero_processor.upgrade_skill(user_id, data)

@rootserviceHandle
def update_hero_soldier(user_id, data):
    return _hero_processor.update_soldier(user_id, data)

@rootserviceHandle
def update_garrison_hero_exp(user_id, data):
    return _hero_processor.update_garrison_hero_exp(user_id, data)

@rootserviceHandle
def upgrade_hero_evolution_level(user_id, data):
    return _hero_processor.upgrade_evolution_level(user_id, data)

@rootserviceHandle
def reborn_hero(user_id, data):
    return _hero_processor.reborn(user_id, data)

@rootserviceHandle
def awaken_hero(user_id, data):
    return _hero_processor.awaken(user_id, data)

@rootserviceHandle
def refine_hero(user_id, data):
    return _hero_processor.refine(user_id, data)

@rootserviceHandle
def refine_hero_upgrade(user_id, data):
    return _hero_processor.refine_upgrade(user_id, data)

_guard_processor = GuardProcessor()

@rootserviceHandle
def update_defense_team(user_id, data):
    return _guard_processor.update_team(user_id, data)


_shop_processor = ShopProcessor()

@rootserviceHandle
def seek_goods(user_id, data):
    return _shop_processor.seek_normal_goods(user_id, data)

@rootserviceHandle
def refresh_goods(user_id, data):
    return _shop_processor.refresh_normal_goods(user_id, data)

@rootserviceHandle
def buy_goods(user_id, data):
    return _shop_processor.buy_goods(user_id, data)

@rootserviceHandle
def seek_achievement_goods(user_id, data):
    return _shop_processor.seek_achievement_goods(user_id, data)

@rootserviceHandle
def refresh_achievement_goods(user_id, data):
    return _shop_processor.refresh_achievement_goods(user_id, data)

@rootserviceHandle
def seek_arena_goods(user_id, data):
    return _shop_processor.seek_arena_goods(user_id, data)

@rootserviceHandle
def refresh_arena_goods(user_id, data):
    return _shop_processor.refresh_arena_goods(user_id, data)

@rootserviceHandle
def seek_legend_city_goods(user_id, data):
    return _shop_processor.seek_legendcity_goods(user_id, data)

@rootserviceHandle
def refresh_legend_city_goods(user_id, data):
    return _shop_processor.refresh_legendcity_goods(user_id, data)

@rootserviceHandle
def buy_legend_city_goods(user_id, data):
    return _shop_processor.buy_legendcity_goods(user_id, data)

@rootserviceHandle
def seek_soul_goods(user_id, data):
    return _shop_processor.seek_soul_goods(user_id, data)

@rootserviceHandle
def refresh_soul_goods(user_id, data):
    return _shop_processor.refresh_soul_goods(user_id, data)

@rootserviceHandle
def seek_gold_goods(user_id, data):
    return _shop_processor.seek_gold_goods(user_id, data)


_union_shop_processor = UnionShopProcessor()

@rootserviceHandle
def seek_union_goods(user_id, data):
    return _union_shop_processor.seek_goods(user_id, data)

@rootserviceHandle
def refresh_union_goods(user_id, data):
    return _union_shop_processor.refresh_goods(user_id, data)

@rootserviceHandle
def buy_union_goods(user_id, data):
    return _union_shop_processor.buy_goods(user_id, data)


_draw_processor = DrawProcessor()


@rootserviceHandle
def get_draw_status(user_id, data):
    return _draw_processor.get_draw_status(user_id, data)

@rootserviceHandle
def multi_draw_with_money(user_id, data):
    return _draw_processor.multi_draw_with_money(user_id, data)

@rootserviceHandle
def draw_with_money(user_id, data):
    return _draw_processor.draw_with_money(user_id, data)

@rootserviceHandle
def multi_draw_with_gold(user_id, data):
    return _draw_processor.multi_draw_with_gold(user_id, data)

@rootserviceHandle
def draw_with_gold(user_id, data):
    return _draw_processor.draw_with_gold(user_id, data)

@rootserviceHandle
def treasure_draw(user_id, data):
    return _draw_processor.treasure_draw(user_id, data)


_item_processor = ItemProcessor()

@rootserviceHandle
def use_herolist(user_id, data):
    return _item_processor.use_herolist(user_id, data)

@rootserviceHandle
def sell_item(user_id, data):
    return _item_processor.sell_item(user_id, data)

@rootserviceHandle
def create_hero_from_starsoul(user_id, data):
    return _item_processor.create_hero_from_starsoul(user_id, data)

@rootserviceHandle
def add_item(user_id, data):
    return _item_processor.add_item(user_id, data)

@rootserviceHandle
def use_resource_package(user_id, data):
    return _item_processor.use_resource_package(user_id, data)

@rootserviceHandle
def resolve_starsoul(user_id, data):
    return _item_processor.resolve_starsoul(user_id, data)

@rootserviceHandle
def use_item(user_id, data):
    return _item_processor.use_item(user_id, data)

@rootserviceHandle
def use_monarch_exp(user_id, data):
    return _item_processor.use_monarch_exp(user_id, data)

@rootserviceHandle
def compose_item(user_id, data):
    return _item_processor.compose_item(user_id, data)

@rootserviceHandle
def casting_item(user_id, data):
    return _item_processor.casting_item(user_id, data)


_speed_processor = SpeedProcessor()

@rootserviceHandle
def use_speed_item(user_id, data):
    return _speed_processor.use_speed_item(user_id, data)


_building_processor = BuildingProcessor()

@rootserviceHandle
def start_create_building(user_id, data):
    return _building_processor.start_create(user_id, data)

@rootserviceHandle
def start_upgrade_building(user_id, data):
    return _building_processor.start_upgrade(user_id, data)

@rootserviceHandle
def finish_upgrade_building(user_id, data):
    return _building_processor.finish_upgrade(user_id, data)

@rootserviceHandle
def complete_upgrade_building(user_id, data):
    return _building_processor.finish_upgrade(user_id, data, force = True)

@rootserviceHandle
def cancel_upgrade_building(user_id, data):
    return _building_processor.cancel_upgrade(user_id, data)

@rootserviceHandle
def update_garrison_hero(user_id, data):
    return _building_processor.update_garrison_hero(user_id, data)


_technology_processor = TechnologyProcessor()

@rootserviceHandle
def start_research_battle_technology(user_id, data):
    return _technology_processor.start_research(user_id, data)

@rootserviceHandle
def finish_research_battle_technology(user_id, data):
    return _technology_processor.finish_research(user_id, data)

@rootserviceHandle
def finish_research_battle_with_gold(user_id, data):
    return _technology_processor.finish_research(user_id, data, force = True)

@rootserviceHandle
def cancel_research_battle_technology(user_id, data):
    return _technology_processor.cancel_research(user_id, data)

@rootserviceHandle
def start_research_interior_technology(user_id, data):
    return _technology_processor.start_research(user_id, data)

@rootserviceHandle
def finish_research_interior_technology(user_id, data):
    return _technology_processor.finish_research(user_id, data)

@rootserviceHandle
def finish_research_interior_with_gold(user_id, data):
    return _technology_processor.finish_research(user_id, data, force = True)

@rootserviceHandle
def cancel_research_interior_technology(user_id, data):
    return _technology_processor.cancel_research(user_id, data)

@rootserviceHandle
def start_research_soldier_technology(user_id, data):
    return _technology_processor.start_research(user_id, data)

@rootserviceHandle
def finish_research_soldier_technology(user_id, data):
    return _technology_processor.finish_research(user_id, data)

@rootserviceHandle
def finish_research_soldier_with_gold(user_id, data):
    return _technology_processor.finish_research(user_id, data, force = True)

@rootserviceHandle
def cancel_research_soldier_technology(user_id, data):
    return _technology_processor.cancel_research(user_id, data)


_resource_processor = ResourceProcessor()

@rootserviceHandle
def exchange(user_id, data):
    return _resource_processor.exchange(user_id, data)

@rootserviceHandle
def add_resource(user_id, data):
    return _resource_processor.add(user_id, data)

@rootserviceHandle
def recalc_resource(user_id, data):
    return _resource_processor.recalc(user_id, data)

@rootserviceHandle
def recalc_all_resource(user_id, data):
    return _resource_processor.recalc_all(user_id, data)

_city_processor = CityProcessor()

@rootserviceHandle
def update_city_info(user_id, data):
    return _city_processor.update_city_info(user_id, data)


_conscript_processor = ConscriptProcessor()
@rootserviceHandle
def start_conscript(user_id, data):
    return _conscript_processor.start_conscript(user_id, data)

@rootserviceHandle
def add_conscript(user_id, data):
    return _conscript_processor.add_conscript(user_id, data)

@rootserviceHandle
def end_conscript(user_id, data):
    return _conscript_processor.end_conscript(user_id, data)

@rootserviceHandle
def end_conscript_with_gold(user_id, data):
    return _conscript_processor.end_conscript_with_gold(user_id, data)

@rootserviceHandle
def cancel_conscript(user_id, data):
    return _conscript_processor.cancel_conscript(user_id, data)


_mission_processor = MissionProcessor()
@rootserviceHandle
def finish_mission(user_id, data):
    return _mission_processor.finish_mission(user_id, data)

@rootserviceHandle
def update_last_user_level(user_id, data):
    return _mission_processor.update_last_user_level(user_id, data)

_ranking_processor = RankingProcessor()
@rootserviceHandle
def query_ranking(user_id, data):
    return _ranking_processor.query_ranking(user_id, data)

@rootserviceHandle
def query_ranking_player_powerful_teams(user_id, data):
    return _ranking_processor.query_ranking_player_powerful_teams(user_id, data)


_equipment_processor = EquipmentProcess()
@rootserviceHandle
def upgrade_hero_equipment(user_id, data):
    return _equipment_processor.upgrade_equipment(user_id, data)

@rootserviceHandle
def enchant_hero_equipment(user_id, data):
    return _equipment_processor.enchant_equipment(user_id, data)

@rootserviceHandle
def upgrade_hero_equipment_max(user_id, data):
    return _equipment_processor.upgrade_equipment_max(user_id, data)

@rootserviceHandle
def enchant_hero_equipment_max(user_id, data):
    return _equipment_processor.enchant_equipment_max(user_id, data)


@rootserviceHandle
def mount_equipment_stone(user_id, data):
    return _equipment_processor.mount_equipment_stone(user_id, data)

@rootserviceHandle
def demount_equipment_stone(user_id, data):
    return _equipment_processor.demount_equipment_stone(user_id, data)

@rootserviceHandle
def upgrade_equipment_stone(user_id, data):
    return _equipment_processor.upgrade_equipment_stone(user_id, data)


_mail_process = MailProcessor()
@rootserviceHandle
def query_mail(user_id, data):
    return _mail_process.query_mail(user_id, data)

@rootserviceHandle
def read_mail(user_id, data):
    return _mail_process.read_mail(user_id, data)

@rootserviceHandle
def use_mail(user_id, data):
    return _mail_process.use_mail(user_id, data)

@rootserviceHandle
def add_mail(user_id, data):
    return _mail_process.add_mail(user_id, data)

@rootserviceHandle
def receive_mail(user_id, data):
    return _mail_process.receive_mail(user_id, data)


_signin_process = SigninProcessor()
@rootserviceHandle
def signin(user_id, data):
    return _signin_process.signin(user_id, data)

@rootserviceHandle
def signin_custom(user_id, data):
    return _signin_process.signin_custom(user_id, data)


_team_process = TeamProcessor()
@rootserviceHandle
def update_team(user_id, data):
    return _team_process.update(user_id, data)

@rootserviceHandle
def refresh_all_teams(user_id, data):
    return _team_process.refresh_all_teams(user_id, data)

@rootserviceHandle
def receive_refresh_all_teams(user_id, data):
    return _team_process.receive_refresh_all_teams(user_id, data)


_map_process = MapProcessor()
@rootserviceHandle
def trigger_war_event(user_id, data):
    return _map_process.trigger_war_event(user_id, data)

@rootserviceHandle
def trigger_lucky_event(user_id, data):
    return _map_process.trigger_lucky_event(user_id, data)

@rootserviceHandle
def trigger_specified_event(user_id, data):
    return _map_process.trigger_specified_event(user_id, data)

@rootserviceHandle
def trigger_custom_war_event(user_id, data):
    return _map_process.trigger_custom_war_event(user_id, data)

@rootserviceHandle
def trigger_custom_event(user_id, data):
    return _map_process.trigger_custom_event(user_id, data)

@rootserviceHandle
def clear_lucky_event(user_id, data):
    return _map_process.clear_lucky_event(user_id, data)

@rootserviceHandle
def rematch_node(user_id, data):
    return _map_process.rematch_node(user_id, data)

@rootserviceHandle
def abandon_node(user_id, data):
    return _map_process.abandon_node(user_id, data)


_plunder_process = PlunderProcessor()

@rootserviceHandle
def query_pvp_players(user_id, data):
    return _plunder_process.query_pvp_players(user_id, data)

@rootserviceHandle
def query_player_info(user_id, data):
    return _plunder_process.query_player_info(user_id, data)

@rootserviceHandle
def reset_attack_num(user_id, data):
    return _plunder_process.reset_attack_num(user_id, data)


_battle_process = BattleProcessor()

@rootserviceHandle
def start_battle(user_id, data):
    return _battle_process.start_battle(user_id, data)

@rootserviceHandle
def finish_battle(user_id, data):
    return _battle_process.finish_battle(user_id, data)

@rootserviceHandle
def skip_battle(user_id, data):
    return _battle_process.finish_battle(user_id, data)


_notice_processor = NoticeProcessor()
@rootserviceHandle
def receive_battle_notice(user_id, data):
    return _notice_processor.receive_notice(user_id, data)

@rootserviceHandle
def receive_legendcity_battle_notice(user_id, data):
    return _notice_processor.receive_legendcity_notice(user_id, data)


_exploitation_process = ExploitationProcessor()

@rootserviceHandle
def gather(user_id, data):
    return _exploitation_process.gather(user_id, data)

@rootserviceHandle
def start_exploitation(user_id, data):
    return _exploitation_process.start_exploit(user_id, data)

@rootserviceHandle
def finish_exploitation(user_id, data):
    return _exploitation_process.finish_exploit(user_id, data)

@rootserviceHandle
def cancel_exploitation(user_id, data):
    return _exploitation_process.cancel_exploit(user_id, data)


_event_process = EventProcessor()
@rootserviceHandle
def start_visit_event(user_id, data):
    return _event_process.start_visit(user_id, data)

@rootserviceHandle
def search_visit_event(user_id, data):
    return _event_process.search_visit(user_id, data)

@rootserviceHandle
def finish_visit_event(user_id, data):
    return _event_process.finish_visit(user_id, data)

@rootserviceHandle
def start_question_event(user_id, data):
    return _event_process.start_question(user_id, data)

@rootserviceHandle
def finish_question_event(user_id, data):
    return _event_process.finish_question(user_id, data)

@rootserviceHandle
def upgrade_node(user_id, data):
    return _event_process.upgrade(user_id, data)


_appoint_process = AppointProcessor()
@rootserviceHandle
def start_appoint(user_id, data):
    return _appoint_process.start_appoint(user_id, data)

@rootserviceHandle
def finish_appoint(user_id, data):
    return _appoint_process.finish_appoint(user_id, data)


_pay_process = PayProcessor()
@rootserviceHandle
def query_pay(user_id, data):
    return _pay_process.query_pay(user_id, data)

@rootserviceHandle
def start_pay(user_id, data):
    return _pay_process.start_pay(user_id, data)

@rootserviceHandle
def finish_pay(user_id, data):
    return _pay_process.finish_pay(user_id, data)

@rootserviceHandle
def try_finish_pay_outside(user_id, data):
    return _pay_process.try_finish_pay_outside(user_id, data)

@rootserviceHandle
def patch_pay(user_id, data):
    return _pay_process.patch_pay(user_id, data)


_activity_process = ActivityProcessor()
@rootserviceHandle
def query_activity(user_id, data):
    return _activity_process.query_activity(user_id, data)

@rootserviceHandle
def accept_activity_reward(user_id, data):
    return _activity_process.accept_activity_reward(user_id, data)

@rootserviceHandle
def operate_activity(user_id, data):
    return _activity_process.operate_activity(user_id, data)

@rootserviceHandle
def add_activity(user_id, data):
    return _activity_process.add_activity(user_id, data)

@rootserviceHandle
def receive_activity_invitation(user_id, data):
    return _activity_process.receive_activity_invitation(user_id, data)

@rootserviceHandle
def award_activity_hero(user_id, data):
    return _activity_process.award_activity_hero(user_id, data)

@rootserviceHandle
def clear_activity_hero_scores(user_id, data):
    return _activity_process.clear_activity_hero_scores(user_id, data)

@rootserviceHandle
def receive_clear_activity_hero_scores(user_id, data):
    return _activity_process.receive_clear_activity_hero_scores(user_id, data)

@rootserviceHandle
def fortune_cat(user_id, data):
    return _activity_process.fortune_cat(user_id, data)

_basic_process = BasicProcessor()
@rootserviceHandle
def add_init_basic_activity(user_id, data):
    return _basic_process.add_init_basic_activity(user_id, data)

@rootserviceHandle
def delete_init_basic_activity(user_id, data):
    return _basic_process.delete_init_basic_activity(user_id, data)

@rootserviceHandle
def query_init_basic_activity(user_id, data):
    return _basic_process.query_init_basic_activity(user_id, data)

@rootserviceHandle
def add_basic_activity(user_id, data):
    return _basic_process.add_basic_activity(user_id, data)

@rootserviceHandle
def delete_basic_activity(user_id, data):
    return _basic_process.delete_basic_activity(user_id, data)

@rootserviceHandle
def query_basic_activity(user_id, data):
    return _basic_process.query_basic_activity(user_id, data)

@rootserviceHandle
def add_basic_activity_step(user_id, data):
    return _basic_process.add_basic_activity_step(user_id, data)

@rootserviceHandle
def delete_basic_activity_step(user_id, data):
    return _basic_process.delete_basic_activity_step(user_id, data)

@rootserviceHandle
def query_basic_activity_step(user_id, data):
    return _basic_process.query_basic_activity_step(user_id, data)

@rootserviceHandle
def add_basic_activity_hero_reward(user_id, data):
    return _basic_process.add_basic_activity_hero_reward(user_id, data)

@rootserviceHandle
def add_basic_activity_treasure_reward(user_id, data):
    return _basic_process.add_basic_activity_treasure_reward(user_id, data)

@rootserviceHandle
def delete_basic_activity_hero_reward(user_id, data):
    return _basic_process.delete_basic_activity_hero_reward(user_id, data)

@rootserviceHandle
def query_basic_activity_hero_reward(user_id, data):
    return _basic_process.query_basic_activity_hero_reward(user_id, data)

@rootserviceHandle
def delete_basic_info(user_id, data):
    return _basic_process.delete_basic_info(user_id, data)

@rootserviceHandle
def add_basic_worldboss(user_id, data):
    return _basic_process.add_basic_worldboss(user_id, data)

@rootserviceHandle
def delete_basic_worldboss(user_id, data):
    return _basic_process.delete_basic_worldboss(user_id, data)

@rootserviceHandle
def query_basic_worldboss(user_id, data):
    return _basic_process.query_basic_worldboss(user_id, data)


_arena_process = ArenaProcessor()
@rootserviceHandle
def query_arena(user_id, data):
    return _arena_process.query_arena(user_id, data)


@rootserviceHandle
def refresh_arena(user_id, data):
    return _arena_process.refresh_arena(user_id, data)


@rootserviceHandle
def update_arena(user_id, data):
    return _arena_process.update_arena(user_id, data)


@rootserviceHandle
def query_arena_ranking(user_id, data):
    return _arena_process.query_arena_ranking(user_id, data)


@rootserviceHandle
def get_arena_win_num_reward(user_id, data):
    return _arena_process.get_arena_win_num_reward(user_id, data)


@rootserviceHandle
def receive_arena_notice(user_id, data):
    return _arena_process.receive_notice(user_id, data)


@rootserviceHandle
def update_arena_offline(user_id, data):
    return _arena_process.update_arena_offline(user_id, data)


@rootserviceHandle
def receive_update_arena_offline(user_id, data):
    return _arena_process.receive_update_arena_offline(user_id, data)


@rootserviceHandle
def add_arena_coin(user_id, data):
    return _arena_process.add_arena_coin(user_id, data)


_melee_process = MeleeProcessor()
@rootserviceHandle
def query_melee(user_id, data):
    return _melee_process.query_melee(user_id, data)


@rootserviceHandle
def refresh_melee(user_id, data):
    return _melee_process.refresh_melee(user_id, data)


@rootserviceHandle
def update_melee(user_id, data):
    return _melee_process.update_melee(user_id, data)


@rootserviceHandle
def query_melee_ranking(user_id, data):
    return _melee_process.query_melee_ranking(user_id, data)


@rootserviceHandle
def get_melee_win_num_reward(user_id, data):
    return _melee_process.get_melee_win_num_reward(user_id, data)


@rootserviceHandle
def receive_melee_notice(user_id, data):
    return _melee_process.receive_notice(user_id, data)


_protection_process = ProtectionProcessor()
@rootserviceHandle
def protect(user_id, data):
    return _protection_process.protect(user_id, data)


_increase_process = IncreaseProcessor()
@rootserviceHandle
def increase(user_id, data):
    return _increase_process.increase(user_id, data)


_legendcity_processor = LegendCityProcessor()
@rootserviceHandle
def query_legend_city_info(user_id, data):
    return _legendcity_processor.query(user_id, data)

@rootserviceHandle
def update_legend_city_info(user_id, data):
    return _legendcity_processor.update(user_id, data)

@rootserviceHandle
def reset_legend_city_attack_info(user_id, data):
    return _legendcity_processor.reset_attack_info(user_id, data)

@rootserviceHandle
def buy_legend_city_buff(user_id, data):
    return _legendcity_processor.buy_buff(user_id, data)



@rootserviceHandle
def query_legend_city_rival(user_id, data):
    return _legendcity_processor.query_rival(user_id, data)

@rootserviceHandle
def add_reputation(user_id, data):
    return _legendcity_processor.add_reputation(user_id, data)

@rootserviceHandle
def delete_legend_city(user_id, data):
    return _legendcity_processor.delete_legend_city(user_id, data)

@rootserviceHandle
def award_legend_city(user_id, data):
    return _legendcity_processor.award_legend_city(user_id, data)

@rootserviceHandle
def get_legendcity_position_rank(user_id, data):
    return _legendcity_processor.get_position_rank(user_id, data)


_energy_process = EnergyProcessor()
@rootserviceHandle
def buy_energy(user_id, data):
    return _energy_process.buy_energy(user_id, data)

@rootserviceHandle
def refresh_energy(user_id, data):
    return _energy_process.refresh_energy(user_id, data)


_pray_process = PrayProcessor()
@rootserviceHandle
def pray(user_id, data):
    return _pray_process.pray(user_id, data)

@rootserviceHandle
def choose_card(user_id, data):
    return _pray_process.choose_card(user_id, data)

@rootserviceHandle
def refresh_pray(user_id, data):
    return _pray_process.refresh_pray(user_id, data)

@rootserviceHandle
def giveup_pray(user_id, data):
    return _pray_process.giveup_pray(user_id, data)


_union_processor = UnionProcessor()
@rootserviceHandle
def query_union(user_id, data):
    return _union_processor.query(user_id, data)

@rootserviceHandle
def query_union_force(user_id, data):
    return _union_processor.query(user_id, data, True)

@rootserviceHandle
def search_union(user_id, data):
    return _union_processor.search(user_id, data)

@rootserviceHandle
def create_union(user_id, data):
    return _union_processor.create(user_id, data)

@rootserviceHandle
def update_union(user_id, data):
    return _union_processor.update(user_id, data)

@rootserviceHandle
def delete_union(user_id, data):
    return _union_processor.delete(user_id, data)

@rootserviceHandle
def try_transfer_union_leader(user_id, data):
    return _union_processor.try_transfer(user_id, data)

_union_manage_processor = UnionManageProcessor()
@rootserviceHandle
def join_union(user_id, data):
    return _union_manage_processor.join(user_id, data)

@rootserviceHandle
def approve_union(user_id, data):
    return _union_manage_processor.approve(user_id, data)

@rootserviceHandle
def manage_union(user_id, data):
    return _union_manage_processor.manage(user_id, data)

@rootserviceHandle
def been_kickout_from_union(user_id, data):
    return _union_manage_processor.been_kickout(user_id, data)

@rootserviceHandle
def been_accept_by_union(user_id, data):
    return _union_manage_processor.been_accept(user_id, data)

@rootserviceHandle
def query_union_member(user_id, data):
    return _union_manage_processor.query_member(user_id, data)

@rootserviceHandle
def add_union_honor(user_id, data):
    return _union_manage_processor.add_honor(user_id, data)


_union_aid_processor = UnionAidProcessor()
@rootserviceHandle
def query_union_aid(user_id, data):
    return _union_aid_processor.query_aid(user_id, data)

@rootserviceHandle
def start_union_aid(user_id, data):
    return _union_aid_processor.start_aid(user_id, data)

@rootserviceHandle
def finish_union_aid(user_id, data):
    return _union_aid_processor.finish_aid(user_id, data)

@rootserviceHandle
def respond_union_aid(user_id, data):
    return _union_aid_processor.respond_aid(user_id, data)


_union_battle_processor = UnionBattleProcessor()
@rootserviceHandle
def query_union_battle(user_id, data):
    """查询联盟战争信息
    """
    return _union_battle_processor.query(user_id, data)

@rootserviceHandle
def launch_union_battle(user_id, data):
    """发起联盟战争
    """
    return _union_battle_processor.launch(user_id, data)

@rootserviceHandle
def launch_union_battle_force(user_id, data):
    """发起联盟战争(可由联盟外成员强制发起)
    """
    return _union_battle_processor.launch(user_id, data, True)

@rootserviceHandle
def launch_two_union_battle(user_id, data):
    """发起两个指定联盟的战争
    """
    return _union_battle_processor.launch_two(user_id, data)

@rootserviceHandle
def deploy_union_battle(user_id, data):
    """部署联盟战争防御
    """
    return _union_battle_processor.deploy(user_id, data)


@rootserviceHandle
def deploy_union_battle_force(user_id, data):
    """指定部署联盟战争防御
    """
    return _union_battle_processor.deploy_force(user_id, data)


@rootserviceHandle
def receive_deploy_union_battle_force(user_id, data):
    """指定部署联盟战争防御
    """
    return _union_battle_processor.receive_deploy_force(user_id, data)


@rootserviceHandle
def cancel_deploy_union_battle(user_id, data):
    """清除联盟战争防御
    """
    return _union_battle_processor.cancel_deploy(user_id, data)

@rootserviceHandle
def drum_for_union_battle(user_id, data):
    """联盟战争中擂鼓
    """
    return _union_battle_processor.drum(user_id, data)

@rootserviceHandle
def start_union_battle(user_id, data):
    """开始联盟战斗
    """
    return _union_battle_processor.start(user_id, data)

@rootserviceHandle
def finish_union_battle(user_id, data):
    """结束联盟战斗
    """
    return _union_battle_processor.finish(user_id, data)

@rootserviceHandle
def skip_union_battle(user_id, data):
    """结束联盟战斗
    """
    return _union_battle_processor.finish(user_id, data)


@rootserviceHandle
def accept_union_battle_node_box_reward(user_id, data):
    return _union_battle_processor.battle_node_reward(user_id, data)


@rootserviceHandle
def accept_union_battle_box(user_id, data):
    """领取联盟战的宝箱
    """
    return _union_battle_processor.accept_union_battle_box(user_id, data)


_union_battle_assist_processor = UnionBattleAssistProcessor()
@rootserviceHandle
def refresh_union_battle_attack(user_id, data):
    """刷新联盟战争个人攻击次数
    """
    return _union_battle_assist_processor.refresh_attack(user_id, data)

@rootserviceHandle
def query_union_battle_individuals(user_id, data):
    """查询联盟战争个人信息
    """
    return _union_battle_assist_processor.query_individuals(user_id, data)

@rootserviceHandle
def accept_union_battle_individual_step_award(user_id, data):
    """领取个人战功阶段奖励
    """
    return _union_battle_assist_processor.accept_individual_step_award(user_id, data)

@rootserviceHandle
def gain_union_battle_individual_score(user_id, data):
    """添加个人联盟战功
    """
    return _union_battle_assist_processor.gain_battle_individual_score(user_id, data)

@rootserviceHandle
def gain_union_battle_score(user_id, data):
    """添加联盟胜场积分
    """
    return _union_battle_assist_processor.gain_battle_score(user_id, data)

@rootserviceHandle
def force_update_union_battle(user_id, data):
    """强制更新联盟战争信息
    """
    return _union_battle_assist_processor.force_update(user_id, data)

@rootserviceHandle
def try_forward_union_battle_season(user_id, data):
    """尝试进入下一个联盟赛季
    """
    return _union_battle_assist_processor.try_forward_season(user_id, data)


@rootserviceHandle
def try_forward_union_battle(user_id, data):
    """尝试进入下一场联盟战争
    """
    return _union_battle_assist_processor.try_forward_battle(user_id, data)


@rootserviceHandle
def forward_union_battle_season(user_id, data):
    """进入下一个联盟赛季
    """
    return _union_battle_assist_processor.forward_season(user_id, data)


@rootserviceHandle
def forward_union_battle(user_id, data):
    """进入下一场联盟战争
    """
    return _union_battle_assist_processor.forward_battle(user_id, data)


@rootserviceHandle
def award_for_union_battle(user_id, data):
    """发放联盟战争奖励
    """
    return _union_battle_assist_processor.award(user_id, data)

_union_boss_processor = UnionBossProcessor()

@rootserviceHandle
def query_unionboss(user_id, data):
    return _union_boss_processor.query(user_id, data)

@rootserviceHandle
def start_unionboss_battle(user_id, data):
    return _union_boss_processor.start_battle(user_id, data)

@rootserviceHandle
def finish_unionboss_battle(user_id, data):
    return _union_boss_processor.finish_battle(user_id, data)

@rootserviceHandle
def accept_unionboss_score_reward(user_id, data):
    return _union_boss_processor.score_reward(user_id, data)

@rootserviceHandle
def accept_unionboss_box_reward(user_id, data):
    return _union_boss_processor.boss_reward(user_id, data)

@rootserviceHandle
def query_unionboss_box_reward(user_id, data):
    return _union_boss_processor.query_boss_reward(user_id, data)

@rootserviceHandle
def reset_unionboss_attack_num(user_id, data):
    return _union_boss_processor.reset(user_id, data)

@rootserviceHandle
def add_basic_unionboss(user_id, data):
    return _union_boss_processor.add(user_id, data)

'''
@rootserviceHandle
def update_unionboss(user_id, data):
    return _union_boss_processor.update(user_id, data)
'''

_common_process = CommonProcessor()
@rootserviceHandle
def query_notice(user_id, data):
    return _common_process.query_notice(user_id, data)


@rootserviceHandle
def add_notice(user_id, data):
    return _common_process.add_notice(user_id, data)


@rootserviceHandle
def delete_notice(user_id, data):
    return _common_process.delete_notice(user_id, data)


@rootserviceHandle
def delete_common(user_id, data):
    return _common_process.delete_common(user_id, data)


_chest_process = ChestProcessor()
@rootserviceHandle
def open_chest(user_id, data):
    return _chest_process.open_chest(user_id, data)


@rootserviceHandle
def query_chest(user_id, data):
    return _chest_process.query_chest(user_id, data)


_trainer_process = TrainerProcessor()
@rootserviceHandle
def add_kill_enemy_num(user_id, data):
    return _trainer_process.add_kill_enemy_num(user_id, data)


_anneal_process = AnnealProcessor()
@rootserviceHandle
def query_anneal(user_id, data):
    return _anneal_process.query_anneal(user_id, data)


@rootserviceHandle
def get_pass_reward(user_id, data):
    return _anneal_process.get_pass_reward(user_id, data)


@rootserviceHandle
def buy_attack_num(user_id, data):
    return _anneal_process.buy_attack_num(user_id, data)


@rootserviceHandle
def start_sweep(user_id, data):
    return _anneal_process.start_sweep(user_id, data)


@rootserviceHandle
def finish_sweep(user_id, data):
    return _anneal_process.finish_sweep(user_id, data)


@rootserviceHandle
def query_anneal_record(user_id, data):
    return _anneal_process.query_anneal_record(user_id, data)


@rootserviceHandle
def modify_anneal_progress(user_id, data):
    return _anneal_process.modify_anneal_progress(user_id, data)


@rootserviceHandle
def modify_anneal_sweep_time(user_id, data):
    return _anneal_process.modify_anneal_sweep_time(user_id, data)

@rootserviceHandle
def reset_anneal_hard_attack_num(user_id, data):
    return _anneal_process.reset_hard_attack_num(user_id, data)


_herostar_processor = HeroStarProcessor()
@rootserviceHandle
def strength_herostar(user_id, data):
    return _herostar_processor.strength(user_id, data)

@rootserviceHandle
def wear_herostar(user_id, data):
    return _herostar_processor.wear(user_id, data)

@rootserviceHandle
def unload_herostar(user_id, data):
    return _herostar_processor.unload(user_id, data)


_worldboss_process = WorldBossProcessor()
@rootserviceHandle
def query_worldboss(user_id, data):
    return _worldboss_process.query_worldboss(user_id, data)


@rootserviceHandle
def query_worldboss_soldier_num(user_id, data):
    return _worldboss_process.query_worldboss_soldier_num(user_id, data)


@rootserviceHandle
def modify_common_worldboss(user_id, data):
    return _worldboss_process.modify_common_worldboss(user_id, data)


@rootserviceHandle
def clear_worldboss_merit(user_id, data):
    return _worldboss_process.clear_worldboss_merit(user_id, data)


@rootserviceHandle
def receive_clear_worldboss_merit(user_id, data):
    return _worldboss_process.receive_clear_worldboss_merit(user_id, data)


_union_donate_processor = UnionDonateProcessor()
@rootserviceHandle
def query_union_donate(user_id, data):
    return _union_donate_processor.query(user_id, data)

@rootserviceHandle
def initiate_union_donate(user_id, data):
    return _union_donate_processor.initiate(user_id, data)

@rootserviceHandle
def start_union_donate(user_id, data):
    return _union_donate_processor.start(user_id, data)

@rootserviceHandle
def reward_union_donate(user_id, data):
    return _union_donate_processor.reward(user_id, data)

@rootserviceHandle
def refresh_union_donate_box(user_id, data):
    return _union_donate_processor.refresh(user_id, data)

@rootserviceHandle
def clear_union_donate_coldtime(user_id, data):
    return _union_donate_processor.clear(user_id, data)

_exchange_processor = ExchangeProcessor()
@rootserviceHandle
def query_exchange(user_id, data):
    return _exchange_processor.query(user_id, data)

@rootserviceHandle
def do_exchange(user_id, data):
    return _exchange_processor.exchange(user_id, data)

_expand_dungeon = ExpandDungeonProcessor()

@rootserviceHandle
def query_expand_dungeon(user_id, data):
    return _expand_dungeon.query(user_id, data)

@rootserviceHandle
def reset_expand_dungeon(user_id, data):
    return _expand_dungeon.reset(user_id, data)

_transfer_processor = TransferProcessor()
@rootserviceHandle
def query_transfer_arena(user_id, data):
    return _transfer_processor.query(user_id, data)

@rootserviceHandle
def buy_transfer_challenge_times(user_id, data):
    return _transfer_processor.buy(user_id, data)

@rootserviceHandle
def reset_transfer_cd(user_id, data):
    return _transfer_processor.reset(user_id, data)

@rootserviceHandle
def start_transfer_battle(user_id, data):
    return _transfer_processor.start_battle(user_id, data)

@rootserviceHandle
def finish_transfer_battle(user_id, data):
    return _transfer_processor.finish_battle(user_id, data)

@rootserviceHandle
def receive_transfer_notice(user_id, data):
    return _transfer_processor.receive(user_id, data)
    
@rootserviceHandle
def award_transfer(user_id, data):
    return _transfer_processor.award(user_id, data)

@rootserviceHandle
def receive_transfer_reward(user_id, data):
    return _transfer_processor.reward(user_id, data)

_friend_processor = FriendProcessor()
@rootserviceHandle
def get_friends(user_id, data):
    return _friend_processor.get_friends(user_id, data)

@rootserviceHandle
def view_apply(user_id, data):
    return _friend_processor.view_apply(user_id, data)

@rootserviceHandle
def view_friend(user_id, data):
    return _friend_processor.view_friend(user_id, data)

@rootserviceHandle
def add_friend(user_id, data):
    return _friend_processor.add_friend(user_id, data)
@rootserviceHandle
def receive_friend(user_id, data):
    return _friend_processor.receive_friend(user_id, data)
@rootserviceHandle
def receive_accept_friend(user_id, data):
    return _friend_processor.receive_accept_friend(user_id, data)
@rootserviceHandle
def manage_friend(user_id, data):
    return _friend_processor.manage_friend(user_id, data)
@rootserviceHandle
def chat_friend(user_id, data):
    return _friend_processor.chat_friend(user_id, data)
@rootserviceHandle
def receive_chat_res(user_id, data):
    return _friend_processor.receive_chat_res(user_id, data)

@rootserviceHandle
def refresh_chat(user_id, data):
    return _friend_processor.refresh_chat(user_id, data)
