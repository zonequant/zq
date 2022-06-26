# -*- coding:utf-8 -*-
"""
@Time : 2021/12/25 12:23
@Author : domionlu@zquant.io
@File : strategy
"""
import abc


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


