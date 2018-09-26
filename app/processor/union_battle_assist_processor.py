#coding:utf8
"""
Created on 2016-08-02
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟战争相关辅助逻辑
"""

from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from proto import union_pb2
from proto import union_battle_pb2
from proto import internal_pb2
from proto import internal_union_pb2
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy
from datalib.global_data import DataBase
from datalib.data_dumper import DataDumper
from app import pack
from app.union_member_matcher import UnionMemberBattleDetailSearcher
from app.union_ranker import UnionRanker
from app.union_recommender import UnionRecommender
from app.union_allocator import UnionAllocator
from app.business import union_battle as union_battle_business


class UnionBattleAssistProcessor(object):

    def query_individuals(self, user_id, request):
        """查询战争中个人表现情况
        """
        timer = Timer(user_id)

        req = union_battle_pb2.QueryUnionBattleIndividualsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_query, req, timer)
        defer.addErrback(self._query_failed, req, timer)
        return defer


    def _calc_query(self, data, req, timer):
        union = data.union.get(True)
        if not union.is_belong_to_target_union(req.union_id):
            res = union_battle_pb2.QueryUnionBattleIndividualsRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._query_succeed, req, res, timer)
            return defer

        searcher = UnionMemberBattleDetailSearcher()
        defer = searcher.search([req.union_id, req.rival_union_id])
        defer.addCallback(self._calc_query_result, data, req, timer)
        return defer


    def _calc_query_result(self, searcher, data, req, timer):
        res = union_battle_pb2.QueryUnionBattleIndividualsRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        for user_id in searcher.members:
            member = searcher.members[user_id]
            user = searcher.users[user_id]
            if member.union_id == req.union_id:
                pack.pack_union_battle_individual_info(member, user, res.own_side.add())
            else:
                pack.pack_union_battle_individual_info(member, user, res.rival_side.add())

        defer = DataBase().commit(data)
        defer.addCallback(self._query_succeed, req, res, timer)
        return defer


    def _query_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Query union battle individuals succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _query_failed(self, err, req, timer):
        logger.fatal("Query union battle individuals failed[reason=%s]" % err)
        res = union_battle_pb2.QueryUnionBattleIndividualsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Query union battle individuals failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def gain_battle_individual_score(self, user_id, request):
        """联盟成员获得战功
        """
        timer = Timer(user_id)

        req = internal_pb2.GainUnionBattleScoreReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_gain_individual, req, timer)
        defer.addCallback(self._gain_individual_succeed, req, timer)
        defer.addErrback(self._gain_individual_failed, req, timer)
        return defer


    def _calc_gain_individual(self, data, req, timer):
        #个人赛季战功增加
        union = data.union.get()
        union.gain_season_score_immediate(req.score)

        #如果需要，同步到联盟（此次战争中的战功增加）
        if req.HasField("union_id"):
            if union.is_belong_to_target_union(req.union_id):
                union_req = internal_union_pb2.InternalGainUnionBattleScoreReq()
                union_req.user_id = data.id
                union_req.individual_score = req.score

                defer = GlobalObject().remote['gunion'].callRemote(
                        "gain_battle_score", req.union_id, union_req.SerializeToString())
                defer.addCallback(self._calc_gain_individual_post, data, req, timer)
                return defer

        defer = DataBase().commit(data)
        return defer


    def _calc_gain_individual_post(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Gain union battle score res error")

        defer = DataBase().commit(data)
        return defer


    def _gain_individual_succeed(self, data, req, timer):
        res = internal_pb2.GainUnionBattleScoreRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Gain union battle individual score succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _gain_individual_failed(self, err, req, timer):
        logger.fatal("Gain union battle individual score failed[reason=%s]" % err)
        res = internal_pb2.GainUnionBattleScoreRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Gain union battle individual score failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



    def gain_battle_score(self, user_id, request):
        """联盟获得胜场积分
        """
        timer = Timer(user_id)

        req = internal_pb2.GainUnionBattleScoreReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_gain, req, timer)
        defer.addCallback(self._gain_succeed, req, timer)
        defer.addErrback(self._gain_failed, req, timer)
        return defer


    def _calc_gain(self, data, req, timer):
        union = data.union.get()
        union_req = internal_union_pb2.InternalGainUnionBattleScoreReq()
        union_req.union_score = req.score

        defer = GlobalObject().remote['gunion'].callRemote(
                "gain_battle_score", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_gain_post, data, req, timer)
        return defer


    def _calc_gain_post(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Gain union battle score res error")

        defer = DataBase().commit(data)
        return defer


    def _gain_succeed(self, data, req, timer):
        res = internal_pb2.GainUnionBattleScoreRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Gain union battle score succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _gain_failed(self, err, req, timer):
        logger.fatal("Gain union battle score failed[reason=%s]" % err)
        res = internal_pb2.GainUnionBattleScoreRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Gain union battle score failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def refresh_attack(self, user_id, request):
        """刷新攻击次数
        """
        timer = Timer(user_id)

        req = union_battle_pb2.RefreshUnionBattleAttackReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh_attack, req, timer)
        defer.addErrback(self._refresh_attack_failed, req, timer)
        return defer


    def _calc_refresh_attack(self, data, req, timer):
        union = data.union.get()
        if not union.is_belong_to_target_union(req.union_id):
            res = union_battle_pb2.RefreshUnionBattleAttackRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._refresh_attack_succeed, req, res, timer)
            return defer

        if not union_battle_business.refresh_attack(data, req.gold, timer.now):
            raise Exception("Refresh attack failed")

        res = union_battle_pb2.RefreshUnionBattleAttackRes()
        res.status = 0
        res.ret = union_pb2.UNION_OK

        defer = DataBase().commit(data)
        defer.addCallback(self._refresh_attack_succeed, req, res, timer)
        return defer


    def _refresh_attack_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Refresh union attack succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _refresh_attack_failed(self, err, req, timer):
        logger.fatal("Refresh union attack failed[reason=%s]" % err)
        res = union_battle_pb2.RefreshUnionBattleAttackRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh union attack failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def accept_individual_step_award(self, user_id, request):
        """领取战功阶段奖励
        """
        timer = Timer(user_id)

        req = union_battle_pb2.AcceptUnionBattleIndividualsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_individual_step, req, timer)
        defer.addErrback(self._accept_individual_step_failed, req, timer)
        return defer


    def _calc_individual_step(self, data, req, timer):
        union = data.union.get()
        if not union.is_belong_to_target_union(req.union_id):
            res = union_battle_pb2.RefreshUnionBattleAttackRes()
            res.status = 0
            res.ret = union_pb2.UNION_NOT_MATCHED

            defer = DataBase().commit(data)
            defer.addCallback(self._accept_individual_step_succeed, req, res, timer)
            return defer

        user = data.user.get(True)
        union_req = internal_union_pb2.InternalAcceptUnionBattleIndividualStepReq()
        union_req.user_id = data.id
        union_req.user_level = user.level
        union_req.target_step = req.target_step
        defer = GlobalObject().remote['gunion'].callRemote(
                "accept_individual_step_award", req.union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_individual_step_result, data, req, timer)
        return defer


    def _calc_individual_step_result(self, union_response, data, req, timer):
        union_res = internal_union_pb2.InternalQueryUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Query union battle res error")

        res = union_battle_pb2.AcceptUnionBattleIndividualsRes()
        res.status = 0
        res.ret = union_res.ret

        if res.ret == union_pb2.UNION_OK:
            #领取战功阶段奖励
            (honor, items) = union_battle_business.accept_individual_step_award(
                    data, req.target_step, timer.now)

            pack.pack_resource_info(data.resource.get(True), res.resource)
            for (item_basic_id, item_num) in items:
                item_msg = res.items.add()
                item_msg.basic_id = item_basic_id
                item_msg.num = item_num
            res.honor = honor

        defer = DataBase().commit(data)
        defer.addCallback(self._accept_individual_step_succeed, req, res, timer)
        return defer


    def _accept_individual_step_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Accept union battle individual step award succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _accept_individual_step_failed(self, err, req, timer):
        logger.fatal("Accept union battle individual step award failed[reason=%s]" % err)
        res = union_battle_pb2.AcceptUnionBattleIndividualsRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Accept union battle individual step award  failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def force_update(self, user_id, request):
        """强制更新联盟战争（内部接口）
        """
        timer = Timer(user_id)

        req = internal_pb2.ForceUpdateUnionBattleReq()
        req.ParseFromString(request)

        defer = GlobalObject().remote['gunion'].callRemote(
                "force_update_battle", req.union_id, req.SerializeToString())
        defer.addCallback(self._force_update_succeed, req, timer)
        defer.addErrback(self._force_update_failed, req, timer)
        return defer


    def _force_update_succeed(self, response, req, timer):
        res = internal_pb2.ForceUpdateUnionBattleRes()
        res.status = 0
        res.ParseFromString(response)

        logger.notice("Force update union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _force_update_failed(self, err, req, timer):
        logger.fatal("Force update union battle failed[reason=%s]" % err)
        res = internal_pb2.ForceUpdateUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Force update union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def award(self, user_id, request):
        """发放联盟战争奖励
        """
        timer = Timer(user_id)

        req = union_battle_pb2.AwardForUnionBattleReq()
        req.ParseFromString(request)

        defer = Deferred()
        defer.addCallback(self._calc_award, req, timer)
        defer.addCallback(self._award_succeed, req, timer)
        defer.addErrback(self._award_failed, req, timer)
        defer.callback(True)
        return defer


    def _calc_award(self, ret, req, timer):
        """
        """
        if req.type == req.UNION:
            prosperity = union_battle_business.calc_award_for_union(req.win)
            self._forward_award_prosperity(req.union_id, prosperity)

        elif req.type == req.SEASON_UNION:
            prosperity = union_battle_business.calc_season_award_for_union(req.ranking)
            self._forward_award_prosperity(req.union_id, prosperity)

        elif req.type == req.UNION_MEMBER:
            (items, gold, honor) = union_battle_business.calc_award_for_union_member(
                    req.win, timer.now)

            if req.win:
                subject = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_win_subject"].value.encode("utf-8")
                content = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_win_content"].value.encode("utf-8")
                content = content.replace("@union_name", req.union_name)
                content = content.replace("@union_id", str(req.union_id))
                content = content.replace("@rival_union_name", req.rival_union_name)
                content = content.replace("@rival_union_id", str(req.rival_union_id))
                content = content.replace("@honor", str(honor))
            else:
                subject = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_fail_subject"].value.encode("utf-8")
                content = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_fail_content"].value.encode("utf-8")
                content = content.replace("@union_name", req.union_name)
                content = content.replace("@union_id", str(req.union_id))
                content = content.replace("@rival_union_name", req.rival_union_name)
                content = content.replace("@rival_union_id", str(req.rival_union_id))

            self._forward_award_mail(req.user_id, subject, content, items, gold)
            if honor > 0:
                self._forward_award_honor(req.user_id, req.union_id, honor)

        elif req.type == req.INDIVIDUAL:
            (items, gold, honor) = union_battle_business.calc_award_for_individual(
                    req.ranking, timer.now)

            subject = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_personal_award_subject"].value.encode("utf-8")
            content = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_personal_award_content"].value.encode("utf-8")
            content = content.replace("@union_name", req.union_name)
            content = content.replace("@union_id", str(req.union_id))
            content = content.replace("@rival_union_name", req.rival_union_name)
            content = content.replace("@rival_union_id", str(req.rival_union_id))
            content = content.replace("@honor", str(honor))
            
            self._forward_award_mail(req.user_id, subject, content, items, gold)
            self._forward_award_honor(req.user_id, req.union_id, honor)

        elif req.type == req.SEASON_UNION_MEMBER:
            (items, gold, honor) = union_battle_business.calc_season_award_for_union_member(
                    req.ranking, timer.now)

            subject = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_season_award_subject"].value.encode("utf-8")
            content = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_season_award_content"].value.encode("utf-8")
            content = content.replace("@union_name", req.union_name)
            content = content.replace("@union_id", str(req.union_id))
            content = content.replace("@ranking", str(req.ranking))
            content = content.replace("@honor", str(honor))
            
            self._forward_award_mail(req.user_id, subject, content, items, gold)
            self._forward_award_honor(req.user_id, req.union_id, honor)

        elif req.type == req.SEASON_INDIVIDUAL:
            (items, gold, honor) = union_battle_business.calc_season_award_for_individual(
                    req.ranking, timer.now)

            subject = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_season_personal_award_subject"].value.encode("utf-8")
            content = data_loader.ServerDescKeyInfo_dict[
                        "union_battle_season_personal_award_content"].value.encode("utf-8")
            content = content.replace("@ranking", str(req.ranking))
            content = content.replace("@honor", str(honor))
            
            self._forward_award_mail(req.user_id, subject, content, items, gold)
            self._forward_award_honor(req.user_id, req.union_id, honor)

        return True


    def _forward_award_prosperity(self, union_id, prosperity):
        union_req = internal_union_pb2.InternalAddUnionProsperityReq()
        union_req.prosperity = prosperity

        defer = GlobalObject().remote['gunion'].callRemote(
                "add_prosperity", union_id, union_req.SerializeToString())
        defer.addCallback(self._check_award_prosperity)
        return defer


    def _check_award_prosperity(self, union_response):
        union_res = internal_union_pb2.InternalAddUnionProsperityRes()
        union_res.ParseFromString(union_response)
        if union_res.status != 0:
            raise Exception("Forward award prosperity failed")


    def _forward_award_honor(self, user_id, union_id, honor):
        forward_req = union_pb2.AddUnionHonorReq()
        forward_req.union_id = union_id
        forward_req.honor = honor

        defer = GlobalObject().root.callChild("portal", "forward_add_honor",
                user_id, forward_req.SerializeToString())
        defer.addCallback(self._check_award_honor)
        return defer


    def _check_award_honor(self, response):
        res = union_pb2.AddUnionHonorRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward award honor failed")


    def _forward_award_mail(self, user_id, subject, content, items, gold):
        forward_req = internal_pb2.ReceiveMailReq()
        forward_req.user_id = user_id
        forward_req.mail.basic_id = 101
        forward_req.mail.subject = subject
        forward_req.mail.content = content
        forward_req.mail.sender = data_loader.ServerDescKeyInfo_dict[
                "union_sender"].value.encode("utf-8")
        for (item_basic_id, item_num) in items:
            info = forward_req.mail.reward_items.add()
            info.basic_id = item_basic_id
            info.num = item_num
        if gold > 0:
            forward_req.mail.reward_resource.gold = gold

        defer = GlobalObject().root.callChild("portal", "forward_mail",
                user_id, forward_req.SerializeToString())
        defer.addCallback(self._check_award_mail)
        return defer


    def _check_award_mail(self, response):
        res = internal_pb2.ReceiveMailRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward award mail failed")


    def _award_succeed(self, ret, req, timer):
        res = union_battle_pb2.AwardForUnionBattleRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Award for union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _award_failed(self, err, req, timer):
        logger.fatal("Award for union battle failed[reason=%s]" % err)
        res = union_battle_pb2.AwardForUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Award for union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def try_forward_battle(self, user_id, request):
        """尝试进入下一场战斗
        """
        timer = Timer(user_id)

        req = union_battle_pb2.TryForwardUnionBattleReq()
        req.ParseFromString(request)

        defer = GlobalObject().remote['gunion'].callRemote(
                "try_forward_battle", req.union_id, req.SerializeToString())
        defer.addCallback(self._calc_forward_battle_own_result, req, timer)
        defer.addErrback(self._try_forward_battle_failed, req, timer)
        return defer


    def _calc_forward_battle_own_result(self, union_response, req, timer):
        union_res = union_battle_pb2.TryForwardUnionBattleRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Try forward union battle res error")

        if not union_res.enable:
            return self._try_forward_battle_succeed(req, union_res, timer)

        if req.union_id == union_res.attack_union_id:
            rival_union_id = union_res.defence_union_id
        elif req.union_id == union_res.defence_union_id:
            rival_union_id = union_res.attack_union_id

        rival_union_req = union_battle_pb2.TryForwardUnionBattleReq()
        rival_union_req.union_id = rival_union_id
        defer = GlobalObject().remote['gunion'].callRemote(
                "try_forward_battle", rival_union_id, rival_union_req.SerializeToString())
        defer.addCallback(self._calc_forward_battle_rival_result, req, union_res, timer)
        return defer


    def _calc_forward_battle_rival_result(self, rival_union_response, req, union_res, timer):
        rival_union_res = union_battle_pb2.TryForwardUnionBattleRes()
        rival_union_res.ParseFromString(rival_union_response)

        if rival_union_res.status != 0:
            raise Exception("Try forward union battle res error")
        assert rival_union_res.enable

        for union_info in rival_union_res.unions:
            union_res.unions.add().CopyFrom(union_info)

        for user_info in rival_union_res.users:
            union_res.users.add().CopyFrom(user_info)

        return self._try_forward_battle_succeed(req, union_res, timer)


    def _try_forward_battle_succeed(self, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Try forward union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _try_forward_battle_failed(self, err, req, timer):
        logger.fatal("Try forward union battle failed[reason=%s]" % err)
        res = union_battle_pb2.TryForwardUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Try forward union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def try_forward_season(self, user_id, request):
        """尝试进入下一个赛季
        """
        timer = Timer(user_id)

        req = union_battle_pb2.TryForwardUnionBattleSeasonReq()
        req.ParseFromString(request)

        #查询一下当前赛季排名（联盟排名、个人排名）
        union_min = min(data_loader.UnionSeasonBattleAwardInfo_dict.keys()) - 1
        union_max = max(data_loader.UnionSeasonBattleAwardInfo_dict.keys()) - 1
        indiv_min = min(data_loader.UnionSeasonBattleIndivAwardInfo_dict.keys()) - 1
        indiv_max = max(data_loader.UnionSeasonBattleIndivAwardInfo_dict.keys()) - 1

        proxy = DataProxy()
        proxy.search_by_rank("unionseason", "score", union_min, union_max)
        proxy.search_by_rank("union", "season_score", indiv_min, indiv_max)
        defer = proxy.execute()
        defer.addCallback(self._calc_season_result, req,
                union_min, union_max, indiv_min, indiv_max, timer)
        defer.addErrback(self._try_forward_season_failed, req, timer)
        return defer


    def _calc_season_result(self, pre_proxy, req,
            union_min, union_max, indiv_min, indiv_max, timer):

        seasons = []
        users = []

        for i, union_info in enumerate(
                pre_proxy.get_rank_result("unionseason", "score", union_min, union_max)):
            seasons.append(union_info)

        for i, indiv_info in enumerate(
                pre_proxy.get_rank_result("union", "season_score", indiv_min, indiv_max)):
            users.append(indiv_info)

        #查询联盟信息
        proxy = DataProxy()
        for union_info in seasons:
            proxy.search("unionunion", union_info.union_id)
            proxy.search_by_index("unionmember", "union_id", union_info.union_id)
        for indiv_info in users:
            proxy.search("user", indiv_info.user_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_season_ranking_result, req, seasons, users, timer)
        return defer


    def _calc_season_ranking_result(self, proxy, req, seasons, indivs, timer):
        unions = {}
        for union in proxy.get_all_result("unionunion"):
            unions[union.id] = union
        users = {}
        for user in proxy.get_all_result("user"):
            users[user.id] = user
        members = proxy.get_all_result("unionmember")

        res = union_battle_pb2.TryForwardUnionBattleSeasonRes()
        res.status = 0
        res.enable = False

        for ranking, season in enumerate(seasons):
            union = unions[season.union_id]
            pack.pack_ranking_info_of_union(
                    union, season.score, ranking + 1, res.union_ranking.add())

        for ranking, indiv in enumerate(indivs):
            user = users[indiv.user_id]
            pack.pack_ranking_info_of_user(
                    user, indiv.season_score, ranking + 1, res.user_ranking.add())

        for member in members:
            member_msg = res.members.add()
            member_msg.user_id = member.user_id
            member_msg.union_id = member.union_id
        for indiv in indivs:
            member_msg = res.members.add()
            member_msg.user_id = indiv.user_id
            member_msg.union_id = indiv.union_id

        dumper = DataDumper()
        defer = dumper.get_all("unionunion", "id")
        defer.addCallback(self._calc_try_forward_season, req, res, timer)
        return defer


    def _calc_try_forward_season(self, union_ids, req, res, timer):
        #服务器没有联盟
        if len(union_ids) == 0:
            return self._try_forward_season_succeed(req, res, timer)

        union_id = union_ids.pop()
        union_req = union_battle_pb2.TryForwardUnionBattleSeasonReq()
        defer = GlobalObject().remote['gunion'].callRemote(
                "try_forward_season", union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_try_forward_season_result,
                None, union_ids, req, res, timer)
        return defer


    def _calc_try_forward_season_result(
            self, union_response, expect, union_ids, req, res, timer):
        union_res = union_battle_pb2.TryForwardUnionBattleSeasonRes()
        union_res.ParseFromString(union_response)

        if union_res.status != 0:
            raise Exception("Try forward union battle season res error")

        if expect is None and not union_res.enable:
            #无法进入下一个赛季，直接返回
            return self._try_forward_season_succeed(req, res, timer)
        elif expect is not None and union_res.enable != expect:
            #各个联盟进入下一个赛季，出现不一致的情况
            logger.warning("Try forward union battle season unexpected")

        #各个联盟均已经进入下一个赛季
        if len(union_ids) == 0:
            res.enable = True
            self._try_forward_season_for_user_not_belong_to_union()
            return self._try_forward_season_succeed(req, res, timer)

        union_id = union_ids.pop()
        union_req = union_battle_pb2.TryForwardUnionBattleSeasonReq()
        defer = GlobalObject().remote['gunion'].callRemote(
                "try_forward_season", union_id, union_req.SerializeToString())
        defer.addCallback(self._calc_try_forward_season_result,
                True, union_ids, req, res, timer)
        return defer


    def _try_forward_season_for_user_not_belong_to_union(self):
        """让不属于任何联盟的玩家，且参加过上个赛季联盟战争的玩家，进入下一个赛季
        """
        users = []

        flag = True
        begin = 0
        gap = 50
        while flag:
            proxy = DataProxy()
            proxy.search_by_rank("union", "season_score", begin, begin + gap)
            defer = proxy.execute()

            for i, indiv_info in enumerate(
                    proxy.get_rank_result("union", "season_score", begin, begin + gap)):
                if indiv_info.season_score > 0:
                    if indiv_info.user_id not in users:
                        users.append(indiv_info.user_id)
                else:
                    flag = False
                    break

            begin += gap

        for user_id in users:
            req = internal_pb2.UnionBattleForwardReq()
            defer = GlobalObject().root.callChild(
                    "portal", "forward_union_battle_season_forward",
                    user_id, req.SerializeToString())
            defer.addCallback(self._check_forward_season_for_user_not_belong_to_union)


    def _check_forward_season_for_user_not_belong_to_union(self, response):
        res = internal_pb2.UnionBattleForwardRes()
        res.ParseFromString(response)
        if res.status != 0:
            raise Exception("Forward union battle season for user not belong to union failed")


    def _try_forward_season_succeed(self, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Try forward union battle season succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _try_forward_season_failed(self, err, req, timer):
        logger.fatal("Try forward union battle season failed[reason=%s]" % err)
        res = union_battle_pb2.TryForwardUnionBattleRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Try forward union battle season failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def forward_battle(self, user_id, request):
        """进入下一场战斗
        """
        timer = Timer(user_id)

        req = internal_pb2.UnionBattleForwardReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_forward_battle, req, timer)
        defer.addCallback(self._forward_battle_succeed, req, timer)
        defer.addErrback(self._forward_battle_failed, req, timer)
        return defer


    def _calc_forward_battle(self, data, req, timer):
        #清除所有驻防部队
        union_battle_business.cancel_all_deploy_for_union_battle(data)

        #进入下一场战争
        union = data.union.get()
        union.forward_battle()

        defer = DataBase().commit(data)
        return defer


    def _forward_battle_succeed(self, data, req, timer):
        res = internal_pb2.UnionBattleForwardRes()
        res.status = 0
        response = res.SerializeToString()
        logger.notice("Forward union battle succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _forward_battle_failed(self, err, req, timer):
        logger.fatal("Forward union battle failed[reason=%s]" % err)
        res = internal_pb2.UnionBattleForwardRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Forward union battle failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def forward_season(self, user_id, request):
        """进入下一个赛季
        """
        timer = Timer(user_id)

        req = internal_pb2.UnionBattleForwardReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_forward_season, req, timer)
        defer.addCallback(self._forward_season_succeed, req, timer)
        defer.addErrback(self._forward_season_failed, req, timer)
        return defer


    def _calc_forward_season(self, data, req, timer):
        #清除所有驻防部队
        union_battle_business.cancel_all_deploy_for_union_battle(data)

        #进入下一个赛季
        union = data.union.get()
        union.forward_season()

        defer = DataBase().commit(data)
        return defer


    def _forward_season_succeed(self, data, req, timer):
        res = internal_pb2.UnionBattleForwardRes()
        res.status = 0

        response = res.SerializeToString()
        logger.notice("Forward union battle season succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _forward_season_failed(self, err, req, timer):
        logger.fatal("Forward union battle season failed[reason=%s]" % err)
        res = internal_pb2.UnionBattleForwardRes()
        res.status = -1

        response = res.SerializeToString()
        logger.notice("Forward union battle season failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response



