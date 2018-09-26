#coding:utf8
"""
Created on 2016-06-25
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 联盟援助逻辑
"""

from utils import logger
from gunion.data.aid import UnionAidInfo


def start_aid(data, user_id, item_basic_id, item_num, now):
    """启动一个联盟援助
    """
    aid_id = UnionAidInfo.generate_id(data.id, user_id)
    aid = data.aid_list.get(aid_id)
    if aid is None:
        aid = UnionAidInfo.create(data.id, user_id)
        data.aid_list.add(aid)

    if not aid.is_finish:
        logger.warning("Union aid is not finished[union_id=%d][user_id=%d]" %
                (data.id, user_id))
        return None

    aid.start(item_basic_id, item_num, now)
    return aid


def finish_aid(data, user_id, now):
    """结束一个联盟援助
    """
    aid_id = UnionAidInfo.generate_id(data.id, user_id)
    aid = data.aid_list.get(aid_id)
    if aid is None:
        logger.warning("Union aid is not exist[union_id=%d][user_id=%d]" %
                (data.id, user_id))
        return None

    if not aid.finish(now):
        logger.warning("Union aid is not able to finish[union_id=%d][user_id=%d]" %
                (data.id, user_id))
        return None

    return aid


def respond_aid(data, member, target_member, item_basic_id, now):
    """进行援助
    """
    aid_id = UnionAidInfo.generate_id(data.id, target_member.user_id)
    aid = data.aid_list.get(aid_id)
    if aid is None:
        #联盟援助不存在：发起玩家退出联盟
        logger.warning("Union aid is not exist[union_id=%d][user_id=%d]" %
                (data.id, target_member.user_id))
        return None

    if aid.is_finish:
        #联盟援助已结束：发起玩家领取
        logger.warning("Union aid is finished[union_id=%d][user_id=%d]" %
                (data.id, target_member.user_id))
        return None

    if aid.is_able_to_finish(now):
        #联盟援助达到满足条件
        logger.warning("Union aid is satisfied[union_id=%d][user_id=%d]" %
                (data.id, target_member.user_id))
        return None

    if not aid.accept(member.user_id, item_basic_id, now):
        raise Exception("Accept aid failed")

    #援助玩家获得荣誉
    (honor, exp, gold) = aid.calc_user_benefit()
    member.gain_honor(honor)

    #联盟获得繁荣度
    prosperity = aid.calc_union_benefit()
    union = data.union.get()
    union.gain_prosperity(prosperity, now)

    return aid



