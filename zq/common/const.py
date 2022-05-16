# -*- coding:utf-8 -*-
"""
@Time : 2021/5/12 12:57
@Author : domionlu@zquant.io
@File : const
"""


# -*- coding:utf-8 -*-
# class const:
#     class ConstError(TypeError): pass
#
#     def __setattr__(self, key, value):
#         if key in self.__dict__:
#             data = "Can't rebind const (%s)" % key
#             raise self.ConstError(data)
#         self.__dict__[key] = value
#
#
# import sys

# sys.modules[__name__] = const()

# 交易对类型 market_type
SPOT = "SPOT" #币币
MARGIN = "MARGIN" #杠杆
FUTURES = "FUTURES"  #交割
USDT_SWAP = "USDT_SWAP" #U永续
SWAP = "SWAP" #币永续
OPTION = "OPTION" #期权
TRANSFER="TRANSFER" #账户资产划转

# 开单方向
BUY = "BUY"
SELL = "SELL"
OPEN_BUY = "OPEN_BUY"
OPEN_SELL = "OPEN_SELL"
CLOSE_BUY = "CLOSE_BUY"
CLOSE_SELL = "CLOSE_SELL"

# 持仓方向
LONG = "LONG"
SHORT = "SHORT"
BOTH = "BOTH"

DEFAULT="DEFAULT"

# 接口业务
TICKER = "TICKER"
ALL_TICKER="ALL_TICKER"
ORDER_BOOK = "ORDER_BOOK"
ORDER = "ORDER"
ORDER_INFO = "ORDER_INFO"
TRADE = "TRADE"
BAR = "BAR"
POSITION = "POSITION"
BALANCE = "BALANCE"
FORCE_ORDER = "FORCE_ORDER"
ACCOUNT = "ACCOUNT"
FUNDING = "FUNDING"
FUNDING_HIS="FUNDING_HIS"
LIQUIDATIONS = "LIQUIDATIONS"
INTEREST = "INTEREST"
EXCHANGE="EXCHANGE"
ALERT="ALERT"
TEST="TEST"
LEVERAGE="LEVERAGE"

CANCEL_ORDER = "CANCEL_ORDER"
CANCEL_ALL_ORDERS = "CANCEL_ALL_ORDERS"
OPEN_ORDERS = "OPEN_ORDERS"
# 持仓类型
ISOLATED = "ISOLATED"
CROSS = "CROSS"
CASH = "CASH"

# 订单种类 (orderTypes, type):
LIMIT = "LIMIT"  # 限价单
MARKET = "MARKET"  # 市价单
STOP = "STOP"  # 止损限价单
STOP_MARKET = "STOP_MARKET"  # 止损市价单
TAKE_PROFIT = "TAKE_PROFIT"  # 止盈限价单
TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"  # 止盈市价单
TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET"  # 跟踪止损单

REDUCE_ONLY = "REDUCE_ONLY"
POST_ONLY = "POST_ONLY"

# 有效方式 (timeInForce):
GTC = "GTC"  # Good Till Cancel 成交为止
IOC = "IOC"  # - Immediate or Cancel 无法立即成交(吃单)的部分就撤销
FOK = "FOK"  # Fill or Kill 无法全部立即成交就撤销
GTX = "GTX"  # - Good Till Crossing 无法成为挂单方就撤销

# K线周期
INTERVAL_S1 = "1s"
INTERVAL_S5 = "5s"
INTERVAL_S15 = "15s"
INTERVAL_TICKER = "T"
INTERVAL_MIN30 = "30m"
INTERVAL_MIN15 = "15m"
INTERVAL_MIN5 = "5m"
INTERVAL_MIN1 = "1m"
INTERVAL_HOUR1 = "1h"
INTERVAL_HOUR2 = "2h"
INTERVAL_HOUR4 = "4h"
INTERVAL_HOUR8 = "8h"
INTERVAL_HOUR12 = "12h"
INTERVAL_DAY = "1d"
INTERVAL_WEEK = "1w"
INTERVAL_MONTH = "month"
INTERVAL_YEAR = "1y"

# 消息类型
INFO = "消息"
WARING = "警告"
DEBUG = "调试"
ERROR = "异常"

# 订单状态 (status):
STATUS_NEW = "NEW"
STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"
STATUS_FILLED = "FILLED"
STATUS_CANCELED = "CANCELED"
STATUS_REJECTED = "REJECTED"
STATUS_EXPIRED = "EXPIRED"



