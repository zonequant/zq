import talib
import numpy as np
# import statsmodels.formula.api as sml
from zq.common.tools import *


def Ema(data,period=21):
    return talib.EMA(data,period)

def Atr(high,low,close,timeperiod=30):
    return talib.ATR(high,low,close,timeperiod=timeperiod)


def StochRSI(close,smoothK,smoothD,lengthRSI,lengthStoch):

    RSI = talib.RSI(close, timeperiod=lengthRSI)
    LLV = RSI.rolling(window=lengthStoch).min()
    HHV = RSI.rolling(window=lengthStoch).max()
    stochRSI = (RSI - LLV) / (HHV - LLV) * 100
    fastk = talib.MA(np.array(stochRSI), smoothK)
    fastd = talib.MA(np.array(fastk),smoothD)
    return fastk, fastd


# def sm_ols(data,N):
#     def ols(d):
#         model=sml.ols(formula="",data=d).fit()
#         return model[1]
#     beta = data.rolling(N).apply(ols, raw=True)
#     return beta


def sigmoid(x):  #sigmoid函数
     return 1/(1+np.exp(-x))



def crossover(series1, series2) -> bool:
    """
    检查两个序列是否在结尾交叉
    :param series1:  序列1
    :param series2:  序列2
    :return:         如果交叉返回True，反之False
    """
    return series1[-2] < series2[-2] and series1[-1] > series2[-1]

def crossunder(series1, series2) -> bool:
    """
    检查两个序列是否在结尾交叉
    :param series1:  序列1
    :param series2:  序列2
    :return:         如果交叉返回True，反之False
    """
    return series1[-2] > series2[-2] and series1[-1] < series2[-1]