#coding:utf8
"""
Created on 2016-06-27
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief :好友推荐
"""

import random
from twisted.internet.defer import Deferred
from utils import logger
from utils import utils
from datalib.data_loader import data_loader
from datalib.data_proxy4redis import DataProxy


class FriendRecommender(object):
    """好友推荐
    """

    def add_condition(self, user):
        self.user = user
        self.result = []


    def match(self, now):
        """进行推荐
        """
        
        proxy = DataProxy()
        proxy.get_all("user", "id")
        defer = proxy.execute()
        defer.addCallback(self._calc_result, now)
        return defer


    def _calc_result(self, proxy, now):
        """推荐计算
         过滤无法加入的推荐好友（用户的好友数达到上限, 不是自己）
        """
        pre_match = []
        users = proxy.get_all_result("user")
        """初次过滤"""
        user_friends = [id for id in utils.split_to_int(self.user.friends) if id > 0]
        for user in users:
            friends = [id for id in utils.split_to_int(user.friends) if id > 0]
            friends_apply = [id for id in utils.split_to_int(user.friends_apply) if id > 0]
            if len(friends) >= 30:
                continue
            elif user.level > int(float(data_loader.OtherBasicInfo_dict['friend_number_limit'].value)):
                continue 
            elif user.id == self.user.id:
                continue
            elif self.user.id in friends_apply:
                continue
            elif user.id in user_friends:
                if self.user.id in friends:
                    continue

            
          
            logger.notice("user_id = %s"%user.id)
            pre_match.append(user)
        logger.notice("pre_match = %s"% len(pre_match)) 
        if len(pre_match) <= 10:
            self.result = pre_match
        else:
            self._filter(pre_match, now)

        return self


    def _filter(self, pre_match, now):
        """进行筛选
        """
        #从近期繁荣度排名靠前的联盟中选择
        #active_unions = sorted(pre_match, key = lambda u:u.recent_prosperity, reverse = True)
        #active_unions = active_unions[:30]
        #num = min(len(active_unions), 10)
        self.result = random.sample(pre_match, 10)

        #从最近创建的联盟中选择
        #new_unions = []
        #for union in pre_match:
        #    if union in self.result:
        #        continue
        #    if now - union.create_time < 604800:#一周
        #        new_unions.append(union)
        #num = min(len(new_unions), 10)
        #self.result.extend(random.sample(new_unions, num))

