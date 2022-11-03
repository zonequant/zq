# -*- coding:utf-8 -*-
"""
@Time : 2022/5/20 16:08
@Author : Domionlu@gmail.com
@File : doublema
"""
from zq.engine.baseStrategy import BaseStrategy
from zq.indicator.common import *
from zq.backtest.backengine import BackEngine,BackBroker
import pandas as pd

class Doublema(BaseStrategy):
    params = {
        "fast": 30,
        "slow":60
    }

    def init(self):
        close = self.data.close
        self.sma1 = Ema(close, self.p.fast)
        self.sma2 = Ema(close, self.p.slow)

    def next(self):
        # 如果此时快线刚好越过慢线，买入全部
        if crossover(self.sma1, self.sma2):
            self.buy()

        # 如果是慢线刚好越过快线，卖出全部
        elif crossunder(self.sma1, self.sma2):
            self.sell()

        # 否则，这个时刻不执行任何操作。
        else:
            pass
def backtest():
    btc = pd.read_csv("btc.csv", parse_dates=True, infer_datetime_format=True)
    btc = btc[0:10000]
    bt = BackEngine(data=btc, strategy=Doublema, broker=BackBroker, cash=1000000.0, commission=0.003,out=True)
    bt.run()
    result = bt.result()
    print(result.tail())
    # pf.create_returns_tear_sheet(result["return"])

if __name__ == '__main__':
    backtest()
