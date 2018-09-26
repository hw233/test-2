#coding:utf8
"""
Created on 2016-03-01
@Author: zhoubin@ice-time.cn
@Brief :演武场副本随机事件逻辑
"""

from utils import logger
import base64
from datalib.data_loader import data_loader
from app.data.map import MapGraph
from app.data.node import NodeInfo
from app.data.melee import MeleeInfo
from app.data.melee_record import MeleeRecordInfo
from app.business import map as map_business
from app.business import mail as mail_business
from app.business import item as item_business
from app.business import map as map_business
from app.business import hero as hero_business
from app import log_formater


def refresh_melee(data, melee, now):
    """刷新竞技场对手
    """
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)

    #花费元宝
    gold_cost = melee.calc_gold_consume_of_refresh()
    if not resource.cost_gold(gold_cost):
        return False
    
    #刷新对手
    melee.refresh()
    
    if gold_cost > 0:
        log = log_formater.output_gold(data, -gold_cost, log_formater.REFRESH_MELEE,
                "Refresh melee by gold", before_gold = original_gold, rival_num = 3)
        logger.notice(log)

    return True


def get_melee_win_num_reward(data, melee, now):
    """领取奖励
    """
    chest = data_loader.ChestInfo_dict[melee.chest_basic_id]

    #可以领取奖励
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    reward_gold = int(float(chest.reward.gold))
    resource.gain_money(int(float(chest.reward.money)))
    resource.gain_food(int(float(chest.reward.food)))
    resource.gain_gold(reward_gold)
    log = log_formater.output_gold(data, reward_gold, log_formater.CHEST_REWARD_GOLD,
                "Gain gold from chest melee", before_gold = original_gold)
    logger.notice(log)    

    assert len(chest.reward.itemBasicIds) == len(chest.reward.itemNums)
    new_items = []
    for i in range(len(chest.reward.itemBasicIds)):
        basic_id = chest.reward.itemBasicIds[i]
        num = chest.reward.itemNums[i]
        new_items.append((basic_id, num))

    if not item_business.gain_item(data, new_items, "melee win reward", log_formater.MELEE_WIN_REWARD):
        return False

    if not melee.get_win_num_reward():
        return False

    return True


def calc_melee_battle_finish(data, melee, is_win, rival):
    """玩家在演武场战斗之后结算
    """
    if is_win:
        status = MeleeRecordInfo.STATUS_ATTACK_WIN
        score_delta = rival.win_score
    else:
        status = MeleeRecordInfo.STATUS_ATTACK_LOSE
        score_delta = rival.lose_score
    
    melee.battle_finish(is_win, score_delta) 

    #新增演武场对战记录
    record = add_melee_record(data, rival.rival_id,
            rival.name, rival.level, rival.icon_id, status, score_delta)

    return record


MAX_RECORD_NUM = 20
def add_melee_record(data, player_id, name, level, icon_id, status, score_delta):
    """增加对战记录
    """
    record_list = data.melee_record_list.get_all()
    records_index = []
    for record in record_list:
        records_index.append(MeleeRecordInfo.get_index(record.id))
    
    if len(records_index) == 0:
        record = MeleeRecordInfo.create(1, data.id)
    else:
        min_record_index = min(records_index)
        max_record_index = max(records_index)

        #保留MAX_RECORD_NUM条记录，删除过久的
        if len(records_index) >= MAX_RECORD_NUM:
            data.melee_record_list.delete(MeleeRecordInfo.generate_id(data.id, min_record_index))

        record = MeleeRecordInfo.create(max_record_index + 1, data.id)

    record.set_record(player_id, name, level, icon_id, status, score_delta)
    data.melee_record_list.add(record)

    return record


def calc_melee_round_result(data, melee, mails, now):
    """结算当前轮次
    """
    #生成奖励邮件
    mail_time = melee.get_round_end_time()
    mail = mail_business.create_melee_reward_mail(data, mail_time)
    mails.append(mail)

    key = "%s_%s" % (melee.index, melee.title_level)
    
    reward = data_loader.GradeBasicInfo_dict[key].finalReward
    reward_money = int(float(reward.money))
    reward_food = int(float(reward.food))
    reward_gold = int(float(reward.gold))

    assert len(reward.itemBasicIds) == len(reward.itemNums)
    reward_item_list = []
    for i in range(len(reward.itemBasicIds)):
        basic_id = int(float(reward.itemBasicIds[i]))
        num = int(float(reward.itemNums[i]))
        reward_item_list.append((basic_id, num))
    
    mail.attach_reward(reward_money, reward_food, reward_gold, reward_item_list)
    #乱斗演武场段位奖励改发代币
    reward_coin = int(float(data_loader.GradeBasicInfo_dict[key].coinReward))
    mail.attach_arena_info(melee.title_level, reward_coin)
   
    #演武币统一存在arena结构里
    arena = data.arena.get()
    arena.gain_coin(reward_coin)

    melee.clear()
    
    #更新轮次
    melee.update_round(now)
    logger.debug("Calc melee reward and update round[key=%s]" % key)


