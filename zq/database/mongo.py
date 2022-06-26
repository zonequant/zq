from pymongo import MongoClient
import datetime
import json

import threading
from zq.model.base_model import *
import pandas as pd
from copy import deepcopy

class MongoEngine:
    _instance_lock = threading.Lock()
    _query = None
    _recordset = None
    _ent = None

    def __init__(self, uri=None, database=None):
        self.conn = MongoClient(uri)
        self.db = self.conn[database]

    @classmethod
    def getInstance(cls, dsn=None):
        if cls._instance is None:
            cls._instance = cls(dsn=dsn)
        return cls._instance

    def __new__(self, *args, **kwargs):
        if not hasattr(MongoEngine, "_instance"):
            with MongoEngine._instance_lock:
                if not hasattr(MongoEngine, "_instance"):
                    MongoEngine._instance = super(MongoEngine, self).__new__(self)
        return MongoEngine._instance

    def get_state(self):
        return self.conn is not None and self.db is not None

    def insert_one(self, collection, data):
        if self.get_state():
            ret = self.db[collection].insert_one(data)
            return ret.inserted_id
        else:
            return ""

    def insert_many(self, collection, data):
        if self.get_state():
            ret = self.db[collection].insert_many(data)
            return ret.inserted_ids
        else:
            return ""

    def find_one(self,collection,data):
        if self.get_state():
            ret = self.db[collection].find_one(data)
            return ret
        else:
            return ""

    def find(self,collection,filter={},field=None):
        if self.get_state():
            ret = self.db[collection].find(filter,field)
            return ret
        else:
            return ""

    def delete(self, col, data={}):
        if self.get_state():
            return self.db[col].delete_many(filter=data)
        return 0

    def query(self, enty,prefix=None):
        query=Query(self,enty,prefix)
        return query


    def add(self, instance):
        col = instance.get_name()
        ret = self.db[col].insert_one(instance.to_dict())
        return ret.inserted_id

    def update(self,col, fileter,data):
        # data format:
        # {key:[old_data,new_data]}
        if self.get_state():
            return self.db[col].update_one(fileter,data)
        return 0

    def get_collections(self):
        return self.db.list_collection_names()

    def drop(self,collection):
        return self.db.drop_collection(collection)

class Query(object):
    """ 各种query 中的数据 data 和 mongodb 文档中的一样"""
    def __init__(self,mg ,ent=None,prefix=None):
        self.mg=mg
        self.ent=ent()
        if prefix:
            self.ent.set_prefix(prefix)
        self.tablename =self.ent.get_name()
        self.query=None

    def find_one(self,data_filter={}):
        self.query = self.mg.find_one(self.tablename,(data_filter))
        return self

    def find(self,data_filter={}):
        """select * from table"""
        self.query = self.mg.find(self.tablename,data_filter)
        return self
    def find_in(self, field, item_list, ):
        """SELECT * FROM inventory WHERE status in ("A", "D")"""
        data = dict()
        data[field] = {"$in": item_list}
        self.query = self.mg.find(self.tablename,data)
        return self

    def find_or(self, data_list,):
        """db.inventory.find(
    {"$or": [{"status": "A"}, {"qty": {"$lt": 30}}]})
        SELECT * FROM inventory WHERE status = "A" OR qty < 30
        """
        data = dict()
        data["$or"] = data_list
        self.query =  self.mg.find(self.tablename,data)
        return self

    def find_between(self, field, value1, value2,):
        """获取俩个值中间的数据"""
        data = dict()
        data[field] = {"$gt": value1, "$lt": value2}
        # data[field] = {"$gte": value1, "$lte": value2} # <>   <= >=
        self.query = self.mg.find(self.tablename,data)
        return self

    def find_more(self, field, value):
        data = dict()
        data[field] = {"$gt": value}
        self.query = self.mg.find(self.tablename,data)
        return self

    def find_less(self, field, value):
        data = dict()
        data[field] = {"$lt": value}
        self.query =  self.mg.find(self.tablename, data)
        return self

    def find_like(self, field, value):
        """ where key like "%audio% """
        data = dict()
        data[field] = {'$regex': '.*' + value + '.*'}
        self.query=  self.mg.find(self.tablename,data)
        return self

    def query_limit(self, num):
        """db.collection.find(<query>).limit(<number>) 获取指定数据"""
        res = self.query.limit(num)
        return res

    def query_count(self):
        res = self.query.count()
        return res

    def query_skip(self, num):
        self.query = self.query.skip(num)
        return self

    def query_sort(self, field, value):
        data = [(field,value)]
        """db.orders.find().sort( { amount: -1 } ) 根据amount 降序排列"""
        self.query= self.query.sort(data)
        return self

    def delete_one(self, data):
        """ 删除单行数据 如果有多个 则删除第一个"""
        res = self.mg.delete(self.tablename, data)
        return res

    def delete_many(self, data):
        """ 删除查到的多个数据 data 是一个字典 """
        res = self.mg.delete(self.tablename, data)
        return res

    def to_list(self):
        if isinstance(self.query,dict):
            return [self.query]
        if self.query is not None:
            return list(self.query)
        else:
            return None

    def to_pd(self):
        if self.query is not None:
            data=list(self.query)
            data=pd.DataFrame(data)
            return data
        else:
            return None

    def to_obj(self):
        list=self.to_list()
        obj_list=[]
        if list is not None:
            if len(list)>0:
                for l in list:
                    t=deepcopy(self.ent)
                    t=t.from_dict(l)
                    id = l.get("_id")
                    setattr(t, "id", id)
                    t._mg=self.mg
                    obj_list.append(t)
            return obj_list

        else:
            log.error("list is None")
            return []



# 使json能够转化datetime对象
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)


# 将 MongoDB 的 document转化为json形式
def convertToJson(o):
    data=[]
    for i in list(o):
        i["id"] = str(i.pop("_id"))
        data.append(i)
    return data
