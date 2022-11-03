# -*- coding:utf-8 -*-
"""
@Time : 2022/5/20 16:04
@Author : Domionlu@gmail.com
@File : main
"""
# -*- coding:utf-8 -*-
from zq.engine.baseStrategy import BaseStrategy
from zq.indicator.common import *


from zq.engine.tqueue import Worker
url="redis://default:redispw@localhost:55000"
worker=Worker(url)
worker.start()
