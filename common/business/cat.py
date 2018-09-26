#coding:utf8
"""
Created on 2016-07-03
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 招财猫
"""

import random
from utils import logger
from datalib.data_loader import data_loader
from common.data.cat import CatInfo

MAX_BROADCAST_NUM = 10
def add_cat( data, common_id, user_id, name, gold, index):
    """添加招财猫记录
    """

    #删除要淘汰的数据
    _eliminate_cat(data, MAX_BROADCAST_NUM - 1)
    cat = CatInfo.create(common_id, user_id, name, gold, index)
    logger.notice("==========CAT")
    data.cat_list.add(cat)
    return True


def _eliminate_cat(data, remain_num = MAX_BROADCAST_NUM):
    """淘汰广播
    """
    logger.notice("===========DELETE")
    #2.条数淘汰
    cat_list = data.cat_list.get_all()
    logger.notice("len=%d"%len(cat_list))
    sort_list = cat_list[::-1]
    delete_list = []
    if len(cat_list) > remain_num:
        delete_list = sort_list[remain_num:]   
        logger.notice("delete_list =%s"%delete_list)                                                                                                                              
    logger.debug("Delete overmuch cat num=%d" % len(delete_list))                                                                                                                   
    #删除末尾数据                                                                                                                                                                         
    for delete_record in delete_list:                                                                                                                                                     
        record = data.cat_list.get(delete_record.id)                                                                                                                                
        logger.debug("Delete one cat[id=%d][name=%s]"                                                                                             
                % (record.id, record.name))                                                                                                     
        data.cat_list.delete(delete_record.id)                  
