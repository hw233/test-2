#coding:utf8
"""
Created on 2016-05-04
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 日志按格式输出，方便分析
"""

import time
from utils import utils
from app.data.node import NodeInfo

def output(data, str, req, res, consume):
    """
    """
    user_id = data.id
    user = data.user.get(True)
    guard_list = data.guard_list.get_all(True)
    if len(guard_list) == 0:
        guard_score = 0
    else:
        guard_score = guard_list[0].score
    battle_score = data.battle_score.get(True).score

    log = ("%s[user_id=%d][level=%d][guard_score=%d][score=%d][req=%s][res=%s][consume=%d]"
            % (str, user_id, user.level, guard_score, battle_score, req, res, consume))
    return log


def output_battle(data, node_id, rival, str, req, res, consume):
    """
    battle_type: 10 pve钱     11 pve粮     12 pve矿
                 20 dungeon1  21 dungeon2  22 dungeon3  23 dungeon4  24 dungeon5  25 dungeon6
                 30 arena
                 40 pvp钱     41 pvp粮     42 pvp矿     43 pvp主城   44 pvp复仇
                 50 pve山贼叛军
                 60 史实城
    """
    user_id = data.id
    user = data.user.get(True)
    guard_list = data.guard_list.get_all(True)
    if len(guard_list) == 0:
        guard_score = 0
    else:
        guard_score = guard_list[0].score
    battle_score = data.battle_score.get(True).score

    node = data.node_list.get(node_id)
    battle = data.battle_list.get(node_id)
    battle_type = 0
    if node is None:
        #复仇
        battle_type = 44
    else:
        if node.is_dependency():
            #山贼
            battle_type = 50
        else:
            if rival.type == NodeInfo.ENEMY_TYPE_DUNGEON:
                #地下城
                dungeon = data.dungeon.get()
                if dungeon.level == 1:
                    battle_type = 20
                elif dungeon.level == 2:
                    battle_type = 21
                elif dungeon.level == 3:
                    battle_type = 22
                elif dungeon.level == 4:
                    battle_type = 23
                elif dungeon.level == 5:
                    battle_type = 24
                elif dungeon.level == 6:
                    battle_type = 25

            elif rival.type == NodeInfo.ENEMY_TYPE_ARENA:
                #演武场
                battle_type = 50
            
            elif rival.type == NodeInfo.ENEMY_TYPE_LEGENDCITY:
                #史实城
                battle_type = 60

            elif rival.type == NodeInfo.ENEMY_TYPE_PVE_RESOURCE:
                #资源点
                if node.is_exploit_money():
                    battle_type = 10
                if node.is_exploit_food():
                    battle_type = 11
                if node.is_exploit_material():
                    battle_type = 12

            elif (rival.type == NodeInfo.ENEMY_TYPE_PVP_CITY
                    or rival.type == NodeInfo.ENEMY_TYPE_PVP_RESOURCE):
                if node.is_rival_pvp_city():
                    #主城
                    battle_type = 43
                else:
                    if node.is_exploit_money():
                        battle_type = 40
                    if node.is_exploit_food():
                        battle_type = 41
                    if node.is_exploit_material():
                        battle_type = 42

    log = ("%s[user_id=%d][level=%d][guard_score=%d][score=%d][battle_type=%d][rival_level=%d][rival_score=%d][req=%s][res=%s][consume=%d]"
            % (str, user_id, user.level, guard_score, battle_score, battle_type, rival.level, rival.score, req, res, consume))

    return log
    


