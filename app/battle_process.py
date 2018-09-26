#coding:utf8
"""
Created on 2015-10-28
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 战斗相关处理逻辑
"""

import random
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import battle_pb2
from proto import rival_pb2
from proto import internal_pb2
from proto import mail_pb2
from proto import unit_pb2
from proto import legendcity_pb2
from proto import broadcast_pb2
from proto import anneal_pb2
from proto import boss_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app.rival_matcher import RivalMatcher
from app.arena_matcher import ArenaMatcher
from app.melee_matcher import MeleeMatcher
from app.data.hero import HeroInfo
from app.data.node import NodeInfo
from app.data.mail import MailInfo
from app.data.rival import RivalInfo
from app.data.arena import ArenaInfo
from app.data.melee import MeleeInfo
from app.data.team import TeamInfo
from app.data.anneal import AnnealInfo
from app.data.arena_record import ArenaRecordInfo
from app.data.melee_record import MeleeRecordInfo
from app.data.legendcity import LegendCityInfo
from app.data.worldboss import WorldBossInfo
from app.business import map as map_business
from app.business import battle as battle_business
from app.business import mail as mail_business
from app.business import legendcity as legendcity_business
from app.business import account as account_business
from app.business import arena as arena_business
from app.business import melee as melee_business
from app.business import anneal as anneal_business
from app.business import worldboss as worldboss_business
from app.business import hero as hero_business
from app.business import appoint as appoint_business
from app.business import expand_dungeon as expand_dungeon_business
from app.business import plunder as plunder_business
from app import compare
from app import log_formater


