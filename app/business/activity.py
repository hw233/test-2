#coding:utf8
"""
Created on 2016-03-14
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 活动相关计算逻辑
"""


from firefly.utils.singleton import Singleton
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from app.data.activity import ActivityInfo
from datalib.data_proxy4redis import DataProxy
from app.data.basic_activity import BasicActivityInfo
from app.data.basic_activity_step import BasicActivityStepInfo
from app.data.basic_activity_hero_reward import BasicActivityHeroRewardInfo
from app.business import item as item_business
from app.business import hero as hero_business
from app.business import account as account_business
from app import log_formater


FUNDS_USER_LEVEL_LIMIT = 30
FUNDS_VIP_LEVEL_LIMIT = 4


class ActivityPool(object):

    __metaclass__ = Singleton


    def __init__(self):
        self._is_invalid = {}
        self._update = {}
        self._operator = {}

        #注册所有的更新方法
        #需要和 Excel 中的 activity basic id 配置一致
        self._update[1] = _update_activity_firstpay
        self._is_invalid[1] = _is_activity_invalid

        self._update[2] = _update_activity_login
        self._is_invalid[2] = _is_activity_invalid

        self._update[3] = _update_activity_funds
        self._is_invalid[3] = _is_activity_funds_valid
        self._operator[3] = _operate_activity_funds

        self._update[4] = _update_activity_pay
        self._is_invalid[4] = _is_activity_invalid

        self._update[5] = _update_activity_shop
        self._is_invalid[5] = _is_activity_invalid_for_shop
        self._operator[5] = _operate_activity_shop

        self._update[6] = _update_activity_cost_gold
        self._is_invalid[6] = _is_activity_invalid

        self._update[7] = _update_activity_cost_energy
        self._is_invalid[7] = _is_activity_invalid

        self._update[8] = _update_activity_pay_once
        self._is_invalid[8] = _is_activity_invalid

        self._update[9] = _update_activity_login
        self._is_invalid[9] = _is_activity_invalid

        self._update[10] = _update_activity_hero
        self._is_invalid[10] = _is_activity_invalid

        #展示活动，不用update
        self._update[11] = _update_activity_hero
        self._is_invalid[11] = _is_activity_invalid

        self._update[12] = _update_activity_hero
        self._is_invalid[12] = _is_activity_invalid

        self._update[13] = _update_activity_hero
        self._is_invalid[13] = _is_activity_invalid

        self._update[14] = _update_activity_hero
        self._is_invalid[14] = _is_activity_invalid

        #开采次数
        self._update[15] = _update_activity_exploit
        self._is_invalid[15] = _is_activity_invalid

        #山贼战斗次数
        self._update[16] = _update_activity_jungle
        self._is_invalid[16] = _is_activity_invalid

        #演武战斗次数
        self._update[17] = _update_activity_arena
        self._is_invalid[17] = _is_activity_invalid

        #掠夺或占领战斗次数
        self._update[18] = _update_activity_key_node
        self._is_invalid[18] = _is_activity_invalid

        #祈福翻牌子次数
        self._update[19] = _update_activity_choose_card
        self._is_invalid[19] = _is_activity_invalid

        #各种商店购买次数
        self._update[20] = _update_activity_buy_goods
        self._is_invalid[20] = _is_activity_invalid

        #搜索次数
        self._update[21] = _update_activity_search
        self._is_invalid[21] = _is_activity_invalid

        #离线事件次数
        self._update[22] = _update_activity_offline_event
        self._is_invalid[22] = _is_activity_invalid

        #世界boss战功活动
        self._update[23] = _update_activity_worldboss_merit
        self._is_invalid[23] = _is_activity_invalid

        #世界boss排名活动
        self._update[24] = _update_activity_worldboss_ranking
        self._is_invalid[24] = _is_activity_invalid

        #vip限时优惠
        self._update[25] = _update_activity_discount
        self._is_invalid[25] = _is_activity_invalid
        self._operator[25] = _operate_activity_discount

        #累计充值天数
        self._update[26] = _update_activity_pay_day_num
        self._is_invalid[26] = _is_activity_invalid

        #每日特惠
        self._update[27] = _update_activity_pay_daily
        self._is_invalid[27] = _is_activity_invalid

        #好友邀请
        self._update[28] = _update_activity_invite
        self._is_invalid[28] = _is_activity_invalid
  
        #夺宝积分
        self._update[29] = _update_activity_treasure
        self._is_invalid[29] = _is_activity_invalid

        #招财
        self._update[30] = _update_fortune_cat
        self._is_invalid[30] = _is_activity_invalid

    def update(self, basic_data, data, activity, now):
        """更新完成度
        """
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        method = self._update[basic_activity.type_id]
        method(basic_data, data, activity, now)


    def is_invalid(self, basic_data, data, activity, now):
        """
        """
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        method = self._is_invalid[basic_activity.type_id]
        return method(basic_data, data, activity,now)


    def operate(self, basic_data, data, activity, op_type, op_input, step_id, now):
        """
        """
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        method = self._operator[basic_activity.type_id]
        return method(basic_data, data, activity, op_type, op_input, step_id, now)


    def get_activity_by_type(self, basic_data, data, type_id, now):
        """
        """
        activities = []
        for activity in data.activity_list.get_all():
            basic_activity = basic_data.activity_list.get(activity.basic_id)
            if basic_activity is None: #说明活动已过期，basic activity信息已经被过期淘汰了
                continue
            if type_id == basic_activity.type_id and activity.is_living(now, basic_activity.style_id):
                activities.append(activity)

        return activities


    def update_activity_by_type(self, basic_data, data, type_id):
        """
        """
        for basic_activity in basic_data.activity_list.get_all():
            if basic_activity.type_id != type_id:
                continue

            activity_id = ActivityInfo.generate_id(data.id, basic_activity.id)
            if data.activity_list.get(activity_id) is None:
                #应有的活动未被创建
                basic_steps = get_basic_activity_steps(basic_data, basic_activity)
                if not add_activity(basic_data, data, basic_activity.id, basic_activity, basic_steps):
                    raise Exception("Update activity by type failed")

        return