EXCHANGE_MONEY_FOOD = 1        #兑换钱粮
EXCHANGE_SOLDIER = 2           #兑换兵开打
DRAW_ONE = 3                   #元宝抽一次
DRAW_MULTI = 4                 #元宝十连抽
BUY_FUNDS = 5                  #购买成长基金
REFRESH_ARENA = 6              #刷新演武场对手
EXCHANGE_ENCHANT_VALUE = 7     #兑换精炼值
UPGRADE_EQUIPMENT = 8          #用元宝进阶装备
UPGRADE_KEYNODE = 9            #用元宝升级节点
PROTECT = 10                   #用元宝买保护盾
REFRESH_WINESHOP_GOODS = 11    #元宝刷新商铺货物
BUY_GOODS = 12                 #购买商铺的元宝物品
VISIT = 13                     #用元宝进行探访
FINISH_CONSCRIPT = 14          #立即完成征兵
FINISH_BUILDING = 15           #立即完成建造
FINISH_TECHNOLOGY = 16         #立即完成研究
INCREASE = 17                  #用元宝买增产
BUY_ENERGY = 18                #用元宝买政令
REFRESH_PRAY = 19              #用元宝刷新祈福
CHOOSE_CARD = 20               #用元宝兑换祈福令去翻牌子
BUY_ATTACK_NUM = 21            #用元宝买攻击次数
#todo
LEGENDCITY_START_BATTLE = 22   #花费元宝进行史实城战斗（造反太守）
LEGENDCITY_REMATCH = 23        #花费元宝重新匹配对手
LEGENDCITY_UPDATE = 24         #花费元宝修改宣言和税（只有第一次免费）
LEGENDCITY_RESET = 25          #花费元宝重置攻击次数
LEGENDCITY_BUY_BUFF = 26       #花费元宝购买buff
ACTIVITY_BUY = 27              #花费元宝购买活动内的商品

REFRESH_MELEE = 28             #刷新乱斗场场对手
OPERATE_ACTIVITY_DISCOUNT = 29 #购买优惠商品
OPERATE_ACTIVITY_SHOP = 30     #购买商品
RESET_HARD_ATTACK = 31         #重置困难模式攻击次数
RESET_DUNGENON_ATTACK = 32     #重置副本攻击次数
RESOLVE_HERO = 33	           #分解武将
DUMOUT_EQUIP_STONE = 34	       #装备卸下宝石
RESET_ATTACK_NUM = 35          #重置攻击次数
TRANSFER_ARENA = 36	           #买换位演武场攻击次数
RESET_CD = 37		           #重置cd
DRUM = 38		               #擂鼓消耗的元宝
REFRESH_ATTACK = 39	           #刷新攻击次数
CREATE_UNION = 40 	           #创建联盟
CONSUME_RESOURCES = 41 	       #根据捐献等级消耗资源
CLEAR_COLDTIME = 42	           #清空冷却时间
UNIONBOSS_RESET = 43           #联盟boss 重置
UNIONUPDATE = 44 	           #联盟更新
UPDATE_USER_NAME = 45          #用元宝更改用户名
BUILDING_TIME = 46 	           #减少建筑时间
LEGENDCITY_LEADER = 47 	       #直接挑战太守
FORTUNE_CAT = 48               #招财猫 
TURN_DRAW = 49                 #转盘夺宝 
#获得的元宝
ACCEPT_REWARD_GOLD = 50        #活动奖励的元宝
ARENA_REWORD_GOLD = 51         #演武场获得的元宝
CHEST_REWARD_GOLD = 52         #红包奖励的元宝
EXPLOIT_GOLD = 53	           #开采获得的元宝
RESOURCE_ITEM_GOLD = 54        #使用元宝袋
ITEM_GOLD = 55		           #使用物品
MAIL_REWARD_GOLD = 56	       #邮件获得的元宝
MISSION_REWARD_GOLD = 57       #完成任务的奖励
INDIVIDUAL_STEP_GOLD = 58      #个人战功奖励
AWARD_GOLD = 59		           #发放的奖励
DONATE_REWARD_GOLD = 60	       #捐献的奖励
RESPOND_AID_REWARD = 61	       #响应援助奖励
INIT_RESOURCE_GOLD = 62        #初始化gold
CHECK_UPDATE_COUNTRY = 63      #选择默认城市给奖励
OPERATE_GOLD = 64	           #强制添加或减少
BAG_GOLD = 65		           #cd-key
PAY_GOLD = 66                  #充值


