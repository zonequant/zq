import aiohttp
from asyncio import (
    get_event_loop,
    set_event_loop,
    AbstractEventLoop,
    run_coroutine_threadsafe,
    sleep
)
from threading import Thread
from aiohttp.http import WSMsgType

import json
import traceback
import gzip
from zq.common.const import *
from zq.common.tools import DictObj
from zq.common.tools import get_cur_timestamp
from zq.engine.baseBroke import BaseBroker
from loguru import logger as log
import threading



class Async_loop():
    _instance_lock = threading.Lock()
    _loop=None

    def __new__(cls, *args, **kwargs):
        if not hasattr(Async_loop, "_instance"):
            with Async_loop._instance_lock:
                if not hasattr(Async_loop, "_instance"):
                    Async_loop._instance = object.__new__(cls)
                    Async_loop._instance._loop=get_event_loop()
                    Async_loop._instance.start()
        return Async_loop._instance

    def start(self):
        thread = Thread(target=self.run_loop, args=(self._loop,))
        thread.daemon = True
        thread.start()
        log.debug("loop started")

    def run_loop(self,loop):
        set_event_loop(loop)
        self._loop.run_forever()

    def create_task(self,coro):
        run_coroutine_threadsafe(coro, self._loop)

class Websocket():
    url = ""
    connected_callback = None
    process_callback = None
    process_binary_callback = None
    check_conn_interval = None

    def __init__(self, check_conn_interval=10, proxy=None):
        """Initialize."""
        self.check_conn_interval = check_conn_interval
        self.proxy = proxy
        self._ws = None  # Websocket connection object.
        self._loop=Async_loop()

    @property
    def ws(self):
        return self._ws

    def init(self, url, connected_callback, process_callback=None, process_binary_callback=None):
        self.url = url
        self.connected_callback = connected_callback
        self.process_binary_callback = process_binary_callback
        self.process_callback = process_callback


    async def _connect(self):
        session = aiohttp.ClientSession()
        try:
            if self.proxy:
                self._ws = await session.ws_connect(self.url, proxy=self.proxy)
            else:
                self._ws = await session.ws_connect(self.url)
                log.debug("ws connected")
            await self.connected_callback()
            log.debug("ws connected callback")
            await self._receive()
            await self.on_disconnected()
        except Exception:
            print("ws error")
            traceback.print_exc()
            await self._check_connection()


    async def on_disconnected(self):
        log.info("connected closed.")
        await self._check_connection()

    async def _reconnect(self):
        """Re-connect to Websocket server."""
        log.warning("reconnecting to Websocket server right now!")
        await self._connect()

    async def _receive(self):
        """Receive stream message from Websocket connection."""
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if self.process_callback:
                    try:
                        data = json.loads(msg.data)
                    except:
                        data = msg.data
                    await self.process_callback(data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                if self.process_binary_callback:
                    await self.process_binary_callback(msg.data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                log.warning("receive event CLOSED:", msg, caller=self)
                await self._reconnect()
            elif msg.type == aiohttp.WSMsgType.PING:
                await self._ws.send(WSMsgType.PONG)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                log.error("receive event ERROR:", msg, caller=self)
            else:
                log.warning("unhandled msg:", msg, caller=self)

    async def _check_connection(self):
        """Check Websocket connection, if connection closed, re-connect immediately."""
        if not self._ws:
            log.warning("Websocket connection not connected yet!")
            return
        if self._ws.closed:
            await self._reconnect()

    async def send(self, data):
        try:
            if not self.ws:
                log.warning("Websocket connection not connected yet!")
                return False
            if isinstance(data, dict):
                await self.ws.send_json(data)
            elif isinstance(data, str):
                await self.ws.send_str(data)
            else:
                return False
            return True
        except :
            log.error("ws send error")
            await self._check_connection()



class BaseMarket(Websocket):
    params = {
        "name": "HUOBI",
        "url": "wss://api.btcgateway.pro/linear-swap-ws",
        "is_binary": True,  # 数据包是否压缩
        "interval": 30  # 心跳间隔
    }
    host = {
        SPOT: "wss://stream.binance.com:9443",  # 现货交易
        MARGIN: "wss://stream.binance.com:9443",  # 杠杆交易
        USDT_SWAP: "wss://fstream.binance.com",  # 永续合约
        SWAP: "wss://dstream.binance.com",  # 币永续
    }
    channels = {
        USDT_SWAP: {
            BAR: {
                "sub": "$symbol$@kline_$?$",
                "topic": "kline",
                "auth": False
            },
            TICKER: {
                "sub": "$symbol$@ticker",
                "topic": "24hrTicker",
                "auth": False
            },
            ALL_TICKER: {
                "sub": "!ticker@arr",
                "topic": "24hrTicker",
                "auth": False
            },
            ORDER_BOOK: {
                "sub": "$symbol$@bookTicker",
                "topic": "bookTicker",
                "auth": False
            }
        }
    }
    assets = {}
    orders = {}
    positions = {}
    order_books = {}
    subscribes = []
    callbacks = {}
    connected = False
    symbol=""
    market_type=""
    islogin=False


    def __init__(self, broker: BaseBroker,params=None,proxy=None):
        super(BaseMarket, self).__init__(proxy=proxy)
        self.broker = broker
        self.name=broker.name
        if params:
            self.params.update(params)
        self.p = DictObj(self.params)
        self.market_type=self.broker.market_type
        self.subscribe=self.get_channels()
        self.heartbeat_time = get_cur_timestamp()

    def get_channels(self):
        return self.channels[self.market_type]

    def format_feed(self,params):
        return params

    def add_feed(self, channels,**kwargs):
        """
        单独的订阅方法，可以在初始化完成后调用
        """
        subscribes = self.get_subscribes(channels,kwargs)
        for k,v in channels.items():
            self.callbacks[k]=v
        for i in subscribes:
            if i not in self.subscribes:
                self.subscribes.append(i)
            if self.connected:
                #已经连接上ws，则直接发送订阅消息，否则等conned_callback统一发送
                self._loop.create_task(self.send(i))

    def start(self):
        """
        """
        url = self.get_url()
        self.init(url, self.connected_callback, self.process_callback, self.process_binary_callback)
        self._loop.create_task(self._connect())

    def get_url(self):
        #有些交易所这里需要重写，如币安需要请求listenKey
        market_type=self.broker.market_type
        url=self.host[market_type]
        return url

    async def process_msg(self, data):
        if self.p.is_binary:
            data = json.loads(gzip.decompress(data).decode())
        await self.process_callback(data)

    async def connected_callback(self):
        self.connected = True
        for c in self.subscribes:
            msg=json.loads(c)
            await self.send(msg)
            log.info(f"send {msg}")
        # 订阅完后可开始处理心跳
        self._loop.create_task(self.heartbeat())


    async def heartbeat(self):
        self.heartbeat_time = get_cur_timestamp()
        while self.connected:  # 不断验证信号量，若收到心跳包，则信号量应该被分发器更改为True，返回心跳包，并修改信号量为False
            if (self.heartbeat_time + self.p.interval) <= get_cur_timestamp():
                # 主动发送ping包
                await self.ping()
                self.heartbeat_time = get_cur_timestamp()
            await sleep(1)

    async def ping(self):
        await self.send(WSMsgType.PONG)

    async def process_callback(self, data):
        key = None
        for k, ch in self.subscribe.items():
            if ch["topic"] in str(data):
                key = k
                break
        if key:
            # print(data)
            parse = "parse_"+key.lower()
            if hasattr(self, parse):
                # 根据topic关键字查询对应的解析函数，默认小写
                func = getattr(self, parse)
                data = func(data)
            func = self.callbacks.get(key)
            if func and data:
                func(data)
        else:
            # 没有对应的回调函数，则调用通用的处理方法,如ping
            await self.callback(data)

    async def callback(self, data):
        pass
        # log.warning("No match:"+str(data))

    def get_subscribes(self, channels,params=None):
        """
        订阅消息格式处理
        根据每个交易所的定义格式，先使用symbol替换占位符，然后根据params逐个替换
        基本格式 "{symbol}@kline_{interval}"
        """
        subs = []
        for ch, callback in channels.items():
            sub = self.subscribe[ch].get("sub",None)
            if sub:
                for k,v in params.items():
                  if "{"+k+"}" in sub:
                    sub=sub.replace("{"+k+"}",v)
                subs.append(sub)
        return subs



if __name__ == "__main__":

    async def onmessage(data):
        channel = data.get("ch")
        if not channel:
            if data.get("ping"):
                hb_msg = {"pong": data.get("ping")}
                await ws.send(hb_msg)
            return
        else:
            log.info(data)

    async def binary_onmessage(msg):
        data = json.loads(gzip.decompress(msg).decode())
        await onmessage(data)

    async def conn():
        print("连接成功")
        await ws.send(' {"sub": "market.BTC-USDT.kline.1min" ,"id": "id8"}')

    url = 'wss://api.btcgateway.pro/linear-swap-ws'
    ws = Websocket(url, connected_callback=conn, process_callback=onmessage, process_binary_callback=binary_onmessage)
    ws.start()


