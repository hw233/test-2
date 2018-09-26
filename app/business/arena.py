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
from app.data.arena import ArenaInfo
from app.data.melee import MeleeInfo
from app.data.arena_record import ArenaRecordInfo
from app.business import map as map_business
from app.business import mail as mail_business
from app.business import item as item_business
from app.business import map as map_business
from app import log_formater


def arise_arena_event(data, node, now, **kwargs):
    """出现演武场事件
    1 敌人关键点出现该事件
    """
    change_nodes = kwargs['change_nodes']
    new_items = kwargs['new_items']
    new_mails = kwargs['new_mails']
    
    arena = data.arena.get()
    user = data.user.get(True)
    
    if not map_business.respawn_enemy_key_node(data, node, now):
        return False

    if not arena.open(node, user, now):
        return False

    #其他的pvp副本复用演武场事件,也需要开启
    melee = data.melee.get()
    if melee.is_able_to_open(user, now):
        if not melee.open(node, user, now):
            return False

    #倒推算出演出场事件应该arise的时间
    lifetime = data_loader.LuckyEventBasicInfo_dict[NodeInfo.EVENT_TYPE_ARENA].lifetime
    arena_arise_time = ArenaInfo.calc_event_arise_time(now, lifetime)

    return node.arise_event(NodeInfo.EVENT_TYPE_ARENA, arena_arise_time)


def clear_arena_event(data, node, now, **kwargs):
    """演武场事件消失
    """
    change_nodes = kwargs['change_nodes']
    new_items = kwargs['new_items']
    new_mails = kwargs['new_mails']

    map = data.map.get()
    user = data.user.get(True)

    if not node.clear_event():
        return False

    if not map_business.close_arena_key_node(data, node, now, now,
            change_nodes, new_items, new_mails):
        return False

    arena = data.arena.get()
    arena.close()

    #其他的pvp副本复用演武场事件,也需要close
    melee = data.melee.get()
    melee.close()
    
    return True


def start_arena_event(data, node, now):
    """启动演武场事件
    并不真正启动，只是检查事件是否处于合法状态
    """
    #节点上必须有合法的副本随机事件
    if node.event_type != NodeInfo.EVENT_TYPE_ARENA:
        logger.warning("Wrong event[type=%d]" % node.event_type)
        return False

    if node.is_event_over_idletime(now):
        logger.warning("Event over idletime[node basic id=%d]"
                "[event type=%d][arise time=%d]" %
                (node.basic_id, node.event_type, node.event_arise_time))
        return False
    return True




def refresh_arena(data, arena, now):
    """刷新竞技场对手
    """
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)

    #花费元宝
    gold_cost = arena.calc_gold_consume_of_refresh()
    if not resource.cost_gold(gold_cost):
        return False
    
    #刷新对手
    arena.refresh()
    
    if gold_cost > 0:
        log = log_formater.output_gold(data, -gold_cost, log_formater.REFRESH_ARENA,
                "Refresh arena by gold", before_gold = original_gold, rival_num = 3)
        logger.notice(log)

    return True


def get_arena_win_num_reward(data, arena, now):
    """领取奖励
    """
    chest = data_loader.ChestInfo_dict[arena.chest_basic_id]

    #可以领取奖励
    resource = data.resource.get()
    original_gold = resource.gold
    reward_gold = int(float(chest.reward.gold))
    resource.update_current_resource(now)
    resource.gain_money(int(float(chest.reward.money)))
    resource.gain_food(int(float(chest.reward.food)))
    resource.gain_gold(reward_gold)
    log = log_formater.output_gold(data, reward_gold, log_formater.ARENA_REWORD_GOLD,
                "Gain gold from arena", before_gold = original_gold)
    logger.notice(log)

    
    assert len(chest.reward.itemBasicIds) == len(chest.reward.itemNums)
    new_items = []
    for i in range(len(chest.reward.itemBasicIds)):
        basic_id = chest.reward.itemBasicIds[i]
        num = chest.reward.itemNums[i]
        new_items.append((basic_id, num))

    if not item_business.gain_item(data, new_items, "arena reward", log_formater.ARENA_REWARD):
        return False

    if not arena.get_win_num_reward():
        return False

    return True


