# -*- coding:utf-8 -*-
"""
@Time : 2021/5/8 10:03
@Author : domionlu@zquant.io
@File : okex
"""
# -*- coding:utf-8 -*-
from zq.engine.baseBroke import BaseBroker
from zq.common.const import *
from zq.common.tools import *
import hmac
import hashlib
from zq.model import Order, Asset, Position, Order_book, Ticker, Bar
from loguru import logger as log
import pandas as pd
from zq.engine.aiowebsocket import BaseMarket
import traceback
from zq.engine.eventengine import Event

market_type_map = {
    SPOT: "SPOT",
    MARGIN: "MARGIN",
    SWAP: "SWAP",
    USDT_SWAP: "USDT_SWAP",
    FUTURES: "FUTURES",
    OPTION: "OPTION"
}

ORDER_TYPE_MAP = {
    LIMIT: "LIMIT",
    MARKET: "MARKET",
    FOK: "FOK",
    IOC: "IOC"
}

SIDE_MAP = {
    OPEN_BUY: "BUY",
    OPEN_SELL: "SELL",
}

STATUS_MAP = {
    "CANCELED": STATUS_CANCELED,
    "NEW": STATUS_NEW,
    "PARTIALLY_FILLED": STATUS_PARTIALLY_FILLED,
    "FILLED": STATUS_FILLED,
    "REJECTED": STATUS_REJECTED
}

INTERVAL_MAP = {

    INTERVAL_MIN1: "1m",
    INTERVAL_MIN5: "5m",
    INTERVAL_MIN15: "15m",
    INTERVAL_MIN30: "30m",
    INTERVAL_HOUR1: "1h",
    INTERVAL_HOUR2: "2h",
    INTERVAL_HOUR4: "4h",
    INTERVAL_HOUR8: "8h",
    INTERVAL_HOUR12: "12h",
    INTERVAL_DAY: "1d",
    INTERVAL_WEEK: "1w",
    INTERVAL_MONTH: "1M"

}

LISTENKEY = "LISTENKEY"
PUT_LISTENKEY="PUT_LISTENKEY"

