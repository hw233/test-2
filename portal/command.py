#coding:utf8
"""
Created on 2015-01-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief :
"""

import types
import sys
from twisted.internet import defer
from firefly.server.globalobject import GlobalObject
from firefly.utils.services import CommandService
from firefly.utils.services import Service
from utils import logger
from portal.command_table import CommandTable


class NetCommandService(CommandService):
    """重载 Service 接口
    根据 command list 管理提供给客户端的接口
    """

    def __init__(self, name, runstyle = Service.SINGLE_STYLE):
        super(NetCommandService, self).__init__(name, runstyle)
        self._commands = CommandTable().commands


    def mapTarget(self, target):
        """add a method to the service
        @param target: method
        """
        self._lock.acquire()
        try:
            name = target.__name__
            id = self._commands[name]
            if id in self._targets:
                raise Exception("Method duplicate[method=%s][id=%d]" % (name, id))
            self._targets[id] = target

        except Exception, e:
            logger.warning("Add method failed[method=%s][exception=%s]" % (name, e))
            raise e

        finally:
            self._lock.release()


    def unmapTarget(self, target):
        """remote a method from the service
        @param target: method
        """
        self._lock.acquire()
        try:
            id = self._commands[target.__name]
            if id not in self._targets:
                raise Exception("Method not exist[method=%s]" % target.__name__)
            del self._targets[id]
        except Exception, e:
            logger.warning("Remove method failed[method=%s][exception=%s]" %
                    (target.__name__, e))
            raise e
        finally:
            self._lock.release()


    def callTargetSingle(self, command_id, *args, **kw):
        """call Target by Single
        @param command_id : command id
        """
        self._lock.acquire()
        try:
            target = self.getTarget(command_id)
            if not target:
                logger.fatal('Command not found in net service[command id=%d]' % command_id)
                return None
            if command_id not in self.unDisplay:
                logger.debug("Call method on net service[command id=%d][method=%s]" %
                        (command_id, target.__name__))

            defer_data = target(command_id, *args, **kw)
            if not defer_data:
                return None
            if isinstance(defer_data,defer.Deferred):
                return defer_data
            d = defer.Deferred()
            d.callback(defer_data)
        finally:
            self._lock.release()
        return d



_netservice = NetCommandService("portalService")
GlobalObject().netfactory.addServiceChannel(_netservice)


def netserviceHandle(target):
    """注册方法
    @param target: function
    """
    try:
        _netservice.mapTarget(target)
    except Exception as e:
        logger.fatal("Register method to net service failed[method=%s]" % target.__name__)
        sys.exit(-1)

    logger.trace("Register method to net service[method=%s]" % target.__name__);
    return target


