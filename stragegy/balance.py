#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/2/16 17:11
# @Author  : Dominolu
# @File    : balance.py
# @Software: PyCharm
import time
import traceback

import pandas as pd
from zq.engine.baseStrategy import BaseStrategy
from loguru import logger as log
from zq.common.const import *
from zq.common.tools import *

class Rebalancing(BaseStrategy):
    portfolio = None
    assets = None
    symbols = None
    baseasset_value = 0

    def next(self):
        pass

    def init(self):
        self.portfolio = pd.DataFrame(self.params["assets"])
        self.assets = list(self.params["assets"]["asset"])
        self.symbols = {(i + self.p.baseasset): i for i in self.assets}
        self.portfolio["price"] = 0
        self.portfolio["balance"] = 0
        amount = self.get_amount()

        log.info(f"当前总市值: {round(amount,4)}")
        for k, v in self.symbols.items():
            self._broker.market.add_feed({TICKER: self.on_ticker}, symbol=k)
        self.status=True

    def on_ticker(self, tick):
        asset = self.symbols[tick.symbol]
        self.portfolio.loc[self.portfolio["asset"] == asset, ['price']] = tick.close
        self.rebalance()

    def on_account(self, data):
        for k,v in data.items():
            if k==self.p.baseasset:
                self.baseasset_value=v.free
            else:
                if k in self.assets:
                    balance = v.balance
                    self.portfolio.loc[self.portfolio["asset"] == k, ['balance']] = balance

    def target_to(self, symbol, volume,price):
        if self.status:
            self.status=False
            try:
                if volume > 0:
                    volume=volume*0.996
                    order = self.buy(symbol, volume,price)
                    if order.status==STATUS_FILLED:
                        log.info(f"买入 {symbol}:{volume}--{order.status}")
                    elif order.status in (STATUS_NEW,STATUS_PARTIALLY_FILLED):
                        time.sleep(0.1)
                        order=self._broker.cancel_order(order)
                        if order:
                            log.info(f"买入订单 {symbol}:{volume}--{order.status}")
                        else:
                            log.info(f"买入 {symbol}:{volume}--{STATUS_FILLED}")

                else:
                    order = self.sell(symbol, abs(volume))
                    if order.status == STATUS_FILLED:
                        log.info(f"卖出 {symbol}:{volume}--{order.status}")
                    else:
                        log.warning(f"卖出 {symbol}:{volume}-{order.err_msg}")
                amount = self.get_amount()
                log.info(f"当前总市值: {round(amount,2)}")
            except:
                log.error(traceback.format_exc())
            self.status=True

    def rebalance(self):
        try:
            self.portfolio["amount"] = self.portfolio["price"] * self.portfolio["balance"]
            amount = self.portfolio["amount"].sum() + self.baseasset_value
            self.portfolio["target"] = amount * self.portfolio["weights"]
            self.portfolio["delta"] = (self.portfolio["target"] - self.portfolio["amount"]) / self.portfolio["price"]
            self.portfolio = self.portfolio.sort_values(by="delta")
            for index, row in self.portfolio.iterrows():
                if row["target"] > 0 and abs((row["target"] - row["amount"]) / row["target"]) > self.p.spread:
                    self.target_to(row["asset"] + self.p.baseasset, row["delta"],row["price"])
            # print_end(f"当前总市值: {round(amount,2)}")
        except:
            log.error(traceback.format_exc())

    def get_amount(self):
        try:
            account = self.get_balance()
            for i in self.assets:
                symbol = i + self.p.baseasset
                tick = self.get_ticker(symbol)
                price = tick.close
                balance = account[i].balance
                self.portfolio.loc[self.portfolio["asset"] == i, ['price', 'balance']] = price, balance
            self.baseasset_value = account[self.p.baseasset].balance
            self.portfolio["amount"] = self.portfolio["price"] * self.portfolio["balance"]
            return self.portfolio["amount"].sum() + self.baseasset_value
        except:
            log.error(traceback.format_exc())
