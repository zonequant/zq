# -*- coding:utf-8 -*-
"""
@Time : 2021/5/12 19:31
@Author : domionlu@zquant.io
@File : basetrade
"""
from zq.engine.restclient import RestClient
from zq.common.const import *
from abc import abstractmethod
from zq.model import Order, Asset, Position, Order_book, Ticker, Bar
from zq.engine.barseries import BarSeries
from zq.engine.timeseries import Dataset
from zq.engine.eventengine import EventManger,Event

class BaseBroker(RestClient):
    name=None
    positions = {}
    orders = {}
    assets = {}
    symbols={}
    datas=None

    def __init__(self, api_key=None, api_secret=None, market_type=SPOT):
        super().__init__()
        self.event=EventManger.get_instance()
        self.api_key = api_key
        self.api_secret = api_secret
        self.market_type = market_type
        self.trade=None
        self.market=None

    def on_account(self, data):
        self.assets.update(self.trade.assets)
        e = Event(ACCOUNT, self.assets)
        self.event.put(e)

    def on_order(self, data):
        e=Event(ORDER,data)
        self.event.put(e)

    def on_position(self,data):
        e = Event(POSITION, data)
        self.event.put(e)

    def set_dataset(self,dataset):
        self.datas=dataset

    def data_feed(self,symbol, interval=INTERVAL_DAY):
        """
        if symbol=ALL,则进行全市场的订阅
        if symbol=List 则订阅组合
        datas数据格式，时序容器，方便方便的访问里面的数据，参考backtrader
        首次加载数据使用get_bars,后续更新数据使用websocket订阅bar推送
        """
        if symbol=="ALL":
            symbol=self.symbols.keys()
        if self.datas is None:
            self.datas=Dataset()
        self.datas.interval=interval
        if isinstance(symbol,list):
            for s in symbol:
                data = self.get_bar(s, interval)
                self.datas.add(BarSeries(data,interval=interval),s)
                self.market.add_feed({BAR: self.on_bar, TICKER: self.on_ticker},symbol=s,interval=interval)
        else:
            data =  self.get_bar(symbol, interval)
            self.datas.add(BarSeries(data,interval=interval),symbol)
            self.market.add_feed({BAR: self.on_bar, TICKER: self.on_ticker},symbol=symbol,interval=interval)

    def on_bar(self,data):
        symbol=data.symbol
        self.datas[symbol].update_bar(data)

    def on_ticker(self, data):
        """
         订阅推送过来的ticker数据，不在datas中的symbol不做处理(由Barseries负责处理数据逻辑)。需要自定义单独的订阅可以直接调用self.market.add_feed()
        需要转义为ticker实例，以便后续处理
        """
        e = Event(TICKER, data)
        self.event.put(e)

    def sell(self, symbol, volume, price=None, order_type=LIMIT):
        o = Order()
        o.symbol = symbol
        o.qty = volume
        o.side = OPEN_SELL
        if price:
            o.price = price
        else:
            order_type = MARKET
        o.order_type = order_type
        return self.create_order(o)

    def buy(self, symbol, volume, price=None, order_type=LIMIT):
        o = Order()
        o.symbol = symbol
        o.qty = volume
        o.side = OPEN_BUY
        if price:
            o.price = price
        else:
            order_type = MARKET
        o.order_type = order_type
        return self.create_order(o)


    def check_order(self,order):
        """
        todo 检查订单的价格限制 ，数量限制
        """

    @abstractmethod
    def get_exchange(self):
        pass

    @abstractmethod
    def get_balance(self, symbol=None):
        pass

    @abstractmethod
    def get_open_order(self, symbol):
        pass

    @abstractmethod
    def get_position(self, symbol=None):
        pass

    @abstractmethod
    def update_order(self, order):
        pass

    @abstractmethod
    def create_order(self, order):
        pass

    @abstractmethod
    def cancel_order(self, order):
        pass

    @abstractmethod
    def cancel_all_orders(self, symbol):
        pass

    @abstractmethod
    def get_bar(self, symbol, interval=INTERVAL_DAY, start_time=None,end_time=None):
        pass

    @abstractmethod
    def get_ticker(self, symbol):
        pass

    @abstractmethod
    def get_order_book(self, symbol):
        pass

    @abstractmethod
    def get_trades(self, symbol):
        pass

    @abstractmethod
    def get_funding(self, symbol):
        pass

    @abstractmethod
    def get_interest(self, symbol):
        pass

    def get_market_type(self,symbol):
        pass