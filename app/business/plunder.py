#coding:utf8
"""
Created on 2016-03-01
@Author: zhoubin@ice-time.cn
@Brief :演武场副本随机事件逻辑
"""

from utils import logger
import base64
from datalib.data_loader import data_loader
from app.data.plunder import PlunderInfo
from app.data.plunder_record import PlunderRecordInfo
from app import log_formater


def reset_attack_num(data, plunder):
    """
    """
    #扣除元宝
    resource = data.resource.get()
    original_gold = resource.gold
    gold_cost = int(float(data_loader.OtherBasicInfo_dict["gold_for_reset_prey_attack_num"].value))
    if not resource.cost_gold(gold_cost):
        return False
    log = log_formater.output_gold(data, -gold_cost, log_formater.RESET_ATTACK_NUM,
                "Reset attak num by gold", before_gold = original_gold)
    logger.notice(log)

    plunder.reset_attack_num()
    return True


def get_plunder_enemy(data, plunder_user_id):
    """获取指定仇人的信息
    """
    enemy_list = data.plunder_record_list.get_all()
    for enemy in enemy_list:
        if enemy.rival_user_id == plunder_user_id:
            return enemy

    return None


def add_plunder_enemy(data, plunder_user_id, name, level, icon_id, country, score, 
        money = 0, food = 0):
    """添加仇人
    """
    #最多有六个仇人，超过就删除仇恨值最小的那个
    enemy_list = data.plunder_record_list.get_all()
    if len(enemy_list) == 6:
        tobe_deleted_enemy = enemy_list[0]
        for enemy in enemy_list:
            if enemy.hatred < tobe_deleted_enemy.hatred:
                tobe_deleted_enemy = enemy
        data.plunder_record_list.delete(tobe_deleted_enemy.id)

    hatred = int(float(data_loader.OtherBasicInfo_dict["hatred_value_by_one_attack"].value))
    been_attacked_num = 1
    plunder_record = PlunderRecordInfo.create(data.id, plunder_user_id)
    plunder_record.set_record(name, level, icon_id, country, hatred, been_attacked_num, score)
    plunder_record.add_today_robbed_resource(money, food)
    data.plunder_record_list.add(plunder_record)

    return


def update_plunder_enemy(data):
    """更新仇人信息（删除错误的信息）
    """
    enemy_list = data.plunder_record_list.get_all()
    tobe_deleted_enemy = []
    for enemy in enemy_list:
        if enemy.rival_user_id == 0:
            tobe_deleted_enemy.append(enemy.id)

    for deleted_id in tobe_deleted_enemy:
        data.plunder_record_list.delete(deleted_id)

    return


def modify_plunder_enemy_by_attack(enemy, money = 0, food = 0):
    """增加
    """
    hatred = int(float(data_loader.OtherBasicInfo_dict["hatred_value_by_one_attack"].value))
    enemy.modify_hatred(hatred)
    enemy.add_been_attacked_num()
    enemy.add_today_attack_resource(money, food)


def modify_plunder_enemy_by_robbed(enemy, money = 0, food = 0):
    """增加仇恨值
    """
    hatred = int(float(data_loader.OtherBasicInfo_dict["hatred_value_by_one_attack"].value))
    enemy.modify_hatred(hatred)
    enemy.add_today_robbed_resource(money, food)


def decay_all_plunder_enemy_daily(data):
    """仇人每日衰减
    """
    decay_hatred = int(float(data_loader.OtherBasicInfo_dict[
        "hatred_value_by_one_attack"].value)) / 2
    
    #删除仇恨值为0的
    enemy_list = data.plunder_record_list.get_all()
    tobe_deleted_enemy = []
    for enemy in enemy_list:
        enemy.modify_hatred(0 - decay_hatred)
        enemy.reset_daily()
        if enemy.hatred == 0:
            tobe_deleted_enemy.append(enemy.id)

    for id in tobe_deleted_enemy:
        data.plunder_record_list.delete(id)






