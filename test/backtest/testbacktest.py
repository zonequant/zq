#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/7 20:43
# @Author  : Dominolu
# @File    : testbacktest.py
# @Software: PyCharm

from zq.backtest.backtest import backtest_factor
import pandas as pd
from zq.backtest.futurebroker import Futurebroker
from zq.backtest.strategy import Strategy
data = pd.read_csv("btc_liq.csv")







dt = backtest_factor(data, Futurebroker, One, ["BUY", "SELL"])
