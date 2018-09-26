#coding:utf8
"""
Created on 2015-09-14
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : Resource 相关业务逻辑
"""

from app.data.resource import ResourceInfo
from app.core import resource as resource_module
from app.core import building as building_module

def recalc_food_output(data):
    """重算粮食产量
        粮食产量 = SUM(农田产量)
    """
    technologys = data.technology_list.get_all(True)
    technologys = [t for t in technologys if t.is_interior_technology() and not t.is_upgrade]

    buildings = data.building_list.get_all(True)
    mansion = [b for b in buildings if b.is_mansion()][0]
    user = data.user.get(True)

    buildings = [b for b in buildings if b.is_farmland() and not b.is_upgrade]
    buildings = [b for b in buildings if b.is_active(user.level, mansion.level)]

    food_output = 0
    for building in buildings:
        heroes_id = building.get_working_hero()
        heroes = [data.hero_list.get(hero_id) for hero_id in heroes_id if hero_id != 0]

        output = resource_module.calc_food_output(building, heroes, technologys)
        building.value = output

        food_output += output

    return food_output

def recalc_money_output(data):
    """重算金币产量
        金币产量 = SUM(市场产量)
    """
    technologys = data.technology_list.get_all(True)
    technologys = [t for t in technologys if t.is_interior_technology() and not t.is_upgrade]

    buildings = data.building_list.get_all(True)
    mansion = [b for b in buildings if b.is_mansion()][0]
    user = data.user.get(True)

    buildings = [b for b in buildings if b.is_market() and not b.is_upgrade]
    buildings = [b for b in buildings if b.is_active(user.level, mansion.level)]
    
    money_output = 0
    for building in buildings:
        heroes_id = building.get_working_hero()
        heroes = [data.hero_list.get(hero_id) for hero_id in heroes_id if hero_id != 0]

        output = resource_module.calc_money_output(building, heroes, technologys)
        building.value = output

        money_output += output

    return money_output

def recalc_food_capacity(data):
    """重算粮食储量
        粮食储量= SUM(农田储量) + 官府储量 + 粮仓储量
    """
    technologys = data.technology_list.get_all(True)
    technologys = [t for t in technologys if t.is_interior_technology() and not t.is_upgrade]

    buildings = data.building_list.get_all(True)
    mansion = [b for b in buildings if b.is_mansion()][0]
    user = data.user.get(True)

    buildings = [b for b in buildings
        if b.is_farmland() or b.is_mansion() or b.is_foodhouse()]
    buildings = [b for b in buildings if b.is_active(user.level, mansion.level)]

    food_capacity = 0
    for building in buildings:
        food_capacity += building_module.calc_food_capacity(
            building.basic_id, building.level, technologys)
    
    return food_capacity

def recalc_money_capacity(data):
    """重算金币储量
        金币储量 = SUM(市场储量) + 官府储量 + 钱库储量
    """
    technologys = data.technology_list.get_all(True)
    technologys = [t for t in technologys if t.is_interior_technology() and not t.is_upgrade]

    buildings = data.building_list.get_all(True)
    mansion = [b for b in buildings if b.is_mansion()][0]
    user = data.user.get(True)

    buildings = [b for b in buildings
        if b.is_market() or b.is_mansion() or b.is_moneyhouse()]
    buildings = [b for b in buildings if b.is_active(user.level, mansion.level)]

    money_capacity = 0
    for building in buildings:
        money_capacity += building_module.calc_money_capacity(
            building.basic_id, building.level, technologys)

    return money_capacity