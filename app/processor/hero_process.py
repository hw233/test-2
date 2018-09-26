#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : Hero 相关逻辑
"""

import time
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import hero_pb2
from proto import item_pb2
from proto import broadcast_pb2
from proto import internal_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app import compare
from app import log_formater
from app.core import technology as technology_module
from app.data.hero import HeroInfo
from app.data.item import ItemInfo
from app.data.soldier import SoldierInfo
from app.business import hero as hero_business
from app.business import building as building_business
from app.business import account as account_business
from app.business import item as item_business


class HeroProcessor(object):
    """处理英雄系统相关逻辑
    包括：升级、升星、升级技能、升级兵种
    """

    def upgrade_level(self, user_id, request):
        """消耗经验丹，升级英雄等级"""
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade_level, req, timer)
        defer.addCallback(self._upgrade_level_succeed, req, timer)
        defer.addErrback(self._upgrade_level_failed, req, timer)
        return defer


    def _calc_upgrade_level(self, data, req, timer):
        """重现客户端英雄升级计算逻辑，和请求进行比较
        Args:
            data[UserData]: 升级前的数据，从数据库中获得
            req[UpdateHeroReq]: 升级后的数据，客户端发送的请求
        Returns:
            data[UserData]: 升级后的数据
        """
        items = []
        for item in req.item:
            item_id = ItemInfo.generate_id(data.id, item.basic_id)
            item = data.item_list.get(item_id)
            items.append(item)

        #新逻辑，传过来经验丹的消耗数量，以防客户端和服务器物品数量不一致
        use_items = []
        for item in req.use_item:
            item_id = ItemInfo.generate_id(data.id, item.basic_id)
            item = data.item_list.get(item_id)
            use_items.append(item)

        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)

        if (len(items) == 0 and len(use_items) == 0) or hero is None:
            raise Exception("Items or hero not exist")
        if len(use_items) != 0:
            #走新逻辑
            for i in range(len(use_items)):
                consume_num = req.use_item[i].num
                if not  hero_business.level_upgrade_by_item(
                        data, hero, use_items[i], consume_num, timer.now):
                    raise Exception("Hero level upgrade failed")
        else:
            for i in range(len(items)):
                consume_num = items[i].num - req.item[i].num
                if not  hero_business.level_upgrade_by_item(
                        data, hero, use_items[i], consume_num, timer.now):
                    raise Exception("Hero level upgrade failed")
        #验证
        compare.check_hero(data, req.hero, with_level = True, with_soldier = True)
        #for item in req.item:
        #    compare.check_item(data, item)

        return DataBase().commit(data)


    def _upgrade_level_succeed(self, data, req, timer):
        """请求处理成功"""
        res = hero_pb2.UpdateHeroRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Upgrade hero level succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _upgrade_level_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Upgrade hero level failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Upgrade hero level failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def upgrade_star(self, user_id, request):
        """消耗将魂石，升级英雄星级"""
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade_star, req, timer)
        defer.addErrback(self._upgrade_star_failed, req, timer)
        return defer


    def _calc_upgrade_star(self, data, req, timer):
        """重现客户端升星计算逻辑，和请求进行比较
        """
        res = hero_pb2.UpdateHeroRes()
        res.status = 0

        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)
        item_id = ItemInfo.generate_id(data.id, req.item[0].basic_id)
        item = data.item_list.get(item_id)

        if hero is None or item is None:
            raise Exception("Hero or item not exist")

        #消耗精魄
        soul_num = 0
        open_flags = account_business.get_flags()
        if "HeroUpStarUseSoul" in open_flags:
            soul_num = data_loader.HeroStarLevelBasicInfo_dict[req.hero.star_level].soul

        #使用灵魂石
        consume_num = data_loader.HeroStarLevelBasicInfo_dict[req.hero.star_level].perceptivity
        ret = hero_business.star_upgrade(data, hero, item, consume_num, soul_num, timer.now)
        if ret != hero_pb2.HERO_OK:
            res.ret = ret
            return self._upgrade_star_succeed(data, req, res, timer)

        #和请求进行比较
        if req.hero.star_level != hero.star:
            raise Exception("Unexpect hero star[expect star=%d]" % hero.star)

        #验证
        compare.check_hero(data, req.hero, with_star = True)
        compare.check_item(data, req.item[0])

        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        res.ret = hero_pb2.HERO_OK
        pack.pack_resource_info(resource, res.resource)

        try:
            if hero.is_need_broadcast_star_level():
                self._add_upgrade_star_level_broadcast(data.user.get(), hero)
        except:
            logger.warning("Send upgrade star level broadcast failed")

        defer = DataBase().commit(data)
        defer.addCallback(self._upgrade_star_succeed, req, res, timer)
        return defer


    def _add_upgrade_star_level_broadcast(self, user, hero):
        """广播玩家英雄升星数据
        Args:

        """
        (mode, priority, life_time, content) = hero.create_broadcast_content_star_level(user)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add upgrade star level broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_upgrade_star_level_broadcast_result)
        return defer


    def _check_add_upgrade_star_level_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add upgrade star level broadcast result failed")

        return True


    def _upgrade_star_succeed(self, data, req, res, timer):
        response = res.SerializeToString()

        if res.ret == hero_pb2.HERO_OK:
            log = log_formater.output(data, "Upgrade hero star succeed", req, res, timer.count_ms())
            logger.notice(log)
        else:
            logger.notice("Upgrade hero star failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                    (timer.id, req, res, timer.count_ms()))

        return response


    def _upgrade_star_failed(self, err, req, timer):
        logger.fatal("Upgrade hero star failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Upgrade Hero star failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def upgrade_skill(self, user_id, request):
        """消耗钱和技能点，升级英雄技能等级"""
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroSkillReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade_skill, req, timer)
        defer.addCallback(self._upgrade_skill_succeed, req, timer)
        defer.addErrback(self._upgrade_skill_failed, req, timer)
        return defer


    def _calc_upgrade_skill(self, data, req, timer):
        """升级技能逻辑计算"""
        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)

        if hero is None:
            raise Exception("Hero not exist")

        if not hero_business.skill_upgrade(data, hero, req.index - 1, timer.now):
            #raise Exception("Skill upgrade failed")
            pass

        #验证
        #compare.check_hero(data, req.hero, with_skill_index = req.index - 1)
        #for item in req.items:
        #    compare.check_item(data, item)

        return DataBase().commit(data)


    def _upgrade_skill_succeed(self, data, req, timer):
        res = hero_pb2.UpdateHeroSkillRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Upgrade hero skill succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _upgrade_skill_failed(self, err, req, timer):
        logger.fatal("Upgrade hero skill failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroSkillRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Upgrade hero skill failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_soldier(self, user_id, request):
        """更新英雄兵种"""
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_soldier, req, timer)
        defer.addCallback(self._update_soldier_succeed, req, timer)
        defer.addErrback(self._update_soldier_failed, req, timer)
        return defer


    def _calc_update_soldier(self, data, req, timer):
        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)
        soldier_id = SoldierInfo.generate_id(data.id, req.hero.soldier_basic_id)
        soldier = data.soldier_list.get(soldier_id, True)

        if not hero_business.soldier_update(data, hero, soldier, timer.now):
            raise Exception("Soldier update failed")

        #验证
        compare.check_hero(data, req.hero, with_soldier = True)

        return DataBase().commit(data)


    def _update_soldier_succeed(self, data, req, timer):
        res = hero_pb2.UpdateHeroRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Upgrade hero soldier succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_soldier_failed(self, err, req, timer):
        logger.fatal("Update hero soldier failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update hero soldier failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update_garrison_hero_exp(self, user_id, request):
        """更新英雄驻守经验
        这个请求是由客户端定时发起的，如果客户端不发起，则不会主动结算英雄驻守经验
        """
        timer = Timer(user_id)

        req = hero_pb2.HeroUpdateGarrisonExpReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_update_garrison_hero_exp, req, timer)
        defer.addErrback(self._update_garrison_hero_exp_failed, req, timer)
        return defer


    def _calc_update_garrison_hero_exp(self, data, req, timer):
        """
        """
        heroes = []
        for hero in req.heroes:
            hero_id = HeroInfo.generate_id(data.id, hero.basic_id)
            hero = data.hero_list.get(hero_id)
            heroes.append(hero)

        for hero in heroes:
            building = data.building_list.get(hero.place_id, True)

            if not building_business.calc_garrison_exp(
                    data, building, [hero], timer.now):
                raise Exception('Calc garrison exp failed')

        res = self._pack_update_garrison_hero_exp_response(heroes, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._update_garrison_hero_exp_succeed, req, res, timer)
        return defer


    def _pack_update_garrison_hero_exp_response(self, heroes, now):
        res = hero_pb2.HeroUpdateGarrisonExpRes()
        res.status = 0
        for hero in heroes:
            pack.pack_hero_info(hero, res.heroes.add(), now)

        return res


    def _update_garrison_hero_exp_succeed(self, data, req, res, timer):
        """
        """
        response = res.SerializeToString()
        log = log_formater.output(data, "Update garrison hero exp succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _update_garrison_hero_exp_failed(self, err, req, timer):
        """
        """
        logger.fatal("Update garrison hero exp failed[reason=%s]" % err)
        res = hero_pb2.HeroUpdateGarrisonExpRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update garrison hero exp failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def upgrade_evolution_level(self, user_id, request):
        """消耗突破石，升级进化等级"""
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade_evolution_level, req, timer)
        defer.addCallback(self._upgrade_evolution_level_succeed, req, timer)
        defer.addErrback(self._upgrade_evolution_level_failed, req, timer)
        return defer


    def _calc_upgrade_evolution_level(self, data, req, timer):
        """重现客户端升星计算逻辑，和请求进行比较
        """
        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)
        item_id = ItemInfo.generate_id(data.id, req.item[0].basic_id)
        item = data.item_list.get(item_id)

        if hero is None or item is None:
            raise Exception("Hero or item not exist")

        #使用突破石
        consume_num = item.num - req.item[0].num
        if not hero_business.evolution_level_upgrade(data, hero, item, consume_num, timer.now):
            raise Exception("Hero evolution level upgrade failed]")

        #和请求进行比较
        if req.hero.evolution_level != hero.evolution_level:
            raise Exception("Unexpect hero evolution level[expect evolution level=%d]"
                    % hero.evolution_level)

        #验证
        compare.check_hero(data, req.hero, with_evolution = True)
        compare.check_item(data, req.item[0])

        if hero.is_need_broadcast():
            #玩家英雄达到一定等级时，广播
            try:
                self._add_upgrade_evolution_level_broadcast(data.user.get(), hero)
            except:
                logger.warning("Send upgrade evolution level broadcast failed")

        return DataBase().commit(data)


    def _add_upgrade_evolution_level_broadcast(self, user, hero):
        """广播玩家进化英雄数据
        Args:

        """
        (mode, priority, life_time, content) = hero.create_broadcast_content(user)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add upgrade evolution level broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_upgrade_evolution_level_broadcast_result)
        return defer


    def _check_add_upgrade_evolution_level_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast result failed")

        return True


    def _upgrade_evolution_level_succeed(self, data, req, timer):
        res = hero_pb2.UpdateHeroRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(
                data, "Upgrade evolution level succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _upgrade_evolution_level_failed(self, err, req, timer):
        logger.fatal("Upgrade evolution level failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Upgrade evolution level failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_hero(self, user_id, request):
        """无条件添加英雄
        """
        timer = Timer(user_id)

        req = internal_pb2.AddHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._check_exist_hero, req, timer)
        defer.addCallback(self._calc_add_hero, req, timer)
        defer.addCallback(self._add_hero_succeed, req, timer)
        defer.addErrback(self._add_hero_failed, req, timer)
        return defer


    def _check_exist_hero(self, data, req, timer):
        hero_basic_id = req.hero.basic_id
        hero_id = HeroInfo.generate_id(data.id, hero_basic_id)

        #内部接口，使用时需要保证英雄没有和其他建筑等关联
        hero = data.hero_list.get(hero_id)
        if hero is not None:
            data.hero_list.delete(hero_id)
            return DataBase().commit(data)
        else:
            return data


    def _calc_add_hero(self, data, req, timer):
        hero_basic_id = req.hero.basic_id

        soldier_basic_id = HeroInfo.get_default_soldier_basic_id(hero_basic_id)
        soldier_id = SoldierInfo.generate_id(data.id, soldier_basic_id)
        soldier = data.soldier_list.get(soldier_id, True)

        skill_ids = []
        skill_ids.append(req.hero.first_skill_id)
        skill_ids.append(req.hero.second_skill_id)
        skill_ids.append(req.hero.third_skill_id)
        skill_ids.append(req.hero.fourth_skill_id)

        user = data.user.get(True)
        #影响英雄所带兵种战力的科技
        battle_technology_basic_id = technology_module.get_battle_technology_for_soldier(
                data.technology_list.get_all(True), soldier_basic_id)

        equipments_id = []
        if (req.hero.HasField("equipment_weapon_id") and 
                req.hero.HasField("equipment_armor_id") and
                req.hero.HasField("equipment_treasure_id")):
            equipments_id.append(req.hero.equipment_weapon_id)
            equipments_id.append(req.hero.equipment_armor_id)
            equipments_id.append(req.hero.equipment_treasure_id)

        stone_weapon = []
        if len(req.hero.stone_weapon) == 4:
            stone_weapon.append(req.hero.stone_weapon[0])
            stone_weapon.append(req.hero.stone_weapon[1])
            stone_weapon.append(req.hero.stone_weapon[2])
            stone_weapon.append(req.hero.stone_weapon[3])
        stone_armor = []
        if len(req.hero.stone_armor) == 4:
            stone_armor.append(req.hero.stone_armor[0])
            stone_armor.append(req.hero.stone_armor[1])
            stone_armor.append(req.hero.stone_armor[2])
            stone_armor.append(req.hero.stone_armor[3])
        stone_treasure = []
        if len(req.hero.stone_treasure) == 4:
            stone_treasure.append(req.hero.stone_treasure[0])
            stone_treasure.append(req.hero.stone_treasure[1])
            stone_treasure.append(req.hero.stone_treasure[2])
            stone_treasure.append(req.hero.stone_treasure[3])

        evolution_level = 1
        if req.hero.HasField("evolution_level"):
            evolution_level = req.hero.evolution_level

        hero = HeroInfo.create_special(user.id, user.level, hero_basic_id,
                req.hero.level, req.hero.star_level,
                soldier, skill_ids, battle_technology_basic_id,
                equipments_id, [], True, evolution_level, 
                stones_weapon_id = stone_weapon,
                stones_armor_id = stone_armor,
                stones_treasure_id = stone_treasure)
        if hero is None:
            raise Exception("Create hero failed")

        data.hero_list.add(hero)
        hero_business.post_gain_hero(data, hero)

        return DataBase().commit(data)


    def _add_hero_succeed(self, data, req, timer):
        res = internal_pb2.AddHeroRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Add hero succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_hero_failed(self, err, req, timer):
        logger.fatal("Add Hero Failed[reason=%s]" % err)

        res = internal_pb2.AddHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add Hero Failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def reborn(self, user_id, request):
        """武将重生"""
        timer = Timer(user_id)

        req = hero_pb2.RebornHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reborn, req, timer)
        defer.addErrback(self._reborn_failed, req, timer)
        return defer

    def _calc_reborn(self, data, req, timer):
        res = hero_pb2.RebornHeroRes()
        res.status = 0

        if req.type == hero_pb2.RebornHeroReq.PERFECT:
            ret = hero_business.is_able_to_perfect_reborn_hero(data, timer.now)
            if ret != True:
                res.return_ret = ret
                return self._reborn_succeed(data, req, res, timer)
            is_perfect = True
        else:
            is_perfect = False

        open_flags = account_business.get_flags()
        if "HeroUpStarUseSoul" in open_flags:
            #分解
            if not hero_business.resolve_hero(data, req.hero.basic_id, is_perfect, timer.now):
                res.return_ret = hero_pb2.RebornHeroRes.REBORN_ERROR
                return self._reborn_succeed(data, req, res, timer)
        else:
            if not hero_business.reborn_hero(data, req.hero.basic_id, is_perfect, timer.now):
                res.return_ret = hero_pb2.RebornHeroRes.REBORN_ERROR
                return self._reborn_succeed(data, req, res, timer)
        
        '''
        if not compare.check_hero_r(data, req.hero, True, True, True, 0, -1, True, True, True):
            res.return_ret = hero_pb2.RebornHeroRes.REBORN_ERROR
            return self._reborn_succeed(data, req, res, timer)
        '''

        #for item in req.items:
        #    if not compare.check_item_r(data, item):
        #        res.return_ret = hero_pb2.RebornHeroRes.REBORN_ERROR
        #        return self._reborn_succeed(data, req, res, timer)
        
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        res.return_ret = hero_pb2.RebornHeroRes.REBORN_SUCCESS
        pack.pack_resource_info(resource, res.resource)
        defer = DataBase().commit(data)
        defer.addCallback(self._reborn_succeed, req, res, timer)
        return defer

    def _reborn_succeed(self, data, req, res, timer):
        if res.return_ret != hero_pb2.RebornHeroRes.REBORN_SUCCESS:
            logger.notice("Reborn hero failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Reborn hero succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response
    
    def _reborn_failed(self, err, req, timer):
        logger.fatal("Reborn hero failed[reason=%s]" % err)

        res = hero_pb2.RebornHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reborn hero failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def awaken(self, user_id, request):
        """武将觉醒"""
        timer = Timer(user_id)

        req = hero_pb2.AwakeningHeroReq()
        req.ParseFromString(request)
        
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_awaken, req, timer)
        defer.addErrback(self._awaken_failed, req, timer)
        return defer

    def _calc_awaken(self, data, req, timer):
        res = hero_pb2.AwakeningHeroRes()
        res.status = 0

        temple = None
        for building in data.building_list.get_all(True):
            if building.is_temple():
                temple = building
                break
        
        if temple is None or temple.level < int(float(data_loader.OtherBasicInfo_dict['unlock_hero_awakening_level'].value)):
            res.return_ret = hero_pb2.AwakeningHeroRes.ERROR_BUILDING
            return self._awaken_succeed(data, req, res, timer)

        hero = hero_business.get_hero_by_id(data, req.hero.basic_id)
        if hero is None:
            res.return_ret = hero_pb2.AwakeningHeroRes.ERROR_HERO
            return self._awaken_succeed(data, req, res, timer)

        ret = hero_business.awaken_hero(data, hero, timer.now)
        if ret != hero_pb2.AwakeningHeroRes.SUCCESS:
            res.return_ret = ret
            return self._awaken_succeed(data, req, res, timer)
        
        try:
            compare.check_hero(data, req.hero, with_awaken=True)
            for item_info in req.items:
                compare.check_item(data, item_info)
        except:
            res.return_ret = hero_pb2.AwakeningHeroRes.INVALID
            return self._awaken_succeed(data, req, res, timer)

        res.return_ret = hero_pb2.AwakeningHeroRes.SUCCESS
        defer = DataBase().commit(data)
        defer.addCallback(self._awaken_succeed, req, res, timer)
        return defer

    def _awaken_succeed(self, data, req, res, timer):
        if res.return_ret != hero_pb2.AwakeningHeroRes.SUCCESS:
            logger.notice("Awaken hero failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Awaken hero succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _awaken_failed(self, err, req, timer):
        logger.fatal("Awaken hero failed[reason=%s]" % err)
        res = hero_pb2.AwakeningHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Awaken hero failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def refine(self, user_id, request):
        """洗髓"""
        timer = Timer(user_id)

        req = hero_pb2.RefineHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refine, req, timer)
        defer.addErrback(self._refine_failed, req, timer)
        return defer

    def _calc_refine(self, data, req, timer):
        res = hero_pb2.RefineHeroRes()
        res.status = 0

        hero = hero_business.get_hero_by_id(data, req.hero.basic_id)
        if hero is None:
            raise Exception("Hero not non-existent[user_id=%d][req_basic_id=%d]" % 
                (data.id, req.hero.basic_id))

        ret = hero_business.hero_refine(data, hero)
        if ret == res.Refine_NEED_ITEM:
            return self._pack_refine_need_item(data, req, hero, timer)

        return self._pack_refine_succeed(data, req, hero, timer)

    def _pack_refine_need_item(self, data, req, hero, timer):
        res = hero_pb2.RefineHeroRes()
        res.status = 0
        res.return_ret = res.Refine_NEED_ITEM

        (item_id, item_num) = hero.refine_item()
        item = item_business.get_item_by_id(data, item_id)
        pack.pack_item_info(item, res.items.add())

        return self._refine_succeed(data, req, res, timer)

    def _pack_refine_succeed(self, data, req, hero, timer):
        res = hero_pb2.RefineHeroRes()
        res.status = 0
        res.return_ret = res.Refine_SUCCESS
        
        pack.pack_hero_info(hero, res.hero, timer.now)
        (item_id, item_num) = hero.refine_item()
        item = item_business.get_item_by_id(data, item_id)
        pack.pack_item_info(item, res.items.add())

        defer = DataBase().commit(data)
        defer.addCallback(self._refine_succeed, req, res, timer)
        return defer


    def _refine_succeed(self, data, req, res, timer):
        if res.return_ret != res.Refine_SUCCESS:
            logger.notice("Refine hero failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Refine hero succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _refine_failed(self, err, req, timer):
        logger.fatal("Refine hero failed[reason=%s]" % err)
        res = hero_pb2.RefineHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refine hero failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refine_upgrade(self, user_id, request):
        """洗髓进阶"""
        timer = Timer(user_id)

        req = hero_pb2.RefineHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refine_upgrade, req, timer)
        defer.addErrback(self._refine_upgrade_failed, req, timer)
        return defer

    def _calc_refine_upgrade(self, data, req, timer):
        res = hero_pb2.RefineHeroRes()
        res.status = 0

        hero = hero_business.get_hero_by_id(data, req.hero.basic_id)
        if hero is None:
            raise Exception("Hero not non-existent[user_id=%d][req_basic_id=%d]" % 
                (data.id, req.hero.basic_id))

        ret = hero_business.hero_refine_upgrade(data, hero, timer.now)
        if ret == res.Refine_CANNT_UPGRADE:
            return self._pack_refine_cannt_upgrade(data, req, hero, timer)

        return self._pack_refine_upgrade_succeed(data, req, hero, timer)

    def _pack_refine_cannt_upgrade(self, data, req, hero, timer):
        res = hero_pb2.RefineHeroRes()
        res.status = 0
        res.return_ret = res.Refine_CANNT_UPGRADE

        pack.pack_hero_info(hero, res.hero, timer.now)
        return self._refine_upgrade_succeed(data, req, res, timer)

    def _pack_refine_upgrade_succeed(self, data, req, hero, timer):
        res = hero_pb2.RefineHeroRes()
        res.status = 0
        res.return_ret = res.Refine_SUCCESS

        pack.pack_hero_info(hero, res.hero, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._refine_upgrade_succeed, req, res, timer)
        return defer

    def _refine_upgrade_succeed(self, data, req, res, timer):
        if res.return_ret != res.Refine_SUCCESS:
            logger.notice("Refine hero upgrade failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Refine hero upgrade succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _refine_upgrade_failed(self, err, req, timer):
        logger.fatal("Refine hero upgrade failed[reason=%s]" % err)
        res = hero_pb2.RefineHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refine hero upgrade failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
