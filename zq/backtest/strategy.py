# -*- coding:utf-8 -*-
"""
@Time : 2021/12/25 12:23
@Author : domionlu@zquant.io
@File : strategy
"""
# -*- coding:utf-8 -*-
import abc
import numpy as np
from typing import Callable


class Strategy(metaclass=abc.ABCMeta):
    """
    抽象策略类，用于定义交易策略。
    如果要定义自己的策略类，需要继承这个基类，并实现两个抽象方法：
    Strategy.init
    Strategy.next
    """
    def __init__(self, broker, data):
        """
        构造策略对象。
        @params broker:  ExchangeAPI    交易API接口，用于模拟交易
        @params data:    list           行情数据数据
        """
        self._indicators = []
        self._broker = broker
        self._data = data
        self._tick = 0

    def prep(self):
        pass

    def I(self, func: Callable, *args) -> np.ndarray:
        """
        计算买卖指标向量。买卖指标向量是一个数组，长度和历史数据对应；
        用于判定这个时间点上需要进行"买"还是"卖"。
        例如计算滑动平均：
        def init():
            self.sma = self.I(utils.SMA, self.data.Close, N)
        """
        value = func(*args)
        value = np.asarray(value)

        self._indicators.append(value)
        return value

    @property
    def tick(self):
        return self._tick

    def init(self):
        """
        初始化策略。在策略回测/执行过程中调用一次，用于初始化策略内部状态。
        这里也可以预计算策略的辅助参数。比如根据历史行情数据：
        计算买卖的指标向量；
        训练模型/初始化模型参数
        """
        pass

    @abc.abstractmethod
    def next(self,t):
        """
        步进函数，执行第tick步的策略。tick代表当前的"时间"。比如data[tick]用于访问当前的市场价格。
        """
        pass

    def buy(self,**kwargs):
        self._broker.buy(**kwargs)

    def sell(self,**kwargs):
        self._broker.sell(**kwargs)

    @property
    def data(self):
        return self._data


