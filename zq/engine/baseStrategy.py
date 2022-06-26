""" Base strategy for implementation """

import abc
from zq.common.tools import DictObj
from zq.engine.eventengine import EventManger
from zq.engine.barseries import BarSeries
from loguru import logger as log
import numpy as np
from zq.engine.timeseries import TimeSeries

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
        "period": 30
    }

    def __init__(self,engine, **kwargs):
        kwargs.update(self.params)
        self.p = DictObj(kwargs)
        self.status = 0     # 0 待启动  1 停止
        self.event=EventManger.get_instance()
        self._broker=engine.brokers
        self._datas=engine.datas

    def set_dataset(self,data):
        self._datas=data

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

    def buy(self, *args, **kwargs):
        self._broker.buy(args, kwargs)

    def sell(self, *args, **kwargs):
        self._broker.sell(args, kwargs)

    def close(self, *args, **kwargs):
        self._broker.close(args, kwargs)

    def cancel(self, *args, **kwargs):
        self._broker.canel(args, kwargs)

    def start(self):
        self.trading = True

    def get_positions(self, symbol=None):
        return self._broker.positions(symbol)

    def on_bar(self, event):
        self.to_timeseries()
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

    def on_stop(self):
        self.status=-1

    @property
    def data(self):
        return self._datas

    def to_timeseries(self):
        for i in dir(self):
            at=getattr(self,i)
            if isinstance(at,np.ndarray):
                setattr(self,i,TimeSeries(i))
