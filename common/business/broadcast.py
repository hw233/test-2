#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 广播逻辑
"""

import random
from utils import logger
from datalib.data_loader import data_loader
from common.data.broadcast import BroadcastInfo


MAX_BROADCAST_NUM = 15    #最大保存的广播条数


def query_broadcast(data, now):
    """查询所有有效的广播记录
    """
    #删除要淘汰的数据
    _eliminate_broadcast(data, now)
    return data.broadcast_list.get_all(True)


def add_broadcast(data, now, mode_id, priority, life_time, content):
    """添加广播记录
    """
    #删除要淘汰的数据
    _eliminate_broadcast(data, now, MAX_BROADCAST_NUM - 1)

    #创建一条新的广播数据
    console = data.console.get()
    broadcast_id = console.generate_broadcast_id()
    broadcast = BroadcastInfo.create(
            broadcast_id, data.id, now, mode_id, priority, life_time, content)
    data.broadcast_list.add(broadcast)
    return True


def _eliminate_broadcast(data, now, remain_num = MAX_BROADCAST_NUM):
    """淘汰广播
    """
    #淘汰数据
    #1.过期淘汰
    broadcast_list = data.broadcast_list.get_all(True)
    delete_list = []
    for record in broadcast_list:
        if record.is_overdue(now):
            logger.debug("Delete one broadcast"
                    "[id=%d][priority=%d][create_time=%d][life_time=%d][now=%d]"
                    % (record.id, record.priority, record.create_time, record.life_time, now))
            delete_list.append(record.id)
    logger.debug("Delete overdue broadcast num=%d" % len(delete_list))
    for delete_id in delete_list:
        data.broadcast_list.delete(delete_id)

    #2.条数淘汰
    broadcast_list = data.broadcast_list.get_all(True)
    sort_list = []
    delete_list = []
    if len(broadcast_list) > remain_num:
        #排序：按优先级从高到低排序，同优先级的时间从近到远排序
        for record in broadcast_list:
            index = 0
            for i in range(0, len(sort_list)):
                if record.priority < sort_list[i].priority:
                    index = i
                    break
                elif (record.priority == record.priority
                        and record.create_time > sort_list[i].create_time):
                    index = i
                    break

            #插入排序队列 sort_list
            sort_list.insert(index, record)

        delete_list = sort_list[remain_num:]

    logger.debug("Delete overmuch broadcast num=%d" % len(delete_list))
    #删除末尾数据
    for delete_record in delete_list:
        record = data.broadcast_list.get(delete_record.id)
        logger.debug("Delete one broadcast[id=%d][priority=%d][create_time=%d][life_time=%d]"
                % (record.id, record.priority, record.create_time, record.life_time))
        data.broadcast_list.delete(delete_record.id)


def delete_broadcast(data, now, ids):
    """删除指定的广播记录
    """
    #删除指定id的数据
    for id in ids:
        broadcast = data.broadcast_list.get(id)
        if broadcast != None:
            data.broadcast_list.delete(id)

    return True


