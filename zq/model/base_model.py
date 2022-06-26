from dataclasses import dataclass, field, asdict, make_dataclass
from zq.common.const import *
from loguru import logger as log
import datetime


class Model():
    _mg = None
    _tablename = None
    id = None
    _prefix = ""

    def get_name(self):
        if self._tablename is None:
            self._tablename = self.__class__.__name__.lower()
        if self._prefix == "":
            return self._tablename
        else:
            return self._prefix + "." + self._tablename

    def set_prefix(self, data):
        self._prefix = data

    def to_dict(self):
        d = self.__dict__
        rs = {}
        for k, v in d.items():
            if not k.startswith("_") :
                if isinstance(v, Model):
                    rs[k] = v.to_dict()
                elif isinstance(v, Enum):
                    rs[k] = '%s.%s' % (v.__class__.__name__, v.name)
                else:
                    rs[k] = v
        return rs

    def from_dict(self, data):
        props = self.__dict__
        if props is None:
            print(self)
        for k, v in props.items():
            if not k.startswith("_"):
                d = data.get(k,None)
                if d:
                    if isinstance(v, Model):
                        o = v.from_dict(d)
                        setattr(self, k, o)
                    elif isinstance(v, Enum):
                        if d is not None:
                            en, ev = d.split(".")
                            o = v.__class__[ev]
                            setattr(self, k, o)
                        else:
                            setattr(self, k, None)
                    else:
                        setattr(self, k, d)
        return self

    def delete(self):
        if self.id is not None:
            res = self._mg.delete(self.get_name(), {"_id": self.id})
            return res.deleted_count == 1
        else:
            log.error("实例未初始化ID，请查询后执行删除，或直接使用mongoengine根据条件删除")
            return False

    def save(self):
        if self.id is not None:
            data = self.to_dict()
            data.pop("id")
            res = self._mg.update(self.get_name(), {"_id": self.id}, {"$set": data})
            return res.modified_count == 1
        else:
            log.error("实例未初始化ID，请查询后执行更新操作，或直接使用mongoengine根据条件更新")
            return False
