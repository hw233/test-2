#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 启动 Firefly 的 master
"""
import os
import sys
from firefly.master.master import Master


if os.name!='nt' and os.name!='posix':
    from twisted.internet import epollreactor
    epollreactor.install()


def show_usage():
    """打印使用帮助信息"""
    print "usage[1] : python start_master.py conf_file"
    print "\t*start all server"
    print "usage[2] : python start_master.py single server_name conf_file"
    print "\t*start single server"


def start_master(config_path):
    """启动 master 模块
    @param  config_path : 配置文件路径
    """
    master = Master()
    master.config(config_path, 'src/start_server.py')
    master.start()


def main():
    """启动
    """
    args = sys.argv

    if len(args) == 2:
        conf_file = args[1]
        start_master(conf_file)
    elif len(args) == 4:
        server_name = args[2]
        conf_file = args[3]
        start_master(conf_file)
    else:
        show_usage()
        raise ValueError


if __name__=="__main__":
    main()


