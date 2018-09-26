#coding:utf-8
"""
Created on 2015-01-18
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 管理在线用户的连接
"""

import time
from firefly.server.globalobject import GlobalObject
from firefly.utils.singleton import Singleton
from utils.redis_agent import RedisAgent
from utils import logger


class TokenRedisAgent(object):
    """访问 Token redis
    """
    __metaclass__ = Singleton


    def connect(self, ip, port, db = '0', password = None, timeout = 1):
        """初始化
        Args:
            timeout : 连接超时事件，单位 s
        """
        self.redis = RedisAgent()
        self.redis.connect(ip, port, db, password, timeout)
        logger.trace("Connect to redis success[addr=%s:%s]" % (ip, port))


    def get(self, token):
        """根据 token 获得 user id
        """
        return self.redis.client.get("TOKEN%d" % token)


    def active(self, user_id, now):
        """标记玩家活跃
        """
        server_id = GlobalObject().server_id
        self.redis.client.zadd("ONLINE%d" % server_id, now, user_id)


class UserInfo(object):
    """一个在线玩家的连接信息
    """

    def __init__(self, session_id, token, user_id, ip, port):
        self.session_id = session_id
        self.token = token
        self.user_id = user_id
        self.ip = ip
        self.port = port

        self.login = int(time.time()) #登录时间戳
        self.update()


    def update(self):
        self.active = int(time.time()) #活跃时间戳
        TokenRedisAgent().active(self.user_id, self.active)


    def is_active(self):
        now = int(time.time())
        INACTIVE_TIME = 300 #5 min
        if now - self.active >= INACTIVE_TIME:
            return False
        return True


