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

if __name__ == '__main__':
    bot = BotEngine()
    param = {"assets": {"asset": ["BTC", "ETH"], "weights": [0.5, 0.5]}, "baseasset": "USDT","spread":0.02}
    bot.add_strategy(Rebalancing, param)
    bn=Binance(api_key="QDxTJVdUACC1PpLaR2AdUIEKLh1tT0LofLrPWiGXrVHvtbz5EMSl0j28QNv6RDRY",api_secret="psh5oR8IW1JR57B6eZbXgOu4B8oZKBDqyujR4VzzS3sh03hYM5wpwYBDRZycFBGM")
    bot.add_broker(bn)
    bot.run()
