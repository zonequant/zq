#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/23 14:00
# @Author  : Dominolu
# @File    : bybittest.py
# @Software: PyCharm
import hashlib
import hmac
import time

import requests

from zq.broker.bybit import Bybit

api_key = "2UkDPOF51mBnAMteyQ"
secret_key = "Z9vK7IQ0n13ZgLii6JuMT9ybgFJ6G6orEw4f"
recv_window=str(5000)

httpClient=requests.Session()
url="https://api.bybit.com" # Testnet endpoint

def bar_test():
    bybit = Bybit()
    data = bybit.get_bar("BTCUSDT", interval="1m")
    print(data)

def deposit_test():
    bybit = Bybit(api_key,secret_key)
    data = bybit.get_deposit("ETH","ETH")
    print(data)

def subdeposit_test(id):
    bybit = Bybit(api_key,secret_key)
    data = bybit.get_subdeposit("ETH","ETH",id)
    print(data)

#
# def HTTP_Request(endPoint,method,payload,Info):
#     global time_stamp
#     time_stamp=str(int(time.time() * 10 ** 3))
#     signature=genSignature(payload)
#     headers = {
#         'X-BAPI-API-KEY': api_key,
#         'X-BAPI-SIGN': signature,
#         'X-BAPI-SIGN-TYPE': '2',
#         'X-BAPI-TIMESTAMP': time_stamp,
#         'X-BAPI-RECV-WINDOW': recv_window,
#         'Content-Type': 'application/json'
#     }
#     if(method=="POST"):
#         response = httpClient.request(method, url+endPoint, headers=headers, data=payload)
#     else:
#         response = httpClient.request(method, url+endPoint+"?"+payload, headers=headers)
#
#     print(response.text)
#     print(Info + " Elapsed Time : " + str(response.elapsed))
#
# def genSignature(payload):
#     param_str= str(time_stamp) + api_key + recv_window + payload
#     hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
#     signature = hash.hexdigest()
#     return signature



endpoint="/v5/asset/deposit/query-address"
method="GET"
params="coin=ETH&chainType=ETH"
# data=HTTP_Request(endpoint,method,params,"Get Deposit Address")

sublist=[67204384,67210898,67346745,67346760,67346774,67346813,67346831,67347258,67347278,67347296,67347315,67347321,67347327,67347354,67347378,67347411,67347425,67347439,67347446,67347453]
for i in sublist:
    subdeposit_test(i)
    time.sleep(5)
