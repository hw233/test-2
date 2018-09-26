#coding:utf8
"""
Created on 2016-09-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 试炼记录逻辑
"""

import random
from utils import logger
from datalib.data_loader import data_loader
from common.data.anneal_record import AnnealRecordInfo


FIRST_FINISH_TYPE = 1
FAST_FINISH_TYPE = 2


def query_anneal_record(data, floor):
    """查询试炼记录
    """
    anneal_record = data.anneal_record_list.get(floor)
    if anneal_record is None:
        anneal_record = AnnealRecordInfo.create(floor, data.id)
        data.anneal_record_list.add(anneal_record)

    return anneal_record


def update_anneal_record(data, floor, type, name, level, icon_id, passed_time, cost_time, now):
    """更新试炼记录
    """
    anneal_record = data.anneal_record_list.get(floor)
    if anneal_record is None:
        anneal_record = AnnealRecordInfo.create(floor, data.id)
        data.anneal_record_list.add(anneal_record)

    if type == FIRST_FINISH_TYPE:
        if anneal_record.is_need_to_update_first_record():
            anneal_record.update_first_record(name, level, icon_id, passed_time, now)

    elif type == FAST_FINISH_TYPE:
        if anneal_record.is_need_to_update_fast_record(cost_time):
            anneal_record.update_fast_record(name, level, icon_id, passed_time, cost_time, now)

    return True
        

