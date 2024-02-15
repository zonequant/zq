from dataclasses import dataclass, field
from zq.common import const as c
from zq.model.base_model import Model

@dataclass
class Order(Model):
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """
    symbol:str = ""
    broker:str = ""
    order_id: str = ""
    side: str = c.OPEN_BUY
    offset : str=c.BOTH
    market_type:  str =c.SPOT
    order_type:str=c.LIMIT
    tif: str=c.GTC
    price: float = 0
    qty: float = 0
    filled_qty: float = 0
    avg_price: float = 0
    traded: float = 0
    fee: float = 0
    reduce = False
    post = False
    ioc= False
    stopPrice: float = 0
    status:str=c.STATUS_NEW
    err_msg:str=""
    time: float = 0

    @property
    def amount(self):
        if self.price==0:
            return self.qty*self.avg_price
        else:
            return self.qty*self.price