def output_gold(data, gold_num, use_type, str, money = 0, food = 0, before_gold = 0, soldier = 0, 
        items_id = [], items_num = [], heroes_id = [], rival_num = 0,
        activity = 0, enchant = 0, achievement = 0, reduce_time = 0, protect_hour = 0,
        increase_hour = 0, energy = 0, pray_type = 0, choose_index = 0, attack_num = 0):
    """
    """
    after_gold =  data.resource.get(True).gold
    user_id = data.id
    user = data.user.get(True)
    guard_list = data.guard_list.get_all(True)
    if len(guard_list) == 0:
        guard_score = 0
    else:
        guard_score = guard_list[0].score
    battle_score = data.battle_score.get(True).score

    if use_type == EXCHANGE_MONEY_FOOD:
        gain = "%d,%d" % (money, food)
    elif use_type == EXCHANGE_SOLDIER:
        gain = "%d" % soldier
    elif use_type == DRAW_ONE or use_type == DRAW_MULTI:
        gain = "%s,%s,%s" % (utils.join_to_string(items_id),
                utils.join_to_string(items_num),
                utils.join_to_string(heroes_id))
    elif use_type == BUY_FUNDS:
        gain = "%d" % activity
    elif use_type == REFRESH_ARENA:
        gain = "%d" % rival_num
    elif use_type == EXCHANGE_ENCHANT_VALUE:
        gain = "%d,%d" % (money, enchant)
    elif use_type == UPGRADE_EQUIPMENT:
        gain = "%d" % money
    elif use_type == UPGRADE_KEYNODE:
        gain = "%d,%d" % (money, food)
    elif use_type == PROTECT:
        gain = "%d" % protect_hour
    elif use_type == REFRESH_WINESHOP_GOODS:
        gain = "%s,%s" % (utils.join_to_string(items_id), utils.join_to_string(items_num))
    elif use_type == BUY_GOODS:
        gain = "%s,%s" % (utils.join_to_string(items_id), utils.join_to_string(items_num))
    elif use_type == VISIT:
        gain = "%d,%d,%s,%s,%s" % (money, achievement,
                utils.join_to_string(items_id),
                utils.join_to_string(items_num),
                utils.join_to_string(heroes_id))
    elif use_type == FINISH_CONSCRIPT or use_type == FINISH_BUILDING or use_type == FINISH_TECHNOLOGY:
        gain = "%d" % reduce_time
    elif use_type == INCREASE:
        gain = "%d" % increase_hour
    elif use_type == BUY_ENERGY:
        gain = "%d" % energy
    elif use_type == REFRESH_PRAY:
        gain = "%d" % pray_type
    elif use_type == CHOOSE_CARD:
        gain = "%d" % choose_index
    elif use_type == BUY_ATTACK_NUM:
        gain = "%d" % attack_num
    elif use_type == PAY_GOLD:
        gain = "%d" % gold_num
    else:
        gain = "none"


    log = ("GOLD_CHANGE[str=%s][user_id=%d][level=%d][guard_score=%d][score=%d][change_gold=%d][after_gold=%d][use_type=%d][gain=%s]"
            % (str, user_id, user.level, guard_score, battle_score, gold_num, after_gold, use_type, gain))

    return log


def output2(user_id, str, req, res, consume):
    """部分逻辑不需要拿到用户所有数据，没有data
    """
    log = ("%s[user_id=%d][req=%s][res=%s][consume=%d]"
            % (str, user_id, req, res, consume))
    return log

