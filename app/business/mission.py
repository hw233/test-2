#coding:utf8
"""
Created on 2015-09-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief:  任务相关业务逻辑
"""

from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from utils.timer import Timer
from app.data.item import ItemInfo
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy
from app.data.mission import MissionInfo
from app.business import user as user_business
from app.business import item as item_business
from app.business import conscript as conscript_business
from app import log_formater

MISSION_TYPE_DAILY = 1
MISSION_TYPE_GROW = 2
MISSION_TYPE_ACHIEVEMENT = 3
MISSION_TYPE_ACTIVITY = 4
MISSION_TYPE_VITALITY = 5
#11~17是开服七天任务

MISSION_SEARCH = "MissionSearch"
MISSION_RESOURCE_GAIN = "MissionResourceGain"
MISSION_RESOURCE_CONSUME = "MissionResourceConsume"
MISSION_CONSCRIPT_NUM = "MissionConscriptNum"
MISSION_CONSCRIPT_SOLDIER_NUM = "MissionConscriptSoldierNum"
MISSION_DEAD_SOLDIER_NUM = "MissionDeadSoldierNum"
MISSION_EQUIPMENT_UPGRADE_NUM = "MissionEquipmentUpgradeNum"
MISSION_EQUIPMENT_ENCHANT_NUM = "MissionEquipmentEnchantNum"
MISSION_ADD_SKILL_POINT = "MissionAddSkillPoint"
MISSION_DAILY_LOGIN = "MissionDailyLogin"
MISSION_MONARCH_LEVEL = "MissionMonarchLevel"
MISSION_BUILDING_UPGRADE = "MissionBuildingUpgrade"
MISSION_SOLDIER_UPGRADE = "MissionSoldierUpgrade"
MISSION_SOLDIER_UPGRADE_NUM = "MissionSoldierUpgradeNum"
MISSION_TECH_UPGRADE = "MissionTechUpgrade"
MISSION_TECH_UPGRADE_NUM = "MissionTechUpgradeNum"
MISSION_EQUIPMENT = "MissionEquipment"
MISSION_HERO = "MissionHero"
MISSION_WIN_ENEMY_BATTLESCORE = "MissionWinEnemyBattleScore"
MISSION_WIN_KEYNODE_LEVEL = "MissionWinKeyNodeLevel"
MISSION_WIN_DEPENDENCY_LEVEL = "MissionWinDependencyLevel"
MISSION_WIN_KEYNODE_NUM = "MissionWinKeyNodeNum"
MISSION_WIN_DEPENDENCY_NUM = "MissionWinDependencyNum"
MISSION_DEFENCE = "MissionDefence"
MISSION_TOTAL_BATTLESCORE = "MissionTotalBattleScore"
MISSION_TEAMSCORE = "MissionTeamScore"
MISSION_PAYCARD = "MissionPayCard"
MISSION_SHARE = "MissionShare"
MISSION_VIP_LEVEL = "MissionVipLevel"
MISSION_VITALITY = "MissionVitality"
MISSION_CAST = "MissionCast"
MISSION_PRAY = "MissionPray"
MISSION_BUY_GOODS_IN_WINESHOP = "MissionBuyGoodsInWineShop"
MISSION_ARENA = "MissionArena"
MISSION_LUCKY_EVENT = "MissionLuckyEvent"
MISSION_BUY_ENERGY = "MissionBuyEnergy"
MISSION_USE_INCREASE_ITEM = "MissionUseIncreaseItem"
MISSION_DAILY_LEVEL_GAP = "MissionDailyLevelGap"
MISSION_DAILY_START_AID = "MissionDailyUnionReqAssist"
MISSION_DAILY_RESPOND_AID = "MissionDailyUnionAssist"
MISSION_DAILY_START_DONATE = "MissionDailyUnionDonate"
MISSION_DAILY_BATTLE_NUM = "MissionDailyBattle"

