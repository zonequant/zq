# -*- coding:utf-8 -*-
"""
@Time : 2021/8/9 14:45
author: Jimmy
contact:234390130@qq.com
"""
# -*- coding:utf-8 -*-


from abc import abstractmethod
from collections import defaultdict
from queue import Empty, Queue
from threading import Thread
from time import sleep
from typing import Any, Callable, List

class EventManger(object):
    instance = None

    def __init__(self):
        raise SyntaxError('can not instance, please use get_instance')

    @staticmethod
    def get_instance():
        if EventManger.instance is None:
            EventManger.instance = EventEngine()
        return EventManger.instance


class Event(object):
    # 事件对象
    def __init__(self, type, data=None):
        self.type = type
        self.data = data

    def __repr__(self):
        return f"Event( type:{self.type} ,data: {self.data}) "


class BaseEngine(object):
    @abstractmethod
    def start(self):
        raise

    @abstractmethod
    def register(self, type: str, callback):
        raise

    @abstractmethod
    def unregister(self, type: str, callback):
        raise

    @abstractmethod
    def put(self, event: Event):
        raise

class EventEngine(BaseEngine):

    def __init__(self, interval: int = 1):
        self._interval: int = interval
        self._queue: Queue = Queue()
        self._active: bool = False
        self._thread: Thread = Thread(target=self._run)
        self._callbacks: defaultdict = defaultdict(list)
        self._general_handlers: List = []

    def _run(self) -> None:
        while self._active:
            try:
                event = self._queue.get(block=True, timeout=1)
                self._process(event)
            except Empty:
                pass

    def _process(self, event: Event) -> None:
        if event.type in self._callbacks:
            [callback(event.data) for callback in self._callbacks[event.type]]

    def start(self) -> None:
        if self._active==False:
            self._active = True
            self._thread.start()

    def stop(self) -> None:
        """
        Stop event engine.
        """
        self._active = False
        self._thread.join()

    def put(self, event: Event) -> None:
        self._queue.put(event)

    def register(self, type: str, callback) -> None:
        callback_list = self._callbacks[type]
        if callback not in callback_list:
            callback_list.append(callback)

    def unregister(self, type: str, callback) -> None:
        callback_list = self._callbacks[type]
        if callback in callback_list:
            callback_list.remove(callback)
        if not callback_list:
            self._callbacks.pop(type)


# 测试
if __name__ == '__main__':
    def test():
        """测试函数"""
        from datetime import datetime

        def simpletest(event):
            print('处理每秒触发的计时器事件：%s' % str(datetime.now()))

        ee = EventManger.get_instance()
        # ee.register(EVENT_TIMER, simpletest)
        ee.start()
        ee.register("event", simpletest)

        for i in range(100):
            e = Event("event")
            e.data = {"int": i}
            ee.put(e)


    test()