def get_basic_activity_steps(basic_data, basic_activity):
    """获得活动的steps信息
    """
    steps = []
    steps_id = basic_activity.get_steps()
    for step_id in steps_id:
        step = basic_data.activity_step_list.get(step_id)
        if step is None:
            return None

        steps.append(step)

    return steps


def init_activity(basic_data, data, pattern, timer):
    """初始化活动
    """
    basic_init = basic_data.init.get(True)
    init_activities = basic_init.get_init_activities()
    logger.debug("init activities[ids=%s]" % utils.join_to_string(init_activities))
    for id in init_activities:
        basic_activity = basic_data.activity_list.get(id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        if basic_steps is None:
            return False

        if not add_activity(basic_data, data, id, basic_activity, basic_steps, now = timer.now):
            return False

    return True


def add_activity(basic_data, data, basic_id, basic_activity, basic_steps, now = 0):
    """添加一个活动
    """
    #try:
    #    ACTIVITY_HERO_TYPE = 10 
    #    draw = data.draw.get()
    #    if basic_activity.type_id == ACTIVITY_HERO_TYPE and draw != None:
    #        draw.clear_activity_scores()
    #except:
    #    pass
    
    activity = ActivityInfo.create(data.id, basic_id, basic_activity, basic_steps, now)
    for exist_activity in data.activity_list.get_all():
        if exist_activity.id == activity.id:
            exist_activity.reset(basic_activity, basic_steps)
            exist_activity.set_time(activity.start_time, activity.end_time)
            return True
        else:
            if ActivityPool().is_invalid(basic_data, data, activity, now):
                return True
    data.activity_list.add(activity)
    return True


def accept_reward(basic_data, data, activity_basic_id, step_id, now):
    """领取奖励
    """
    basic_activity = basic_data.activity_list.get(activity_basic_id)
    activity_id = ActivityInfo.generate_id(data.id, activity_basic_id)
    activity = data.activity_list.get(activity_id)

    if not activity.accept_reward(basic_activity, step_id):
        return False

    if not activity.is_living(now, basic_activity.style_id):
        logger.warning("Activity is not living[basic id=%d]" % activity_basic_id)
        return False
    #领取奖励后更新activity，保证部分活动可以重新修改活动状态
    _update_one_activity(basic_data, data, activity, now)

    #获得奖励
    stepInfo = basic_data.activity_step_list.get(step_id)
    for hero_basic_id in stepInfo.get_heroes_basic_id():
        if not hero_business.gain_hero(data, hero_basic_id):
            return False

    items = stepInfo.get_items()
    if not item_business.gain_item(data, items, "activity reward", log_formater.ACTIVITY_REWARD):
        return False

    gold = stepInfo.gold
    if gold > 0:
        resource = data.resource.get()
        original_gold = resource.gold
        resource.gain_gold(gold)
        log = log_formater.output_gold(data, gold, log_formater.ACCEPT_REWARD_GOLD,
                "Gain gold from activity", before_gold = original_gold)
        logger.notice(log)

    return True

def cat_reward(basic_data, data, activity_basic_id, step_id, now):
    """领取奖励
    """
    basic_activity = basic_data.activity_list.get(activity_basic_id)
    
    activity_id = ActivityInfo.generate_id(data.id, activity_basic_id)
    activity = data.activity_list.get(activity_id)
    if not activity.accept_reward(basic_activity, step_id):
        return False
    if not activity.is_living(now, basic_activity.style_id):
        logger.warning("Activity is not living[basic id=%d]" % activity_basic_id)
        return False
    #领取奖励后更新activity，保证部分活动可以重新修改活动状态
    _update_one_activity(basic_data, data, activity, now)

    #获得奖励
    stepInfo = basic_data.activity_step_list.get(step_id)
    for hero_basic_id in stepInfo.get_heroes_basic_id():
        if not hero_business.gain_hero(data, hero_basic_id):
            return False

    items = stepInfo.get_items()
    if not item_business.gain_item(data, items, "activity reward", log_formater.ACTIVITY_REWARD):
        return False
    cost_gold = 0
    min_gold = 0
    max_gold = 0
    gold = stepInfo.gold
    if gold > 0:
        cost_gold = gold
    min_gold = stepInfo.value1
    max_gold = stepInfo.value2
    return (cost_gold, min_gold, max_gold)



def update_activity(basic_data, data, now):
    """更新所有活动信息
    """
    #涉及到跨天的数据统计，所以此处要更新所有跨天数据
    if not account_business.update_across_day_info(data, now):
        raise Exception("Update across day info failed")

    #遍历活动基础数据，若在有效期内而未添加的活动，进行创建
    basic_activities = basic_data.activity_list.get_all()
    for basic_activity in basic_activities:
        activity_id = ActivityInfo.generate_id(data.id, basic_activity.id)
        if (data.activity_list.get(activity_id) is None and 
            basic_activity.is_living(now)):
            #应有的活动未被创建
            basic_steps = get_basic_activity_steps(basic_data, basic_activity)
            if not add_activity(basic_data, data, basic_activity.id, basic_activity, basic_steps):
                raise Exception("Update activity and add new activity failed")

    delete = []
    for activity in data.activity_list.get_all():
        if _update_one_activity(basic_data, data, activity, now):
            delete.append(activity)

    for activity in delete:
        if data.activity_list.get(activity.id) is not None:
            try:
                data.activity_list.delete(activity.id)
            except:
                pass

    return True


def _update_one_activity(basic_data, data, activity, now):
    """更新一个活动
    Return:
        bool: 是否需要删除
    """
    #不合法，删除
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    if basic_activity is None:
        logger.debug("basic activity has gone[basic_activity_id=%d]" % activity.basic_id)
        return True

    if ActivityPool().is_invalid(basic_data, data, activity, now):
        return True

    #不再有效期内（可能是未开启），do nothing
    if not activity.is_living(now, basic_activity.style_id):
        return False

    #更新完成度
    ActivityPool().update(basic_data, data, activity, now)
    return False


def _is_activity_invalid_for_shop(basic_data, data, activity, now):
    """商铺活动需要对终生卡做特殊处理
    """
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    basic_steps = get_basic_activity_steps(basic_data, basic_activity)
    #判断是否为终生卡
    if basic_steps[0].items_id == "502":
        pay = data.pay.get()
        if pay.has_card(4):
            return True

    #其他情况
    return _is_activity_invalid(basic_data, data, activity, now)
        
    
    
def _is_activity_invalid(basic_data, data, activity, now):
    """是否非法
    """
    if activity.has_time_limit():
        #有时间限制：超时，活动非法
        return activity.is_timeout(now)
    else:
        #无时间限制：领取玩所有奖励后，活动非法
        return activity.is_accept_all()


def _update_activity_firstpay(basic_data, data, activity, now):
    """更新首次充值活动的完成度
    """
    pay = data.pay.get(True)
    if pay.pay_amount >= 6:
        value = 1
    else:
        value = 0

    basic_activity = basic_data.activity_list.get(activity.basic_id)

    activity.forward_all(basic_activity, value, now)


def _update_activity_login(basic_data, data, activity, now):
    """更新七日签到活动的完成度
    """
    basic_activity = basic_data.activity_list.get(activity.basic_id)

    if not utils.is_same_day(activity.forward_time, now):
        next_step_id = activity.get_next_step_id_unaccepted(basic_activity)
        if next_step_id != 0:
            activity.forward(basic_activity, next_step_id, 1, now)


def _is_activity_funds_valid(basic_data, data, activity, now):
    """成长基金活动是否非法
    """
    #用户超过30级，且未购买基金
    user = data.user.get(True)
    if user.level >= FUNDS_USER_LEVEL_LIMIT and not activity.is_unlocked():
        return True

    #领取完所有奖励后，不合法
    return activity.is_accept_all()


def _update_activity_funds(basic_data, data, activity, now):
    """更新成长基金活动的完成度
    """
    user = data.user.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, user.level, now)


