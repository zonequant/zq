# -*- coding:utf-8 -*-
"""
@Time : 2020/4/25 1:21 下午
@Author : Domionlu
@Site : 
@File : ftx.py
"""
import hmac
from zq.engine.baseBroke import BaseBroker
from zq.common.const import *
from requests import Request
from zq.common.tools import *
import time
import traceback
from zq.model import *
import pandas as pd
from loguru import logger as log
from zq.engine.aiowebsocket import BaseMarket
import json
from zq.engine.barseries import BarSeries

INTERVAL_MAP = {

    INTERVAL_MIN1: 60,
    INTERVAL_MIN5: 300,
    INTERVAL_MIN15: 60 * 15,
    INTERVAL_MIN30: 60 * 30,
    INTERVAL_HOUR1: 3600,
    INTERVAL_HOUR2: 3600 * 2,
    INTERVAL_HOUR4: 3600 * 4,
    INTERVAL_HOUR8: 3600 * 8,
    INTERVAL_HOUR12: 3600 * 12,
    INTERVAL_DAY: 3600 * 24,
    INTERVAL_WEEK: 3600 * 24 * 7,
    INTERVAL_MONTH: 3600 * 24 * 30

}

SIDE_MAP = {
    OPEN_BUY: "buy",
    OPEN_SELL: "sell",
}

ORDER_TYPE_MAP = {
    LIMIT: "limit",
    MARKET: "market",
    POST_ONLY: "post_only",
    FOK: "fok",
    IOC: "ioc"
}

STATUS_MAP = {
    "cancelled": STATUS_CANCELED,
    "new": STATUS_NEW,
    "open":STATUS_NEW,
    "partially_filled": STATUS_PARTIALLY_FILLED,
    "filled": STATUS_FILLED,
    "closed":STATUS_CANCELED
}

ord_type_map = {
    "market": MARKET,
    "limit": LIMIT,
    "post_only": POST_ONLY,
    "fok": FOK,
    "ioc": IOC
}

MARKET_TYPE_MAP = {
    SPOT: "SPOT",
    MARGIN: "MARGIN",
    SWAP: "SWAP",
    FUTURES: "FUTURES",
    OPTION: "OPTION"
}


