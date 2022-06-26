from dataclasses import dataclass, field
from zq.common import const as c
from zq.model.base_model import Model
from zq.model.order import Order

@dataclass
class Leg(Model):
    offset: c.OPEN_BUY
    price:float=0
    volume:float=0
    order:Order=field(default=Order)

@dataclass
class Pair(Model):
    right:Leg=field(default=Leg)
    left:Leg=field(default=Leg)
    starttime:float=0
    side:str=c.LONG
    status:int=0
    def __init__(self,side=None):
        super().__init__()
        if side:
            self.side=side

    def add_right(self,price):
        if self.side==c.LONG:
            self.right.price=self.left.price+price
            self.right.volume=self.left.volume
        else:
            self.right.price=self.left.price-price
            self.right.volume=self.right.volume 