def _operate_activity_funds(basic_data, data, activity, op_type, op_input, step_id, now):
    """购买成长基金
    """
    #超过30级，不允许购买
    user = data.user.get(True)
    if user.level >= FUNDS_USER_LEVEL_LIMIT:
        logger.warning("User level invalid[level=%d]" % user.level)
        return False
    if user.vip_level < FUNDS_VIP_LEVEL_LIMIT:
        logger.warning("User vip level invalid[vip_level=%d]" % user.vip_level)
        return False

    resource = data.resource.get()
    original_gold = resource.gold
    gold = 1000
    if not resource.cost_gold(gold):
        return False

    #解锁基金
    activity.unlock_all_reward()

    log = log_formater.output_gold(data, -gold, log_formater.BUY_FUNDS,
            "Buy funds by gold", before_gold = original_gold, activity = activity.basic_id)
    logger.notice(log)
    return True


def _update_activity_pay(basic_data, data, activity, now):
    """更新充值奖励活动的完成度
    """
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    pay_record_list = data.pay_record_list.get_all(True)
    total_pay_price = 0
    for pay_record in pay_record_list:
        if pay_record.is_finish and activity.is_living(pay_record.time, basic_activity.style_id):
            total_pay_price += pay_record.price

    activity.forward_all(basic_activity, int(total_pay_price), now)


