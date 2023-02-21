""" Base strategy for implementation """

import abc
from zq.common.tools import DictObj
from zq.engine.eventengine import EventManger
from zq.common.const import *
from loguru import logger as log


class BaseStrategy(metaclass=abc.ABCMeta):
    """
    抽象策略类，用于定义交易策略。
    如果要定义自己的策略类，需要继承这个基类，并实现两个抽象方法：
    Strategy.init
    Strategy.next
    """
    parameters = []
    variables = []
    strategy_name = ""
    trading = False

    params = {

    }

    def __init__(self,engine, **kwargs):
        self.params=kwargs
        self.p = DictObj(kwargs)
        self.status = 0     # 0 待启动  1 停止
        self.event=EventManger.get_instance()
        self._broker=engine.broker
        self._datas=engine.datas
        self.reg()

    def reg(self):
        self.event.register(BAR,self.on_bar)
        self.event.register(TICKER,self.on_tick)
        self.event.register(ORDER,self.on_order)
        self.event.register(POSITION,self.on_position)
        self.event.register(ACCOUNT,self.on_account)


    def init(self):
        """
       初始化策略。在策略回测/执行过程中调用一次，用于初始化策略内部状态。
       这里也可以预计算策略的辅助参数。比如根据历史行情数据：
       计算买卖的指标向量；
       训练模型/初始化模型参数
        """
        log.info("策略已完成初始化.")

    @abc.abstractmethod
    def next(self):
        """
        步进函数，执行第tick步的策略。tick代表当前的"时间"。比如data[tick]用于访问当前的市场价格。
        """
        pass

    def buy(self, *args,**kwargs):
        return self._broker.buy(*args,**kwargs)

    def sell(self, *args,**kwargs):
        return self._broker.sell(*args,**kwargs)

    def close(self, *args,**kwargs):
        return self._broker.close(*args,**kwargs)

    def cancel(self, *args, **kwargs):
        return self._broker.canel(*args, **kwargs)

    def start(self):
        self.trading = True

    def get_positions(self, symbol=None):
        return self._broker.get_position(symbol)

    def get_balance(self,symbol=None):
        return  self._broker.get_balance(symbol)

    def get_ticker(self,symbol):
        return  self._broker.get_ticker(symbol)

    def on_bar(self, event):
        self.next()

    def on_tick(self, event):
        pass

    def on_order(self, event):
        pass

    def on_trade(self, event):
        pass

    def on_alert(self,event):
        pass

    def on_position(self, event):
        pass

    def on_account(self,event):
        print(event)

    def on_stop(self):
        self.status=-1

    @property
    def data(self):
        return self._datas


