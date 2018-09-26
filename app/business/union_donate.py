#coding:utf8
"""
Created on 2016-10-27
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 联盟捐献处理逻辑
"""


from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app.data.donate_box import UserDonateBox
from app.union_member_matcher import UnionMemberMatcher
from app.business import item as item_business
from app import pack
from proto import resource_pb2
from proto import union_pb2
from app import log_formater


def syn_donate_boxes(user_data, boxes_info):
    """同步所有的宝箱信息"""
    for box_info in boxes_info:
        syn_donate_box(user_data, box_info)

def syn_donate_box(user_data, box_info):
    """同步单个宝箱信息"""
    id = UserDonateBox.generate_id(user_data.id, box_info.treasurebox_id)
    donate_box = user_data.userdonatebox_list.get(id)
    if donate_box == None:
        donate_box = UserDonateBox.create(user_data.id, box_info.treasurebox_id)
        donate_box.refresh_donate_level()
        donate_box.update_donate_box_by_boxinfo(box_info)
        user_data.userdonatebox_list.add(donate_box)
    else:
        donate_box.update_donate_box_by_boxinfo(box_info)

def is_donate_box_valid(user_data, box_id):
    """宝箱是否可用"""
    id = UserDonateBox.generate_id(user_data.id, box_id)
    donate_box = user_data.userdonatebox_list.get(id, True)
    return not(donate_box is None or donate_box.status == UserDonateBox.NULL)

def is_donate_box_rewarded(user_data, box_id):
    """宝箱是否领取过了"""
    id = UserDonateBox.generate_id(user_data.id, box_id)
    donate_box = user_data.userdonatebox_list.get(id, True)
    if donate_box is None:
        return False
    
    if donate_box.status == UserDonateBox.UNLOCKED and \
        donate_box.is_rewarded == 1:
        return True
    else:
        return False
    
def query_donate_level(user_data, box_id):
    """查询该用户可捐献的等级"""
    id = UserDonateBox.generate_id(user_data.id, box_id)
    donate_box = user_data.userdonatebox_list.get(id, True)
    if donate_box == None:
        raise Exception("No such box in donate_box list")
        
    return donate_box.get_donate_level()
    

def trun_donate_records_to_strings(donate_records):
    """把捐献记录转化成字符串"""
    '''
    matcher = UnionMemberMatcher()
    for record in donate_records:
        matcher.add_condition(record.user_id)
    defer = matcher.match()
    defer.addCallback(_calc_trun_donate_records_to_strings, donate_records)
    return defer


def _calc_trun_donate_records_to_strings(matcher, donate_records):
    '''
    strings = []
    for record in donate_records:
        #(name, level, icon, last_login_time, battle_score, honor) = matcher.result[record.user_id]
        (money, gold) = get_donate_resources_by_boxid(record.box_id, record.grade)

        string = union_pb2.UnionDonateRecord()
        string.user_name = record.user_name#name
        string.money = money
        string.gold = gold
        string.box_id = record.box_id
        string.progress = record.add_progress
        string.prosperity = record.add_prosperity
        strings.append(string)

    return strings


def get_donate_resources_by_boxid(box_id, grade):
    """通过宝箱id和捐献等级获取捐献的资源"""
    box_type = data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id].type
    key = str(box_type) + "_" + str(grade)
    money = data_loader.UnionDonateCostBasicInfo_dict[key].money
    gold = data_loader.UnionDonateCostBasicInfo_dict[key].gold

    return (money, gold)

def get_true_cold_time(user_data, timer):
    """获取真实的冷却时间"""
    union = user_data.union.get(True)
    truetime = union.last_donate_time + union.donate_coldtime - timer.now
    if truetime < 0:
        return 0
    else:
        return truetime

def is_able_start_donate(user_data, box_id, donate_type, timer):
    """判断是否可以进行捐献"""
    (money, gold) = get_donate_resources_by_boxid(box_id, donate_type)
    donate_level = query_donate_level(user_data, box_id)
    truetime = get_true_cold_time(user_data, timer)

    resource = user_data.resource.get()
    resource.update_current_resource(timer.now)

    box_type = data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id].type
    key = str(box_type) + "_" + str(donate_type)
    limit_time = data_loader.UnionDonateCostBasicInfo_dict[key].coldTimeLimit
    
    return resource.money >= money and resource.gold >= gold and \
        donate_type in donate_level and \
        truetime < limit_time

def start_donate(user_data, box_id, honor, donate_type, timer):
    """进行联盟捐献"""
    _refresh_cold_time(user_data, box_id, donate_type, timer)
    _refresh_donate_level(user_data, box_id)
    _consume_resources(user_data, box_id, donate_type, timer)

    union = user_data.union.get()
    union.gain_honor(honor)