def _update_activity_shop(basic_data, data, activity, now):
    """更新神秘商店活动的完成度
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)


def _operate_activity_shop(basic_data, data, activity, op_type, op_input, step_id, now):
    """购买物品
    """
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    step_info = basic_data.activity_step_list.get(step_id)

    resource = data.resource.get()
    original_gold =  resource.gold
    if not resource.cost_gold(step_info.value1):
        return False
    log = log_formater.output_gold(data, -step_info.value1, log_formater.OPERATE_ACTIVITY_SHOP,
                "operate activity shop by gold", before_gold = original_gold)
    logger.notice(log)

    #改变进度
    activity.forward(basic_activity, step_id, 1, now)
    return True


def _update_activity_cost_gold(basic_data, data, activity, now):
    """更新限时消耗元宝活动完成度
    """
    resource = data.resource.get(True)
    basic_activity = basic_data.activity_list.get(activity.basic_id)

    weekly_use_gold = utils.split_to_int(resource.six_days_ago_use_gold)

    total_use_gold = 0

    if activity.is_living(now, basic_activity.style_id):
        total_use_gold = resource.daily_use_gold

    for index in range(0, len(weekly_use_gold)):
        if activity.is_living(now - (index + 1) * 86400, basic_activity.style_id):
            total_use_gold += weekly_use_gold[index] 
    
    activity.forward_all(basic_activity, int(total_use_gold), now)


def _update_activity_cost_energy(basic_data, data, activity, now):
    """更新限时消耗政令活动完成度
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    energy = data.energy.get(True)
    
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, energy.daily_use_energy, now)


