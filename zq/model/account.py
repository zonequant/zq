from zq.common import const as c
from dataclasses import dataclass, field
from zq.model.base_model import Model
from collections import defaultdict


@dataclass
class Asset(Model):
    name:str=""
    symbol:str=""
    balance: float = 0
    frozen:float=0
    free: float = 0
    leverage:int=0
    pnl:float=0.0

@dataclass
class Account(Model):
    info:str=""
    name: str = ""
    type:str=c.SPOT
    id:str=""
    api_key:str=""
    api_secret:str=""
    assets= {}
    leverage:int=0
    positionside="BOTH"

        

