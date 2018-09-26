#coding:utf8
"""
Created on 2017-05-06
@Author: huangluyu(huangluyu@ice-time.cn)
@Brief : 换位演武场匹配
"""

from twisted.internet.defer import Deferred
from datalib.data_proxy4redis import DataProxy
from common.data.transfer import TransferInfo
from common.business import transfer as transfer_business
from datalib.data_loader import data_loader
from utils import logger
import random


class TransferMatcher(object):
    
    MAX_RANK = 2000

    def get_top20(self, data):
        ranks = range(1, 21)

        transfers = self._get_by_ranks(data, ranks)
        return transfers[:20]

        
    def _get_by_ranks(self, data, ranks):
        transfers = []
        for rank in ranks:
            if rank < 1:
                continue

            transfer = None
            for t in data.transfer_list.get_all():
                if t.rank == rank:
                    transfer = t
                    break
                    
            if transfer == None:
                transfer = self._create_transfer(data, rank)
                if transfer == None:
                    raise Exception("No enough robot")
                data.transfer_list.add(transfer)
            
            transfers.append(transfer)
            
        return transfers


    def _create_transfer(self, data, rank):
        """在pve表中选择一个机器人阵容"""
        ids = data_loader.PVEEnemyBasicInfo_dict.keys()
        ids.sort()

        #在pve表中[0, max_index]中根据rank比值选取对手
        #在pve表中，战力是从小到大排列的，index越大战力越高
        max_index = int(float(data_loader.OtherBasicInfo_dict['transfer_arena_robot_max_index'].value))
        assert max_index <= len(ids) - 1
        
        index = max_index - int(max_index * (rank / float(self.MAX_RANK)))

        i = 0
        while transfer_business.get_transfer_by_user_id(data, ids[index], True) != None:
            logger.debug("robot conflict[rank=%d][id=%d]" % (rank, ids[index]))
            index = (index + 1) % len(ids)

            i += 1
            if i > len(ids):
                return None
        
        return TransferInfo.create(1, ids[index], rank, True)

    def match(self, data, transfer):
        ranks = []
        if transfer.rank == 1:
            return []
            
        if transfer.rank < 40:
            ranks.extend([transfer.rank - 1, transfer.rank - 2, transfer.rank - 3])
        elif transfer.rank < 56:
            ranks.append(random.randint(21, 27))
            ranks.append(random.randint(28, 34))
            ranks.append(random.randint(35, 39))
        elif transfer.rank < 66:
            ranks.append(random.randint(21, 35))
            ranks.append(random.randint(36, 45))
            ranks.append(random.randint(46, 56))
        else:
            ranks.extend([
                random.randint(int(transfer.rank * 0.3), int(transfer.rank * 0.45)),
                random.randint(int(transfer.rank * 0.5), int(transfer.rank * 0.9)),
                random.randint(int(transfer.rank * 0.95), int(transfer.rank * 0.99 - 1))
            ])
        
        transfers = self._get_by_ranks(data, ranks)
        return transfers[:3]


    def get_behind5(self, data, transfer):
        if transfer.rank >= self.MAX_RANK:
            return []

        ranks = range(transfer.rank + 1, min(transfer.rank + 1 + 5, self.MAX_RANK))

        transfers = self._get_by_ranks(data, ranks)
        return transfers[:5]