class OnlineManager(object):
    """管理 Portal 模块和客户端的连接"""
    __metaclass__ = Singleton


    #response的缓存策略：达到上限后，按照最不活跃的用户id，淘汰掉一批缓存数据
    BUFFER_MAX_NUM = 1000        #存储上限
    BUFFER_ELIMINATE_NUM = 200    #一次淘汰的数量

    def __init__(self):
        self._factory = GlobalObject().netfactory

        self._token_dict = {}   # token <-> UserInfo
        self._session_dict = {} # session id <-> token
        self._id_dict = {}      # user id <-> token
        self._response_dict = {}     # user id <-> (seq_id, response, active_time)

        self._enable_test = GlobalObject().json_config.get("test")


    def get_all_inactive_user_id(self):
        """获取所有非活跃状态的用户 user id
        """
        id_list = []
        for user in self._token_dict.values():
            if not user.is_active():
                id_list.append(user.user_id)

        return id_list


    def update_user(self, token, conn):
        """用户处于活动状态，更新信息
        Returns:
            user_id: int
            -1 表示失败
        """
        if token not in self._token_dict:
            #用户登录
            if not self._add_user_info(token, conn):
                return -1
        else:
            #更新在线信息
            if not self._update_user_info(token, conn):
                return -1

        if len(self._response_dict) >= self.BUFFER_MAX_NUM:
            self.eliminate_response()

        return self._token_dict[token].user_id


    def delete_user(self, conn):
        """用户主动断开连接，更新信息
        """
        session_id = conn.transport.sessionno
        if session_id in self._session_dict:
            token = self._session_dict[session_id]
            self._delete_user_info(token)


    def _add_user_info(self, token, conn):
        """
        用户上线：建立新连接
        Args:
            token: 玩家登录 token(gate 模块分配)
            conn: 连接信息
        """
        #session_id : 连接 id
        session_id = conn.transport.sessionno
        ip = conn.transport.client[0]
        port = conn.transport.client[1]

        if session_id in self._session_dict:
            #连接重复，这是异常情况，并不应该发生，需要排查
            #或者是 SDK （比如腾讯 YSDK）发起了重新登录的请求，token 发生变更
            logger.warning("Connection duplicated[session id=%d]" % session_id)
            old_token = self._session_dict[session_id]
            self._delete_user_info(old_token)

        user_id = self._fetch_user_id(token)
        if user_id == -1:
            #获取玩家 user id 失败: token 已经失效，断开当前玩家的连接
            logger.warning("Token invalid[token=%d]" % token)
            logger.notice('User abort[token=%d][session id=%d][addr=%s:%d]' %
                    (token, session_id, ip, port))
            self._factory.loseConnection(session_id)
            return False

        if user_id in self._id_dict:
            #帐号重复登录，将之前登录的连接信息删除
            logger.warning("User has already login[user id=%d]" % user_id)
            old_token = self._id_dict[user_id]
            self._delete_user_info(old_token)

        info = UserInfo(session_id, token, user_id, ip, port)
        self._token_dict[token] = info
        self._session_dict[session_id] = token
        self._id_dict[user_id] = token

        logger.notice('User login[token=%d][user id=%d][session id=%d][addr=%s:%d]' %
                (token, info.user_id, info.session_id, info.ip, info.port))

        return True


    def _update_user_info(self, token, conn):
        """更新用户在线信息
        """
        session_id = conn.transport.sessionno
        if session_id not in self._session_dict:
            #新连接
            #可能是用户重新建立了连接，没有关闭旧连接
            old_user = self._token_dict[token]
            old_session_id = old_user.session_id
            logger.warning("User reconnect unexpected"
                    "[token=%d][user id=%d][old session id=%d][old addr=%s:%d]" %
                    (token, old_user.user_id, old_user.session_id, old_user.ip, old_user.port))
            self._delete_user_info(token)
            return self._add_user_info(token, conn)

        assert self._session_dict[session_id] == token
        self._token_dict[token].update()
        
        return True


    def _delete_user_info(self, token):
        """用户离线：删除连接信息
        """
        user = self._token_dict.pop(token)
        assert self._session_dict[user.session_id] == token
        self._session_dict.pop(user.session_id)
        assert self._id_dict[user.user_id] == token
        self._id_dict.pop(user.user_id)

        logger.notice('User logout[token=%d][user id=%d][session id=%d][addr=%s:%d]' %
                (token, user.user_id, user.session_id, user.ip, user.port))


    def _fetch_user_id(self, token):
        """
        通过 token 获取 user id（访问 redis）
        Returns:
            user_id: int
            -1 表示失败
        """
        #测试模式
        if self._enable_test:
            return token

        user_id = TokenRedisAgent().get(token)
        if user_id is None:
            logger.debug("Get user id by token failed[token=%d]" % token)
            return -1

        user_id = int(user_id)
        return user_id


    def _disconnect_user(self, token):
        """强制断线用户
        """
        user = self._token_dict[token]

        logger.notice('User abort[token=%d][user id=%d][session id=%d][addr=%s:%d]' %
                (token, user.user_id, user.session_id, user.ip, user.port))
        self._factory.loseConnection(user.session_id)
        self._delete_user_info(token)


    def get_user_session_id(self, user_id):
        """根据 user id 获得 session id
        玩家不在线返回 -1
        """
        if user_id in self._id_dict:
            token = self._id_dict[user_id]
            user = self._token_dict[token]
            if user.is_active():
                return user.session_id
            else:
                pass
                #TODO delete user info

        return -1


    def update_response(self, user_id, seq_id, response):
        """存储在线用户对应的上一条seq id对应的请求返回值
        """
        #if user_id not in self._id_dict:
        #    logger.warning("User not online[user_id=%d]" % user_id)
        #    return

        #if seq_id == 1:
        #    #seq id 为1的请求不缓存
        #    #因为客户端每次登陆都是从1开始，假设init请求就出错，就会缓存错误结果导致一直无法登陆了
        #    return

        now = int(time.time()) #活跃时间戳
        self._response_dict[user_id] = (seq_id, response, now)
        logger.debug("update seq response[len=%s][total_res_num=%d]" 
                % (len(response), len(self._response_dict)))
        

    def fetch_response(self, user_id, seq_id):
        """
        """
        if user_id not in self._id_dict:
            logger.warning("User not online[user_id=%d]" % user_id)
            return

        if self._response_dict.has_key(user_id):
            (exist_seq_id, response, active_time) = self._response_dict[user_id]
            if seq_id != exist_seq_id:
                return None
            else:
                logger.notice("Get response by the same seq id[user_id=%d][seq_id=%d]"
                        % (user_id, seq_id))

            now = int(time.time()) #活跃时间戳
            self._response_dict[user_id] = (exist_seq_id, response, now)
            return response

        else:
            return None


    def eliminate_response(self):
        """淘汰过量的response存储
        """
        users_id = self._response_dict.keys()
        if len(users_id) < self.BUFFER_ELIMINATE_NUM:
            logger.warning("Do not need to eliminate[res_len=%d]" % len(users_id))
            return

        actives_time = []
        for user_id in users_id:
            actives_time.append(self._response_dict[user_id][2])

        for i in range(len(actives_time)):
            for j in range(i + 1, len(actives_time)):
                if actives_time[i] > actives_time[j]:
                    #交换时间
                    tmp_time = actives_time[j]
                    actives_time[j] = actives_time[i]
                    actives_time[i] = tmp_time
                    #交换user id
                    tmp_user = users_id[j]
                    users_id[j] = users_id[i]
                    users_id[i] = tmp_user

        delete_users_id = users_id[0:self.BUFFER_ELIMINATE_NUM]
        logger.notice("eliminate response[eliminate_num=%d][total_num=%d]" 
                % (len(delete_users_id), len(users_id)))

        for user_id in delete_users_id:
            self._response_dict.pop(user_id)
        







