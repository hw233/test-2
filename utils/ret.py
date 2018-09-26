#coding:utf8

class Ret(object):
    
    def __init__(self, ret = None):
        self._ret = ret

    def setup(self, ret):
        self._ret = ret

    def get(self):
        return self._ret