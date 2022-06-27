# -*- coding:utf-8 -*-
"""
@Time : 2021/12/30 13:51
@Author : domionlu@zquant.io
@File : test
"""
# -*- coding:utf-8 -*-
# from zq.backtest.backengine import Broker
import pandas as pd
import requests
from zq.common.tools import *
import time


url="https://api.binance.com/api/v3/klines"


def download(starttime=1577808000000):
    param = {"symbol": "BTCUSDT", "interval": "1m", "startTime": starttime, "limit": 1000}
    req = requests.get(url, param)
    data=req.json()
    return data

@time_cost
def main():
    starttime = 1577808000000
    datas=[]
    while True:
        dt=download(starttime)
        size = len(dt)
        datas=datas+dt
        print(f"down {ts_to_datetime_str(starttime)},count{size}.")
        if len(dt) == 1000:
            starttime = dt[-1][0]+1
            time.sleep(0.1)
        else:
            break
    return datas

data=main()
dt=pd.DataFrame(data,columns=["datetime","open","high","low","close","voluem","closetime","amount","trades","buy","sell","1"])
dt.to_csv("btcusdt.csv")