def calc_battle_score(melee, rival_score):
    """计算单场得分
    Args:
        melee(meleeInfo): 己方竞技场信息
        rival_score(int):  对手积分
    """
    self_score = MeleeInfo.get_real_score(melee.score)
    D = abs(self_score - rival_score)
    #P
    for i in data_loader.ELOBasicInfo_dict:
        elo = data_loader.ELOBasicInfo_dict[i]
        if D >= elo.lowerLimitScore and D <= elo.upperLimitScore:
            if self_score >= rival_score:
                P = float(elo.expectationA)
            else:
                P = float(elo.expectationB)
            break
    #K1 得分系数与段位相关
    key = "%s_%s" % (melee.index, melee.title_level)
    K1 = float(data_loader.GradeBasicInfo_dict[key].factorK1)

    #K2 连胜连败修正系数
    max_num = max(data_loader.ArenaContinuousWinRepairFactor_dict.keys())
    min_num = min(data_loader.ArenaContinuousWinRepairFactor_dict.keys())
    #胜
    if melee.continuous_win_num >= 0:
        num_win = min(max_num, melee.continuous_win_num + 1)
    else:
        num_win = min(max_num, 1)
    #负
    if melee.continuous_win_num < 0:
        num_lose = max(min_num, melee.continuous_win_num - 1)
    else:
        num_lose = max(min_num, -1)
    
    continuous_factor = data_loader.ArenaContinuousWinRepairFactor_dict[num_win]
    K2_win = float(continuous_factor.factor)
    continuous_factor = data_loader.ArenaContinuousWinRepairFactor_dict[num_lose]
    K2_lose = float(continuous_factor.factor)

    #K3 场次修正系数
    max_num = max(data_loader.ArenaNumRepairFactor_dict.keys())
    num = min(max_num, melee.total_num)
    num_factor = data_loader.ArenaNumRepairFactor_dict[num]
    if num_factor is None:
        max_num = 0
        for i in data_loader.ArenaNumRepairFactor_dict:
            num = data_loader.ArenaNumRepairFactor_dict[i].num
            if max_num < num:
                max_num = num
        num_factor = data_loader.ArenaNumRepairFactor_dict[max_num]
    K3 = float(num_factor.factor)
    
    R = 1
    win_score = K1 * K2_win * K3 * (R - P)
    R = 0
    lose_score = K1 * K2_lose * K3 * (R - P)

    logger.debug("Calc melee battle score[D=%d][P=%f][K1=%d][K2_win=%d][K2_lose=%d][K3=%d][win_score=%d][lose_score=%d]" %
            (D, P, K1, K2_win, K2_lose, K3, win_score, lose_score))

    #打胜最低也能得30分，避免出现0积分的情况
    return (max(35, int(win_score)), int(lose_score))


def update_melee_title_level(data, melee, rank, mails, now):
    """更新竞技场段位
    """
    title_level = melee.calc_arena_title_level(rank)
    if melee.update_title_level(title_level):
        #升段位
        #生成升段位奖励邮件
        mail = mail_business.create_melee_upgrade_reward_mail(data, now)
        mails.append(mail)
        
        key = "%s_%s" % (melee.index, melee.title_level)
        reward = data_loader.GradeBasicInfo_dict[key].upgradeReward
        
        reward_money = int(float(reward.money))
        reward_food = int(float(reward.food))
        reward_gold = int(float(reward.gold))
        assert len(reward.itemBasicIds) == len(reward.itemNums)
        reward_item_list = []
        for i in range(len(reward.itemBasicIds)):
            basic_id = int(float(reward.itemBasicIds[i]))
            num = int(float(reward.itemNums[i]))
            reward_item_list.append((basic_id, num))

        mail.attach_reward(reward_money, reward_food, reward_gold, reward_item_list)
        mail.attach_arena_info(melee.title_level, 0)

    return True


def is_need_broadcast_win_num(melee):
    """演武场发广播
    """
    broadcast_continuous_win_num = int(float(data_loader.OtherBasicInfo_dict["arena_win_num_broadcast"].value))

    if (melee.continuous_win_num > 0 and
        melee.continuous_win_num % broadcast_continuous_win_num == 0):
        return True
    else:
        return False


def create_broadcast_content_win_num(user, melee):
    """
    """
    broadcast_id = int(float(data_loader.OtherBasicInfo_dict["broadcast_id_melee_win_num"].value))
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(user.name), 1)
    content = content.replace("#str#", str(melee.continuous_win_num), 1)

    return (mode_id, priority, life_time, content)



BROADCAST_TITLE_LEVELS = []
for i in range(15, 60):
    BROADCAST_TITLE_LEVELS.append(i)

def is_need_broadcast_title(old_title_level, melee):
    """演武场发广播
    """
    if melee.title_level in BROADCAST_TITLE_LEVELS and old_title_level < melee.title_level:
        return True
    else:
        return False


def create_broadcast_content_title(user, melee):
    """
    """
    base = int(float(data_loader.OtherBasicInfo_dict["broadcast_id_melee_title_base"].value))

    broadcast_id = base + melee.title_level
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(user.name), 1)

    return (mode_id, priority, life_time, content)


def start_battle(data, melee, now):
    """开始战斗"""
    user = data.user.get(True)
    if not melee.is_able_to_open(user, now):
        logger.warning("melee is not open[user_id=%d]" % data.id)
        #return -1

    node_basic_id = melee.get_node_basic_id()
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    node = data.node_list.get(node_id)
    if node is None:
        node = NodeInfo.create(data.id, node_basic_id)
        data.node_list.add(node)

    node.set_melee()

    return node_id
