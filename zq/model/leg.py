from dataclasses import dataclass, field
from zq.common import const as c
from datetime import datetime
from zq.model.ticker import Ticker
from zq.model.base_model import Model
from zq.model.order import Order


@dataclass
class Leg():
    exchange: str = ""
    symbol: str = ""
    type:str=c.SPOT # 现货，杠杆，永续，交割
    multiplier: float = 1  # 乘数
    status: int = 0
    tick: Ticker = Ticker()

    def __init__(self, broker=None):
        if broker:
            self.broker = broker

    def on_tick(self, data):
        self.tick = data
        

    def set_broker(self, broker):
        self.broker = broker

    def buy(self,volume):
        self.broker.buy(self.symbol,volume)
    
    def sell(self,volume):
        self.broker.sell(self.symbol,volume)
        
    def start(self):
        if self.broker:
            self.broker.sub([self.symbol], self.on_tick)
            return True
        else:
            return False