class Binance(BaseBroker):
    "https://binance-docs.github.io/apidocs/spot/cn/"
    host = {
        SPOT: "https://api.binance.com",  # 现货交易
        MARGIN: "https://api.binance.com",  # 杠杆交易
        USDT_SWAP: "https://fapi.binance.com",  # U永续合约
        SWAP: "https://dapi.binance.com",  # 币永续
    }
    """
    todo 更新swap,usdt_swap的定义
    """
    api = {
        SPOT: {
            EXCHANGE: {
                "path": "/api/v3/exchangeInfo",
                "method": "GET",
                "auth": False
            },
            BAR: {
                "path": "/api/v3/klines",
                "method": "GET",
                "auth": False
            },
            TICKER: {
                "path": "/api/v3/ticker/24hr",
                "method": "GET",
                "auth": False
            },

            ORDER_BOOK: {
                "path": "/api/v3/depth",
                "method": "GET",
                "auth": False
            },
            TRADE: {
                "path": "/api/v3/ticker/bookTicker",
                "method": "GET",
                "auth": False
            },
            BALANCE: {
                "path": "/api/v3/account",
                "method": "GET",
                "auth": True
            },
            ORDER: {
                "path": "/api/v3/order",
                "method": "post",
                "auth": True
            },
            TEST: {
                "path": "/api/v3/order/test",
                "method": "POST",
                "auth": True
            },
            CANCEL_ORDER: {
                "path": "/api/v3/order",
                "method": "DELETE",
                "auth": True
            },
            CANCEL_ALL_ORDERS: {
                "path": "/api/v3/openOrders",
                "method": "DELETE",
                "auth": True
            },
            OPEN_ORDERS: {
                "path": "/api/v3/openOrders",
                "method": "GET",
                "auth": True
            },
            ORDER_INFO: {
                "path": "/api/v3/order",
                "method": "GET",
                "auth": True
            },
            LISTENKEY: {
                "path": "/api/v3/userDataStream",  #
                "method": "POST",
                "auth": True
            },
            PUT_LISTENKEY: {
                "path": "/api/v1/userDataStream",  #
                "method": "PUT",
                "auth": True
            },

        },
        MARGIN: {
            EXCHANGE: {
                "path": "/sapi/v1/margin/allPairs",
                "method": "GET",
                "auth": False
            },
            BAR: {
                "path": "/api/v3/klines",
                "method": "GET",
                "auth": False
            },
            TICKER: {
                "path": "/api/v3/ticker/bookTicker",
                "method": "GET",
                "auth": False
            },

            ORDER_BOOK: {
                "path": "/api/v3/depth",
                "method": "GET",
                "auth": False
            },
            TRADE: {
                "path": "/api/v3/trades",
                "method": "GET",
                "auth": False
            },
            BALANCE: {
                "path": "/sapi/v1/margin/account",
                "method": "GET",
                "auth": True
            },
            ORDER: {
                "path": "/sapi/v1/margin/order",
                "method": "POST",
                "auth": True
            },
            CANCEL_ORDER: {
                "path": "/sapi/v1/margin/order",
                "method": "DELETE",
                "auth": True
            },
            CANCEL_ALL_ORDERS: {
                "path": "/sapi/v1/margin/openOrders",
                "method": "DELETE",
                "auth": True
            },
            OPEN_ORDERS: {
                "path": "/sapi/v1/margin/openOrders",
                "method": "GET",
                "auth": True
            },
            ORDER_INFO: {
                "path": "/sapi/v1/margin/order",
                "method": "GET",
                "auth": True
            },
            TRANSFER: {
                "path": "/sapi/v1/margin/transfer",  # 只支持全仓杠杆账户划转
                "method": "POST",
                "auth": True
            },
            LISTENKEY: {
                "path": "/sapi/v1/userDataStream",  #
                "method": "POST",
                "auth": True
            },
            PUT_LISTENKEY: {
                "path": "/sapi/v1/userDataStream",  #
                "method": "PUT",
                "auth": True
            },

        },
        USDT_SWAP: {
            EXCHANGE: {
                "path": "/fapi/v1/exchangeInfo",
                "method": "GET",
                "auth": False
            },
            BAR: {
                "path": "/fapi/v1/klines",
                "method": "GET",
                "auth": False
            },
            TICKER: {
                "path": "/fapi/v1/ticker/bookTicker",
                "method": "GET",
                "auth": False
            },

            ORDER_BOOK: {
                "path": "/fapi/v1/depth",
                "method": "GET",
                "auth": False
            },
            TRADE: {
                "path": "/fapi/v1/trades",
                "method": "GET",
                "auth": False
            },
            BALANCE: {
                "path": "/fapi/v2/account",
                "method": "GET",
                "auth": True
            },
            ORDER: {
                "path": "/fapi/v1/order",
                "method": "POST",
                "auth": True
            },
            CANCEL_ORDER: {
                "path": "/fapi/v1/order",
                "method": "DELETE",
                "auth": True
            },
            CANCEL_ALL_ORDERS: {
                "path": "fapi/v1/allOpenOrders",
                "method": "DELETE",
                "auth": True
            },
            OPEN_ORDERS: {
                "path": "/fapi/v1/openOrder",
                "method": "GET",
                "auth": True
            },
            ORDER_INFO: {
                "path": "/fapi/v1/order",
                "method": "GET",
                "auth": True
            },
            POSITION: {
                "path": "/fapi/v2/account",  #
                "method": "POST",
                "auth": True
            },

            TRANSFER: {
                "path": "/sapi/v1/futures/transfer",  # 只支持全仓杠杆账户划转
                "method": "POST",
                "auth": True
            },
            FUNDING: {
                "path": "/fapi/v1/premiumIndex",  # 当前资金费率
                "method": "GET",
                "auth": False
            },
            FUNDING_HIS: {
                "path": "/fapi/v1/fundingRate",  # 历史资金费率
                "method": "GET",
                "auth": False
            },
            LIQUIDATIONS: {
                "path": "/fapi/v1/forceOrders",  # 爆仓记录
                "method": "GET",
                "auth": False
            },
            LEVERAGE: {
                "path": "/fapi/v1/leverage",  # 调整开仓杠杆率
                "method": "POST",
                "auth": True
            },
            LISTENKEY: {
                "path": "/fapi/v1/listenKey",  #
                "method": "POST",
                "auth": True
            },
            PUT_LISTENKEY: {
                "path": "/fapi/v1/listenKey",  #
                "method": "PUT",
                "auth": True
            },


        },
        SWAP: {
            EXCHANGE: {
                "path": "/dapi/v1/exchangeInfo",
                "method": "GET",
                "auth": False
            },
            BAR: {
                "path": "/dapi/v1/klines",
                "method": "GET",
                "auth": False
            },
            TICKER: {
                "path": "/dapi/v1/ticker/24hr",
                "method": "GET",
                "auth": False
            },

            ORDER_BOOK: {
                "path": "/dapi/v1/depth",
                "method": "GET",
                "auth": False
            },
            TRADE: {
                "path": "/dapi/v1/trades",
                "method": "GET",
                "auth": False
            },
            BALANCE: {
                "path": "/dapi/v1/balance",
                "method": "POST",
                "auth": True
            },
            ORDER: {
                "path": "/dapi/v1/order",
                "method": "POST",
                "auth": True
            },
            CANCEL_ORDER: {
                "path": "/dapi/v1/order",
                "method": "DELETE",
                "auth": True
            },
            CANCEL_ALL_ORDERS: {
                "path": "dapi/v1/allOpenOrders",
                "method": "DELETE",
                "auth": True
            },
            OPEN_ORDERS: {
                "path": "/dapi/v1/openOrder",
                "method": "GET",
                "auth": True
            },
            ORDER_INFO: {
                "path": "/dapi/v1/order",
                "method": "GET",
                "auth": True
            },
            POSITION: {
                "path": "/dapi/v1/account",  # 只支持全仓杠杆账户划转
                "method": "POST",
                "auth": True
            },
            TRANSFER: {
                "path": "/sapi/v1/futures/transfer",  # 只支持全仓杠杆账户划转
                "method": "POST",
                "auth": True
            },
            FUNDING: {
                "path": "/dapi/v1/premiumIndex",  # 当前资金费率
                "method": "GET",
                "auth": False
            },
            FUNDING_HIS: {
                "path": "/dapi/v1/fundingRate",  # 历史资金费率
                "method": "GET",
                "auth": False
            },
            LIQUIDATIONS: {
                "path": "/dapi/v1/forceOrders",  # 历史资金费率
                "method": "GET",
                "auth": False
            },
            LISTENKEY: {
                "path": "/dapi/v1/listenKey",  #
                "method": "POST",
                "auth": True
            },
            PUT_LISTENKEY: {
                "path": "/dapi/v1/listenKey",  #
                "method": "PUT",
                "auth": True
            },

        },
    }
    name = "Binance"

    def __init__(self, api_key=None, api_secret=None, market_type=SPOT):
        super().__init__()
        self.symbols = self.get_exchange()
        self.api_key = api_key
        self.api_secret = api_secret
        self.market_type = market_type
        self.market = Binance_Market(self)
        self.market.start()
        if self.api_key and self.get_listenkey():
            self.trade = Binance_Trade(self)
            self.trade.start()
            self.trade.add_feed({ACCOUNT: self.on_account, ORDER: self.on_order})

    def on_account(self, data):
        """
        接收websocket解析后的数据，
        :param data:
        :return:
        """
        self.assets.update(self.trade.assets)
        self.positions.update(self.trade.positions)
        account=data.get(ACCOUNT,None)
        if len(account)>0:
            e = Event(ACCOUNT, account)
            self.event.put(e)
        position = data.get(POSITION, None)
        if len(account)>0:
            e = Event(POSITION, position)
            self.event.put(e)



    def get_exchange(self):
        return self.fetch(EXCHANGE)


    def exchange_parse(self, data):
        """
        todo 数据重新解析
        """
        if "symbols" in data:
            symbols = data["symbols"]
            for s in symbols:
                symbol = s["symbol"]
                s["market_type"] = self.market_type
                self.symbols[symbol] = s
            return self.symbols

    def sign_request(self, request):
        data = request.params if request.method == "GET" else request.data
        if data:
            msg = "&".join(["=".join([str(k), str(v)]) for k, v in data.items()])
        else:
            msg = ""
        sign = hmac.new(self.api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        if isinstance(data, dict):
            data["signature"] = sign
        else:
            data = {"signature": sign}
        if request.method == "GET":
            request.params = data
        else:
            request.data = data
        header = dict()
        header["X-MBX-APIKEY"] = self.api_key
        request.headers = header
        return request

    def get_balance(self, symbol=None):
        p = {"timestamp": get_cur_timestamp_ms()}
        data = self.fetch(BALANCE, p)
        # print(data)
        self.assets = data
        if symbol:
            return data[symbol]
        else:
            return data

    def parse_balance(self, data):

        "适用于现货"
        if self.market_type==SPOT:
            balances = data["balances"]
            assets = {}
            for b in balances:
                asset = Asset()
                asset.name = b["asset"]
                asset.free = float(b["free"])
                asset.frozen = float(b["locked"])
                asset.balance = asset.free + asset.frozen
                assets[asset.name] = asset
            return assets
        elif self.market_type==MARGIN:
            "适用于全仓杠杆资产"
            balance=data["userAssets"]
            assets = {}
            for b in balance:
                asset = Asset()
                asset.name = b["asset"]
                asset.free = float(b["free"])
                asset.balance = float(b["netAsset"])
                assets[asset.name] = asset
            return assets
        else:
            assets = {}
            balance = data["assets"]
            for b in balance:
                asset = Asset()
                asset.name = b["asset"]
                asset.free = float(b["availableBalance"])
                asset.pnl = float(b["unrealizedProfit"])
                asset.balance = float(b["walletBalance"])
                assets[asset.name] = asset
            return assets

    def create_order(self, order: Order):
        params = {
            "symbol": order.symbol,
            "side": SIDE_MAP[order.side],
            "type": ORDER_TYPE_MAP[order.order_type],
            "quantity": order.qty,
            "timestamp": get_cur_timestamp_ms()
        }
        if order.price:
            params["price"] = order.price
        if order.order_type == LIMIT:
            params["timeInForce"] = "GTC"

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
        返回订单实例后的对象
        """
        if "code" in data:
            code = data["code"]
            msg = data["msg"]
            return STATUS_REJECTED, msg
        else:
            status = STATUS_MAP[data["status"]]
            orderid = data["orderId"]
            return status, orderid

    def get_open_orders(self, symbol):
        p = {"timestamp": get_cur_timestamp_ms()}
        if symbol:
            p["symbol"] = symbol
        return self.fetch(OPEN_ORDERS, p)

    def parse_open_orders(self, data):
        orders = []
        if "code" not in data:
            for l in data:
                order = self.parse_order_info(l)
                orders.append(order)
        return orders


    def cancel_order(self, order):
        p = {"symbol": order.symbol, "orderId": order.order_id, "timestamp": get_cur_timestamp_ms()}
        order = self.fetch(CANCEL_ORDER, p)
        return order

    def parse_cancel_order(self, data):
        return self.parse_order_info(data)

    def cancel_all_orders(self, symbol):
        p = {"symbol": symbol, "timestamp": get_cur_timestamp_ms()}
        return self.fetch(CANCEL_ALL_ORDERS, p)

    def parse_cancel_all_orders(self, data):
        return len(data)

    def update_order(self, order):
        p = {"symbol": order.symbol, "orderId": order.order_id, "timestamp": get_cur_timestamp_ms()}
        return self.fetch(ORDER_INFO, p)

    def parse_order_info(self, data):
        if "code" in data:
            return None
        else:
            o = Order()
            o.order_id = data["orderId"]
            o.symbol = data["symbol"]
            o.qty = data["origQty"]
            o.price = data["price"]
            o.filled_qty = data["executedQty"]
            o.status = STATUS_MAP[data["status"]]
            o.time = data.get("time",get_cur_timestamp())
            o.market_type = self.market_type
            o.side = BUY if data.get("side") == "BUY" else SELL
            return o

    # def transfer(self,):
    def get_bar(self, symbol, interval=INTERVAL_DAY, start_time=None,end_time=None):
        """
        :param symbol:
        :param interval:
        :param start_time:
        :return:
        """
        p = {"symbol": symbol, "interval": INTERVAL_MAP[interval]}
        if start_time:
            p["startTime"] = int(start_time)
        if end_time:
            p["endTime"] = int(end_time)
        return self.fetch(BAR, p)

    def parse_bar(self, data):
        if "code" in data:
            log.error(data)
            return None
        elif len(data):
            df = []
            for i in data:
                item = [(i[0]), float(i[1]), float(i[2]), float(i[3]), float(i[4]), float(i[5]), float(i[7]), int(i[8])]
                df.append(item)
            df = pd.DataFrame(df,columns= ["startTime", "open", "high", "low", "close", "volume", "amount", "trades"])
            df=df.sort_values(by="startTime")
            return df
        else:
            return None

    def get_ticker(self, symbol):
        p = {"symbol": symbol}
        return self.fetch(TICKER, p)

    def parse_ticker(self, data):
        tick = Ticker()
        tick.symbol = data["symbol"]
        tick.ask_price = float(data["askPrice"])
        tick.ask_volume = float(data["askQty"])
        tick.bid_price = float(data["bidPrice"])
        tick.bid_volume = float(data["bidQty"])
        tick.mid_price = (tick.ask_price + tick.bid_price) / 2
        return tick

    def get_order_book(self, symbol):
        p = {"symbol": symbol}
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
        {
            "symbol": "BTCUSDT",  // 交易对
            "initialMargin": "0",   // 当前所需起始保证金(基于最新标记价格)
            "maintMargin": "0", //维持保证金
            "unrealizedProfit": "0.00000000",  // 持仓未实现盈亏
            "positionInitialMargin": "0",  // 持仓所需起始证金(基于最新标记价格)
            "openOrderInitialMargin": "0",  // 当前挂单所需起始保证金(基于最新标记价格)
            "leverage": "100",  // 杠杆倍率
            "isolated": true,  // 是否是逐仓模式
            "entryPrice": "0.00000",  // 持仓成本价
            "maxNotional": "250000",  // 当前杠杆下用户可用的最大名义价值
            "positionSide": "BOTH",  // 持仓方向
            "positionAmt": "0",      // 持仓数量
            "updateTime": 0         // 更新时间
        }
        """
        if "positions" in data:
            poss = data["positions"]
            for p in poss:
                symbol=p["symbol"]
                pos = self.positions.get(symbol,None)
                if pos is None:
                    pos = Position()
                    pos.symbol = symbol
                pos.pnl = float(p["unrealizedProfit"])
                pos.price = float(p["entryPrice"])
                pos.amount = float(p["positionAmt"])
                pos.side = p["positionSide"]
                pos.margin = float(p["positionInitialMargin"])
                pos.leverage = int(p["leverage"])
                if 'BOTH' == pos.side:
                    if pos.amount < 0:
                        pos.side = LONG
                    else:
                        pos.side = SHORT
                elif "LONG" == pos.side:
                    pos.side = LONG
                else:
                    pos.side = SHORT
                    pos.amount = abs(pos.amount)
                self.positions[pos.symbol] = pos
            return self.positions

    def set_leverage(self, symbol, leverage):
        """
        symbol	STRING	YES	交易对
leverage	INT	YES	目标杠杆倍数：1 到 125 整数
recvWindow	LONG	NO
timestamp	LONG	YES
        """
        p = {"symbol": symbol, "leverage": leverage, "timestamp": get_cur_timestamp_ms()}
        new = self.fetch(LEVERAGE, p)
        if new == leverage:
            return True
        else:
            return False

    def parse_leverage(self, data):
        if "leverage" in data:
            return data["leverage"]
        else:
            log.error(data)
            return False

    def get_funding(self, symbol):
        p = {"symbol": symbol}
        return self.fetch(FUNDING, p)

    def get_funding_his(self, symbol,startTime=None,endTime=None):
        p = {"instId": symbol,"limit":1000}
        if startTime:
            p["startTime"]=startTime
        if endTime:
            p["endTime"]=endTime
        return self.fetch(FUNDING_HIS, p)

    def get_listenkey(self):
        return self.fetch(LISTENKEY)

    def parse_listenkey(self, data):
        if "listenKey" in data:
            return data["listenKey"]

    def update_listenkey(self):
        return self.fetch(PUT_LISTENKEY)

    def transfer(self, asset, amount, t):
        """
        不支持逐仓划转
        :param asset:币种
        :param amount:数据
        :param type:MAIN_UMFUTURE 现货钱包转向U本位合约钱包
                    MAIN_CMFUTURE 现货钱包转向币本位合约钱包
                    MAIN_MARGIN 现货钱包转向杠杆全仓钱包
                    UMFUTURE_MAIN U本位合约钱包转向现货钱包
                    UMFUTURE_MARGIN U本位合约钱包转向杠杆全仓钱包
                    CMFUTURE_MAIN 币本位合约钱包转向现货钱包
                    MARGIN_MAIN 杠杆全仓钱包转向现货钱包
                    MARGIN_UMFUTURE 杠杆全仓钱包转向U本位合约钱包
                    MARGIN_CMFUTURE 杠杆全仓钱包转向币本位合约钱包
                    CMFUTURE_MARGIN 币本位合约钱包转向杠杆全仓钱包
                    MAIN_FUNDING 现货钱包转向资金钱包
                    FUNDING_MAIN 资金钱包转向现货钱包
                    FUNDING_UMFUTURE 资金钱包转向U本位合约钱包
                    UMFUTURE_FUNDING U本位合约钱包转向资金钱包
                    MARGIN_FUNDING 杠杆全仓钱包转向资金钱包
                    FUNDING_MARGIN 资金钱包转向杠杆全仓钱包
                    FUNDING_CMFUTURE 资金钱包转向币本位合约钱包
                    CMFUTURE_FUNDING 币本位合约钱包转向资金钱包
        :return:
        """
        p={"type":t,"asset":asset,"amount":amount,"timestamp": get_cur_timestamp_ms()}
        return self.fetch(TRANSFER,p)


class Binance_Market(BaseMarket):
    params = {
        "name": "Binance",
        "is_binary": False,
        "interval": 600  # 心跳间隔
    }
    host = {
        SPOT: "wss://stream.binance.com:9443/ws",  # 现货交易
        MARGIN: "wss://stream.binance.com:9443/ws",  # 杠杆交易
        USDT_SWAP: "wss://fstream.binance.com/ws",  # 永续合约
        SWAP: "wss://dstream.binance.com/ws",  # 币永续
    }
    channels = {
        SPOT: {
            BAR: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@kline_{interval}"],"id":1024}',
                "topic": "kline",
                "auth": False
            },
            TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@ticker"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ALL_TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["!ticker@arr"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ORDER_BOOK: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@depth20@100ms"],"id":1024}',
                "topic": "depthUpdate",
                "auth": False
            }
        },
        MARGIN: {
            BAR: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@kline_{interval}"],"id":1024}',
                "topic": "kline",
                "auth": False
            },
            TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@ticker"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ALL_TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["!ticker@arr"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ORDER_BOOK: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@depth20@100ms"],"id":1024}',
                "topic": "depthUpdate",
                "auth": False
            },
            LIQUIDATIONS: {
                "sub": '{"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1024}',
                "topic": "forceOrder",
                "auth": False
            }
        },
        USDT_SWAP: {
            BAR: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@kline_{interval}"],"id":1024}',
                "topic": "kline",
                "auth": False
            },
            TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@ticker"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ALL_TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["!ticker@arr"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ORDER_BOOK: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@depth@100ms"],"id":1024}',
                "topic": "depthUpdate",
                "auth": False
            },
            LIQUIDATIONS:{
                "sub": '{"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1024}',
                "topic": "forceOrder",
                "auth": False
            }
        },
        SWAP: {
            BAR: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@kline_{interval}"],"id":1024}',
                "topic": "kline",
                "auth": False
            },
            TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@ticker"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ALL_TICKER: {
                "sub": '{"method":"SUBSCRIBE","params":["!ticker@arr"],"id":1024}',
                "topic": "24hrTicker",
                "auth": False
            },
            ORDER_BOOK: {
                "sub": '{"method":"SUBSCRIBE","params":["{symbol}@depth20@100ms"],"id":1024}',
                "topic": "depthUpdate",
                "auth": False
            },
            LIQUIDATIONS:{
                "sub": '{"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1024}',
                "topic": "forceOrder",
                "auth": False
            }
        }
    }

    def add_feed(self, channels, **kwargs):
        """
        单独的订阅方法，可以在初始化完成后调用
        """
        if "symbol" in kwargs.keys():
            kwargs["symbol"]=kwargs["symbol"].lower()
        subscribes = self.get_subscribes(channels, kwargs)
        # log.debug(subscribes)
        for k, v in channels.items():
            if k == ALL_TICKER:     #不同的订阅使用相同的处理流程
                K = TICKER
            self.callbacks[k] = v
        for i in subscribes:
            if i not in self.subscribes:
                self.subscribes.append(i)
            if self.connected:
                # 已经连接上ws，则直接发送订阅消息，否则等conned_callback统一发送
                self._loop.create_task(self.send(i))

    async def callback(self, data):
        """
        被动处理服务的ping请求
        :param data:
        :return:
        """
        if "ping" in str(data):
            await self.ping()

    def parse_bar(self, data):
        try:
            b = Bar()
            b.broker = self.name
            data = data["k"]
            b.symbol = data["s"]
            b.startTime = data["t"]
            b.open = data["o"]
            b.high = data["h"]
            b.low = data["l"]
            b.close = data["c"]
            b.volume = data["v"]
            b.amount = data["q"]
            b.trades = data["n"]
            b.datetime=data["T"]
            return b
        except:
            log.error(traceback.print_exc())

    def parse_order_book(self,data):
        try:
            self.heartbeat_time = get_cur_timestamp()
            symbol = data["s"]
            if data:
                ob = self.order_books.get(symbol)
                if ob is None:
                    ob = Order_book()
                    ob.symbol = symbol
                ob.update_time = float(data["T"])
                asks = data["a"]#卖方深度
                bids = data["b"]#买方深度
                ob.update(bids, asks)
                return ob

        except:
            log.error(traceback.print_exc())

    def parse_ticker(self,data):
        """
        :param data:
        :return:
        """
        try:
            self.heartbeat_time = get_cur_timestamp()
            ticker = Ticker()
            ticker.symbol = data["s"]
            ticker.amount = float(data["Q"])
            ticker.open = float(data["o"])
            ticker.close = float(data["c"])
            ticker.high = float(data["h"])
            ticker.low = float(data["l"])
            ticker.volume = float(data["v"])
            ticker.price = float(data["c"])
            ticker.time = data["E"]
            return ticker
        except:
            log.error(traceback.print_exc())

    def parse_liquidations(self,data):
        try:
            self.heartbeat_time = get_cur_timestamp()
            return data["o"]
        except:
            log.error(traceback.print_exc())


