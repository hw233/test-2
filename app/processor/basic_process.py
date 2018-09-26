#coding:utf8
"""
Created on 2016-09-30
@Author: zhoubin(zhoubin@ice-time.cn)
@Brief : 基础数据相关处理逻辑
"""

import base64
from firefly.server.globalobject import GlobalObject
from utils import logger
from utils import utils
from utils.timer import Timer
from proto import activity_pb2
from proto import internal_pb2
from proto import boss_pb2
from datalib.data_loader import data_loader
from datalib.global_data import DataBase
from app import basic_view
from app import pack
from app import compare
from app import log_formater
from app.business import activity as activity_business
from app.business import basic_init as basic_init_business
from app.business import worldboss as worldboss_business
from app.data.activity import ActivityInfo
from app.data.basic_activity_hero_reward import BasicActivityHeroRewardInfo


class BasicProcessor(object):
    """基础数据相关逻辑
    """

    def add_init_basic_activity(self, user_id, request):
        """添加初始活动id
        """
        timer = Timer(user_id)

        req = activity_pb2.AddInitBasicActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_add_init_basic_activity, req, timer)
        defer.addCallback(self._add_init_basic_activity_succeed, req, timer)
        defer.addErrback(self._add_init_basic_activity_failed, req, timer)
        return defer


    def _calc_add_init_basic_activity(self, basic_data, req, timer):
        """
        """
        if not activity_business.add_init_basic_activity(basic_data, req.activities_id):
            raise Exception("Add init basic activity failed")

        return DataBase().commit_basic(basic_data)


    def _add_init_basic_activity_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.AddInitBasicActivityRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Add init basic activity succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_init_basic_activity_failed(self, err, req, timer):
        """
        """
        logger.fatal("Add init basic activity failed[reason=%s]" % err)

        res = activity_pb2.AddInitBasicActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add init basic activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_init_basic_activity(self, user_id, request):
        """删除初始活动id
        """
        timer = Timer(user_id)

        req = activity_pb2.DeleteInitBasicActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_delete_init_basic_activity, req, timer)
        defer.addCallback(self._delete_init_basic_activity_succeed, req, timer)
        defer.addErrback(self._delete_init_basic_activity_failed, req, timer)
        return defer


    def _calc_delete_init_basic_activity(self, basic_data, req, timer):
        """
        """
        if not activity_business.delete_init_basic_activity(basic_data, req.activities_id):
            raise Exception("Delete init basic activity failed")

        return DataBase().commit_basic(basic_data)


    def _delete_init_basic_activity_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.DeleteInitBasicActivityRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete init basic activity succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_init_basic_activity_failed(self, err, req, timer):
        """
        """
        logger.fatal("Delete init basic activity failed[reason=%s]" % err)

        res = activity_pb2.DeleteInitBasicActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete init basic activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_init_basic_activity(self, user_id, request):
        """查询初始活动id
        """
        timer = Timer(user_id)

        req = activity_pb2.QueryInitBasicActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_query_init_basic_activity, req, timer)
        defer.addErrback(self._query_init_basic_activity_failed, req, timer)
        return defer


    def _calc_query_init_basic_activity(self, basic_data, req, timer):
        """
        """
        init = basic_data.init.get(True)
        activities_id = init.get_init_activities() 

        defer = DataBase().commit_basic(basic_data)
        defer.addCallback(self._query_init_basic_activity_succeed, activities_id, req, timer)
        return defer


    def _query_init_basic_activity_succeed(self, basic_data, activities_id, req, timer):
        """
        """
        res = activity_pb2.QueryInitBasicActivityRes()
        res.status = 0
        for id in activities_id:
            res.activities_id.append(id)

        response = res.SerializeToString()
        logger.notice("Query init basic activity succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_init_basic_activity_failed(self, err, req, timer):
        """
        """
        logger.fatal("Query init basic activity failed[reason=%s]" % err)

        res = activity_pb2.QueryInitBasicActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query init basic activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_basic_activity(self, user_id, request):
        """添加基础活动信息
        """
        timer = Timer(user_id)

        req = activity_pb2.AddBasicActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_add_basic_activity, req, timer)
        defer.addCallback(self._add_basic_activity_succeed, req, timer)
        defer.addErrback(self._add_basic_activity_failed, req, timer)
        return defer


    def _calc_add_basic_activity(self, basic_data, req, timer):
        """
        """
        activities = []
        for activity_msg in req.activities:
            activities.append(self._parse_activity_msg(activity_msg))

        if not activity_business.add_basic_activity(basic_data, basic_view.BASIC_ID, activities):
            raise Exception("Add basic activity failed")
        
        return DataBase().commit_basic(basic_data)


    def _parse_activity_msg(self, activity_msg):
        """解析 activity 配置信息
           Return:
               (id, type_id, start_time, end_time, start_day, end_day, icon_name, 
                 name, description, hero_basic_id, list(steps)) 十一元组
        """
        id = activity_msg.id
        type_id = activity_msg.type_id

        if activity_msg.HasField("style_id"):
            style_id = activity_msg.style_id
        else:
            style_id = 5  #5是普通活动

        if activity_msg.HasField("start_time"):
            start_time = activity_msg.start_time
        else:
            start_time = ""

        if activity_msg.HasField("end_time"):
            end_time = activity_msg.end_time
        else:
            end_time = ""

        if activity_msg.HasField("start_day"):
            start_day = activity_msg.start_day
        else:
            start_day = 0
 
        if activity_msg.HasField("end_day"):
            end_day = activity_msg.end_day
        else:
            end_day = 0

        if activity_msg.HasField("icon_name"):
            icon_name = activity_msg.icon_name
        else:
            icon_name = ""

        if activity_msg.HasField("name"):
            name = activity_msg.name
        else:
            name = ""

        if activity_msg.HasField("description"):
            description = activity_msg.description
        else:
            description = ""

        if activity_msg.HasField("hero_basic_id"):
            hero_basic_id = activity_msg.hero_basic_id
        else:
            hero_basic_id = 0
        
        if activity_msg.HasField("weight"):
            weight = activity_msg.weight
        else:
            weight = 0
        
        steps_id = []
        for step_id in activity_msg.steps_id:
            steps_id.append(step_id)

        return (id, style_id, type_id, start_time, end_time, start_day, end_day, 
                icon_name, name, description, hero_basic_id, steps_id, weight)


    def _add_basic_activity_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.AddBasicActivityRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Add basic activity succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_basic_activity_failed(self, err, req, timer):
        """
        """
        logger.fatal("Add basic activity failed[reason=%s]" % err)

        res = activity_pb2.AddBasicActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add basic activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_basic_activity(self, user_id, request):
        """删除活动基础信息
        """
        timer = Timer(user_id)

        req = activity_pb2.DeleteBasicActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_delete_basic_activity, req, timer)
        defer.addCallback(self._delete_basic_activity_succeed, req, timer)
        defer.addErrback(self._delete_basic_activity_failed, req, timer)
        return defer


    def _calc_delete_basic_activity(self, basic_data, req, timer):
        """1.删除活动基础数据
           2.删除该活动step数据
           （若step数据与其他活动共用，则不删除）
           3.将该活动从init中删去
        """
        delete_steps_id = activity_business.get_delete_steps_of_delete_activities(
            basic_data, req.ids)

        if not activity_business.delete_basic_activity_step(basic_data, delete_steps_id):
            raise Exception("Delete basic activity step failed")

        if not activity_business.delete_basic_activity(basic_data, req.ids):
            raise Exception("Delete basic activity failed")
    
        activity_business.delete_init_basic_activity(basic_data, req.ids)

        logger.notice("delete basic acitivities[ids=%s]" % utils.join_to_string(req.ids))
        logger.notice("delete basic steps[ids=%s]" % utils.join_to_string(delete_steps_id))

        return DataBase().commit_basic(basic_data)


    def _delete_basic_activity_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.DeleteBasicActivityRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete basic activity succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_basic_activity_failed(self, err, req, timer):
        """
        """
        logger.fatal("Delete basic activity failed[reason=%s]" % err)

        res = activity_pb2.DeleteBasicActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete basic activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_basic_activity(self, user_id, request):
        """查询活动的基本信息
        """
        timer = Timer(user_id)

        req = activity_pb2.QueryBasicActivityReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_query_basic_activity, req, timer)
        defer.addErrback(self._query_basic_activity_failed, req, timer)
        return defer


    def _calc_query_basic_activity(self, basic_data, req, timer):
        """
        """
        activity_business.eliminate_invalid_basic_activities(basic_data, timer.now)

        activities = []
        for id in req.ids:
            activity = basic_data.activity_list.get(id)
            if activity is not None:
                activities.append(activity)

        if req.HasField("is_all"):
            if req.is_all:
                activities = basic_data.activity_list.get_all()

        with_detail = False
        if req.HasField("with_detail"):
            with_detail = req.with_detail
            
        defer = DataBase().commit_basic(basic_data)
        defer.addCallback(self._query_basic_activity_succeed, activities, with_detail, req, timer)
        return defer


    def _query_basic_activity_succeed(self, basic_data, activities, with_detail, req, timer):
        """
        """
        res = activity_pb2.QueryBasicActivityRes()
        res.status = 0
        for activity in activities:
            msg = res.activities.add()
            pack.pack_basic_activity_info(activity, msg, timer.now)
            
            if with_detail:
                #steps
                steps_id = activity.get_steps()
                for step_id in steps_id:
                    step = basic_data.activity_step_list.get(step_id)
                    if step is None:
                        logger.warning("not exist activity step[id=%d]" % step_id)
                        continue
                    pack.pack_basic_activity_step_info(step, msg.steps_info.add(), timer.now)

                #rewards
                if activity.hero_basic_id != 0:
                    rewards_id = BasicActivityHeroRewardInfo.generate_all_ids(
                        activity.hero_basic_id)
                    for reward_id in rewards_id:
                        reward = basic_data.activity_hero_reward_list.get(reward_id)
                        if reward is None:
                            logger.warning("not exist activity hero reward[id=%d]" % reward_id)
                            continue
                        pack.pack_basic_hero_reward_info(reward, 
                            msg.hero_rewards_info.add(), timer.now)
                
        response = res.SerializeToString()
        logger.notice("Query basic activity succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_basic_activity_failed(self, err, req, timer):
        """
        """
        logger.fatal("Query basic activity failed[reason=%s]" % err)

        res = activity_pb2.QueryBasicActivityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query basic activity failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def add_basic_activity_step(self, user_id, request):
        """添加基础活动step的信息
        """
        timer = Timer(user_id)

        req = activity_pb2.AddBasicActivityStepReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_add_basic_activity_step, req, timer)
        defer.addCallback(self._add_basic_activity_step_succeed, req, timer)
        defer.addErrback(self._add_basic_activity_step_failed, req, timer)
        return defer


    def _calc_add_basic_activity_step(self, basic_data, req, timer):
        """
        """
        if not basic_data.is_valid():
            basic_init_business.create_basic_init(basic_data, basic_view.BASIC_ID)

        steps = []
        for step_msg in req.steps:
            steps.append(self._parse_activity_step_msg(step_msg))

        if not activity_business.add_basic_activity_step(basic_data, basic_view.BASIC_ID, steps):
            raise Exception("Add basic activity step failed")

        return DataBase().commit_basic(basic_data)


    def _parse_activity_step_msg(self, step_msg):
        """解析 activity_step 配置信息
           Return:
               (id, target, default_lock, list(heroes_basic_id), list(items_id), list(items_num),
               gold, value1, value2, description) 十元组
        """
        id = step_msg.id
        
        if step_msg.HasField("target"):
            target = step_msg.target
        else:
            target = 0

        if step_msg.HasField("default_lock"):
            default_lock = step_msg.default_lock
        else:
            default_lock = False

        heroes_basic_id = []
        for basic_id in step_msg.heroes_basic_id:
            heroes_basic_id.append(basic_id)

        items_id = []
        items_num = []
        for item in step_msg.reward_items:
            items_id.append(item.basic_id)
            items_num.append(item.num)

        if step_msg.HasField("gold"):
            gold = step_msg.gold
        else:
            gold = 0

        if step_msg.HasField("value1"):
            value1 = step_msg.value1
        else:
            value1 = 0

        if step_msg.HasField("value2"):
            value2 = step_msg.value2
        else:
            value2 = 0

        if step_msg.HasField("description"):
            description = step_msg.description
        else:
            description = ""

        return (id, target, default_lock, heroes_basic_id, items_id, items_num,
                gold, value1, value2, description)  


    def _add_basic_activity_step_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.AddBasicActivityStepRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Add basic activity step succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_basic_activity_step_failed(self, err, req, timer):
        """
        """
        logger.fatal("Add basic activity step failed[reason=%s]" % err)

        res = activity_pb2.AddBasicActivityStepRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add basic activity step failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_basic_activity_step(self, user_id, request):
        """删除活动 step 基础信息
        """
        timer = Timer(user_id)

        req = activity_pb2.DeleteBasicActivityStepReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_delete_basic_activity_step, req, timer)
        defer.addCallback(self._delete_basic_activity_step_succeed, req, timer)
        defer.addErrback(self._delete_basic_activity_step_failed, req, timer)
        return defer


    def _calc_delete_basic_activity_step(self, basic_data, req, timer):
        """
        """
        if not activity_business.delete_basic_activity_step(basic_data, req.ids):
            raise Exception("Delete basic activity step failed")

        return DataBase().commit_basic(basic_data)


    def _delete_basic_activity_step_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.DeleteBasicActivityStepRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete basic activity step succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_basic_activity_step_failed(self, err, req, timer):
        """
        """
        logger.fatal("Delete basic activity step failed[reason=%s]" % err)

        res = activity_pb2.DeleteBasicActivityStepRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete basic activity step failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_basic_activity_step(self, user_id, request):
        """查询活动step的基本信息
        """
        timer = Timer(user_id)

        req = activity_pb2.QueryBasicActivityStepReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_query_basic_activity_step, req, timer)
        defer.addErrback(self._query_basic_activity_step_failed, req, timer)
        return defer


    def _calc_query_basic_activity_step(self, basic_data, req, timer):
        """
        """
        steps = []
        for id in req.ids:
            step = basic_data.activity_step_list.get(id)
            if step is not None:
                steps.append(step)

        if req.HasField("is_all"):
            if req.is_all:
                steps = basic_data.activity_step_list.get_all()

        defer = DataBase().commit_basic(basic_data)
        defer.addCallback(self._query_basic_activity_step_succeed, steps, req, timer)
        return defer


    def _query_basic_activity_step_succeed(self, basic_data, steps, req, timer):
        """
        """
        res = activity_pb2.QueryBasicActivityStepRes()
        res.status = 0
        for step in steps:
            msg = res.steps.add()
            pack.pack_basic_activity_step_info(step, msg, timer.now)
        
        response = res.SerializeToString()
        logger.notice("Query basic activity step succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_basic_activity_step_failed(self, err, req, timer):
        """
        """
        logger.fatal("Query basic activity step failed[reason=%s]" % err)

        res = activity_pb2.QueryBasicActivityStepRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query basic activity step failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def add_basic_activity_hero_reward(self, user_id, request):
        """添加限时英雄活动奖励的基础信息
        """
        timer = Timer(user_id)

        req = activity_pb2.AddBasicActivityHeroRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_add_basic_activity_hero_reward, req, timer)
        defer.addCallback(self._add_basic_activity_hero_reward_succeed, req, timer)
        defer.addErrback(self._add_basic_activity_hero_reward_failed, req, timer)
        return defer


    def _calc_add_basic_activity_hero_reward(self, basic_data, req, timer):
        """
        """
        rewards = []
        for reward_msg in req.rewards:
            rewards.append(self._parse_activity_hero_reward_msg(reward_msg))
        logger.notice("rewards=%s"%rewards)
        if not activity_business.add_basic_activity_hero_reward(basic_data, 
                basic_view.BASIC_ID, rewards):
            raise Exception("Add basic activity hero reward failed")

        return DataBase().commit_basic(basic_data)


    def _parse_activity_hero_reward_msg(self, reward_msg):
        """解析 activity_hero_reward 配置信息
           Return:
               (id, level, list(items_id), list(items_num))四元组
        """
        id = reward_msg.id
        level = reward_msg.level
        items_id = []
        items_num = []
        for item in reward_msg.reward_items:
            items_id.append(item.basic_id)
            items_num.append(item.num)
        return (id, level, items_id, items_num)


    def _add_basic_activity_hero_reward_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.AddBasicActivityHeroRewardRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Add basic activity hero reward succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_basic_activity_hero_reward_failed(self, err, req, timer):
        """
        """
        logger.fatal("Add basic activity hero reward failed[reason=%s]" % err)

        res = activity_pb2.AddBasicActivityHeroRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add basic activity hero reward failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_basic_activity_hero_reward(self, user_id, request):
        """删除限时英雄活动奖励的基础信息
        """
        timer = Timer(user_id)

        req = activity_pb2.DeleteBasicActivityHeroRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_delete_basic_activity_hero_reward, req, timer)
        defer.addCallback(self._delete_basic_activity_hero_reward_succeed, req, timer)
        defer.addErrback(self._delete_basic_activity_hero_reward_failed, req, timer)
        return defer


    def _calc_delete_basic_activity_hero_reward(self, basic_data, req, timer):
        """
        """
        if not activity_business.delete_basic_activity_hero_reward(basic_data, req.ids, req.levels):
            raise Exception("Delete basic activity hero reward failed")

        return DataBase().commit_basic(basic_data)


    def _delete_basic_activity_hero_reward_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.DeleteBasicActivityHeroRewardRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete basic activity hero reward succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_basic_activity_hero_reward_failed(self, err, req, timer):
        """
        """
        logger.fatal("Delete basic activity hero reward failed[reason=%s]" % err)

        res = activity_pb2.DeleteBasicActivityHeroRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete basic activity hero reward failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_basic_activity_hero_reward(self, user_id, request):
        """查询限时英雄活动奖励的基本信息
        """
        timer = Timer(user_id)

        req = activity_pb2.QueryBasicActivityHeroRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_query_basic_activity_hero_reward, req, timer)
        defer.addErrback(self._query_basic_activity_hero_reward_failed, req, timer)
        return defer


    def _calc_query_basic_activity_hero_reward(self, basic_data, req, timer):
        """
        """
        rewards = []
        for id in req.ids:
            reward = basic_data.activity_hero_reward_list.get(id)
            if reward is not None:
                rewards.append(reward)

        if req.HasField("is_all"):
            if req.is_all:
                rewards = basic_data.activity_hero_reward_list.get_all()

        defer = DataBase().commit_basic(basic_data)
        defer.addCallback(self._query_basic_activity_hero_reward_succeed, rewards, req, timer)
        return defer


    def _query_basic_activity_hero_reward_succeed(self, basic_data, rewards, req, timer):
        """
        """
        res = activity_pb2.QueryBasicActivityHeroRewardRes()
        res.status = 0
        for reward in rewards:
            msg = res.rewards.add()
            pack.pack_basic_hero_reward_info(reward, msg, timer.now)

        response = res.SerializeToString()
        logger.notice("Query basic activity hero reward succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_basic_activity_hero_reward_failed(self, err, req, timer):
        """
        """
        logger.fatal("Query basic activity hero reward failed[reason=%s]" % err)

        res = activity_pb2.QueryBasicActivityHeroRewardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query basic activity hero reward failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def delete_basic_info(self, user_id, request):
        """删除basic基础数据
        """
        timer = Timer(user_id)

        req = internal_pb2.DeleteBasicInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_delete_basic_info, req, timer)
        defer.addErrback(self._delete_basic_info_failed, req, timer)
        return defer


    def _calc_delete_basic_info(self, basic_data, req, timer):
        """
        """
        basic_data.delete()

        defer = DataBase().commit_basic(basic_data)
        defer.addCallback(self._delete_basic_info_succeed, req, timer)
        return defer


    def _delete_basic_info_succeed(self, basic_data, req, timer):
        """
        """
        res = internal_pb2.DeleteBasicInfoRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete basic info succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_basic_info_failed(self, err, req, timer):
        """
        """
        logger.fatal("Delete basic info failed[reason=%s]" % err)

        res = internal_pb2.DeleteBasicInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete basic info failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

        


    def add_basic_worldboss(self, user_id, request):
        """添加基础世界boss信息
        """
        timer = Timer(user_id)

        req = boss_pb2.AddBasicWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_add_basic_worldboss, req, timer)
        defer.addCallback(self._add_basic_worldboss_succeed, req, timer)
        defer.addErrback(self._add_basic_worldboss_failed, req, timer)
        return defer


    def _calc_add_basic_worldboss(self, basic_data, req, timer):
        """
        """
        bosses = []
        for boss_msg in req.bosses:
            bosses.append(self._parse_worldboss_msg(boss_msg))

        if not worldboss_business.add_basic_worldboss(basic_data, basic_view.BASIC_ID, bosses):
            raise Exception("Add basic worldboss failed")
        
        return DataBase().commit_basic(basic_data)


    def _parse_worldboss_msg(self, boss_msg):
        """解析 worldboss 配置信息
           Return:
             (id, boss_id, date, start_time, end_time, description,
             total_soldier_num, list(arrays_id)) 八元组
        """
        id = boss_msg.id
        boss_id = boss_msg.boss_id
        
        if boss_msg.HasField("date"):
            date = boss_msg.date
        else:
            date = ""

        if boss_msg.HasField("start_time"):
            start_time = boss_msg.start_time
        else:
            start_time = ""
 
        if boss_msg.HasField("end_time"):
            end_time = boss_msg.end_time
        else:
            end_time = ""

        if boss_msg.HasField("description"):
            description = boss_msg.description
        else:
            description = ""

        if boss_msg.HasField("total_soldier_num"):
            total_soldier_num = boss_msg.total_soldier_num
        else:
            total_soldier_num = 1000
        
        arrays_id = []
        for array_id in boss_msg.arrays_id:
            arrays_id.append(array_id)

        return (id, boss_id, date, start_time, end_time, description, total_soldier_num, arrays_id)


    def _add_basic_worldboss_succeed(self, basic_data, req, timer):
        """
        """
        res = boss_pb2.AddBasicWorldBossRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Add basic worldboss succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_basic_worldboss_failed(self, err, req, timer):
        """
        """
        logger.fatal("Add basic worldboss failed[reason=%s]" % err)

        res = boss_pb2.AddBasicWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add basic worldboss failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete_basic_worldboss(self, user_id, request):
        """删除世界boss基础信息
        """
        timer = Timer(user_id)

        req = boss_pb2.DeleteBasicWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_delete_basic_worldboss, req, timer)
        defer.addCallback(self._delete_basic_worldboss_succeed, req, timer)
        defer.addErrback(self._delete_basic_worldboss_failed, req, timer)
        return defer


    def _calc_delete_basic_worldboss(self, basic_data, req, timer):
        """删除boss基础数据
        """
        if not worldboss_business.delete_basic_worldboss(basic_data, req.ids):
            raise Exception("Delete basic worldboss failed")
    
        logger.notice("delete basic worldbosses[ids=%s]" % utils.join_to_string(req.ids))

        return DataBase().commit_basic(basic_data)


    def _delete_basic_worldboss_succeed(self, basic_data, req, timer):
        """
        """
        res = boss_pb2.DeleteBasicWorldBossRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete basic worldboss succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_basic_worldboss_failed(self, err, req, timer):
        """
        """
        logger.fatal("Delete basic worldboss failed[reason=%s]" % err)

        res = boss_pb2.DeleteBasicWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete basic worldboss failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_basic_worldboss(self, user_id, request):
        """查询世界boss的基本信息
        """
        timer = Timer(user_id)

        req = boss_pb2.QueryBasicWorldBossReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_query_basic_worldboss, req, timer)
        defer.addErrback(self._query_basic_worldboss_failed, req, timer)
        return defer


    def _calc_query_basic_worldboss(self, basic_data, req, timer):
        """
        """
        worldboss_business.eliminate_invalid_basic_worldboss(basic_data, timer.now)

        bosses = []
        for id in req.ids:
            boss = basic_data.worldboss_list.get(id)
            if boss is not None:
                bosses.append(boss)

        if req.HasField("is_all"):
            if req.is_all:
                bosses = basic_data.worldboss_list.get_all()

    #    defer = DataBase().commit_basic(basic_data)
    #    defer.addCallback(self._query_basic_worldboss_succeed, bosses, req, timer)
    #    return defer


    #def _query_basic_worldboss_succeed(self, basic_data, bosses, req, timer):
    #    """
    #    """
        res = boss_pb2.QueryBasicWorldBossRes()
        res.status = 0
        for boss in bosses:
            msg = res.bosses.add()
            pack.pack_basic_worldboss_info(boss, msg, timer.now)
            
        response = res.SerializeToString()
        logger.notice("Query basic worldboss succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_basic_worldboss_failed(self, err, req, timer):
        """
        """
        logger.fatal("Query basic worldboss failed[reason=%s]" % err)

        res = boss_pb2.QueryBasicWorldBossRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query basic worldboss failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def add_basic_activity_treasure_reward(self, user_id, request):
        """添加转盘活动奖励的基础信息
        """
        timer = Timer(user_id)

        req = activity_pb2.AddBasicActivityHeroRewardReq()
        req.ParseFromString(request)

        defer = DataBase().get_basic_data(basic_view.BASIC_ID)
        defer.addCallback(self._calc_add_basic_activity_treasure_reward, req, timer)
        defer.addCallback(self._add_basic_activity_treasure_reward_succeed, req, timer)
        defer.addErrback(self._add_basic_activity_treasure_reward_failed, req, timer)
        return defer

    def _calc_add_basic_activity_treasure_reward(self, basic_data, req, timer):
        """
        """
        logger.notice("1111111111111")
        rewards = []
        for reward_msg in req.rewards:
            rewards.append(self._parse_activity_treasure_reward_msg(reward_msg))

        if not activity_business.add_basic_activity_treasure_reward(basic_data,
                basic_view.BASIC_ID, rewards):
            raise Exception("Add basic activity treasure reward failed")

        return DataBase().commit_basic(basic_data)


    def _parse_activity_treasure_reward_msg(self, reward_msg):
        """解析 activity_treasure_reward 配置信息
           Return:
               (id, level, list(items_id), list(items_num))四元组
        """
        id = reward_msg.id
        level = reward_msg.level
        items_id = reward_msg.basic_id
        items_num = reward_msg.num
        weight = reward_msg.weight
        #items_id = []
        #items_num = []
        #for item in reward_msg.reward_items:
        #    items_id.append(item.basic_id)
        #    items_num.append(item.num)
        logger.notice("items_id=%d"%items_id)
        return (id, level, items_id, items_num, weight)

    def _add_basic_activity_treasure_reward_succeed(self, basic_data, req, timer):
        """
        """
        res = activity_pb2.AddBasicActivityHeroRewardRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Add basic activity treasure reward succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response
                                                                                                                                            
                                                                                                                                            
    def _add_basic_activity_treasure_reward_failed(self, err, req, timer):                                                                      
        """                                                                                                                                 
        """                                                                                                                                 
        logger.fatal("Add basic activity treasure reward failed[reason=%s]" % err)                                                              
                                                                                                                                            
        res = activity_pb2.AddBasicActivityHeroRewardRes()                                                                                  
        res.status = -1                                                                                                                     
        response = res.SerializeToString()                                                                                                  
        logger.notice("Add basic activity treasure reward failed[user_id=%d][req=%s][res=%s][consume=%d]" %                                     
                (timer.id, req, res, timer.count_ms()))                                                                                     
        return response

