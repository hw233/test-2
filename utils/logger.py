#coding:utf8
'''
Created on 2015-01-15
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 日志类，定义日志等级和格式
'''

import json
import sys
import time
import traceback
import logging
import logging.handlers
from twisted.python import log
from zope.interface import implements


#日志等级
_LOG_LEVELS = {
        'FATAL' : logging.ERROR,
        'WARNING' : logging.WARNING,
        'NOTICE' : logging.INFO,
        'TRACE' : logging.INFO,
        'DEBUG' : logging.DEBUG,
        'FRAME' : logging.NOTSET # 框架中打印的日志
}


class Logger:
    """打印日志
    根据不同的等级打印到不同的文件中

    日志格式：[LEVEL] time | timestamp * module_name trace : message
    """
    implements(log.ILogObserver)

    def __init__(self, module_name, conf_path):
        config = json.load(open(conf_path, 'r'))
        log_conf = config.get(module_name)

        #日志等级
        level = log_conf.get('level')
        if level not in _LOG_LEVELS:
            raise ValueError
        Logger.level = _LOG_LEVELS[level]

        self._module_name = module_name

        debug_path = log_conf.get('debug_path')
        notice_path = log_conf.get('notice_path')
        warning_path = log_conf.get('warning_path')

        self._log = logging.getLogger(self._module_name)
        self._log.setLevel(self.level)

        formatter = logging.Formatter(
                '[%(levelname)s] %(asctime)s | %(created)d * %(name)s %(message)s',
                "%Y-%m-%d %H:%M:%S")

        if Logger.level <= _LOG_LEVELS["DEBUG"]:
            debug_handler = logging.handlers.TimedRotatingFileHandler(
                    debug_path, "H", 1, 30)
            debug_handler.suffix = "%Y%m%d.%H"  # 设置后缀
            debug_handler.setFormatter(formatter)
            debug_handler.setLevel(logging.DEBUG)
            self._log.addHandler(debug_handler)

        if Logger.level <= _LOG_LEVELS["NOTICE"]:
            notice_handler = logging.handlers.TimedRotatingFileHandler(
                    notice_path, "H", 1, 30)
            notice_handler.suffix = "%Y%m%d.%H"
            notice_handler.setFormatter(formatter)
            notice_handler.setLevel(logging.INFO)
            self._log.addHandler(notice_handler)

        if Logger.level <= _LOG_LEVELS["WARNING"]:
            warning_handler = logging.handlers.TimedRotatingFileHandler(
                    warning_path, "H", 1, 30)
            warning_handler.suffix = "%Y%m%d.%H"
            warning_handler.setFormatter(formatter)
            warning_handler.setLevel(logging.WARNING)
            self._log.addHandler(warning_handler)


    def __call__(self, eventDict):
        """被 twisted.python.log 模块调用
        """
        if 'LEVEL' in eventDict:
            level = eventDict['LEVEL']
        elif eventDict['isError']:
            level = logging.ERROR
        else:
            level = logging.NOTSET

        if level < Logger.level:
            return

        text = log.textFromEventDict(eventDict)
        if text is None:
            return

        text = text.replace('\n', ' ')
        trace = ""
        if 'TRACE' in eventDict:
            trace = eventDict['TRACE']
        #trace = traceback.extract_stack()
        message = "%s : %s" % (trace, text)

        self._log_to_file(level, message)


    def _log_to_file(self, level, message):
        self._log.log(level, message)



def fatal(message):
    """打印致命错误"""
    level = logging.ERROR
    if level >= Logger.level:
        trace = traceback.extract_stack(limit = 2)[0][:3]
        log.msg(message, LEVEL = level, TRACE = trace)


def warning(message):
    """打印警告信息"""
    level = logging.WARNING
    if level >= Logger.level:
        trace = traceback.extract_stack(limit = 2)[0][:3]
        log.msg(message, LEVEL = level, TRACE = trace)


def notice(message):
    """打印业务信息"""
    level = logging.INFO
    if level >= Logger.level:
        trace = traceback.extract_stack(limit = 2)[0][:3]
        log.msg(message, LEVEL = level, TRACE = trace)


def trace(message):
    """打印程序运行必要的跟踪信息"""
    level = logging.INFO
    if level >= Logger.level:
        trace = traceback.extract_stack(limit = 2)[0][:3]
        log.msg(message, LEVEL = level, TRACE = trace)


def debug(message):
    """打印调试信息，线上运行模块一般不开启"""
    level = logging.DEBUG
    if level >= Logger.level:
        trace = traceback.extract_stack(limit = 2)[0][:3]
        log.msg(message, LEVEL = level, TRACE = trace)


