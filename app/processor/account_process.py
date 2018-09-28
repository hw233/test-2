#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 帐号相关处理逻辑
"""

import time
from twisted.internet.defer import Deferred
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils import utils
from utils.timer import Timer
from proto import init_pb2
from proto import internal_pb2
from proto import internal_union_pb2
from proto import union_pb2
from proto import unit_pb2
from proto import legendcity_pb2
from datalib.global_data import DataBase
from datalib.data_dumper import DataDumper
from app import basic_view
from app import pack
from app import log_formater
from datalib.data_loader import data_loader
from app.data.resource import ResourceInfo
from app.data.city import CityInfo
from app.data.battle import BattleInfo
from app.data.signin import SignInfo
from app.data.map import MapInfo
from app.data.arena import ArenaInfo
from app.data.melee import MeleeInfo
from app.data.statistics import StatisticsInfo
from app.data.battlescore import BattleScoreInfo
from app.data.trainer import TrainerInfo
from app.data.node import NodeInfo
from app.data.exploitation import ExploitationInfo
from app.data.anneal import AnnealInfo
from app.data.transfer import UserTransferInfo
from app.data.plunder import PlunderInfo
from app.rival_matcher import RivalMatcher
from app.arena_matcher import ArenaMatcher
from app.melee_matcher import MeleeMatcher
from app.business import account as account_business
from app.business import user as user_business
from app.business import item as item_business
from app.business import city as city_business
from app.business import building as building_business
from app.business import technology as technology_business
from app.business import map as map_business
from app.business import shop as shop_business
from app.business import draw as draw_business
from app.business import mission as mission_business
from app.business import conscript as conscript_business
from app.business import battle as battle_business
from app.business import mail as mail_business
from app.business import shop as shop_business
from app.business import pay as pay_business
from app.business import activity as activity_business
from app.business import arena as arena_business
from app.business import legendcity as legendcity_business
from app.business import energy as energy_business
from app.business import pray as pray_business
from app.business import union as union_business
from app.business import chest as chest_business
from app.business import anneal as anneal_business
from app.business import worldboss as worldboss_business
from app.business import basic_init as basic_init_business
from app.business import herostar as herostar_business
from app.business import expand_dungeon as expand_dungeon_business
from app.business import melee as melee_business
from app.processor.worldboss_process import WorldBossProcessor
from app.union_patcher import UnionBattleStagePatcher
from app.user_matcher import UserMatcher

class AccountProcessor(object):
    """处理 User 相关逻辑"""


    def init(self, user_id, request):
        """用户登录服务器进行游戏：
        1 如果用户是初次登录，为其初始化游戏需要的数据
        2 如果用户不是初次登录，载入其之前的游戏数据，并计算离线数据，返回
        """
        timer = Timer(user_id)

        req = init_pb2.InitReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._create_basic_init, user_id, req, timer)
        return defer


    def _create_basic_init(self, basic_data, user_id, req, timer):
        if not basic_data.is_valid():
            basic_init_business.create_basic_init(basic_data, basic_view.BASIC_ID)

        defer = DataBase().commit_basic(basic_data)
        defer.addCallback(self._init_user, user_id, req, timer)
        return defer


    def _init_user(self, basic_data, user_id, req, timer):
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._create_or_load, basic_data, req, timer)
        defer.addErrback(self._init_failed, req, timer)
        return defer


    def _create_or_load(self, data, basic_data, req, timer):
        """新建玩家数据，或者载入玩家数据
        """
        if data.is_valid(): # Not New
            return self._load_user(basic_data, data, req, timer)
        else: # New
            return self._create_new_user(basic_data, data, req, timer)


    def _create_new_user(self, basic_data, data, req, timer):
        """创建一个新用户，初始化其所需要的所有数据
        """
        defer = self._generate_all_info(basic_data, data, timer)
        defer.addCallback(self._pack_user_info, basic_data, req, timer, True)
        return defer


    def _generate_all_info(self, basic_data, data, timer, pattern = 1):
        """初始化账户信息
        Args:
            data[UserData]: 用户数据
            pattern[int]: 帐号初始化的模式
        Returns:
            UserData: 一个玩家的完整数据
        """
        user_id = data.id

        #用户信息
        if data_loader.OtherBasicInfo_dict.has_key("init_id"):
            pattern = int(float(data_loader.OtherBasicInfo_dict['init_id'].value))
        if not user_business.init_user(data, data.id, pattern, timer.now):
            raise Exception("Init user failed")

        #初始资源
        if not user_business.init_resource(data, pattern, timer.now):
            raise Exception("Init resource failed")

        #初始赠送物品
        if not item_business.init_default_items(data, pattern):
            raise Exception("Init items failed")

        #初始化战斗地图，以及所有节点信息
        if not map_business.init_map(data, pattern, timer.now):
            raise Exception("Init map failed")

        #初始主城
        if not city_business.create_main_city(data, pattern):
            raise Exception("Create main city failed")

        #初始化主城中的建筑
        if not city_business.init_main_city(data, pattern):
            raise Exception("Init building in main city failed")

        #建筑物会解锁出科技、城防、征兵等
        technology_list = []
        defense_list = []
        conscript_list = []
        resource = data.resource.get()
        for new_building in data.building_list.get_all():
            if not building_business.post_upgrade(data,
                    new_building, timer.now, [None, None, None], [],
                    resource, None, None,
                    technology_list, defense_list, conscript_list):
                raise Exception("Init technology / defense / conscript failed")

        for technology in technology_list:
            data.technology_list.add(technology)
        for defense in defense_list:
            data.defense_list.add(defense)
        for conscript in conscript_list:
            data.conscript_list.add(conscript)

        #兵种科技会解锁兵种
        soldier_list = []
        for technology in technology_list:
            if not technology.is_soldier_technology():
                continue

            new_soldier = technology_business.post_research_for_soldier_technology(
                    data, data.id, technology, timer.now, new = True)
            if new_soldier is None:
                raise Exception("Init soldier failed")
            soldier_list.append(new_soldier)

        for soldier in soldier_list:
            data.soldier_list.add(soldier)

        #初始化联盟信息
        union_business.init_union(data, timer.now)

        #初始商店信息
        if not shop_business.init_shop(data, timer.now):
            raise Exception("Init shop failed")

        #初始充值商店信息
        if not pay_business.init_pay(data, pattern, timer.now):
            raise Exception("Init pay failed")

        #初始化活动信息
        if not activity_business.init_activity(basic_data, data, pattern, timer):
            raise Exception("Init activity failed")

        #初始抽奖信息
        if not draw_business.init_draw(data, timer.now):
            raise Exception("Init draw failed")

        #初始化演武场信息
        arena = ArenaInfo.create(data.id)
        data.arena.add(arena)
        #初始化乱斗场信息
        melee = MeleeInfo.create(data.id)
        data.melee.add(melee)

        #初始化史实城信息
        if not legendcity_business.init_legendcity(data, timer.now):
            raise Exception("Init legendcity failed")

        #初始邮件信息
        if not mail_business.init_postoffice(data, timer.now):
            raise Exception("Init postoffice failed")

        #基础任务
        mission_list = mission_business.init(data.id, pattern)
        for mission in mission_list:
            data.mission_list.add(mission)
        #日常任务
        mission_business.reset_daily_missions(data, pattern)

        #初始化统计信息
        statistics = StatisticsInfo.create(data.id)
        data.statistics.add(statistics)

        #初始化签到信息
        sign = SignInfo.create(data.id)
        data.sign.add(sign)

        #初始化总战力信息
        battle_score = BattleScoreInfo.create(data.id)
        data.battle_score.add(battle_score)

        #初始化一些统计信息
        trainer = TrainerInfo.create(data.id)
        data.trainer.add(trainer)
        trainer.add_login_num(1)

        #初始化政令信息
        energy = energy_business.init_energy(data, timer.now)
        data.energy.add(energy)

        #初始化祈福信息
        pray = pray_business.init_pray(data, timer.now)
        data.pray.add(pray)

        #初始化红包信息
        chest = chest_business.init_chest(data, timer.now)
        data.chest.add(chest)

        #初始化演武场信息
        exploitation = ExploitationInfo.create(data.id)
        data.exploitation.add(exploitation)

        #初始化试炼场信息
        anneal = anneal_business.init_anneal(data, timer.now)
        data.anneal.add(anneal)

        #初始化将星盘信息
        herostar_business.init_herostar(data)

        #初始化世界boss信息
        worldboss = worldboss_business.init_worldboss(basic_data, data, timer.now)
        data.worldboss.add(worldboss)
        if worldboss.is_arised():
            worldboss_process = WorldBossProcessor()
            worldboss_process.query_common_worldboss(data, worldboss)

        #初始化扩展副本
        expand_dungeon_business.init_expand_dungeon(data)

        #初始化换位演武场
        transfer = UserTransferInfo.create(data.id)
        data.transfer.add(transfer)
 
        #初始化掠夺信息
        plunder = PlunderInfo.create(data.id)
        data.plunder.add(plunder)

        return DataBase().commit(data)


    def _pack_user_info(self, data, basic_data, req, timer, first_init, arena_matcher = None, melee_matcher = None):
        """打包所有用户数据
        Args:
            data[UserData]: 用户数据
            req[protobuf]: 请求
        Returns:
            res[protobuf]
        """
        res = init_pb2.InitRes()
        res.status = 0
        res.first_init = first_init
        info = res.info

        user = data.user.get(True)
        pay = data.pay.get(True)
        pack.pack_monarch_info(user, info.monarch)
        union = data.union.get(True)
        resource = data.resource.get(True)
        if union.is_belong_to_union():
            info.monarch.union_id = union.union_id
            info.union_battle_stage = UnionBattleStagePatcher().patch(union.union_id)

        pack.pack_resource_info(data.resource.get(True), info.resource)
        for item in data.item_list.get_all(True):
            pack.pack_item_info(item, info.items.add())
        for hero in data.hero_list.get_all(True):
            pack.pack_hero_info(hero, info.heroes.add(), timer.now)
        for team in data.team_list.get_all(True):
            pack.pack_team_info(team, info.teams.add())

        pack.pack_map_info(data, data.map.get(True), info.map, timer.now)

        for city in data.city_list.get_all(True):
            pack.pack_city_info(city, info.cities.add())
        for building in data.building_list.get_all(True):
            pack.pack_building_info(building, info.buildings.add(), timer.now)
        for technology in data.technology_list.get_all(True):
            pack.pack_technology_info(technology, info.techs.add(), timer.now)
        for conscript in data.conscript_list.get_all(True):
            pack.pack_conscript_info(conscript, info.conscripts.add(), timer.now)
        assert len(data.defense_list) == 1

        pack.pack_money_draw_info(data.draw.get(True), info.money_draw, timer.now)
        pack.pack_gold_draw_info(data.draw.get(True), info.gold_draw, timer.now)

        for mission in data.mission_list:
            pack.pack_mission_info(mission.get(True), info.missions.add())

        #邮件看产生时间顺序给出
        # data.mail.sort(cmp = None, key=lambda x:x.time, reverse = False)
        for mail in data.mail_list.get_all(True):
            pack.pack_mail_info(mail, info.mails.add(), timer.now)

        pack.pack_sign_info(data.sign.get(True), info.sign_in)

        #演武场
        arena = data.arena.get(True)
        arena_ranking = 0
        if arena_matcher is not None:
            arena_ranking = arena_matcher.rank
        pack.pack_arena_info(user, arena, info.arena, timer.now, arena_ranking)
        #if user.allow_pvp_arena and arena.is_arena_active(timer.now):
        #    #胜场奖励
        #    if arena.is_able_to_get_win_num_reward():
        #        pack.pack_arena_reward_info(arena, info.arena.win_num_reward)
        #    #对手信息
        #    if arena.rivals_user_id != '':
        #        rivals_id = arena.generate_arena_rivals_id()
        #        for rival_id in rivals_id:
        #            rival = data.rival_list.get(rival_id, True)
        #            pack.pack_arena_player(rival, info.arena.rivals.add())
        #        #系统选定的对战对手
        #        choose_rival_id = arena.get_choose_rival_id()
        #        choose_rival = data.rival_list.get(choose_rival_id, True)
        #        info.arena.choosed_user_id = choose_rival.rival_id

        #    #对战记录
        #    record_list = data.arena_record_list.get_all(True)
        #    for record in record_list:
        #        pack.pack_arena_record(record, info.arena.records.add())

        flags = account_business.get_flags()
        if 'is_open_melee' in flags:
            #乱斗场
            melee = data.melee.get(True)
            melee_ranking = 0
            if melee_matcher is not None:
                melee_ranking = melee_matcher.rank
            pack.pack_melee_info(user, melee, info.melee_arena, timer.now, melee_ranking)
            #if melee.is_able_to_unlock(user) and melee.is_arena_active(timer.now):
            #    #胜场奖励
            #    if melee.is_able_to_get_win_num_reward():
            #        pack.pack_arena_reward_info(melee, info.melee_arena.win_num_reward)
            #    #对手信息
            #    if melee.rivals_user_id != '':
            #        rivals_id = melee.generate_arena_rivals_id()
            #        for rival_id in rivals_id:
            #            rival = data.rival_list.get(rival_id, True)
            #            pack.pack_melee_player(rival, info.melee_arena.rivals.add())

            #    #对战记录
            #    record_list = data.melee_record_list.get_all(True)
            #    for record in record_list:
            #        pack.pack_arena_record(record, info.melee_arena.records.add())
            ##乱斗场阵容
            #(heroes_list, positions_list) = melee.get_heroes_position()
            #if len(heroes_list) > 0:
            #    info.melee_team.index = 0
            #for hero_basic_id in heroes_list:
            #    (info.melee_team.heroes.add()).basic_id = hero_basic_id
            #for position in positions_list:
            #    info.melee_team.hero_positions.append(position)

        #政令
        energy = data.energy.get(True)
        pack.pack_energy_info(energy, info.energy_info, timer.now)

        #祈福
        pray = data.pray.get(True)
        pack.pack_pray_info(pray, info.pray, timer.now)

        #红包
        chest = data.chest.get(True)
        pack.pack_chest_info(chest, info.chest, timer.now)

        #试炼场
        anneal = data.anneal.get(True)
        pack.pack_anneal_info(data, anneal, info.anneal, timer.now) 

        #打包新手引导进度信息
        pack.pack_guide_info(data.user.get(True), info.guide)

        #将星盘
        herostar_list = data.herostar_list.get_all(True)
        for herostar in herostar_list:
            info.hero_star.append(herostar.star_id)
        
        #世界boss
        #pack.pack_worldboss_info(data.worldboss.get(True), user, info.world_boss, timer.now)

        #功能开关
        #flags = account_business.get_flags()
        pack.pack_flag_info(flags, info.flags)

        #扩展副本
        dungeons = data.expand_dungeon_list.get_all()
        for dungeon in dungeons:
            dungeon.daily_update(timer.now)
            pack.pack_expand_dungeon_info(dungeon, user, info.expand_dungeons.add(), 0,
                    timer.now, brief=True)
       
        #主界面的按钮提示
        pack.pack_button_tips(basic_data, data, info, timer.now)

        #lua
        #pack.pack_luas(info.luas)

        logger.notice("Submit Role[user_id=%d][level=%d][name=%s][vip=%d][status=LOGIN][create_time=%d][last_login_time=%d][money=%d][food=%d][gold=%d][pay_count=%d][pay_amount=%.2f]"
                % (user.id, user.level, user.name, user.vip_level, user.create_time, user.last_login_time, resource.money, resource.food, resource.gold, pay.pay_count, pay.pay_amount))
        
        #log = log_formater.output_gold(data, 0, log_formater.INIT_RESOURCE_GOLD,
        #       "Gain gold from init resource", before_gold = data.resource.get(True).gold)
        #logger.notice(log)
        
        return self._init_succeed(data, req, res, timer)


    def _init_succeed(self, data, req, res, timer):
        response = res.SerializeToString()

        log = log_formater.output(data, "Init succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _init_failed(self, err, req, timer):
        logger.fatal("Init failed[reason=%s]" % err)

        res = init_pb2.InitRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Init failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    #def _load_user(self, data, req, timer):
    #    """载入玩家数据，并计算离线数据
    #    """
    #    defer = self._update_all_info(data, req, timer)
    #    defer.addCallback(self._pack_user_info, False, req, timer)
    #    return defer


    def _load_user(self, basic_data, data, req, timer):
        """载入玩家数据，并计算离线数据
        """
        defer = Deferred()

        arena_matcher = ArenaMatcher()
        melee_matcher = MeleeMatcher()
        defer.addCallback(self._query_arena_ranking, data, req, timer, arena_matcher)
        defer.addCallback(self._query_melee_ranking, data, req, timer, melee_matcher)
        defer.addCallback(self._update_all_info, basic_data, data, req, timer)
        defer.addCallback(self._pack_user_info, basic_data, req, timer, False, arena_matcher, melee_matcher)
        defer.callback(True)
        return defer


    def _query_arena_ranking(self, proxy, data, req, timer, arena_matcher):
        """用户登录时需要查询演武场排名
        """
        #更新数据
        user = data.user.get()
        if not user.allow_pvp_arena:
            return True

        arena = data.arena.get()
        if arena.need_query_rank():
            defer = arena_matcher.query_ranking(data, arena)
            return defer

        return True


    def _query_melee_ranking(self, proxy, data, req, timer, melee_matcher):
        """用户登录时需要查询乱斗场排名
        """
        #更新数据
        user = data.user.get()
        if not user.allow_pvp_arena:
            return True

        melee = data.melee.get()
        #if melee.need_query_rank():
        #    defer = melee_matcher.query_ranking(data, melee)
        #    return defer
        #return True
        defer = melee_matcher.match(data, melee)
        return defer


    def _update_all_info(self, proxy, basic_data, data, req, timer):
        """用户登录游戏服时，载入数据，更新所有离线的信息
        """
        #更新离线数据
        if not self._update_offline_info(basic_data, data, timer.now):
            raise Exception("Update offline info failed")

        map_business.check_map_data(data)

        #更新数据
        defer = DataBase().commit(data)
        return defer


    def _update_offline_info(self, basic_data, data, now):
        """更新所有离线数据
        """
        if not account_business.update_across_day_info(data, now, True):
            logger.warning("Update across day info failed")
            return False

        user = data.user.get()
        #更新战斗信息
        battles = data.battle_list.get_all()
        for battle in battles:
            if not battle.is_appoint and battle.is_able_to_finish(now):
                if battle.is_revenge():
                    node = None
                else:
                    node = data.node_list.get(battle.node_id)
                if not battle_business.lose_battle(data, node, now):
                    return False
            if battle.is_appoint: #有些错误导致节点委任已结束，但是战斗还处于委任状态 
                node = data.node_list.get(battle.node_id)
                if not node.is_in_battle():
                    battle.finish()

        #检查所有未完成的充值，尝试完成漏单
        pay_business.try_check_all_order(data, now)

        #更新世界boss
        worldboss = data.worldboss.get()
        worldboss_business.update_worldboss(data, basic_data, worldboss, user.level, now)
        if worldboss.is_arised():
            worldboss_process = WorldBossProcessor()
            worldboss_process.query_common_worldboss(data, worldboss)

        #tips:以下为临时修复数据逻辑
        #更新队伍信息（由于委任丢失，导致部队和英雄锁死）
        teams = data.team_list.get_all()
        for team in teams:
            if team.is_in_battle():
                node_id = NodeInfo.generate_id(data.id, team.battle_node_basic_id)
                node = data.node_list.get(node_id, True)
                if not node.is_in_battle() or not node.is_visible() or not node.is_enemy_complete():
                    #部队复位
                    team.clear_in_battle()
                    #英雄复位
                    for hero_id in team.get_heroes():
                        hero = data.hero_list.get(hero_id)
                        if hero is not None:
                            hero.clear_in_battle()

                    #battle信息清空
                    battle = data.battle_list.get(node.id)
                    if battle is None:
                        #node复位
                        node.clear_in_battle()
                        break

                    if battle.is_appoint:
                        own_soldier_info = battle.get_own_soldier_info()
                        enemy_soldier_info = battle.get_enemy_soldier_info()
                        if not battle_business.lose_battle(
                                data, node, now, enemy_soldier_info, own_soldier_info):
                            raise Exception("Fix appoint battle failed")
                        logger.debug("Fix appoint battle[node basic id=%d]" % node.basic_id)
                    else:
                        battle.finish()

                    #node复位
                    node.clear_in_battle()
            if team.is_in_anneal_sweep():
                #英雄复位
                for hero_id in team.get_heroes():
                    hero = data.hero_list.get(hero_id)
                    if hero is not None:
                        hero.clear_in_anneal_sweep()
                team.clear_in_anneal_sweep()

                anneal = data.anneal.get()
                if anneal.is_in_sweep():
                    anneal.finish_sweep()

        #修复节点（战斗信息已经丢失，但节点还处于战斗状态）
        nodes = data.node_list.get_all()
        for node in nodes:
            if node.is_in_battle():
                battle = data.battle_list.get(node.id)
                if battle is not None and battle.is_able_to_start():
                    node.clear_in_battle()
            if node.is_rival_exist() and node.rival_id == 0:
                if node.is_key_node():
                    node.clear_key_node()

        #修复地下城dungeon
        dungeon = data.dungeon.get()
        if dungeon.is_dungeon_open():
            node = data.node_list.get(dungeon.node_id)
            if not node.is_rival_exist():
                dungeon.close()

        #修复征兵
        conscripts = data.conscript_list.get_all()
        for conscript in conscripts:
            if conscript.conscript_num == 0:
                building = data.building_list.get(conscript.building_id)
                if building.has_working_hero() and not building.is_upgrade:
                    logger.notice("Auto fix conscripts[user_id=%d]" % data.id)
                    heroes_id = utils.split_to_int(building.hero_ids)
                    building.hero_ids = "0#0#0"
                    for hero_id in heroes_id:
                        if hero_id == 0:
                            continue
                        hero = data.hero_list.get(hero_id)
                        hero.finish_working()

        #修复研究科技
        ministerhouse_id = int(float(data_loader.OtherBasicInfo_dict['building_ministerhouse'].value))
        ministerhouse_list = building_business.get_buildings_by_basic_id(data, ministerhouse_id) #丞相府
        ministerhouse = ministerhouse_list[0] if len(ministerhouse_list) > 0 else None
        if ministerhouse != None and not ministerhouse.is_upgrade and ministerhouse.hero_ids != "0#0#0":
            technologys = data.technology_list.get_all()
            #获取正在升级的内政科技
            interior = [t for t in technologys if t.type == t.INTERIOR_TECH_TYPE and t.is_upgrade]
            if len(interior) == 0:
                logger.notice("Auto fix interior technology[user_id=%d]" % data.id)
                heroes_id = utils.split_to_int(ministerhouse.hero_ids)
                ministerhouse.hero_ids = "0#0#0"
                for hero_id in heroes_id:
                    if hero_id == 0:
                        continue
                    hero = data.hero_list.get(hero_id)
                    hero.finish_working()
                
        generalhouse_id = int(float(data_loader.OtherBasicInfo_dict['building_generalhouse'].value))
        generalhouse_list = building_business.get_buildings_by_basic_id(data, generalhouse_id) #将军府
        generalhouse = generalhouse_list[0] if len(generalhouse_list) > 0 else None
        if generalhouse != None and not generalhouse.is_upgrade and generalhouse.hero_ids != "0#0#0":
            technologys = data.technology_list.get_all()
            #获取正在升级的战斗科技
            battle = [t for t in technologys if t.type != t.INTERIOR_TECH_TYPE and t.is_upgrade]
            if len(battle) == 0:
                logger.notice("Auto fix battle technology[user_id=%d]" % data.id)
                heroes_id = utils.split_to_int(generalhouse.hero_ids)
                generalhouse.hero_ids = "0#0#0"
                for hero_id in heroes_id:
                    if hero_id == 0:
                        continue
                    hero = data.hero_list.get(hero_id)
                    hero.finish_working()


        #修复英雄工作状态
        heroes = data.hero_list.get_all()
        for hero in heroes:
            if hero.place_type == hero.PLACE_TYPE_BUILDING:
                building = data.building_list.get(hero.place_id)
                if building is not None and not building.is_heroes_working([hero]):
                    hero.finish_working()

            elif hero.place_type == hero.PLACE_TYPE_NODE:
                node = data.node_list.get(hero.place_id)
                heroes_id = utils.split_to_int(node.exploit_team)
                if hero.id not in heroes_id:
                    hero.finish_working()

        buildings = data.building_list.get_all()
        for building in buildings:
            heroes_id = utils.split_to_int(building.hero_ids)
            for hero_id in heroes_id:
                if hero_id == 0:
                    continue;
                hero = data.hero_list.get(hero_id)
                if hero.place_type == hero.PLACE_TYPE_INVALID:
                    hero.assign_working_in_building(building.id, now)

        return True


    def delete(self, user_id, request):
        """删除用户数据
        """
        timer = Timer(user_id)

        req = internal_pb2.DeleteUserReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._delete_player, req, timer)
        defer.addCallback(self._delete_succeed, req, timer)
        defer.addErrback(self._delete_failed, req, timer)
        return defer


    def _delete_player(self, data, req, timer):
        if not data.is_valid():
            return data
        
        force = False
        if req.HasField("force") and req.force == True:
            force = True
        
        #删除用户数据:
        # 1. 删除联盟数据
        # 2. 删除史实城官职信息
        # 3. 删除用户数据

        union = data.union.get(True)
        if union is not None and force:
            # 退出联盟
            union_req = internal_union_pb2.InternalManageUnionReq()
            union_req.user_id = data.id
            union_req.op = union_pb2.ManageUnionReq.EXIT
            union_req.target_user_id = data.id

            defer = GlobalObject().remote['gunion'].callRemote(
                "manage_union", union.union_id, union_req.SerializeToString())
            defer.addCallback(self._delete_player_union, data)
            return defer
        
        return self._delete_player_union(None, data)

    def _delete_player_union(self, union_response, data):
        if union_response is not None:
            union_res = internal_union_pb2.InternalQueryUnionRes()
            union_res.ParseFromString(union_response)

            if union_res.status != 0:
                raise Exception("Exit union res error")
        
        # 删除史实城官职信息
        city_id_list = []
        for city in data.legendcity_list.get_all():
            city_id_list.append(city.city_id)
        
        defer = self._try_cancel_position_of_legendcity(data, city_id_list)
        defer.addCallback(self._delete_player_legendcity, data)
        return defer

    def _delete_player_legendcity(self, unit_res, data):
        assert unit_res.status == 0
        if unit_res.ret != legendcity_pb2.OK:
            raise Exception("Unit cancel position res error[res=%s]" % unit_res)

        # 删除用户数据
        data.delete()
        defer = DataBase().commit(data)
        defer.addCallback(self._delete_cache)
        return defer

    def _try_cancel_position_of_legendcity(self, data, city_id_list):
        """试图撤掉所有史诗城的官职"""
        unit_req = unit_pb2.UnitCancelPositionReq()
        unit_req.user_id = data.id
        unit_req.force = True
        city_id = city_id_list[-1]
        defer = GlobalObject().remote['unit'].callRemote(
                "cancel_position", city_id, unit_req.SerializeToString())
        defer.addCallback(self._recv_cancel_position_of_legendcity, data, city_id_list)
        return defer

    def _recv_cancel_position_of_legendcity(self, unit_response, data, city_id_list):
        unit_res = unit_pb2.UnitCancelPositionRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit cancel position res error[res=%s]" % unit_res)

        city_id_list.pop()
        if len(city_id_list) == 0 or unit_res.ret != legendcity_pb2.OK:
            return unit_res
        else:
            return self._try_cancel_position_of_legendcity(data, city_id_list)

    def _delete_cache(self, data):
        DataBase().clear_data(data)
        return data


    def _delete_succeed(self, data, req, timer):
        res = internal_pb2.DeleteUserRes()
        res.status = 0
        response = res.SerializeToString()

        logger.notice("Delete succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_failed(self, err, req, timer):
        logger.fatal("Delete failed[reason=%s]" % err)

        res = internal_pb2.DeleteUserRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def clear_cache(self, user_id, request):
        """清除用户数据缓存
        """
        timer = Timer(user_id)
        req = internal_pb2.DeleteUserReq()
        req.ParseFromString(request)

        DataBase().clear_data_by_id(user_id)

        res = internal_pb2.DeleteUserRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Clear cache succeed[id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def clear_users_cache(self, user_id, request):
        """清除用户数据缓存
        """
        timer = Timer(user_id)
        req = internal_pb2.ClearUsersCacheReq()
        req.ParseFromString(request)

        for user_id in req.users_id:
            DataBase().clear_data_by_id(user_id)

        res = internal_pb2.ClearUsersCacheRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Clear users cache succeed[id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def get_all(self, user_id, request):
        """获取所有 id
        """
        timer = Timer(user_id)
        req = internal_pb2.GetAllReq()
        req.ParseFromString(request)

        dumper = DataDumper()
        if req.type == req.USER:
            defer = dumper.get_all("user", "id")
        elif req.type == req.LEGENDCITY:
            defer = dumper.get_all("unitcity", "id")
        elif req.type == req.UNION:
            defer = dumper.get_all("unionunion", "id")
        defer.addCallback(self._calc_all_result, req, timer)
        return defer


    def _calc_all_result(self, ids, req, timer):
        res = internal_pb2.GetAllRes()
        res.status = 0
        for id in ids:
            res.ids.append(id)
        response = res.SerializeToString()
        logger.notice("Get all succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        return response


    def basic_info(self, user_id, request):
        """内部接口:获取用户基本信息"""
        timer = Timer(user_id)

        req = internal_pb2.GetUserBasicInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_basic_info, req, timer)
        defer.addErrback(self._basic_info_falied, req, timer)
        return defer

    def _calc_basic_info(self, data, req, timer):
        user = data.user.get(True)

        res = internal_pb2.GetUserBasicInfoRes()
        res.status = 0
        pack.pack_user_basic_info(user, res.user_info)

        return self._basic_info_succeed(data, req, res, timer)

    def _basic_info_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("query user basic info succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _basic_info_falied(self, err, req, timer):
        logger.fatal("query user basic info failed[reason=%s]" % err)
        res = internal_pb2.GetUserBasicInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("query user basic info failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def update_basic_info(self, user_id, request):
        """内部接口:更新用户基本信息"""
        timer = Timer(user_id)

        req = internal_pb2.UpdateUserBasicInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_basic_info, req, timer)
        defer.addErrback(self._update_basic_info_failed, req, timer)
        return defer
    
    def _calc_update_basic_info(self, data, req, timer):
        user = data.user.get()

        account_business.update_user_basic_info(user, req.user_info)

        res = internal_pb2.UpdateUserBasicInfoRes()
        res.status = 0

        defer = DataBase().commit(data)
        defer.addCallback(self._update_basic_info_succeed, req, res, timer)
        return defer

    def _update_basic_info_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("update user basic info succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _update_basic_info_failed(self, err, req, timer):
        logger.fatal("update user basic info failed[reason=%s]" % err)
        res = internal_pb2.UpdateUserBasicInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("update user basic info failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_inactivity_user(self, user_id, request):
        """删除不活跃的用户(内部接口)"""
        timer = Timer(user_id)

        req = internal_pb2.DeleteInactivityUsersReq()
        req.ParseFromString(request)

        dumper = DataDumper()
        defer = dumper.get_all("user", "id")
        defer.addCallback(self._calc_delete_dump, req, timer)
        defer.addErrback(self._delete_inactivity_failed, req, timer)
        return defer

    def _calc_delete_dump(self, ids, req, timer):
        matcher = UserMatcher()
        for id in ids:
            matcher.add_condition(id)

        defer = matcher.match()
        defer.addCallback(self._calc_delete_match, req, timer)
        return defer

    def _calc_delete_match(self, users, req, timer):
        def _delete_user(ids, index):
            user_id = ids[index]

            fwd_req = internal_pb2.DeleteUserReq()
            fwd_req.user_id = user_id
            fwd_req.force = True

            fwd_request = fwd_req.SerializeToString()
            defer = GlobalObject().root.callChild("portal", "forward_delete", user_id, fwd_request)
            defer.addCallback(_delete_user_result, ids, index + 1)
            return defer

        def _delete_user_result(fwd_response, ids, index):
            fwd_res = internal_pb2.DeleteUserRes()
            fwd_res.ParseFromString(fwd_response)
            if fwd_res.status != 0:
                #return False
                pass

            if index >= len(ids):
                return True

            defer = _delete_user(ids, index)
            return defer

        delete_ids = [
            id
            for id, user_info in users.items()
            if timer.now - user_info.last_login_time > req.day * 86400 and user_info.level <= req.level
        ]

        if len(delete_ids) == 0:
            return self._delete_inactivity_succeed(req, timer)

        defer = _delete_user(delete_ids, 0)
        defer.addCallback(self._calc_delete_do, req, timer)
        return defer

    def _calc_delete_do(self, result, req, timer):
        if result == False:
            raise Exception("delete user failed")
        
        return self._delete_inactivity_succeed(req, timer)

    def _delete_inactivity_succeed(self, req, timer):
        res = internal_pb2.DeleteUserRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Delete inactivity user succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _delete_inactivity_failed(self, err, req, timer):
        logger.fatal("Delete inactivity user failed[reason=%s]" % err)
        res = internal_pb2.DeleteUserRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete inactivity user failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_user_info_offline(self, user_id, request):
        """离线更新所有用户的数据，如资源(内部接口)"""
        timer = Timer(user_id)

        req = internal_pb2.UpdateUserInfoOfflineReq()
        req.ParseFromString(request)

        dumper = DataDumper()
        defer = dumper.get_all("user", "id")
        defer.addCallback(self._calc_update_user_info_offline_dump, req, timer)
        defer.addErrback(self._update_user_info_offline_failed, req, timer)
        return defer

    def _calc_update_user_info_offline_dump(self, ids, req, timer):
        matcher = UserMatcher()
        for id in ids:
            matcher.add_condition(id)

        defer = matcher.match()
        defer.addCallback(self._calc_update_user_info_offline_match, req, timer)
        return defer

    def _calc_update_user_info_offline_match(self, users, req, timer):
        def _update_user_info_offline(ids, index):
            user_id = ids[index]

            fwd_req = internal_pb2.UpdateUserInfoOfflineReq()
            fwd_req.user_id = user_id

            fwd_request = fwd_req.SerializeToString()
            defer = GlobalObject().root.callChild("portal", "forward_update_user_info_offline", user_id, fwd_request)
            defer.addCallback(_update_user_info_offline_result, ids, index + 1)
            return defer

        def _update_user_info_offline_result(fwd_response, ids, index):
            fwd_res = internal_pb2.UpdateUserInfoOfflineRes()
            fwd_res.ParseFromString(fwd_response)
            if fwd_res.status != 0:
                return False

            if index >= len(ids):
                return True

            defer = _update_user_info_offline(ids, index)
            return defer

        delete_ids = [id for id, user_info in users.items()]

        if len(delete_ids) == 0:
            return self._update_user_info_offline_succeed(req, timer)

        defer = _update_user_info_offline(delete_ids, 0)
        defer.addCallback(self._calc_update_user_info_offline_do, req, timer)
        return defer

    def _calc_update_user_info_offline_do(self, result, req, timer):
        if result == False:
            raise Exception("update user info offline failed")
        
        return self._update_user_info_offline_succeed(req, timer)

    def _update_user_info_offline_succeed(self, req, timer):
        res = internal_pb2.UpdateUserInfoOfflineRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Update user info offline succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def _update_user_info_offline_failed(self, err, req, timer):
        logger.fatal("Update user info offline failed[reason=%s]" % err)
        res = internal_pb2.UpdateUserInfoOfflineRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update user info offline failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def receive_update_user_info_offline(self, user_id, request):
        """内部接口:离线更新用户资源数据"""
        timer = Timer(user_id)

        req = internal_pb2.UpdateUserInfoOfflineReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_update_user_info_offline, req, timer)
        defer.addErrback(self._receive_update_user_info_offline_failed, req, timer)
        return defer
    
    def _calc_receive_update_user_info_offline(self, data, req, timer):
        
        #更新资源
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        #todo

        res = internal_pb2.UpdateUserInfoOfflineRes()
        res.status = 0

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_update_user_info_offline_succeed, req, res, timer)
        return defer

    def _receive_update_user_info_offline_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Receive update user info offline succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        logger.notice("111")
        DataBase().clear_data(data)
        return response

    def _receive_update_user_info_offline_failed(self, err, req, timer):
        logger.fatal("Receive update user info offline failed[reason=%s]" % err)
        res = internal_pb2.UpdateUserInfoOfflineRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Receive update user info offline failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response





