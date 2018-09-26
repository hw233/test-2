#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 启动各个 server
"""

import os
import json
import sys
from twisted.python import log
from firefly.server.server import FFServer
from utils import logger


if os.name!='nt' and os.name!='posix':
    from twisted.internet import epollreactor
    epollreactor.install()


def show_usage():
    """打印使用帮助信息"""
    print "usage : python start_server.py server_name conf_file"
    print "\t*start server, include: portal, app"


def start_module(module_name, config_path):
    """单独启动一个模块
    @param  module_name : 模块名
    @param  config_path : 配置文件路径
    """
    config = json.load(open(config_path, 'r'))
    server_id = config.get('id')
    version = config.get('version')
    master_conf = config.get('master', {})
    servers_conf = config.get('servers', {})
    db_conf = config.get('db')
    cache_conf = config.get('cache')

    module_conf = servers_conf.get(module_name)
    _start_logging(module_name, module_conf)

    ser = FFServer()
    ser.config(
            server_id,
            version,
            module_conf,
            dbconfig = db_conf,
            cacheconfig = cache_conf,
            masterconf = master_conf)
    ser.start()


def _start_logging(module_name, module_config):
    """开始记录日志
    @param  module_name : 模块名
    @param  config_path : 配置文件路径
    """
    log_conf_path = module_config.get('logconf')
    log.addObserver(logger.Logger(module_name, log_conf_path))


def main():
    """启动模块
    """
    args = sys.argv

    if len(args) == 3:
        server_name = args[1]
        config_path = args[2]
        start_module(server_name, config_path)
    else:
        show_usage()
        raise ValueError


if __name__=="__main__":
    main()


