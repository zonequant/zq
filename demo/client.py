from zq.engine.tqueue import RedisQueue
import threading

url="redis://default:redispw@localhost:55000"

def do(data):
    print(f"Thread:{threading.current_thread().ident}-data")

queue=RedisQueue(url)
queue.enqueue(do,hello="abc")
