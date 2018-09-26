#coding:utf8
"""
Created on 2016-11-22
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 兑换流程
"""

from common.data.exchange import CommonExchangeInfo

def refresh_exchange(data, now):
    """刷新兑换信息"""
    exchange = data.exchange.get()
    if now - exchange.last_refresh_time >= CommonExchangeInfo.refresh_time():
        exchange.refresh()
        exchange.last_refresh_time = \
            now - (now - exchange.last_refresh_time) % CommonExchangeInfo.refresh_time()
