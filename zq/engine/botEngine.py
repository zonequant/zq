# -*- coding:utf-8 -*-
"""
@Time : 2021/4/12 20:26
@Author : domionlu@zquant.io
@File : bot
"""



import traceback
from loguru import logger as log
from zq.engine.eventengine import EventManger
from zq.broker.brokerManger import BrokerManger
from zq.engine.timeseries import Dataset

class BotEngine(object):
    _datas=Dataset()
    strats=list()
    _broker=None
    anlyzers=list()
    status=0

    def __init__(self):
        self.runstrat=list()
        self.ee=EventManger.get_instance()

    def add_strategy(self, strategy, params : dict):
        """
        添加策略类
        """
        self.strats.append([strategy, params])

    def add_broker(self,broker):
        self._broker=broker

    def run(self):
        """
        策略启动
        """

        if  self._broker:
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
            strat = stratcls(self,**params)
            log.info(f"策略{stratcls.__name__}加载完成。")
            strat.init()
            log.info(f"策略{stratcls.__name__}初始化完成。")
            strat.start()
            log.info(f"策略{stratcls.__name__}已启动")
            return strat
        except  Exception as e:
            log.error(traceback.print_exc())

    @property
    def datas(self):
        return self._datas

    @property
    def broker(self):
        return self._broker