class Binance_Trade(Binance_Market):
    """
    todo 完成spot ,margen,swap的api定认
    """
    channels = {
        SPOT: {
            ACCOUNT: {
                "topic": "ACCOUNT_UPDATE"
            },
            ORDER: {
                "topic": "ORDER_TRADE_UPDATE"
            }
        },
        MARGIN: {
            ACCOUNT: {
                "topic": "ACCOUNT_UPDATE"
            },
            ORDER: {
                "topic": "ORDER_TRADE_UPDATE"
            }
        },
        USDT_SWAP: {
            ACCOUNT: {
                "topic": "ACCOUNT_UPDATE"
            },
            ORDER: {
                "topic": "ORDER_TRADE_UPDATE"
            }
        },
        SWAP: {
            ACCOUNT: {
                "topic": "ACCOUNT_UPDATE"
            },
            ORDER: {
                "topic": "ORDER_TRADE_UPDATE"
            }
        }
    }
    listenkey_time = 0
    def get_url(self):
        """
        获取listenkey
        """
        listenKey = self.broker.get_listenkey()
        self.listenkey_time=get_cur_timestamp()
        url = super().get_url()
        return url + "/" + listenKey

    async def ping(self):

        if self.listenkey_time+60*60<get_cur_timestamp():
            self.broker.update_listenkey()
            self.listenkey_time=get_cur_timestamp()


    def parse_order(self,data):
        """
        todo 合约的已经测试完毕，还需要添加现货的
        """
        if "ORDER_TRADE_UPDATE" in str(data):
            data=data["o"]
            o = Order()
            o.order_id = data["i"]
            o.symbol = data["s"]
            o.qty = data["q"]
            o.price = data["p"]
            o.filled_qty = data["z"]
            o.status = STATUS_MAP[data["X"]]
            side = data["S"]
            o.time = data["T"]
            o.market_type = self.market_type
            if side == "BUY":
                o.side = OPEN_BUY
            else:
                o.side = OPEN_SELL
            return o
        else:
            return ""

    def parse_account(self,data):
        """
        todo 合约的已经测试完毕，还需要添加现货的
        """
        if "ACCOUNT_UPDATE" in str(data):
            data=data["a"]
            bss=data["B"]
            assets = {}
            for b in bss:
                asset= Asset()
                asset.name = b["a"]
                asset.balance =float(b["wb"])
                asset.free=float(b["cw"])-float(b["bc"])
                asset.frozen =asset.balance- asset.free
                assets[asset.name]=asset
            self.assets.update(assets)

            poss=data["P"]
            ps={}
            for p in poss:
                pos = Position()
                pos.symbol = p["s"]
                pos.pnl = float(p["up"])
                pos.price = float(p["ep"])
                pos.amount = float(p["pa"])
                pos.side = p["ps"]
                if 'BOTH' == pos.side:
                    if pos.amount < 0:
                        pos.side = LONG
                    else:
                        pos.side = SHORT
                elif "LONG" == pos.side:
                    pos.side = LONG
                else:
                    pos.side = SHORT
                    pos.amount = abs(pos.amount)
                ps[pos.symbol]=pos
            self.positions.update(ps)
            result={ACCOUNT:assets , POSITION:ps}
            return result