def _refresh_cold_time(user_data, box_id, donate_type, timer):
    """刷新冷却时间"""
    truetime = get_true_cold_time(user_data, timer)

    box_type = data_loader.UnionDonateTreasureBoxBasicInfo_dict[box_id].type
    key = str(box_type) + "_" + str(donate_type)
    truetime += data_loader.UnionDonateCostBasicInfo_dict[key].coldTimePerDonate
    
    union = user_data.union.get()
    union.last_donate_time = timer.now
    union.donate_coldtime = truetime

def _refresh_donate_level(user_data, box_id):
    """刷新可捐献等级"""
    id = UserDonateBox.generate_id(user_data.id, box_id)
    donate_box = user_data.userdonatebox_list.get(id)
    if donate_box == None:
        raise Exception("No Such Box in donate_box list")
    donate_box.refresh_donate_level()

def _consume_resources(user_data, box_id, donate_type, timer):
    """根据捐献等级消耗资源"""
    (money, gold) = get_donate_resources_by_boxid(box_id, donate_type)
    resource = user_data.resource.get()

    resource.update_current_resource(timer.now)
    original_gold = resource.gold
    resource.cost_money(money)
    resource.cost_gold(gold)
    log = log_formater.output_gold(user_data, -gold, log_formater.CONSUME_RESOURCES,
              "Consume resources use gold", before_gold = original_gold)
    logger.notice(log)

def pack_resources(user_data, timer):
    """打包资源"""
    resource_pack = resource_pb2.ResourceInfo()
    resource = user_data.resource.get()
    resource.update_current_resource(timer.now)
    
    pack.pack_resource_info(resource, resource_pack)
    return resource_pack

def reward_donate_box(user_data, reward, box_id, timer):
    """领取捐献箱奖励"""
    id = UserDonateBox.generate_id(user_data.id, box_id)
    donate_box = user_data.userdonatebox_list.get(id)
    if donate_box == None:
        raise Exception("No such box in donate_box list")    
    donate_box.reward_donate_box()

    resource = user_data.resource.get()
    resource.update_current_resource(timer.now)
    original_gold = resource.gold
    resource.gain_money(reward.resource.money)
    resource.gain_food(reward.resource.food)
    resource.gain_gold(reward.resource.gold)
    log = log_formater.output_gold(user_data, reward.resource.gold, log_formater.DONATE_REWARD_GOLD,
                "Gain gold from donate box", before_gold = original_gold)
    logger.notice(log)

    item_list = []
    for i, id in enumerate(reward.item_id):
        item_list.append([id, reward.item_num[i]])
    
    item_business.gain_item(user_data, item_list, "donate reward", log_formater.DONATE_REWARD)

def is_able_clear_coldtime(user_data, gold, timer):
    """是否能够(有足够的元宝)清空冷却时间"""
    key = data_loader.UnionDonateCostBasicInfo_dict.keys()[0]
    if data_loader.UnionDonateCostBasicInfo_dict[key].goldNum != gold:
        raise Exception("Bad gold request")
    
    resource = user_data.resource.get()
    resource.update_current_resource(timer.now)
    return resource.gold >= gold

def clear_coldtime(user_data, gold, timer):
    """清空冷却时间"""
    resource = user_data.resource.get()
    resource.update_current_resource(timer.now)
    original_gold = resource.gold
    assert resource.cost_gold(gold)
        
    log = log_formater.output_gold(user_data, -gold, log_formater.CLEAR_COLDTIME,
              "Clear coldtime by gold", before_gold = original_gold)
    logger.notice(log)

    union = user_data.union.get()
    union.donate_coldtime = timer.now - union.last_donate_time

def is_able_reward_donate_box(user_data, box_id):
    """是否可以领取宝箱"""
    id = UserDonateBox.generate_id(user_data.id, box_id)
    donate_box = user_data.userdonatebox_list.get(id, True)
    if donate_box is None:
        return False
    return donate_box.status == UserDonateBox.UNLOCKED and \
        donate_box.is_rewarded == 0

def refresh_donate_box(user_data, old_box_id, new_box_info):
    """刷新宝箱"""
    #旧宝箱不删除,仅标记为NULL
    id = UserDonateBox.generate_id(user_data.id, old_box_id)
    old_box = user_data.userdonatebox_list.get(id)
    old_box.status = UserDonateBox.NULL
    #添加新宝箱
    syn_donate_box(user_data, new_box_info)