class BattleProcessor(object):

    def start_battle(self, user_id, request):
        """开始战斗
        """
        timer = Timer(user_id)

        req = battle_pb2.StartBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_start_battle, req, timer)
        defer.addErrback(self._start_battle_failed, req, timer)
        return defer


    def _calc_start_battle(self, data, req, timer):
        """开战逻辑
        """
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        #参战队伍 & 英雄
        teams = []
        heroes = []
        for team_info in req.battle.attack_teams:
            if req.type == battle_pb2.BATTLE_MELEE:
                for hero_info in team_info.heroes:
                    if hero_info.basic_id != 0:
                        hero_id = HeroInfo.generate_id(data.id, hero_info.basic_id)
                        hero = data.hero_list.get(hero_id)
                        heroes.append(hero)

            elif req.type == battle_pb2.BATTLE_EXPANDDUNGEON:
                for hero_info in team_info.heroes:
                    if hero_info.basic_id != 0:
                        hero_id = HeroInfo.generate_id(data.id, hero_info.basic_id)
                        hero = data.hero_list.get(hero_id)
                        heroes.append(hero)
            else:
                team_id = TeamInfo.generate_id(data.id, team_info.index)
                team = data.team_list.get(team_id)
                if team is None:
                    continue
                teams.append(team)

                for hero_id in team.get_heroes():
                    if hero_id != 0:
                        hero = data.hero_list.get(hero_id)
                        heroes.append(hero)

                # for hero_info in team_info.heroes:
                #     if hero_info.basic_id != 0:
                #         hero_id = HeroInfo.generate_id(data.id, hero_info.basic_id)
                #         hero = data.hero_list.get(hero_id)
                #         heroes.append(hero)

        dungeon_ret = -1
        #敌人信息
        mail = None
        node = None
        if req.type == battle_pb2.BATTLE_REVENGE:#复仇
            mail_index = req.mail_index
            mail_id = MailInfo.generate_id(data.id, mail_index)
            mail = data.mail_list.get(mail_id)

            node_id = RivalInfo.generate_revenge_id(data.id)
            node = data.node_list.get(node_id)

            rival_id = node_id
            rival = data.rival_list.get(rival_id)

            if mail.related_enemy_user_id != rival.rival_id:
                raise Exception("Revenge error[revenge user id=%d][mail user id=%d]" %
                        (rival.rival_id, mail.related_enemy_user_id))

        elif req.type == battle_pb2.BATTLE_NODE:
            node_basic_id = req.node.basic_id
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            rival_id = node_id
            node = data.node_list.get(node_id)
            rival = data.rival_list.get(rival_id)

            rival.reward_user_exp = 0
            if 'is_battle_cost_energy' in account_business.get_flags():
                if node.rival_type in (NodeInfo.ENEMY_TYPE_PVE_BANDIT, NodeInfo.ENEMY_TYPE_PVE_REBEL):
                    """山贼"""
                    rival.reward_user_exp = int(float(data_loader.OtherBasicInfo_dict['bandit_battle_cost_energy'].value))
                elif node.rival_type == NodeInfo.ENEMY_TYPE_DUNGEON:
                    """外敌入侵"""
                    rival.reward_user_exp = int(float(data_loader.OtherBasicInfo_dict['dungeon_battle_cost_energy'].value))
                else:
                    """侦察敌军"""
                    rival.reward_user_exp = int(float(data_loader.OtherBasicInfo_dict['keynode_battle_cost_energy'].value))

            logger.debug("start battle in node"
                    "[basic id=%d][event type=%d]" % (node.basic_id, node.event_type))

        elif req.type == battle_pb2.BATTLE_ARENA:
            arena = data.arena.get()
            node_id = arena_business.start_battle(data, arena, timer.now)
            node = data.node_list.get(node_id)
            if node is None:
                #raise Exception("Arena is not open")
                logger.warning("Arena is not open")
                NOT_IN_BATTLE_TIME = 6
                defer = DataBase().commit(data)
                defer.addCallback(self._start_battle_succeed, node, None, req, timer,
                        battle_ret=NOT_IN_BATTLE_TIME)
                return defer

            rival_id = arena.get_arena_rival_id(req.arena.user_id)
            rival = data.rival_list.get(rival_id)
            logger.debug("start battle in arena[rival id=%d]" % rival_id)

        elif req.type == battle_pb2.BATTLE_MELEE:
            melee = data.melee.get()
            node_id = melee_business.start_battle(data, melee, timer.now)
            node = data.node_list.get(node_id)
            if node is None:
                raise Exception("Melee is not open")
            rival_id = melee.get_arena_rival_id(req.arena.user_id)
            rival = data.rival_list.get(rival_id)
            #记录下攻击阵容
            heroes_basic_id = []
            heroes_position = []
            for team_info in req.battle.attack_teams:
                for hero_info in team_info.heroes:
                    heroes_basic_id.append(hero_info.basic_id)
                for position in team_info.hero_positions:
                    heroes_position.append(position)

            melee.set_heroes_position(heroes_basic_id, heroes_position)

            logger.debug("start battle in melee[id=%d][rival id=%d]" % (rival.id, rival_id))

        elif req.type == battle_pb2.BATTLE_LEGENDCITY:
            city_id = LegendCityInfo.generate_id(data.id, req.city_id)
            legendcity = data.legendcity_list.get(city_id)
            node_id = legendcity.node_id
            node = data.node_list.get(node_id)
            logger.debug("Get rival for legendcity[rival_id=%d]" % legendcity.node_id)
            rival = data.rival_list.get(node_id)
            logger.debug("Start battle in legendcity")
            return self._start_battle_of_legendcity(
                    data, legendcity, node, rival, heroes, req, timer)

        elif req.type == battle_pb2.BATTLE_ANNEAL:
            anneal = data.anneal.get()
            if not anneal_business.start_battle(data, anneal, req.anneal_type, 
                    req.anneal_floor, req.anneal_level, timer.now):
                raise Exception("anneal start battle failed")

            node_id = anneal.generate_anneal_node_id()
            node = data.node_list.get(node_id)
 
            rival_id = anneal.generate_anneal_rival_id(req.anneal_type)
            rival = data.rival_list.get(rival_id)
 
            logger.debug("Start battle in anneal")

        elif req.type == battle_pb2.BATTLE_WORLD_BOSS:
            worldboss = data.worldboss.get()
            node_basic_id = worldboss.get_node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id)
            rival = data.rival_list.get(node_id)
            logger.debug("worldboss rival[node_id=%d][rival_id=%d]" % (node_id, rival.id))
 
            logger.debug("Start battle in worldboss")
            return self._start_battle_of_worldboss(
                    data, worldboss, node, rival, heroes, req, timer)

        elif req.type == battle_pb2.BATTLE_EXPANDDUNGEON:
            if req.HasField("expanddungeon_battle_level"):
                battle_level = req.expanddungeon_battle_level
            else:
                battle_level = 0

            dungeon = expand_dungeon_business.get_dungeon_by_id(data, req.dungeon_id)
            dungeon_ret = expand_dungeon_business.start_battle(data, dungeon, battle_level, timer.now)

            node_basic_id = dungeon.node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id)
            rival = data.rival_list.get(node_id)

            logger.debug("Start battle expand dungeon")

        elif req.type == battle_pb2.BATTLE_PLUNDER:
            plunder = data.plunder.get()
            plunder.consume_attack_num()
            node_id = NodeInfo.generate_id(data.id, 
                    int(float(data_loader.MapConfInfo_dict['plunder_node_basic_id'].value)))
            node = data.node_list.get(node_id)
            rival_id = plunder.get_plunder_rival_id(req.plunder_user_id)
            rival = data.rival_list.get(rival_id)
            logger.debug("start battle in arena[rival id=%d]" % rival_id)
 

        elif req.type == battle_pb2.BATTLE_PLUNDER_ENEMY:
            plunder = data.plunder.get()
            plunder.consume_attack_num()
            node_id = NodeInfo.generate_id(data.id, 
                    int(float(data_loader.MapConfInfo_dict['plunder_node_basic_id'].value)))
            node = data.node_list.get(node_id)
            rival_id = plunder.generate_specify_rival_id()
            rival = data.rival_list.get(rival_id)
            logger.debug("start battle in arena[rival id=%d]" % rival_id)       

        else:
            raise Exception("Invalid battle type")

        #TODO 以后这个 force 值要传
        if not battle_business.start_battle(
                data, node, rival, mail, teams, heroes, timer.now, True):
            raise Exception("Start battle failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._start_battle_succeed, node, rival, req, timer,
                dungeon_ret=dungeon_ret)
        return defer


    def _start_battle_succeed(self, data, node, rival, req, timer,
            worldboss_ret = -1, dungeon_ret = -1, battle_ret = -1):
        res = battle_pb2.StartBattleRes()
        res.status = 0

        battle = data.battle_list.get(node.id, True)
        if battle is not None:
            pack.pack_battle_reward_info(battle, res.reward)
        pack.pack_resource_info(data.resource.get(True), res.resource)
        conscript_list = data.conscript_list.get_all(True)
        for conscript in conscript_list:
            pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)

        if worldboss_ret != -1:
            res.world_boss_ret = worldboss_ret
        if dungeon_ret != -1:
            res.dungeon_ret = dungeon_ret
        if battle_ret != -1:
            res.battle_ret = battle_ret

        response = res.SerializeToString()
        if rival is not None:
            log = log_formater.output_battle(data, node.id, rival, "Start battle succeed",
                    req, res, timer.count_ms())
            logger.notice(log)

        return response


    def _start_battle_failed(self, err, req, timer):
        logger.fatal("Start battle failed[reason=%s]" % err)
        res = battle_pb2.StartBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start battle failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def finish_battle(self, user_id, request):
        """结束战斗
        """
        timer = Timer(user_id)

        req = battle_pb2.FinishBattleReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_finish_battle, req, timer)
        defer.addErrback(self._finish_battle_failed, req, timer)
        return defer


    def _calc_finish_battle(self, data, req, timer):
        """结束战斗逻辑
        """
        skip = False
        if req.HasField("is_skip") and req.is_skip == True:
            #跳过战斗
            skip = True
            #不允许跳过战斗的类型
            if req.type in [battle_pb2.BATTLE_WORLD_BOSS, battle_pb2.BATTLE_MELEE,
                            battle_pb2.BATTLE_ARENA, battle_pb2.BATTLE_ANNEAL]:
                return self._pack_finish_battle_failed_response(data, req,
                    battle_pb2.BATTLE_CONNOT_SKIP, timer)

        node = None
        win = True if req.battle.result == req.battle.WIN else False
        trainer = data.trainer.get()
        is_plunder = False
        battle_level = 0
        if req.type == battle_pb2.BATTLE_NODE:
            node_basic_id = req.node.basic_id
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id, True)
        elif req.type == battle_pb2.BATTLE_ARENA:
            node_basic_id = data.arena.get(True).get_node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id, True)
            #记录次数
            trainer.add_daily_arena_num(1)
        elif req.type == battle_pb2.BATTLE_MELEE:
            node_basic_id = data.melee.get(True).get_node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id, True)
        elif req.type == battle_pb2.BATTLE_REVENGE:
            node_id = NodeInfo.generate_id(data.id, 0)     #0表示主城
        elif req.type == battle_pb2.BATTLE_LEGENDCITY:
            legendcity = data.legendcity_list.get(
                LegendCityInfo.generate_id(data.id, req.city_id))
            node_id = legendcity.node_id
            node = data.node_list.get(node_id, True)
            #记录次数
            trainer.add_daily_battle_legendcity(1)

        elif req.type == battle_pb2.BATTLE_ANNEAL:
            anneal = data.anneal.get(True)
            node_id = anneal.generate_anneal_node_id()
            #记录次数
            if win:
                if anneal.current_type == AnnealInfo.NORMAL_MODE:
                    trainer.add_daily_battle_anneal_normal(1)
                elif anneal.current_type == AnnealInfo.HARD_MODE:
                    trainer.add_daily_battle_anneal_hard(1)
                
        elif req.type == battle_pb2.BATTLE_WORLD_BOSS:
            worldboss = data.worldboss.get()
            node_basic_id = worldboss.get_node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id, True)
        elif req.type == battle_pb2.BATTLE_EXPANDDUNGEON:
            if req.HasField("expanddungeon_battle_level"):
                battle_level = req.expanddungeon_battle_level
            else:
                battle_level = 0

            dungeon = expand_dungeon_business.get_dungeon_by_id(data, req.dungeon_id)
            dungeon.daily_update(timer.now)
            win = True if req.battle.result == req.battle.WIN else False
            ret = expand_dungeon_business.finish_battle(data, dungeon, timer.now,
                    dungeon_level=req.dungeon_level, win=win)
            node_basic_id = dungeon.node_basic_id()
            node_id = NodeInfo.generate_id(data.id, node_basic_id)
            node = data.node_list.get(node_id, True)
            #记录次数
            if dungeon.basic_id == 1:
                trainer.add_daily_battle_expand_one(1)
            elif dungeon.basic_id == 2:
                trainer.add_daily_battle_expand_two(1)
            elif dungeon.basic_id == 3:
                trainer.add_daily_battle_expand_three(1)
        elif req.type == battle_pb2.BATTLE_PLUNDER:
            is_plunder = True
            win = True if req.battle.result == req.battle.WIN else False
            plunder = data.plunder.get()
            node_id = NodeInfo.generate_id(data.id, 
                    int(float(data_loader.MapConfInfo_dict['plunder_node_basic_id'].value)))
            node = data.node_list.get(node_id)
            #rival_id = plunder.get_plunder_rival_id(req.plunder_user_id)
            #rival = data.rival_list.get(rival_id)

        elif req.type == battle_pb2.BATTLE_PLUNDER_ENEMY:
            is_plunder = True
            win = True if req.battle.result == req.battle.WIN else False
            plunder = data.plunder.get()
            node_id = NodeInfo.generate_id(data.id, 
                    int(float(data_loader.MapConfInfo_dict['plunder_node_basic_id'].value)))
            node = data.node_list.get(node_id)
            #rival_id = plunder.generate_specify_rival_id()
            #rival = data.rival_list.get(rival_id)

        battle = data.battle_list.get(node_id)
        logger.debug("battle rival[node id=%d][rival id=%d]" % (battle.node_id, battle.rival_id))
        rival = data.rival_list.get(battle.rival_id, True)

        if (req.type == battle_pb2.BATTLE_NODE or req.type == battle_pb2.BATTLE_PLUNDER 
                or req.type == battle_pb2.BATTLE_PLUNDER_ENEMY):
            #大地图上攻取、掠夺模式等生效
            if win and rival.type != NodeInfo.ENEMY_TYPE_PVE_RESOURCE:
                enemy = plunder_business.get_plunder_enemy(data, rival.rival_id)
                if enemy is None:
                    plunder_business.add_plunder_enemy(data, rival.rival_id, 
                            rival.name, rival.level, rival.icon_id, rival.country, 
                            rival.score, battle.reward_money, battle.reward_food)
                else:
                    plunder_business.modify_plunder_enemy_by_attack(
                            enemy, battle.reward_money, battle.reward_food)
                    
        teams = []
        for team_index in battle.get_battle_team():
            team_id = TeamInfo.generate_id(data.id, team_index)
            teams.append(data.team_list.get(team_id))

        heroes = []
        for hero_id in battle.get_battle_hero():
            hero = hero_business.get_hero_by_id(data, hero_id)
            heroes.append(hero)

        #判断玩家是否使用加速作弊
        if not skip:
            if battle_business.is_speed_cheat(data, node, req.battle.battle_limit_time, timer.now):
                return self._pack_finish_battle_failed_response(
                    data, req, battle_pb2.BATTLE_SPEED_UP, timer)

        #战斗结果
        if not skip:
            own_soldier_info = []
            for result in req.battle.attack_heroes:
                hero_basic_id = result.hero.basic_id
                hero_id = HeroInfo.generate_id(data.id, hero_basic_id)
                hero = data.hero_list.get(hero_id, True)
                own_soldier_info.append((
                    hero.soldier_basic_id,
                    hero.soldier_level,
                    result.soldier_survival))

            enemy_soldier_info = []
            if req.battle.HasField("relive_times"):
                for i in range(req.battle.relive_times):
                    for result in req.battle.defence_heroes:
                        #攻打世界boss时有重生逻辑，实际杀敌会更多
                        enemy_soldier_info.append((
                            result.hero.soldier_basic_id,
                            result.hero.soldier_level,
                            0))

            for result in req.battle.defence_heroes:
                enemy_soldier_info.append((
                    result.hero.soldier_basic_id,
                    result.hero.soldier_level,
                    result.soldier_survival))

            if req.battle.result == req.battle.WIN:
                win = True
            else:
                win = False
        else:
            (win, own_soldier_info, enemy_soldier_info) = \
                appoint_business.calc_battle_result(data, battle, rival, teams, heroes)

        if req.type == battle_pb2.BATTLE_LEGENDCITY:
            return self._finish_battle_of_legendcity(
                    data, own_soldier_info, enemy_soldier_info, heroes, win, skip, req, timer)
        elif req.type == battle_pb2.BATTLE_WORLD_BOSS:
            return self._finish_battle_of_worldboss(
                    data, own_soldier_info, enemy_soldier_info, req, timer)
        
        rival_user_id = 0
        if rival is not None:
            rival_user_id = rival.rival_id
        if rival != None and rival.is_arena_player():
            arena = data.arena.get()
            arena_origin_score = ArenaInfo.get_real_score(arena.score)
        if rival != None and rival.is_melee_player():
            melee = data.melee.get()
            melee_origin_score = MeleeInfo.get_real_score(melee.score)

        need_notice = False
        if node is not None and node.is_rival_pvp() and rival.is_real_player():
            #PVP战斗需要发送邮件
            need_notice = True
            rival_type = node.rival_type
        elif rival != None and rival.is_revenge_rival() and rival.is_real_player():
            #复仇需要发送通知邮件
            need_notice = True
            rival_type = NodeInfo.ENEMY_TYPE_PVP_CITY
        elif req.type == battle_pb2.BATTLE_PLUNDER:
            #掠夺模式需要发送邮件通知
            need_notice = True
            rival_type = NodeInfo.ENEMY_TYPE_PLUNDER
        elif req.type == battle_pb2.BATTLE_PLUNDER_ENEMY:
            #掠夺模式中的复仇或指定玩家战斗，需要发送邮件通知
            need_notice = True
            rival_type = NodeInfo.ENEMY_TYPE_PLUNDER_ENEMY

        change_nodes = []
        new_items = []
        new_mails = []
        new_arena_records = []

        reward_money = 0
        reward_food = 0
        if win:
            if battle is not None:
                reward_money = battle.reward_money
                reward_food = battle.reward_food
            if not battle_business.win_battle(
                    data, node, enemy_soldier_info, own_soldier_info,
                    change_nodes, timer.now, new_arena_records, is_plunder = is_plunder):
                raise Exception("Win battle failed")
        else:
            if not battle_business.lose_battle(
                    data, node, timer.now, enemy_soldier_info, own_soldier_info,
                    change_nodes, new_items, new_mails, new_arena_records):
                raise Exception("Lost battle failed")

        if not skip:
            #检查请求
            if win:
                compare.check_user(data, req.monarch, with_level = True)
                #for info in req.battle.attack_heroes:
                #    compare.check_hero(data, info.hero, with_level = True)
                for item_info in req.items:
                    compare.check_item(data, item_info)

        #通知敌对玩家
        if need_notice and not rival.is_arena_player():
            user = data.user.get(True)
            guard = data.guard_list.get(data.id, True)
            self._notice_battle_result(user, guard, win, rival_user_id, rival_type, 
                    reward_money, reward_food)

        #通知演武场的对手
        if rival != None and rival.is_arena_player():
            user = data.user.get(True)
            arena = data.arena.get(True)
            if not arena.is_arena_rival_pve(rival_user_id):
                self._notice_arena_result(
                        user, win, arena, rival_user_id, arena_origin_score)
            if arena_business.is_need_broadcast_win_num(arena):
                #演武场连胜发广播
                try:
                    self._add_arena_broadcast_win_num(user, arena)
                except:
                    logger.warning("Send arena broadcast failed")

            arena_matcher = ArenaMatcher()
            #打赢了需要重新匹配对手
            defer = arena_matcher.match(data, arena)

        #通知乱斗场的对手
        if rival != None and rival.is_melee_player():
            user = data.user.get(True)
            melee = data.melee.get(True)
            if not melee.is_arena_rival_pve(rival_user_id):
                self._notice_melee_result(
                        user, win, melee, rival_user_id, melee_origin_score)
            if melee_business.is_need_broadcast_win_num(melee):
                #演武场连胜发广播
                try:
                    self._add_melee_broadcast_win_num(user, melee)
                except:
                    logger.warning("Send melee broadcast failed")

            melee_matcher = MeleeMatcher()
            #打赢了需要重新匹配对手
            defer = melee_matcher.match(data, melee)
            
        #试炼场需要更新记录
        #if rival != None and rival.is_anneal_rival():
        if req.type == battle_pb2.BATTLE_ANNEAL:
            anneal = data.anneal.get()
            user = data.user.get()

            self._update_anneal_record(user, anneal, timer.now)
            anneal_business.finish_battle(data, anneal, win)

        #为新刷出的敌方节点匹配敌人
        invalid_rival = [data.id]
        for node in data.node_list.get_all(True):
            if node.is_rival_pvp() and node.is_enemy_complete():
                rival_id = node.id
                rival_tmp = data.rival_list.get(rival_id, True)
                invalid_rival.append(rival_tmp.rival_id)

        user = data.user.get(True)
        matcher = RivalMatcher(user.level, invalid_rival)
        for node in change_nodes:
            if node.is_lack_enemy_detail():
                matcher.add_condition(data, node)

        defer = matcher.match(user.country)
        defer.addCallback(self._pack_finish_battle_response,
                data, rival, change_nodes, new_items, new_mails,
                new_arena_records, req, timer, skip=skip, win=win,
                own_soldier_info=own_soldier_info, heroes=heroes,
                expand_battle_level=battle_level)
        return defer

    def _pack_finish_battle_failed_response(self, data, req, ret, timer):
        res = battle_pb2.FinishBattleRes()
        res.status = 0
        res.battle_ret = ret

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_battle_succeed, req, res, timer)
        return defer

    def _pack_finish_battle_response(self, matcher, data, rival,
            node_list, new_items, new_mails, new_arena_records, req, timer, world_boss_ret = -1,
            skip = False, win = False, own_soldier_info=[], heroes=[], expand_battle_level = 0):
        """打包结束战斗响应
        """
        resource = data.resource.get(True)
        conscript_list = data.conscript_list.get_all(True)

        res = battle_pb2.FinishBattleRes()
        res.status = 0
        res.battle_ret = battle_pb2.BATTLE_OK

        pack.pack_resource_info(resource, res.resource)
        for conscript in conscript_list:
            pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)
        for node in node_list:
            pack.pack_node_info(data, node, res.nodes.add(), timer.now)

        for item in new_items:
            item_message = res.items.add()
            item_message.basic_id = item[1]
            item_message.num = item[0]
        for mail in new_mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        if rival != None and rival.is_arena_player():
            arena = data.arena.get(True)
            pack.pack_arena_info(
                    data.user.get(True), arena, res.arena, timer.now, with_own = False)
            for record in new_arena_records:
                pack.pack_arena_record(record, res.arena.records.add())
            #胜场奖励
            if arena.is_able_to_get_win_num_reward():
                pack.pack_arena_reward_info(arena, res.arena.win_num_reward)
            #对手信息
            rivals_id = arena.generate_arena_rivals_id()
            for rival_id in rivals_id:
                rival = data.rival_list.get(rival_id, True)
                if rival is not None:
                    pack.pack_arena_player(rival, res.arena.rivals.add())
            #系统选定的对战对手
            choose_rival_id = arena.get_choose_rival_id()
            choose_rival = data.rival_list.get(choose_rival_id, True)
            res.arena.choosed_user_id = choose_rival.rival_id

        if rival != None and rival.is_melee_player():
            melee = data.melee.get(True)
            pack.pack_melee_info(
                    data.user.get(True), melee, res.arena, timer.now, with_own = False)
            for record in new_arena_records:
                pack.pack_arena_record(record, res.arena.records.add())
            #胜场奖励
            if melee.is_able_to_get_win_num_reward():
                pack.pack_arena_reward_info(melee, res.arena.win_num_reward)
            #对手信息
            rivals_id = melee.generate_arena_rivals_id()
            for rival_id in rivals_id:
                rival = data.rival_list.get(rival_id, True)
                pack.pack_melee_player(rival, res.arena.rivals.add())

        if world_boss_ret != -1:
            res.world_boss_ret = world_boss_ret
            pack.pack_worldboss_info(data.worldboss.get(True), data.user.get(True),
                    res.boss, timer.now)

        if skip:
            pack.pack_monarch_info(data.user.get(True), res.monarch)
            if win:
                res.battle.result = battle_pb2.BattleOutputInfo.WIN
            else:
                res.battle.result = battle_pb2.BattleOutputInfo.LOSE
            
            for i, hero in enumerate(heroes):
                attack_hero = res.battle.attack_heroes.add()
                pack.pack_hero_info(hero, attack_hero.hero, timer.now)
                attack_hero.soldier_survival = own_soldier_info[i][2]

        if req.type == battle_pb2.BATTLE_EXPANDDUNGEON:
            dungeon = expand_dungeon_business.get_dungeon_by_id(data, req.dungeon_id)
            pack.pack_expand_dungeon_info(dungeon, data.user.get(True), res.dungeon, 
                    expand_battle_level, timer.now)

        if 'is_battle_cost_energy' in account_business.get_flags():
            energy = data.energy.get()
            energy.update_current_energy(timer.now)
            pack.pack_energy_info(energy, res.energy, timer.now)

        map_business.check_map_data(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._finish_battle_succeed, req, res, timer)
        return defer


    def _finish_battle_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Finish battle succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _finish_battle_failed(self, err, req, timer):
        logger.fatal("Finish battle failed[reason=%s]" % err)
        res = battle_pb2.FinishBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Finish battle failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _notice_battle_result(self, user, guard, win, rival_user_id, rival_type, reward_money, reward_food):
        """通知敌对玩家战斗结果
        Args:
            rival_user_id[int]: 敌对玩家 user id
            win[bool]: 战斗结果
            rob[bool]: 是否掠夺敌对玩家的资源
        """
        req = internal_pb2.BattleResultNoticeReq()
        req.user_id = rival_user_id
        req.win = not win
        req.rival_name = user.get_readable_name()
        req.rival_user_id = user.id
        req.rival_type = rival_type
        req.rival_level = user.level
        req.rival_icon_id = user.icon_id
        req.rival_score = guard.score
        req.rival_country = user.country
        req.lost_money = reward_money
        req.lost_food = reward_food
        request = req.SerializeToString()

        logger.debug("Notice battle result[req=%s]" % req)
        defer = GlobalObject().root.callChild(
                'portal', "forward_battle_notice", rival_user_id, request)
        defer.addCallback(self._check_notice_battle_result)
        return defer


    def _check_notice_battle_result(self, response):
        res = internal_pb2.BattleResultNoticeRes()
        res.ParseFromString(response)

        if res.status != 0:
            logger.warning("Notice battle result failed")
            #raise Exception("Notice battle result failed")


    def _notice_arena_result(self, user, win, arena, rival_id, arena_score):
        """通知对战的演武场玩家
        Args:
            win[bool]: 战斗结果
        """
        if win:
            status = ArenaRecordInfo.STATUS_DEFEND_LOSE
        else:
            status = ArenaRecordInfo.STATUS_DEFEND_WIN

        req = internal_pb2.ArenaResultNoticeReq()
        req.user_id = rival_id
        req.rival_name = user.get_readable_name()
        req.rival_user_id = user.id
        req.rival_level = user.level
        req.rival_icon_id = user.icon_id
        req.status = status
        req.rival_score = arena_score
        request = req.SerializeToString()

        logger.debug("Notice arena result[req=%s]" % req)
        defer = GlobalObject().root.callChild(
                'portal', "forward_arena_notice", rival_id, request)
        defer.addCallback(self._check_notice_arena_result)
        return defer


    def _check_notice_arena_result(self, response):
        res = internal_pb2.ArenaResultNoticeRes()
        res.ParseFromString(response)

        if res.status != 0:
            logger.warning("Notice arena result failed")
            #raise Exception("Notice arena result failed")


    def _add_arena_broadcast_win_num(self, user, arena):
        """广播玩家演武场战况
        Args:

        """
        (mode, priority, life_time, content) = arena_business.create_broadcast_content_win_num(user, arena)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add arena broadcast win num[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_arena_broadcast_win_num_result)
        return defer


    def _check_add_arena_broadcast_win_num_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast win num result failed")

        return True


    def _notice_melee_result(self, user, win, melee, rival_id, melee_score):
        """通知对战的乱斗场玩家
        Args:
            win[bool]: 战斗结果
        """
        if win:
            status = MeleeRecordInfo.STATUS_DEFEND_LOSE
        else:
            status = MeleeRecordInfo.STATUS_DEFEND_WIN

        req = internal_pb2.ArenaResultNoticeReq()
        req.user_id = rival_id
        req.rival_name = user.get_readable_name()
        req.rival_user_id = user.id
        req.rival_level = user.level
        req.rival_icon_id = user.icon_id
        req.status = status
        req.rival_score = melee_score
        request = req.SerializeToString()

        logger.debug("Notice melee result[req=%s]" % req)
        defer = GlobalObject().root.callChild(
                'portal', "forward_melee_notice", rival_id, request)
        defer.addCallback(self._check_notice_melee_result)
        return defer


    def _check_notice_melee_result(self, response):
        res = internal_pb2.ArenaResultNoticeRes()
        res.ParseFromString(response)

        if res.status != 0:
            logger.warning("Notice melee result failed")
            #raise Exception("Notice melee result failed")


    def _add_melee_broadcast_win_num(self, user, arena):
        """广播玩家乱斗场战况
        Args:

        """
        (mode, priority, life_time, content) = melee_business.create_broadcast_content_win_num(user, arena)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add melee broadcast win num[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_melee_broadcast_win_num_result)
        return defer


    def _check_add_melee_broadcast_win_num_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add melee broadcast win num result failed")

        return True


    def _start_battle_of_legendcity(self, data, legendcity, node, rival, heroes, req, timer):
        """史实城战斗开始
        1 查询是否可以攻击
        2 查询双方段位和锁定状态
        3 锁定对手
        4 如果在其他史实城有官职，取消官职
        """
        if not legendcity.is_able_to_attack():
            raise Exception("Not able to start legend city battle[attack count=%d]" %
                    legendcity.attack_count)
        legendcity.add_attack_count()

        city_id_list = []
        for city in data.legendcity_list.get_all():
            if city.city_id != legendcity.city_id:
                city_id_list.append(city.city_id)

        defer = self._try_cancel_position_of_legendcity(data, city_id_list)
        defer.addCallback(self._calc_start_battle_of_legendcity,
                data, legendcity, node, rival, heroes, req, timer)
        return defer


    def _calc_start_battle_of_legendcity(self,
            unit_res, data, legendcity, node, rival, heroes, req, timer):
        """
        """
        #取消官职不成功
        if unit_res.ret != legendcity_pb2.OK:
            return self._start_battle_of_legendcity_invalid(data, unit_res, req, timer)

        unit_req = unit_pb2.UnitCheckLegendCityReq()
        unit_req.user_id = data.id
        unit_req.rival_id = rival.rival_id
        unit_req.rival_position_level = rival.legendcity_position_level

        defer = GlobalObject().remote['unit'].callRemote(
                "start_battle", legendcity.city_id, unit_req.SerializeToString())
        defer.addCallback(self._check_start_battle_of_legendcity,
                data, node, rival, heroes, req, timer)
        return defer


    def _try_cancel_position_of_legendcity(self, data, city_id_list):
        """取消史实城的官职
        """
        unit_req = unit_pb2.UnitCancelPositionReq()
        unit_req.user_id = data.id
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


    def _check_start_battle_of_legendcity(
            self, unit_response, data, node, rival, heroes, req, timer):
        unit_res = unit_pb2.UnitCheckLegendCityRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit res error[res=%s]" % unit_res)

        #如果对手已经处于不合法的状态，返回原因
        if unit_res.ret != legendcity_pb2.OK:
            return self._start_battle_of_legendcity_invalid(data, unit_res, req, timer)

        #如果直接挑战太守，花费元宝
        legendcity = data.legendcity_list.get(
                LegendCityInfo.generate_id(data.id, req.city_id))

        need_gold = legendcity.calc_challenge_cost(
                unit_res.user_position_level, unit_res.rival_position_level)
        log = log_formater.output_gold(data, -need_gold, log_formater.LEGENDCITY_LEADER,
                "battle leader direct")
        logger.notice(log)
        if need_gold != 0 and need_gold != req.cost_gold:
            raise Exception("Challenge gold error[need=%d][cost=%d]" %
                    (need_gold, req.cost_gold))
        resource = data.resource.get()
        if not resource.cost_gold(need_gold):
            raise Exception("Cost gold failed")

        #TODO 以后这个 force 值要传
        if not battle_business.start_battle(
                data, node, rival, None, [], heroes, timer.now, True):
            raise Exception("Start battle failed")
        defer = DataBase().commit(data)
        defer.addCallback(self._start_battle_succeed, node, rival, req, timer)
        return defer


    def _start_battle_of_legendcity_invalid(self, data, unit_res, req, timer):
        assert unit_res.ret != legendcity_pb2.OK

        res = battle_pb2.StartBattleRes()
        res.status = 0
        res.ret = unit_res.ret
        if unit_res.HasField("unlock_time"):
            res.unlock_time = unit_res.unlock_time

        response = res.SerializeToString()
        logger.notice("Start battle failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_battle_of_legendcity(
            self, data, own_soldier_info, enemy_soldier_info, heroes, win, skip, req, timer):
        """史实城战斗结束
        1 判断是否超过时间限制
        2 解锁对手
        """
        legendcity = data.legendcity_list.get(
                LegendCityInfo.generate_id(data.id, req.city_id))
        rival = data.rival_list.get(legendcity.node_id, True)

        unit_req = unit_pb2.UnitCheckLegendCityReq()
        unit_req.user_id = data.id
        unit_req.rival_id = rival.rival_id
        unit_req.rival_position_level = rival.legendcity_position_level
        unit_req.win = win

        defer = GlobalObject().remote['unit'].callRemote(
                "finish_battle", req.city_id, unit_req.SerializeToString())
        defer.addCallback(self._check_finish_battle_of_legendcity,
                data, own_soldier_info, enemy_soldier_info, heroes, win, skip, req, timer)
        return defer


    def _check_finish_battle_of_legendcity(
            self, unit_response, data, own_soldier_info, enemy_soldier_info,
            heroes, win, skip, req, timer):
        """结算史实城战斗结果
        """
        unit_res = unit_pb2.UnitCheckLegendCityRes()
        unit_res.ParseFromString(unit_response)
        if unit_res.status != 0:
            raise Exception("Unit res error[res=%s]" % unit_res)

        #如果对手已经处于不合法的状态，战斗算失败，返回原因
        if unit_res.ret != legendcity_pb2.OK:
            win = False

        user = data.user.get(True)
        legendcity = data.legendcity_list.get(
                LegendCityInfo.generate_id(data.id, req.city_id))
        node = data.node_list.get(legendcity.node_id)
        rival = data.rival_list.get(legendcity.node_id)
        rival_id = rival.rival_id

        guard = data.guard_list.get(data.id, True)

        #添加战斗记录
        record = legendcity_business.add_battle_record(data, legendcity)
        record.set_result(win, True, timer.now)
        if win:
            user_position_level = unit_res.rival_position_level
        else:
            user_position_level = unit_res.user_position_level
        record.set_user(user, guard.get_team_score(),
                user_position_level, legendcity.buffs)
        record.set_rival(rival,
                rival.legendcity_position_level, rival.legendcity_buffs)

        change_nodes = []
        new_items = []
        new_mails = []
        new_arena_records = []
        if win:
            if not battle_business.win_battle(
                    data, node, enemy_soldier_info, own_soldier_info,
                    change_nodes, timer.now, new_arena_records, is_legendcity = True):
                raise Exception("Win battle failed")
        else:
            if not battle_business.lose_battle(
                    data, node, timer.now, enemy_soldier_info, own_soldier_info,
                    change_nodes, new_items, new_mails, new_arena_records):
                raise Exception("Lost battle failed")

        #添加初始 buff
        if win:
            legendcity.add_default_buff(unit_res.user_position_level, timer.now)

        #通知对手
        (rival_id, is_robot, rival_postion_level) = legendcity.get_rival_info(rival_id)
        if not is_robot:
            self._notice_legendcity_battle_result(req.city_id, rival_id, record)

        #检查请求
        if win:
            compare.check_user(data, req.monarch, with_level = True)
            #for info in req.battle.attack_heroes:
            #    compare.check_hero(data, info.hero, with_level = True)
            for item_info in req.items:
                compare.check_item(data, item_info)

            #玩家获得太守等职位，要播广播
            if legendcity_business.is_need_broadcast(unit_res.user_position_level):
                try:
                    self._add_legendcity_leader_broadcast(user, legendcity.city_id, unit_res.user_position_level)
                except:
                    logger.warning("Send add legendcity leader broadcast failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._pack_finish_battle_of_legendcity_response, unit_res.ret,
                change_nodes, new_items, new_mails, req, timer, skip=skip, win=win,
                own_soldier_info=own_soldier_info, heroes=heroes)
        return defer


    def _add_legendcity_leader_broadcast(self, user, city_id, position_level):
        """广播玩家获得史实城太守
        Args:

        """
        (mode, priority, life_time, content) = legendcity_business.create_broadcast_content(user, city_id, position_level)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add legendcity leader broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_legendcity_leader_broadcast_result)
        return defer


    def _check_add_legendcity_leader_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add legendcity leader broadcast result failed")

        return True



    def _notice_legendcity_battle_result(self, city_id, rival_user_id, record):
        """通知敌对玩家史实城战斗结果
        Args:
            city_id[int]
            record[LegendCityRecordInfo]
        """
        req = internal_pb2.LegendCityBattleResultNoticeReq()
        req.city_id = city_id
        pack.pack_legendcity_record(record, req.record)
        request = req.SerializeToString()

        logger.debug("Notice battle result[req=%s]" % req)
        defer = GlobalObject().root.callChild(
                'portal', "forward_legendcity_battle_notice", rival_user_id, request)
        defer.addCallback(self._check_notice_battle_result)
        return defer


    def _pack_finish_battle_of_legendcity_response(self, data, ret,
            node_list, new_items, new_mails, req, timer,
            skip = False, win = False, own_soldier_info=[], heroes=[]):
        """打包结束战斗响应
        """
        resource = data.resource.get(True)
        conscript_list = data.conscript_list.get_all(True)

        res = battle_pb2.FinishBattleRes()
        res.status = 0

        pack.pack_resource_info(resource, res.resource)
        for conscript in conscript_list:
            pack.pack_conscript_info(conscript, res.conscripts.add(), timer.now)
        for node in node_list:
            pack.pack_node_info(data, node, res.nodes.add(), timer.now)

        for item in new_items:
            item_message = res.items.add()
            item_message.basic_id = item[1]
            item_message.num = item[0]
        for mail in new_mails:
            pack.pack_mail_info(mail, res.mails.add(), timer.now)

        res.ret = ret

        if skip:
            pack.pack_monarch_info(data.user.get(True), res.monarch)
            if win:
                res.battle.result = battle_pb2.BattleOutputInfo.WIN
            else:
                res.battle.result = battle_pb2.BattleOutputInfo.LOSE
            
            for i, hero in enumerate(heroes):
                attack_hero = res.battle.attack_heroes.add()
                pack.pack_hero_info(hero, attack_hero.hero)
                attack_hero.soldier_survival = own_soldier_info[i][2]

        map_business.check_map_data(data)
        return self._finish_battle_succeed(data, req, res, timer)



    def _update_anneal_record(self, user, anneal, now):
        """更新试炼记录
        Args:
        """
        if (not anneal.is_need_to_update_first_record() 
                and not anneal.is_need_to_update_fast_record(user.level)):
            return True

        req = anneal_pb2.UpdateAnnealRecordReq()

        req.floor = anneal.current_floor
        if anneal.is_need_to_update_first_record():
            record = req.records.add()
            record.type = anneal_pb2.AnnealRecordInfo.FIRST_FINISH
            record.name = user.name
            record.level = user.level
            record.icon_id = user.icon_id
            record.finish_passed_time = 0
            record.cost_time = 0
        if anneal.is_need_to_update_fast_record(user.level):
            record = req.records.add()
            record.type = anneal_pb2.AnnealRecordInfo.FAST_FINISH
            record.name = user.name
            record.level = user.level
            record.icon_id = user.icon_id
            record.finish_passed_time = 0
            record.cost_time = now - anneal.current_start_time
        
        request = req.SerializeToString()

        logger.debug("Update anneal record[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("update_anneal_record", 1, request)
        defer.addCallback(self._check_update_anneal_record_result)
        return defer


    def _check_update_anneal_record_result(self, response):
        res = anneal_pb2.UpdateAnnealRecordRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Check update anneal record result failed")

        return True


    def _start_battle_of_worldboss(self, data, worldboss, node, rival, heroes, req, timer):
        """世界boss战斗开始
        1 与common同步信息
        2 查询世界boss是否可被攻击、击杀
        """
        defer = self._query_common_worldboss_start_battle(worldboss)
        defer.addCallback(self._calc_start_battle_of_worldboss,
                data, worldboss, node, rival, heroes, req, timer)
        return defer


    def _query_common_worldboss_start_battle(self, worldboss):
        """查询世界boss的公共数据
        """
        if not worldboss.is_arised():
            return True

        req = boss_pb2.QueryCommonWorldBossReq()
        request = req.SerializeToString()

        logger.debug("sync worldboss start battle[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("query_common_worldboss", 1, request)
        defer.addCallback(self._check_worldboss_result, worldboss)
        return defer


    def _calc_start_battle_of_worldboss(self, result, data, worldboss, node, rival, heroes, req, timer):
        """
        """
        if not worldboss.is_able_to_attack(timer.now):
            logger.debug("Not able to start worldboss battle")
            boss_ret = WorldBossInfo.BOSS_KILLED 
            defer = DataBase().commit(data)
            defer.addCallback(self._start_worldboss_battle_boss_killed_succeed, req, timer, boss_ret)
            return defer


        boss_ret = worldboss_business.start_battle(data, worldboss,
                    req.world_boss_choose_index, timer.now)
        if boss_ret == -1:
            raise Exception("worldboss start battle failed")

        logger.debug("start_battle_of_worldboss[boss_ret=%d]" % boss_ret)
        if not battle_business.start_battle(
                data, node, rival, None, [], heroes, timer.now, True):
            raise Exception("Start battle failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._start_battle_succeed, node, rival, req, timer, boss_ret)
        return defer


    def _start_worldboss_battle_boss_killed_succeed(self, data, req, timer, boss_ret):
        res = battle_pb2.StartBattleRes()
        res.status = 0

        if boss_ret != -1:
            res.world_boss_ret = boss_ret

        response = res.SerializeToString()
        logger.notice("Start battle failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _finish_battle_of_worldboss(
            self, data, own_soldier_info, enemy_soldier_info, req, timer):
        """世界boss战斗结束
        1 与common同步信息
        2 结算结果，并返回boss状态
        """
        user = data.user.get(True)
        worldboss = data.worldboss.get()
        node_basic_id = worldboss.get_node_basic_id()
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        battle = data.battle_list.get(node_id)
        logger.debug("battle rival[rival id=%d]" % battle.rival_id)
        rival = data.rival_list.get(battle.rival_id, True)
        if rival is None or not rival.is_worldboss_rival():
            raise Exception("Finish worldboss battle failed")

        #计算杀敌数
        kill_soldier_num = battle_business._calc_number_of_death(enemy_soldier_info)

        defer = self._query_common_worldboss_finish_battle(worldboss, user, kill_soldier_num)
        defer.addCallback(self._calc_finish_battle_of_worldboss, data, worldboss, rival,
                own_soldier_info, enemy_soldier_info, kill_soldier_num, req, timer)
        return defer


    def _query_common_worldboss_finish_battle(self, worldboss, user, kill_soldier_num):
        """查询世界boss的公共数据
        """
        if not worldboss.is_arised():
            return True

        req = boss_pb2.QueryCommonWorldBossReq()
        req.kills_addition = kill_soldier_num
        req.user_id = user.id
        req.user_name = user.name
        request = req.SerializeToString()

        logger.debug("sync worldboss finish battle[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("query_common_worldboss", 1, request)
        defer.addCallback(self._check_worldboss_result, worldboss)
        return defer


    def _calc_finish_battle_of_worldboss(self, result, data, worldboss, rival,
            own_soldier_info, enemy_soldier_info, kill_soldier_num, req, timer):
        """
        """
        if not worldboss.is_able_to_finish_attack(timer.now):
            raise Exception("Not able to finish worldboss battle")

        node_basic_id = worldboss.get_node_basic_id()
        node_id = NodeInfo.generate_id(data.id, node_basic_id)
        node = data.node_list.get(node_id)
        change_nodes = []
        new_items = []
        new_mails = []
        new_arena_records = []
        if req.battle.result == req.battle.WIN:
            win = True
            if not battle_business.win_battle(
                    data, node, enemy_soldier_info, own_soldier_info,
                    change_nodes, timer.now, new_arena_records):
                raise Exception("Win battle failed")
        else:
            win = False
            if not battle_business.lose_battle(
                    data, node, timer.now, enemy_soldier_info, own_soldier_info,
                    change_nodes, new_items, new_mails, new_arena_records):
                raise Exception("Lost battle failed")

        #检查请求
        if req.battle.result == req.battle.WIN:
            compare.check_user(data, req.monarch, with_level = True)
            #for info in req.battle.attack_heroes:
            #    compare.check_hero(data, info.hero, with_level = True)
            for item_info in req.items:
                compare.check_item(data, item_info)

        boss_ret = worldboss_business.finish_battle(data, worldboss,
                    result, kill_soldier_num, timer.now)
        if boss_ret == WorldBossInfo.BOSS_OVERTIME:
            res = battle_pb2.FinishBattleRes()
            res.status = 0
            res.battle_ret = boss_ret
            return self._finish_battle_succeed(data, req, res, timer)

        defer = DataBase().commit(data)
        defer.addCallback(self._pack_finish_battle_response,
                data, rival, change_nodes, new_items, new_mails,
                new_arena_records, req, timer, boss_ret)
        return defer


    def _check_worldboss_result(self, response, worldboss):
        res = boss_pb2.QueryCommonWorldBossRes()
        res.ParseFromString(response)
        worldboss.current_soldier_num = res.current_soldier_num
        worldboss.kill_user_name = res.kill_user_name
        worldboss.kill_user_id = res.kill_user_id

        if res.status != 0:
            raise Exception("Check query common worldboss result failed")

        return True


