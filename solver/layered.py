"""Persistent bounded-width layers, checked by the finite-state Lean kernel.

For q=2^width, bit q*x+y permits states (x,y) in adjacent layers. End masks
use bit x; padding permits exactly x=y. The supplied decomposition is part of
the input. Discovering it or compiling arbitrary SAT is not free. Updates path-copy immutable nodes;
full witness output and native replay after restart are separately charged.
"""
from solver.active_cache import PayloadCache
import time
from solver.knowledge_store import KnowledgeStore
from solver.resources import BudgetExceeded


def compose(a,b,q):
    result=0;mask=(1<<q)-1
    for x in range(q):
        row=0
        for y in range(q):
            if a & (1<<(q*x+y)):row|=(b>>(q*y))&mask
        result|=row<<(q*x)
    return result


class LayeredSolver:
    def __init__(self, service, width):
        if type(width) is not int or not 1<=width<=4:raise ValueError("Layer width must be 1 to 4")
        self.width,self.states=width,1<<width
        self.identity=sum(1<<(self.states*x+x) for x in range(self.states))
        self.service=service;self.db=service.db
        self.store=KnowledgeStore(self.db,service.engine_id)
        self.cache=PayloadCache(service.active_cache_bytes,2048);self.verified=set();self.worker=None
        self.metrics={}

    @staticmethod
    def create(db):
        db.execute('''CREATE TABLE IF NOT EXISTS layered_states (
            engine TEXT NOT NULL,id TEXT NOT NULL,evidence TEXT NOT NULL,created_ns INTEGER NOT NULL,
            PRIMARY KEY(engine,id))''')

    def read(self,token):
        self.service._check_deadline();self.metrics['node_reads']+=1
        if token in self.cache:
            self.cache.move_to_end(token);node=self.cache[token]
        else:
            node=self.store.get(token,'layered_node');self.cache[token]=node
        if node['width']!=self.width:raise ValueError('Layer width differs from saved version')
        return node

    def save(self,node):
        node=dict(node,width=self.width)
        token=self.store.put('layered_node',node)[0]
        self.metrics['node_writes']+=1
        self.cache[token]=node
        if token in self.cache:self.cache.move_to_end(token)
        return token

    def leaf(self,mask):return self.save(dict(height=0,mask=mask))

    def join(self,left,right):
        a,b=self.read(left),self.read(right)
        if a['height']!=b['height']:raise ValueError('Unbalanced chain join')
        self.metrics['compositions']+=1
        return self.save(dict(height=a['height']+1,mask=compose(a['mask'],b['mask'],self.states),left=left,right=right))

    def padding(self,height):
        root=self.leaf(self.identity)
        for _ in range(height):root=self.join(root,root)
        return root

    def replace(self,root,index,mask):
        node=self.read(root)
        if node['height']==0:return self.leaf(mask)
        middle=1<<(node['height']-1)
        if index<middle:return self.join(self.replace(node['left'],index,mask),node['right'])
        return self.join(node['left'],self.replace(node['right'],index-middle,mask))

    def build(self,edges):
        capacity=1<<max(0,(len(edges)-1).bit_length())
        level=[self.leaf(mask) for mask in edges]+[self.leaf(self.identity)]*(capacity-len(edges))
        if not level:level=[self.leaf(self.identity)]
        while len(level)>1:level=[self.join(level[i],level[i+1]) for i in range(0,len(level),2)]
        return level[0]

    def check_witness(self,root,size,left,right,word):
        if len(word)!=size+1 or any(type(b) is not int or not 0<=b<self.states for b in word):raise ValueError('Malformed chain witness')
        if not (left&(1<<word[0]) and right&(1<<word[-1])):raise ValueError('Invalid chain witness endpoints')
        position=0;stack=[root]
        while stack and position<size:
            node=self.read(stack.pop())
            if node['height']:stack.extend([node['right'],node['left']])
            else:
                if not node['mask'] & (1<<(self.states*word[position]+word[position+1])):raise ValueError('Invalid chain edge witness')
                position+=1
        if position!=size:raise ValueError('Incomplete chain witness')
        self.metrics['witness_checks']=position

    def ensure(self,root):
        if self.worker is not self.service.process or self.worker is None or self.worker.poll() is not None:
            self.verified.clear()
        pending=[];seen=set();stack=[(root,False)]
        while stack:
            token,ready=stack.pop()
            if token in self.verified or token in seen:continue
            node=self.read(token)
            if not ready and node['height']:
                stack.extend([(token,True),(node['right'],False),(node['left'],False)])
            else:
                pending.append(dict(id=token,**node));seen.add(token)
        cap=min(200000,self.service.native_layer_cells//self.states**2)
        if len(self.verified)+len(pending)>cap:
            # Traverse the live closure only under pressure. Retain all of it,
            # or refuse explicitly; a smaller-than-working-set reset thrashes.
            live=set();stack=[root]
            while stack:
                self.service._check_deadline()
                token=stack.pop()
                if token in live:continue
                live.add(token);self.metrics['retention_visits']+=1
                if len(live)>cap:
                    raise BudgetExceeded('Native layered working set exceeds cell budget; archive retained')
                node=self.read(token)
                if node['height']:stack.extend([node['left'],node['right']])
            keep=self.verified & live
            self.service._request(dict(mode='layered_retain',ids=sorted(keep)))
            self.metrics['native_evictions']+=len(self.verified)-len(keep)
            self.verified=keep
        for offset in range(0,len(pending),128):
            batch=pending[offset:offset+128]
            result=self.service._request(dict(mode='layered_define',nodes=batch))
            if not result['valid']:raise ValueError('Native chain definitions rejected')
            self.verified.update(n['id'] for n in batch)
            self.worker=self.service.process
            self.metrics['native_definitions']+=len(batch)

    def run(self,base,replace,append,left,right,witness):
        if not isinstance(replace,dict) or not isinstance(append,list):raise ValueError('Expected replacement map and append list')
        if type(witness) is not bool:raise ValueError('Witness option must be Boolean')
        if any(type(v) is not int or not 0<=v<(1<<(self.states*self.states)) for v in list(replace.values())+append):
            raise ValueError('Relation mask exceeds the supplied layer width')
        if any(type(v) is not int or not 0<=v<(1<<self.states) for v in (left,right)):
            raise ValueError('Endpoint mask exceeds the supplied layer width')
        if len(replace)+len(append)>4096:raise BudgetExceeded('Chain delta exceeds 4096 edges')
        self.metrics=dict(node_reads=0,node_writes=0,compositions=0,native_definitions=0,witness_checks=0,
                          retention_visits=0,native_evictions=0)
        before=self.store.inserted_objects
        try:
            with self.service._phase('layered_storage'),self.db:
                if base is None:
                    if replace:raise ValueError('Cannot replace edges in an empty chain')
                    root=self.build(append);size=len(append);append=[]
                else:
                    row=self.db.execute('SELECT evidence FROM layered_states WHERE engine=? AND id=?',
                                        (self.service.engine_id,base)).fetchone()
                    if row is None:raise ValueError('Unknown chain version')
                    old=self.store.get(row[0],'layered_result');root=old['root'];size=old['size']
                for index,mask in replace.items():
                    # JSON object keys are strings; forbid ambiguous forms.
                    if isinstance(index,str) and index.isdecimal() and str(int(index))==index:index=int(index)
                    if type(index) is not int or not 0<=index<size:raise ValueError('Replacement index outside the chain')
                    root=self.replace(root,index,mask)
                for mask in append:
                    height=self.read(root)['height']
                    if size==1<<height:root=self.join(root,self.padding(height))
                    root=self.replace(root,size,mask);size+=1
                    if size>65536:raise BudgetExceeded('Chain exceeds active capacity')
                self.ensure(root)
                checked=self.service._request(dict(mode='layered_query',root=root,size=size,
                                                   left=left,right=right,witness=witness))
                if witness and checked['answer']:self.check_witness(root,size,left,right,checked['witness'])
                record=dict(width=self.width,root=root,size=size,left=left,right=right,answer=checked['answer'],witness=checked['witness'])
                evidence=self.store.put('layered_result',record)[0]
                self.db.execute('INSERT OR IGNORE INTO layered_states VALUES (?,?,?,?)',
                                (self.service.engine_id,evidence,evidence,time.time_ns()))
            self.metrics.update(new_objects=self.store.inserted_objects-before,height=self.read(root)['height'],
                                active_cache_nodes=len(self.cache),native_cells=len(self.verified)*self.states**2,
                                native_cells_cap=self.service.native_layer_cells,
                                composition_cell_bound=self.metrics['compositions']*self.states**3)
            return dict(state=evidence,source='balanced_layers',**record,layered=dict(self.metrics),counted_complete=False)
        except BaseException:
            self.cache.clear()
            raise