def calc_arena_battle_finish(data, arena, is_win, rival):
    """玩家在演武场战斗之后结算
    """
    if is_win:
        status = ArenaRecordInfo.STATUS_ATTACK_WIN
        score_delta = rival.win_score
    else:
        status = ArenaRecordInfo.STATUS_ATTACK_LOSE
        score_delta = rival.lose_score
    
    arena.battle_finish(is_win, score_delta) 

    #新增演武场对战记录
    record = add_arena_record(data, rival.rival_id,
            rival.name, rival.level, rival.icon_id, status, score_delta)

    return record


MAX_RECORD_NUM = 20
def add_arena_record(data, player_id, name, level, icon_id, status, score_delta):
    """增加对战记录
    """
    record_list = data.arena_record_list.get_all()
    records_index = []
    for record in record_list:
        records_index.append(ArenaRecordInfo.get_index(record.id))
    
    if len(records_index) == 0:
        record = ArenaRecordInfo.create(1, data.id)
    else:
        min_record_index = min(records_index)
        max_record_index = max(records_index)

        #保留MAX_RECORD_NUM条记录，删除过久的
        if len(records_index) >= MAX_RECORD_NUM:
            data.arena_record_list.delete(ArenaRecordInfo.generate_id(data.id, min_record_index))

        record = ArenaRecordInfo.create(max_record_index + 1, data.id)

    record.set_record(player_id, name, level, icon_id, status, score_delta)
    data.arena_record_list.add(record)

    return record


def calc_arena_round_result(data, arena, mails, now):
    """结算当前轮次
    """
    #生成奖励邮件
    mail_time = arena.get_round_end_time()
    mail = mail_business.create_arena_reward_mail(data, mail_time)
    mails.append(mail)

    key = "%s_%s" % (arena.index, arena.title_level)
    
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
    
    #演武场段位奖励改发代币
    reward_coin = int(float(data_loader.GradeBasicInfo_dict[key].coinReward))
    mail.attach_arena_info(arena.title_level, reward_coin)
    arena.gain_coin(reward_coin)

    arena.clear()
    
    #更新轮次
    arena.update_round(now)
    logger.debug("Calc arena reward and update round[key=%s][reward_coin=%d]" % (key, reward_coin))


def calc_battle_score(arena, rival_score):
    """计算单场得分
    Args:
        arena(ArenaInfo): 己方竞技场信息
        rival_score(int):  对手积分
    """
    self_score = ArenaInfo.get_real_score(arena.score)
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
    key = "%s_%s" % (arena.index, arena.title_level)
    K1 = float(data_loader.GradeBasicInfo_dict[key].factorK1)

    #K2 连胜连败修正系数
    max_num = max(data_loader.ArenaContinuousWinRepairFactor_dict.keys())
    min_num = min(data_loader.ArenaContinuousWinRepairFactor_dict.keys())
    #胜
    if arena.continuous_win_num >= 0:
        num_win = min(max_num, arena.continuous_win_num + 1)
    else:
        num_win = min(max_num, 1)
    #负
    if arena.continuous_win_num < 0:
        num_lose = max(min_num, arena.continuous_win_num - 1)
    else:
        num_lose = max(min_num, -1)
    
    continuous_factor = data_loader.ArenaContinuousWinRepairFactor_dict[num_win]
    K2_win = float(continuous_factor.factor)
    continuous_factor = data_loader.ArenaContinuousWinRepairFactor_dict[num_lose]
    K2_lose = float(continuous_factor.factor)

    #K3 场次修正系数
    max_num = max(data_loader.ArenaNumRepairFactor_dict.keys())
    num = min(max_num, arena.total_num)
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

    logger.debug("Calc arena battle score[D=%d][P=%f][K1=%d][K2_win=%d][K2_lose=%d][K3=%d][win_score=%d][lose_score=%d]" %
            (D, P, K1, K2_win, K2_lose, K3, win_score, lose_score))

    #打胜最低也能得30分，避免出现0积分的情况
    return (max(35, int(win_score)), int(lose_score))


