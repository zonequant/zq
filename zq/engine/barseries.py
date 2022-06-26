# -*- coding:utf-8 -*-
"""
@Time : 2021/4/21 11:24
@Author : domionlu@zquant.io
@File : dataBase
"""
# -*- coding:utf-8 -*-
from zq.common.const import *
from zq.model import Ticker,Bar
from loguru import logger as log
from zq.engine.timeseries import TimeSeries
from zq.engine.eventengine import EventManger,Event
from zq.common.tools import *
import pandas as pd


class BarSeries(TimeSeries):

    """
    1.支持多币种，以字典形式管理数据
    2.支持多周期，使用重采样
    3.支持便捷访问，默认一个币种数据时，可以直接访问字段数据
    4.支持事件订阅，每个采集周期结束时，回调指定的函数(策略中的next()，用于定期计算交易)
    5.支持多交易所数据管理，symbol=>binance.btcusdt
    6.单个交易对的时候，可以直接使用data.close的方式引用数据，多个交易对的时候,在init初始函数中 使用a=data["binance.btcusdt"].close,b=data["okex.btcusdt"].close引用数据
    """
    lines = ["startTime", "open", "high", "low", "close", "volume", "amount", "trades"]  #导入的pandas数据字段要求一致
    interval="" #当前使用的周期
    next_time=0 #

    def __init__(self, data=None, interval=INTERVAL_DAY):
        super().__init__(data)
        self.interval=interval
        self.event=EventManger.get_instance()

    def update_bar(self,b:Bar):
        """
        :param b:当前周期的bar
        :return:
        """
        last_bar = self.last()
        if b.startTime>last_bar.startTime:
                last_bar=Bar(last_bar)
                last_bar.broker=b.broker
                last_bar.symbol=b.symbol
                self.append(b.to_list())
                self.on_event(BAR,last_bar)
        else:
            self.update(b.to_list())

    def on_trade(self,data):
        last_bar = self.last()
        last_bar = Bar(last_bar)
        symbol=data["market"]
        broker=data["broker"]
        data = data["data"]
        nexttime=covent_nexttime(self.interval,last_bar.startTime)
        if get_cur_timestamp_ms()>=nexttime:
            last_bar=Bar()
            last_bar.startTime=nexttime

        last_bar.symbol =symbol
        last_bar.broker = broker
        for i in data:
            price=i["price"]
            volume=i["size"]
            if last_bar.open==0:
                last_bar.open=price
                last_bar.high=price
                last_bar.low=price
                last_bar.close=price
            last_bar.high=max(last_bar.high,price)
            last_bar.low=min(last_bar.low,price)
            last_bar.volume=last_bar.volume+volume
            last_bar.amount=last_bar.amount+price*volume
            last_bar.trades=last_bar.trades+1
        self.update_bar(last_bar)


    def on_event(self,type,data):
        """
        todo 时序数据回调，用于绑定数据源与具体策略的调用关系
        定义几种事件类型，
        1.BAR,新bar生成
        2.TICKER，每次ticker事件
        3.spread，二个种币价差满足条件，用于套利等策略
        4.后续可以扩展计算方式
        在update_ticke函数中根据r定义事件回调对应的函数
        """
        e=Event(type,data)
        self.event.put(e)
        # log.info("put event")


def covent_nexttime(timeframe,t):
    "Bar的"
    s={
        INTERVAL_S1:1,
        INTERVAL_S5: 5,
        INTERVAL_S15: 15,
        INTERVAL_MIN1: 60,
        INTERVAL_MIN5: 60*5,
        INTERVAL_MIN15: 60*15,
        INTERVAL_MIN30: 60 * 30,
        INTERVAL_HOUR1: 3600,
        INTERVAL_HOUR2: 3600*2,
        INTERVAL_HOUR4: 3600*4,
        INTERVAL_HOUR8: 3600*8,
        INTERVAL_HOUR12: 3600 * 12,
        INTERVAL_DAY: 86400,
        INTERVAL_WEEK:86400*7,
        INTERVAL_MONTH:86400*30
    }
    return t+s[timeframe]*1000