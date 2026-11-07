"""LRU bounds on retained serialized proposal payloads, not Python heap/RSS.

Mutated entries are remeasured at safe points. A large object can still exist
transiently while being checked; rejecting retention never deletes the archive.
"""
from collections import OrderedDict
import json

class PayloadCache(OrderedDict):
    def __init__(self,max_bytes,max_entries):
        super().__init__();self.max_bytes=max_bytes;self.max_entries=max_entries
        self.sizes={};self.payload_bytes=0;self.evictions=0

    def __setitem__(self,key,value):
        if key in self:self.__delitem__(key)
        size=len(json.dumps([key,value],separators=(',',':')).encode())
        if size>self.max_bytes:return
        super().__setitem__(key,value);self.sizes[key]=size;self.payload_bytes+=size
        while self.payload_bytes>self.max_bytes or len(self)>self.max_entries:self.popitem(last=False)

    def __delitem__(self,key):
        self.payload_bytes-=self.sizes.pop(key);super().__delitem__(key)

    def popitem(self,last=True):
        key,value=super().popitem(last=last)
        self.payload_bytes-=self.sizes.pop(key);self.evictions+=1
        return key,value

    def clear(self):
        super().clear();self.sizes.clear();self.payload_bytes=0

    def refresh(self):
        items=list(self.items());self.clear()
        for key,value in items:self[key]=value

    def report(self):
        return dict(retained_payload_bytes=self.payload_bytes,payload_cap_bytes=self.max_bytes,
                    entries=len(self),entry_cap=self.max_entries,evictions=self.evictions)
