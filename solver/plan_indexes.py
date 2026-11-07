"""Immutable indexes for delta planning; iteration remains an explicit full scan."""
from solver.manifests import Manifest


class Sources:
    def __init__(self, manifest, root=None, size=0, counter="source_delta_reads"):
        self.manifest,self.root,self.size,self.counter=manifest,root,size,counter
        self.added=set();self.removed=set()

    def fork(self):return Sources(self.manifest,self.root,self.size,self.counter)
    def __len__(self):return self.size
    def __iter__(self):return (key for key,_ in self.manifest.items(self.root))

    def change(self,key,delta):
        self.manifest.metrics[self.counter]+=1
        old=self.manifest.get(self.root,key,0);new=old+delta
        if new<0:raise ValueError('Negative source reference count')
        if old==new:return
        self.root=self.manifest.update(self.root,key,new if new else None)
        if not old and new:
            self.size+=1
            if key in self.removed:self.removed.remove(key)
            else:self.added.add(key)
        if old and not new:
            self.size-=1
            if key in self.added:self.added.remove(key)
            else:self.removed.add(key)

    def add(self,key):
        if not self.manifest.get(self.root,key,0):self.change(key,1)

    def discard(self,key):
        count=self.manifest.get(self.root,key,0)
        if count:self.change(key,-count)


class Order:
    def __init__(self,manifest,rank_root=None,order_root=None,size=0):
        self.manifest,self.rank_root,self.order_root,self.size=manifest,rank_root,order_root,size

    def fork(self):return Order(self.manifest,self.rank_root,self.order_root,self.size)
    def __len__(self):return self.size
    def __iter__(self):return (v for _,v in self.manifest.items(self.order_root))
    def __reversed__(self):return (v for _,v in self.manifest.items(self.order_root,reverse=True))
    def __contains__(self,v):return self.manifest.get(self.rank_root,str(v)) is not None
    def __getitem__(self,v):
        rank=self.manifest.get(self.rank_root,str(v))
        if rank is None:raise KeyError(v)
        return rank

    def append(self,v):
        if v in self:raise ValueError('Repeated variable in elimination order')
        self.rank_root=self.manifest.update(self.rank_root,str(v),self.size)
        self.order_root=self.manifest.update(self.order_root,str(self.size).zfill(20),v)
        self.size+=1


def restore(record,store,deadline,metrics):
    manifest=Manifest(store,deadline,metrics)
    return dict(order=Order(manifest,record['rank_root'],record['order_root'],record['order_size']),
                active=Sources(manifest,record['source_root'],record['source_size']),
                constants=Sources(manifest,record['constant_root'],record['constant_size'],'constant_delta_reads'))
