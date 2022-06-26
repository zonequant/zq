from dataclasses import dataclass, field
from zq.common.const import *
from typing import List
from zq.model.base_model import Model

@dataclass
class Ticker(Model):
    broker:str=""
    deth: int = 1 # 报价深度
    symbol: str = ""
    tick_id: str = ""
    datetime: float = 0
    price: float = 0
    high: float = 0
    open:float=0
    close:float=0
    low: float = 0
    volume: float = 0  # 成交量
    trades:float=0 #成交笔数
    amount: float = 0  # 成交金额
    ask_price: float = 0  # 卖一价
    ask_volume: float = 0  # 卖一量
    bid_price: float = 0
    bid_volume: float = 0
    mid_price:float=0
    asks: List[any] = field(default_factory=list)
    bids: List[any] = field(default_factory=list)