#coding:utf8
'''
Created on 2013-8-14

@author: lan (www.9miao.com)
'''
from twisted.spread import pb
from twisted.internet import reactor
reactor = reactor
from reference import ProxyReference


def callRemote(obj,funcName,*args,**kw):
    '''远程调用
    @param funcName: str 远程方法
    '''
    return obj.callRemote(funcName, *args,**kw)


class RemoteManager(object):
    """远程调用对象 管理者
    """

    def __init__(self, localName):
        """
        """
        self._localName = localName
        self._remote = {} #remoteName - RemoteObjectSet


    def parseRemoteName(self, name):
        """解析远程对象的名称
        支持命名：
        name        ~ 一类远程对象，一个实例
        name:index  ~ 一类远程对象，多个实例
        Returns:
            (name, index)
        """
        sep = ':'
        index = 1
        if sep in name:
            fields = name.split(sep)
            name = fields[0]
            index = int(fields[1])
        return (name, index)


    def addRemote(self, remoteName):
        """添加远程对象
        """
        (rname, rindex) = self.parseRemoteName(remoteName)
        if rname not in self._remote:
            self._remote[rname] = RemoteObjectSet(self._localName)

        return self._remote[rname]


    def connectRemote(self, remoteName, addr):
        """连接远程对象
        """
        (rname, rindex) = self.parseRemoteName(remoteName)
        remote = self.addRemote(remoteName)
        remote.connect(addr, rindex)


    def __getitem__(self, remoteName):
        """访问
        """
        (rname, rindex) = self.parseRemoteName(remoteName)
        return self._remote[rname]


class RemoteObjectSet(object):
    """远程对象 可能包含多个实例
    """
    def __init__(self, name):
        self._name = name
        self._reference = ProxyReference()
        self._set = []
        self._count = 0


    def connect(self, addr, rindex):
        """初始化，连接远程调用对象
        """
        #避免重复 connect
        for o in self._set:
            if rindex == o.index:
                return

        r = RemoteObject(self._name, rindex, self._reference)
        r.connect(addr)
        self._set.append(r)
        self._set = sorted(self._set, key = lambda r : r.index)
        self._count += 1


    def callRemote(self, commandId, user_id, data):
        """远程调用
        按照规则选择一个远程对象实例
        """
        if self._count == 0:
            raise Exception("Server not ready")

        index = self._calcIndex(user_id)
        print "call remote[total=%r][id=%r][index=%r][command=%r]" % (
                self._count, user_id, index, commandId)
        return self._set[index].callRemote(commandId, user_id, data)


    def _calcIndex(self, user_id):
        """hash 规则
        """
        return user_id % self._count


class RemoteObject(object):
    '''远程调用对象 一个实例
    '''

    def __init__(self, name, index = 1, ref = None):
        '''初始化远程调用对象
        @param port: int 远程分布服的端口号
        @param rootaddr: 根节点服务器地址
        '''
        self.setName(name)
        self.index = index
        self._factory = pb.PBClientFactory()
        if ref is None:
            self._reference = ProxyReference()
        else:
            self._reference = ref
        self._addr = None


    def setName(self,name):
        '''设置节点的名称'''
        self._name = name


    def getName(self):
        '''获取节点的名称'''
        return self._name


    def connect(self,addr):
        '''初始化远程调用对象'''
        self._addr = addr
        reactor.connectTCP(addr[0], addr[1], self._factory)
        self.takeProxy()


    def reconnect(self):
        '''重新连接'''
        self.connect(self._addr)


    def addServiceChannel(self,service):
        '''设置引用对象'''
        self._reference.addService(service)


    def takeProxy(self):
        '''像远程服务端发送代理通道对象
        '''
        deferedRemote = self._factory.getRootObject()
        deferedRemote.addCallback(callRemote,'takeProxy',self._name,self._reference)


    def callRemote(self,commandId,*args,**kw):
        '''远程调用'''
        deferedRemote = self._factory.getRootObject()
        return deferedRemote.addCallback(callRemote,'callTarget',commandId,*args,**kw)


