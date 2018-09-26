#coding:utf8
"""
Created on 2015-01-19
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 好友相关逻辑
"""

import time
from firefly.server.globalobject import GlobalObject
from twisted.internet.defer import Deferred
from utils import logger
from utils.timer import Timer
from utils import utils
from proto import friend_pb2
from datalib.global_data import DataBase
from datalib.data_loader import data_loader
from app import pack
from app import compare
from app import log_formater
from app.data.user import UserInfo
from app.data.friend import FriendInfo
from app.data.message import MessageInfo
from app.friend_matcher import FriendMatcher
from app.friend_recommender import FriendRecommender
from app.friend_member_matcher import FriendMemberMatcher
from datalib.data_proxy4redis import DataProxy

MAX_MSG_NUM = 21

class FriendProcessor(object):
    """处理好友相关逻辑
    包括：好G友推荐， 添加好友， 处理申请，好友聊天等
    """

    def get_friends(self, user_id, request):
        """ 获取推荐好友列表 """
        timer = Timer(user_id)

        req = friend_pb2.GetFriendsReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_get_friends, req, timer)
        defer.addErrback(self._get_friends_failed, req, timer)
        return defer


    def _calc_get_friends(self, data, req, timer):
        """
        Args:
            data[UserData]: 自己的数据
            req[]: 客户端请求
        Returns:
            data[UserData]: 处理后的数据
        """
        user = data.user.get()
        if req.type == req.SEARCH:
            matcher = FriendMatcher()
            friend_list = user.get_friends()
            friends = [id for id in friend_list if id > 0]

            if not req.friend_user_id in friends:
                matcher.add_condition(req.friend_user_id)
            else:
                matcher.add_condition(0)
            defer = matcher.match()

        elif req.type == req.RECOMMEND:
            matcher = FriendRecommender()
            matcher.add_condition(user)
            defer = matcher.match(timer.now)
                                                                                                                                                                                           
        defer.addCallback(self._calc_get_friends_result, data, req, timer)                                                                                                                 
        return defer 


    def _calc_get_friends_result(self, matcher, data, req, timer):
        #好友信息，查询数据库
        matcher_friend = FriendMemberMatcher()
        for user in matcher.result:
            matcher_friend.add_condition(user.id)
        defer = matcher_friend.match()
        defer.addCallback(self._calc_get_friends_info, matcher, data, req, timer) 
        return defer

 
    def _calc_get_friends_info(self, matcher_friend, matcher, data, req, timer):
        res = friend_pb2.GetFriendsRes()                                                                                                                                                  
        res.status = 0
        res.ret = friend_pb2.FRIEND_OK
        #proxy = DataProxy()
 
        for user in matcher.result:
            (id, name, icon_id, level, score) = matcher_friend.result[
                    user.id]
            message = res.friends.add() 
            message.user_id = id
            message.name = name
            message.icon_id = icon_id
            message.level = level
            message.score = score

        defer = DataBase().commit(data)
        defer.addCallback(self._get_friends_succeed, req, res, timer)
        return defer


    def _get_friends_succeed(self, data, req, res, timer):
        """请求处理成功"""

        user =  data.user.get()
        friend_list = user.get_friends()
        friends = [id for id in friend_list if id > 0]
        friend_num = len(friends)
        res.friend_num = friend_num
        response = res.SerializeToString()
        log = log_formater.output(data, "Get friends succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _get_friends_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Get friends failed[reason=%s]" % err)

        res = friend_pb2.GetFriendsRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK
        response = res.SerializeToString()

        logger.notice("Get friends failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def view_apply(self, user_id, request):
        """查看好友申请"""
        timer = Timer(user_id)

        req = friend_pb2.QueryFriendsReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_view_apply, req, timer)
        defer.addErrback(self._view_apply_failed, req, timer)
        return defer 


    def _calc_view_apply(self, data, req, timer):
        
        user = data.user.get()
        apply_list = [id for id in user.get_apply() if id > 0 ]
        condition = []
        if not req.friend_user_id == 0:
            #申请的好友id不在申请列表里面
            if not req.friend_user_id in apply_list:

                logger.notice("[user_id = %d] not in apply"%req.friend_user_id)
                #输入的id 不在好友申请列表中
                res = friend_pb2.QueryFriendsRes()
                res.status = 0
                res.ret = friend_pb2.NOTINAPPLY
                defer = DataBase().commit(data)
                defer.addCallback(self._view_apply_succeed, req, res, timer)

                return defer
            else:

                condition.append(req.friend_user_id)
        else:

            condition = apply_list
        matcher_friend = FriendMemberMatcher()
        decondition = condition[::-1]
        for id in decondition:
            matcher_friend.add_condition(id)
        defer = matcher_friend.match()
        defer.addCallback(self._calc_view_apply_info, decondition, data, req, timer)
        return defer
    
     
    def _calc_view_apply_info(self, matcher_friend, condition, data, req, timer):
        res = friend_pb2.QueryFriendsRes()
        res.status = 0
        res.ret = friend_pb2.FRIEND_OK

        for id in condition:
            (id, name, icon_id, level, score) = matcher_friend.result[
                    id]
            message = res.friends.add()
            message.user_id = id
            message.name = name
            message.icon_id = icon_id
            message.level = level
            message.score = score
            logger.notice("message = %s"% message)
        defer = DataBase().commit(data)
        defer.addCallback(self._view_apply_succeed, req, res, timer)
        return defer


    def _view_apply_succeed(self, data, req, res, timer):
        """请求处理成功"""
        user =  data.user.get()
        friend_list = user.get_friends()
        friends = [id for id in friend_list if id > 0]
        friend_num = len(friends)
        res.friend_num = friend_num

        response = res.SerializeToString()
        log = log_formater.output(data, "View friend apply succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _view_apply_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("view friend apply failed[reason=%s]" % err)

        res = friend_pb2.QueryFriendsRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK
        response = res.SerializeToString()                                                                                                                                                
        logger.notice("view friend apply failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def view_friend(self, user_id, request):
        """查看好友"""
        timer = Timer(user_id)

        req = friend_pb2.ViewFriendsReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_view_friend, req, timer)
        defer.addErrback(self._view_friend_failed, req, timer)
        return defer


    def _calc_view_friend(self, data, req, timer):

        user = data.user.get()
        friends_list = user.get_friends()
        logger.notice("friend_list = %s"%friends_list)

        condition = []
        if not req.friend_user_id == 0:
            if not req.friend_user_id in friends_list:
                res = friend_pb2.ViewFriendsRes()                                                                                                                                                 
                res.status = 0 
                res.ret = friend_pb2.NOTINFRIENDS
                defer = DataBase().commit(data)
                defer.addCallback(self._view_friend_succeed, req, res, timer)
                return defer 
            else:
                condition.append(req.friend_user_id)
        else:
            condition = friends_list

        matcher_friend = FriendMemberMatcher()
        for id in condition:
            if id != 0:
                matcher_friend.add_condition(id)
        defer = matcher_friend.match()
        defer.addCallback(self._calc_view_friend_info, condition, data, req, friends_list, timer)
        return defer


    def _calc_view_friend_info(self, matcher_friend, condition, data, req, friends_list, timer): 
        res = friend_pb2.ViewFriendsRes()
        res.status = 0
        ret = friend_pb2.FRIEND_OK

        for id in condition:
            """去掉删除置0的id"""
            if not id == 0:
                logger.notice("ID = %d"%id)
                (id, name, icon_id, level, score) = matcher_friend.result[
                        id]
                message = res.friends.add()
                message.user_id = id
                message.name = name
                message.icon_id = icon_id
                message.level = level
                message.score = score
                message.index = friends_list.index(id)

        message_list = data.message_list.get_all()
        logger.notice("len =%d"%len(message_list))
        for message_info in message_list:
            if message_info.status == 1:
                message = res.messages.add()
                message.user_id = message_info.user_id
                message.friend_index = message_info.friend_index
                message.content = message_info.content
                message.status  = message_info.status
                message.message_from  = message_info.message_from
                logger.notice("message = %s"%message.content)
            else:
                continue
        defer = DataBase().commit(data)
        defer.addCallback(self._view_friend_succeed, req, res, timer)
        return defer


    def _view_friend_succeed(self, data, req, res, timer):
        """请求处理成功"""
        user =  data.user.get()
        friend_list = user.get_friends()
        friends = [id for id in friend_list if id > 0]
        friend_num = len(friends)
        res.friend_num = friend_num
        response = res.SerializeToString()
        log = log_formater.output(data, "View friend succeed", req, res, timer.count_ms())
        logger.notice(log)

        return response


    def _view_friend_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("view friend failed[reason=%s]" % err)

        res = friend_pb2.ViewFriendsRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK
        response = res.SerializeToString()
        logger.notice("view friend  failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def add_friend(self, user_id, request):
        """添加好友"""
        timer = Timer(user_id)

        req = friend_pb2.AddFriendReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_add_friend, req, timer)
        defer.addErrback(self._add_friend_failed, req, timer)
        return defer


    def _calc_add_friend(self, data, req, timer):
        user = data.user.get()
        #friend_list = user.get_friends
        """过滤掉id 为0 的元素"""
        friends = [id for id in utils.split_to_int(user.friends) if id > 0]
        friends_apply = [id for id in utils.split_to_int(user.friends_apply) if id > 0]

        if len(friends) >= 30:
            res = friend_pb2.AddFriendRes()
            res.status = 0
            res.ret = friend_pb2.FRIENDFULL
            defer = DataBase().commit(data)
            defer.addCallback(self._add_friend_succeed, data, req, res, timer)
            return defer
        #当在好友申请中时直接添加
        if req.friend_id in friends_apply:

                app_req = friend_pb2.ManageFriendsReq()                                                                                                                                      
                app_req.user_id = req.user_id                                                                                                                                           
                app_req.friend_id = req.friend_id                                                                                                                                           
                app_req.status = 2                                                                                                                                           
                request = app_req.SerializeToString()

                self.manage_friend(req.user_id, request)

                res = friend_pb2.AddFriendRes()
                res.status = 0                
                res.ret = friend_pb2.FRIEND_OK

                defer = DataBase().commit(data)
                defer.addCallback(self._add_friend_succeed, data, req, res, timer)
                return defer

        app_req = friend_pb2.AddFriendReq()
        app_req.friend_id = req.user_id
        app_req.user_id = req.friend_id
        request = app_req.SerializeToString()
        defer = DataBase().commit(data) 
        defer = GlobalObject().root.callChild(
                'portal', "forward_receive_friend", req.friend_id, request)

        res = friend_pb2.AddFriendRes()
        res.status = 0
        res.ret = friend_pb2.APPLYSUCCEED

        defer.addCallback(self._add_friend_succeed, data,  req, res, timer)
        return defer 


    def _add_friend_succeed(self, app_response, data, req, res, timer):
        """请求处理成功"""
        user =  data.user.get()                                                                                                                                                           
        friend_list = user.get_friends()                                                                                                                                                  
        friends = [id for id in friend_list if id > 0]                                                                                                                                    
        friend_num = len(friends)
        res.friend_num = friend_num
        response = res.SerializeToString()
        log = log_formater.output(data, "Add friend  succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response


    def _add_friend_failed(self, err, req, timer):                                                                                                                                    
        """请求处理失败"""                                                                                                                                                                
        logger.fatal("Add friend  failed[reason=%s]" % err)                                                                                                                     

        res = friend_pb2.AddFriendRes()                                                                                                                                                   
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK                                                                                                                                                                   
        response = res.SerializeToString()        
                                                                                                                                        
        logger.notice("Add friend  failed[user_id=%d][req=%s][res=%s][consume=%d]" %                                                                                           
                (timer.id, req, res, timer.count_ms()))                                                                                                                                   
        return response           


    def receive_friend(self, user_id, request):
        """ 接收好友请求
            friend_id 好友的user_id
        """
        timer = Timer(user_id)
        logger.notice("user_id =%d"%user_id) 
        req = friend_pb2.AddFriendReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_friend, req, timer)
        defer.addErrback(self._receive_friend_failed, req, timer)
        return defer


    def _calc_receive_friend(self, data, req, timer):
        logger.notice("===========1")
        #user = data.user.get()
        logger.notice("222222")
        user = data.user.get()
        apply_list = user.get_apply()
        #已经在申请列表中不添加
        logger.notice("===========friend_id=")
        if not req.friend_id in apply_list:
            apply_list.append(req.friend_id)
            user.friends_apply = utils.join_to_string(apply_list)
        else: 
            index = apply_list.index(req.friend_id)
            apply_list[index] = 0
            apply_list.append(req.friend_id)
            user.friends_apply = utils.join_to_string(apply_list)
 
        defer = DataBase().commit(data)

        res = friend_pb2.AddFriendRes()
        res.status = 0
        res.ret = friend_pb2.FRIEND_OK
        defer.addCallback(self._receive_friend_succeed, req, res, timer)
        return defer


    def _receive_friend_succeed(self, data, req, res, timer):
        """请求处理成功"""
        log = log_formater.output(data, "Receive friend apply succeed", req, res, timer.count_ms())
        logger.notice(log)
        return res


    def _receive_friend_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Receive friend apply  failed[reason=%s]" % err)

        res = friend_pb2.AddFriendRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK

        logger.notice("Receive friend  apply  failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return res


    def manage_friend(self, user_id, request):
        """ 好友管理 """
        
        timer = Timer(user_id)

        req = friend_pb2.ManageFriendsReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_manage_friend, req, timer)
        defer.addErrback(self._manage_failed, req, timer)
        return defer


    def _calc_manage_friend(self, data, req, timer):
         
        user = data.user.get()
        defer = Deferred() 

        if req.status == 2:
            defer.addCallback(self._accept, user, req, timer)
        elif req.status == 3:
            defer.addCallback(self._refuse, user, req, timer)
        elif req.status == 4:
            defer.addCallback(self._delete, user, req, timer)
        else:
             raise Exception("Invalid operation[status=%d]" % req.status)

        defer.addCallback(self._post_manage, data, req, timer)
        defer.callback(data)
        return defer


    def _post_manage(self, res, data, req, timer):
        user =  data.user.get()
        friend_list = user.get_friends()
        friends = [id for id in friend_list if id > 0]
        friend_num = len(friends) 
        res.friend_num = friend_num
        logger.notice("RES=%s"%res)

        defer = DataBase().commit(data)

        defer.addCallback(self._manage_succeed, req, res, timer)
        return defer


    def _manage_succeed(self, data, req, res, timer):

        response = res.SerializeToString()
        logger.notice("Manage friend succeed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response 


    def _manage_failed(self, err, req, timer):

        logger.fatal("Manage friend failed[reason=%s]" % err)
        res = friend_pb2.ManageFriendsRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK
        response = res.SerializeToString()
        logger.notice("Manage union failed"
                "[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _accept(self, data, user, req, timer):
        """接受好友请求"""


        defer = DataBase().get_data(data.id)
        defer.addCallback(self._calc_accept_friend, req, timer)
        defer.addErrback(self._manage_failed, req, timer)
        return defer


    def _calc_accept_friend(self, data, req, timer):

        proxy = DataProxy()
        proxy.search("user", req.friend_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_accept_friend_info, data, req, timer)
        return defer


    def _calc_accept_friend_info(self, proxy, data, req, timer):
        if not proxy.get_result("user", req.friend_id):
            res = friend_pb2.ManageFriendsRes()
            res.status = 0                                                                                                                                                                    
            res.ret = friend_pb2.WITHOUTID
            defer = DataBase().commit(data)
            return self._manage_succeed(data, req, res, timer) 


        app_req = friend_pb2.ManageFriendsReq()                                                                                                                                           
        app_req.friend_id = req.user_id                                                                                                                                                   
        app_req.user_id = req.friend_id                                                                                                                                                   
        app_req.status = 2                                                                                                                                                                
        request = app_req.SerializeToString()
       # friendstr = proxy.get_result("user", req.friend_id).friends
       # logger.notice("friendstr=%s"%friendstr)
       # friend = utils.split_to_int(friendstr)
       # friend_list = [id for id in friend if id >0]
       # logger.notice("size = %d"%len(friend_list))
       # logger.notice("friend_id = %d"%req.friend_id)
        user =  data.user.get()
        friend_list = user.get_friends()
        friends = [id for id in friend_list if id > 0]
        if len(friends) >= 30:
            res = friend_pb2.ManageFriendsRes()
            res.status = 0
            res.ret = friend_pb2.FRIENDFULL
            return res
        
        defer = GlobalObject().root.callChild(
                'portal', "forward_receive_accept", req.friend_id, request)                                                                                                                                                                                      
        defer.addCallback(self._accept_result, data, req, timer)
        return defer


    def _accept_result(self, app_response, data, req, timer):
        logger.notice("app_response = %s"%app_response)
        user =  data.user.get()
        apply_list = user.get_apply()
        friend_list = user.get_friends()
        friends = [id for id in friend_list if id > 0]

        if len(friends) >= 30:
            res = friend_pb2.ManageFriendsRes()
            res.status = 0
            res.ret = friend_pb2.FRIENDFULL
            return res
        elif req.friend_id in friend_list :
            res = friend_pb2.ManageFriendsRes()
            res.status = 0
            res.ret = friend_pb2.FRIEND_OK
            return res

        index = 0
        if req.friend_id in apply_list:
            #不能重复添加
            if not req.friend_id in friend_list:
                apply_list.remove(req.friend_id)
                index = len(friend_list)
                friend_list.append(req.friend_id)
            else: 
                res = friend_pb2.ManageFriendsRes()
                res.status = 0
                res.ret = friend_pb2.ALREADYIN
                return res
        else:
            
            res = friend_pb2.ManageFriendsRes()
            res.status = 0
            return res

        user.friends_apply = utils.join_to_string(apply_list)
        user.friends = utils.join_to_string(friend_list)
        logger.notice("id = %d, friend_id = %d, index = %d"% (data.id, req.friend_id, index))
        #初始化好友关系                                                                                                                                                                 
        friendinfo = FriendInfo.create(data.id, req.friend_id, index)
        data.friend_list.add(friendinfo)

        return self._post_accept(data, timer, req, apply_list)


    def _post_accept(self, data, timer, req, apply_list):     

        matcher_friend = FriendMemberMatcher()
        for id in apply_list:
            if id != 0:
                matcher_friend.add_condition(id)
        defer = matcher_friend.match()
        defer.addCallback(self._pack_manage_response, apply_list, data, req, timer)
        return defer

    def _pack_manage_response(self, matcher_friend, apply_list, data, req, timer):
        res = friend_pb2.ManageFriendsRes()                                                                                                                                               
        res.status = 0
        res.ret = friend_pb2.FRIEND_OK

        for id in apply_list:
            if id != 0:
                (id, name, icon_id, level, score) = matcher_friend.result[                                                                                                                    
                        id]                                                                                                                                                              
                message = res.friends.add()                                                                                                                                                   
                logger.notice("======================4")                                                                                                                                      
                message.user_id = id                                                                                                                                                          
                message.name = name                                                                                                                                                           
                message.icon_id = icon_id                                                                                                                                                     
                message.level = level                                                                                                                                                         
                message.score = score                                                                                                                                                         
                logger.notice("message = %s"% message)
        # return self._manage_succeed(data, req, res, timer)        
        return res                       


    def _pack_manage_wrong_response(self, ret, data, req, timer):
        res = friend_pb2.ManageFriendsRes()
        res.status = 0
        res.ret = ret
        
        return res 


    def receive_accept_friend(self, user_id, request):
        """在好友的好友列表中添加自己"""
        timer = Timer(user_id)

        req = friend_pb2.ManageFriendsReq()
        req.ParseFromString(request)
        defer = DataBase().get_data(user_id)
        defer.addCallback(self._accept_receive, req, timer)
        defer.addErrback(self._receive_accept_friend_failed, req, timer)
        return defer 



    def _accept_receive(self, data, req, timer):

        logger.notice("================ac2")
        user = data.user.get()
        friend_list = user.get_friends()
        index = 0 
        friends = [id for id in friend_list if id > 0]
        if len(friends) >= 30:
            return self._pack_manage_wrong_response(friend_pb2.FRIENDFULLOTHER, data, req, timer)
        if not req.friend_id in friend_list:
            index = len(friend_list)
            friend_list.append(req.friend_id)
            user.friends = utils.join_to_string(friend_list)
            #初始化好友关系                                                                                                                                                                 
            friendinfo = FriendInfo.create(data.id, req.friend_id, index)
            data.friend_list.add(friendinfo)
            logger.notice("FRIEND = %d"% len(data.friend_list))
        else:
            return self._pack_manage_wrong_response(friend_pb2.ALREADYIN, data, req, timer)

        defer = DataBase().commit(data)
        res = friend_pb2.ManageFriendsRes()
        res.status = 0
        res.ret = friend_pb2.FRIEND_OK
        defer.addCallback(self._receive_accept_friend_succeed, req, res, timer)
        return defer
       

    def _receive_accept_friend_succeed(self, data, req, res, timer):
        """请求处理成功"""
        response = res.SerializeToString()
        log = log_formater.output(data, "Receive accept friend apply succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response     


    def _receive_accept_friend_failed(self, err, req, timer):
        """请求处理失败"""
        logger.fatal("Receive accept friend apply  failed[reason=%s]" % err)

        res = friend_pb2.ManageFriendsRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK
        response = res.SerializeToString()

        logger.notice("Receive accept friend  apply  failed[user_id=%d][req=%s][res=%s][consume=%d]" %
                (timer.id, req, res, timer.count_ms()))
        return response


    def _refuse(self, data, user, req, timer):
        """拒绝好友申请"""
        apply_list = user.get_apply()
        if req.friend_id in apply_list:
            apply_list.remove(req.friend_id)
            logger.notice("apply_list=%s"%len(apply_list))
        else :
            return self._pack_manage_wrong_response(friend_pb2.NOTINAPPLY, data, req, timer) 

        user.friends_apply = utils.join_to_string(apply_list)
        return self._post_accept(data, timer, req, apply_list)


    def _delete(self, data, user, req, timer):
        """ 删除好友 """
        friend_list = user.get_friends()

        index = 0
        if req.friend_id in friend_list:
            index = friend_list.index(req.friend_id)
            friend_list[index] = 0
        else:
            return self._pack_manage_wrong_response(friend_pb2.NOTINFRIENDS, data, req, timer)

        user.friends = utils.join_to_string(friend_list) 
        id = FriendInfo.generate_id(user.id, index)
        logger.notice("id = %d"%id)
        return self._post_accept(data, timer, req, friend_list)


    def chat_friend(self, user_id, request): 
        """  好友聊天 """
        timer = Timer(user_id)

        req = friend_pb2.ChatFriendReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_chat_friend, req, timer)
        defer.addErrback(self._chat_friend_failed, req, timer)
        return defer


    def _calc_chat_friend(self, data, req, timer):

        logger.notice("TEXT = %s"% req.content)
        proxy = DataProxy()
        proxy.search("user", req.friend_id)
        defer = proxy.execute()
        defer.addCallback(self._calc_chat_friend_info, data, req, timer)
        return defer


    def _calc_chat_friend_info(self, proxy, data, req, timer):

        res = friend_pb2.ChatFriendRes()
        res.status = 0
        if not proxy.get_result("user", req.friend_id):
            user = data.user.get()
            friend_list = user.get_friends()
            index = friend_list.index(req.friend_id)
            friend_list[index] = 0
            user.friends = utils.join_to_string(friend_list)
            id = FriendInfo.generate_id(user.id, index)
            logger.notice("id = %d"%id)
            data.friend_list.delete(id)
            res.ret = friend_pb2.WITHOUTID
            return self._chat_friend_succeed(data, req, res, timer)
        logger.notice("content = %s"% req.content)


        message_list = data.message_list.get_all()
        for message in message_list:
            message.status = 2       


        if not req.HasField("content"):
            return self._pack_chat_response(data, req, timer)
        else:
            friendstr = proxy.get_result("user", req.friend_id).friends
            friend = utils.split_to_int(friendstr) 
            user = data.user.get()
            message_list = data.message_list.get_all()
            #最后一条消息的index加一
            msg_index = 1
            if not len(message_list) == 0:
                msg_index = message_list[-1].message_index + 1
            logger.notice("msg_index =%d"%msg_index)
            #当自己id 在好友的好友列表中, 将消息的index 放入自己的friend中
            logger.notice("frinds=%s"%friend)
            if req.user_id in friend:
                friend_id = FriendInfo.generate_id(data.id, req.friend_index)
                self._eliminate_msg(data, friend_id, req.friend_index, MAX_MSG_NUM - 1)
                message = MessageInfo.create(data.id, req.friend_index, msg_index, req.content, 2, 1)
                logger.notice("MSG_ID=%s"%message.content)
                
                data.message_list.add(message)
                #friend_id = FriendInfo.generate_id(data.id, req.friend_index)
                message_index = data.friend_list.get(friend_id).message_index_list
                message_index_list = utils.split_to_int(message_index)
                message_index_list.append(msg_index)
                data.friend_list.get(friend_id).message_index_list = utils.join_to_string(message_index_list)
                logger.notice("message_index_list = %s"%data.friend_list.get(friend_id).message_index_list)
                #将自己id 和好友id 互换
                app_req = friend_pb2.ChatFriendReq()
                app_req.friend_id = req.user_id
                app_req.user_id = req.friend_id
                app_req.content = req.content
                request = app_req.SerializeToString()
                GlobalObject().root.callChild("portal", "forward_receive_chat", req.friend_id, request)
                 
                return self._pack_chat_response(data, req, timer)
            else:
                res.ret = friend_pb2.CANNOTCHAT
                return self._chat_friend_succeed(data, req, res, timer)
           
    def _pack_chatwrong_response(self, data, ret):
        res = friend_pb2.ChatFriendRes()
        res.status = 0
        res.ret = ret
        return res
      

    def _pack_chat_response(self, data, req, timer): 
        """封装聊天记录"""
        res = friend_pb2.ChatFriendRes()
        res.status = 0
        res.ret = friend_pb2.FRIEND_OK 
        user_id = req.user_id
        friend_index = req.friend_index
        user = data.user.get()
        id = FriendInfo.generate_id(user_id, req.friend_index)
        logger.notice("friend_id = %d"% id)
        friend = data.friend_list.get(id)
        assert friend != None
        if friend == None:
            return res
        else:
            logger.notice("======================1")
            message_index = friend.message_index_list
            logger.notice("msg_index= %s"%message_index)
            message_index_list = utils.split_to_int(message_index)[::-1]
            num = min (len(message_index_list), 21)
            msg_index_list = message_index_list[:num]
            logger.notice("msg_index=%s"%msg_index_list)
            logger.notice("NUM=%d"%num)
            for msg_index in msg_index_list[::-1]:
                message_info = res.messages.add()
                message_id = MessageInfo.generate_id(user_id, friend_index, msg_index)
                logger.notice("MSG_ID=%d"%message_id)
                message = data.message_list.get(message_id)
                message.status = 2
                message_info.user_id = user_id
                message_info.friend_index = friend_index
                message_info.content = message.content
                message_info.status = message.status
                message_info.message_from = message.message_from
                
                logger.notice("message_info = %s"% message_info)
        defer = DataBase().commit(data)
        return self._chat_friend_succeed(data, req, res, timer)
    
    def _chat_friend_succeed(self, data, req, res, timer):

        response = res.SerializeToString()
        log = log_formater.output(data, "Chat friend succeed", req, res, timer.count_ms())
        logger.notice(log)
        return response
       

    def _chat_friend_failed(self, err, req, timer):
        logger.fatal("Receive chat notice failed[reason=%s]" % err)
        res = friend_pb2.ChatFriendRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK
        response = res.SerializeToString()

        logger.notice("Receive chat notice failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))

        return response 
   

    def receive_chat_res(self, user_id, request):
        """接收的好友消息"""
        timer = Timer(user_id)

        req = friend_pb2.ChatFriendReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_receive_chat_friend, req, timer)
        defer.addErrback(self._receive_chat_failed, req, timer)
        return defer


    def _calc_receive_chat_friend(self, data, req, timer):

        user = data.user.get()
        logger.notice("FRIEDNS= %s"%user.id)
        friend_index = utils.split_to_int(user.friends).index(req.friend_id)
        friend_id = FriendInfo.generate_id(data.id, friend_index)
        logger.notice("friend_id = %d"%friend_id)
        friend_msg = data.friend_list.get(friend_id)
        user_id = data.id
        message_list = data.message_list.get_all()
        friendstr = user.friends
        friend = utils.split_to_int(friendstr)
        msg_index = 1
        if not len(message_list) == 0:
            msg_index = message_list[-1].message_index+1
        self._eliminate_msg(data, friend_id, friend_index, MAX_MSG_NUM - 1)
        message = MessageInfo.create(data.id, friend_index, msg_index, req.content, 1, 2)
        data.message_list.add(message)
        
        message_index = data.friend_list.get(friend_id).message_index_list
        message_index_list = utils.split_to_int(message_index)
        message_index_list.append(msg_index)
        data.friend_list.get(friend_id).message_index_list = utils.join_to_string(message_index_list)

        res = friend_pb2.ChatFriendRes()
        res.status = 0
        res.ret = friend_pb2.FRIEND_OK

        message_index = friend_msg.message_index_list
        message_index_list = utils.split_to_int(message_index)[::-1]
        num = min (len(message_index_list), 20)
        msg_index_list = message_index_list[:num]

        for msg_index in msg_index_list[::-1]:
            message_info = res.messages.add()
            message_id = MessageInfo.generate_id(user_id, friend_index, msg_index)
            message =  data.message_list.get(message_id)     
            message_info.user_id = user_id
            message_info.friend_index = friend_index
            message_info.content = message.content
            message_info.status = message.status
            message_info.message_from = message.message_from

            logger.notice("message_info = %s"% message_info)

       # response = res.SerializeToString()
       # logger.notice("====================1")
       # defer = GlobalObject().root.callChild("portal", "push_chat_record", data.id, response) 
       # logger.notice("====================2")

        defer = DataBase().commit(data)
        defer.addCallback(self._receive_chat_succeed, req, res, timer)
        return defer

    def _receive_chat_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Receive chat notice succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response

    def _receive_chat_failed(self, err, req, timer):                                                                                                                                           
        logger.fatal("Receive chat notice failed[reason=%s]" % err)       
        res = friend_pb2.ChatFriendRes()
        res.status = -1
        res.ret = friend_pb2.FRIEND_OK                                                                                                                                                                   
        response = res.SerializeToString()                                                                                                                                                
        logger.notice("Receive chat notice failed[req=%s][res=%s][consume=%d]" %                                                                                                      
                (req, res, timer.count_ms()))  
        return response



    def _eliminate_msg(self, data, friend_id, friend_index,  remain_num = MAX_MSG_NUM):
        """淘汰消息  friend_id: friend 的主键id 
        """
        #1.条数淘汰
        message_list = data.message_list.get_all()
        message_index =data.friend_list.get(friend_id).message_index_list
        message_index_list = utils.split_to_int(message_index)
        sort_list = message_index_list[::-1]
        delete_list = []
       
        if len(sort_list) > remain_num:
    
            delete_list = sort_list[remain_num:]
            logger.notice("delete_list = %s"%delete_list)
    
        logger.debug("Delete overmuch message num=%d" % len(delete_list))
        #删除末尾数据                                                                                                                                                                         
        for delete_record in delete_list:
            message_index_list.remove(delete_record)
            data.friend_list.get(friend_id).message_index_list = utils.join_to_string(message_index_list)
            message_id = MessageInfo.generate_id(data.id, friend_index, delete_record)
            record = data.message_list.get(message_id)
            logger.notice("Delete one message_list[id=%d][message_index=%d]"
                    % (message_id, delete_record))
            data.message_list.delete(message_id)


    def refresh_chat(self, user_id, request):
        """刷新红点"""
        timer = Timer(user_id)

        req = friend_pb2.RefreshStatusReq()
        req.ParseFromString(request)

        defer = DataBase().get_data(user_id)
        defer.addCallback(self._calc_refresh_chat, req, timer)
        defer.addErrback(self._refresh_chat_failed, req, timer)
        return defer


    def _calc_refresh_chat(self, data, req, timer):
       
        res = friend_pb2.RefreshStatusRes()
        res.status = 0 
        message_list = data.message_list.get_all()
                                                                                                                                                                                          
        res.chat = 0                                                                                                                                                                      
        for message in message_list:                                                                                                                                                      
            if message.status == 1:                                                                                                                                                       
                res.chat = 1                                                                                                                                                              
                break
        defer = DataBase().commit(data)
        defer.addCallback(self._refresh_chat_succeed, req, res, timer)
        return defer


    def _refresh_chat_succeed(self, data, req, res, timer):
        response = res.SerializeToString()
        logger.notice("Refresh chat  succeed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response


    def _refresh_chat_failed(self, err, req, timer):
        logger.fatal("Refresh chat failed[reason=%s]" % err)
        res = friend_pb2.RefreshStatusRes()
        res.status = -1
        response = res.SerializeToString()
        logger.notice("Refresh chat notice failed[req=%s][res=%s][consume=%d]" %
                (req, res, timer.count_ms()))
        return response 
         
