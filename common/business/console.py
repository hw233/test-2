#coding:utf8
"""
Created on 2016-07-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 控制
"""

import random
from utils import logger
from common.business import worldboss as worldboss_business
from common.data.console import ConsoleInfo
from common.data.exchange import CommonExchangeInfo
from common.data.country import CountryInfo


def init_console(data, now):
    console = ConsoleInfo.create(data.id)
    data.console.add(console)

    worldboss_business.init_worldboss(data, now)
    
    exchange = CommonExchangeInfo.create(data.id)
    data.exchange.add(exchange)

    country = CountryInfo.create(data.id)
    data.country.add(country)
    return True



