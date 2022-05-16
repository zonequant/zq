# -*- coding:utf-8 -*-
"""
@Time : 2020/4/5 10:43 上午
@Author : Domionlu
@Site : 
@File : analysis.py
@Software: PyCharm
"""

import empyrical
import pandas as pd
import numpy as np

""""
param:
result:日收益率
benchmark：基准收益率
trades:成交记录

1、盈亏比 交易对
2、胜率  交易对
3、年化收益率 empyrical
4、累计收益率 empyrical
5、最大回撤 empyrical
6、夏普比 empyrical
7、alpha
8、beta
"""
# 统计策略指标



def pls_ws(trades):
    """
    盈亏比，胜率
    :param trades:
    [0]:time
    [1]:side "BUY" or "SELL"
    [2]:order price
    [3]:volume
    :return:
    pls:盈亏比
    wr:胜比
    最佳回报 pls*wr>1
    """
    trade = []
    for i in trades:
        time = i[0]
        side = i[1]
        price = i[2]
        volume = i[3]
        if side == "Buy":
            trade.append([time, price, 0, 0, 0])
        if side == "Sell" and len(trade) > 0:
            trade[-1][2] = price
            trade[-1][3] = price - trade[-1][1]
            trade[-1][4] = (price - trade[-1][1]) / trade[-1][1]
    result = pd.DataFrame(trade, columns=["time", "open", "close", "pnl", "res"])
    apls = result[result["pnl"] > 0]["pnl"]
    bpls = result[result["pnl"] < 0]["pnl"]
    # 胜率 =盈利次数/总成交次数
    wr = apls.count() / len(trades)
    # 盈亏比 = 平均盈利 / 平均亏损 = (盈利总金额 / 盈利次数) / (亏损总金额 / 亏损次数)
    pls = abs(apls.sum() / apls.count() / (bpls.sum() / bpls.count()))
    return pls, wr
    pass



def pnl_res(data):
    """"
    计算日收益率=(当日收益-前日收益)/前日收益
    :param data:
    [0]:time
    [1]:pnl
    """
    result=[]
    for i in data:
        time=i[0]
        p=i[1]
        if len(result) == 0:
            result.append([time, p, 0.00])
        else:
            pdaily=result[-1][0].strftime("%Y-%m-%d")
            day=time.strftime("%Y-%m-%d")
            if day!=pdaily:
                ppnl=result[-1][1]
                returns = (p - ppnl) / ppnl
                result.append([time,p,returns])
    result=pd.DataFrame(result)
    return result[2].values


def Analysis(results):
    """
    技术指标分析器
    :param results:
    {
    'returns':[0.1,0.1,0.1],
    'benchmark':[0.1,0.1,0.1]
    'trades':[[2020.01.01 01:00:00,'BUY',6234.10,1]]
    }
    :return:
    """
    res=pnl_res(results["returns"])
    bres=pnl_res(results["benchmark"])
    return_ratio = empyrical.cum_returns_final(res)
    annual_return_ratio = empyrical.annual_return(res)
    sharp_ratio = empyrical.sharpe_ratio(res, 0.035 / 252)
    return_volatility = empyrical.annual_volatility(res)
    max_drawdown = empyrical.max_drawdown(res)
    alpha, beta = empyrical.alpha_beta_aligned(res, bres)
    pls,wr=pls_ws(results["trades"])
    return  {
        'pls':pls,
        'wr':wr,
        'return_ratio': return_ratio,
        'annual_return_ratio': annual_return_ratio,
        'beta': beta,
        'alpha': alpha,
        'sharp_ratio': sharp_ratio,
        'return_volatility': return_volatility,
        'max_drawdown': max_drawdown,
    }

if __name__ == "__main__":
    pass