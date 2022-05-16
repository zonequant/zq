import pika
import json
import zlib
from zq.common.tools import *
from loguru import logger as log


class Event():
    exchange="zq.*"
    queue=""
    routing_key="*"
    data=""
    def loads(self, b):
        b = zlib.decompress(b)
        d = json.loads(b.decode("utf8"))
        self.exchange = d.get("e")
        self.routing_key = d.get("k")
        self.data = d.get("d")
        return d

    def on_consume(self, ch, method, props, body):
        self.loads(body)
        self.callback(self.data)

    def callback(self,data):
        st = int(self.data)
        et = get_cur_timestamp_ms()
        log.info(f"协程消息推送耗时:{et - st}")

    def dumps(self):
        d = {
            "e": self.exchange,
            "k": self.routing_key,
            "d": self.data
        }
        s = json.dumps(d)
        b = zlib.compress(s.encode("utf8"))
        return b
    def __str__(self):
        info = "EVENT: exchange={e}, queue={q}, routing_key={r}, data={d}".format(
            e=self.exchange, q=self.queue, r=self.routing_key, d=self.data)
        return info
    def __repr__(self):
        return str(self)

class RpcEvent(Event):
    exchange ="zq.RPC"
    def __init__(self):
        self._channel=None
    async def on_consume(self, ch, method, props, body):
        self._channel=ch
        self.loads(body)
        result=self.callback(self.data)
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= props.correlation_id),
                         body=str(result))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def callback(self,data):
        print(data)
        return True

class IndEvent(Event):
    exchange = "zq.IND"

    def __init__(self):
        self._channel = None



class RabbitMq:
    def __init__(self, user, pwd, host, port):
        credentials = pika.PlainCredentials(user, pwd)  # mq用户名和密码
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, port=port, credentials=credentials, heartbeat=0)
        )
        self._channel = self.connection.channel()
        self._channel.basic_qos(prefetch_count=1)
        self._event_handler={}
        exchanges = ["zq.RPC", "zq.IND", "zq.DATA", "zq.ACCOUNT","zq.*"]
        for name in exchanges:
            self._channel.exchange_declare(exchange=name, exchange_type="topic")


    def _on_consume_event_msg(self,ch, method, props, body):
        try:
            key = "{exchange}:{routing_key}".format(exchange=method.exchange, routing_key=method.routing_key)
            funcs = self._event_handler[key]
            for func in funcs:
                func.on_consume(ch, method, props, body)
        except:
            log.error("event handle error! body:", body, caller=self)
            return
        
    def subscribe(self, event: Event, callback=None):
        AQasync.run(self._subscribe,event,callback)

    async def _subscribe(self, event: Event, callback=None):
        result = self._channel.queue_declare('', exclusive=True)
        queue_name = result.method.queue
        self._channel.queue_bind(exchange=event.exchange, queue=queue_name, routing_key=event.routing_key)
        self._channel.basic_consume(queue=queue_name, on_message_callback=self._on_consume_event_msg, auto_ack=True)
        key = "{exchange}:{routing_key}".format(exchange=event.exchange, routing_key=event.routing_key)
        event.callback=callback
        if key in self._event_handler:
            self._event_handler[key].append(event)
        else:
            self._event_handler[key] = [event]
        self._channel.start_consuming()




    def publish(self, event: Event):
        if self.connection.is_open:
            data = event.dumps()
            self._channel.basic_publish(exchange=event.exchange, routing_key=event.routing_key,body=data)


    def close(self):
        self.connection.close()


def callback( body):
    st=int(body)
    et=get_cur_timestamp_ms()
    log.info(f"协程消息推送耗时:{et-st}")

if __name__ == "__main__":
    ev=RabbitMq(user='admin', pwd='admin', host='127.0.0.1', port=5672)
    e=Event()
    e.routing_key="test"
    t=ev.subscribe(e,callback)
    time.sleep(1)
    while True:
        e.data=str(get_cur_timestamp_ms())
        ev.publish(e)
        time.sleep(2)
