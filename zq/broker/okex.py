# -*- coding:utf-8 -*-
"""
@Time : 2021/5/8 10:03
@Author : domionlu@zquant.io
@File : okex
"""
import base64
from zq.engine.baseBroke import BaseBroker
from zq.common.const import *
from zq.common.tools import *
import hmac
from zq.model import Order, Asset, Position, Order_book, Ticker, Bar
from loguru import logger as log
import pandas as pd
from zq.engine.aiowebsocket import BaseMarket
import traceback
from urllib.parse import urlparse
import json
from zq.engine.timeseries import Dataset
from zq.engine.barseries import BarSeries

INTERVAL_MAP = {

    INTERVAL_MIN1: "1m",
    INTERVAL_MIN5: "5m",
    INTERVAL_MIN15: "15m",
    INTERVAL_MIN30: "30m",
    INTERVAL_HOUR1: "1H",
    INTERVAL_HOUR2: "2H",
    INTERVAL_HOUR4: "4H",
    INTERVAL_HOUR8: "8H",
    INTERVAL_HOUR12: "12H",
    INTERVAL_DAY: "1D",
    INTERVAL_WEEK: "1W",
    INTERVAL_MONTH: "1M"

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
    "canceled": STATUS_CANCELED,
    "live": STATUS_NEW,
    "partially_filled": STATUS_PARTIALLY_FILLED,
    "filled": STATUS_FILLED
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
    USDT_SWAP: "SWAP",
    OPTION: "OPTION"
}


def get_timestamp():
    now = datetime.datetime.utcnow()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


