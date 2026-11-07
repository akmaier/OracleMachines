"""Persistent AVL maps for expansion snapshots; updates share unchanged subtrees.

Keys are caller-supplied constraint names. No result or prior snapshot is evicted.
Only changed search paths allocate nodes. Full iteration is explicitly charged.
"""
class Manifest:
    def __init__(self, store, deadline, metrics):
        self.store,self.deadline,self.metrics=store,deadline,metrics
        self.cache={}

    def read(self, root):
        if root is None:return None
        self.deadline.check()
        self.metrics['manifest_reads']+=1
        if root not in self.cache:self.cache[root]=self.store.get(root,'expansion_map')
        return self.cache[root]

    def height(self, root):
        return self.read(root)[4] if root else 0

    def make(self,key,value,left,right):
        self.deadline.check()
        node=[key,value,left,right,1+max(self.height(left),self.height(right))]
        root=self.store.put('expansion_map',node)[0]
        self.cache[root]=node
        self.metrics['manifest_writes']+=1
        return root

    def balance(self,key,value,left,right):
        if self.height(left)-self.height(right)>1:
            a,av,al,ar,_=self.read(left)
            if self.height(al)<self.height(ar):
                b,bv,bl,br,_=self.read(ar)
                left=self.make(b,bv,self.make(a,av,al,bl),br)
                a,av,al,ar,_=self.read(left)
            return self.make(a,av,al,self.make(key,value,ar,right))
        if self.height(right)-self.height(left)>1:
            a,av,al,ar,_=self.read(right)
            if self.height(ar)<self.height(al):
                b,bv,bl,br,_=self.read(al)
                right=self.make(b,bv,bl,self.make(a,av,br,ar))
                a,av,al,ar,_=self.read(right)
            return self.make(a,av,self.make(key,value,left,al),ar)
        return self.make(key,value,left,right)

    def update(self,root,key,value):
        if root is None:
            if value is None:raise KeyError('Cannot remove an absent constraint')
            return self.make(key,value,None,None)
        k,v,l,r,_=self.read(root)
        if key<k:return self.balance(k,v,self.update(l,key,value),r)
        if key>k:return self.balance(k,v,l,self.update(r,key,value))
        if value is not None:
            return root if value==v else self.make(k,value,l,r)
        if l is None:return r
        if r is None:return l
        successor=self.read(r)
        while successor[2] is not None:successor=self.read(successor[2])
        return self.balance(successor[0],successor[1],l,self.update(r,successor[0],None))

    def items(self,root):
        stack=[]
        while root or stack:
            while root:
                node=self.read(root);stack.append(node);root=node[2]
            node=stack.pop();yield node[0],node[1];root=node[3]
