from dataclasses import dataclass, field
from zq.common.const import *
from zq.model.base_model import Model

@dataclass
class Trade(Model):
    """
    Trade data contains information of a fill of an order. One order
    can have several trade fills.
    """
    symbol: str=""
    side: str=""
    price: float = 0
    qty: float = 0
    fee: float = 0
    time: float = 0