def _update_activity_pay_once(basic_data, data, activity, now):
    """更新限时单次充值返利活动完成度
    """
    pay_record_list = data.pay_record_list.get_all(True)
    step_status = activity.get_reward_status()
    step_target = activity.get_step_target()

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    steps_id = basic_activity.get_steps()

    for step_index in range(0, len(step_status)):
        step_id = steps_id[step_index]
        step_pay_price = basic_data.activity_step_list.get(step_id).value2

        progress = 0
        for pay_record in pay_record_list:
            if activity.is_living(pay_record.time, basic_activity.style_id):
                if pay_record.is_finish and pay_record.price == step_pay_price:
                    progress += 1
        activity.forward(basic_activity, step_id, progress, now)

        if step_status[step_index] == activity.REWARD_ACCEPTED:
            #重制领取过的任务，并将target加1
            activity.update_target(basic_activity, step_id, step_target[step_index] + 1)
            activity.reset_reward(basic_activity, step_id)


def _update_activity_hero(basic_data, data, activity, now):
    """更新拍卖武将活动积分
    """
    pass

def _update_activity_exploit(basic_data, data, activity, now):
    """开采次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)
    progress = trainer.daily_finish_tax_num + trainer.daily_finish_farm_num +\
            trainer.daily_finish_mining_num + trainer.daily_finish_gold_num

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, progress, now)


def _update_activity_jungle(basic_data, data, activity, now):
    """山贼战斗次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, trainer.dnode_daily_win, now)


def _update_activity_arena(basic_data, data, activity, now):
    """演武战斗次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, trainer.daily_arena_num, now)


def _update_activity_key_node(basic_data, data, activity, now):
    """掠夺或占领战斗次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, trainer.knode_daily_win, now)


def _update_activity_choose_card(basic_data, data, activity, now):
    """祈福翻牌子次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, trainer.daily_choose_card_num, now)


def _update_activity_buy_goods(basic_data, data, activity, now):
    """各种商店购买次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)
    progress = trainer.daily_buy_goods_in_wineshop + trainer.daily_buy_goods_in_achievement_shop + \
            trainer.daily_buy_goods_in_legendcity_shop + trainer.daily_buy_goods_in_union_shop

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, progress, now)


