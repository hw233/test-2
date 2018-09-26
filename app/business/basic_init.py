#coding:utf8
"""
Created on 2016-09-22
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 
"""

import random
from utils import logger
from utils import utils
#from datalib.data_loader import data_loader
from app.data.basic_init import BasicInitInfo
#from app.business import conscript as conscript_business


def create_basic_init(basic_data, basic_id):
    init = BasicInitInfo.create(basic_id)
    basic_data.init.add(init)
    return True

