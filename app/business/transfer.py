#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场
"""

from datalib.data_loader import data_loader
from app.data.transfer_record import TransferRecordInfo
from app.business import item as item_business
from utils import logger
from utils.ret import Ret
from app import log_formater

def update_transfer(data, match):
    transfer = data.transfer.get()
    match_ids = [m.user_id for m in match]
    is_robots = [int(m.is_robot) for m in match]
    transfer.set_match_ids(match_ids)
    transfer.set_is_robots(is_robots)

def buy_attack_times(data, now, ret = Ret()):
    gold = int(float(data_loader.OtherBasicInfo_dict['transfer_arena_challenge_buy_cost'].value))
    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold
    if not resource.cost_gold(gold):
        ret.setup("NO_ENOUGH_GOLD")
        return False
    log = log_formater.output_gold(data, -gold, log_formater.TRANSFER_ARENA,
                "Transfer arena challenge", before_gold = original_gold)
    logger.notice(log)

    transfer = data.transfer.get(True)
    if not transfer.reduce_attack_num(1, ret):
        return False

    return True

def reset_cd(data, now, ret = Ret()):
    gold = int(float(data_loader.OtherBasicInfo_dict['transfer_arena_reset_cd_cost'].value))
    resource = data.resource.get()
    resource.update_current_resource(now)
    original_gold = resource.gold
    if not resource.cost_gold(gold):
        ret.setup("NO_ENOUGH_GOLD")
        return False
    log = log_formater.output_gold(data, -gold, log_formater.RESET_CD,
                "Reset cd by gold", before_gold = original_gold)
    logger.notice(log)

    transfer = data.transfer.get(True)
    transfer.reset_cd(now)

    return True

def start_battle(data, target_id, now, ret = Ret()):
    """开始战斗"""
    #1.检查是否满足开战条件: 攻击次数, CD时间
    #2.增加攻击次数, 设置CD时间

    transfer = data.transfer.get()
    if not transfer.is_able_to_start_battle(target_id, now, ret):
        return False

    transfer.start_battle(now)
    return True


def add_battle_record(data, target_user_id, target_user_name, target_level, target_icon,
    status, self_rank, rival_rank):
    """添加对战记录"""
    transfer = data.transfer.get()
    record = TransferRecordInfo.create(
        data.id,
        transfer.generate_record_index(),
        target_user_id,
        target_user_name,
        target_level,
        target_icon,
        status,
        self_rank,
        rival_rank
    )

    MAX_RECORD_NUM = 20 #最大对战记录数量

    transfer_records = data.transfer_record_list.get_all(True)
    if len(transfer_records) > MAX_RECORD_NUM:
        delete_record = None
        for transfer_record in transfer_records:
            if delete_record == None:
                delete_record = transfer_record
                continue

            if record.index < delete_record:
                delete_record = transfer_record

        assert delete_record != None
        data.transfer_record_list.delete(delete_record.id)

    data.transfer_record_list.add(record)

def rank_reward(ranking):
    """排名奖励"""
    for key in data_loader.TransferRewardBasicInfo_dict:
        upper_rank, lower_rank = [int(r) for r in key.split("_")]
        if upper_rank <= ranking <= lower_rank:
            gold = data_loader.TransferRewardBasicInfo_dict[key].gold
            items_id = data_loader.TransferRewardBasicInfo_dict[key].itemBasicIds
            items_num = data_loader.TransferRewardBasicInfo_dict[key].itemNums

            return (gold, items_id, items_num)

    return (None, None, None)
