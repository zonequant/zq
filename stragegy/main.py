#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/2/17 18:48
# @Author  : Dominolu
# @File    : main.py
# @Software: PyCharm
from zq.engine.botEngine import BotEngine
from stragegy.balance import Rebalancing
from zq.broker.binance import Binance
from zq.config import settings
from zq.common.tools import *

if __name__ == '__main__':
    bot = BotEngine()
    param=read_json("config.json")
    bot.add_strategy(Rebalancing, param)
    bn = Binance(api_key=settings.API_KEY,api_secret=settings.API_SECRET)
    bot.add_broker(bn)
    bot.run()


