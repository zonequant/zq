# -*- coding:utf-8 -*-
"""
@Time : 2021/4/12 20:26
@Author : domionlu@zquant.io
@File : bot
"""
# -*- coding:utf-8 -*-



from zq.common.const import *
from zq.engine.orderManagerServer import OrderManagerServer
import traceback
from loguru import logger as log


class BotEngine(object):
    datas=list()
    strats=list()
    brokers=list()
    anlyzers=list()
    status=0

    def __init__(self):
        self.runstrat=list()
        self.ee=AsyncEngine()
        self.oms=OrderManagerServer(self)
        self.ee.start()

    def register(self):
        self.ee.register(BAR,self.on_bar)
        self.ee.register(TICKER, self.on_tick)
        self.ee.register(ORDER, self.on_order)
        self.ee.register(POSITION, self.on_posistion)
        self.ee.register(BALANCE, self.on_balance)

    def add_strategy(self, strategy, params : dict):
        """
        添加策略类
        """
        self.strats.append([strategy, params])

    def add_broker(self,broker):
        self.brokers.append(broker)

    def run(self):
        """
        策略启动
        """
        if len(self.brokers)>0:
            for stratcls, params in self.strats:
                strat=self.runstrategies(stratcls,params)
                self.runstrat.append(strat)
        else:
            log.error("尚未加载broker数据源")

    def runstrategies(self,stratcls,params):
        """
        初始化策略，并进行相应配置
        """
        try:
            strat = stratcls(params)
            strat.set_broker(self.brokers)
            log.info(f"策略{stratcls.__name__}加载完成。")
            strat.init()
            log.info(f"策略{stratcls.__name__}初始化完成。")
            strat.start()
            log.info(f"策略{stratcls.__name__}已启动")
            return strat
        except  Exception as e:
            log.error(traceback.print_exc())

    async def on_stop(self):
        self.status=-1
        for i  in self.runstrat:
            i.on_stop()

    async def on_bar(self,data):
        for i in self.runstrat:
            i.on_bar(data)

    async def on_tick(self,data):
        for i in self.runstrat:
            i.on_tick(data)

    async def on_posistion(self,data):
        self.oms.on_position(data)
        for i in self.runstrat:
            i.on_position(data)

    async def on_balance(self,data):
        self.oms.on_balance(data)
        for i in self.runstrat:
            i.on_balance(data)

    async def on_order(self, data):
        self.oms.on_order(data)
        for i in self.runstrat:
            i.on_order(data)

"""
Bot 主调度类
Oms 订单管理类  管理策略发出的开空仓 操作请求，路由调度具体的交易所，内部维护broker[symbol]对应关系 symbol->broker 
broker 实盘交易所  对接交易所，一个账户一个实例
Strategry 具体实现策略 根据datas数据源生成信号，根据信号发出买卖请求，与数据源，交易所解耦，由oms负责对接调度  
"""

if __name__ == '__main__':
    bot = BotEngine()
    symbol = "BTC-USDT"
    broker = Binance(api_key="", api_secret="",)
    broker.data_feed(symbol,"1D")
    bot.add_broker(broker)
    params = {"short_period": 15, "long_period": 30, "qty": 0.001}
    bot.add_strategy(Doubleema, params)
    bot.run()