from dataclasses import dataclass, field
from zq.common import const as c
from zq.model.base_model import Model

@dataclass
class Position(Model):
    symbol: str = ""
    side: str=c.LONG
    type:str=c.USDT_SWAP
    price: float = 0
    avg_price: float = 0
    qty: float = 0
    available: float = 0
    amount:float=0
    margin: float = 0  # 保证金
    leverage: int = 1  # 杠杆倍数
    pnl: float = 0
    time: float = 0
    liquidation_Price: float = 0
