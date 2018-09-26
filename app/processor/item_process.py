#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 处理物品相关的请求
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import hero_pb2
from proto import item_pb2
from proto import internal_pb2
from proto import monarch_pb2
from proto import blacksmith_pb2
from proto import broadcast_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.hero import HeroInfo
from app.data.item import ItemInfo
from app.data.soldier import SoldierInfo
from app.business import item as item_business
from app.business import hero as hero_business
import pdb


class ItemProcessor(object):

    def use_herolist(self, user_id, request):
        """打开国士名册，可以获得物品和英雄"""
        timer = Timer(user_id)

        req = hero_pb2.OpenHeroListReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_herolist_reward, req, timer)
        defer.addErrback(self._use_herolist_failed, req, timer)
        return defer


    def _calc_herolist_reward(self, data, req, timer):
        """打开国士名册
           1 核实 item 的信息
           2 打开国士名册，获取英雄和物品
           3 根据获得的物品，更新数据库
           4 构造返回
        Args:
            data[DataUser]: 包含 item 信息
            req[protobuf]: 客户端请求
            timer[Timer]: 计时器
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
        item = data.item_list.get(item_id)
        if item is None:
            raise Exception("Item not exist")

        consume_num = item.num - req.item.num
        #打开国士名册
        hero_list = [] # [(hero_basic_id, num)]
        item_list = [] # [(item_basic_id, num)]
        if not item.use_herolist_item(hero_list, item_list, consume_num):
            raise Exception("Use herolist item failed")

        compare.check_item(data, req.item)

        for (hero_basic_id, hero_num) in hero_list:
            if not hero_business.gain_hero(data, hero_basic_id, hero_num):
                raise Exception("Gain hero failed")
        if not item_business.gain_item(data, item_list, "herolist reward", log_formater.HEROLIST_REWARD):
            raise Exception("Gain item failed")

        #获得S级武将要播广播
        for (hero_basic_id, hero_num) in hero_list:
            if hero_business.is_need_broadcast(hero_basic_id):
                try:
                    self._add_get_hero_broadcast(data.user.get(), hero_basic_id)
                except:
                    logger.warning("Send get hero broadcast failed")

        #构造返回
        #返回客户端的是从国士名册中获得的英雄和物品（并未将已经拥有的英雄分解成将魂石）
        #客户端会自行进行分解
        res = self._pack_use_herolist_response(data, hero_list, item_list, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._use_herolist_succeed, req, res, timer)
        return defer


    def _add_get_hero_broadcast(self, user, hero_basic_id):
        """广播玩家获得S级英雄数据
        Args:

        """
        (mode, priority, life_time, content) = hero_business.create_broadcast_content(user, hero_basic_id, type = 2)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = user.id
        req.mode_id = mode
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add get hero herolist broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_get_hero_broadcast_result)
        return defer


    def _check_add_get_hero_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add arena broadcast result failed")

        return True



    def _pack_use_herolist_response(self, data, hero_list, item_list, now):
        """构造返回
        Args:
            hero_list[list(hero_basic_id, num)]: 英雄信息
            item_list[list(item_basic_id, num)]: 物品信息
        Returns:
            res[protobuf]: 向客户端的返回的响应
        """
        win_hero = []
        for (basic_id, num) in hero_list:
            soldier_basic_id = HeroInfo.get_default_soldier_basic_id(basic_id)
            soldier_id = SoldierInfo.generate_id(data.id, soldier_basic_id)
            soldier = data.soldier_list.get(soldier_id, True)

            hero = HeroInfo.create(data.id, basic_id, soldier, technology_basic_ids = [])
            for i in range(0, num):
                win_hero.append(hero)

        win_item = []
        for (basic_id, num) in item_list:
            item = ItemInfo.create(data.id, basic_id, num)
            win_item.append(item)

        res = hero_pb2.OpenHeroListRes()
        res.status = 0
        for info in win_hero:
            pack.pack_hero_info(info, res.heroes.add(), now)
        for info in win_item:
            pack.pack_item_info(info, res.items.add())

        return res


    def _use_herolist_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        log = log_formater.output(data, "Use herolist item succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _use_herolist_failed(self, err, req, timer):
        logger.fatal("Use herolist item failed[reason=%s]" % err)

        res = hero_pb2.OpenHeroListRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Use herolist item[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def use_monarch_exp(self, user_id, request):
        """使用主公经验丹，升级用户等级
        """
        timer = Timer(user_id)

        req = item_pb2.UpgradeMonarchReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_use_monarch_exp, req, timer)
        defer.addCallback(self._use_monarch_exp_succeed, req, timer)
        defer.addErrback(self._use_monarch_exp_failed, req, timer)
        return defer


    def _calc_use_monarch_exp(self, data, req, timer):
        item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
        item = data.item_list.get(item_id)

        use_num = item.num - req.item.num
        if not item_business.use_monarch_exp(data, item, use_num, timer.now):
            raise Exception("Use monarch exp failed")

        compare.check_user(data, req.monarch, with_level = True)
        compare.check_item(data, req.item)
        return DataBase().commit(data)


    def _use_monarch_exp_succeed(self, data, req, timer):
        res = item_pb2.UpgradeMonarchRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Use monarch exp succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        log = log_formater.output(data, "Use monarch exp succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _use_monarch_exp_failed(self, err, req, timer):
        logger.fatal("Use monarch exp failed[reason=%s]" % err)

        res = item_pb2.UpgradeMonarchRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Use monarch exp failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def use_item(self, user_id, request):
        """使用物品：资源包
        粮包、钱包、元宝袋 - 换取对应的资源
        """
        timer = Timer(user_id)

        req = item_pb2.UseItemReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_use_item, req, timer)
        defer.addCallback(self._use_item_succeed, req, timer)
        defer.addErrback(self._use_item_failed, req, timer)
        return defer


    def _calc_use_item(self, data, req, timer):
        item_id = ItemInfo.generate_id(data.id, req.item[0].basic_id)
        item = data.item_list.get(item_id)

        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        use_num = item.num - req.item[0].num
        if not item_business.use_item(data, item, use_num, resource, timer.now):
            raise Exception("Use item failed")

        item_id = ItemInfo.generate_id(data.id, req.item[0].basic_id)
        item = data.item_list.get(item_id)
        if item.is_vip_point_item():
            compare.check_user(data, req.monarch, with_vip = True)

        for i in range(0, len(req.item)):
            compare.check_item(data, req.item[i])
        return DataBase().commit(data)


    def _use_item_succeed(self, data, req, timer):
        res = item_pb2.UseItemRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)

        item_id = ItemInfo.generate_id(data.id, req.item[0].basic_id)
        item = data.item_list.get(item_id)
        if item.is_energy_item():
            pack.pack_energy_info(data.energy.get(True), res.energy_info, timer.now)

        response = res.SerializeToString()
        log = log_formater.output(data, "Use item succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _use_item_failed(self, err, req, timer):
        logger.fatal("Use item failed[reason=%s]" % err)

        res = item_pb2.UseItemRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Use item failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def use_resource_package(self, user_id, request):
        """使用物品：资源包
        粮包、钱包、元宝袋 - 换取对应的资源
        """
        timer = Timer(user_id)

        req = item_pb2.UseItemForResourceReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_use_resource_package, req, timer)
        defer.addCallback(self._use_resource_package_succeed, req, timer)
        defer.addErrback(self._use_resource_package_failed, req, timer)
        return defer


    def _calc_use_resource_package(self, data, req, timer):
        for item_info in req.item:
            item = item_business.get_item_by_id(data, item_info.basic_id)

            resource = data.resource.get()
            resource.update_current_resource(timer.now)

            use_num = item.num - item_info.num
            if use_num > item.num:
                logger.warning("Use resource item error[item.id=%d][own_num=%d][use_num=%d]"
                        % (item.basic_id, item.num, use_num))
                return DataBase().commit(data)
            elif use_num < 0:
                logger.warning("item num error[item.id=%d][own_num=%d][use_num=%d]" 
                        % (item.basic_id, item.num, use_num))
                return DataBase().commit(data)

            if not item_business.use_resource_item(data, resource, item, use_num):
                raise Exception("Use resource item failed")
        return DataBase().commit(data)


    def _use_resource_package_succeed(self, data, req, timer):
        res = item_pb2.UseItemForResourceRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)

        for item_info in req.item:
            item = item_business.get_item_by_id(data, item_info.basic_id, True)
            if item.is_energy_item():
                pack.pack_energy_info(data.energy.get(True), res.energy_info, timer.now)

        response = res.SerializeToString()
        log = log_formater.output(data, "Use resource package succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _use_resource_package_failed(self, err, req, timer):
        logger.fatal("Use resource package failed[reason=%s]" % err)

        res = item_pb2.UseItemForResourceRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Use resource package failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def sell_item(self, user_id, request):
        """出售物品，获得金钱
        """
        timer = Timer(user_id)

        req = item_pb2.UseItemForResourceReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_sell_item, req, timer)
        defer.addCallback(self._sell_item_succeed, req, timer)
        defer.addErrback(self._sell_item_failed, req, timer)
        return defer


    def _calc_sell_item(self, data, req, timer):
        resource = data.resource.get()
        resource.update_current_resource(timer.now)

        for item_info in req.item:
            item = item_business.get_item_by_id(data, item_info.basic_id)

            use_num = item.num - item_info.num
            if not item_business.sell(resource, item, use_num):
                raise Exception("Sell item failed")
        return DataBase().commit(data)


    def _sell_item_succeed(self, data, req, timer):
        res = item_pb2.UseItemForResourceRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Sell item succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _sell_item_failed(self, err, req, timer):
        logger.fatal("Sell item failed[reason=%s]" % err)

        res = item_pb2.UseItemForResourceRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Sell item failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def create_hero_from_starsoul(self, user_id, request):
        """用将魂石合成英雄
        """
        timer = Timer(user_id)

        req = hero_pb2.GenerateHeroReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_use_starsoul_item, req)
        defer.addCallback(self._create_hero_from_starsoul_succeed, req, timer)
        defer.addErrback(self._create_hero_from_starsoul_failed, req, timer)
        return defer


    def _calc_use_starsoul_item(self, data, req):
        item_id = ItemInfo.generate_id(data.id, req.item.basic_id)
        item = data.item_list.get(item_id)
        if item is None:
            raise Exception("Item not exist[basic id= %d]" % req.item.basic_id)

        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)
        if hero is not None:
            raise Exception("Hero exist[basic id= %d]" % req.hero.basic_id)

        soldier_basic_id = HeroInfo.get_default_soldier_basic_id(req.hero.basic_id)
        soldier_id = SoldierInfo.generate_id(data.id, soldier_basic_id)
        soldier = data.soldier_list.get(soldier_id, True)

        use_num = item.num - req.item.num
        hero = item_business.use_starsoul_item(data, item, use_num, soldier)
        if hero is None:
            raise Exception("Use starsoul item error")

        if hero.basic_id != req.hero.basic_id:
            raise Exception("Unexpected hero[hero basic id=%d][exp basic id=%d]" %
                    (req.hero.basic_id, hero.basic_id))

        data.hero_list.add(hero)
        return DataBase().commit(data)


    def _create_hero_from_starsoul_succeed(self, data, req, timer):
        res = hero_pb2.GenerateHeroRes()
        res.status = 0
        hero = hero_business.get_hero_by_id(data, req.hero.basic_id, True)
        pack.pack_hero_info(hero, res.hero, timer.now)

        response = res.SerializeToString()
        log = log_formater.output(data, "Create hero from starsoul succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _create_hero_from_starsoul_failed(self, err, req, timer):
        logger.fatal("Create fero from starsoul failed[reason=%s]" % err)

        res = hero_pb2.GenerateHeroRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Create fero from starsoul failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def compose_item(self, user_id, request):
        """物品合成
        """
        timer = Timer(user_id)

        req = item_pb2.ComposeItemsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_compose, req, timer)
        defer.addCallback(self._compose_succeed, req, timer)
        defer.addErrback(self._compose_failed, req, timer)
        return defer


    def _calc_compose(self, data, req, timer):
        """合成物品
        """
        src_info = []
        for item_info in req.item_source:
            src_info.append(item_info.basic_id)

        item = item_business.get_item_by_id(data, req.item.basic_id)
        if item is None:
            dest_num = req.item.num
        else:
            dest_num = req.item.num - item.num
        if dest_num <= 0:
            logger.warning("Dest item full[item.basic_id=%d][item.num=%d]" % (item.basic_id, item.num))
            return DataBase().commit(data)
        
        #使用原材料物品合成目标物品
        dest_item = item_business.compose(data, src_info, req.item.basic_id, timer.now, dest_num)
        if dest_item == False:
            raise Exception("Compose item failed")

        #验证客户端正确性
        #compare.check_item(data, req.item)
        #for item_info in req.item_source:
        #    compare.check_item(data, item_info)

        #如果是宝珠合成需要广播
        if dest_item != False and dest_item.is_equipment_stone_item():
            try:
                self._add_compose_broadcast(data, dest_item)
            except:
                logger.warning("Send compose item broadcast failed")

        return DataBase().commit(data)


    def _add_compose_broadcast(self, data, item):
        (mode_id, priority, life_time, content) = item_business.create_broadcast_of_compose(
                data, item)
        req = broadcast_pb2.AddBroadcastInfoReq()
        req.user_id = data.id
        req.mode_id = mode_id
        req.priority = priority
        req.life_time = life_time
        req.content = content
        request = req.SerializeToString()

        logger.debug("Add compose broadcast[req=%s]" % req)
        defer = GlobalObject().remote["common"].callRemote("add_broadcast_record", 1, request)
        defer.addCallback(self._check_add_compose_broadcast_result)
        return defer


    def _check_add_compose_broadcast_result(self, response):
        res = broadcast_pb2.AddBroadcastInfoRes()
        res.ParseFromString(response)

        if res.status != 0:
            raise Exception("Add compose broadcast result failed")

        return True


    def _compose_succeed(self, data, req, timer):
        """
        """
        res = item_pb2.ComposeItemsRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Compose Item succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _compose_failed(self, err, req, timer):
        """
        """
        logger.fatal("Compose Item Failed[reason=%s]" % err)

        res = item_pb2.ComposeItemsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Compose Item Failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_item(self, user_id, request):
        """无条件添加物品
        """
        timer = Timer(user_id)

        req = internal_pb2.AddItemReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_item, req)
        defer.addCallback(self._add_item_succeed, req, timer)
        defer.addErrback(self._add_item_failed, req, timer)
        return defer


    def _calc_add_item(self, data, req):
        win_item = []
        for info in req.items:
            win_item.append((info.basic_id, info.num))

        if not item_business.gain_item(data, win_item, "wim item", log_formater.WIN_REWARD):
            raise Exception("Merge reward failed")

        return DataBase().commit(data)


    def _add_item_succeed(self, data, req, timer):
        res = internal_pb2.AddItemRes()
        res.status = 0
        response = res.SerializeToString()
        log = log_formater.output(data, "Add item succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_item_failed(self, err, req, timer):
        logger.fatal("Add Item Failed[reason=%s]" % err)

        res = internal_pb2.AddItemRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add Item Failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def casting_item(self, user_id, request):
        """熔铸物品
        """
        timer = Timer(user_id)

        req = blacksmith_pb2.CastingReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_casting_item, req, timer)
        defer.addErrback(self._casting_item_failed, req, timer)
        return defer


    def _calc_casting_item(self, data, req, timer):
        """
        """
        src_info = []
        for item_info in req.origin_items:
            origin_item_id = ItemInfo.generate_id(data.id, item_info.basic_id)
            origin_item = data.item_list.get(origin_item_id)
            if origin_item is None:
                raise Exception("Casting source item not exist[basic_id=%d" % item_info.basic_id)

            src_info.append((item_info.basic_id, origin_item.num - item_info.num))

        building_level = 0
        for building in data.building_list.get_all(True):
            if building.is_blacksmith():
                building_level = building.level
                break

        if req.HasField("target_item_num"):
            target_item_num = req.target_item_num
        else:
            target_item_num = 1

        #使用原进阶材料物品合成目标进阶材料
        (result, dest_item) = item_business.casting(
                data, src_info, req.target_item_id, target_item_num, building_level)
        if result == False:
	    target_item_num = 0	
            raise Exception("Casting item failed")
	
        item_id = ItemInfo.generate_id(data.id, req.target_item_id)
        item = data.item_list.get(item_id)
        #验证客户端正确性
        for item_info in req.origin_items:
            compare.check_item(data, item_info)

        #记录升级次数
        trainer = data.trainer.get()
        trainer.add_daily_cast_item_num(1)

        defer = DataBase().commit(data)
        defer.addCallback(self._casting_item_succeed, req, timer, dest_item)
        return defer


    def _casting_item_succeed(self, data, req, timer, dest_item):
        """
        """
        res = blacksmith_pb2.CastingRes()
        res.status = 0

        if dest_item != None:
            item = ItemInfo.create(data.id, req.target_item_id, req.target_item_num)
            pack.pack_item_info(item, res.target_item)

        response = res.SerializeToString()
        log = log_formater.output(data, "Casting item succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _casting_item_failed(self, err, req, timer):
        """
        """
        logger.fatal("Casting item Failed[reason=%s]" % err)

        res = blacksmith_pb2.CastingRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Casting item Failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def resolve_starsoul(self, user_id, request):
        """分解将魂石"""
        return self.use_resource_package(user_id, request)



