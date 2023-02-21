#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/10/11 15:54
# @Author  : Dominolu
# @File    : backtest.py
# @Software: PyCharm

import numpy as np
import pandas as pd
from .backengine import BackBroker
from loguru import logger as log



def run(data, factor, strategy, broker):
    size = int(data.shape[0])
    factor=strategy.factors(data)
    broker.strategy=strategy
    for i in range(size):
        strategy.data = data[:i+1]
        broker.data=data[:i+1]
        broker.match() #对上一根bar生成的订单进行虚拟撮合
        if i<size:
            strategy.next() #最后一根bar不能下单，需要全部平仓
        else:
            broker.close()  #结束撮合，全部平仓
    return broker.equitys,broker.returns,broker.fees

def analyzers(dt):
    """
    回测结果分析
    :param dt:
    :return:
    """
    start_date = dt.index[0]
    end_date = dt.index[-1]

    values = dt["values"]
    capital = values[0]
    end_balance = values[-1]
    rt = dt["return"]
    pnl = dt["pnl"]
    commission = dt["commission"]
    # sharpe = np.sqrt(self._annual_factor) * values.mean() / values.std()
    ret = end_balance / capital - 1
    # annual_return = pow(1 + ret, self._annual_factor / len(rt)) - 1
    max_drawdown = ((values.cummax() - values) / values.cummax()).max()
    total_net_pnl = end_balance - capital
    total_commission = (commission).sum()
    profit_return = len(rt[rt > 0.0])
    zeno = len(rt[rt == 0.0])
    loss_return = len(rt[rt < 0.0])
    win_rate = profit_return / (profit_return + loss_return)
    if profit_return == 0:
        avg_profit = 0
    else:
        avg_profit = pnl[pnl > 0].sum() / profit_return
    if loss_return == 0:
        avg_loss = 0
        pl_radio = 1
    else:
        avg_loss = pnl[pnl < 0].sum() / loss_return
        pl_radio = avg_profit / abs(avg_loss)
    returns = {
        "start_date": start_date,
        "end_date": end_date,
        "capital": capital,
        "end_balance": end_balance,
        "return": ret,
        # "sharpe": sharpe,
        # "annual_return": annual_return,
        "max_drawdown": max_drawdown,
        "total_net_pnl": total_net_pnl,
        "total_commission": total_commission,
        "profit_return": profit_return,
        "loss_return": loss_return,
        "win_rate": win_rate,
        "avg_profit": avg_profit,
        "avg_loss": avg_loss,
        "pl_radio": pl_radio
    }
    return returns


def backtest_factor(df: pd.DataFrame, broker, stratgry, factors: list):
    data = df[['date','open', 'high', 'low', 'close', 'volume']].to_numpy()
    factor = df[factors].to_numpy()
    results = run(data, factor, stratgry(), broker())
    # results = analyzers(results)
    return results


