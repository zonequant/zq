# -*- coding:utf-8 -*-
"""
@Time : 2020/4/4 1:27 下午
@Author : Domionlu
@Site : 
@File : base.py
@Software: PyCharm
"""
import numpy as np
import statsmodels.formula.api as sml
import pandas as pd
import talib

def StochRSI(close,smoothK,smoothD,lengthRSI,lengthStoch):

    RSI = talib.RSI(close, timeperiod=lengthRSI)
    LLV = RSI.rolling(window=lengthStoch).min()
    HHV = RSI.rolling(window=lengthStoch).max()
    stochRSI = (RSI - LLV) / (HHV - LLV) * 100
    fastk = talib.MA(np.array(stochRSI), smoothK)
    fastd = talib.MA(np.array(fastk),smoothD)
    return fastk, fastd




if __name__ == "__main__":
    feed = pd.read_csv("binance_BTCUSDT_1d.csv")
    close=feed['close']
    # beta=polyslope(close,10)
    # print(beta)
    # # beta=ols(close,10)

    pass