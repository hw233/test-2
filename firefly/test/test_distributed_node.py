#coding:utf8
'''
Created on 2011-10-17

@author: lan (www.9miao.com)
'''
from firefly.utils import services
from firefly.distributed.node import RemoteObject
from twisted.internet import reactor
from twisted.python import util,log
import sys

log.startLogging(sys.stdout)

reactor = reactor

addr = ('localhost',10001)#目标主机的地址
remote = RemoteObject('test_node')#实例化远程调用对象

service = services.Service('reference',services.Service.SINGLE_STYLE)#实例化一条服务对象
remote.addServiceChannel(service)


def serviceHandle(target):
    '''服务处理
    @param target: func Object
    '''
    service.mapTarget(target)

@serviceHandle
def printOK(data):
    print data
    print "############################"
    return "call printOK_01"
    
def apptest(commandID,*args,**kw):
    print "apptest"
    d = remote.callRemote(commandID,*args,**kw)
    print "call remote"
    d.addCallback(lambda a:util.println(a))
    return d

def startClient():
    reactor.callLater(1,apptest,'printData1',"node测试1","node测试2")
    remote.connect(addr)#连接远程主机
    reactor.run()

if __name__=='__main__':
    startClient()