def _update_activity_search(basic_data, data, activity, now): 
    """搜索次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    draw = data.draw.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, draw.daily_money_draw_num + draw.daily_gold_draw_num, now)

def _update_activity_treasure(basic_data, data, activity, now):
    """夺宝次数
    """
   # if not utils.is_same_day(activity.forward_time, now):
   #     basic_activity = basic_data.activity_list.get(activity.basic_id)
   #     basic_steps = get_basic_activity_steps(basic_data, basic_activity)
   #     activity.reset(basic_activity, basic_steps)

   # draw = data.draw.get(True)

   # basic_activity = basic_data.activity_list.get(activity.basic_id)

   # activity.forward_all(basic_activity, draw.total_treasure_draw_num, now)
    pass


def _update_activity_offline_event(basic_data, data, activity, now): 
    """离线事件次数
    """
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)
    progress = trainer.daily_finish_search_num + trainer.daily_finish_deep_mining_num + \
            trainer.daily_finish_hermit_num

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    
    activity.forward_all(basic_activity, progress, now)


def _update_activity_worldboss_merit(basic_data, data, activity, now):
    """世界boss战功活动
    """
    worldboss = data.worldboss.get(True)
    user = data.user.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    steps_id = basic_activity.get_steps()
    targets = activity.get_step_target()
    
    if targets[0] == 0:
        #特殊逻辑，战功的target为0，玩家根据自己主公等级配置target
        key = user.level
        if not data_loader.WorldBossTaget_dict.has_key(key):
            key = min(data_loader.WorldBossTaget_dict.keys())
        new_targets = data_loader.WorldBossTaget_dict[key].target
        for index in range(0, len(targets)):
            activity.update_target(basic_activity, steps_id[index], new_targets[index])

    activity.forward_all(basic_activity, worldboss.merit, now)


def _update_activity_worldboss_ranking(basic_data, data, activity, now):
    """世界boss排行榜活动
    """
    worldboss = data.worldboss.get(True)
    user = data.user.get(True)

    if not worldboss.is_unlock():
        return

    if worldboss.is_arised() and worldboss.is_battle_time_passed(now):
        #世界打完了才能解锁
        activity.unlock_all_reward()
    else:
        return

    #获得玩家自己的排名
    rankings = []
    _get_worldboss_ranking(data.id, rankings)
    rank = rankings[0]
    logger.warning("worldboss ranking[self_rank=%d]" % rank)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    steps_id = basic_activity.get_steps()
    for step_id in steps_id:
        basic_activity_step = basic_data.activity_step_list.get(step_id)

        #击杀者奖励
        if basic_activity_step.value1 == 0 and basic_activity_step.value2 == 0:
            if worldboss.is_killer(user.id):
                activity.forward(basic_activity, step_id, 1, now)

        if basic_activity_step.value1 <= rank and rank <= basic_activity_step.value2:
            activity.forward(basic_activity, step_id, 1, now)


def operate_activity(basic_data, data, activity_basic_id, activity_step_id, op_type, op_input, now):
    """特殊处理
    """
    activity_id = ActivityInfo.generate_id(data.id, activity_basic_id)
    activity = data.activity_list.get(activity_id)

    if not ActivityPool().operate(basic_data,
            data, activity, op_type, op_input, activity_step_id, now):
        return False

    _update_one_activity(basic_data, data, activity, now)
    return True


def _get_worldboss_ranking(user_id, rankings):
    proxy = DataProxy()
    proxy.search_ranking("worldboss", "merit", user_id)   #查玩家自己的排名
    defer = proxy.execute()
    defer.addCallback(_calc_get_worldboss_ranking, user_id, rankings)
    return defer


def _calc_get_worldboss_ranking(proxy, user_id, rankings):
    self_ranking = proxy.get_ranking("worldboss", "merit", user_id) + 1
    rankings.append(self_ranking)
    return True


def get_activity_hero_award(basic_data, hero_basic_id, rank):
    """拍卖英雄活动的奖励
    """
    id = BasicActivityHeroRewardInfo.generate_id(hero_basic_id, rank)
    reward = basic_data.activity_hero_reward_list.get(id)
    items = reward.get_items()

    return items



def add_init_basic_activity(basic_data, id_list):
    """添加初始的活动id
    """
    init = basic_data.init.get()
    activity_list = basic_data.activity_list.get_all()
    
    #验证要添加的id是否在所有activity列表中
    for new_id in id_list:
        activity = basic_data.activity_list.get(new_id)
        if activity is None:
            logger.warning("Add a not exist activity[add_id=%d]" % new_id)
            return False

    init.add_init_activities(id_list)

    return True


def delete_init_basic_activity(basic_data, id_list):
    """删除初始的活动id
    """
    init = basic_data.init.get()
    
    init.delete_init_activities(id_list)

    return True



def add_basic_activity(basic_data, basic_id, activities):
    """添加活动的基础信息
       activity:
         (id, type_id, start_time, end_time, start_day, end_day, icon_name, 
             name, description, hero_basic_id, list(steps)) 十一元组
    """
    for add_activity in activities:
        id = add_activity[0]
        style_id = add_activity[1]
        type_id = add_activity[2]
        start_time = add_activity[3]
        end_time = add_activity[4]
        start_day = add_activity[5]
        end_day = add_activity[6]
        icon_name = add_activity[7]
        name = add_activity[8]
        description = add_activity[9]
        hero_basic_id = add_activity[10]
        steps_id = add_activity[11]
        weight = add_activity[12]
        
        #验证step是否都存在
        for step_id in steps_id:
            step = basic_data.activity_step_list.get(step_id)
            if step is None:
                logger.warning("not exist activity step[id=%d]" % step_id)
                return False

        activity = basic_data.activity_list.get(id)
        if activity is None:
            activity = BasicActivityInfo.create(id, basic_id)
            basic_data.activity_list.add(activity)
        activity.update(style_id, type_id, start_time, end_time, start_day, end_day,
                icon_name, name, description, hero_basic_id, steps_id, weight)   

    return True


def delete_basic_activity(basic_data, id_list):
    """删除活动的基础信息
    """
    id_list = list(set(id_list))
    for id in id_list:
        activity = basic_data.activity_list.get(id)
        if activity is not None:
            basic_data.activity_list.delete(id)
    
    return True


def get_delete_steps_of_delete_activities(basic_data, delete_activities_id):
    """获取欲删除活动的可以删除的step
       （只能删除不与其他活动共用的step）
    """
    basic_activities = basic_data.activity_list.get_all()

    delete_steps_id = []
    for id in delete_activities_id:
        basic_activity = basic_data.activity_list.get(id)
        if basic_activity is None:
            logger.warning("not exist basic activity[id=%d]" % id)
            continue

        delete_steps_id = delete_steps_id + basic_activity.get_steps()
    delete_steps_id = list(set(delete_steps_id))

    #step数据可能公用,只能删除只在要删的activity中出现的steps
    not_delete_steps_id = []
    for basic_activity in basic_activities:
        if basic_activity.id not in delete_activities_id:
            steps = basic_activity.get_steps()
            for step in steps:
                if step in delete_steps_id:
                    not_delete_steps_id.append(step)

    delete_steps_id = list(set(delete_steps_id) ^ set(not_delete_steps_id))

    return delete_steps_id


def add_basic_activity_step(basic_data, basic_id, steps):
    """添加活动step的基础信息
       step:
         (id, target, default_lock, list(heroes_basic_id), list(items_id), list(items_num),
             gold, value1, value2, description) 十元组
    """
    for add_step in steps:
        id = add_step[0]
        target = add_step[1]
        default_lock = add_step[2]
        heroes_basic_id = add_step[3]
        items_id = add_step[4]
        items_num = add_step[5]
        gold = add_step[6]
        value1 = add_step[7]
        value2 = add_step[8]
        description = add_step[9]

        step = basic_data.activity_step_list.get(id)
        if step is None:
            step = BasicActivityStepInfo.create(id, basic_id)
            basic_data.activity_step_list.add(step)
        step.update(target, default_lock, heroes_basic_id, items_id, items_num, gold,
                description, value1, value2)   

    return True


def delete_basic_activity_step(basic_data, id_list):
    """删除活动step的基础信息
    """
    id_list = list(set(id_list))
    for id in id_list:
        step = basic_data.activity_step_list.get(id)
        if step is not None:
            basic_data.activity_step_list.delete(id)
    
    return True


def add_basic_activity_hero_reward(basic_data, basic_id, rewards):
    """添加限时搜索英雄奖励的基础信息
       reward:      
         (id, level, list(items_id), list(items_num))四元组
    """
    for add_reward in rewards:
        original_id = add_reward[0]
        level = add_reward[1]

        id = BasicActivityHeroRewardInfo.generate_id(original_id, level)
        items_id = add_reward[2]
        items_num = add_reward[3]

        reward = basic_data.activity_hero_reward_list.get(id)
        if reward is None:
            reward = BasicActivityHeroRewardInfo.create(original_id, basic_id, level, 0)
            basic_data.activity_hero_reward_list.add(reward)
        reward.update(level, items_id, items_num, 0)

    return True

def add_basic_activity_treasure_reward(basic_data, basic_id, rewards):
    """添加转盘奖励的基础信息
       reward:      
         (id, level, list(items_id), list(items_num), weight)四元组
    """
    for add_reward in rewards:
        original_id = add_reward[0]
        level = add_reward[1]

        id = BasicActivityHeroRewardInfo.generate_id(original_id, level)
        items_id = add_reward[2]
        items_num = add_reward[3]
        weight = add_reward[4]
        
        reward = basic_data.activity_hero_reward_list.get(id)
        if reward is None:
            reward = BasicActivityHeroRewardInfo.create(original_id, basic_id, level, weight)
            basic_data.activity_hero_reward_list.add(reward)
        reward.update(level, items_id, items_num, weight)   

    return True


def delete_basic_activity_hero_reward(basic_data, id_list, level_list):
    """删除限时搜索英雄奖励的基础信息
    """
    if len(id_list) != len(level_list):
        return False

    for i in range(len(id_list)):
        id = BasicActivityHeroRewardInfo.generate_id(id_list[i], level_list[i])

        reward = basic_data.activity_hero_reward_list.get(id)
        if reward is not None:
            basic_data.activity_hero_reward_list.delete(id)
    
    return True


def eliminate_invalid_basic_activities(basic_data, now):
    """删除过期的活动基础数据
    """
    basic_activities = basic_data.activity_list.get_all()
    basic_init = basic_data.init.get()

    delete_activities_id = []
    for basic_activity in basic_activities:
        if basic_activity.is_invalid(now):
            delete_activities_id.append(basic_activity.id)

    delete_steps_id = get_delete_steps_of_delete_activities(basic_data, delete_activities_id)

    logger.notice("eliminate invalide basic acitivities[ids=%s]" % utils.join_to_string(delete_activities_id))
    logger.notice("eliminate invalide basic steps[ids=%s]" % utils.join_to_string(delete_steps_id))

    delete_basic_activity(basic_data, delete_activities_id)
    delete_basic_activity_step(basic_data, delete_steps_id)
    delete_init_basic_activity(basic_data, delete_activities_id)


def _operate_activity_discount(basic_data, data, activity, op_type, op_input, step_id, now):
    """购买优惠商品"""
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    step_info = basic_data.activity_step_list.get(step_id)

    #判断vip等级
    user = data.user.get(True)
    if user.vip_level < step_info.value2:
        return False

    resource = data.resource.get()
    original_gold = resource.gold
    if not resource.cost_gold(step_info.value1):
        return False
    log = log_formater.output_gold(data, -step_info.value1, log_formater.OPERATE_ACTIVITY_DISCOUNT,
                "operate activity discount by gold", before_gold = original_gold)
    logger.notice(log)
    #改变进度
    activity.forward(basic_activity, step_id, 1, now)
    return True

def _update_activity_discount(basic_data, data, activity, now):
    """更新"""
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

def _update_activity_pay_day_num(basic_data, data, activity, now):
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    pay_record_list = data.pay_record_list.get_all(True)
    step_status = activity.get_reward_status()
    step_target = activity.get_step_target()
    pay_day_index = []
    for pay_record in pay_record_list:
        if pay_record.is_finish and activity.is_living(pay_record.time, basic_activity.style_id):
            pay_day_index.append(int((pay_record.time - activity.start_time) / 86400) + 1)

    pay_day_index = set(pay_day_index)
    activity.forward_all(basic_activity, len(pay_day_index), now)

def _update_activity_pay_daily(basic_data, data, activity, now):
    if not utils.is_same_day(activity.forward_time, now):
        basic_activity = basic_data.activity_list.get(activity.basic_id)
        basic_steps = get_basic_activity_steps(basic_data, basic_activity)
        activity.reset(basic_activity, basic_steps)

    trainer = data.trainer.get(True)
    progress = trainer.buy_daily_discount
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    activity.forward_all(basic_activity, progress, now)

def _update_activity_invite(basic_data, data, activity, now):
    basic_activity = basic_data.activity_list.get(activity.basic_id)
    step_ids = basic_activity.get_steps()
    user = data.user.get(True)
    invitee_levels = utils.split_to_int(user.invitee_level)
    for step_id in step_ids:
        step_info = basic_data.activity_step_list.get(step_id)
        progress = 0
        #接受邀请的活动
        if step_info.value2 > 0:
            if user.is_invited():
                progress = 1
        else: #邀请别人的活动
            for level in invitee_levels:
                if level >= step_info.value1:
                    progress += 1
        activity.forward(basic_activity, step_id, progress, now)

def _update_fortune_cat(basic_data, data, activity, now):
    """招财猫
    """
   # if not utils.is_same_day(activity.forward_time, now):
   #     basic_activity = basic_data.activity_list.get(activity.basic_id)
   #     basic_steps = get_basic_activity_steps(basic_data, basic_activity)
   #     activity.reset(basic_activity, basic_steps)

    user = data.user.get(True)

    basic_activity = basic_data.activity_list.get(activity.basic_id)
    activity.forward_all(basic_activity, user.vip_level, now)
    pass

