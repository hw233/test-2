#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 启动脚本
"""

import argparse
import subprocess
from version import VERSION


def main():
    parser = argparse.ArgumentParser(description = "start san server", prog='san-srv')
    parser.add_argument("-c", "--conf", help="config file", default="conf/config.json")
    parser.add_argument("-s", "--server", help="server name", default="")
    parser.add_argument("-t", "--test", action="count", help="test mode")
    parser.add_argument("-v", "--version", action="version", help="show version",
            version="%(prog)s {0}".format(VERSION))

    args = parser.parse_args()

    if args.test > 0:
        test_conf = "test_conf/config.json"
        command = "python src/start_master.py %s" % test_conf
    elif args.server == "":
        command = "python src/start_master.py %s" % args.conf
    else:
        command = "python src/start_master.py single %s %s" % (args.server, args.conf)

    cp = subprocess.Popen(command, shell = True)
    cp.wait()


if __name__=="__main__":
    main()


