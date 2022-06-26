# -*- coding:utf-8 -*-
"""
@Time : 2021/9/23 18:11
@Author : domionlu@zquant.io
@File : __init__.py
"""
# -*- coding:utf-8 -*-
from .mongo import MongoEngine
from zq.common.logger import log
import threading



def get_mongo(uri,database):
    return MongoEngine(uri,database)


class DataManager():
    _instance_lock = threading.Lock()


    def __new__(cls, *args, **kwargs):
        if not hasattr(DataManager, "_instance"):
            with DataManager._instance_lock:
                if not hasattr(DataManager, "_instance"):
                    DataManager._instance = super(DataManager, cls).__new__(cls)
        return DataManager._instance

    def __init__(self,config):
        try:
            database=config.type
            if database=="mongo":
                session=get_mongo(config.uri,config.database)
            else:
                session = get_mongo(config.uri, config.database)
            self.conn=session
        except Exception as e:
            log.error(e)

    @classmethod
    def get_connect(cls):
        if cls._instance:
            return cls._instance.conn
        else:
            log.error(f"Database未初始化，请先初始化数据库连接")