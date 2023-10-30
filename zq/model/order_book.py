# -*- coding:utf-8 -*-
"""
@Time : 2021/5/31 14:21
@Author : domionlu@zquant.io
@File : order_book
"""
# -*- coding:utf-8 -*-
from zq.model.base_model import Model
from zq.common.tools import *
class Order_book(Model):

    def __init__(self):
        self.last_id = 0
        self.symbol = ""
        self.broker = ""
        self._asks = {}
        self._bids = {}
        self.asks = []
        self.bids = []
        self.queue = []
        self.update_time = None
        self.limit = 20
        self.synced=0  # 0 未同步 1 正同步 2 已同步未合并，3已合并


    def update(self,bids,asks):
        for ask in asks:
            price = str(ask[0])
            qty = float(ask[1])
            if qty ==0:
                if price in self._asks:
                    del self._asks[price]
            else:
                self._asks[price] = qty
        for bid in bids:
            price = str(bid[0])
            qty = float(bid[1])
            if qty ==0 :
                if  price in self._bids:
                    del self._bids[price]
            else:
                self._bids[price] = qty
        self.asks = sorted([[float(k), v] for k, v in self._asks.items()])
        self.bids = sorted([[float(k), v] for k, v in self._bids.items()], reverse=True)
        self.bids = self.bids[:self.limit]
        self.asks = self.asks[:self.limit]
        self.update_time=get_cur_timestamp_ms()

    def copy(self,data):
        self._asks = data._asks
        self._bids = data._bids
        self.asks = data.asks
        self.bids = data.bids
        self.last_id = data.last_id


    def __str__(self):
        if len(self.bids)>0 and len(self.asks)>0:
            return f"broker:{self.broker},symbol:{self.symbol},best_bid:{self.bids[0]},best_ask:{self.asks[0]},update_time:{self.update_time}"
        else:
            return f"broker:{self.broker},symbol:{self.symbol} is empty"