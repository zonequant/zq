#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/11/17 20:46
# @Author  : Dominolu
# @File    : test1.py
# @Software: PyCharm

from zq.common.tools import *
import numpy as np

@time_cost
def go_fast(a): # 首次调用时，函数被编译为机器代码
    trace = 0
    # 假设输入变量是numpy数组
    for i in range(a):
        for j in range(a):
            trace=trace+i*j

x =100000


go_fast(x)

