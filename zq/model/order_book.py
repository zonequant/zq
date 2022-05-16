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
    last_id:int=0
    symbol:str=""
    broker:str=""
    _asks:dict={}
    _bids:dict={}
    # 经过排序的列表
    asks:list=[]
    bids:list=[]
    update_time=None
    limit=20
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


