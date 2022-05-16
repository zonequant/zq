# -*- coding:utf-8 -*-
"""
@Time : 2020/3/16 12:12 上午
@Author : Domionlu
@Site : 
@File : baseEngine.py
@Software: PyCharm
"""


from loguru import logger as log

class BaseEngine():

    def __init__(self):
        self.event_engine=EventEngine()
        self.strategy=None
        self.broker=None
        self.strategy_class=None

    def run(self):
        self.broker.start()
        log.info("行情引擎已启动...")
        self.strategy.init()
        self.event_engine.start()
        log.info("策略引擎已启动")

    def add_strategy(self, strategy_class: type, params: dict):
        """"""
        self.strategy_class = strategy_class
        self.strategy = strategy_class(self, params)
        self.strategy.set_broker(self.broker)

    def add_broker(self,broker):
        self.broker=broker
        self.broker.set_event(self.event_engine)




"""
借鉴sklean中pipeline管道的处理逻辑
依次处理指标计算，入场，止盈止损，评估等相对固定的流程节点
bot=BotLine()
bot.add_strator(DoubleEma)
bot.add_data(datas)
bot.run()
bot.profile()

数据容器
{data:[],account:[],order:[],position:[]}

strator.next()
   



"""

