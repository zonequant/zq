# -*- coding:utf-8 -*-
"""
@Time : 2022/1/8 11:49
@Author : domionlu@zquant.io
@File : test_series
"""
# -*- coding:utf-8 -*-
import numpy as np
import traceback
import pandas as pd

DEFAULT = "DEFAULT"

class Dataset(object):
    """
    多品种时序数据容器
    1.添加时判断格式并进行转换
    2.同步interval
    3.添加快捷访问属性
    """
    _data={}   # TimeSeries时序数组
    _keys=[]
    instance = None
    _i=0

    def add(self,data,name=None):
        if name is None:
            name=data._name
        if isinstance(data,pd.DataFrame):
            data = TimeSeries(data)
        if isinstance(data, TimeSeries):
            self._data[name]=data
            self._keys.append(name)
            setattr(self,name,data)
        else:
            raise Exception(f"无效的数据类型{type(data)}") # 只支持DataFrame,Timeseries


    def __getitem__(self, key):
        if isinstance(key, int):
            index=self._keys[key]
            return self._data[index]
        elif isinstance(key, str) and key in self._keys:
            return self._data[key]

    def __getattr__(self, item):
        """
        默认获取第一个时序数据的字段数据
        :param item:
        :return:
        """
        data = self._data[self._keys[0]]
        data=getattr(data, item)
        return data[:self._i]

    def next(self):
        self._i+=1
        for k,v in self._data.items():
            v.set_index(self._i)


    @property
    def symbols(self):
        return self._keys

    def size(self):
        return len(self._data[self._keys[0]])

class TimeSeries():
    _columns = []  # 列标题列表，用于按字段名取列数据
    _data = None  # ndarray数组
    _i = 0  # 当前数组的内部索引
    datetime_col="datetime"
    _name=""
    step_size=10000

    def __init__(self, data, step_size=100000):
        """
        基于numpy管理时序数据
        通过先初始化一个大尺寸的矩阵解决numpy数据增改速度慢问题
        :param data: 带日期的索引的根据索引做为时间数据，否则取第一列的数据
        :param size: 默认numpy矩阵长底10w
        """
        self.step_size = step_size
        if isinstance(data, pd.DataFrame):
            if pd.api.types.is_datetime64_any_dtype(data.index):
                index=True
            else:
                index=False
            self._data = data.to_records(index=index)
            self._columns = self._data.dtype.names
            self.datetime_col = self._columns[0]
        elif isinstance(data, np.ndarray):
            self._data = data
            if data.dtype.names is not None:
                self._columns = data.dtype.names
                self.datetime_col = self._columns[0]
        else:
            print(type(data))
            print(data)
        self.size = len(self._data)- 1
        self._i = self.size
        self.set_attr()

    def set_attr(self):
        if self._columns:
            for i in self._columns:
                setattr(self,i,self._data[i])

    # @property
    # def datetime(self):
    #     return self._data[self.datetime_col][:self._i]
    def set_index(self,i):
        self._i=i

    def __array__(self):
        """
        在numpy类计算函数调用时可以自动转换成numpy
        :return:
        """
        return self._data

    # def __getattr__(self, item):
    #     """
    #     使用 data.close访问数据
    #     :param item:
    #     :return:
    #     """
    #     if item in self._columns:
    #         return self._data[item][:self._i]
    #     # else:
    #         # return getattr(self, item)

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                key = self._i + key + 1
            return self._data[key]
        elif isinstance(key, slice):
            # todo 在内存索引中使用切片
            return self.__class__(self._data[key])
        elif key in self._columns:
            return self._data[key][:self._i]
        else:
            raise ValueError(f"{key} is not in columns.")

    # def index(self,key):
    #     if isinstance(key, int):
    #         if key < 0:
    #             key = self._i + key + 1
    #         return self._data[key]
    #     elif isinstance(key, slice):
    #         # todo 在内存索引中使用切片
    #         return self.__class__(self._list[key])

    def last(self):
        return self._data[self._i]

    def __len__(self):
        return self._i

    def append(self, data):
        """
        添加数据的时候，在内部索引处更新数据，并向下移动一位
        :param data: dict or list
        :return:
        """
        if self._i == self.size:
            self.resize()
        if self.update(data, self._i + 1):
            self._i += 1

    def update(self, data, index=None):
        """
        统一的更新数据函数，未指定内部索引的则直接使用当前内部索引
        :param data:
        :param index:
        :return:
        """
        try:
            if index == None:
                index = self._i
            if index > self.size:
                raise ValueError(f"{index} out of size.")
            if isinstance(data, dict):
                for k, v in data.items():
                    self._data[index][k] = v
            else:
                for i in range(len(data)):
                    self._data[index][i] = data[i]
            return True
        except:
            traceback.print_exc()

    def resize(self):
        """
        扩展numpy空间
        :return:
        """
        self._data.resize(self.size + self.step_size)
        self.size = self._data.shape[0] - 1
