#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/2/23 20:05
# @Author  : Dominolu
# @File    : function.py
# @Software: PyCharm

def cumulative_return(df):
    df["pos"].fillna(method='ffill', inplace=True)
    # 计算持仓收益
    df["position_return"] = df["pos"].shift(1) * (df["close"] / df["close"].shift(1) - 1)
    # 计算现金收益
    df["cash_return"] = df["close"] / df["close"].shift(1) - 1
    # 计算总收益
    df["total_return"] = df["position_return"] + (1 - abs( df["pos"].shift(1))) * df["cash_return"]
    # 计算累计收益
    df["cumulative_return"] = (1 + df["total_return"]).cumprod() - 1
    return df