#开服七天任务
DAY7_MISSION_LOGIN = "Day7MissionDailyLogin"
DAY7_MISSION_WIN_DEPENDENCY_NUM = "Day7MissionWinDependencyNum"
DAY7_MISSION_BUY_ENERGY = "Day7MissionBuyEnergy"
DAY7_MISSION_MONARCH_LEVEL = "Day7MissionMonarchLevel"
DAY7_MISSION_WIN_ENEMY_BATTLE_SCORE = "Day7MissionWinEnemyBattleScore"
DAY7_MISSION_PRAY = "Day7MissionPray"
DAY7_MISSION_BUILDING_UPGRADE = "Day7MissionBuildingUpgrade"
DAY7_MISSION_BUY_GOODS_IN_WINESHOP = "Day7MissionBuyGoodsInWineShop"
DAY7_MISSION_CONSCRIT_SOLDIER_NUM = "Day7MissionConscriptSoldierNum"
DAY7_MISSION_HERO = "Day7MissionHero"
DAY7_MISSION_RESOURCE_GAIN = "Day7MissionResourceGain"
DAY7_MISSION_DEFENCE = "Day7MissionDefence"
DAY7_MISSION_EQUIPMENT_UPGRADE_NUM = "Day7MissionEquipmentUpgradeNum"
DAY7_MISSION_EQUIPMENT_ENCHANT_NUM = "Day7MissionEquipmentEnchantNum"
DAY7_MISSION_TECH_UPGRADE = "Day7MissionTechUpgrade"
DAY7_MISSION_UNION_DONATE = "Day7MissionDailyUnionDonate"
DAY7_MISSION_ADD_SKILLPOINT = "Day7MissionAddSkillPoint"
DAY7_MISSION_UNION_ASSIST = "Day7MissionDailyUnionAssist"
DAY7_MISSION_DUNGEO = "Day7MissionDailyDungeo"
DAY7_MISSION_EQUIPMENT = "Day7MissionEquipment"
DAY7_MISSION_SEARCH = "Day7MissionDailySearch"
DAY7_MISSION_LUCKY_EVENT_SEARCH = "Day7MissionLuckyEventSearch"
DAY7_MISSION_LUCKY_EVENT_TAX = "Day7MissionDailyLuckyEventTax"
DAY7_MISSION_LUCKY_EVENT_FARM = "Day7MissionDailyLuckyEventFarm"
DAY7_MISSION_DEAD_SOLDIER_NUM = "Day7MissionDeadSoldierNum"
DAY7_MISSION_ZHANJINSHAJUE = "Day7MissionDailyZhanJinShaJue"
DAY7_MISSION_HAOFAWUSHANG = "Day7MissionDailyHaoFaWuShang"
DAY7_MISSION_ZHENGFENDUOMIAO = "Day7MissionDailyZhengFenDuoMiao"
DAY7_MISSION_SHILIBANG = "Day7MissionDailyShiLiBang"
DAY7_MISSION_VITALITY = "Day7MissionVitality"