def update_arena_title_level(data, arena, rank, mails, now):
    """更新竞技场段位
    """
    title_level = arena.calc_arena_title_level(rank)
    if arena.update_title_level(title_level):
        #升段位
        #生成升段位奖励邮件
        mail = mail_business.create_arena_upgrade_reward_mail(data, now)
        mails.append(mail)
        
        key = "%s_%s" % (arena.index, arena.title_level)
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
        mail.attach_arena_info(arena.title_level, 0)

    return True


def update_arena_offline(data, user, arena):
    """离线更新演武场信息
    """
    ##积分衰减
    #score = ArenaInfo.get_real_score(arena.score)
    #decay = float(data_loader.OtherBasicInfo_dict["ArenaScoreDecay"].value)
    #new_score = int(score * decay)
    #score_diff = new_score - score
    #arena.add_score(score_diff)
    
    #积分清零
    #score = ArenaInfo.get_real_score(arena.score)
    #score_diff = 0 - score
    #arena.add_score(score_diff)

    #积分衰减（退一档，低于等于1600就不再衰减）
    decay_score = arena.calc_decay_score()
    score_diff = decay_score - ArenaInfo.get_real_score(arena.score)
    arena.add_score(score_diff)
    
    #清除对战记录
    record_id = []
    for record in data.arena_record_list.get_all(True):
        record_id.append(record.id)
    for id in record_id:
        data.arena_record_list.delete(id)

    #根据主公等级重新分配房间
    arena.update_index(user.level)

    #重置演武场最高段位
    arena.reset_highest_title_level()

    #乱斗场清理
    #积分清零
    melee = data.melee.get()
    decay_score = melee.calc_decay_score()
    score_diff = decay_score - MeleeInfo.get_real_score(melee.score)
    melee.add_score(score_diff)
    
    #清除对战记录
    record_id = []
    for record in data.melee_record_list.get_all(True):
        record_id.append(record.id)
    for id in record_id:
        data.melee_record_list.delete(id)

    #根据主公等级重新分配房间
    melee.update_index(user.level)

    #重置演武场最高段位
    melee.reset_highest_title_level()

    return True


def is_need_broadcast_win_num(arena):
    """演武场发广播
    """
    broadcast_continuous_win_num = int(float(data_loader.OtherBasicInfo_dict["arena_win_num_broadcast"].value))

    if (arena.continuous_win_num > 0 and
        arena.continuous_win_num % broadcast_continuous_win_num == 0):
        return True
    else:
        return False


def create_broadcast_content_win_num(user, arena):
    """
    """
    broadcast_id = int(float(data_loader.OtherBasicInfo_dict["broadcast_id_arena_win_num"].value))
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(user.name), 1)
    content = content.replace("#str#", str(arena.continuous_win_num), 1)

    return (mode_id, priority, life_time, content)



BROADCAST_TITLE_LEVELS = []
for i in range(15, 60):
    BROADCAST_TITLE_LEVELS.append(i)

def is_need_broadcast_title(old_title_level, arena):
    """演武场发广播
    """
    if arena.title_level in BROADCAST_TITLE_LEVELS and old_title_level < arena.title_level:
        return True
    else:
        return False


def create_broadcast_content_title(user, arena):
    """
    """
    base = int(float(data_loader.OtherBasicInfo_dict["broadcast_id_arena_title_base"].value))

    broadcast_id = base + arena.title_level
    mode_id = data_loader.BroadcastTemplate_dict[broadcast_id].modeId
    life_time = data_loader.BroadcastTemplate_dict[broadcast_id].lifeTime
    template = data_loader.BroadcastTemplate_dict[broadcast_id].template.encode("utf-8")
    priority = data_loader.BroadcastBasicInfo_dict[mode_id].priority

    content = template.replace("#str#", base64.b64decode(user.name), 1)

    return (mode_id, priority, life_time, content)


def start_battle(data, arena, now):
    """开始战斗"""
    user = data.user.get(True)
    if not arena.is_able_to_open(user, now):
        logger.warning("arena is not open[user_id=%d]" % data.id)
        #return -1

    node_basic_id = arena.get_node_basic_id()
    node_id = NodeInfo.generate_id(data.id, node_basic_id)
    node = data.node_list.get(node_id)
    if node is None:
        node = NodeInfo.create(data.id, node_basic_id)
        data.node_list.add(node)
    
    node.set_arena()

    return node_id
