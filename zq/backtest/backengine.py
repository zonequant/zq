# -*- coding:utf-8 -*-
"""
@Time : 2021/12/25 12:19
@Author : domionlu@zquant.io
@File : backtest
"""
# -*- coding:utf-8 -*-
import numpy as np
import pandas as pd
from zq.backtest.strategy import Strategy
from loguru import logger as log
from zq.engine.timeseries import  Dataset
from zq.model import Position,Order
from zq.common.const import *
from zq.backtest.risk import  Risk
from zq.broker.brokerManger import BrokerManger
from zq.engine.baseBroke import BaseBroker

class BackBroker(BaseBroker):
    open: float
    high: float
    low: float
    close: float

    def __init__(self, cash=100000, commission=0.001, lot=1, out=False):
        """
        :param data:
        :param cash:
        :param commission:
        :param lot:
        """
        super().__init__()
        self._inital_cash = cash
        self._commission = commission
        self._position = {} #持仓状态{symbol:qty}
        self._lot = lot
        self._cash = cash
        self._orders = list()       #未成交订单列表[time,symbol,side,qty,price,status]
        self._retuns = list()
        self._fees=0.00
        self._t = 0
        self.out=out

    def log(self,msg):
        if self.out:
            print(msg)

    @property
    def cash(self):
        """
        :return: 返回当前账户现金数量
        """
        return self._cash

    def positions(self,symbol="DEFAULT"):
        """
        :return: 返回当前账户仓位
        """
        pos=self._position.get(symbol,None)
        if pos==None:
            pos=Position()
            pos.symbol=symbol
            self._position[symbol]=pos
        return pos

    @property
    def initial_cash(self):
        """
        :return: 返回初始现金数量
        """
        return self._inital_cash

    def set_dataset(self,dataset):
        self._datas=dataset
        self.symbol=dataset.symbols[0]


    def get_value(self,price,openprice,qty):
        cash=abs(openprice+qty)
        cash=cash+(price-openprice)*qty
        return cash

    def buy(self, *args,**kwargs):
        """
        用当前账户剩余资金，按照市场价格全部买入
        当可用余额不足时，订单数量修改为最小单位，或最小单位无法满足时，订单将被撤销
        :param price:   float        订单价格，当没有传价格时为市价，取当前k线的close为订单价格，并在下根k线进行按限价单进行撮合
        :param qty:   float     订单数据，当没有订单数量为设置的最小单位_lot
        """
        price = kwargs.get("price", None)
        symbol=kwargs.get("symbol",self.symbol)
        close=self._datas[symbol].close[-1]
        position=self.positions(symbol)
        if price is None:
            price = close#
        qty = kwargs.get("qty", None)
        if qty is None:
            qty = self._lot
        o = Order()
        o.time =self._time
        o.symbol = symbol
        o.price = price
        o.qty = qty
        o.side = BUY
        if position.qty<0:                                                     #如果原持仓为负，则订单为减仓，数量超过持仓部分，则为反向单，只能进行减仓 reduce only,但没有处理撮合成交时原持仓已经平仓的情况
            if qty>abs(position.qty):
                q1=qty+position.qty
                if self._cash>=q1*price*(1 + self._commission):              #检测反向单订单资金余额
                    self._cash = self._cash - q1 * price * (1 + self._commission)
                    self._orders.append(o)
            else:
                self._orders.append(o)
            self.log(f"{self._time}-close sell:{o.qty}@{o.price}")

        else :
            if self._cash>qty * price * (1 + self._commission) :
                self._cash = self._cash - qty * price * (1 + self._commission)  # 22.01.08 增加手续费计算
                self._orders.append(o)
                self.log(f"{self._time}-open buy:{o.qty}@{o.price}")
            else:
                self.log(f"{self._time}-open buy:余额不足 call:{self._cash},qty:{qty},price:{price}")

    def sell(self, *args, **kwargs):
        """
        卖出当前账户剩余持仓
        """
        price = kwargs.get("price", None)
        symbol = kwargs.get("symbol", self.symbol)
        close = self._datas[symbol].close[-1]
        position = self.positions(symbol)
        if price is None:
            price = close
        qty = kwargs.get("qty", None)

        if qty is None:
            qty = self._lot
        o = Order()
        o.time = self._time
        o.symbol = symbol
        o.price = price
        o.qty = qty
        o.side = SELL
        if position.qty > 0:
            if qty > (position.qty) :
                q1=qty -position.qty
                if self._cash>=q1*price*(1 + self._commission):              #检测反向单订单资金余额
                    self._cash = self._cash - q1 * price * (1 + self._commission)
                    self._orders.append(o)
            else:
                self._orders.append(o)
            self.log(f"{self._time}-close buy:{o.qty}@{o.price}")
        else:
            if self._cash >= qty * price * (1 + self._commission):
                self._cash = self._cash - qty * price * (1 + self._commission)  # 22.01.08 增加手续费计算
                self._orders.append(o)
                self.log(f"{self._time}-open sell:{o.qty}@{o.price}")
            else:
                self.log(f"{self._time}-open sell:余额不足 call:{self._cash},qty:{qty},price:{price}")

    def next(self):
        self._datas.next()
        self._time=self._datas.datetime[-1]
        self.match()
        self._retuns.append(self.market_value())

    def match(self):
        """
        在进入策略事件之前计算，先完成上一根k线的订单撮合。
        市价单使用k线的收盘价，在下根k线时计算撮合情况。
        卖单价<high，or 买单价>low 即为撮合成功。
        撮合顺序 价格优先
        """
        orders = []
        for i in self._orders:
            symbol=i.symbol
            position = self.positions(symbol)
            low=self._datas[symbol].low[-1]
            high = self._datas[symbol].high[-1]
            side = i.side
            qty=i.qty
            price=i.price
            if side == BUY and low <= price:
                """
                买单撮合成功
                减仓，增加cash，开仓价不变
                增仓，开仓价，加权平均
                """
                i.status=STATUS_FILLED
                # position.qty=position.qty+qty
                if position.qty<=0:
                    if qty<=abs(position.qty):
                        self._cash = self._cash + qty * price * (1 - self._commission)
                        self._fees=self._fees+qty * price *  self._commission
                    else:
                        self._cash=self._cash + abs(position.qty) * price * (1 - self._commission)
                        self._fees = self._fees + abs(position.qty) * price * self._commission
                else:
                    position.side=LONG
                position.price=price
                position.qty = position.qty + qty
                self._position[symbol] = position
                self.log(f"{self._time}-Buy订单 price:{price} 撮合成功,pos:{position.qty},Cash :{self._cash}")
            elif side == SELL and high >= price:
                i.side=STATUS_FILLED
                if position.qty>=0:
                    if qty <= abs(position.qty):
                        self._cash = self._cash + qty * price * (1 - self._commission)
                        self._fees = self._fees + qty * price * self._commission
                    else:
                        self._cash = self._cash + abs(position.qty) * price * (1 - self._commission)
                        self._fees = self._fees + abs(position.qty) * price * self._commission
                else:
                    position.side=SHORT

                position.qty = position.qty - qty
                position.price = price
                self._position[symbol] = position
                self.log(f"{self._time}-Sell 订单 price:{price} 撮合成功,pos:{position.qty},Cash :{self._cash}")
            else:
                orders.append(i)
        self._orders = orders

    def order_value(self):
        """
        计算当前挂单占用的资金
        :return:
        """

        value = 0
        for order in self._orders:
            value=value+order.price*order.qty
        return value

    def position_pnl(self):
        """
        计算当前持仓的pnl
        :return:
        """
        pnl=0
        for symbol,posistion in self._position.items():
            price=self._datas[posistion.symbol].close[-1]
            pnl=pnl+(price-posistion.price)*posistion.qty+posistion.price*abs(posistion.qty)
        return pnl

    def market_value(self):
        """
        计算当前持仓pnl+挂单占用资金+cash
        :return: [t,返回当前市值]
        """
        value=self._cash+self.position_pnl()+self.order_value()
        fees=self._fees
        self._fees=0
        return [self._time,value,fees]

    def results(self):
        return self._retuns

