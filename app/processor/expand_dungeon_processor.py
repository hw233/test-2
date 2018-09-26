#coding:utf8
"""
Created on 2017-03-11
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 扩展副本
"""

from utils import logger
from utils.timer import Timer
from datalib.global_data import DataBase
from proto import dungeon_pb2
from app.business import expand_dungeon as expand_dungeon_business
from app import pack


class ExpandDungeonProcessor(object):
    """扩展副本"""

    def query(self, user_id, request):
        timer = Timer(user_id)

        req = dungeon_pb2.QueryExpandDungeonInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer

    def _calc_query(self, data, req, timer):
        res = dungeon_pb2.QueryExpandDungeonInfoRes()
        res.status = 0

        if req.HasField("battle_level"):
            battle_level = req.battle_level
        else:
            battle_level = 0

        dungeon = expand_dungeon_business.get_dungeon_by_id(data, req.id)
        if dungeon is None:
            res.ret = dungeon_pb2.DUNGEON_NO_DUNGEON
            return self._query_succeed(data, req, res, timer)

        dungeon.daily_update(timer.now)

        user = data.user.get(True)
        res.ret = dungeon_pb2.DUNGEON_OK
        pack.pack_expand_dungeon_info(dungeon, user, res.dungeon_info, battle_level, timer.now)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer

    def _query_succeed(self, data, req, res, timer):
        if res.ret == dungeon_pb2.DUNGEON_OK:
            logger.notice("Query expand dungeon succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Query expand dungeon failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _query_failed(self, err, req, timer):
        logger.fatal("Query expand dungeon failed[reason=%s]" % err)
        res = dungeon_pb2.QueryExpandDungeonInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query expand dungeon failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    def reset(self, user_id, request):
        """重置攻击次数"""
        timer = Timer(user_id)

        req = dungeon_pb2.QueryExpandDungeonInfoReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_reset, req, timer)
        defer.addErrback(self._reset_failed, req, timer)
        return defer

    def _calc_reset(self, data, req, timer):
        res = dungeon_pb2.QueryExpandDungeonInfoRes()
        res.status = 0

        dungeon = expand_dungeon_business.get_dungeon_by_id(data, req.id)
        if dungeon is None:
            res.ret = dungeon_pb2.DUNGEON_NO_DUNGEON
            return self._reset_succeed(data, req, res, timer)

        ret = expand_dungeon_business.reset_attack_count(data, dungeon, timer.now)
        if ret != dungeon_pb2.DUNGEON_OK:
            res.ret = ret
            return self._reset_succeed(data, req, res, timer)

        resource = data.resource.get()
        resource.update_current_resource(timer.now)
        user = data.user.get(True)
        
        res.ret = dungeon_pb2.DUNGEON_OK
        pack.pack_expand_dungeon_info(dungeon, user, res.dungeon_info, 0, timer.now, brief=True)
        pack.pack_resource_info(resource, res.resource)

        defer = DataBase().commit(data)
        defer.addCallback(self._reset_succeed, req, res, timer)
        return defer

    def _reset_succeed(self, data, req, res, timer):
        if res.ret == dungeon_pb2.DUNGEON_OK:
            logger.notice("Reset expand dungeon succeed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        else:
            logger.notice("Reset expand dungeon failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))

        response = res.SerializeToString()
        return response

    def _reset_failed(self, err, req, timer):
        logger.fatal("Reset expand dungeon failed[reason=%s]" % err)
        res = dungeon_pb2.QueryExpandDungeonInfoRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Reset expand dungeon failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response

    
