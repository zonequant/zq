# -*- codeing = utf-8 -*-
# @Time：2022/6/20 18:15
# @Author：Dominolu
# @File：tqueue.py
# @Mail: dominolu@gmail.com
import threading
import time
import traceback
from zq.common.tools import *
import pickle
from loguru import logger as log
from redis import StrictRedis, ConnectionPool, Redis


class RedisQueue(object):
    redis_queue_namespace_prefix = "zq:queue:"

    def __init__(self, url, name="*"):
        pool = ConnectionPool.from_url(url)
        self._conn = Redis(connection_pool=pool, decode_responses=True)
        # redis的默认参数为：host='localhost', port=6379, db=0， 其中db为定义redis database的数量
        self.key = self.redis_queue_namespace_prefix + name

    def qsize(self):
        return self._conn.llen(self.key)  # 返回队列里面list内元素的数量

    def put(self, item):
        return self._conn.rpush(self.key, item)  # 添加新元素到队列最右方

    def get_wait(self, timeout=None):
        # 返回队列第一个元素，如果为空则等待至有元素被加入队列（超时时间阈值为timeout，如果为None则一直等待）
        item = self._conn.blpop(self.key, timeout=timeout)
        # if item:
        #     item = item[1]  # 返回值为一个tuple
        return item

    def get(self, key):
        return self._conn.hgetall(key)

    def get_nowait(self):
        # 直接返回队列第一个元素，如果队列为空返回的是None
        item = self._conn.lpop(self.key)
        return item

    def push_job(self, job_id, pipe=None):
        connection = pipe if pipe is not None else self._conn
        connection.lpush(self.key, job_id)

    def enqueue(self,func,**kwargs):
        # Add Queue key set
        job = Job.create(self._conn,func=func, data=kwargs)
        job.set_status(0)
        job.save()
        self.push_job(job.job_id)
        return job


class Job(object):
    job_id = ""
    redis_job_namespace = "zq:job:"
    data = None
    func = None
    create_t = None
    start_t = None
    end_t = None
    description = ""
    status = 0  # 0:创建任务，1、任务待启动，2、任务启动中，3、任务已完成 ，4、任务失败(包括超时）
    timeout = 5  #
    result = ""
    worker = ""
    thread = ""

    @classmethod
    def create(cls, connection,func, data=None):
        job = cls(conn=connection)
        job.func=func
        job.data = data
        return job

    @classmethod
    def fetch(cls, connection,job_id):
        job = cls( conn=connection,id=job_id)
        job.refresh()
        return job

    def __init__(self,conn, id=None):
        self._conn = conn
        if id:
            self.job_id = id
        else:
            self.job_id = get_uuid1()
            self.create_t = get_cur_timestamp_ms()

    @property
    def key(self):
        return (self.redis_job_namespace +self.job_id).encode('utf-8')

    def wait_finish(self):
        while self.status in (0, 1, 2):
            self.refresh()
            if self.create_t:
                delta = get_cur_timestamp_ms() - self.create_t
                if delta > self.timeout * 1000:
                    self.status = 4
                    self.save()
                    # print(f"Job:{self.job_id} timeout.")
            time.sleep(0.01)

    def refresh(self):
        data = self._conn.hgetall(self.key)
        if not data:
            raise ('No such job: {0}'.format(self.key))
        self.parse(data)

    def parse(self, data):
        strdata = {}
        for k, v in data.items():
            if k.decode() in ("data","func"):
                strdata[k.decode()] = pickle.loads(v)
            else:
                strdata[k.decode()] = v.decode()
        self.data = strdata.get("data")
        self.func=strdata.get("func")
        self.create_t = int(strdata.get("create_t")) if strdata.get("create_t") else None
        self.start_t = int(strdata.get("start_t")) if strdata.get("start_t") else None
        self.end_t = int(strdata.get("end_t")) if strdata.get("end_t") else None
        self.description = strdata.get('description')
        self.result = strdata.get('result') if strdata.get('result') else None
        self.timeout = int((strdata.get('timeout'))) if strdata.get('timeout') else 5
        self.status = int(strdata.get('status')) if strdata.get('status') else None

    def save(self, pipe=None):
        connection = pipe if pipe is not None else self._conn
        data = self.to_dict()
        # print(data)
        connection.hmset(self.key, mapping=data)

    def to_dict(self):
        data = {
            "job_id": self.key,
            "description": self.description,
            "timeout": self.timeout,
            "status": self.status,
            "func":pickle.dumps(self.func),
            "data": pickle.dumps(self.data),
        }
        if self.result is not None:
            data["result"] = self.result
        if self.create_t is not None:
            data["create_t"] = self.create_t
        if self.start_t is not None:
            data["start_t"] = self.start_t
        if self.end_t is not None:
            data["end_t"] = self.end_t
        return data

    def set_status(self, status):
        self._status = status
        # self._conn.hset(self.key, 'status', self._status)

    @classmethod
    def update(cls, conn, key, **kwargs):
        conn.hmset(key, mapping=kwargs)


class Worker(object):
    """
    主进程获取redis任务
    多进程执行任务
    """
    threads = {}
    redis_queue_namespace_prefix = "zq:queue:"

    def __init__(self, url, name="*"):
        pool = ConnectionPool.from_url(url)
        self._conn = Redis(connection_pool=pool, decode_responses=True)
        self.key = self.redis_queue_namespace_prefix + name
        self.worker_id = get_uuid1()
        self.thread = threading.Thread(target=self.work)

    def start(self):
        self.thread.start()

    def work(self):
        log.info(f"Worker:{self.worker_id} started.")
        while True:
            job_id = self._conn.lpop(self.key)
            if job_id:
                self.run(job_id.decode())
            for k, v in self.threads.items():
                if v.is_alive():
                    log.info(f"Job {k} is finished.")
                    result = v.get_result()
                    self.threads.pop(k)
                    Job.update(self._conn,k, status=4, result=result)
            time.sleep(0.1)

    def run(self, job_id):
        job = Job.fetch(self._conn,job_id)
        func = job.func
        thread = Task_thread(func,args=job.data)
        self.threads[job_id] = thread
        thread.start()
        job.status = 3
        job.thread = thread.ident
        job.save()
        log.info(f"Job {job_id} is running,thread_id:{thread.ident}")

class Task_thread(threading.Thread):
    def __init__(self, func, args):
        super(Task_thread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(self.args)  # 在执行函数的同时，把结果赋值给result,
        # 然后通过get_result函数获取返回的结果

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            return None
