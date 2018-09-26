#coding:utf8
"""
Created on 2015-02-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 城市相关数值计算
"""

import time
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.city import CityInfo
from app.data.building import BuildingInfo


def create_main_city(data, pattern):
    """创建一个主城
    Args:
        data[UserData]: 用户信息
        pattern[int]: 初始化模式
    Returns:
        True
        False
    """
    basic_id = data_loader.InitUserBasicInfo_dict[pattern].cityBasicId
    city = CityInfo.create(data.id, basic_id, True)
    data.city_list.add(city)

    name = data_loader.InitUserBasicInfo_dict[pattern].cityName
    name = name.encode("utf-8")
    if not city.change_name(name):
        return False

    return True


def init_main_city(data, pattern):
    """初始化主城，在主城中初始化必要建筑
    在初始化配置中配置
    理论上需要包括：官邸、酒肆、城防
    Args:
        data[UserData]: 用户信息
        pattern[int]: 初始化模式
    Returns:
        True
        False
    """
    user = data.user.get()

    main_city = None
    for city in data.city_list.get_all():
        if city.is_main:
            main_city = city
            break

    if main_city is None:
        logger.warning("Main city not exist")
        return False

    #初次创建建筑时，并不检查是否可以进行建造
    info = data_loader.InitUserBasicInfo_dict[pattern]
    building_ids = info.buildingBasicId
    building_levels = info.buildingLevel
    building_slots = info.buildingSlotIndex
    building_garrison = info.buildingGarrisonNum
    assert len(building_ids) == len(building_levels)
    assert len(building_ids) == len(building_slots)
    assert len(building_ids) == len(building_garrison)

    #首先创建官邸建筑
    mansion_basic_id = BuildingInfo.get_mansion_basic_id()
    mansion_index = building_ids.index(mansion_basic_id)
    mansion = create_building(main_city, user, 0,
            building_slots[mansion_index], mansion_basic_id, building_levels[mansion_index])
    if mansion is None:
        logger.warning("Create mansion failed")
        return False
    occupy_num = int(data_loader.OccupyNodeNumByMansion_dict[mansion.level].occupyNodeNum)
    map = data.map.get()
    map.update_occupy_node_num_mansion(occupy_num)
    data.building_list.add(mansion)

    #创建其他建筑
    for index in range(0, len(building_ids)):
        basic_id = building_ids[index]
        if basic_id == mansion_basic_id:
            continue

        level = building_levels[index]
        slot_index = building_slots[index]
        garrison_num = building_garrison[index]

        building = create_building(main_city, user, mansion.level,
                slot_index, basic_id, level, garrison_num, True)
        if building is None:
            logger.warning("Create building failed[basic id=%d]" % basic_id)
            return False

        if building.is_watchtower() and building.level != 0:
            occupy_num = int(data_loader.OccupyNodeNumByWatchTower_dict[building.level].occupyNodeNum)
            map.update_occupy_node_num_watchtower(occupy_num)

        data.building_list.add(building)

    return True


def _is_able_to_create(city, building_basic_id, mansion_level):
    """检查建筑是否可以新建
    Args:
        city[CityInfo]: 建筑所在城池
        building_basic_id[int]: 新建建筑的basic_id
        mansion_level[int]: 官邸等级
    """
    #同一个城池内，同类型建筑数量不超上限
    slots = city.get_all_building()
    count = 1
    for id in slots:
        bid = BuildingInfo.get_basic_id(id)
        if bid == building_basic_id:
            count += 1

    key = '%d_%d' % (building_basic_id, count)
    if key not in data_loader.BuildingNumBasicInfo_dict:
        logger.warning("Can not create building any more[basic_id=%d][count=%d]" %
                (building_basic_id, count))
        return False

    #官邸等级满足要求
    need_mansion_level = data_loader.BuildingNumBasicInfo_dict[key].limitBuildingLevel
    if mansion_level < need_mansion_level:
        logger.warning("Invalid mansion[need level=%d][level=%d]"
                "[building basic id=%d][building count=%d]" %
                (need_mansion_level, mansion_level, building_basic_id, count))
        return False

    return True


def create_building(city, user, mansion_level,
        slot_index, building_basic_id, level = 0, garrison_num = 1,
        force = False):
    """创建一个新的建筑
    Args:
        city[CityInfo in/out]: 城池信息
        slot_index[int]: 建筑物的位置, 从1开始
        building_basic_id[int]: 建筑物的basic id
        level[int]: 建筑物的等级，默认为0
        garrison_num[int]: 建筑物的驻守位数量，默认为1
    Returns:
        BuildingInfo 建筑物信息
    """
    if not force and not _is_able_to_create(city, building_basic_id, mansion_level):
        return None

    building = BuildingInfo.create(
            user.id, building_basic_id,
            city, slot_index, level, garrison_num)

    if not city.place_building(building, building.is_mansion()):
        return None

    return building


