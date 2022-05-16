from dataclasses import dataclass, field
from zq.common import const as c
from zq.model.base_model import Model
from typing import List


@dataclass
class Bar(Model):
    symbol:str=""
    broker:str=""
    startTime:int=0
    open:float=0
    high: float = 0
    low: float = 0
    close: float = 0
    volume:float=0
    amount:float=0
    trades:int=0
    datetime=None

    def __init__(self,data=None):
        if data:
            self.startTime=int(data[0])
            self.open=data[1]
            self.high=data[2]
            self.low=data[3]
            self.close=data[4]
            self.volume=data[5]
            self.amount=data[6]
            self.trades=data[7]


    def to_list(self):
        return [self.startTime,self.open,self.high,self.low,self.close,self.volume,self.amount,self.trades]
