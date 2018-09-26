#coding:utf8
"""
Created on 2016-08-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟信息管理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from utils.timer import Timer
from proto import internal_union_pb2
from proto import internal_pb2
from proto import union_pb2
from gunion.data.member import UnionMemberInfo
from gunion.business import battle as battle_business
from gunion import pack


class UnionPatcher(object):
    """联盟信息填充
    """

    def patch(self, message, data, user_id, now, enable_application = False):
        """填充联盟信息 message[protobuf UnionInfo]
        Args:
            message[protobuf UnionInfo]
            data[UnionData]
            user_id[int]: 玩家 user id
            now[int]: 时间戳
            enable_application[bool]: 是否需要包含申请信息
        """
        self.patch_message = message

        #基本信息
        union = data.union.get(True)
        pack.pack_union_info(union, message)

        #成员信息
        for member in data.member_list.get_all(True):
            pack.pack_member_info(member, message.members.add())

        #联盟申请
        if enable_application:
            for application in data.application_list.get_all(True):
                if application.is_available(now):
                    pack.pack_application_info(application, message.applications.add())

        #联盟援助
        for aid in data.aid_list.get_all(True):
            if aid.is_active_for(user_id, now):
                pack.pack_aid_info(aid, message.aids.add(), user_id, now)

        #战争信息
        return self._patch_battle_info(data, message.battle)


    def _patch_battle_info(self, message, data, use_id, now):
        """填充联盟战争信息
        Args:
            message[protobuf UnionBattleInfo]
            data[UnionData]
            user_id[int]: 玩家 user id
            now[int]: 时间戳
        """
        #战争基础信息
        season = data.season.get(True)
        battle = battle_business.update_battle(data, timer.now) #刷新战争情况
        pack.pack_battle_info(union, season, battle, message, timer.now)

        #个人数据
        member_id = UnionMemberInfo.generate_id(data.id, user_id)
        member = data.member_list.get(member_id, True)
        pack.pack_battle_individual_info(
                member, message.user)

        #己方防守地图信息
        nodes = battle_business.get_battle_map(data)
        pack.pack_battle_map_info(
                union, season,
                battle, nodes, message.own_map, timer.now)

        #战斗记录
        records = data.battle_record_list.get(True)
        for record in records:
            pack.pack_battle_records(record, message.records.add(), timer.now)

        #如果需要，查询敌对联盟的战斗信息
        if battle.is_at_war():
            union_req = internal_pb2.InternalQueryUnionBattleReq()
            union_req.user_id = user_id
            defer = GlobalObject().remote['gunion'].callRemote(
                    "query_battle", rival_union_id, launch_req.SerializeToString())
            defer.addCallback(self._patch_rival_battle_info)
        else:
            return self


    def _patch_rival_battle_info(self, union_response, message, data, user_id, now):
        """填充敌对联盟的战争信息
        """
        union_res = internal_pb2.InternalQueryUnionBattleReq()
        union_res.ParseFromString(union_response)
        if union_res.status != 0 or union_res.ret != union_pb2.UNION_OK:
            raise Exception("Query rival union battle res error")

        #敌对联盟防守地图信息
        battle_message.rival_map.CopyFrom(union_res.battle.own_map)

        #补充战斗记录
        for record in union_res.records:
            message.records.add().CopyFrom(record)

        return self

