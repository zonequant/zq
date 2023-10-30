#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/23 13:06
# @Author  : Dominolu
# @File    : bybit.py
# @Software: PyCharm
import hashlib
import hmac
import json
import time
import traceback

from zq.common.const import *
from zq.engine.baseBroke import BaseBroker
import pandas as pd

INTERVAL_MAP = {

    INTERVAL_MIN1: "1",
    INTERVAL_MIN5: "5",
    INTERVAL_MIN15: "15",
    INTERVAL_MIN30: "30",
    INTERVAL_HOUR1: "60",
    INTERVAL_HOUR2: "120",
    INTERVAL_HOUR4: "240",
    INTERVAL_HOUR8: "480",
    INTERVAL_HOUR12: "720",
    INTERVAL_DAY: "D",
    INTERVAL_WEEK: "W",
    INTERVAL_MONTH: "M"

}
SUBDEPOSIT="SUBDEPOSIT"

class Bybit(BaseBroker):
    " api文档 https://bybit-exchange.github.io/docs/zh-TW/v5/intro"
    name = "Bybit"
    api = {
        BAR: {
            "path": "/v5/market/kline",  # 调整开仓杠杆率
            "method": "GET",
            "auth": False
        },
        DEPOSIT: {
            "path": "/v5/asset/deposit/query-address",  # 调整开仓杠杆率
            "method": "GET",
            "auth": True
        },
        SUBDEPOSIT: {
            "path": "/v5/asset/deposit/query-sub-member-address",  # 调整开仓杠杆率
            "method": "GET",
            "auth": True
        },

    }
    host = "https://api.bybit.com"
    recv_window = 5000

    def sign_request(self, request, sign=True):
        timestamp = int(time.time() * 1000)
        data = request.params if request.method == "GET" else request.data
        if request.method == "GET":
            # payload = "&".join(["=".join([str(k), str(v)]) for k, v in sorted(data.items())])
            payload = "&".join([str(k) + "=" + str(v) for k, v in data.items() if v is not None])
        else:
            string_params = [
                "qty",
                "price",
                "triggerPrice",
                "takeProfit",
                "stopLoss",
            ]
            integer_params = ["positionIdx"]
            for key, value in data.items():
                if key in string_params:
                    if type(value) != str:
                        data[key] = str(value)
                elif key in integer_params:
                    if type(value) != int:
                        data[key] = int(value)
            payload = json.dumps(data)

        param_str = str(timestamp) + self.api_key + str(self.recv_window) + payload
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers = {"X-BAPI-API-KEY": self.api_key,
                   "X-BAPI-SIGN": signature,
                   "X-BAPI-TIMESTAMP": str(timestamp),
                   "X-BAPI-RECV-WINDOW": str(self.recv_window),
                   "X-BAPI-SIGN-TYPE": '2'
                   }
        request.headers = headers
        return request

    def get_url(self):
        "统一账户的交易，不需要分产品类型区分url"
        return self.host

    def get_api(self):
        "统一账户的交易，不需要分产品类型区分api"
        return self.api

    def get_bar(self, symbol, interval=INTERVAL_DAY, start_time=None, end_time=None):
        p = {"symbol": symbol, 'category': self.market_type.lower(), "interval": INTERVAL_MAP[interval]}
        if start_time:
            p["start"] = int(start_time)
        if end_time:
            p["end"] = int(end_time)
        return self.fetch(BAR, p)

    def parse_bar(self, data):
        retCode = data.get("retCode", False)
        if retCode == 0:
            df = []
            ls = data["result"]['list']
            for i in ls:
                df.append({"startTime": float(i[0]),
                           "open": float(i[1]),
                           "high": float(i[2]),
                           "low": float(i[3]),
                           "close": float(i[4]),
                           "volume": float(i[5]),
                           'amount': float(i[6]),
                           "trades": 0
                           })
            df = pd.DataFrame(df)
            df.columns = ['startTime', 'open', 'high', 'low', 'close', 'volume', "amount", "trades"]
            df = df.sort_values(by="startTime")
            return df
        else:
            return []

    def sub_order_book(self,symbol,callback):
        ob=self.get_order_book(symbol)
        self.market.order_books[symbol]=ob
        self.market.add_feed({ORDER_BOOK: callback},symbol=symbol)
    def get_deposit(self, chain, coin):
        p = {"coin": coin, "chainType": chain}
        return self.fetch(DEPOSIT, p)

    def get_subdeposit(self, chain, coin,subid):
        p = {"coin": coin, "chainType": chain,"subMemberId":subid}
        return self.fetch(SUBDEPOSIT, p)

    def parse_deposit(self, data):
        retCode = data.get("retCode", 100)
        if retCode == 0:
            try:
                result=data["result"]["chains"]
                address=result[0]["addressDeposit"]
                return address
            except:
                traceback.print_exc()


    def parse_subdeposit(self, data):
        retCode = data.get("retCode", 100)
        if retCode == 0:
            try:
                result = data["result"]["chains"]
                address = result["addressDeposit"]
                return address
            except:
                traceback.print_exc()