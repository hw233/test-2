#coding:utf8
"""
Created on 2015-01-16
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief :
"""

from firefly.utils.singleton import Singleton
from utils import logger


class CommandTable():
    __metaclass__ = Singleton


    def __init__(self):
        self.commands = {}


    def load(self, command_file):
        """read command list from file
        @format : id \t function_name
        """
        with open(command_file, 'r') as fp:
            for line in fp:
                line = line.strip(' \n\r\t')
                # logger.debug("Read line[line=%s]" % line)
                command = line.split(' ')
                if len(command) != 2:
                    continue

                id = int(command[0])
                if id in self.commands:
                    raise Exception("Duplicate command id[id=%d][line=%s]" % (id, line))
                method = command[1].strip(' \n\r\t')
                self.commands[method] = id
                # logger.debug("Load command list[id=%d][method=%s]" % (id, method))

            if len(self.commands) == 0:
                raise Exception("Empty file[file=%s]" % command_file)

            # for key in self.commands:
            #     logger.debug("Init command[%s=%d]" % (key, self.commands[key]))


def init_command(command_file):
    try:
        CommandTable().load(command_file)
    except Exception as e:
        logger.fatal("Init NetCommandService failed[file=%s][expection=%s]"
                % (command_file, e))
        sys.exit(-1)


