# -*- coding:utf-8 -*-
"""
@Time : 2022/5/18 20:44
@Author : Domionlu@gmail.com
@File : brokerManger
"""
# -*- coding:utf-8 -*-

class BrokerManger():
    _brokers={}

    def __init__(self,data):
        self._datas=data

    def __len__(self):
        return len(self._brokers)

    def add_broker(self,broker):
        broker.set_dataset(self._datas)
        self._brokers[broker.name]=broker

    def __getattr__(self, item):
        try:
            getattr(self._brokers[self._brokers.keys()[0]],item)
        except:
            raise AttributeError(f"Not found attribute'{item}'")

    def buy(self,**kwargs):
        return

    def sell(self,**kwargs):
        return

    def close(self,**kwargs):
        return

    def position(self,**kwargs):
        return

    def order(self,**kwargs):
        return