#消耗的物品
COMPOSE_CONSUME = 200		#合成消耗物品
CASTING_CONSUME = 201		#熔铸消耗物品
SELL = 202			        #卖出物品
LEGENDCITY_BUF = 203		#使用史实诚buff
EXP_ITEM = 204			    #使用经验丹
MONARCH_EXP_ITEM = 205		#主攻经验丹
SPEED_ITEM = 206 		    #使用加速物品
APPOINT_ITEM = 207		    #使用委任物品
ANNEAL_ITEM = 208		    #使用试炼场攻击次数购买符
STONE_ITEM = 209		    #使用装备的宝石
HEROLIST_ITEM = 210		    #用国士名册 
MONTHCARD_ITEM = 211		#使用vip物品
PACKAGE_ITEM = 212		    #使用物品
VIP_ITEM = 213			    #使用vip物品
ENERGY_ITEM = 214		    #使用政令符物品
SOUL_ITEM = 215			    #使用精魄包物品
GOLD_ITEM = 216 		    #用元宝袋物品
FOOD_ITEM = 217			    #"使用粮包物品 
MONEY_ITEM = 218		    #使用钱包物品
EVOLUTION_ITEM = 219		#使用突破石物品
RESOLVE_STARSOUL_ITEM = 220	#分解将魂石,返还精魄
STARSOUL_ITEM = 221		    #使用将魂石物品 
REFRESH_ITEM = 222		    #使用商铺刷新代币 
DRAW_ITEM = 223			    #用搜索券
INCREASE_ITEM = 224		    #资源点增产
EQUIPT = 225			    #装备进阶
REFINE = 226			    #英雄洗髓
AWAKEN_HERO = 227		    #觉醒英雄
SKILL_ITEM = 228 		    #技能书
ENCHANT = 229 			    #装备精炼
STRENGTH_HEROSTAR = 230		#升级将星
CHOOSE_CARD = 231		    #翻牌
PROTECT = 232 			    #城市保护
DRUM = 233			        #擂鼓
RESPOND_AID = 234		    #联盟响应援助
#获得的物品
SCORE_REWARD = 300		    #战功奖励
BOsS_REWARD = 301		    #boss奖励
CDKEY_REWARD = 302		    #cdkey奖励
DRAW = 303			        #抽奖
WIN_REWARD = 304		    #获胜奖励
HEROLIST_REWARD = 305		#国士名册奖励
SIGNIN_REWARD = 306		    #签到奖励
NODE_REWARD = 307		    #node 宝箱奖励
ACTIVITY_REWARD = 308 		#活动奖励
PASS_REWARD = 309		    #过关奖励
SWEEP_REWARD = 310		    #演武场扫荡奖励
NEW_SWEEP_REWARD = 311		#新演武场奖励
ARENA_REWARD = 312		    #演武场副本奖励
WIN_BATTLE = 313		    #战斗胜利奖励
CHEST_REWARD = 314		    #红包奖励
GATHER = 315			    #开采资源采集
EXPLOIT_REWARD = 316 		#开采结束的奖励
HERO_SPLIT = 317 		    #重复武将分解成将魂石
RETURN_MATERIAL = 318 		#进阶返还的材料
DEMOUNT_STONE = 319		    #卸下宝石
RESOLVE_HERO = 320 		    #分解武将
REBORN_HERO = 321		    #重生武将
MAIL_REWARD = 322 		    #邮件获取的奖励
MELEE_WIN_REWARD = 323		#演武场获胜奖励
MISSION_REWARD = 324		#任务奖励
PAY_REWARD = 325		    #支付奖励的物品
CHOOSE_CARD = 326		    #翻牌
QUESTION_REWARD = 327 		#问答奖励
SHOP = 328			        #商店购买
WIN_BATTLE = 329 		    #战斗胜利
INDIVIDUAL_AWARD = 330 		#个人战功阶段奖励
AWARD = 331 			    #发放的奖励
DONATE_REWARD = 332		    #联盟捐献奖励
FINISH_AID = 333		    #结束援助
UNION_BATTLE = 334		    #联盟站奖励大宝箱
RESOURCE = 335			    #使用资源包获取物品
COMPOSE_GAIN = 336 		    #合成获得的物品
CASTING_GAIN = 337 		    #熔铸获得的物品
def output_item(data, str, item_type, item):
    log = ("ITEM_CHANGE[str=%s][use_type=%d]%s"%(str, item_type, item))
    return log




EXP_WIN_BATTLE = 400	#战斗胜利经验
EXP_BUILDING = 401		#完成建造经验
EXP_EVENT = 402 		#事件奖励经验
EXP_MONARCH = 403		#主公经验丹
EXP_MISSION = 404		#任务经验
EXP_AID = 405			#援助经验
def output_exp(data, str, exp_type, exp_change, level, exp):
    log = ("EXP_CHANGE[str=%s][exp_type=%d][exp_change=%d][level=%d][exp=%d]"%(str, exp_type, exp_change, level, exp))
    return log
