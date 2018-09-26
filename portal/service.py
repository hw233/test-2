#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Portal 模块提供的服务
"""

from firefly.server.globalobject import GlobalObject
from firefly.server.globalobject import masterserviceHandle
from utils import logger
from portal.command import netserviceHandle
from portal.online_manager import OnlineManager
from proto import init_pb2


# @masterserviceHandle
# def clear_cache():
#     """清除不在线上的玩家的缓存数据
#     """
#     logger.debug("clear cache")
#     id_list = OnlineManager().get_all_inactive_user_id()
#     for user_id in id_list:
#         defer = GlobalObject().remote['app'].callRemote("clear_cache", user_id, "")
#         defer.addCallback(_clear_ok)
#         return defer
#     return True



@netserviceHandle
def user_init(command_id, seq_id, user_id, conn, data):
    """返回用户数据"""
    logger.debug("user init[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("user_init", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def user_delete(command_id, seq_id, user_id, conn, data):
    """删除用户数据"""
    logger.debug("user delete[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("user_delete", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def delete_inactivity_user(command_id, seq_id, user_id, conn, data):
    """删除用户数据"""
    logger.debug("delete inactivity user[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("delete_inactivity_user", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_user_info_offline(command_id, seq_id, user_id, conn, data):
    logger.debug("update_user_info_offline[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_user_info_offline", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def clear_cache(command_id, seq_id, user_id, conn, data):
    """清除用户数据缓存"""
    logger.debug("clear cache[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("clear_cache", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def clear_users_cache(command_id, seq_id, user_id, conn, data):
    """清除用户数据缓存"""
    logger.debug("clear users cache[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("clear_users_cache", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def user_update_name(command_id, seq_id, user_id, conn, data):
    """修改主公姓名"""
    logger.debug("user update name[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("user_update_name", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def user_update_icon(command_id, seq_id, user_id, conn, data):
    """修改主公头像"""
    logger.debug("user update icon[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("user_update_icon", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def be_invited(command_id, seq_id, user_id, conn, data):
    """被邀请"""
    logger.debug("Be invited[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("be_invited", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def forward_guide(command_id, seq_id, user_id, conn, data):
    """新手引导进度前进"""
    logger.debug("forward guide[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("forward_guide", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def manage_guide(command_id, seq_id, user_id, conn, data):
    """管理新手引导进度"""
    logger.debug("manage guide[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("manage_guide", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_chat(command_id, seq_id, user_id, conn, data):
    """开始聊天"""
    logger.debug("start chat[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_chat", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def manage_chat(command_id, seq_id, user_id, conn, data):
    """管理聊天"""
    logger.debug("manage_chat[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("manage_chat", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_suggested_country(command_id, seq_id, user_id, conn, data):
    """查询推荐的国家"""
    logger.debug("query_suggested_country[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_suggested_country", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_country(command_id, seq_id, user_id, conn, data):
    """查询推荐的国家"""
    logger.debug("update_country[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_country", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_hero(command_id, seq_id, user_id, conn, data):
    logger.debug("add hero[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_hero", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def upgrade_hero_level(command_id, seq_id, user_id, conn, data):
    logger.debug("upgrade hero level[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_hero_level", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def upgrade_hero_star(command_id, seq_id, user_id, conn, data):
    logger.debug("upgrade hero star[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_hero_star", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def upgrade_hero_skill(command_id, seq_id, user_id, conn, data):
    logger.debug("upgrade hero skill[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_hero_skill", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def update_hero_soldier(command_id, seq_id, user_id, conn, data):
    logger.debug("update hero soldier[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_hero_soldier", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def update_garrison_hero_exp(command_id, seq_id, user_id, conn, data):
    logger.debug("update_garrison_hero_exp[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_garrison_hero_exp", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def upgrade_hero_evolution_level(command_id, seq_id, user_id, conn, data):
    logger.debug("upgrade_hero_evolution_level[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_hero_evolution_level", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def awaken_hero(command_id, seq_id, user_id, conn, data):
    logger.debug("awaken hero[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("awaken_hero", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def refine_hero(command_id, seq_id, user_id, conn, data):
    logger.debug("refine_hero[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refine_hero", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def refine_hero_upgrade(command_id, seq_id, user_id, conn, data):
    logger.debug("refine_hero_upgrade[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refine_hero_upgrade", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def mount_equipment_stone(command_id, seq_id, user_id, conn, data):
    logger.debug("mount_equipment_stone[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("mount_equipment_stone", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def demount_equipment_stone(command_id, seq_id, user_id, conn, data):
    logger.debug("demount_equipment_stone[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("demount_equipment_stone", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def upgrade_equipment_stone(command_id, seq_id, user_id, conn, data):
    logger.debug("upgrade_equipment_stone[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_equipment_stone", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def use_herolist(command_id, seq_id, user_id, conn, data):
    logger.debug("use hero list[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("use_herolist", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def seek_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("seek goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("seek_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def buy_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("buy goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("buy_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def seek_achievement_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("seek achievement goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("seek_achievement_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_achievement_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh achievement goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_achievement_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def seek_arena_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("seek arena goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("seek_arena_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_arena_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh arena goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_arena_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def seek_soul_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("seek soul goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("seek_soul_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def refresh_soul_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh soul goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_soul_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def seek_gold_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("seek gold goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("seek_gold_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def get_draw_status(command_id, seq_id, user_id, conn, data):
    logger.debug("get draw status[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("get_draw_status", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def multi_draw_with_money(command_id, seq_id, user_id, conn, data):
    logger.debug("multi draw with money[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("multi_draw_with_money", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def draw_with_money(command_id, seq_id, user_id, conn, data):
    logger.debug("draw with money[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("draw_with_money", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def multi_draw_with_gold(command_id, seq_id, user_id, conn, data):
    logger.debug("multi draw with gold[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("multi_draw_with_gold", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def draw_with_gold(command_id, seq_id, user_id, conn, data):
    logger.debug("draw with gold[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("draw_with_gold", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def use_resource_package(command_id, seq_id, user_id, conn, data):
    logger.debug("use resource package[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("use_resource_package", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def resolve_starsoul(command_id, seq_id, user_id, conn, data):
    logger.debug("resolve_starsoul[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("resolve_starsoul", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def use_item(command_id, seq_id, user_id, conn, data):
    logger.debug("use resource package[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("use_item", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def use_speed_item(command_id, seq_id, user_id, conn, data):
    logger.debug("use speed item[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("use_speed_item", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def use_monarch_exp(command_id, seq_id, user_id, conn, data):
    logger.debug("use monarch exp[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("use_monarch_exp", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def sell_item(command_id, seq_id, user_id, conn, data):
    logger.debug("sell item[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("sell_item", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def create_hero_from_starsoul(command_id, seq_id, user_id, conn, data):
    logger.debug("create hero from starsoul[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("create_hero_from_starsoul", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def add_item(command_id, seq_id, user_id, conn, data):
    logger.debug("add item[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_item", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_create_building(command_id, seq_id, user_id, conn, data):
    logger.debug("start create building[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("start_create_building", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_upgrade_building(command_id, seq_id, user_id, conn, data):
    logger.debug("start upgrade building[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("start_upgrade_building", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_upgrade_building(command_id, seq_id, user_id, conn, data):
    logger.debug("finish upgrade building[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("finish_upgrade_building", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def complete_upgrade_building(command_id, seq_id, user_id, conn, data):
    logger.debug("finish upgrade building[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("complete_upgrade_building", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def cancel_upgrade_building(command_id, seq_id, user_id, conn, data):
    logger.debug("Cancel upgrade building[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("cancel_upgrade_building", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def update_garrison_hero(command_id, seq_id, user_id, conn, data):
    logger.debug("update garrison hero[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("update_garrison_hero", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_research_battle_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("start research battle technology[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("start_research_battle_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_research_battle_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("finish research battle technology[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("finish_research_battle_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_research_battle_with_gold(command_id, seq_id, user_id, conn, data):
    logger.debug("finish research battle technology[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("finish_research_battle_with_gold", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def cancel_research_battle_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("finish research battle technology[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("cancel_research_battle_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_research_interior_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("start research interior technology[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_research_interior_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_research_interior_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("finish research interior technology[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_research_interior_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_research_interior_with_gold(command_id, seq_id, user_id, conn, data):
    logger.debug("finish research interior with gold[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_research_interior_with_gold", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def cancel_research_interior_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("cancel research interior technology[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("cancel_research_interior_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_research_soldier_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("start research soldier technology[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("start_research_soldier_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_research_soldier_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("finish research soldier technology[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("finish_research_soldier_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_research_soldier_with_gold(command_id, seq_id, user_id, conn, data):
    logger.debug("finish research soldier technology with gold[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("finish_research_soldier_with_gold", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def cancel_research_soldier_technology(command_id, seq_id, user_id, conn, data):
    logger.debug("cancel research soldier technology[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("cancel_research_soldier_technology", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def exchange(command_id, seq_id, user_id, conn, data):
    logger.debug("exchange[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("exchange", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def add_resource(command_id, seq_id, user_id, conn, data):
    logger.debug("add resource[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("add_resource", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def recalc_resource(command_id, seq_id, user_id, conn, data):
    logger.debug("recalc resource[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("recalc_resource", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def recalc_all_resource(command_id, seq_id, user_id, conn, data):
    logger.debug("recalc all resource[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("recalc_all_resource", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def add_reputation(command_id, seq_id, user_id, conn, data):
    logger.debug("add reputation[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("add_reputation", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_city_info(command_id, seq_id, user_id, conn, data):
    logger.debug("update_city_info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_city_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_conscript(command_id, seq_id, user_id, conn, data):
    logger.debug("start_conscript[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_conscript", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def add_conscript(command_id, seq_id, user_id, conn, data):
    logger.debug("add_conscript[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_conscript", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def end_conscript(command_id, seq_id, user_id, conn, data):
    logger.debug("end_conscript[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("end_conscript", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def end_conscript_with_gold(command_id, seq_id, user_id, conn, data):
    logger.debug("end_conscript_with_gold[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("end_conscript_with_gold", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def cancel_conscript(command_id, seq_id, user_id, conn, data):
    logger.debug("cancel_conscript[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("cancel_conscript", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_mission(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_mission[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_mission", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def update_last_user_level(command_id, seq_id, user_id, conn, data):
    logger.debug("update last user level[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_last_user_level", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def query_ranking(command_id, seq_id, user_id, conn, data):
    logger.debug("query_ranking[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_ranking", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def query_ranking_player_powerful_teams(command_id, seq_id, user_id, conn, data):
    logger.debug("query_ranking_player_powerful_teams[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_ranking_player_powerful_teams", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def compose_item(command_id, seq_id, user_id, conn, data):
    logger.debug("compose_item[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("compose_item", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def casting_item(command_id, seq_id, user_id, conn, data):
    logger.debug("casting_item[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("casting_item", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def upgrade_hero_equipment(command_id, seq_id, user_id, conn, data):
    logger.debug("update_hero_equipment[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_hero_equipment", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def enchant_hero_equipment(command_id, seq_id, user_id, conn, data):
    logger.debug("enchant_hero_equipment[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("enchant_hero_equipment", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def upgrade_hero_equipment_max(command_id, seq_id, user_id, conn, data):
    logger.debug("update_hero_equipment_max[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_hero_equipment_max", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def enchant_hero_equipment_max(command_id, seq_id, user_id, conn, data):
    logger.debug("enchant_hero_equipment_max[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("enchant_hero_equipment_max", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_mail(command_id, seq_id, user_id, conn, data):
    logger.debug("query_mail[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_mail", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def read_mail(command_id, seq_id, user_id, conn, data):
    logger.debug("read_mail[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("read_mail", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def use_mail(command_id, seq_id, user_id, conn, data):
    logger.debug("use_mail[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("use_mail", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_mail(command_id, seq_id, user_id, conn, data):
    logger.debug("add_mail[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_mail", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def signin(command_id, seq_id, user_id, conn, data):
    logger.debug("signin[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("signin", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def signin_custom(command_id, seq_id, user_id, conn, data):
    logger.debug("signin_custom[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("signin_custom", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_team(command_id, seq_id, user_id, conn, data):
    logger.debug("update_team[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_team", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_all_teams(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh_all_teams[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_all_teams", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def trigger_war_event(command_id, seq_id, user_id, conn, data):
    logger.debug("trigger_war_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("trigger_war_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def trigger_lucky_event(command_id, seq_id, user_id, conn, data):
    logger.debug("trigger_lucky_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("trigger_lucky_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def trigger_specified_event(command_id, seq_id, user_id, conn, data):
    logger.debug("trigger_specified_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("trigger_specified_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def trigger_custom_war_event(command_id, seq_id, user_id, conn, data):
    logger.debug("trigger_custom_war_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("trigger_custom_war_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def trigger_custom_event(command_id, seq_id, user_id, conn, data):
    logger.debug("trigger_custom_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("trigger_custom_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def clear_lucky_event(command_id, seq_id, user_id, conn, data):
    logger.debug("clear_lucky_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("clear_lucky_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def abandon_node(command_id, seq_id, user_id, conn, data):
    logger.debug("abandon_node[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("abandon_node", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def rematch_node(command_id, seq_id, user_id, conn, data):
    logger.debug("rematch_node[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("rematch_node", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def upgrade_node(command_id, seq_id, user_id, conn, data):
    logger.debug("upgrade_node[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("upgrade_node", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_pvp_players(command_id, seq_id, user_id, conn, data):
    logger.debug("query_pvp_players[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_pvp_players", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_player_info(command_id, seq_id, user_id, conn, data):
    logger.debug("query_player_info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_player_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def reset_attack_num(command_id, seq_id, user_id, conn, data):
    logger.debug("reset_attack_num[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("reset_attack_num", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("start_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def skip_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("skip_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("skip_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def gather(command_id, seq_id, user_id, conn, data):
    logger.debug("gather[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("gather", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_exploitation(command_id, seq_id, user_id, conn, data):
    logger.debug("start_exploitation[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_exploitation", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_exploitation(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_exploitation[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_exploitation", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def cancel_exploitation(command_id, seq_id, user_id, conn, data):
    logger.debug("cancel_exploitation[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("cancel_exploitation", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_visit_event(command_id, seq_id, user_id, conn, data):
    logger.debug("start_visit_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_visit_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def search_visit_event(command_id, seq_id, user_id, conn, data):
    logger.debug("search_visit_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("search_visit_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_visit_event(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_visit_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_visit_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_question_event(command_id, seq_id, user_id, conn, data):
    logger.debug("start_question_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_question_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_question_event(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_question_event[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_question_event", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_appoint(command_id, seq_id, user_id, conn, data):
    logger.debug("start_appoint[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_appoint", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_appoint(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_appoint[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_appoint", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_pay(command_id, seq_id, user_id, conn, data):
    logger.debug("query_pay[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_pay", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_pay(command_id, seq_id, user_id, conn, data):
    logger.debug("start_pay[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_pay", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_pay(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_pay[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_pay", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def try_finish_pay_outside(command_id, seq_id, user_id, conn, data):
    logger.debug("try_finish_pay_outside[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("try_finish_pay_outside", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def patch_pay(command_id, seq_id, user_id, conn, data):
    logger.debug("patch_pay[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("patch_pay", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_activity(command_id, seq_id, user_id, conn, data):
    logger.debug("query_activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def operate_activity(command_id, seq_id, user_id, conn, data):
    logger.debug("operate_activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("operate_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def accept_activity_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("accept_activity_reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("accept_activity_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_activity(command_id, seq_id, user_id, conn, data):
    logger.debug("add_activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def award_activity_hero(command_id, seq_id, user_id, conn, data):
    logger.debug("award_activity_hero[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("award_activity_hero", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def clear_activity_hero_scores(command_id, seq_id, user_id, conn, data):
    logger.debug("clear_activity_hero_scores[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("clear_activity_hero_scores", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_arena(command_id, seq_id, user_id, conn, data):
    logger.debug("query_arena[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_arena", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_arena(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh_arena[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_arena", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_arena_ranking(command_id, seq_id, user_id, conn, data):
    logger.debug("query_arena_ranking[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_arena_ranking", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def get_arena_win_num_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("get_arena_win_num_reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("get_arena_win_num_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_arena(command_id, seq_id, user_id, conn, data):
    logger.debug("update_arena[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_arena", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_melee(command_id, seq_id, user_id, conn, data):
    logger.debug("query_melee[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_melee", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_melee(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh_melee[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_melee", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_melee_ranking(command_id, seq_id, user_id, conn, data):
    logger.debug("query_melee_ranking[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_melee_ranking", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def get_melee_win_num_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("get_melee_win_num_reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("get_melee_win_num_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_melee(command_id, seq_id, user_id, conn, data):
    logger.debug("update_melee[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_melee", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_arena_offline(command_id, seq_id, user_id, conn, data):
    logger.debug("update_arena_offline[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_arena_offline", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def protect(command_id, seq_id, user_id, conn, data):
    logger.debug("protect[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("protect", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def increase(command_id, seq_id, user_id, conn, data):
    logger.debug("increase[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("increase", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def use_cdkey(command_id, seq_id, user_id, conn, data):
    logger.debug("use_cd_key[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("use_cdkey", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def buy_energy(command_id, seq_id, user_id, conn, data):
    logger.debug("buy_energy[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("buy_energy", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def refresh_energy(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh_energy[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_energy", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def pray(command_id, seq_id, user_id, conn, data):
    logger.debug("pray[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("pray", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def choose_card(command_id, seq_id, user_id, conn, data):
    logger.debug("choose_card[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("choose_card", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def refresh_pray(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh_pray[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_pray", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def giveup_pray(command_id, seq_id, user_id, conn, data):
    logger.debug("giveup_pray[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("giveup_pray", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_legend_city_info(command_id, seq_id, user_id, conn, data):
    logger.debug("query_legend_city_info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_legend_city_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_legend_city_info(command_id, seq_id, user_id, conn, data):
    logger.debug("update_legend_city_info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_legend_city_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def reset_legend_city_attack_info(command_id, seq_id, user_id, conn, data):
    logger.debug("reset_legend_city_attack_info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "reset_legend_city_attack_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def buy_legend_city_buff(command_id, seq_id, user_id, conn, data):
    logger.debug("buy_legend_city_buff[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "buy_legend_city_buff", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def seek_legend_city_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("seek_legend_city_goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "seek_legend_city_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_legend_city_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh_legend_city_goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "refresh_legend_city_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def buy_legend_city_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("buy_legend_city_goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "buy_legend_city_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_legend_city_rival(command_id, seq_id, user_id, conn, data):
    logger.debug("query_legend_city_rival[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_legend_city_rival", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_legend_city(command_id, seq_id, user_id, conn, data):
    logger.debug("delete_legend_city[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "delete_legend_city", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def award_legend_city(command_id, seq_id, user_id, conn, data):
    logger.debug("award_legend_city[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "award_legend_city", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_vip_points(command_id, seq_id, user_id, conn, data):
    logger.debug("add vip points[command_id=%d]" % command_id);
    defer = GlobalObject().remote['app'].callRemote("add_vip_points", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def get_all(command_id, seq_id, user_id, conn, data):
    logger.debug("get_all[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "get_all", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def get_legendcity_position_rank(command_id, seq_id, user_id, conn, data):
    logger.debug("get_legendcity_position_rank[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "get_legendcity_position_rank", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_union(command_id, seq_id, user_id, conn, data):
    logger.debug("query_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_union_force(command_id, seq_id, user_id, conn, data):
    logger.debug("query_union force[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_union_force", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def search_union(command_id, seq_id, user_id, conn, data):
    logger.debug("search_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "search_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def create_union(command_id, seq_id, user_id, conn, data):
    logger.debug("create_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "create_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_union(command_id, seq_id, user_id, conn, data):
    logger.debug("delete_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "delete_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def join_union(command_id, seq_id, user_id, conn, data):
    logger.debug("join_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "join_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def approve_union(command_id, seq_id, user_id, conn, data):
    logger.debug("approve_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "approve_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def update_union(command_id, seq_id, user_id, conn, data):
    logger.debug("update_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "update_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def manage_union(command_id, seq_id, user_id, conn, data):
    logger.debug("manage_union[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "manage_union", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_union_member(command_id, seq_id, user_id, conn, data):
    logger.debug("query_union_member[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_union_member", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def seek_union_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("seek_union_goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("seek_union_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_union_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("refresh_union_goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_union_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def buy_union_goods(command_id, seq_id, user_id, conn, data):
    logger.debug("buy_union_goods[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("buy_union_goods", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_union_honor(command_id, seq_id, user_id, conn, data):
    logger.debug("add_union_honor[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_union_honor", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_union_aid(command_id, seq_id, user_id, conn, data):
    logger.debug("query_union_aid[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_union_aid", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_union_aid(command_id, seq_id, user_id, conn, data):
    logger.debug("start_union_aid[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "start_union_aid", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_union_aid(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_union_aid[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "finish_union_aid", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def respond_union_aid(command_id, seq_id, user_id, conn, data):
    logger.debug("respond_union_aid[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "respond_union_aid", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Query union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def launch_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Launch union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "launch_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def launch_union_battle_force(command_id, seq_id, user_id, conn, data):
    logger.debug("Launch union battle force[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "launch_union_battle_force", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def launch_two_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Launch two union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "launch_two_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def deploy_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Deploy union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "deploy_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def deploy_union_battle_force(command_id, seq_id, user_id, conn, data):
    logger.debug("Deploy union battle force[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "deploy_union_battle_force", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def cancel_deploy_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Cancel deploy union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "cancel_deploy_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def drum_for_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Drum for union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "drum_for_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Start union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "start_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Finish union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "finish_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def skip_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("Skip union battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "skip_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

                                                                                                 
@netserviceHandle                                                                                
def accept_union_battle_node_box_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("Accept union battle node box[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "accept_union_battle_node_box_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def refresh_union_battle_attack(command_id, seq_id, user_id, conn, data):
    logger.debug("Refresh union battle attack[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "refresh_union_battle_attack", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_union_battle_individuals(command_id, seq_id, user_id, conn, data):
    logger.debug("query_union_battle_individuals[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_union_battle_individuals", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def accept_union_battle_individual_step_award(command_id, seq_id, user_id, conn, data):
    logger.debug("accept_union_battle_individual_step_award[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "accept_union_battle_individual_step_award", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def gain_union_battle_individual_score(command_id, seq_id, user_id, conn, data):
    logger.debug("gain_union_battle_individual_score[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "gain_union_battle_individual_score", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def gain_union_battle_score(command_id, seq_id, user_id, conn, data):
    logger.debug("gain_union_battle_score[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "gain_union_battle_score", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

                                                                                                 
@netserviceHandle                                                                                
def accept_union_battle_box(command_id, seq_id, user_id, conn, data):
    logger.debug("Accept union battle box[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "accept_union_battle_box", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def force_update_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("force_update_union_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "force_update_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def try_forward_union_battle_season(command_id, seq_id, user_id, conn, data):
    logger.debug("try_forward_union_battle_season[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "try_forward_union_battle_season", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def try_forward_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("try_forward_union_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "try_forward_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def forward_union_battle_season(command_id, seq_id, user_id, conn, data):
    logger.debug("forward_union_battle_season[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "forward_union_battle_season", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def forward_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("forward_union_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "forward_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def award_for_union_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("award_for_union_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "award_for_union_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def try_transfer_union_leader(command_id, seq_id, user_id, conn, data):
    logger.debug("try_transfer_union_leader[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "try_transfer_union_leader", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_unionboss(command_id, seq_id, user_id, conn, data):
    logger.debug("query_unionboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_unionboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_unionboss_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("start_unionboss_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "start_unionboss_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_unionboss_battle(command_id, seq_id, user_id, conn, data):
    logger.debug("finish_unionboss_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "finish_unionboss_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def accept_unionboss_score_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("accept_unionboss_score_reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "accept_unionboss_score_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def accept_unionboss_box_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("accept_unionboss_box_reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "accept_unionboss_box_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

'''
@netserviceHandle
def query_unionboss_box_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("query_unionboss_box_reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_unionboss_box_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer
'''

@netserviceHandle
def reset_unionboss_attack_num(command_id, seq_id, user_id, conn, data):
    logger.debug("reset_unionboss_attack_num[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "reset_unionboss_attack_num", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def add_basic_unionboss(command_id, seq_id, user_id, conn, data):
    logger.debug("add_basic_unionboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "add_basic_unionboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

'''
@netserviceHandle
def update_unionboss(command_id, seq_id, user_id, conn, data):
    logger.debug("update_unionboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "update_unionboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer
'''

@netserviceHandle
def query_notice(command_id, seq_id, user_id, conn, data):
    logger.debug("query_notice[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_notice", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_notice(command_id, seq_id, user_id, conn, data):
    logger.debug("add_notice[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "add_notice", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_notice(command_id, seq_id, user_id, conn, data):
    logger.debug("delete_notice[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "delete_notice", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def open_chest(command_id, seq_id, user_id, conn, data):
    logger.debug("open_chest[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "open_chest", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_chest(command_id, seq_id, user_id, conn, data):
    logger.debug("query_chest[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_chest", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_common(command_id, seq_id, user_id, conn, data):
    logger.debug("Delete common[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "delete_common", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_kill_enemy_num(command_id, seq_id, user_id, conn, data):
    logger.debug("Add kill enemy num[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "add_kill_enemy_num", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_arena_coin(command_id, seq_id, user_id, conn, data):
    logger.debug("Add arena coin[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "add_arena_coin", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_anneal(command_id, seq_id, user_id, conn, data):
    logger.debug("Query anneal[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_anneal", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def get_pass_reward(command_id, seq_id, user_id, conn, data):
    logger.debug("Get pass reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "get_pass_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def buy_attack_num(command_id, seq_id, user_id, conn, data):
    logger.debug("Buy attack num[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "buy_attack_num", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def start_sweep(command_id, seq_id, user_id, conn, data):
    logger.debug("Start sweep[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "start_sweep", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def finish_sweep(command_id, seq_id, user_id, conn, data):
    logger.debug("Finish sweep[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "finish_sweep", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_anneal_record(command_id, seq_id, user_id, conn, data):
    logger.debug("Query anneal record[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "query_anneal_record", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def modify_anneal_progress(command_id, seq_id, user_id, conn, data):
    logger.debug("Modify anneal progress[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "modify_anneal_progress", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def modify_anneal_sweep_time(command_id, seq_id, user_id, conn, data):
    logger.debug("Modify anneal sweep time[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "modify_anneal_sweep_time", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def reset_anneal_hard_attack_num(command_id, seq_id, user_id, conn, data):
    logger.debug("reset_anneal_hard_attack_num[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "reset_anneal_hard_attack_num", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_init_basic_activity(command_id, seq_id, user_id, conn, data):
    """添加用户初始化的活动id"""
    logger.debug("add init basic activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_init_basic_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def delete_init_basic_activity(command_id, seq_id, user_id, conn, data):
    """删除用户初始化的活动id"""
    logger.debug("delete init basic activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("delete_init_basic_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def query_init_basic_activity(command_id, seq_id, user_id, conn, data):
    """查询用户初始化的活动id"""
    logger.debug("query init basic activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_init_basic_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_basic_activity(command_id, seq_id, user_id, conn, data):
    """添加基础活动信息"""
    logger.debug("add basic activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_basic_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_basic_activity(command_id, seq_id, user_id, conn, data):
    """删除基础活动信息"""
    logger.debug("delete basic activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("delete_basic_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_basic_activity(command_id, seq_id, user_id, conn, data):
    """查询基础活动信息"""
    logger.debug("query basic activity[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_basic_activity", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_basic_activity_step(command_id, seq_id, user_id, conn, data):
    """添加基础活动step信息"""
    logger.debug("add basic activity step[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_basic_activity_step", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_basic_activity_step(command_id, seq_id, user_id, conn, data):
    """删除基础活动step信息"""
    logger.debug("delete basic activity step[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("delete_basic_activity_step", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_basic_activity_step(command_id, seq_id, user_id, conn, data):
    """查询基础活动step信息"""
    logger.debug("query basic activity step[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_basic_activity_step", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def add_basic_activity_hero_reward(command_id, seq_id, user_id, conn, data):
    """添加限时英雄活动的reward基础信息"""
    logger.debug("add basic activity hero reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_basic_activity_hero_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def add_basic_activity_treasure_reward(command_id, seq_id, user_id, conn, data):
    """添加限时英雄活动的reward基础信息"""
    logger.debug("add basic activity treasure reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_basic_activity_treasure_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_basic_activity_hero_reward(command_id, seq_id, user_id, conn, data):
    """删除限时英雄活动的reward基础信息"""
    logger.debug("delete basic activity hero reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("delete_basic_activity_hero_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_basic_activity_hero_reward(command_id, seq_id, user_id, conn, data):
    """查询限时英雄活动的reward基础信息"""
    logger.debug("query basic activity hero reward[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_basic_activity_hero_reward", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_basic_info(command_id, seq_id, user_id, conn, data):
    logger.debug("Delete basic info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote(
            "delete_basic_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def strength_herostar(command_id, seq_id, user_id, conn, data):
    """升级将星"""
    logger.debug("strength herostar[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("strength_herostar", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def wear_herostar(command_id, seq_id, user_id, conn, data):
    """装备将星"""
    logger.debug("wear herostar[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("wear_herostar", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def unload_herostar(command_id, seq_id, user_id, conn, data):
    """装备将星"""
    logger.debug("unload herostar[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("unload_herostar", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer
    

@netserviceHandle
def add_basic_worldboss(command_id, seq_id, user_id, conn, data):
    """添加基础世界boss信息"""
    logger.debug("add basic worldboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_basic_worldboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def delete_basic_worldboss(command_id, seq_id, user_id, conn, data):
    """删除基础世界boss信息"""
    logger.debug("delete basic worldboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("delete_basic_worldboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_basic_worldboss(command_id, seq_id, user_id, conn, data):
    """查询基础世界boss信息"""
    logger.debug("query basic worldboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_basic_worldboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_worldboss(command_id, seq_id, user_id, conn, data):
    """查询世界boss信息"""
    logger.debug("query worldboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_worldboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_worldboss_soldier_num(command_id, seq_id, user_id, conn, data):
    """查询世界boss信息"""
    logger.debug("query worldboss soldier num[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_worldboss_soldier_num", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def modify_common_worldboss(command_id, seq_id, user_id, conn, data):
    """修改世界boss的公共信息"""
    logger.debug("modify common worldboss[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("modify_common_worldboss", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def clear_worldboss_merit(command_id, seq_id, user_id, conn, data):
    """清空世界boss的战功"""
    logger.debug("clear worldboss merit[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("clear_worldboss_merit", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer


@netserviceHandle
def query_union_donate(command_id, seq_id, user_id, conn, data):
    """查询联盟捐献信息"""
    logger.debug("query union donate[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_union_donate", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def initiate_union_donate(command_id, seq_id, user_id, conn, data):
    """发起联盟捐献"""
    logger.debug("initiate union donate[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("initiate_union_donate", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_union_donate(command_id, seq_id, user_id, conn, data):
    """开始联盟捐献"""
    logger.debug("start union donate[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_union_donate", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def reward_union_donate(command_id, seq_id, user_id, conn, data):
    """领取捐献宝箱"""
    logger.debug("reward union donate[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("reward_union_donate", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def refresh_union_donate_box(command_id, seq_id, user_id, conn, data):
    """刷新捐献宝箱"""
    logger.debug("refresh union donate box[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_union_donate_box", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def clear_union_donate_coldtime(command_id, seq_id, user_id, conn, data):
    """清空冷却时间"""
    logger.debug("clear union donate coldtime[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("clear_union_donate_coldtime", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def reborn_hero(command_id, seq_id, user_id, conn, data):
    """英雄重生"""
    logger.debug("reborn hero[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("reborn_hero", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def query_exchange(command_id, seq_id, user_id, conn, data):
    """查询兑换信息"""
    logger.debug("query exchange info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_exchange", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def do_exchange(command_id, seq_id, user_id, conn, data):
    """进行兑换"""
    logger.debug("do exchange[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("do_exchange", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def get_user_basic_info(command_id, seq_id, user_id, conn, data):
    """内部接口:获取用户基本信息"""
    logger.debug("get user basic info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("get_user_basic_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def update_user_basic_info(command_id, seq_id, user_id, conn, data):
    """内部接口:修改用户基本信息"""
    logger.debug("update user basic info[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("update_user_basic_info", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def query_expand_dungeon(command_id, seq_id, user_id, conn, data):
    """进行兑换"""
    logger.debug("query_expand_dungeon[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_expand_dungeon", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def reset_expand_dungeon(command_id, seq_id, user_id, conn, data):
    """进行兑换"""
    logger.debug("reset_expand_dungeon[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("reset_expand_dungeon", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer
    
@netserviceHandle
def query_transfer_arena(command_id, seq_id, user_id, conn, data):
    """查询换位演武场"""
    logger.debug("query_transfer_arena[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("query_transfer_arena", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def buy_transfer_challenge_times(command_id, seq_id, user_id, conn, data):
    """购买换位演武场挑战次数"""
    logger.debug("buy_transfer_challenge_times[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("buy_transfer_challenge_times", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def reset_transfer_cd(command_id, seq_id, user_id, conn, data):
    """重置换位演武场冷却时间"""
    logger.debug("reset_transfer_cd[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("reset_transfer_cd", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def start_transfer_battle(command_id, seq_id, user_id, conn, data):
    """开始换位演武场战斗"""
    logger.debug("start_transfer_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("start_transfer_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def finish_transfer_battle(command_id, seq_id, user_id, conn, data):
    """开始换位演武场战斗"""
    logger.debug("finish_transfer_battle[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("finish_transfer_battle", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def award_transfer(command_id, seq_id, user_id, conn, data):
    """发放换位演武场奖励"""
    logger.debug("award_transfer[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("award_transfer", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def treasure_draw(command_id, seq_id, user_id, conn, data):
    """ 夺宝抽奖 """
    logger.debug("treasure_draw[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("treasure_draw", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def fortune_cat(command_id, seq_id, user_id, conn, data):
    """ 招财猫 """
    logger.debug("fortune cat[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("fortune_cat", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def get_friends(command_id, seq_id, user_id, conn, data):
    """ 获取推荐好友 """
    logger.debug("get_friends[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("get_friends", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def view_apply(command_id, seq_id, user_id, conn, data):
    """ 获取好友请求 """
    logger.debug("view_apply[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("view_apply", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def view_friend(command_id, seq_id, user_id, conn, data):
    """ 获取好友 """
    logger.debug("view_friend[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("view_friend", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def add_friend(command_id, seq_id, user_id, conn, data):
    """ 添加好友 """
    logger.debug("add_friend[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("add_friend", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer
@netserviceHandle
def receive_friend(command_id, seq_id, user_id, conn, data):
    """ 添加好友对方接收消息 """
    logger.debug("add_friend[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("receive_friend", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def manage_friend(command_id, seq_id, user_id, conn, data):
    """ 管理好友 """
    logger.debug("manage_friend[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("manage_friend", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def chat_friend(command_id, seq_id, user_id, conn, data):
    """ 好友聊天 """
    logger.debug("chat_friend[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("chat_friend", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

@netserviceHandle
def refresh_chat(command_id, seq_id, user_id, conn, data):
    """ 好友红点刷新 """
    logger.debug("refresh_chat[command_id=%d]" % command_id)
    defer = GlobalObject().remote['app'].callRemote("refresh_chat", user_id, data)
    defer.addCallback(store_user_response, user_id, seq_id)
    return defer

def store_user_response(response, user_id, seq_id):
    OnlineManager().update_response(user_id, seq_id, response)
    return response

