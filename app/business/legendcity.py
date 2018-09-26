#coding:utf8
"""
Created on 2016-05-18
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 史实城相关业务逻辑
"""

import base64
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.legendcity import LegendCityInfo
from app.data.legendcity import LegendCityRecordInfo
from app.data.node import NodeInfo


def init_legendcity(data, now):
    """初始化史实城
    """
    for city_id in data_loader.LegendCityBasicInfo_dict:
        node_id = NodeInfo.generate_id(data.id,
                data_loader.LegendCityBasicInfo_dict[city_id].nodeId)
        legendcity = LegendCityInfo.create(data.id, city_id, node_id, now)
        data.legendcity_list.add(legendcity)

    return True


def add_battle_record(data, legendcity):
    """添加史实城战斗记录
    """
    index = legendcity.get_next_record_index()

    #TODO 临时方案 fix bug
    while True:
        id = LegendCityRecordInfo.generate_id(data.id, legendcity.city_id, index)
        record = data.legendcity_record_list.get(id, True)
        if record is None:
            break
        index = legendcity.get_next_record_index()

    #删除过旧的记录
    MAX_COUNT = 20
    if index > MAX_COUNT:
        delete_index = index - MAX_COUNT
        id = LegendCityRecordInfo.generate_id(data.id, legendcity.city_id, delete_index)
        record = data.legendcity_record_list.get(id, True)
        if record is not None:
            data.legendcity_record_list.delete(id)

    record = LegendCityRecordInfo.create(data.id, legendcity.city_id, index)
    data.legendcity_record_list.add(record)
    return record


def get_legendcity_award(city_id, position_level):
    """史实城官职奖励
    """
    key = "%d_%d" % (city_id, position_level)
    items_id = data_loader.LegendCityPositionBasicInfo_dict[key].rewardItemsBasicId
    items_num = data_loader.LegendCityPositionBasicInfo_dict[key].rewardItemsNum
    assert len(items_id) == len(items_num)

    items = []
    for index in range(0, len(items_id)):
        items.append((items_id[index], items_num[index]))

    return items



BROADCAST_POSITION_LEVELS = [7, 6, 5]
def is_need_broadcast(position_level):
    """获得官阶时触发广播
    """
    if position_level in BROADCAST_POSITION_LEVELS:
        return True
    else:
        return False


def create_broadcast_content(user, legendcity_id, position_level):
    """创建广播信息
    """
    key = "broadcast_id_legendcity_" + str(position_level)

    broadcast_id = int(float(data_loader.OtherBasicInfo_dict[key].value))

    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(user.name), 1)
    content = content.replace("#str#", ("@%s@" % data_loader.LegendCityBasicInfo_dict[
        legendcity_id].nameKey).encode("utf-8"), 1)

    return (mode_id, priority, life_time, content)


