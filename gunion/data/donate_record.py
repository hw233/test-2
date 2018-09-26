#coding:utf8
"""
Created on 2016-10-27
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟捐献记录
"""

from proto import union_pb2
import base64

class UnionDonateRecord(object):
    """联盟捐献记录"""

    PRIMARY_DONATE = union_pb2.Primary
    MIDDLE_DONATE = union_pb2.Intermediate
    HIGH_DONATE = union_pb2.Advanced

    __slots__ = [
        "id",
        "union_id",
        "index",

        "user_id",
        "user_name",
        "box_id",
        "grade",
        "add_honor",
        "add_progress",
        "add_prosperity",
    ]

    def __init__(self):
        self.id = 0
        self.union_id = 0
        self.index = 0
        self.user_id = 0
        self.user_name = ''
        self.box_id = 0
        self.grade = 0
        self.add_honor = 0
        self.add_progress = 0
        self.add_prosperity = 0

    @staticmethod
    def generate_id(union_id, index):
        return union_id << 32 | index
    
    @staticmethod
    def create(union_id, index, user_id, user_name, box_id, grade, add_honor, add_progress, add_prosperity):
        id = UnionDonateRecord.generate_id(union_id, index)

        donate = UnionDonateRecord()
        donate.id = id
        donate.union_id = union_id
        donate.index = index
        donate.user_id = user_id
        donate.user_name = user_name
        donate.box_id = box_id
        donate.grade = grade
        donate.add_honor = add_honor
        donate.add_progress = add_progress
        donate.add_prosperity = add_prosperity

        return donate

    def get_readable_name(self):
        """获取可读的名字"""
        return base64.b64decode(self.user_name)