#coding:utf8
"""
Created on 2015-06-10
@Author: taoshucai(taoshucai@ice-time.cn)
@Brief:  装备
"""

from utils import logger
from utils.timer import Timer
from proto import hero_pb2
from datalib.global_data import DataBase
from app import pack
from app import compare
from app import log_formater
from app.data.hero import HeroInfo
from app.data.item import ItemInfo
from app.business import hero as hero_business
from app.business import account as account_business


class EquipmentProcess(object):

    def upgrade_equipment(self, user_id, request):
        """装备进阶
        """
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroEquipmentReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade_equipment, req, timer)
        defer.addCallback(self._upgrade_equipment_succeed, req, timer)
        defer.addErrback(self._upgrade_equipment_failed, req, timer)
        return defer


    def _calc_upgrade_equipment(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        cost_gold = 0
        if req.HasField("gold"):
            cost_gold = req.gold

        if not hero_business.equipment_upgrade(
                data, req.hero.basic_id, req.type, cost_gold, timer.now):
            raise Exception("Upgrade equipment failed")

        #验证
        compare.check_hero(data, req.hero, with_equipment_type = req.type)
        for item_info in req.items:
            compare.check_item(data, item_info)

        return DataBase().commit(data)


    def _upgrade_equipment_succeed(self, data, req, timer):
        res = hero_pb2.UpdateHeroEquipmentRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Upgrade hero equipment succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response

    def _upgrade_equipment_failed(self, err, req, timer):
        logger.fatal("Upgrade hero equipment failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroEquipmentRes()
        res.status = -1
        response = res.SerializeToString()

        logger.notice("Upgrade hero equipment failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def enchant_equipment(self, user_id, request):
        """装备精炼
        """
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroEquipmentReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_enchant_equipment, req, timer)
        defer.addCallback(self._enchant_equipment_succeed, req, timer)
        defer.addErrback(self._enchant_equipment_failed, req, timer)
        return defer


    def _calc_enchant_equipment(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        #精炼后的装备 id
        if req.type == HeroInfo.EQUIPMENT_TYPE_WEAPON:
            dest_equipment_id = req.hero.equipment_weapon_id
        elif req.type == HeroInfo.EQUIPMENT_TYPE_ARMOR:
            dest_equipment_id = req.hero.equipment_armor_id
        elif req.type == HeroInfo.EQUIPMENT_TYPE_TREASURE:
            dest_equipment_id = req.hero.equipment_treasure_id
        else:
            raise Exception("Invalid input equipment type[type=%d]" % req.type)

        #精炼消耗的材料
        cost_item = []
        for item_info in req.items:
            item_id = ItemInfo.generate_id(data.id, item_info.basic_id)
            item = data.item_list.get(item_id)
            cost_num = item.num - item_info.num
            cost_item.append((item.id, cost_num))

        #精炼消耗的元宝
        cost_gold = 0
        if req.HasField("gold"):
            cost_gold = req.gold

        if not hero_business.equipment_enchant(
                data, req.hero.basic_id, req.type, dest_equipment_id,
                cost_item, cost_gold, timer.now):
            raise Exception("Enchant equipment failed")

        #验证
        compare.check_hero(data, req.hero, with_equipment_type = req.type)
        for item_info in req.items:
            compare.check_item(data, item_info)

        return DataBase().commit(data)


    def _enchant_equipment_succeed(self, data, req, timer):
        res = hero_pb2.UpdateHeroEquipmentMaxRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Enchant hero equipment succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _enchant_equipment_failed(self, err, req, timer):
        logger.fatal("Enchant hero equipment failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroEquipmentMaxRes()
        res.status = -1
        response = res.SerializeToString()

        logger.notice("Enchant hero equipment failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def upgrade_equipment_max(self, user_id, request):
        """一键装备进阶
        """
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroEquipmentMaxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade_equipment_max, req, timer)
        defer.addCallback(self._upgrade_equipment_max_succeed, req, timer)
        defer.addErrback(self._upgrade_equipment_max_failed, req, timer)
        return defer


    def _calc_upgrade_equipment_max(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        cost_gold = 0
        if req.HasField("gold"):
            cost_gold = req.gold

        if not hero_business.equipment_upgrade_max(
                data, req.hero.basic_id, req.type, req.targetId, cost_gold, timer.now):
            raise Exception("Upgrade equipment failed")

        #验证
        compare.check_hero(data, req.hero, with_equipment_type = req.type)
        for item_info in req.items:
            compare.check_item(data, item_info)

        return DataBase().commit(data)


    def _upgrade_equipment_max_succeed(self, data, req, timer):
        res = hero_pb2.UpdateHeroEquipmentMaxRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Upgrade hero equipment max succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response

    def _upgrade_equipment_max_failed(self, err, req, timer):
        logger.fatal("Upgrade hero equipment max failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroEquipmentMaxRes()
        res.status = -1
        response = res.SerializeToString()

        logger.notice("Upgrade hero equipment max failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def enchant_equipment_max(self, user_id, request):
        """装备一键精炼
        """
        timer = Timer(user_id)

        req = hero_pb2.UpdateHeroEquipmentMaxReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_enchant_equipment_max, req, timer)
        defer.addCallback(self._enchant_equipment_max_succeed, req, timer)
        defer.addErrback(self._enchant_equipment_max_failed, req, timer)
        return defer


    def _calc_enchant_equipment_max(self, data, req, timer):
        #涉及到跨天的数据统计，所以此处要更新所有跨天数据
        if not account_business.update_across_day_info(data, timer.now):
            raise Exception("Update across day info failed")

        #精炼后的装备 id
        if req.type == HeroInfo.EQUIPMENT_TYPE_WEAPON:
            dest_equipment_id = req.hero.equipment_weapon_id
        elif req.type == HeroInfo.EQUIPMENT_TYPE_ARMOR:
            dest_equipment_id = req.hero.equipment_armor_id
        elif req.type == HeroInfo.EQUIPMENT_TYPE_TREASURE:
            dest_equipment_id = req.hero.equipment_treasure_id
        else:
            raise Exception("Invalid input equipment type[type=%d]" % req.type)

        #精炼消耗的材料
        cost_item = []
        for item_info in req.items:
            item_id = ItemInfo.generate_id(data.id, item_info.basic_id)
            item = data.item_list.get(item_id)
            cost_num = item.num - item_info.num
            cost_item.append((item.id, cost_num))

        #精炼消耗的元宝
        cost_gold = 0
        if req.HasField("gold"):
            cost_gold = req.gold

        if not hero_business.equipment_enchant_max(
                data, req.hero.basic_id, req.type, dest_equipment_id,
                cost_item, cost_gold, timer.now):
            raise Exception("Enchant equipment max failed")

        #验证
        compare.check_hero(data, req.hero, with_equipment_type = req.type)
        for item_info in req.items:
            compare.check_item(data, item_info)

        return DataBase().commit(data)


    def _enchant_equipment_max_succeed(self, data, req, timer):
        res = hero_pb2.UpdateHeroEquipmentMaxRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()

        log = log_formater.output(data, "Enchant hero equipment max succeed",
                req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _enchant_equipment_max_failed(self, err, req, timer):
        logger.fatal("Enchant hero equipment max failed[reason=%s]" % err)

        res = hero_pb2.UpdateHeroEquipmentMaxRes()
        res.status = -1
        response = res.SerializeToString()

        logger.notice("Enchant hero equipment max failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def mount_equipment_stone(self, user_id, request):
        """给装备镶嵌宝石
        """
        timer = Timer(user_id)

        req = hero_pb2.MountStoneReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_mount_equipment_stone, req, timer)
        defer.addCallback(self._mount_equipment_stone_succeed, req, timer)
        defer.addErrback(self._mount_equipment_stone_failed, req, timer)
        return defer


    def _calc_mount_equipment_stone(self, data, req, timer):
        """装备镶嵌宝石逻辑"""
        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)

        if hero is None:
            raise Exception("Hero not exist")

        if len(req.hero.stone_weapon) != 0:
            equipment_type = HeroInfo.EQUIPMENT_TYPE_WEAPON
            equipment_stones_id = req.hero.stone_weapon
        elif len(req.hero.stone_armor) != 0:
            equipment_type = HeroInfo.EQUIPMENT_TYPE_ARMOR
            equipment_stones_id = req.hero.stone_armor
        elif len(req.hero.stone_treasure) != 0:
            equipment_type = HeroInfo.EQUIPMENT_TYPE_TREASURE
            equipment_stones_id = req.hero.stone_treasure
        else:
            raise Exception("Equipment type error")

        if not hero_business.mount_equipment_stone(data, req.hero.basic_id,
                req.item.basic_id, equipment_type, equipment_stones_id, timer.now):
            raise Exception("Mount equipment stone failed")

        #验证
        compare.check_hero(data, req.hero, with_equipment_type = equipment_type, 
                with_equipment_stone = True)
        compare.check_item(data, req.item)

        return DataBase().commit(data)


    def _mount_equipment_stone_succeed(self, data, req, timer):
        res = hero_pb2.MountStoneRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Mount equipment stone succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _mount_equipment_stone_failed(self, err, req, timer):
        logger.fatal("Mount equipment stone failed[reason=%s]" % err)

        res = hero_pb2.MountStoneRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Mount equipment stone failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def demount_equipment_stone(self, user_id, request):
        """给装备卸下宝石
        """
        timer = Timer(user_id)

        req = hero_pb2.DemountStoneReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_demount_equipment_stone, req, timer)
        defer.addCallback(self._demount_equipment_stone_succeed, req, timer)
        defer.addErrback(self._demount_equipment_stone_failed, req, timer)
        return defer


    def _calc_demount_equipment_stone(self, data, req, timer):
        """装备卸下宝石逻辑
        """
        heroes_basic_id = []
        equipments_type = []
        equipments_stones_id =[]

        for hero_info in req.heros:
            heroes_basic_id.append(hero_info.basic_id)
            
            if len(hero_info.stone_weapon) != 0:
                equipments_type.append(HeroInfo.EQUIPMENT_TYPE_WEAPON)
                equipments_stones_id.append(hero_info.stone_weapon)
            elif len(hero_info.stone_armor) != 0:
                equipments_type.append(HeroInfo.EQUIPMENT_TYPE_ARMOR)
                equipments_stones_id.append(hero_info.stone_armor)
            elif len(hero_info.stone_treasure) != 0:
                equipments_type.append(HeroInfo.EQUIPMENT_TYPE_TREASURE)
                equipments_stones_id.append(hero_info.stone_treasure)
            else:
                raise Exception("Equipment type error")

        item_list = []
        if not hero_business.demount_equipment_stone(data, heroes_basic_id,
                equipments_type, equipments_stones_id, req.item.basic_id, timer.now):
            raise Exception("Demount equipment stone failed")

        #验证
        for i in range(len(req.heros)):
            compare.check_hero(data, req.heros[i], with_equipment_type = equipments_type[i],
                with_equipment_stone = True)
        compare.check_item(data, req.item)

        return DataBase().commit(data)


    def _demount_equipment_stone_succeed(self, data, req, timer):
        res = hero_pb2.DemountStoneRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Demount equipment stone succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _demount_equipment_stone_failed(self, err, req, timer):
        logger.fatal("Demount equipment stone failed[reason=%s]" % err)

        res = hero_pb2.DemountStoneRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Demount equipment stone failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def upgrade_equipment_stone(self, user_id, request):
        """给装备上的宝石升级
        """
        timer = Timer(user_id)

        req = hero_pb2.UpgradeStoneReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_upgrade_equipment_stone, req, timer)
        defer.addCallback(self._upgrade_equipment_stone_succeed, req, timer)
        defer.addErrback(self._upgrade_equipment_stone_failed, req, timer)
        return defer


    def _calc_upgrade_equipment_stone(self, data, req, timer):
        """装备上的宝石升级逻辑
        """
        hero_id = HeroInfo.generate_id(data.id, req.hero.basic_id)
        hero = data.hero_list.get(hero_id)

        if hero is None:
            raise Exception("Hero not exist")

        if len(req.hero.stone_weapon) != 0:
            equipment_type = HeroInfo.EQUIPMENT_TYPE_WEAPON
            equipment_stones_id = req.hero.stone_weapon
        elif len(req.hero.stone_armor) != 0:
            equipment_type = HeroInfo.EQUIPMENT_TYPE_ARMOR
            equipment_stones_id = req.hero.stone_armor
        elif len(req.hero.stone_treasure) != 0:
            equipment_type = HeroInfo.EQUIPMENT_TYPE_TREASURE
            equipment_stones_id = req.hero.stone_treasure
        else:
            raise Exception("Equipment type error")

        if not hero_business.upgrade_equipment_stone(data, req.hero.basic_id,
                req.item.basic_id, equipment_type, equipment_stones_id, timer.now):
            raise Exception("Upgrade equipment stone failed")

        #验证
        compare.check_hero(data, req.hero, with_equipment_type = equipment_type, 
                with_equipment_stone = True)
        compare.check_item(data, req.item)

        return DataBase().commit(data)


    def _upgrade_equipment_stone_succeed(self, data, req, timer):
        res = hero_pb2.UpgradeStoneRes()
        res.status = 0
        pack.pack_resource_info(data.resource.get(True), res.resource)
        response = res.SerializeToString()
        log = log_formater.output(data, "Upgrade equipment stone succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _upgrade_equipment_stone_failed(self, err, req, timer):
        logger.fatal("Upgrade equipment stone failed[reason=%s]" % err)

        res = hero_pb2.UpgradeStoneRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Upgrade equipment stone failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