class Ftx(BaseBroker):
    """
        api文档 https://docs.ftx.com/#overview
        """
    api = {
        BAR: {
            "path": "/markets/{market_name}/candles",
            "method": "GET",
            "auth": False
        },

        ORDER_BOOK: {
            "path": "/markets/{market_name}/orderbook?depth=20",
            "method": "GET",
            "auth": False
        },
        TRADE: {
            "path": "/markets/{market_name}/trades",
            "method": "GET",
            "auth": False
        },
        EXCHANGE: {
            "path": "/markets",
            "method": "GET",
            "auth": False
        },
        BALANCE: {
            "path": "/wallet/balances",
            "method": "GET",
            "auth": True
        },
        ORDER: {
            "path": "/orders",
            "method": "POST",
            "auth": True
        },
        CANCEL_ORDER: {
            "path": "/orders/{order_id}",
            "method": "DELETE",
            "auth": True
        },
        CANCEL_ALL_ORDERS: {
            "path": "/orders",
            "method": "DELETE",
            "auth": True
        },
        OPEN_ORDERS: {
            "path": "/orders?market={market}",
            "method": "GET",
            "auth": True
        },
        POSITION: {
            "path": "/positions",
            "method": "GET",
            "auth": True
        },
        ORDER_INFO: {
            "path": "/orders/{order_id}",
            "method": "GET",
            "auth": True
        },
        LEVERAGE: {
            "path": "/account/leverage",  # 调整开仓杠杆率
            "method": "POST",
            "auth": True
        },
        FUNDING: {
            "path": "/futures/{future_name}/stats",
            "method": "GET",
            "auth": False
        },
        FUNDING_HIS: {
            "path": "/funding_rates",  # 历史资金费率
            "method": "GET",
            "auth": False
        },

    }
    host = "https://ftx.com/api"

    def __init__(self, api_key=None, api_secret=None, market_type=SPOT):
        super().__init__()
        self.symbols = self.get_exchange()
        self.api_key = api_key
        self.api_secret = api_secret
        self.market_type = market_type
        self.market = Ftx_Market(self)
        self.market.start()
        if self.api_key:
            self.trade = Ftx_Trade(self)
            self.trade.start()
            self.trade.add_feed({ORDER: self.on_order})

    def build_request(self, action, **kwargs):
        api = self.get_api()
        api = api.get(action, None)
        host = self.get_url()
        if api:
            path = api.get("path")
            m = api.get("method")
            auth = api.get("auth")
            params = kwargs.get("data", None)
            # 增加path传参的逻辑
            path, params = self.replace_param(path, params)
            request_path = path
            if m == "GET":
                request = Request(m, host + request_path, params=params)
            else:
                request = Request(m, host + request_path, json=params)
            # 是否为私有数据，进行签名处理
            if auth:
                request = self.sign_request(request)
            return request
        else:
            return False

    def replace_param(self, path, params):
        """
        用于拼接url参数化 形式{param}
        :param path:
        :param params:
        :return:
        """
        param_list = ["market_name", "order_id", "market", "future_name"]
        for i in param_list:
            p = "{" + i + "}"
            if p in path:
                param=str(params[i])
                path=path.replace(p, param)
                params.pop(i)
        return path, params

    def get_url(self):
        return self.host

    def get_api(self):
        return self.api


    def data_feed(self,symbol, interval=INTERVAL_DAY):
        """
        if symbol=ALL,则进行全市场的订阅
        if symbol=List 则订阅组合
        datas数据格式，时序容器，方便方便的访问里面的数据，参考backtrader
        首次加载数据使用get_bars,后续更新数据使用websocket订阅ticker，自己合成bar
        """
        if isinstance(symbol,list):
            for s in symbol:
                data =self.get_bar(s, interval)
                self.datas.add(BarSeries(data, interval=interval),s)
                self.market.add_feed({TRADE: self.on_trade},symbol=s)
        else:
            data=self.get_bar(symbol,interval)
            self.datas.add(BarSeries(data,interval=interval), symbol)
            self.market.add_feed({ TRADE: self.on_trade},symbol=symbol)

    def on_trade(self, data):

        if "data" in data:
            symbol = data["market"]
            data["broker"]=self.name
            self.datas[symbol].on_trade(data)

    def sign_request(self, request):
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        method=prepared.method
        signature_payload = f'{ts}{method}{prepared.path_url}'.encode()
        if (method == 'POST') or (method == 'DELETE'):
            signature_payload = f'{ts}{method}{prepared.path_url}'.encode()
            signature_payload += prepared.body
            request.headers['Content-Type'] = 'application/json'
        signature = hmac.new(self.api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self.api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        return request

    def get_exchange(self):
        return self.fetch(EXCHANGE)

    def parse_exchange(self, data):
        if data.get("success", None) == True:
            ls = data.get("result", [])
            for i in ls:
                symbol = i["name"]
                self.symbols[symbol] = i
            return self.symbols

    def get_balance(self, symbol=None):
        data = self.fetch(BALANCE)
        self.assets = data
        if symbol:
            return data[symbol]
        else:
            return data

    def parse_balance(self, data):
        data = data.get("result", None)
        if data:
            assets = {}
            for i in data:
                coin = i.get("coin")
                asset = assets.get(coin, None)
                if asset is None:
                    asset = Asset()
                    asset.name = coin
                    asset.free = float(i.get("free"))
                    asset.balance = float(i.get("total"))
                    asset.frozen = asset.balance - asset.free
                assets[asset.name] = asset
            return assets
        return None

    def create_order(self, o: Order):

        params = {'market': o.symbol,
                  'side': SIDE_MAP[o.side],
                  'price':o.price,
                  'size': o.qty,
                  "type": ORDER_TYPE_MAP[o.order_type],
                  'reduceOnly': o.reduce,
                  'ioc': o.ioc,
                  'postOnly': o.post,
                  'clientId':None
                  }
        if o.order_type == MARKET:
            params["price"] = o.price

        status, msg = self.fetch(ORDER, params)
        order.status = status
        if status == STATUS_REJECTED:
            order.err_msg = msg
            log.error(order)
            log.error(msg)
        else:
            order.order_id = msg
        return order

    def parse_order(self, data):
        """
        :param data:订单返回的状态
        :return: 正常订单 状态+orderid,拒绝订单 状态+msg
        """
        success = data.get("success", False)
        if success:
            ls = data.get("result")
            status = STATUS_MAP[ls["status"]]
            orderid = ls["id"]
            return status, orderid
        else:
            msg =  data.get("error")
            return STATUS_REJECTED, msg

    def get_open_orders(self, symbol):
        p = {"market": symbol}
        return self.fetch(OPEN_ORDERS, p)

    def parse_open_orders(self, data):
        success = data.get("success", False)
        if success:
            orders = []
            ls = data["result"]
            for l in ls:
                order = self.order_info_parse(l)
                orders.append(order)
            return orders
        else:
            return None

    def order_info_parse(self, data):
        o = Order()
        o.order_id = data["id"]
        o.symbol = data["market"]
        o.qty = data["size"]
        o.price = data["price"]
        o.filled_qty = data["filledSize"]
        o.status = STATUS_MAP[data["status"]]
        if o.status=="closed":
            if o.filled_qty==0:
                o.status=STATUS_CANCELED
            elif o.filled_qty<o.qty:
                o.status=STATUS_PARTIALLY_FILLED
            else:
                o.status=STATUS_FILLED
        o.time = data["createdAt"]
        o.side = BUY if data.get("side") == "buy" else SELL
        return o

    def cancel_order(self, order):
        p = {"order_id": order.order_id}
        result = self.fetch(CANCEL_ORDER, p)
        if result["success"]:
            order.status = STATUS_CANCELED
        else:
            msg = result["error"]
            log.error(msg)
            order = self.update_order(order)
        return order

    def cancel_all_orders(self, symbol):
        p = {"market": symbol}
        result = self.fetch(CANCEL_ALL_ORDERS, p)
        return result.get("success", False)

    def update_order(self, order):
        p = {"order_id": order.order_id}
        result = self.fetch(ORDER_INFO, p)
        if result.get("success", False):
            return self.order_info_parse(result["result"])

    def get_bar(self, symbol, interval=INTERVAL_DAY, start_time=None, end_time=None):
        p = {"market_name": symbol, "resolution": INTERVAL_MAP[interval]}
        if start_time:
            p["start_time"] = int(start_time)
        if end_time:
            p["end_time"] = int(end_time)
        return self.fetch(BAR, p)

    def parse_bar(self, data):
        success = data.get("success", False)
        if success:
            df = []
            ls = data["result"]
            for i in ls:
                df.append({"startTime": float(i["time"]),
                           "open": float(i["open"]),
                           "high": float(i["high"]),
                           "low": float(i["low"]),
                           "close": float(i["close"]),
                           "volume": float(i["volume"]),
                           "amount": 0,
                           "trades": 0
                           })
            df = pd.DataFrame(df)
            df.columns = ['startTime', 'open', 'high', 'low', 'close', 'volume', "amount", "trades"]
            df = df.sort_values(by="startTime")
            return df
        else:
            return []

    def get_ticker(self, symbol):
        """
        :param symbol:
        :return:
        """
        p = {"market_name": symbol}
        return self.fetch(TICKER, p)

    def parse_tick(self, data):
        data = data.get("result", None)
        if data:
            tick = Ticker()
            tick.price = float(data["price"])
            tick.ask_price = float(data["ask"])
            tick.bid_price = float(data["bid"])
            tick.time = get_cur_timestamp_ms()
            tick.symbol = data["name"]
            tick.mid_price = (tick.ask_price + tick.bid_price) / 2
            return tick
        else:
            return None

    def get_order_book(self, symbol, depth=20):
        p = {"market_name": symbol, "depth": depth}
        ob = self.fetch(ORDER_BOOK, p)
        ob.symbol = symbol
        return ob

    def parse_order_book(self, data):
        ob = Order_book()
        bids = data["bids"]
        asks = data["asks"]
        ob.update(bids, asks)
        ob.update_time = get_cur_timestamp_ms()
        return ob

    def get_position(self, symbol=None):
        p = {"timestamp": get_cur_timestamp_ms()}
        pos = self.fetch(POSITION, p)
        return pos

    def parse_position(self, data):
        """
        :param data:
        :return:
        """
        success = data.get("success", False)
        if success:
            poss = data["positions"]

            for p in poss:
                symbol = p["future"]
                pos = self.positions.get(symbol, None)
                if pos is None:
                    pos = Position()
                    pos.symbol = symbol
                pos.pnl = float(p["realizedPnl"])
                pos.price = float(p["entryPrice"])
                pos.amount = float(p["size"])
                pos.side = SHORT if (p["side"]) == "sell" else LONG
                pos.margin = float(p["initialMarginRequirement"])
                self.positions[pos.symbol] = pos
            return self.positions

    def set_leverage(self, leverage):
        """
        默认全仓模式
        :param symbol:
        :param leverage:
        :return:
        """
        p = {"leverage": leverage}
        return self.fetch(LEVERAGE, p)

    def parse_leverage(self, data):
        return data.get("success", False)

    def get_trades(self, symbol):
        p = {"market_name": symbol}
        return self.fetch(TRADE, p)

    def parse_trades(self, data):
        """
        :param data:
        :return: {
                  "id": 3855995,
                  "liquidation": false,
                  "price": 3857.75,
                  "side": "buy",
                  "size": 0.111,
                  "time": "2019-03-20T18:16:23.397991+00:00"
                }
        """
        if data.get("success", False):
            return data["result"]

    def get_funding(self, symbol):
        p = {"future_name": symbol}
        return self.fetch(FUNDING, p)

    def parse_funding(self, data):
        """
        :param data:
        :return:  {
                    "volume": 1000.23,
                    "nextFundingRate": 0.00025,
                    "nextFundingTime": "2019-03-29T03:00:00+00:00",
                    "expirationPrice": 3992.1,
                    "predictedExpirationPrice": 3993.6,
                    "strikePrice": 8182.35,
                    "openInterest": 21124.583
                  }
        """
        if data.get("success", False):
            return data["result"]

    def get_funding_his(self, symbol, startTime=None, endTime=None):
        p = {"future": symbol}
        if startTime:
            p["start_time"] = startTime
        if endTime:
            p["end_time"] = endTime
        return self.fetch(FUNDING, p)

    def parse_funding_his(self, data):
        """
        :param data:
        :return: [
                    {
                      "future": "BTC-PERP",
                      "rate": 0.0025,
                      "time": "2019-06-02T08:00:00+00:00"
                    }
                ]
        """
        if data.get("success", False):
            return data["result"]


class Ftx_Market(BaseMarket):
    params = {
        "name": "FTX",
        "topics": ["data"],
        "is_binary": False,
        "interval": 15  # 心跳间隔 单位秒
    }
    host = "wss://ftx.com/ws/"
    channels = {
                TRADE:{
                    "sub": '{"op": "subscribe", "channel": "trades","market":  "{symbol}"}',
                    "topic": "trades",
                    "auth": False
                },
                TICKER: {
                    "sub": '{"op": "subscribe", "channel": "ticker","market":  "{symbol}"}',
                    "topic": "ticker",
                    "auth": False
                },
                ORDER_BOOK: {
                    "sub": '{"op": "subscribe", "channel": "orderbook","market":  "{symbol}"}',
                    "topic": "orderbook",
                    "auth": False
                }
            }

    def get_channels(self):
        return self.channels

    def get_url(self):
        return self.host

    def parse_bar(self, data):
        try:
            b = Bar()
            b.broker = self.name
            print(data)
        except:
            log.error(traceback.print_exc())

    def parse_order_book(self, data):
        try:
            symbol = data["market"]
            data = data.get("data")
            if data:
                ob = self.order_books.get(symbol)
                if ob is None:
                    ob = Order_book()
                    ob.symbol = symbol

                ob.update_time = float(data["time"])
                bids = data["bids"]
                asks = data["asks"]
                ob.update(bids,asks)
                return ob
        except:
            log.error(traceback.print_exc())

    def parse_ticker(self, data):
        try:
            if "data" in data:
                ticker = Ticker()
                ticker.symbol = data["market"]
                data=data["data"]
                ticker.broker = self.p.name
                ticker.ask_price = float(data["ask"])
                ticker.ask_volume =float(data["askSize"])
                ticker.bid_price = float(data["bid"])
                ticker.bid_volume = float(data["bidSize"])
                ticker.price=float(data["last"])
                ticker.time = data["time"]
                ticker.mid_price = (ticker.ask_price + ticker.bid_price) / 2
                return ticker
        except:
            log.error(traceback.print_exc())


class Ftx_Trade(Ftx_Market):
    params = {
        "name": "FTX",
        "topics": ["data"],
        "is_binary": False,
        "interval": 15  # 心跳间隔 单位秒
    }
    host = "wss://ftx.com/ws/"
    channels = {
        ORDER: {
            "sub": '{"op":"subscribe", "channel": "orders"}',
            "topic": "orders",
        },
    }

    async def connected_callback(self):
        self.connected = True
        sign = self.sign_sub()
        await self.send(sign)
        i = 0
        while i < 10:
            if self.islogin:
                for c in self.subscribes:
                    msg = json.loads(c)
                    await self.send(msg)
                    log.info(f"send {msg}")
                    i=10
            else:
                i+=1
        # 订阅完后可开始处理心跳
        self._loop.create_task(self.heartbeat())

    def sign_sub(self, **kwargs):
        ts = int(time.time() * 1000)
        data = {'op': 'login', 'args': {
            'key': self.broker.api_key,
            'sign': hmac.new(
                self.broker.api_secret.encode(), f'{ts}websocket_login'.encode(), 'sha256').hexdigest(),
            'time': ts,
        }}
        return data

    async def callback(self, data):
        # print(data)
        if "login" in str(data):
            if data["code"] == "0":
                self.islogin = True



    async def ping(self):
        await self.send("{'op': 'ping'}")

    def order_parse(self, data):
        ls = data.get("data")
        orders = []
        if ls:
            for i in ls:
                try:
                    o = Order()
                    o.symbol = i['market']
                    o.broker = "FTX"
                    o.order_id = i['id']
                    o.time = get_cur_timestamp_ms()
                    o.side = i['side']
                    o.type = i['type']
                    o.price = float(i['price'])
                    o.qty = float(i['size'])
                    o.filled_qty = float(i['filledSize'])
                    o.avg_price = i['avgFillPrice']
                    o.status = STATUS_MAP[i['status']]
                    orders.append(order)
                except Exception as e:
                    log.error(traceback.format_exc())

            return orders
