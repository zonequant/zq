# -*- coding:utf-8 -*-
"""
@Time : 2021/4/19 19:57
@Author : domionlu@zquant.io
@File : orderManagerServer
"""
# -*- coding:utf-8 -*-
from zq.model import Order,Position
from zq.common.const import *
import traceback

class OrderManagerServer(object):
    _orders=list()
    _balance=list()
    _position=dict()

    def __init__(self,bot):
        self._brokers=None
        self._datas=None
        self._symbols=dict()  #{"btcust":Huobi()}
        self.bot=bot

    def next(self):
        for i in range(len(self._orders),-1, -1):
            broker,order=self._orders[i]
            order=broker.update_order(order)
            if order.status in(STATUS_FILLED,STATUS_CANCELED,STATUS_REJECTED):
                self.bot.put("E_ORDER",order)
                self._orders.pop(i)
                symbol=broker.name+":"+order.symbol
                self.upate(symbol)

    def upate(self,symbol):
        try:
            if symbol is None:
                symbol=self._datas[0]
            if symbol:
                broker,s=self._symbols[symbol]
                self._balance[symbol]=broker.get_balance(s)
                self._position[symbol] = broker.get_position(s)
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    def get_symbols(self):
        return self._symbols.keys()

    def set_brokers(self,brokers):
        for i in brokers:
            symbol=i.symbol+"."+i.name
            self._brokers[symbol]=i





    def buy(self,symbol=None,qty=0.0,price=None,order_type="limit"):
        if symbol is None:
            symbol=self._datas[0].symbol
        else:
            symbol=self._symbols.get(symbol,None)
        if symbol:
            broker= self._symbols[symbol]
            order=broker.buy(symbol, qty, price, order_type)
            self._orders.append([broker,order])
            return order
        else:
            return None

    def sell(self,symbol=None,qty=0.0,price=None,order_type="limit"):
        if symbol is None:
            symbol=self._datas[0].symbol
        else:
            symbol=self._symbols.get(symbol,None)
        if symbol:
            broker = self._symbols[symbol]
            order=broker.sell(symbol, qty, price, order_type)
            self._orders.append([broker,order])
            return order
        else:
            return None

    # def close(self,order:Order):
    #     if order.side==LONG:
    #         self.sell(order.symbol,order.qty)
    #     else:
    #         self.buy(order.symbol, order.qty)


    def balance(self,symbol=None):
        if symbol is None:
            symbol=self._datas[0]
        if symbol:
            broker,s=self._symbols[symbol]
            self._balance[symbol]=broker.get_balance(s)
            return self._balance[symbol]
        else:
            return False

    def position(self,symbol=None):
        if symbol is None:
            data=self._datas[0]
            symbol=data.name
        if symbol:
            broker,s=self._symbols[symbol]
            self._position[symbol]=broker.get_position(s)
            return self._position[symbol]
        else:
            return False

    def __getattr__(self, attr):
        def wrapper(*args, **kw):
            symbol=kw.get("symbol")
            if symbol is None:
                data = self._datas[0]
                symbol = data.name
            if symbol:
                broker= self._symbols[symbol]
                if hasattr(broker, attr):
                    return getattr(broker, attr)(*args, **kw)
                return False
            else:
                return False
        return wrapper



