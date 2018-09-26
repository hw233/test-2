#coding:utf8
"""
Created on 2016-10-31
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟捐献逻辑
"""

from gunion.business import member as member_business
from gunion.data.donate_box import UnionDonateBox
from gunion.data.member import UnionMemberInfo
from gunion.data.donate_record import UnionDonateRecord
from datalib.data_loader import data_loader
from utils import utils
import random
from proto import union_pb2

def get_donate_box(union_data, box_id, readonly = False):
    id = UnionDonateBox.generate_id(union_data.id, box_id)
    return union_data.donate_box_list.get(id, readonly)

def is_able_to_initiate_donate(union_data, user_id, box_id, timer):
    """是否可以发起捐献"""
    member = member_business.find_member(union_data, user_id)
    donate_box = get_donate_box(union_data, box_id, True)
    if donate_box is None:
        return union_pb2.UNION_DONATE_BOX_INVALID
    is_leader = member.position != UnionMemberInfo.POSITION_MEMBER
    is_box_status = donate_box.get_status(timer.now) == UnionDonateBox.IDLE
    
    if not is_leader:
        return union_pb2.UNION_NO_AUTH
    if not is_box_status:
        return union_pb2.UNION_DONATE_BOX_INVALID
    return 0

def initiate_donate(union_data, box_id, timer):
    """发起捐献"""
    donate_box = get_donate_box(union_data, box_id)
    donate_box.initiate_donate(timer.now)

def is_able_to_start_donate(union_data, box_id, timer):
    """是否可以进行捐献"""
    donate_box = get_donate_box(union_data, box_id, True)
    if donate_box is None:
        return False
    return donate_box.get_status(timer.now) == UnionDonateBox.DONATING

def start_donate(union_data, box_id, user_id, user_name, donate_tpye, timer):
    """进行捐献"""
    (probability, honor, prosperity, progress) = get_donate_info_by_grade(box_id, donate_tpye)

    donate_box = get_donate_box(union_data, box_id)
    member = member_business.find_member(union_data, user_id)
    union = union_data.union.get()
    donate_box.gain_donate_progress(progress, timer.now)
    member.gain_honor(honor)
    union.gain_prosperity(prosperity, timer.now)

    #如果这次捐献导致宝箱捐满，就生成一个新宝箱
    if donate_box.get_status(timer.now) == UnionDonateBox.UNLOCKED:       
        new_donate_box = create_new_donate_box(union_data)
        add_donate_box(union_data, new_donate_box)
    
    add_donate_record(
        union_data, user_id, user_name, box_id, donate_tpye, honor, progress, prosperity)

    return honor, donate_box

def get_donate_info_by_grade(box_id, donate_grade):
    """获取捐献等级信息"""
    box_type = data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id].type
    key = str(box_type) + "_" + str(donate_grade)
    
    probability = data_loader.UnionDonateCostBasicInfo_dict[key].probability
    honor = data_loader.UnionDonateCostBasicInfo_dict[key].unionHonor
    prosperity = data_loader.UnionDonateCostBasicInfo_dict[key].unionProsperity
    progress = data_loader.UnionDonateCostBasicInfo_dict[key].donateProgress

    return (probability, honor, prosperity, progress)

def is_able_to_reward_donate_box(union_data, box_id, timer):
    """是否可以领取捐献箱"""
    donate_box = get_donate_box(union_data, box_id)
    if donate_box is None:
        return False
    return donate_box.get_status(timer.now) == UnionDonateBox.UNLOCKED

def is_able_to_refresh_donate_box(union_data, box_id, user_id, timer):
    """是否可以刷新捐献箱"""
    member = member_business.find_member(union_data, user_id)
    donate_box = get_donate_box(union_data, box_id)
    if donate_box is None:
        return union_pb2.UNION_DONATE_BOX_INVALID

    if member is None:
        is_leader = False
    else:
        is_leader = member.position != UnionMemberInfo.POSITION_MEMBER
    is_box_status = donate_box.get_status(timer.now) == UnionDonateBox.IDLE
    is_refresh = donate_box.is_refresh(union_data, timer.now)

    if not is_leader:
        return union_pb2.UNION_NO_AUTH
    if not is_box_status:
        return union_pb2.UNION_DONATE_BOX_INVALID
    if not is_refresh:
        return union_pb2.UNION_DONATE_NO_CONDITION
    return 0

def create_new_donate_box(union_data):
    """生成一个新宝箱"""
    my_boxes_id = set([box.box_id 
        for box in union_data.donate_box_list.get_all(True) 
        if box.status != UnionDonateBox.NULL])
    box_list = [
        data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id]
        for box_id in data_loader.UnionDonateTreasureBoxBasicInfo_dict.keys()
        if box_id not in my_boxes_id
    ]
    assert len(box_list) > 0
    box_info = _choice_donate_box(box_list)
    return UnionDonateBox.create(
        union_data.id, box_info.donateTreasureBoxID, UnionDonateBox.IDLE)


def _choice_donate_box(box_list):
    box_weight_list = []
    weight = 0
    for box in box_list:
        weight += box.weight
        box_weight_list.append(weight)

    rand = random.uniform(0, weight)
    for i, box in enumerate(box_list):
        if i == 0:
            if 0 <= rand <= box_weight_list[i]:
                return box
        else:
            if box_weight_list[i - 1] <= rand <= box_weight_list[i]:
                return box

def refresh_donate_box(union_data, old_box_id, timer, auto = False):
    """刷新捐献箱"""
    old_box = get_donate_box(union_data, old_box_id)
    new_box = create_new_donate_box(union_data)
    union = union_data.union.get()

    old_box.status = UnionDonateBox.NULL
    if not auto:#手动刷新
        union.donate_last_refresh_time = timer.now
    else:#自动刷新
        union.donate_last_auto_time = timer.now

    return add_donate_box(union_data, new_box)

def add_donate_box(union_data, box):
    """添加新宝箱"""
    my_box = union_data.donate_box_list.get(box.id)
    if my_box is None:
        union_data.donate_box_list.add(box)
        return box
    else:
        my_box.status = box.status
        my_box.start_time = box.start_time
        my_box.progress = box.progress
        return my_box

def auto_refresh_donate_boxes(union_data, timer):
    """自动刷新捐献箱(所有可刷新的宝箱)"""
    for donate_box in union_data.donate_box_list.get_all():
        if donate_box.is_auto_refresh(union_data, timer.now):
            refresh_donate_box(union_data, donate_box.box_id, timer, True)

MAX_DONATE_RECORDS = 20     #最大捐献记录数

def add_donate_record(union_data, user_id, user_name, box_id, grade, add_honor, add_progress, add_prosperity):
    """添加捐献记录"""
    union = union_data.union.get()
    index = union.get_donate_next_index()
    
    new_record = UnionDonateRecord.create(
        union_data.id,
        index,
        user_id,
        user_name,
        box_id,
        grade,
        add_honor,
        add_progress,
        add_prosperity
    )
    union_data.donate_record_list.add(new_record)


def get_donate_records(union_data):
    """读取捐献记录"""
    donate_records = union_data.donate_record_list.get_all()
    donate_records.sort(key=lambda record: record.index)

    for record in donate_records:
        if len(donate_records) > MAX_DONATE_RECORDS:
            record = donate_records.pop(0)
            union_data.donate_record_list.delete(record.id)

    return donate_records
