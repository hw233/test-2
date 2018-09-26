#coding:utf8
"""
Created on 2015-01-12
@Author: jiangtaoran(jiangtaoran@ice-time.cn)
@Brief : 排序相关功能
"""


class SortCache(object):

    def __init__(self):
        self._dict = {}
        self._rank = []
        pass


    def add(self, user_id, value):
        assert user_id not in self._dict

        self._dict[user_id] = value
        self._rank.append((value, user_id))
        self._rank.sort(reverse = True)


    def update(self, user_id, value):
        if user_id in self._dict:
            index = self.find(user_id)
            self._dict[user_id] = value
            self._rank[index] = (value, user_id)
            self._rank.sort(reverse = True)
        else:
            add(user_id, value)


    def rank(self, user_id):
        if user_id not in self._dict:
            return None

        value = self._dict[user_id]
        index = self._rank.index((value, user_id))
        while index > 0 and self._rank[index-1][0] == value:
            index = index - 1
        return index


    def find(self, user_id):
        if user_id not in self._dict:
            return None

        value = self._dict[user_id]
        return self._rank.index((value, user_id))


    def show(self):
        for info in self._rank:
            print info



