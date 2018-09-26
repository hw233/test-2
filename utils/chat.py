#coding:utf8
"""
Created on 2016-07-07
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 聊天
"""
import ssl
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError
from sleekxmpp.exceptions import IqTimeout
from utils import logger


class ChatRoomCreator(ClientXMPP):
    """聊天室创建者
    连接 XMPP 服务器（OpenFire server）
    建立聊天室，设置名称和密码
    """

    def __init__(self, jid, password, roomname, roompasswd):
        logger.debug("Init ChatRoomCreator[jid=%s][passwd=%s][roomname=%s][roompasswd=%s]" %
                (jid, password, roomname, roompasswd))

        ClientXMPP.__init__(self, jid, password)

        self.roomname = roomname
        self.roompasswd = roompasswd

        self.add_event_handler("session_start", self.session_start)
        #self.add_event_handler("message", self.message)

        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # XMPP Ping

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        # import ssl
        self.ssl_version = ssl.PROTOCOL_SSLv3


    def session_start(self, event):
        try:
            logger.debug("Create session start")
            self.send_presence()
            roster =  self.get_roster()

            #创建聊天室
            nickname = "roomadmin"
            self.plugin['xep_0045'].joinMUC(self.roomname, nickname,
                    password = self.roompasswd, wait=True)
            logger.debug("Join MUC[roomname=%s][nickname=%s]" % (self.roomname, nickname))

            #修改聊天室设置
            config = self.plugin['xep_0045'].getRoomConfig(self.roomname)
            fields = config["fields"]
            #聊天室需要密码
            passwdroom_field = fields["muc#roomconfig_passwordprotectedroom"]
            passwdroom_field.set_true()
            #设置密码
            secret_field = fields["muc#roomconfig_roomsecret"]
            secret_field.set_value(self.roompasswd)
            self.plugin['xep_0045'].setRoomConfig(self.roomname, config)
            logger.debug("Set room config")

        except IqError as err:
            logger.debug(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logger.debug("Timeout")
            self.disconnect()
        finally:
            self.disconnect()
            logger.debug("Finish create room")



class ChatRoomDestroyer(ClientXMPP):
    """聊天室销毁者
    连接 XMPP 服务器（OpenFire server）
    销毁聊天室
    """

    def __init__(self, jid, password, roomname, roompasswd):
        logger.debug("Init ChatRoomDestroyer"
                "[jid=%s][passwd=%s][roomname=%s][roompasswd=%s]" %
                (jid, password, roomname, roompasswd))

        ClientXMPP.__init__(self, jid, password)

        self.roomname = roomname
        self.roompasswd = roompasswd

        self.add_event_handler("session_start", self.session_start)
        #self.add_event_handler("message", self.message)

        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # XMPP Ping

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        # import ssl
        self.ssl_version = ssl.PROTOCOL_SSLv3


    def session_start(self, event):
        try:
            logger.debug("Destroy session start")
            self.send_presence()
            roster =  self.get_roster()

            #加入聊天室
            nickname = "roomadmin"
            self.plugin['xep_0045'].joinMUC(self.roomname, nickname,
                    password = self.roompasswd, wait=True)
            logger.debug("Join MUC[roomname=%s][nickname=%s]" % (self.roomname, nickname))

            #销毁聊天室
            self.plugin['xep_0045'].destroy(self.roomname)
            logger.debug("Destroy room[roomname=%s]" % self.roomname)

        except IqError as err:
            logger.debug(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logger.debug("Timeout")
            self.disconnect()
        finally:
            self.disconnect()
            logger.debug("Finish destroy room")


class ChatRoomDecapitator(ClientXMPP):
    """聊天室踢人管理
    连接 XMPP 服务器（OpenFire server）
    从聊天室踢出指定人员
    """

    def __init__(self, jid, password, roomname, roompasswd, target_nickname):
        logger.debug("Init ChatRoomDecapitator"
                "[jid=%s][passwd=%s][roomname=%s][roompasswd=%s][target_nickname=%s]" %
                (jid, password, roomname, roompasswd, target_nickname))

        ClientXMPP.__init__(self, jid, password)

        self.roomname = roomname
        self.roompasswd = roompasswd
        self.target_nickname = target_nickname

        self.add_event_handler("session_start", self.session_start)
        #self.add_event_handler("message", self.message)

        # If you wanted more functionality, here's how to register plugins:
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # XMPP Ping

        # Here's how to access plugins once you've registered them:
        # self['xep_0030'].add_feature('echo_demo')

        # If you are working with an OpenFire server, you will
        # need to use a different SSL version:
        # import ssl
        self.ssl_version = ssl.PROTOCOL_SSLv3


    def session_start(self, event):
        try:
            self.send_presence()
            roster =  self.get_roster()

            #加入聊天室
            nickname = "roomadmin"
            self.plugin['xep_0045'].joinMUC(self.roomname, nickname,
                    password = self.roompasswd, wait=True)
            logger.debug("Join MUC[roomname=%s][nickname=%s]" % (self.roomname, nickname))

            #从聊天室中踢人
            self.plugin['xep_0045'].setRole(self.roomname, self.target_nickname, 'none')
            logger.debug("Kick %s from room[roomname=%s]" %
                    (self.target_nickname, self.roomname))

        except IqError as err:
            logger.debug(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            logger.debug("Timeout")
            self.disconnect()
        finally:
            self.disconnect()
            logger.debug("Finish kick member")



