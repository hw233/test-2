#coding:utf8
"""
Created on 2016-06-21
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟处理逻辑
"""

from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from proto import internal_union_pb2
from proto import union_pb2
from datalib.data_dup_checker import DataDupChecker
from datalib.global_data import DataBase
from gunion.season_searcher import SeasonRankingSearcher
from gunion.business import union as union_business
from gunion.business import member as member_business
from gunion.business import battle as battle_business
from gunion.business import donate as donate_business
from gunion.data.donate_box import UnionDonateBox
from gunion.data.union import UnionInfo
from gunion import pack


class UnionProcessor(object):


    def create(self, union_id, request):
        """创建联盟信息
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalCreateUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_create, req, timer)
        defer.addErrback(self._create_failed, req, timer)
        return defer


    def _calc_create(self, data, req, timer):
        """建立新联盟
        """
        if data.is_valid():
            #联盟已存在
            raise Exception("Union is exist[union_id=%d]" % data.id)

        #检查名称是否重复
        checker = DataDupChecker()
        defer = checker.check("unionunion", "name", UnionInfo.get_saved_name(req.name))
        defer.addCallback(self._do_create, data, req, timer)
        return defer


    def _do_create(self, is_name_exist, data, req, timer):
        if is_name_exist:
            #名字重复
            logger.debug("Union name is conflict[name=%s]" % req.name)
            res = self._pack_invalid_query_response(union_pb2.UNION_NAME_CONFLICT)
            return self._create_succeed(None, req, res, timer)

        else:
            if not union_business.init_union(
                    data, req.user_id, req.name, req.icon_id, timer.now):
                raise Exception("Init union failed")
            res = self._pack_query_response(data, req.user_id, timer, True)

            defer = DataBase().commit(data)
            defer.addCallback(self._create_succeed, req, res, timer)
            return defer


    def _pack_query_response(self, data, user_id, timer, enable_application = False):
        """打包结果
        Args:
            data: 联盟数据
            user_id: 玩家 user id
            enable_application: 是否需要打包申请（盟主和副盟主有权处理）
        """
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        union = data.union.get(True)
        pack.pack_union_info(union, res.union)

        for member in data.member_list.get_all(True):
            pack.pack_member_info(member, res.union.members.add())

        if enable_application:
            for application in data.application_list.get_all(True):
                if application.is_available(timer.now):
                    pack.pack_application_info(application, res.union.applications.add())

        for aid in data.aid_list.get_all(True):
            if aid.is_active_for(user_id, timer.now):
                if aid.user_id == user_id:
                    pack.pack_aid_info(aid, res.union.aid_own, user_id, timer.now)
                else:
                    pack.pack_aid_info(aid, res.union.aids.add(), user_id, timer.now)

        #战争基础信息
        season = data.season.get(True)
        battle = battle_business.update_battle(data, timer.now)
        pack.pack_battle_info(union, season, battle, res.union.battle, timer.now)

        #个人数据
        member = member_business.find_member(data, user_id)
        if member is not None:
            pack.pack_battle_individual_info(member, res.union.battle.user)

        #己方防守地图信息
        nodes = battle_business.get_battle_map(data)
        pack.pack_battle_map_info(union, season,
                battle, nodes, res.union.battle.own_map, timer.now)

        #战斗记录
        records = data.battle_record_list.get_all(True)
        for record in records:
            pack.pack_battle_record_info(record, res.union.battle.records.add(), timer.now)

        #联盟捐献信息
        donate_boxes = data.donate_box_list.get_all(True)
        for donate_box in donate_boxes:
            if donate_box.status != UnionDonateBox.NULL:
                pack.pack_donate_box_info(data, user_id, donate_box, res.boxes_info.add(), timer)

        donate_records = donate_business.get_donate_records(data)
        for donate_record in donate_records:
            pack.pack_donate_record_info(donate_record, res.donate_records.add())

        return res


    def _pack_invalid_query_response(self, ret):
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = ret
        return res


    def _create_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Create union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _create_failed(self, err, req, timer):
        logger.fatal("Create union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Create union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query(self, union_id, request, force = False):
        """查询联盟信息
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_query, req, timer, force)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer, force):
        """
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
            return self._query_succeed(data, req, res, timer)

        #检查是否是联盟成员
        member = member_business.find_member(data, req.user_id)
        if member is None:#玩家已经不属于此联盟
            if force:
                res = self._pack_query_response(data, req.user_id, timer)
            else:
                res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        elif member.is_leader() or member.is_vice_leader():#盟主和副盟主
            member_business.delete_not_available_application(data, timer.now)
            res = self._pack_query_response(data, req.user_id, timer, True)
        else:#普通成员
            res = self._pack_query_response(data, req.user_id, timer)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def query_summary(self, union_id, request):
        """查询联盟摘要
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_query_summary, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query_summary(self, data, req, timer):
        """
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
            return self._query_succeed(data, req, res, timer)

        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        union = data.union.get(True)
        pack.pack_union_info(union, res.union)

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_summary_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union summary succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_summary_failed(self, err, req, timer):
        logger.fatal("Query union summary failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union summary failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def update(self, union_id, request):
        """设置联盟
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalUpdateUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_update, req, timer)
        defer.addErrback(self._update_failed, req, timer)
        return defer


    def _calc_update(self, data, req, timer):
        """更新联盟信息
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
            return self._update_succeed(data, req, res, timer)

        if req.HasField("name"):
            #检查名称是否重复
            checker = DataDupChecker()
            defer = checker.check("unionunion", "name", UnionInfo.get_saved_name(req.name))
            defer.addCallback(self._do_calc_update, data, req, timer)
            return defer
        else:
            return self._do_calc_update(False, data, req, timer)


    def _do_calc_update(self, is_name_exist, data, req, timer):
        """更新
        """
        member = member_business.find_member(data, req.user_id)
        if member is None:
            #玩家已经不属于此联盟
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        elif is_name_exist:
            #名字重复
            logger.debug("Union name is conflict[name=%s]" % req.name)
            res = self._pack_invalid_query_response(union_pb2.UNION_NAME_CONFLICT)
        else:
            name = None
            icon_id = None
            need_level = None
            join_status = None
            announcement = None
            if req.HasField("name"):
                name = req.name
            if req.HasField("icon_id"):
                icon_id = req.icon_id
            if req.HasField("need_level"):
                need_level = req.need_level
            if req.HasField("join_status"):
                join_status = req.join_status
            if req.HasField("announcement"):
                announcement = req.announcement

            if union_business.update_union(data, member,
                    name, icon_id, need_level, join_status, announcement):
                res = self._pack_query_response(data, req.user_id, timer, True)
            else:
                res = self._pack_invalid_query_response(union_pb2.UNION_NO_AUTH)

        defer = DataBase().commit(data)
        defer.addCallback(self._update_succeed, req, res, timer)
        return defer


    def _update_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Update union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _update_failed(self, err, req, timer):
        logger.fatal("Update union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Update union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def delete(self, union_id, request):
        """删除联盟信息，内部接口
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalDeleteUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_delete, req, timer)
        defer.addCallback(self._delete_succeed, req, timer)
        defer.addErrback(self._delete_failed, req, timer)
        return defer


    def _calc_delete(self, data, req, timer):
        """删除联盟
        """
        if not data.is_valid():
            return data

        data.delete()
        defer = DataBase().commit(data)
        defer.addCallback(self._delete_cache)
        return defer


    def _delete_cache(self, data):
        DataBase().clear_data(data)
        return data


    def _delete_succeed(self, data, req, timer):
        res = internal_union_pb2.InternalDeleteUnionRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Delete union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _delete_failed(self, err, req, timer):
        logger.fatal("Delete union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalDeleteUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Delete union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def sync(self, union_id, request):
        """同步联盟信息（内部接口）
        同步是否在联盟中，联盟等级
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalQueryUnionReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_sync, req, timer)
        defer.addErrback(self._sync_failed, req, timer)
        return defer


    def _calc_sync(self, data, req, timer):
        """
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
            return self._sync_succeed(data, req, res, timer)

        #检查是否是联盟成员
        member = member_business.find_member(data, req.user_id)
        if member is None:#玩家已经不属于此联盟
            res = self._pack_invalid_query_response(union_pb2.UNION_NOT_MATCHED)
        else:#普通成员
            res = self._pack_sync_response(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._sync_succeed, req, res, timer)
        return defer


    def _pack_sync_response(self, data):
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        union = data.union.get(True)
        res.union.id = union.id
        res.union.name = union.get_readable_name()
        res.union.icon_id = union.icon
        res.union.level = union.level

        return res


    def _sync_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Sync union succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _sync_failed(self, err, req, timer):
        logger.fatal("Sync union failed[reason=%s]" % err)
        res = internal_union_pb2.InternalQueryUnionRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Sync union failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def start_chat(self, union_id, request):
        """开始聊天
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalStartUnionChatReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_start_chat, req, timer)
        defer.addErrback(self._start_chat_failed, req, timer)
        return defer


    def _calc_start_chat(self, data, req, timer):
        """
        """
        if not data.is_valid():
            #联盟不存在
            res = self._pack_invalid_start_chat_response(union_pb2.UNION_NOT_MATCHED)
            return self._start_chat_succeed(data, req, res, timer)

        #检查是否是联盟成员
        member = member_business.find_member(data, req.user_id)
        if member is None:#玩家已经不属于此联盟
            res = self._pack_invalid_start_chat_response(union_pb2.UNION_NOT_MATCHED)
        else:#普通成员
            res = self._pack_start_chat_response(data)

        defer = DataBase().commit(data)
        defer.addCallback(self._start_chat_succeed, req, res, timer)
        return defer


    def _pack_invalid_start_chat_response(self, ret):
        res = internal_union_pb2.InternalStartUnionChatRes()
        res.status = 0
        res.ret = ret
        return res


    def _pack_start_chat_response(self, data):
        res = internal_union_pb2.InternalStartUnionChatRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        union = data.union.get(True)
        res.roomname = union.chatroom
        res.password = union.chatpasswd
        return res


    def _start_chat_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Start union chat succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _start_chat_failed(self, err, req, timer):
        logger.fatal("Start union chat failed[reason=%s]" % err)
        res = internal_union_pb2.InternalStartUnionChatRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Start union chat failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_prosperity(self, union_id, request):
        """增加繁荣度
        """
        timer = Timer(union_id)

        req = internal_union_pb2.InternalAddUnionProsperityReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(union_id)
        defer.addCallback(self._calc_add_prosperity, req, timer)
        defer.addCallback(self._add_prosperity_succeed, req, timer)
        defer.addErrback(self._add_prosperity_failed, req, timer)
        return defer


    def _calc_add_prosperity(self, data, req, timer):
        #增加联盟繁荣度
        union = data.union.get()
        union.gain_prosperity(req.prosperity, timer.now)

        defer = DataBase().commit(data)
        return defer


    def _add_prosperity_succeed(self, data, req, timer):
        res = internal_union_pb2.InternalAddUnionProsperityRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Add prosperity succeed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _add_prosperity_failed(self, err, req, timer):
        logger.fatal("Add prosperity failed[reason=%s]" % err)
        res = internal_union_pb2.InternalAddUnionProsperityRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Add prosperity failed"
                "[union_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