class MissionPool(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._missions = {}
        self._callbacks = {}
        self._last_user_level = 0   #战力排行榜中第50名用户的等级

        #建立从任务id到任务类型的反向索引
        self._load_mission_data(MISSION_SEARCH)
        self._load_mission_data(MISSION_RESOURCE_GAIN)
        self._load_mission_data(MISSION_RESOURCE_CONSUME)
        self._load_mission_data(MISSION_CONSCRIPT_NUM)
        self._load_mission_data(MISSION_CONSCRIPT_SOLDIER_NUM)
        self._load_mission_data(MISSION_DEAD_SOLDIER_NUM)
        self._load_mission_data(MISSION_EQUIPMENT_UPGRADE_NUM)
        self._load_mission_data(MISSION_EQUIPMENT_ENCHANT_NUM)
        self._load_mission_data(MISSION_ADD_SKILL_POINT)
        self._load_mission_data(MISSION_DAILY_LOGIN)
        self._load_mission_data(MISSION_MONARCH_LEVEL)
        self._load_mission_data(MISSION_BUILDING_UPGRADE)
        self._load_mission_data(MISSION_SOLDIER_UPGRADE)
        self._load_mission_data(MISSION_SOLDIER_UPGRADE_NUM)
        self._load_mission_data(MISSION_TECH_UPGRADE)
        self._load_mission_data(MISSION_TECH_UPGRADE_NUM)
        self._load_mission_data(MISSION_EQUIPMENT)
        self._load_mission_data(MISSION_HERO)
        self._load_mission_data(MISSION_WIN_ENEMY_BATTLESCORE)
        self._load_mission_data(MISSION_WIN_KEYNODE_LEVEL)
        self._load_mission_data(MISSION_WIN_DEPENDENCY_LEVEL)
        self._load_mission_data(MISSION_WIN_KEYNODE_NUM)
        self._load_mission_data(MISSION_WIN_DEPENDENCY_NUM)
        self._load_mission_data(MISSION_DEFENCE)
        self._load_mission_data(MISSION_TOTAL_BATTLESCORE)
        self._load_mission_data(MISSION_TEAMSCORE)
        self._load_mission_data(MISSION_PAYCARD)
        self._load_mission_data(MISSION_SHARE)
        self._load_mission_data(MISSION_VIP_LEVEL)
        self._load_mission_data(MISSION_VITALITY)
        self._load_mission_data(MISSION_CAST)
        self._load_mission_data(MISSION_PRAY)
        self._load_mission_data(MISSION_BUY_GOODS_IN_WINESHOP)
        self._load_mission_data(MISSION_ARENA)
        self._load_mission_data(MISSION_LUCKY_EVENT)
        self._load_mission_data(MISSION_BUY_ENERGY)
        self._load_mission_data(MISSION_USE_INCREASE_ITEM)
        self._load_mission_data(MISSION_DAILY_LEVEL_GAP)
        self._load_mission_data(MISSION_DAILY_START_AID)
        self._load_mission_data(MISSION_DAILY_RESPOND_AID)
        self._load_mission_data(MISSION_DAILY_START_DONATE)
        self._load_mission_data(MISSION_DAILY_BATTLE_NUM)
        self._load_mission_data(DAY7_MISSION_LOGIN)
        self._load_mission_data(DAY7_MISSION_WIN_DEPENDENCY_NUM)
        self._load_mission_data(DAY7_MISSION_BUY_ENERGY)
        self._load_mission_data(DAY7_MISSION_MONARCH_LEVEL)
        self._load_mission_data(DAY7_MISSION_WIN_ENEMY_BATTLE_SCORE)
        self._load_mission_data(DAY7_MISSION_PRAY)
        self._load_mission_data(DAY7_MISSION_BUILDING_UPGRADE)
        self._load_mission_data(DAY7_MISSION_BUY_GOODS_IN_WINESHOP)
        self._load_mission_data(DAY7_MISSION_CONSCRIT_SOLDIER_NUM)
        self._load_mission_data(DAY7_MISSION_HERO)
        self._load_mission_data(DAY7_MISSION_RESOURCE_GAIN)
        self._load_mission_data(DAY7_MISSION_DEFENCE)
        self._load_mission_data(DAY7_MISSION_EQUIPMENT_UPGRADE_NUM)
        self._load_mission_data(DAY7_MISSION_EQUIPMENT_ENCHANT_NUM)
        self._load_mission_data(DAY7_MISSION_TECH_UPGRADE)
        self._load_mission_data(DAY7_MISSION_UNION_DONATE)
        self._load_mission_data(DAY7_MISSION_ADD_SKILLPOINT)
        self._load_mission_data(DAY7_MISSION_UNION_ASSIST)
        self._load_mission_data(DAY7_MISSION_DUNGEO) 
        self._load_mission_data(DAY7_MISSION_EQUIPMENT)
        self._load_mission_data(DAY7_MISSION_SEARCH) 
        self._load_mission_data(DAY7_MISSION_LUCKY_EVENT_SEARCH)
        self._load_mission_data(DAY7_MISSION_LUCKY_EVENT_TAX)
        self._load_mission_data(DAY7_MISSION_LUCKY_EVENT_FARM) 
        self._load_mission_data(DAY7_MISSION_DEAD_SOLDIER_NUM)
        self._load_mission_data(DAY7_MISSION_ZHANJINSHAJUE)
        self._load_mission_data(DAY7_MISSION_HAOFAWUSHANG)
        self._load_mission_data(DAY7_MISSION_ZHENGFENDUOMIAO)
        self._load_mission_data(DAY7_MISSION_SHILIBANG)
        self._load_mission_data(DAY7_MISSION_VITALITY)

        #注册不同任务类型对应的回调方法
        #用于更新任务进度
        self._callbacks[MISSION_SEARCH] =                _update_mission_search
        self._callbacks[MISSION_RESOURCE_GAIN] =         _update_mission_resource_gain
        self._callbacks[MISSION_RESOURCE_CONSUME] =      _update_mission_resource_consume
        self._callbacks[MISSION_CONSCRIPT_NUM] =         _update_mission_conscript_num
        self._callbacks[MISSION_CONSCRIPT_SOLDIER_NUM] = _update_mission_conscript_soldier_num
        self._callbacks[MISSION_DEAD_SOLDIER_NUM] =      _update_mission_dead_soldier_num
        self._callbacks[MISSION_EQUIPMENT_UPGRADE_NUM] = _update_mission_equipment_upgrade_num
        self._callbacks[MISSION_EQUIPMENT_ENCHANT_NUM] = _update_mission_equipment_enchant_num
        self._callbacks[MISSION_ADD_SKILL_POINT] =       _update_mission_add_skill_point
        self._callbacks[MISSION_DAILY_LOGIN] =           _update_mission_daily_login
        self._callbacks[MISSION_MONARCH_LEVEL] =         _update_mission_monarch_level
        self._callbacks[MISSION_BUILDING_UPGRADE] =      _update_mission_building_upgrade
        self._callbacks[MISSION_SOLDIER_UPGRADE] =       _update_mission_soldier_upgrade
        self._callbacks[MISSION_SOLDIER_UPGRADE_NUM] =   _update_mission_soldier_upgrade_num
        self._callbacks[MISSION_TECH_UPGRADE] =          _update_mission_tech_upgrade
        self._callbacks[MISSION_TECH_UPGRADE_NUM] =      _update_mission_tech_upgrade_num
        self._callbacks[MISSION_EQUIPMENT] =             _update_mission_equipment
        self._callbacks[MISSION_HERO] =                  _update_mission_hero
        self._callbacks[MISSION_WIN_ENEMY_BATTLESCORE] = _update_mission_win_enemy_battlescore
        self._callbacks[MISSION_WIN_KEYNODE_LEVEL] =     _update_mission_win_keynode_level
        self._callbacks[MISSION_WIN_DEPENDENCY_LEVEL] =  _update_mission_win_dependency_level
        self._callbacks[MISSION_WIN_KEYNODE_NUM] =       _update_mission_win_keynode_num
        self._callbacks[MISSION_WIN_DEPENDENCY_NUM] =    _update_mission_win_dependency_num
        self._callbacks[MISSION_DEFENCE] =               _update_mission_defence
        self._callbacks[MISSION_TOTAL_BATTLESCORE] =     _update_mission_total_battlescore
        self._callbacks[MISSION_TEAMSCORE] =             _update_mission_teamscore
        self._callbacks[MISSION_PAYCARD] =               _update_mission_paycard
        self._callbacks[MISSION_SHARE] =                 _update_mission_share
        self._callbacks[MISSION_VIP_LEVEL] =             _update_mission_vip_level
        self._callbacks[MISSION_VITALITY] =              _update_mission_vitality
        self._callbacks[MISSION_CAST] =                  _update_mission_cast
        self._callbacks[MISSION_PRAY] =                  _update_mission_pray
        self._callbacks[MISSION_BUY_GOODS_IN_WINESHOP] = _update_mission_buy_goods_in_wineshop
        self._callbacks[MISSION_ARENA] =                 _update_mission_arena
        self._callbacks[MISSION_LUCKY_EVENT] =           _update_mission_lucky_event
        self._callbacks[MISSION_BUY_ENERGY] =            _update_mission_buy_energy
        self._callbacks[MISSION_USE_INCREASE_ITEM] =     _update_mission_use_increase_item
        self._callbacks[MISSION_DAILY_LEVEL_GAP] =       _update_mission_daily_level_gap
        self._callbacks[MISSION_DAILY_START_AID] =       _update_mission_daily_start_aid
        self._callbacks[MISSION_DAILY_RESPOND_AID] =     _update_mission_daily_respond_aid
        self._callbacks[MISSION_DAILY_START_DONATE] =    _update_mission_daily_start_donate
        self._callbacks[MISSION_DAILY_BATTLE_NUM] =      _update_mission_daily_battle_num
        self._callbacks[DAY7_MISSION_LOGIN] =                      _update_day7_mission_login 
        self._callbacks[DAY7_MISSION_WIN_DEPENDENCY_NUM] =         _update_mission_win_dependency_num
        self._callbacks[DAY7_MISSION_BUY_ENERGY] =                 _update_day7_mission_buy_energy 
        self._callbacks[DAY7_MISSION_MONARCH_LEVEL] =              _update_mission_monarch_level
        self._callbacks[DAY7_MISSION_WIN_ENEMY_BATTLE_SCORE] =     _update_mission_win_enemy_battlescore
        self._callbacks[DAY7_MISSION_PRAY] =                       _update_day7_mission_pray
        self._callbacks[DAY7_MISSION_BUILDING_UPGRADE] =           _update_day7_mission_building_upgrade
        self._callbacks[DAY7_MISSION_BUY_GOODS_IN_WINESHOP] =      _update_day7_mission_buy_goods_in_wineshop
        self._callbacks[DAY7_MISSION_CONSCRIT_SOLDIER_NUM] =       _update_mission_conscript_soldier_num
        self._callbacks[DAY7_MISSION_HERO] =                       _update_mission_hero
        self._callbacks[DAY7_MISSION_RESOURCE_GAIN] =              _update_mission_resource_gain
        self._callbacks[DAY7_MISSION_DEFENCE] =                    _update_mission_defence
        self._callbacks[DAY7_MISSION_EQUIPMENT_UPGRADE_NUM] =      _update_day7_mission_equipment_upgrade_num
        self._callbacks[DAY7_MISSION_EQUIPMENT_ENCHANT_NUM] =      _update_day7_mission_equipment_enchant_num
        self._callbacks[DAY7_MISSION_TECH_UPGRADE] =               _update_day7_mission_tech_upgrade
        self._callbacks[DAY7_MISSION_UNION_DONATE] =               _update_day7_mission_start_donate 
        self._callbacks[DAY7_MISSION_ADD_SKILLPOINT] =             _update_day7_mission_add_skill_point
        self._callbacks[DAY7_MISSION_UNION_ASSIST] =               _update_day7_mission_respond_aid
        self._callbacks[DAY7_MISSION_DUNGEO] =                     _update_day7_mission_lucky_event
        self._callbacks[DAY7_MISSION_EQUIPMENT] =                  _update_mission_equipment
        self._callbacks[DAY7_MISSION_SEARCH] =                     _update_day7_mission_search
        self._callbacks[DAY7_MISSION_LUCKY_EVENT_SEARCH] =         _update_day7_mission_lucky_event 
        self._callbacks[DAY7_MISSION_LUCKY_EVENT_TAX] =            _update_day7_mission_lucky_event 
        self._callbacks[DAY7_MISSION_LUCKY_EVENT_FARM] =           _update_day7_mission_lucky_event
        self._callbacks[DAY7_MISSION_DEAD_SOLDIER_NUM] =           _update_mission_dead_soldier_num
        self._callbacks[DAY7_MISSION_ZHANJINSHAJUE] =              _update_day7_mission_battle_num 
        self._callbacks[DAY7_MISSION_HAOFAWUSHANG] =               _update_day7_mission_battle_num
        self._callbacks[DAY7_MISSION_ZHENGFENDUOMIAO] =            _update_day7_mission_battle_num
        self._callbacks[DAY7_MISSION_SHILIBANG] =                  _update_day7_mission_battle_num
        self._callbacks[DAY7_MISSION_VITALITY] =                   _update_day7_mission_vitality 

    def get_mission_method(self, mission_basic_id):
        if mission_basic_id not in self._missions:
            return None
        else:
            return self._callbacks[self._missions[mission_basic_id]]


    def get_mission_name(self, mission_basic_id):
        return self._missions[mission_basic_id]

    def get_last_user_level(self):
        return self._last_user_level

    def update_last_user_level(self, level):
        self._last_user_level = level

    def _load_mission_data(self, mission_name):
        mission_dict = getattr(data_loader, mission_name + "_dict")
        for basic_id in mission_dict:
            self._missions[basic_id] = mission_name


def init(user_id, pattern):
    """创建用户时初始化任务
    """
    mission_basic_ids = data_loader.InitUserBasicInfo_dict[pattern].missionBasicId
    missions = []
    for basic_id in mission_basic_ids:
        mission = MissionInfo.create(user_id, basic_id)
        missions.append(mission)
    return missions


def get_mission(data, mission_name):
    """获取某一类的任务
    """
    missions = []

    mission_dict = getattr(data_loader, mission_name + "_dict")
    for basic_id in mission_dict:
        mission_id = MissionInfo.generate_id(data.id, basic_id)
        m = data.mission_list.get(mission_id, True)
        if m is not None:
            missions.append(m)

    return missions


def reset_daily_missions(data, pattern = 1):
    """新的一天，更新日常任务
    """
    #先找出所有旧日常任务
    old_daily_missions = {}
    missions = data.mission_list.get_all()
    for i in range(len(missions)):
        if missions[i].type == MISSION_TYPE_DAILY:
            old_daily_missions[missions[i].basic_id] = missions[i]

    #更新日常任务(已有的reset，缺少的新增 )
    old_daily_missions_reset = {}
    mission_basic_ids = data_loader.InitUserBasicInfo_dict[pattern].dailyMissionBasicId
    for basic_id in mission_basic_ids:
        if old_daily_missions.has_key(basic_id):
            old_daily_missions[basic_id].reset()
            old_daily_missions_reset[basic_id] = old_daily_missions[basic_id]
        else:
            mission = MissionInfo.create(data.id, basic_id)
            data.mission_list.add(mission)

    #删除多余的旧日常任务
    for basic_id in old_daily_missions:
        if not old_daily_missions_reset.has_key(basic_id):
            data.mission_list.delete(old_daily_missions[basic_id].id)


def update_all_missions(data, now):
    """更新一遍所有任务的状态
    """
    mission_list = data.mission_list.get_all()
    user = data.user.get(True)

    #是否删除超过7天的开服七天任务
    now_time = utils.get_start_second(now)
    create_time = utils.get_start_second(user.create_time)
    if (now_time - create_time) / utils.SECONDS_OF_DAY > 7:
        day7_mission_overtime = True
    else:
        day7_mission_overtime = False

    #由于删除了任务，特殊处理：任务逻辑不存在时，删除原任务数据
    #TODO
    to_delete = []
    for mission in mission_list:
        method = MissionPool().get_mission_method(mission.basic_id)
        if method is None:
            to_delete.append(mission.id)
            continue
            # raise Exception("unknown mission id[id=%d]" % mission.basic_id)

        if mission.is_day7_type() and day7_mission_overtime:
            to_delete.append(mission.id)
            continue

        method(data, mission)

    for mission_id in to_delete:
        data.mission_list.delete(mission_id)


def finish_mission(mission_basic_id, data, now):
    """完成指定的任务
    玩家已经达到了任务目标，完成指定任务，领取奖励
    Args:
        mission_basic_id
        data
        now
    Returns:
        True/False: 是否成功完成
    """
    mission_id = MissionInfo.generate_id(data.id, mission_basic_id)
    mission = data.mission_list.get(mission_id)
    if mission is None:
        logger.warning("mission not exist")
        return False

    #若是分享任务，服务器默认完成（暂时无法check)
    if MissionPool().get_mission_name(mission.basic_id) == MISSION_SHARE:
        trainer = data.trainer.get()
        trainer.add_share_num(1)

    #若是战力任务，服务器默认完成（客户端和服务器存在战力计算不完全一致的情况)
    force = False
    if (MissionPool().get_mission_name(mission.basic_id) == MISSION_TOTAL_BATTLESCORE or
            MissionPool().get_mission_name(mission.basic_id) == DAY7_MISSION_WIN_ENEMY_BATTLE_SCORE):
        force = True

    #获取任务的处理方法
    method = MissionPool().get_mission_method(mission_basic_id)
    if method is None:
        logger.warning("unknown mission id[id=%d]" % mission_basic_id)
        return False

    method(data, mission)

    #结算任务
    return _calc_mission(data, mission, now, force)

def update_last_user_level():
    """更新第50名用户的等级"""
    proxy = DataProxy()
    proxy.search_by_rank("battle_score", "score", 0, 49)

    defer = proxy.execute()
    defer.addCallback(_update_last_user_level_rank)
    return defer
    
def _update_last_user_level_rank(proxy):
    results = proxy.get_rank_result("battle_score", "score", 0, 49)
    if len(results) == 0:
        MissionPool.update_last_user_level(0)
        return 0
        
    last_user_id = results[len(results) - 1].user_id
    proxy = DataProxy()
    proxy.search("user", last_user_id)

    defer = proxy.execute()
    defer.addCallback(_update_last_user_level_result, last_user_id)
    return defer

def _update_last_user_level_result(proxy, last_user_id):
    result = proxy.get_result("user", last_user_id)

    MissionPool().update_last_user_level(result.level)
    return result.level

def _update_mission_search(data, mission):
    draw= data.draw.get(True)

    if mission.type == MISSION_TYPE_DAILY:
        mission.update(draw.daily_money_draw_num + draw.daily_gold_draw_num)

def _update_day7_mission_search(data, mission):
    draw= data.draw.get(True)
    mission.update(draw.total_gold_draw_num)

def _update_mission_resource_consume(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    resource = data.resource.get(True)

    if mission.type == MISSION_TYPE_DAILY:
        if mission_data.moneyUsedDest != 0:
            mission.update(resource.daily_use_money)
        elif mission_data.foodUsedDest != 0:
            mission.update(resource.daily_use_food)
        elif mission_data.goldUsedDest != 0:
            mission.update(resource.daily_use_gold)
    else:
        if mission_data.moneyUsedDest != 0:
            mission.update(resource.total_use_money)
        elif mission_data.foodUsedDest != 0:
            mission.update(resource.total_use_food)
        elif mission_data.goldUsedDest != 0:
            mission.update(resource.total_use_gold)


def _update_mission_resource_gain(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    resource = data.resource.get(True)

    if mission.type == MISSION_TYPE_DAILY:
        if mission_data.moneyGainDest != 0:
            mission.update(resource.daily_gain_money)
        elif mission_data.foodGainDest != 0:
            mission.update(resource.daily_gain_food)
        elif mission_data.goldGainDest != 0:
            mission.update(resource.daily_gain_gold)
    else:
        mission.update(resource.total_gain_money + resource.total_gain_food)


def _update_mission_conscript_num(data, mission):
    num = 0
    conscript_list = data.conscript_list.get_all(True)
    for conscript in conscript_list:
        if conscript.daily_conscript_soldier > 0:
            num += 1

    mission.update(num)


def _update_mission_conscript_soldier_num(data, mission):
    #先更新现有兵数
    timer = Timer()
    resource = data.resource.get()
    conscript_list = data.conscript_list.get_all()
    for conscript in conscript_list:
        conscript_business.update_current_soldier(conscript, timer.now)

    conscript_soldier_num = 0
    conscript_list = data.conscript_list.get_all(True)
    for conscript in conscript_list:
        if mission.type == MISSION_TYPE_DAILY:
            conscript_soldier_num += conscript.daily_conscript_soldier
        else:
            conscript_soldier_num += conscript.total_conscript_soldier

    mission.update(conscript_soldier_num)


def _update_mission_dead_soldier_num(data, mission):
    trainer = data.trainer.get(True)

    if mission.type == MISSION_TYPE_DAILY:
        mission.update(trainer.daily_deads)
    else:
        mission.update(trainer.total_deads)


def _update_mission_equipment_upgrade_num(data, mission):
    trainer = data.trainer.get(True)

    if mission.type == MISSION_TYPE_DAILY:
        mission.update(trainer.daily_equipment_upgrade)


def _update_mission_equipment_enchant_num(data, mission):
    trainer = data.trainer.get(True)

    if mission.type == MISSION_TYPE_DAILY:
        mission.update(trainer.daily_equipment_enchant)


def _update_mission_add_skill_point(data, mission):
    trainer = data.trainer.get(True)

    if mission.type == MISSION_TYPE_DAILY:
        mission.update(trainer.daily_skill_upgrade)


def _update_day7_mission_equipment_upgrade_num(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.total_equipment_upgrade)


def _update_day7_mission_equipment_enchant_num(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.total_equipment_enchant)


def _update_day7_mission_add_skill_point(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.total_skill_upgrade)



def _update_mission_daily_login(data, mission):
    timer = Timer()
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    start = utils.get_spec_second(timer.now, mission_data.startTime)
    end = utils.get_spec_second(timer.now, mission_data.endTime)
    tolerance = 120
    #if timer.now >= start - tolerance and timer.now <= end + tolerance:
    #    mission.update(1)
    #暂时为了避免时区等错误，登陆任务都放过
    mission.update(1)


def _update_day7_mission_login(data, mission):
    timer = Timer()
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    start = utils.get_spec_second(timer.now, mission_data.startTime)
    end = utils.get_spec_second(timer.now, mission_data.endTime)
    tolerance = 120
    #if timer.now >= start - tolerance and timer.now <= end + tolerance:
    #    mission.update(1)
    #暂时为了避免时区等错误，登陆任务都放过
    mission.update(data.trainer.get(True).total_login_num)


def _update_mission_monarch_level(data, mission):
    user = data.user.get(True)
    mission_data = data_loader.AllMission_dict[mission.basic_id]

    mission.update(user.level)


def _update_mission_building_upgrade(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    building_list = data.building_list.get_all(True)

    num = 0
    for building in building_list:
        basic_id = building.basic_id
        for building_basic_id in mission_data.buildingBasicId:
            if basic_id == building_basic_id \
                    and building.level >= mission_data.needLevel:
                num += 1
                break

    mission.update(num)


def _update_day7_mission_building_upgrade(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    building_list = data.building_list.get_all(True)

    num = 0
    for building in building_list:
        basic_id = building.basic_id
        for building_basic_id in mission_data.buildingBasicId:
            if basic_id == building_basic_id:
                mission.update(building.level)
                break


def _update_mission_soldier_upgrade(data, mission):
    soldier_list = data.soldier_list.get_all(True)
    mission_data = data_loader.AllMission_dict[mission.basic_id]

    num = 0
    for soldier in soldier_list:
        basic_id = soldier.basic_id
        for soldier_basic_id in mission_data.soldierBasicIds:
            if basic_id == soldier_basic_id \
                    and soldier.level >= mission_data.needLevel:
                num += 1
                break

    mission.update(num)


def _update_mission_soldier_upgrade_num(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.total_soldier_tech_upgrade)


def _update_mission_tech_upgrade(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_tech_upgrade_num)


def _update_day7_mission_tech_upgrade(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    trainer = data.trainer.get(True)
    mission.update(trainer.total_tech_upgrade_num)


def _update_mission_tech_upgrade_num(data, mission):
    trainer = data.trainer.get(True)

    tech_upgrade_num = trainer.total_battle_tech_upgrade \
            + trainer.total_interior_tech_upgrade   #策划指的科技是战斗和内政科技
    mission.update(tech_upgrade_num)


def _update_mission_equipment(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    need_upgrade_level = mission_data.needUpgradeLevel
    need_enchant_level = mission_data.needEnchantLevel
    need_num = mission_data.needNum

    num = 0
    hero_list = data.hero_list.get_all(True)
    for hero in hero_list:
        equipment_list = hero.get_equipments()
        equip_num = 0
        for equipment_basic_id in equipment_list:
            equipment_data = data_loader.EquipmentBasicInfo_dict[equipment_basic_id]
            if equipment_data.upgradeLevel >= need_upgrade_level \
                    and equipment_data.enchantLevel >= need_enchant_level:
                equip_num += 1

        if equip_num >= need_num:
            num += 1

    mission.update(num)


def _update_mission_hero(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    need_level = mission_data.needLevel
    need_star_level = mission_data.needStarLevelNow
    need_max_potential_level = mission_data.needMaxPotentialLevel

    num = 0
    hero_list = data.hero_list.get_all(True)
    for hero in hero_list:
        if (hero.level >= need_level and
                hero.star >= need_star_level and
                data_loader.HeroBasicInfo_dict[hero.basic_id].potentialLevel >=
                need_max_potential_level):
            num += 1

    mission.update(num)


def _update_mission_win_enemy_battlescore(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.rival_highest_battlescore)


def _update_mission_win_keynode_level(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.knode_highest_level)


def _update_mission_win_dependency_level(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.dnode_highest_level)


def _update_mission_win_keynode_num(data, mission):
    trainer = data.trainer.get(True)
    if mission.type == MISSION_TYPE_DAILY:
        mission.update(trainer.knode_daily_win)
    else:
        mission.update(trainer.knode_total_win)


def _update_mission_win_dependency_num(data, mission):
    trainer = data.trainer.get(True)
    if mission.type == MISSION_TYPE_DAILY:
        mission.update(trainer.dnode_daily_win)
    else:
        mission.update(trainer.dnode_total_win)


def _update_mission_defence(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.defense_win)


def _update_mission_total_battlescore(data, mission):
    battle_score = data.battle_score.get(True)
    mission.update(battle_score.score)
    #ugly 客户端战力和服务器计算不一致，导致任务领取失败，临时修改
    #mission.update(mission.target_num)

def _update_mission_teamscore(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    team_list = data.team_list.get_all(True)

    num = 0
    for team in team_list:
        if team.battle_score >= mission_data.battleScore:
            num += 1

    mission.update(num)


def _update_mission_paycard(data, mission):
    """更新月卡任务
    检查充值情况，如果月卡有效，则完成当前任务
    """
    user = data.user.get(True)
    if mission.is_finish(user.level):
        return

    mission_data = data_loader.AllMission_dict[mission.basic_id]
    pay = data.pay.get()
    if pay.has_card(mission_data.cardType):
        timer = Timer()
        left_day = pay.get_card_left_day(mission_data.cardType, timer.now)
        mission.update(left_day)


def _update_mission_share(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_share)


def _update_mission_vip_level(data, mission):
    user = data.user.get(True)

    mission_data = data_loader.AllMission_dict[mission.basic_id]
    if user.vip_level >= mission_data.limitVipLevel:
        mission.update(1)

def _update_mission_vitality(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_vitality)

def _update_day7_mission_vitality(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.day7_vitality)


def _update_mission_cast(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_cast_item_num)

def _update_mission_pray(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_pray_num)

def _update_day7_mission_pray(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.total_pray_num)

def _update_mission_buy_goods_in_wineshop(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_buy_goods_in_wineshop)

def _update_day7_mission_buy_goods_in_wineshop(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.total_buy_goods_in_wineshop)

def _update_mission_arena(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_arena_num)

def _update_mission_lucky_event(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    trainer = data.trainer.get(True)
    mission.update(trainer.get_daily_event_num(mission_data.luckyEventType))

def _update_day7_mission_lucky_event(data, mission):
    mission_data = data_loader.AllMission_dict[mission.basic_id]
    trainer = data.trainer.get(True)
    mission.update(trainer.get_total_event_num(mission_data.luckyEventType))

def _update_mission_buy_energy(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_buy_energy_num)

def _update_day7_mission_buy_energy(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.total_buy_energy_num)

def _update_mission_use_increase_item(data, mission):
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_increase_item_num)

def _update_mission_daily_level_gap(data, mission):
    user = data.user.get(True)
    mission.current_num = MissionPool().get_last_user_level() - user.level

    '''
    proxy = DataProxy()
    proxy.search_by_rank("battle_score", "score", 0, 49)

    defer = proxy.execute()
    defer.addCallback(_update_mission_daily_level_gap_rank, data, mission)
    
def _update_mission_daily_level_gap_rank(proxy, data, mission):
    results = proxy.get_rank_result("battle_score", "score", 0, 49)
    last_user_id = results[len(results) - 1].user_id
    proxy.search("user", last_user_id)

    defer = proxy.execute()
    defer.addCallback(_update_mission_daily_level_gap_result, data, mission, last_user_id)

def _update_mission_daily_level_gap_result(proxy, data, mission, last_user_id):
    result = proxy.get_result("user", last_user_id)

    user = data.user.get(True)
    mission.current_num = result.level - user.level
    '''

def _update_mission_daily_start_aid(data, mission):
    """每日发起联盟援助"""
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_start_union_aid)

def _update_mission_daily_respond_aid(data, mission):
    """每日响应里联盟援助"""
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_respond_union_aid)

def _update_day7_mission_respond_aid(data, mission):
    """响应里联盟援助"""
    trainer = data.trainer.get(True)
    mission.update(trainer.total_respond_union_aid)


def _update_mission_daily_start_donate(data, mission):
    """每日进行联盟捐献"""
    trainer = data.trainer.get(True)
    mission.update(trainer.daily_start_union_donate)


def _update_day7_mission_start_donate(data, mission):
    """进行联盟捐献"""
    trainer = data.trainer.get(True)
    mission.update(trainer.total_start_union_donate)


def _update_mission_daily_battle_num(data, mission):
    """每日进行仙豆"""
    trainer = data.trainer.get(True)

    mission_data = data_loader.AllMission_dict[mission.basic_id]
    BATTLE_FINISH_TYPE_LEGENDCITY = 0
    BATTLE_FINISH_TYPE_ANNEAL_NORMAL = 1
    BATTLE_FINISH_TYPE_ANNEAL_HARD = 2
    BATTLE_FINISH_TYPE_EXPAND_ONE = 3
    BATTLE_FINISH_TYPE_EXPAND_TWO = 4
    BATTLE_FINISH_TYPE_EXPAND_THREE = 5
    BATTLE_FINISH_TYPE_TRANSFER = 6

    if mission_data.battleFinishType == BATTLE_FINISH_TYPE_LEGENDCITY:
        mission.update(trainer.daily_battle_legendcity)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_ANNEAL_NORMAL:
        mission.update(trainer.daily_battle_anneal_normal)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_ANNEAL_HARD:
        mission.update(trainer.daily_battle_anneal_hard)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_EXPAND_ONE:
        mission.update(trainer.daily_battle_expand_one)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_EXPAND_TWO:
        mission.update(trainer.daily_battle_expand_two)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_EXPAND_THREE:
        mission.update(trainer.daily_battle_expand_three)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_TRANSFER:
        mission.update(trainer.daily_battle_transfer)


def _update_day7_mission_battle_num(data, mission):
    """每日进行仙豆"""
    trainer = data.trainer.get(True)

    mission_data = data_loader.AllMission_dict[mission.basic_id]
    BATTLE_FINISH_TYPE_LEGENDCITY = 0
    BATTLE_FINISH_TYPE_ANNEAL_NORMAL = 1
    BATTLE_FINISH_TYPE_ANNEAL_HARD = 2
    BATTLE_FINISH_TYPE_EXPAND_ONE = 3
    BATTLE_FINISH_TYPE_EXPAND_TWO = 4
    BATTLE_FINISH_TYPE_EXPAND_THREE = 5
    BATTLE_FINISH_TYPE_TRANSFER = 6

    if mission_data.battleFinishType == BATTLE_FINISH_TYPE_LEGENDCITY:
        mission.update(trainer.total_battle_legendcity)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_ANNEAL_NORMAL:
        mission.update(trainer.total_battle_anneal_normal)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_ANNEAL_HARD:
        mission.update(trainer.total_battle_anneal_hard)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_EXPAND_ONE:
        mission.update(trainer.total_battle_expand_one)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_EXPAND_TWO:
        mission.update(trainer.total_battle_expand_two)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_EXPAND_THREE:
        mission.update(trainer.total_battle_expand_three)
    elif mission_data.battleFinishType == BATTLE_FINISH_TYPE_TRANSFER:
        mission.update(trainer.total_battle_transfer)

def _calc_mission(data, mission, now, force):
    """结算已经完成的任务
    1 获得奖励
    2 开启后续任务（如果有后续的话）
    """
    #检查是否结束
    user = data.user.get(True)
    if not force and not mission.is_finish(user.level):
        logger.warning("Mission not finish[basic id=%d]" % (mission.basic_id))
        return False

    reward = data_loader.AllMission_dict[mission.basic_id].reward
    #获得资源
    resource = data.resource.get()
    original_gold = resource.gold
    resource.update_current_resource(now)
    resource.gain_money(reward.money)
    resource.gain_food(reward.food)
    resource.gain_gold(reward.gold)
    log = log_formater.output_gold(data, reward.gold, log_formater.MISSION_REWARD_GOLD,
                "Gain gold from compelete mission", before_gold = original_gold)
    logger.notice(log)

    #获得政令
    energy = data.energy.get()
    energy.update_current_energy(now)
    energy.gain_energy(reward.energy)

    #获得战利品
    item_list = mission.get_reward_items()
    if not item_business.gain_item(data, item_list, "mission reward", log_formater.MISSION_REWARD):
        return False
    for i in range(0, len(item_list)):
        id = ItemInfo.generate_id(data.id, item_list[i][0])
        item = data.item_list.get(id)
    

    #用户获得经验
    if not user_business.level_upgrade(data, reward.monarchExp, now, "mission exp", log_formater.EXP_MISSION):
        return False

    #创建后续任务
    next_mission = mission.create_next()
    if next_mission is not None:
        data.mission_list.add(next_mission)

    return True


