#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/10/11 16:01
# @Author  : Dominolu
# @File    : futurebroker.py
# @Software: PyCharm
from numba.experimental import jitclass
import numba as nb
import numpy as np
from numba.typed import List

BUY="BUY"
SELL="SELL"
STATUS_FILLED="STATUS_FILLED"



class Futurebroker():
    """
    v1.0
    极简回测broker，支持多币种
    """
    _position=None # 持仓结构：[交易对][持仓数量,开仓价格,当前价格，持仓价值]
    _orders=None  # "订单结构：[订单时间，交易对，订单数量，订单价格，手续费]"
    _retuns = None #收益率：[收益率]
    _fees = None  #手续费: [手续费]
    _equity=None  #资产余额：[资产余额] 现金+持仓
    _index=0 #当前指针
    def __init__(self, cash=100000, comm_rate=0.0002, out=False):
        """
        :param data:
        :param cash: 初始保证金
        :param commission: 手续费率
        :param lot:
        """
        self._cash = cash #初始现金
        self._comm_rate = comm_rate
        self.out = out

    def create(self,data):
        """
        :return:
        """
        shape=data.shape
        self._data=data
        self._cash=np.full(shape[0],self._cash)
        self._equity=np.zeros(shape[0],dtype=np.float64)
        self._fees=np.zeros(shape[0],dtype=np.float64)
        self._retuns=np.zeros(shape[0],dtype=np.float64)
        self._position=np.zeros([shape[0],5],dtype=np.float64)
        self._orders=None
        self._index=0

    def log(self, msg):
        if self.out:
            print(f"{self.time}:{msg}")

    @property
    def time(self):
        return self._data[0][0][self._index]

    @property
    def equitys(self):
        """
        :return: 返回当前账户资产价值
        """
        return self._equity

    @property
    def equity(self):
        """
        :return: 返回当前账户资产价值
        """
        return self._equity[self._index]

    @equity.setter
    def equity(self, value):
        self._equity[self._index:]=value

    @property
    def cash(self):
        """
        :return: 返回当前账户现金可用余额
        """
        return self._cash[self._index]

    @cash.setter
    def cash(self,value):
        self._cash[self._index:]=value

    @property
    def fee(self):
        return self._fees[self._index]

    @fee.setter
    def fee(self,value):
        self._fees[self._index]=value

    def results(self):
        return self._retuns

    @property
    def result(self):
        return self._retuns[self._index]

    @result.setter
    def result(self,value):
        self._retuns[self._index:]=value

    @property
    def orders(self):
        if self._orders:
            return self._orders
        else:
            return []

    def add_order(self,**kwargs):
        if self._orders:
            self._orders=np.append(self._orders,[kwargs],axis = 0)
        else:
            self._orders=np.array([kwargs])

    def del_order(self,index):
        self._orders=np.delete(self._orders,index,axis=0)

    def reset(self):
        self.create(self._data)

    def get_data(self,symbol:None):
        if symbol:
            return self._data[symbol, self._index, :]
        else:
            return self._data[:, self._index, :]

    def get_posistion_value(self,pos):
        """
        获取当前所有的持仓价值
        （现价-开仓价）*持仓数量
        [交易对,持仓数量,开仓价格,当前价格，持仓价值]
        持仓价值=持仓数量*(当前价格-开仓价格)+abs(数量)*开仓价格
        """
        bar=self.get_data()
        pos[3]=bar[pos[0],1]
        pos[4]=pos[1]*(pos[3]-pos[2])+abs(pos[1])*pos[2]
        return pos[4].sum()

    def get_result(self):
        e=self._equity[self._index]
        p=self._equity[self._index-1]
        return  (e-p)/p

    def match(self,index):
        """
        在进入策略事件之前计算，先完成上一根k线的订单撮合。
        市价单使用k线的收盘价，在下根k线时计算撮合情况。
        卖单价<high，or 买单价>low 即为撮合成功。
        撮合顺序 价格优先
        [订单时间，交易对，订单数量，订单价格，手续费]
        """
        self._index=index
        pos = self._position
        pos_value=self.get_posistion_value(pos)
        self.equity=pos_value+self._cash[self._index-1]
        if self.equity<=0:
            "持仓亏损大于现金，说明已经爆仓"
            # todo 后续订单清单清零0，资产清0
            self._position=self._position*0
            self._orders=None
            self.equity=0
            self.cash=0
        else:
            orders=list()
            fee=0
            for i in self.orders:
                t,s,v,p,f=i[1]
                bar=self.get_data(s)
                t, o, h, l, c, v=bar
                if p>0 and p<h:
                    pos[s,2]=(pos[s,1]*pos[s,2]+p*v)/(pos[s,1]+v)
                    pos[s,1] = pos[s,1] + v
                    fee=fee+abs(p*v)*self._comm_rate
                else:
                    orders.append(i)
            pos_value = self.get_posistion_value(pos)
            if self.equity-pos_value-fee<=self.cash:
                self._position=pos
                self._orders=np.array(orders)
                self.cash=self.equity-pos_value
                self.fee=fee
            else:
                self._orders=None
                self.log("余额不足，订单取消")

        if self._index>0:
            self.result=self.get_result()
        else:
            self.result=0.0



    def order(self,**kwargs):
        self.add_order([])

    def buy(self,**kwargs):
        pass

    def sell(self,**kwargs):
        pass
