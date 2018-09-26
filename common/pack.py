#coding:utf8
"""
"""

def pack_transfer_info(info, message, transfer_type):
    message.user_id = info.user_id
    message.rank = info.rank
    message.is_robot = info.is_robot
    message.transfer_type = transfer_type