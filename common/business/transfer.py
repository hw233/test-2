#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场
"""

from common.data.transfer import TransferInfo

def get_transfer_by_user_id(data, user_id, readonly=False):
    id = TransferInfo.generate_id(data.id, user_id)
    return data.transfer_list.get(id, readonly)

