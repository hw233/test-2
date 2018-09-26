#coding:utf8
"""
Created on 2016-08-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟信息管理逻辑
"""

from firefly.server.globalobject import GlobalObject
from utils import logger
from proto import internal_union_pb2
from proto import union_pb2
from datalib.data_proxy4redis import DataProxy
from app.union_member_matcher import UnionMemberMatcher


class UnionBattleStagePatcher(object):
    """联盟战争状态查询
    """
    def patch(self, union_id):
        proxy = DataProxy()
        proxy.search("unionseason", union_id)
        proxy.search_by_index("unionbattle", "union_id", union_id)
        proxy.execute(asyn = False)

        season = proxy.get_result("unionseason", union_id)
        for battle in proxy.get_all_result("unionbattle"):
            if battle.index == season.current_battle_index:
                return battle.stage

        raise Exception("union data error")


class UnionPatcher(object):
    """联盟信息填充
    """

    def patch(self, message, union_message, data, now):
        """填充联盟信息 message[protobuf UnionInfo]
        Args:
            message[protobuf UnionInfo]: 需要打包的联盟信息
            union_message[protobuf UnionInfo]: gunion 返回的联盟信息
            data[UserData]
            now[int]: 时间戳
            enable_application[bool]: 是否需要包含申请信息
        """
        #本方联盟返回的信息
        message.CopyFrom(union_message)
        message.battle.begin_battle_left_time = message.battle.begin_battle_left_time + (data.id % 220)

        #援助信息
        union = data.union.get(True)
        message.aid_lock_time_left = union.aid_lock_time - now

        #成员信息，查询数据库
        matcher = UnionMemberMatcher()
        for member in message.members:
            matcher.add_condition(member.user.user_id)
        defer = matcher.match()
        defer.addCallback(self._patch_member_info, message, union_message, data, now)
        return defer


    def _patch_member_info(self, matcher, message, union_message, data, now):
        """填充成员信息
        """
        for member_msg in message.members:
            (name, level, icon, last_login_time, battle_score, honor) = matcher.result[
                    member_msg.user.user_id]
            member_msg.user.name = name
            member_msg.user.level = level
            member_msg.user.headicon_id = icon
            member_msg.battle_score = battle_score
            member_msg.last_login_pass_time = now - last_login_time
            member_msg.current_honor = honor

        for aid_msg in message.aids:
            (name, level, icon, last_login_time, battle_score, honor) = matcher.result[
                    aid_msg.sender.user_id]
            aid_msg.sender.name = name
            aid_msg.sender.level = level
            aid_msg.sender.headicon_id = icon

        if message.HasField("aid_own"):
            user = data.user.get(True)
            message.aid_own.sender.name = user.get_readable_name()
            message.aid_own.sender.level = user.level
            message.aid_own.sender.headicon_id = user.icon_id

        return self._patch_battle_info(message, union_message, data, now)


    def _patch_battle_info(self, message, union_message, data, now):
        """填充战争信息
        """
        defer = UnionBattlePatcher().patch(message.battle, union_message.battle, data, now)
        defer.addCallback(self._patch_post)
        return defer


    def _patch_post(self, battle_patcher):
        """完成填充
        """
        return self



class UnionBattlePatcher(object):
    """填充联盟战争信息，可能包括敌对联盟信息
    """

    def patch(self, message, union_message, data, now):
        """填充联盟战争信息
        Args:
            message[protobuf UnionBattleInfo]: 需要打包的联盟信息
            union_message[protobuf UnionBattleInfo]: 己方联盟返回的战斗信息
            data[UserData]
            now[int]: 时间戳
        """
        #本方联盟返回的联盟战斗信息
        message.CopyFrom(union_message)

        #补充个人信息
        user = data.user.get(True)
        union = data.union.get(True)
        message.user.user.user_id = user.id
        message.user.user.name = user.get_readable_name()
        message.user.user.headicon_id = user.icon_id
        message.user.left_attack_count = union.battle_attack_count_left
        message.user.refresh_attack_num = union.battle_attack_refresh_num
        message.user.drum_count = union.battle_drum_count

        if (union_message.stage != union_message.INVALID and
                union_message.stage != union_message.IDLE):
            #在战争中，需要查询对手联盟的战斗信息
            rival_union_req = internal_union_pb2.InternalQueryUnionBattleReq()
            defer = GlobalObject().remote['gunion'].callRemote(
                    "query_battle", union_message.rival_union_id,
                    rival_union_req.SerializeToString())
            defer.addCallback(self._patch_rival_battle_info, message, data, now)
            return defer
        else:
            return self._patch_ranking_info(message, data, now)


    def _patch_rival_battle_info(self, union_response, message, data, now):
        """填充敌对联盟的战争信息
        """
        rival_union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        rival_union_res.ParseFromString(union_response)
        if rival_union_res.status != 0 or rival_union_res.ret != union_pb2.UNION_OK:
            raise Exception("Query rival union battle res error")

        #敌对联盟防守地图信息
        message.rival_map.CopyFrom(rival_union_res.battle.own_map)

        #补充战斗记录
        for record in rival_union_res.battle.records:
            message.records.add().CopyFrom(record)

        return self._patch_ranking_info(message, data, now)


    def _patch_ranking_info(self, message, data, now):
        """补充双方联盟的排名信息，个人排名
        """
        proxy = DataProxy()
        #联盟赛季胜场积分排名
        proxy.search_ranking("unionseason", "score", message.union_id)
        if message.rival_union_id != 0:
            proxy.search_ranking("unionseason", "score", message.rival_union_id)

        #联盟赛季个人战功排名
        proxy.search_ranking("union", "season_score", data.id)
        defer = proxy.execute()
        defer.addCallback(self._patch_post, message, data, now)
        return defer


    def _patch_post(self, proxy, message, data, now):
        """完成填充
        """
        union_ranking = proxy.get_ranking("unionseason", "score", message.union_id) + 1
        if message.rival_union_id != 0:
            rival_union_ranking = proxy.get_ranking(
                    "unionseason", "score", message.rival_union_id) + 1
        individual_ranking = proxy.get_ranking("union", "season_score", data.id) + 1

        message.own_map.season_ranking = union_ranking
        if message.rival_union_id != 0:
            message.rival_map.season_ranking = rival_union_ranking

        union = data.union.get(True)
        message.user.season_score = union.season_score
        message.user.season_ranking = individual_ranking

        return self


    def patch_by_both_message(self, message, union_message, rival_union_message, data, now):
        """根据双方联盟的返回，补充信息
        """
        #本方联盟返回的联盟战斗信息
        message.CopyFrom(union_message)

        #补充个人信息
        user = data.user.get(True)
        union = data.union.get(True)
        message.user.user.name = user.get_readable_name()
        message.user.user.headicon_id = user.icon_id
        message.user.left_attack_count = union.battle_attack_count_left
        message.user.refresh_attack_num = union.battle_attack_refresh_num
        message.user.drum_count = union.battle_drum_count
        message.user.season_score = union.season_score

        #敌对联盟防守地图信息
        message.rival_map.CopyFrom(rival_union_message.own_map)

        #补充战斗记录
        for record in rival_union_message.records:
            message.records.add().CopyFrom(record)

        #补充双方排名信息
        return self._patch_ranking_info(message, data, now)