class BackEngine:
    """
    BackEngine回测类，用于读取历史行情数据、执行策略、模拟交易并估计收益。
    初始化的时候调用BackEngine.train来时回测
    """

    def __init__(self,
                 data: pd.DataFrame,
                 strategy: type(Strategy),
                 broker: type(BackBroker),
                 cash: float = 10000,
                 lot=1,
                 commission: float = .0,
                 out=False):
        """
        构造回测对象。需要的参数包括：历史数据，策略对象，初始资金数量，手续费率等。
        初始化过程包括检测输入类型，填充数据空值等。
        参数：
        :param data:            pd.DataFrame        pandas Dataframe格式的历史OHLCV数据
        :param broker_type:     type(ExchangeAPI)   交易所API类型，负责执行买卖操作以及账户状态的维护
        :param strategy_type:   type(Strategy)      策略类型
        :param cash:            float               初始资金数量
        :param commission:       float               每次交易手续费率。如2%的手续费此处为0.02
        """

        data = data.copy(False)
        # 利用数据，初始化交易所对象和策略对象。
        self._datas = self._check_data(data)
        self._broker =broker(cash=cash, commission=commission,lot=lot,out=out)
        self._broker.set_dataset(self._datas)
        self._strategy_cls = strategy
        self._results = None
        self._strategy = None

    def _check_data(self, data):
        dt=Dataset()
        dt.add(data,"test")
        return dt


    def run(self, **kwargs):
        """
        运行回测，迭代历史数据，执行模拟交易并返回回测结果。
        """
        broker = self._broker
        log.info(f"初始化策略{self._strategy_cls.__name__}")
        strategy = self._strategy_cls(self,**kwargs)

        # 提前计算策略中的指标
        strategy.init()
        strategy.to_timeseries()
        start = 30
        total_size = self._datas.size()
        log.info(f"回测数据量 {total_size+1}")
        for i in range(1, total_size):
            broker.next()
            if i >= start:
                strategy.next()
            broker.match()
            # progress_bar(i/total_size)
        log.info(f"完成回测")
        self._results=broker.results()
        return self._results

    def result(self):
        """
        根据资产余额转换为日收益率
        :return:
        """
        dt = pd.DataFrame(self._results, columns=["date", "values", "commission"])
        dt["date"] = pd.to_datetime(dt["date"])
        dt = dt.set_index("date")
        dt=dt["values"].resample("D",label='left', closed='right').last()
        dt=dt.to_frame("values")
        dt["return"] = dt["values"].pct_change()
        dt["return"].fillna(0, inplace=True)
        dt["pnl"] = dt["values"] * dt["return"]
        return dt

    def analyzers(self,out=False):
        """
        分种数据转换成days result
        根据日收益计算日收益率
        :param
        :return: 分析结果
        """
        dt=self.result()
        r=Risk(dt)
        result=r.calculate_statistics()
        if out:
            print("开始时间:"+str(result["start_date"]))
            print("结束时间:" +str( result["end_date"]))
            print("初始资金:" + str(round(result["capital"],4)))
            print("结束资金:" + str(round(result["end_balance"],4)))
            print("总收益:" + str(round(result["total_net_pnl"], 4)))
            print("总收益率:" + str(round(result["return"]*100,4))+ "%")
            print("夏普:" +str(round(result["sharpe"],2)))
            print("年化收益率:" + str(round(result["annual_return"]*100,4))+ "%")
            print("最大回撤:" +str(round(result["max_drawdown"]*100,4))+ "%")
            print("总手续费:" +str(round(result["total_commission"],4)))
            print("盈利天数:" + str(round( result["profit_return"],0)))
            print("亏损天数:" + str(round(result["loss_return"],0)))
            print("胜率:" + str(round( result["win_rate"]*100,2))+ "%")
            print("盈利金额:" + str(round(result["avg_profit"],4)))
            print("亏损金额:" + str(round(result["avg_loss"],4)))
            print("盈亏比:" + str(round(result["pl_radio"],2)))

        return result

    @property
    def datas(self):
        return self._datas

    @property
    def brokers(self):
        return self._broker

