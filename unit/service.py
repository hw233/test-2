#coding:utf8
"""
Created on 2015-01-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : App 模块提供的服务，供 Portal 模块使用
"""

from firefly.server.globalobject import rootserviceHandle
from unit.processor.city_processor import CityProcessor
from unit.processor.shop_processor import ShopProcessor
from unit.processor.battle_processor import BattleProcessor


_city_processor = CityProcessor()
@rootserviceHandle
def query_city_info(city_id, data):
    """查询史实城信息"""
    return _city_processor.query(city_id, data)

@rootserviceHandle
def update_city_info(city_id, data):
    """更新史实城信息（太守更新）"""
    return _city_processor.update(city_id, data)

@rootserviceHandle
def check(city_id, data):
    """核实信息"""
    return _city_processor.check(city_id, data)

@rootserviceHandle
def add_reputation(city_id, data):
    """获得声望"""
    return _city_processor.add_reputation(city_id, data)

@rootserviceHandle
def cancel_position(city_id, data):
    """取消官职"""
    return _city_processor.cancel_position(city_id, data)

@rootserviceHandle
def delete_city(city_id, data):
    """删除史实城"""
    return _city_processor.delete_city(city_id, data)

@rootserviceHandle
def get_position_rank(city_id, data):
    """获取官职榜"""
    return _city_processor.get_position_rank(city_id, data)


_shop_processor = ShopProcessor()
@rootserviceHandle
def buy_goods(city_id, data):
    """购买商品"""
    return _shop_processor.buy_goods(city_id, data)


_battle_processor = BattleProcessor()
@rootserviceHandle
def start_battle(city_id, data):
    """开始战斗"""
    return _battle_processor.start_battle(city_id, data)

@rootserviceHandle
def finish_battle(city_id, data):
    """结束战斗"""
    return _battle_processor.finish_battle(city_id, data)



