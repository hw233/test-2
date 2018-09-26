#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : common模块提供的服务，供 App 模块使用
"""

from firefly.server.globalobject import rootserviceHandle
from common.processor.broadcast_processor import BroadcastProcessor
from common.processor.common_processor import CommonProcessor
from common.processor.anneal_record_processor import AnnealRecordProcessor
from common.processor.worldboss_processor import WorldBossProcessor
from common.processor.exchange_processor import ExchangeProcessor
from common.processor.transfer_processor import TransferProcessor
from common.processor.country_processor import CountryProcessor

_common_processor = CommonProcessor()
@rootserviceHandle
def delete_common(common_id, data):
    """删除common内容"""
    return _common_processor.delete_common(common_id, data)

@rootserviceHandle
def fortune_cat(common_id, data):
    """添加招财猫奖励记录"""
    return _common_processor.add_cat(common_id, data)
@rootserviceHandle
def query_cat(common_id, data):
    """查询招财猫奖励记录"""
    return _common_processor.query_cat(common_id, data)

_broadcast_processor = BroadcastProcessor()
@rootserviceHandle
def query_broadcast_record(common_id, data):
    """查询广播信息"""
    return _broadcast_processor.query(common_id, data)


@rootserviceHandle
def add_broadcast_record(common_id, data):
    """增加广播信息"""
    return _broadcast_processor.add(common_id, data)


@rootserviceHandle
def delete_broadcast_record(common_id, data):
    """删除广播信息"""
    return _broadcast_processor.delete(common_id, data)


_anneal_record_processor = AnnealRecordProcessor()
@rootserviceHandle
def query_anneal_record(common_id, data):
    """查询试炼记录"""
    return _anneal_record_processor.query_anneal_record(common_id, data)


@rootserviceHandle
def update_anneal_record(common_id, data):
    """更新试炼记录信息"""
    return _anneal_record_processor.update_anneal_record(common_id, data)


_worldboss_processor = WorldBossProcessor()
@rootserviceHandle
def query_common_worldboss(common_id, data):
    """查询世界boss公共信息"""
    return _worldboss_processor.query(common_id, data)


@rootserviceHandle
def modify_common_worldboss(common_id, data):
    """修改世界boss公共信息"""
    return _worldboss_processor.modify(common_id, data)


_exchange_processor = ExchangeProcessor()
@rootserviceHandle
def query_exchange_info(common_id, data):
    """查询兑换信息"""
    return _exchange_processor.query(common_id, data)

_transfer_processor = TransferProcessor()
@rootserviceHandle
def query_transfer_info(common_id, data):
    """查询换位演武场排行棒"""
    return _transfer_processor.query(common_id, data)

@rootserviceHandle
def exchange_transfer(common_id, data):
    """交换换位演武场排名"""
    return _transfer_processor.exchange(common_id, data)


_country_processor = CountryProcessor()
@rootserviceHandle
def query_suggested_country(common_id, data):
    """查询推荐的国家势力"""
    return _country_processor.query_suggested_country(common_id, data)

@rootserviceHandle
def update_country(common_id, data):
    """更改国家势力"""
    return _country_processor.update_country(common_id, data)