class Okex(BaseBroker):
    """
    api文档 https://www.okx.com/docs-v5/zh/#7d0fb355e8
    """
    _name = "OKEX"
    api = {
        BAR: {
            "path": "/api/v5/market/candles",
            "method": "GET",
            "auth": False
        },
        TICKER: {
            "path": "/api/v5/market/ticker",
            "method": "GET",
            "auth": False
        },
        ORDER_BOOK: {
            "path": "/api/v5/market/books",
            "method": "GET",
            "auth": False
        },
        TRADE: {
            "path": "/api/v5/market/trades",
            "method": "GET",
            "auth": False
        },
        EXCHANGE: {
            "path": "/api/v5/public/instruments",
            "method": "GET",
            "auth": False
        },
        BALANCE: {
            "path": "/api/v5/account/balance",
            "method": "GET",
            "auth": True
        },
        ORDER: {
            "path": "/api/v5/trade/order",
            "method": "POST",
            "auth": True
        },
        CANCEL_ORDER: {
            "path": "/api/v5/trade/cancel-order",
            "method": "POST",
            "auth": True
        },
        CANCEL_ALL_ORDERS: {
            "path": "/api/v5/trade/cancel-batch-orders",
            "method": "POST",
            "auth": True
        },
        OPEN_ORDERS: {
            "path": "/api/v5/trade/orders-pending",
            "method": "GET",
            "auth": True
        },
        POSITION: {
            "path": "/api/v5/account/positions",
            "method": "GET",
            "auth": True
        },
        ORDER_INFO: {
            "path": "/api/v5/trade/order",
            "method": "GET",
            "auth": True
        },
        LEVERAGE: {
            "path": "/api/v5/account/set-leverage",  # 调整开仓杠杆率
            "method": "POST",
            "auth": True
        },
        FUNDING: {
                   "path": "/api/v5/public/funding-rate",
                   "method": "GET",
                   "auth": False
               },
        FUNDING_HIS: {
            "path": "/api/v5/public/funding-rate-history",  # 历史资金费率
            "method": "GET",
            "auth": False
            },
        WITHDRAW:{
            "path": "/api/v5/asset/withdrawal",  # 提币
            "method": "GET",
            "auth": True
        },
        TOKEN:{
            "path": "/api/v5/asset/currencies",  # 提币
            "method": "GET",
            "auth": True
        },
        FEE:{"path": "/api/v5/account/trade-fee",  # 充币地址
         "method":"GET",
         "auth":True }

    }
    host = "https://aws.okx.com"

    def __init__(self, api_key=None, api_secret=None, passphrase=None, market_type=SPOT):
        super().__init__(api_key,api_secret,market_type)
        self.symbols = self.get_exchange()
        self.passphrase = passphrase
        self.market = Okex_Market(self)
        self.market.start()
        if self.api_key:
            self.trade = Okex_Trade(self)
            self.trade.start()
            self.trade.add_feed({ACCOUNT: self.on_account, ORDER: self.on_order,POSITION:self.on_position},instType=self.market_type)

    def get_exchange(self):
        p = {"instType": MARKET_TYPE_MAP[self.market_type]}
        return self.fetch(EXCHANGE, p)


    def parse_exchange(self, data):
        if data.get("code", None) == "0":
            ls = data.get("data", [])
            for i in ls:
                symbol = i["instId"]
                i["market_type"]=self.market_type
                self.symbols[symbol] = i
            return self.symbols

    def sign_request(self, request,sign=True):
        time_stamp = get_timestamp()
        path = request.url
        path = urlparse(path)
        prepared = request.prepare()
        request_path = path.path
        params = request.data
        method = request.method
        if method == "GET" :
            request_path = prepared.path_url
        body = json.dumps(params) if method == "POST" else ""
        request.data = body
        message = str(time_stamp) + str.upper(method) + request_path + body
        mac = hmac.new(bytes(self.api_secret, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        d = mac.digest()
        sign = base64.b64encode(d)
        header = dict()
        header['Content-Type'] = "application/json"
        header["OK-ACCESS-KEY"] = self.api_key
        header["OK-ACCESS-SIGN"] = sign
        header["OK-ACCESS-TIMESTAMP"] = str(time_stamp)
        header["OK-ACCESS-PASSPHRASE"] = self.passphrase
        request.headers = header
        return request

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
        map={INTERVAL_MIN1:"candle1m",
             INTERVAL_MIN5:"candle5m",
             INTERVAL_MIN15:"candle15m",
             INTERVAL_MIN30:"candle30m",
             INTERVAL_HOUR1: "candle1H",
             INTERVAL_HOUR2: "candle2H",
             INTERVAL_HOUR4: "candle4H",
             INTERVAL_HOUR12: "candle12H",
             INTERVAL_DAY: "candle1D",
             INTERVAL_WEEK: "candle1W",
             INTERVAL_MONTH:"candle1M"
             }
        if symbol=="ALL":
            symbol=self.symbols.keys()
        self.datas.interval=interval
        if isinstance(symbol,list):
            for s in symbol:
                data =self.get_bar(s, interval)
                self.datas.add(BarSeries(data, interval=interval),s)
                self.market.add_feed({BAR: self.on_bar, TICKER: self.on_ticker},symbol=s, interval=map[interval])
        else:
            data=self.get_bar(symbol,interval)
            self.datas.add(BarSeries(data,interval=interval), symbol)
            self.market.add_feed({BAR: self.on_bar, TICKER: self.on_ticker},symbol=symbol, interval=map[interval])



    def get_balance(self, asset=None):
        p = ""
        if asset:
            p = {"ccy": asset}
        data = self.fetch(BALANCE, p)
        self.assets = data
        if asset:
            if asset in data:
                return data[asset]
            else:
                result= Asset()
                result.name = asset
                result.broker = self.name
                return result
        else:
            return data

    def parse_balance(self, data):
        if data.get("code", None) == "0":
            ls = data.get("data")[0]
            detail = ls.get("details", [])
            assets = {}
            for i in detail:
                currency = i.get("ccy")
                asset = assets.get(currency, None)
                if asset is None:
                    asset = Asset()
                    asset.name = currency
                asset.free = float(i.get("cashBal"))
                asset.frozen = float(i.get("frozenBal"))
                asset.balance = float(i.get("eq"))
                assets[asset.name] = asset
            return assets
        else:
            log.info(f"get balance error {data}")
            return {}


    def create_order(self,  order: Order):
        """
        交易模式，下单时需要指定
        简单交易模式：
        - 币币和期权买方：cash
        单币种保证金模式：
        - 逐仓杠杆：isolated
        - 全仓杠杆：cross
        - 全仓币币：cash
        - 全仓交割/永续/期权：cross
        - 逐仓交割/永续/期权：isolated
        跨币种保证金模式：
        - 逐仓杠杆：isolated
        - 全仓币币：cross
        - 全仓交割/永续/期权：cross
        - 逐仓交割/永续/期权：isolated
        todo 2021.5.19 目标只支持币币或全仓模式，不支持逐仓模式
        """
        order.qty=self.qty_ct(order.symbol,order.qty)
        p = {
            "instId": order.symbol,
            "side": SIDE_MAP[order.side],
            "sz": order.qty,
            "ordType": ORDER_TYPE_MAP[order.order_type],
        }
        if self.market_type == SPOT:
            p["tdMode"] = "cash"
        else:
            p["tdMode"] = "cross"
        if order.order_type == MARKET:
            p["sz"] = order.qty
        else:
            p["sz"] = order.qty
            p["px"] = order.price
        status, msg = self.fetch(ORDER, p)
        order.status = status
        order.broker = self.name
        order.market_type = self.market_type
        if status == STATUS_REJECTED:
            order.err_msg = msg
            log.error(order)
            log.error(msg)
        else:
            order.order_id = msg
        return order

    def qty_ct(self,symbol,qty):
        """
        合约使用张数，需要换算成币数，币币交易不需要换算
        查询订单返回的张数需要换算成币数
        :param symbol:
        :param qty:
        :return:
        """
        filters=self.symbols[symbol]
        if self.market_type==SPOT:
            lot_size=filters.get("lotSz",None)
            if lot_size:
                min_qty = float(lot_size["minQty"])
                min_qty = round(1 / min_qty)
                qty=round(qty*min_qty)/min_qty
        else:
            ctVal=filters.get("ctVal",None)
            if ctVal:
                min_qty = float(ctVal)
                qty=round(qty/min_qty)
        return qty

    def ct_qty(self,symbol,qty):
        if self.market_type==SPOT:
            return qty
        else:
            filters=self.symbols[symbol]
            qty=qty*float(filters["ctVal"])
            return qty

    def parse_order(self, data):
        """

        :param data:订单返回的状态
        :return: 正常订单 状态+orderid,拒绝订单 状态+msg
        """
        if data["code"]=="0":
            ls = data.get("data")[0]
            orderid = ls["ordId"]
            return STATUS_NEW,orderid
        else:
            ls = data.get("data")[0]
            msg = ls.get("sMsg")
            return STATUS_REJECTED, msg

    def get_open_orders(self, symbol):
        p = {"instId": symbol,"instType": MARKET_TYPE_MAP[self.market_type]}
        return self.fetch(OPEN_ORDERS, p)

    def parse_open_orders(self, data):
        if data.get("code", None) == "0":
            ls = data.get("data")
            data = []
            for l in ls:
                order = self.parse_order_info(l)
                data.append(order)
            return data
        else:
            return None

    def cancel_order(self, order):
        """
        todo 撤消订单解析结果需要修复
        :param order:
        :return:
        """
        p = {"instId": order.symbol, "ordId": order.order_id}
        result = self.fetch(CANCEL_ORDER, p)
        if result["code"]=="0":
            order.status = STATUS_CANCELED
        else:
            msg = result["data"][0]["sMsg"]
            log.error(msg)
            order = self.update_order(order)
        return order




    def cancel_all_orders(self, orders):
        p = []
        for o in orders:
            p.append({"instId": o.symbol, "ordId": o.order_id})
        return self.fetch(CANCEL_ALL_ORDERS, p)

    def cancel_all_orders_parse(self, data):
        if data.get("code", None) == "0":
            return True
        else:
            return False

    def update_order(self, order):
        p = {"instId": order.symbol, "ordId": order.order_id}
        return self.fetch(ORDER_INFO, p)

    def parse_order_info(self, data):
        """
        合约返回的订单信息是张数，需要转换成币数
        :param data:
        :return:
        """
        if data.get("code", None) == "0":
            # log.info(data)
            data=data["data"][0]
            order = Order()
            order.symbol = data.get("instId")
            order.broker = self.name
            order.market_type = self.market_type
            order.order_id = data.get("ordId")
            avgpx=data.get("avgPx",0)
            order.avg_price = 0 if avgpx=="" else float(avgpx)
            order.price = float(data.get("px"))
            order.side = BUY if data.get("side") == "buy" else SELL
            order.qty=self.ct_qty(order.symbol,float(data.get("sz")))
            order.filled_qty=self.ct_qty(order.symbol,float(data.get("fillSz")))
            order.fee = float(data.get("fee"))
            status = data.get("state")
            order.status = STATUS_MAP[status]
            order.order_type = ord_type_map[data.get("ordType")]
            for k, v in MARKET_TYPE_MAP.items():
                if v == data.get("instType"):
                    order.market_type = k
            order.time = int(data.get("cTime"))
            return order

    def get_bar(self, symbol, interval=INTERVAL_DAY, start_time=None,end_time=None):
        p = {"instId": symbol, "bar": INTERVAL_MAP[interval]}
        if start_time:
            p["before"] = int(start_time)
        if end_time:
            p["after"] = int(end_time)
        return self.fetch(BAR, p)

    def parse_bar(self, data):
        if data.get("code", None) == "0":
            ls = data.get("data", [])
            df = []
            for i in ls:
                df.append({"startTime": float(i[0]),
                           "open": float(i[1]),
                           "high": float(i[2]),
                           "low": float(i[3]),
                           "close": float(i[4]),
                           "volume": float(i[5]),
                           "amount": float(i[6]),
                           "trades": 0
                           })
            df = pd.DataFrame(df)
            df.columns = ['startTime', 'open', 'high', 'low', 'close', 'volume', "amount", "trades"]
            df=df.sort_values(by="startTime")
            return df
        else:
            return []

    def get_ticker(self, symbol):
        """
        :param symbol:
        :return:
        """
        p = {"instId": symbol}
        return self.fetch(TICKER, p)

    def parse_ticker(self, data):
        if data.get("code", None) == "0":
            t = data["data"][0]
            ticker = Ticker()
            ticker.amount = float(t["volCcy24h"])
            ticker.open = float(t["open24h"])
            ticker.close = float(t["last"])
            ticker.high = float(t["high24h"])
            ticker.low = float(t["low24h"])
            ticker.volume = float(t["vol24h"])
            ticker.price = float(t["last"])
            ticker.ask_price = float(t["askPx"])
            ticker.ask_volume = float(t["askSz"])
            ticker.bid_price = float(t["bidPx"])
            ticker.bid_volume = float(t["bidSz"])
            ticker.time = t["ts"]
            ticker.mid_price = (ticker.ask_price + ticker.bid_price) / 2
            return ticker
        else:
            return None

    def get_order_book(self, symbol):
        p = {"instId": symbol, "sz": 20}
        ob=self.fetch(ORDER_BOOK, p)
        if ob:
            ob.symbol=symbol
        return ob

    def parse_order_book(self, data):
        if data.get("code", None) == "0":
            data=data["data"][0]
            ob = Order_book()
            ob.broker=self.name
            bids = data["bids"]
            asks = data["asks"]
            ob.update(bids, asks)
            ob.update_time = get_cur_timestamp_ms()
            return ob


    def get_position(self, symbol=None):
        p = {}
        if symbol:
            p["instId"] = symbol
        data = self.fetch(POSITION, p)
        if data:
            if symbol:
                return data[symbol]
            else:
                return data
        else:
            return Position()

    def parse_position(self, data):
        ls = data.get("data")
        for i in ls:
            symbol = i["instId"]
            side = i["posSide"]
            qty = float(i["pos"])
            if side == "net" and qty > 0 or side == "long":
                side = LONG
            if side == "net" and qty < 0 or side == "short":
                side = SHORT
                qty = abs(qty)
            pos = self.positions[symbol]
            pos.symbol = i["instId"]
            pos.qty=self.ct_qty(symbol,qty)
            pos.price = 0 if i["avgPx"]=="" else float(i["avgPx"])
            pos.side = side
            pos.leverage = 0 if i["lever"]=="" else float(i["lever"])
            pos.margin = 0 if i["margin"]=="" else float(i["margin"])
            pos.available =0 if i["availPos"]=="" else float(i["availPos"])
            pos.time = i["uTime"]
            pos.pnl = i["upl"]
            self.positions[symbol] = pos
        return self.positions

    def set_leverage(self, symbol, leverage):
        """
        默认全仓模式
        :param symbol:
        :param leverage:
        :return:
        """
        p = {"instId": symbol, "lever": leverage, "mgnMode": "cross"}
        new = self.fetch(LEVERAGE, p)
        if new == leverage:
            return True
        else:
            return False

    def parse_leverage(self, data):
        if data.get("code", None) == "0":
            return data["data"][0]["lever"]
        else:
            log.error(data)
            return False
        
    def get_trades(self, symbol):
        p = {"instId": symbol}
        return self.fetch(TRADE, p)

    def get_funding(self, symbol):
        p = {"instId": symbol}
        return self.fetch(FUNDING, p)

    def get_funding_his(self, symbol,startTime=None,endTime=None):
        p = {"instId": symbol,"limit":100}
        if startTime:
            p["before"]=startTime
        if endTime:
            p["after"]=endTime
        return self.fetch(FUNDING_HIS, p)

    def get_tokens(self,token):
        p={"ccy":token}
        return self.fetch(TOKEN, p)

    def parse_token(self,data):
        if data.get("code", None) == "0":
            return data["data"]
        else:
            log.error(data)
            return False

    def withdraw(self,address,amount,chain,coin):
        data=self.get_tokens(coin)
        fee=0
        for i in data:
            if i["chain"]==chain:
                fee=i["minFee"]
        p = {"ccy": coin, "chain": chain, "amt": amount, "dest": "4", "toAddr": address,"fee":fee}
        return self.fetch(WITHDRAW, p)

    def get_fees(self,symbol=None):
        p = {"instType": MARKET_TYPE_MAP[self.market_type]}
        if symbol:
            if self.market_type in(SPOT,MARGIN):
                p["instId"] = symbol
            else:
                # instId: BTC-USDT-SWAP 转换为instFamily: BTC-USDT
                symbol=self.symbols[symbol]
                p["instFamily"] = symbol["instFamily"]
        return self.fetch(FEE,p)

    def parse_fee(self,data):
        # maker/taker的值：正数，代表是返佣的费率；负数，代表平台扣除的费率。 统一负的转为正的
        if data.get("code", None) == "0":
            fee= data["data"][0]
            maker =  fee.get("maker") or fee.get("makerU") or fee.get("makerUSDC")
            taker = fee.get("taker") or fee.get("takerU") or fee.get("takerUSDC")
            return {MAKER:-float(maker),TAKER:-float(taker)}
        else:
            log.error(data)
            return None

class Okex_Market(BaseMarket):

    params = {
        "topics": ["data"],
        "is_binary": False,
        "interval": 25  # 心跳间隔 单位秒
    }
    host="wss://ws.okx.com:8443/ws/v5/public"
    channels = {
        BAR: {
            "sub": '{"op": "subscribe","args": [{"channel": "{interval}","instId": "{symbol}"}]}',
            "topic": "candle1m",
            "auth": False
        },
       TICKER: {
            "sub": '{"op": "subscribe","args": [{"channel": "tickers","instId": "{symbol}"}]}',
            "topic": "tickers",
            "auth": False
        },
       ORDER_BOOK: {
            "sub": '{"op": "subscribe","args": [{"channel": "books","instId": "{symbol}"}]}',
            "topic": "books",
            "auth": False
        },
       FUNDING: {
            "sub": '{"op": "subscribe","args": [{"channel": "funding-rate","instId": "{symbol}"}]}',
            "topic": "funding-rate",
            "auth": False
        }

    }
    def get_url(self):
        return self.host

    def get_channels(self):
        return self.channels


    def parse_bar(self, data):
        try:
            symbol = data["arg"]["instId"]
            data = data.get("data")
            if data:
                d = data[0]
                bar = Bar()
                bar.broker=self.name
                bar.symbol = symbol
                bar.startTime=int(d[0])
                bar.open=float(d[1])
                bar.high=float(d[2])
                bar.low=float(d[3])
                bar.close=float(d[4])
                bar.volume=float(d[5])
                bar.amount=float(d[6])
                bar.update_time = get_cur_timestamp_ms()
                return bar
        except:
            log.error(traceback.print_exc())

    def parse_order_book(self, data):
        try:
            symbol = data["arg"]["instId"]
            data = data.get("data")
            if data:
                data = data[0]
                ob = self.order_books[symbol]
                ob.broker=self.name
                ob.symbol = symbol
                ob.update_time = float(data["ts"])
                bids = data["bids"]
                bids = [[row[0], row[1]] for row in bids]
                asks = data["asks"]
                asks=[[row[0], row[1]] for row in asks]
                if self.market_type in [FUTURES,SWAP,USDT_SWAP]:
                    ctVal=float(self.broker.symbols.get(symbol)['ctVal'])
                    ctValCcy=self.broker.symbols.get(symbol)['ctValCcy']
                    tickSz=0.0001
                    if ctValCcy=="USD":
                        bids = [[row[0], round(float(row[1])*ctVal/float(row[0]),4)] for row in bids]
                        asks = [[row[0], round(float(row[1])*ctVal/float(row[0]),4)] for row in asks]
                    else:
                        bids = [[row[0], round(float(row[1]) * ctVal,4)] for row in bids]
                        asks = [[row[0], round(float(row[1]) * ctVal,4)] for row in asks]
                ob.update(bids, asks)
                self.order_books[symbol]=ob
                return ob
        except:
            log.error(traceback.print_exc())

    def parse_ticker(self, data):
        try:
            data = data.get("data")
            if data:
                t = data[0]
                ticker = Ticker()
                ticker.symbol = t["instId"]
                ticker.broker=self.name
                ticker.amount = float(t["volCcy24h"])
                ticker.open = float(t["open24h"])
                ticker.close = float(t["last"])
                ticker.high = float(t["high24h"])
                ticker.low = float(t["low24h"])
                ticker.volume = float(t["vol24h"])
                ticker.price = float(t["last"])
                ticker.ask_price = float(t["askPx"])
                ticker.ask_volume = float(t["askSz"])
                ticker.bid_price = float(t["bidPx"])
                ticker.bid_volume = float(t["bidSz"])
                ticker.time = t["ts"]
                ticker.mid_price = (ticker.ask_price + ticker.bid_price) / 2
                return ticker
        except:
            log.error(traceback.print_exc())

    def parse_funding(self,data):
        try:
            data=data.get("data")[0]
            return data
        except:
            log.error(traceback.print_exc())


    async def ping(self):
        await self.send("ping")

class Okex_Trade(Okex_Market):
    params = {
        "url": "wss://ws.okx.com:8443/ws/v5/private",
        "is_binary": False,
        "interval": 20  # 心跳间隔
    }
    channels = {
       ACCOUNT: {
            "sub": '{"op": "subscribe","args": [{"channel": "account"}]}',
            "topic": "account",
        },
       POSITION: {
            "sub": '{"op": "subscribe","args": [{"channel": "positions","instType": "{instType}"}]}',
            "topic": "positions",
        },
       ORDER: {
            "sub": '{"op": "subscribe","args": [{"channel": "orders","instType": "{instType}"}]}',
            "topic": "orders",
        },
    }
    host ="wss://ws.okx.com:8443/ws/v5/private"


    async def connected_callback(self):
        self.connected = True
        sign = self.sign_sub()
        await self.send(sign)
        self._loop.create_task(self.heartbeat())


    def sign_sub(self, **kwargs):
        timestamp = str(time.time()).split(".")[0] + "." + str(time.time()).split(".")[1][:3]
        message = str(timestamp) + "GET" + "/users/self/verify"
        mac = hmac.new(bytes(self.broker.api_secret, encoding="utf8"), bytes(message, encoding="utf8"),
                       digestmod="sha256")
        d = mac.digest()
        signature = base64.b64encode(d).decode()
        data = {
            "op": "login",
            "args": [{
                "apiKey": self.broker.api_key,
                "passphrase": self.broker.passphrase,
                "timestamp": timestamp,
                "sign": signature
            }]
        }
        return data

    async def callback(self, data):
        if "login" in str(data):
            if data["code"] == "0":
                self.islogin = True
                for c in self.subscribes:
                    msg = json.loads(c)
                    await self.send(msg)


    def parse_account(self, data):
        ls = data.get("data")
        if ls:
            detail = ls[0].get("details", [])
            assets = {}
            for i in detail:
                currency = i.get("ccy")
                asset = Asset()
                asset.symbol = currency
                # bal=float(i.get("availBal",0))
                availEq = float(i.get("availEq", 0))
                asset.free = availEq
                asset.frozen = float(i.get("frozenBal", 0))
                asset.balance = float(i.get("cashBal", 0))
                assets[currency]=asset
            self.assets.update(assets)
            return assets

    def parse_order(self, data):
        ls = data.get("data")
        orders ={}
        if ls:
            for i in ls:
                order = Order()
                order.broker=self.name
                order_id = i["ordId"]
                order.order_id = order_id
                order.symbol = i["instId"]
                order.qty =self.broker.ct_qty(order.symbol,float(i.get("sz",0)))
                px = data.get("px", 0)
                order.price = 0.0 if px == "" else float(px)
                side = i["side"]
                if side == "buy":
                    order.side =OPEN_BUY
                else:
                    order.side =OPEN_SELL
                order.status = STATUS_MAP[i["state"]]
                order.filled_qty = self.broker.ct_qty(float(i.get("fillSz",0)))
                avgpx = data.get("avgPx", 0)
                order.avg_price = 0.0 if avgpx == "" else float(avgpx)
                order.time = i["uTime"]
                order.fee = i["fee"]
                orders[order_id]=order
            return orders



    def parse_position(self, data):
        ls = data.get("data")
        positions = {}
        if ls:
            for i in ls:
                pos = Position()
                pos.brorker = self.name
                symbol = i["instId"]
                side = i["posSide"]
                qty = float(i["pos"])
                if side == "net" and qty > 0 or side == "long":
                    side =LONG
                if side == "net" and qty < 0 or side == "short":
                    side =SHORT
                    qty = abs(qty)
                pos.symbol = symbol
                pos.qty =self.broker.ct_qty(symbol,qty)
                pos.price =0 if i["avgPx"]=="" else float(i["avgPx"])
                pos.side = side
                pos.avg_price = float(i["avgPx"])
                pos.leverage = 0 if i["lever"]=="" else float(i["lever"])
                pos.margin =0 if i["margin"]=="" else float(i["margin"])
                pos.available =0 if i["availPos"]=="" else float(i["availPos"])
                pos.time = i["uTime"]
                pos.pnl = i["upl"]
                positions[symbol]=pos
            self.positions.update(positions)
            return positions
