#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/5/25 15:11
# @Author  : Dominolu
# @File    : okxtest.py
# @Software: PyCharm
from zq.broker.okex import Okex


api_key = "5b194f2d-1442-4384-baef-c759d9a1bcc8"
api_secret = "5F36038C1D2883BB6A1B4D0E80D58BF6"
passphrase = "Zksync01@"
def get_tokens(token):
    okx=Okex(api_key,api_secret,passphrase)
    data=okx.get_tokens(token)
    print(data)


get_tokens("USDT")