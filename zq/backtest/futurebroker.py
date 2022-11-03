#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/10/11 16:01
# @Author  : Dominolu
# @File    : futurebroker.py
# @Software: PyCharm
BUY="BUY"
SELL="SELL"
STATUS_FILLED="STATUS_FILLED"

class Futurebroker():
    """
    v1.0
    极简回测broker，只支持单币种
    """

    equity:float    # 资产余额
    returns:float   # 回报率
    commission:float    #手续费
    strategy:None   # 策略
    data:None
    def __init__(self, cash=100000, comm_rate=0.0002, out=False):
        """
        :param data:
        :param cash: 初始保证金
        :param commission: 手续费率
        :param lot:
        """
        super().__init__()
        self._cash = cash #初始现金
        self._comm_rate = comm_rate
        self._position = 0  # 持仓状态{symbol:qty}
        self._orders = list()  # 未成交订单列表[time,symbol,side,qty,price,status]
        self._retuns = 0.00
        self._fill_orders=list()
        self._fees = 0.00
        self._t = 0
        self.out = out

    def log(self, msg):
        if self.out:
            print(msg)

    @property
    def cash(self):
        """
        :return: 返回当前账户现金数量
        """
        return self._cash


    def check_order(self):
        """
        用当前账户剩余资金，按照市场价格全部买入
        当可用余额不足时，订单数量修改为最小单位，或最小单位无法满足时，订单将被撤销
        :param price:   float        订单价格，当没有传价格时为市价，取当前k线的close为订单价格，并在下根k线进行按限价单进行撮合
        :param qty:   float     订单数据，当没有订单数量为设置的最小单位_lot
        """
        orders=[]
        for o in self._orders:
            price = o.get("price", None)
            qty = o.get("qty", None)
            side=o.get("side", None)
            o,h,l,c,v=self.data[-1]
            if price is None:
                price = c  #
            if side==SELL:
                qty=-qty
            q=self._position+qty
            p=self._position
            if (p>0 and q>0) or (p<0 and q<0) or p==0: # 增加同方向仓位
                q=qty
            elif qty/p>2:   #反向持仓所需保证金超过平仓之后
                q=qty-p*2
            else:  #减仓未超
                q=0
            if self._cash>=abs(q)*price*(1+self._comm_rate):
                orders.append(o)
        return orders

    def match(self):
        """
        在进入策略事件之前计算，先完成上一根k线的订单撮合。
        市价单使用k线的收盘价，在下根k线时计算撮合情况。
        卖单价<high，or 买单价>low 即为撮合成功。
        撮合顺序 价格优先
        """
        orders = []  #未能撮合订单列表
        for i in self.check_order():
            p=self._position
            o, h, l, c, v = self.data[-1]
            side = i["side"]
            qty =i["qty"] if side== BUY else -i["qty"]
            price = i["price"]
            if (side == BUY and l <= price) or (side == SELL and h >= price):
                pos_pnl = self.equity - self._cash
                self.equity = self._cash + pos_pnl + (price - pos_pnl / abs(p)) * p
                self._position=p+qty
                fee=abs(qty) * price * self._comm_rate
                self._cash = self.equity - (abs(self._position) * price)-fee
                self.equity=self.equity-fee
                self._fees=self._fees+fee
                if self.equity<0:# 爆仓
                    self.equity=0
                    self._cash=0
                    self._position=0
                self._fill_orders.append(i)
            else:
                orders.append(i)
        self._orders = orders

    def close(self):
        """
        最后一根bar，平仓结算
        :return:
        """
        if self._position!=0:
            o, h, l, c, v = self.data[-1]
            pos_pnl = self.equity - self._cash
            self.equity = self._cash + pos_pnl + (c - pos_pnl / abs(self._position)) * self._position
            self._position=0
            fee = abs(self._position) * c * self._comm_rate
            self._fees=self._fees+fee
            self._cash = self.equity=self.equity-fee
            self._fill_orders.append({"side":BUY if self._position>0 else SELL,"qty":self._position,"price":c})

    def results(self):
        return self._retuns
