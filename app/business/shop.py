#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 商店相关计算逻辑
"""

from utils import logger
from datalib.data_loader import data_loader
from app.data.item import ItemInfo
from app.data.hero import HeroInfo
from app.data.shop import ShopInfo
from app.data.legendcity import LegendCityInfo
from app.business import item as item_business
from app import log_formater


def init_shop(data, now):
    """创建商店信息
    """
    #主城商店：包括金钱商店、元宝商店
    shop = ShopInfo.create(data.id, ShopInfo.GOODS_TYPE_MONEY)
    data.shop_list.add(shop)

    #大地图商店：技巧值商店
    shop = ShopInfo.create(data.id, ShopInfo.GOODS_TYPE_ACHIEVEMENT)
    data.shop_list.add(shop)

    #史实城商店
    for city_id in data_loader.LegendCityBasicInfo_dict:
        shop = ShopInfo.create(data.id, ShopInfo.GOODS_TYPE_LEGENDCITY, city_id)
        data.shop_list.add(shop)

    #联盟商店
    shop = ShopInfo.create(data.id, ShopInfo.GOODS_TYPE_UNION)
    data.shop_list.add(shop)

    #演武场商店
    shop = ShopInfo.create(data.id, ShopInfo.GOODS_TYPE_ARENA)
    data.shop_list.add(shop)

    #精魄商店
    shop = ShopInfo.create(data.id, ShopInfo.GOODS_TYPE_SOUL_SOUL)
    data.shop_list.add(shop)
    
    #元宝商城
    shop = ShopInfo.create(data.id, ShopInfo.GOODS_TYPE_GOLD)
    data.shop_list.add(shop)

    return refresh_goods(data, data.shop_list.get_all(), [], now, None, True)


def refresh_goods(data, shops, goods_list, now, refresh_item = None, free = False):
    """刷新酒肆中可以购买的货物
    Args:
        data[UserData]: 用户信息
        shops[list(ShopInfo)]: 酒肆信息
        goods_list[list(GoodsInfo) out]: 可以购买的货物列表
        now[int]: 当前时间戳
        free[bool]: 是否免费刷新
    """
    user = data.user.get(True)
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)

    use_refresh_item = False
    if not free and refresh_item != None:
        #耗费商铺代币
        if not refresh_item.is_refresh_item():
            logger.warning("Refresh item is wrong[basic_id=%d]" % refresh_item.basic_id)
            return False
        use_refresh_item = True
        if not refresh_item.use_refresh_item(1):
            raise Exception("Use refresh item failed")

    for shop in shops:
        if not free and use_refresh_item == False:
            #花费元宝
            gold_cost = shop.calc_gold_consume_of_refresh_goods(user.vip_level)
            if gold_cost == -1:
                return False
            if not resource.cost_gold(gold_cost):
                return False

        #刷新货物
        if not _refresh_goods_in_shop(data, shop, goods_list, now, free):
            return False

        if not free and refresh_item is None:
            goods_items_id = []
            goods_items_num = []
            for goods in goods_list:
                goods_items_id.append(goods.item_basic_id)
                goods_items_num.append(goods.item_num)
            log = log_formater.output_gold(data, -gold_cost, log_formater.REFRESH_WINESHOP_GOODS,
                    "Refresh wineshop goods by gold", before_gold = original_gold, items_id = goods_items_id,
                    items_num = goods_items_num)
            logger.notice(log)

    return True


def _refresh_goods_in_shop(data, shop, goods_list, now, free):
    """在商店中刷新货物
    """
    user = data.user.get(True)
    union = data.union.get(True)

    #计算货物池
    if shop.type == shop.GOODS_TYPE_MONEY:
        #货物池和主公等级有关
        pool_name = data_loader.GoodsPoolMatchBasicInfo_dict[user.level].moneyPoolName
        goods_num = data_loader.VipBasicInfo_dict[user.vip_level].wineshopItemNum
        discount_num = data_loader.VipBasicInfo_dict[user.vip_level].wineshopDiscountItemNum
        discount = data_loader.VipBasicInfo_dict[user.vip_level].wineshopDiscount
    elif shop.type == shop.GOODS_TYPE_GOLD:
        #货物池和主公等级有关
        pool_name = data_loader.GoodsPoolMatchBasicInfo_dict[user.level].goldPoolName
        #goods_num = data_loader.VipBasicInfo_dict[user.vip_level].wineshopItemNum
        #discount_num = data_loader.VipBasicInfo_dict[user.vip_level].wineshopDiscountItemNum
        #discount = data_loader.VipBasicInfo_dict[user.vip_level].wineshopDiscount
        goods_num = 50
        discount_num = 0
        discount = 10
    elif shop.type == shop.GOODS_TYPE_ACHIEVEMENT:
        #货物池和主公等级有关
        pool_name = data_loader.GoodsPoolMatchBasicInfo_dict[user.level].achievementPoolName
        goods_num = data_loader.VipBasicInfo_dict[user.vip_level].achievementItemNum
        discount_num = data_loader.VipBasicInfo_dict[
                user.vip_level].achievementDiscountItemNum
        discount = data_loader.VipBasicInfo_dict[user.vip_level].achievementDiscount
    elif shop.type == shop.GOODS_TYPE_LEGENDCITY:
        #货物池和史实城有关
        pool_name = data_loader.CityGoodsPoolMatchBasicInfo_dict[shop.index].poolName
        goods_num = 8
        discount_num = 0
        discount = 10
    elif shop.type == shop.GOODS_TYPE_UNION:
        #货物池和联盟等级有关
        pool_name = data_loader.UnionGoodsPoolMatchBasicInfo_dict[union.union_level].poolName
        goods_num = 8
        discount_num = 0
        discount = 10
    elif shop.type == shop.GOODS_TYPE_ARENA:
        #货物池和主公等级有关
        pool_name = data_loader.ArenaGoodsPoolMatchBasicInfo_dict[user.level].poolName
        goods_num = 8
        discount_num = 0
        discount = 10
    elif shop.type == shop.GOODS_TYPE_SOUL_SOUL:
        #精魄的货物池
        pool_name = data_loader.SoulGoodsPoolMatchBasicInfo_dict['soul'].poolName
        goods_num = 8
        discount_num = 0
        discount = 10
    elif shop.type == shop.GOODS_TYPE_SOUL_GOLD:
        #元宝的货物池
        pool_name = data_loader.SoulGoodsPoolMatchBasicInfo_dict['gold'].poolName
        goods_num = 8
        discount_num = 0
        discount = 10
    else:
        logger.warning("Shop type invalid[type=%d]" % shop.type)
        return False

    return shop.refresh_goods(
            pool_name, goods_num, discount_num, discount, goods_list, now, free)



def seek_goods(data, shops, goods_list, now):
    """查询酒肆中可以购买的货物
    如果可以免费刷新，则自动刷新一次
    Args:
        data[UserData]: 用户信息
        shops[list(ShopInfo)]: 酒肆信息
        goods_list[list(GoodsInfo)]: 货物信息列表
        now[int]: 当前时间戳
    Returns:
        True 查询成功
        False 查询失败
    """
    for shop in shops:
        shop.try_reset_shop(now)

        if shop.is_able_to_refresh_free(now):
            #如果可以免费刷新，自动刷新一次
            logger.debug("Refresh goods free auto")
            if not refresh_goods(data, [shop], goods_list, now, free = True):
                return False
        else:
            #如果不能免费刷新，返回之前的货物
            if shop.check_goods():
                if not shop.seek_goods(goods_list):
                    return False
            else:
                #如果因为配表变化导致原来物品失效，则直接刷新
                logger.debug("Refresh goods free for fix")
                if not refresh_goods(data, [shop], goods_list, now, free = True):
                    return False

    return True


def buy_goods(data, shop, id, now, tax = 0):
    """购买货物
    Args:
        shop[ShopInfo out]: 酒肆信息
        resource[ResourceInfo out]: 资源信息
        id[int]: 货物的 id
        tax[int]: 税率 [0-100]
    Returns:
        True/False 是否成功
    """
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)

    goods = shop.buy_goods(id)
    if goods is None:
        return False

    #记录次数
    trainer = data.trainer.get()


    if shop.type == ShopInfo.GOODS_TYPE_MONEY:
        #消耗金钱
        if not resource.cost_money(goods.get_real_price()):
            return False
        trainer.add_daily_buy_goods_in_wineshop(1)
    elif shop.type == ShopInfo.GOODS_TYPE_GOLD:
        #消耗元宝
        if not resource.cost_gold(goods.get_real_price()):
            return False
        trainer.add_daily_buy_goods_in_wineshop(1)
    elif shop.type == ShopInfo.GOODS_TYPE_ACHIEVEMENT:
        #消耗成就值
        if not resource.cost_achievement(goods.get_real_price()):
            return False
        trainer.add_daily_buy_goods_in_achievement_shop(1)

    elif shop.type == ShopInfo.GOODS_TYPE_LEGENDCITY:
        pass
        trainer.add_daily_buy_goods_in_legendcity_shop(1)
    elif shop.type == ShopInfo.GOODS_TYPE_UNION:
        #消耗联盟荣誉
        union = data.union.get()
        if not union.consume_honor(goods.get_real_price()):
            return False
        trainer.add_daily_buy_goods_in_union_shop(1)
    elif shop.type == ShopInfo.GOODS_TYPE_ARENA:
        #消耗演武场代币
        arena = data.arena.get()
        if not arena.cost_coin(goods.get_real_price()):
            return False
    elif shop.type == ShopInfo.GOODS_TYPE_SOUL_SOUL:
        #消耗精魄
        if not resource.cost_soul(goods.get_real_price()):
            return False
        trainer.add_daily_buy_goods_in_soul_shop(1)
    elif shop.type == ShopInfo.GOODS_TYPE_SOUL_GOLD:
        #消耗元宝
        if not resource.cost_gold(goods.get_real_price()):
            return False
        trainer.add_daily_buy_goods_in_soul_shop(1)
    else:
        logger.warning("Invalid shop type[type=%d]" % shop.type)
        return False

    #得到物品
    if not item_business.gain_item(data, [(goods.item_basic_id, goods.item_num)], "shop", log_formater.SHOP):
        return False
    id = ItemInfo.generate_id(data.id, goods.item_basic_id)
    item = data.item_list.get(id)
    if shop.type == ShopInfo.GOODS_TYPE_GOLD:
        log = log_formater.output_gold(data, -goods.get_real_price(), log_formater.BUY_GOODS,
                "Buy goods by gold", before_gold = original_gold, items_id = [goods.item_basic_id],
                items_num = [goods.item_num])
        logger.notice(log)

    return True


