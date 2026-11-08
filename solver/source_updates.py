"""Persistent source-bearing CNF trees with checked local bucket replacements.

A version identifies all clauses in fixed adjacent variable blocks. Native code
checks each leaf, each join and the exact edit; evidence follows the same tree
as relation summaries. No full source/witness traversal is needed on warm
decision-only edits. Restart, a different layout and old branches are charged.
"""
import time
from solver.layered import LayeredSolver,compose


class SourceSolver(LayeredSolver):
    node_kind='source_node'
    mode_prefix='source'
    storage_fields=('inserted_objects','serialized_bytes','inserted_raw_bytes',
                    'inserted_packed_bytes','object_reads','read_packed_bytes')

    def __init__(self,service,layout_id,layout):
        super().__init__(service,layout['width'])
        self.layout_id,self.layout=layout_id,layout
        self.size=len(layout['layers'])-1

    @staticmethod
    def create(db):
        db.execute('''CREATE TABLE IF NOT EXISTS source_states (
            engine TEXT NOT NULL,id TEXT NOT NULL,evidence TEXT NOT NULL,
            answer INTEGER NOT NULL,created_ns INTEGER NOT NULL,PRIMARY KEY(engine,id))''')
        db.execute('CREATE INDEX IF NOT EXISTS source_version_identity ON source_states(id)')

    def reset_native(self):
        self.service._request(dict(mode='source_init',id=self.layout_id,**self.layout))
        self.metrics['layout_replays']+=1

    def read(self,token):
        node=super().read(token)
        if node['layout']!=self.layout_id:raise ValueError('Source layout differs from saved node')
        return node

    def save(self,node):
        return super().save(dict(node,layout=self.layout_id))

    def leaf(self,value):
        return self.save(dict(height=0,**value))

    def join(self,left,right):
        a,b=self.read(left),self.read(right)
        if a['height']!=b['height'] or b['start']!=a['start']+(1<<a['height']):
            raise ValueError('Source children must cover consecutive balanced intervals')
        self.metrics['compositions']+=1
        return self.save(dict(height=a['height']+1,start=a['start'],
            mask=compose(a['mask'],b['mask'],self.states),left=left,right=right))

    def build_source(self,buckets,masks):
        if len(buckets)!=self.size or len(masks)!=self.size:raise ValueError('Incomplete compiled source')
        capacity=1<<(self.size-1).bit_length()
        level=[self.leaf(dict(start=i,mask=masks[i],clauses=buckets[i])) for i in range(self.size)]
        level += [self.leaf(dict(start=i,mask=self.identity,clauses=[])) for i in range(self.size,capacity)]
        while len(level)>1:level=[self.join(level[i],level[i+1]) for i in range(0,len(level),2)]
        return level[0]

    def run(self,base,clauses,replace,witness):
        if type(witness) is not bool:raise ValueError('Witness option must be Boolean')
        self.metrics=dict(node_reads=0,node_writes=0,compositions=0,native_definitions=0,
            witness_checks=0,retention_visits=0,native_evictions=0,reachability_updates=0,
            layout_replays=0,patch_visits=0,binding_visits=0,compiled_cells=0,
            binding_leaves=0,binding_relation_comparisons=0,binding_cell_bound=0,binding_source_test_bound=0,
            compiled_literal_test_bound=0,native_source_cells=0,native_literal_test_bound=0,
            original_source_nodes=0,original_clause_entries=0,original_literal_entries=0,
            peak_native_cells=len(self.verified)*self.states**2)
        before={field:getattr(self.store,field) for field in self.storage_fields}
        try:
            with self.service._phase('source_update'),self.db:
                if base is None:
                    if replace:raise ValueError('Initial source cannot have edits')
                    original=dict(**self.layout,clauses=clauses)
                    compiled=self.service._request(dict(mode='layered_compile',**original))
                    self.metrics['compiled_cells']=compiled['relation_cells']
                    self.metrics['compiled_literal_test_bound']=self.states**2*(self.size+sum(1+len(c) for c in clauses))
                    root=self.build_source(compiled['buckets'],compiled['masks'])
                    self.ensure(root)
                    checked=self.service._request(dict(mode='source_bind',root=root,witness=witness,**original))
                    self.metrics['binding_visits']=checked['binding_visits']
                    for field in ('binding_leaves','binding_relation_comparisons','binding_cell_bound','binding_source_test_bound'):
                        self.metrics[field]=checked[field]
                    checked=checked['verdict']
                else:
                    previous=self.store.get(base,'source_version')
                    if previous['layout']!=self.layout_id or previous['size']!=self.size:
                        raise ValueError('Source version partition differs')
                    old=root=previous['root']
                    self.ensure(old)
                    edits=[];seen=set()
                    if not isinstance(replace,dict) or len(replace)>4096:raise ValueError('Expected at most 4096 source bucket replacements')
                    for index,bucket in replace.items():
                        if isinstance(index,str) and index.isdecimal() and str(int(index))==index:index=int(index)
                        if type(index) is not int or not 0<=index<self.size or index in seen:
                            raise ValueError('Invalid or duplicate source edge')
                        seen.add(index);edits.append(dict(edge=index,clauses=bucket))
                    if edits:
                        compiled=self.service._request(dict(mode='source_compile',edits=edits))
                        self.metrics['compiled_cells']=compiled['source_cells']
                        self.metrics['compiled_literal_test_bound']=compiled['literal_test_bound']
                        for edit,mask in zip(edits,compiled['masks'],strict=True):
                            root=self.replace(root,edit['edge'],dict(start=edit['edge'],clauses=edit['clauses'],mask=mask))
                        # Keep the base until its transition is checked. This
                        # explicit transient reservation is at most the new DAG.
                        self.ensure(root,defer_eviction=True)
                        checked=self.service._request(dict(mode='source_patch',base=old,root=root,edits=edits,witness=witness))
                        self.metrics['patch_visits']=checked['patch_visits'];checked=checked['verdict']
                        cap=min(200000,self.service.native_layer_cells//self.states**2)
                        self.evict(max(0,len(self.verified)-cap))
                    else:
                        checked=self.service._request(dict(mode='source_query',root=root,witness=witness))
                if witness and checked['answer']:
                    self.check_witness(root,self.size,(1<<self.states)-1,(1<<self.states)-1,checked['witness'])
                state=self.store.put('source_version',dict(layout=self.layout_id,root=root,size=self.size))[0]
                record=dict(state=state,answer=checked['answer'],witness=checked['witness'])
                evidence=self.store.put('source_result',record)[0]
                self.db.execute('INSERT OR IGNORE INTO source_states VALUES (?,?,?,?,?)',
                    (self.service.engine_id,state,evidence,int(checked['answer']),time.time_ns()))
            height=self.read(root)['height']
            self.metrics.update(native_cells=len(self.verified)*self.states**2,
                live_nodes=len(self.live_refs),native_cells_cap=self.service.native_layer_cells,
                height=height,composition_cell_bound=self.metrics['compositions']*self.states**3,
                query_composition_bound=0 if not witness or self.size==1<<height else height*self.states**3,
                metadata_entries=len(self.live_refs)+len(self.native_children)+len(self.native_incoming),
                **{field:getattr(self.store,field)-before[field] for field in self.storage_fields})
            return dict(**record,root=root,layout=self.layout_id,size=self.size,width=self.width,
                source='source_cnf',source_updates=dict(self.metrics),counted_complete=False)
        except BaseException:
            self.cache.clear();self.forget_native()
            raise
