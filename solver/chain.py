"""Persistent balanced binary-relation chains, checked by the Lean tree kernel.

An edge mask has bit (2*x+y) set iff the edge allows (x,y). End masks use
bit x. Padding is identity (mask 9). The explicit API avoids pretending that
recognizing arbitrary SAT as a chain is free. Updates path-copy immutable nodes;
full witness output and native replay after restart are separately charged.
"""
from collections import OrderedDict
import time
from solver.knowledge_store import KnowledgeStore
from solver.resources import BudgetExceeded


def compose(a,b):
    return sum(1<<(2*x+z) for x in range(2) for z in range(2)
               if any(a & (1<<(2*x+y)) and b & (1<<(2*y+z)) for y in range(2)))


class ChainSolver:
    def __init__(self, service):
        self.service=service;self.db=service.db
        self.store=KnowledgeStore(self.db,service.engine_id)
        self.cache=OrderedDict();self.verified=set();self.worker=None
        self.metrics={}

    @staticmethod
    def create(db):
        db.execute('''CREATE TABLE IF NOT EXISTS chain_states (
            engine TEXT NOT NULL,id TEXT NOT NULL,evidence TEXT NOT NULL,created_ns INTEGER NOT NULL,
            PRIMARY KEY(engine,id))''')

    def read(self,token):
        self.service._check_deadline();self.metrics['node_reads']+=1
        if token not in self.cache:
            self.cache[token]=self.store.get(token,'chain_node')
        self.cache.move_to_end(token)
        while len(self.cache)>2048:self.cache.popitem(last=False)
        return self.cache[token]

    def save(self,node):
        token=self.store.put('chain_node',node)[0]
        self.metrics['node_writes']+=1
        self.cache[token]=node
        self.cache.move_to_end(token)
        while len(self.cache)>2048:self.cache.popitem(last=False)
        return token

    def leaf(self,mask):return self.save(dict(height=0,mask=mask))

    def join(self,left,right):
        a,b=self.read(left),self.read(right)
        if a['height']!=b['height']:raise ValueError('Unbalanced chain join')
        self.metrics['compositions']+=1
        return self.save(dict(height=a['height']+1,mask=compose(a['mask'],b['mask']),left=left,right=right))

    def padding(self,height):
        root=self.leaf(9)
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
        level=[self.leaf(mask) for mask in edges]+[self.leaf(9)]*(capacity-len(edges))
        if not level:level=[self.leaf(9)]
        while len(level)>1:level=[self.join(level[i],level[i+1]) for i in range(0,len(level),2)]
        return level[0]

    def check_witness(self,root,size,left,right,word):
        if len(word)!=size+1 or any(type(b) is not bool for b in word):raise ValueError('Malformed chain witness')
        if not (left&(1<<word[0]) and right&(1<<word[-1])):raise ValueError('Invalid chain witness endpoints')
        position=0;stack=[root]
        while stack and position<size:
            node=self.read(stack.pop())
            if node['height']:stack.extend([node['right'],node['left']])
            else:
                if not node['mask'] & (1<<(2*word[position]+word[position+1])):raise ValueError('Invalid chain edge witness')
                position+=1
        if position!=size:raise ValueError('Incomplete chain witness')
        self.metrics['witness_checks']=position

    def ensure(self,root):
        if self.worker is not self.service.process or self.worker is None or self.worker.poll() is not None:
            self.verified.clear()
        if len(self.verified)>12000:
            self.service._request(dict(mode='chain_reset'));self.verified.clear()
        pending=[];seen=set();stack=[(root,False)]
        while stack:
            token,ready=stack.pop()
            if token in self.verified or token in seen:continue
            node=self.read(token)
            if not ready and node['height']:
                stack.extend([(token,True),(node['right'],False),(node['left'],False)])
            else:
                pending.append(dict(id=token,**node));seen.add(token)
        for offset in range(0,len(pending),128):
            batch=pending[offset:offset+128]
            result=self.service._request(dict(mode='chain_define',nodes=batch))
            if not result['valid']:raise ValueError('Native chain definitions rejected')
            self.verified.update(n['id'] for n in batch)
            self.worker=self.service.process
            self.metrics['native_definitions']+=len(batch)

    def run(self,base,replace,append,left,right,witness):
        if not isinstance(replace,dict) or not isinstance(append,list):raise ValueError('Expected replacement map and append list')
        if type(witness) is not bool:raise ValueError('Witness option must be Boolean')
        if any(type(v) is not int or not 0<=v<16 for v in list(replace.values())+append):
            raise ValueError('Edge masks must be integers from 0 to 15')
        if any(type(v) is not int or not 0<=v<4 for v in (left,right)):
            raise ValueError('Endpoint masks must be integers from 0 to 3')
        if len(replace)+len(append)>4096:raise BudgetExceeded('Chain delta exceeds 4096 edges')
        self.metrics=dict(node_reads=0,node_writes=0,compositions=0,native_definitions=0,witness_checks=0)
        before=self.store.inserted_objects
        try:
            with self.service._phase('chain_storage'),self.db:
                if base is None:
                    if replace:raise ValueError('Cannot replace edges in an empty chain')
                    root=self.build(append);size=len(append);append=[]
                else:
                    row=self.db.execute('SELECT evidence FROM chain_states WHERE engine=? AND id=?',
                                        (self.service.engine_id,base)).fetchone()
                    if row is None:raise ValueError('Unknown chain version')
                    old=self.store.get(row[0],'chain_result');root=old['root'];size=old['size']
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
                checked=self.service._request(dict(mode='chain_query',root=root,size=size,
                                                   left=left,right=right,witness=witness))
                if witness and checked['answer']:self.check_witness(root,size,left,right,checked['witness'])
                record=dict(root=root,size=size,left=left,right=right,answer=checked['answer'],witness=checked['witness'])
                evidence=self.store.put('chain_result',record)[0]
                self.db.execute('INSERT OR IGNORE INTO chain_states VALUES (?,?,?,?)',
                                (self.service.engine_id,evidence,evidence,time.time_ns()))
            self.metrics.update(new_objects=self.store.inserted_objects-before,height=self.read(root)['height'],
                                active_cache_nodes=len(self.cache))
            return dict(state=evidence,source='balanced_chain',**record,chain=dict(self.metrics),counted_complete=False)
        except BaseException:
            self.cache.clear()
            raise
