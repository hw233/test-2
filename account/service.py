#coding:utf8
"""
Created on 2015-05-04
@Author: taoshucai(taioshucai@ice-time.cn)
@Brief : account模块提供的服务
"""

from firefly.server.globalobject import GlobalObject
from firefly.server.globalobject import rootserviceHandle
from utils import logger


@rootserviceHandle
def regist(data):
    pass


@rootserviceHandle
def change_passwd(data):
    pass


@rootserviceHandle
def query_passwd(data):
    pass


@rootserviceHandle
def check_login(data):
    pass


@rootserviceHandle
def recharge(data):
    pass
