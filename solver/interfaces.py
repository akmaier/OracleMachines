"""Checked, persistent variable elimination with small local interfaces.

The Python planner and saved tables are untrusted. Every new/replayed factor is
checked by the native engine; SAT is checked on all active original constraints,
and UNSAT needs an empty relation whose checked source leaves remain active.
All graph objects are immutable. Fallback handles instances exceeding width caps.
"""
from collections import OrderedDict
import hashlib
import json
import time

from solver.components import analyze, conjunction
from solver.incremental import parse_postfix
from solver.knowledge_store import KnowledgeStore
from solver.relations import assignments, row_index, pack, unpack, project
from solver.manifests import Manifest
from solver.resources import BudgetExceeded, Deadline


def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def counters():
    return dict(input_bytes=0,parsed_nodes=0,leaf_rows=0,combination_rows=0,table_probes=0,
        node_hits=0,node_acquisitions=0,native_definitions=0,native_replays=0,native_rows=0,
        ordering_candidates=0,ordering_edges=0,max_bag=0,manifest_reads=0,manifest_writes=0,
        semantic_duplicates=0,relation_payload_bytes=0,archive_new_objects=0,row_hits=0,native_row_acquisitions=0,native_row_checks=0,
        planned_rows=0,unknown_rows=0,active_cache_nodes=0)


def evaluate(nodes,assignment):
    values=[]
    for n in nodes:
        if n[0]=='false':value=False
        elif n[0]=='var':value=assignment[n[1]]
        elif n[0]=='not':value=not values[n[1]]
        else:value=values[n[1]] and values[n[2]]
        values.append(value)
    return values[-1]


class InterfaceSolver:
    def __init__(self,service,max_interface=3,active_nodes=1024):
        if not 0<=max_interface<=10:raise ValueError('Interface cap must be between zero and ten')
        self.service=service
        self.db=service.db
        self.store=KnowledgeStore(self.db,service.engine_id)
        self.engine=service.engine_id
        self.max_interface=max_interface
        self.active_nodes=active_nodes
        self.cache=OrderedDict()
        self.verified=set()
        self.worker=None
        self.bound=set()
        self.verified_rows=set()
        self.metrics=counters()
        self.deadline=None

    def remember(self,name,node):
        self.cache[name]=node;self.cache.move_to_end(name)
        while len(self.cache)>self.active_nodes:self.cache.popitem(last=False)
        return node

    def read(self,name):
        self.deadline.check()
        if name in self.cache:
            self.cache.move_to_end(name);return self.cache[name]
        row=self.db.execute('SELECT evidence,relation FROM interface_nodes WHERE engine=? AND id=?',(self.engine,name)).fetchone()
        if row is None:return None
        node=self.store.get(row['evidence'],'interface_evidence')
        if identity(node['definition'])!=name:raise ValueError('Interface evidence identity mismatch')
        relation=self.store.get(row['relation'],'interface_relation')
        node.update(id=name,relation=row['relation'],rows=unpack(relation,len(node['scope'])))
        node['choice_values']=unpack(node['choices'],len(node['scope'])) if node['choices'] is not None else [None]*len(node['rows'])
        for row in self.db.execute('SELECT row_index,answer,choice FROM interface_rows WHERE engine=? AND id=?',(self.engine,name)):
            if not 0<=row[0]<len(node['rows']):raise ValueError('Invalid stored row index')
            node['rows'][row[0]]=bool(row[1]);node['choice_values'][row[0]]=None if row[2] is None else bool(row[2])
        return self.remember(name,node)

    def ensure(self,name):
        """Replay checked DAG nodes once per native worker; cap active state."""
        if self.worker is not self.service.process or self.worker is None or self.worker.poll() is not None:
            self.verified.clear();self.bound.clear();self.verified_rows.clear();self.worker=self.service.process
        stack=[(name,False)]
        while stack:
            self.deadline.check()
            token,ready=stack.pop()
            if token in self.verified:continue
            node=self.read(token)
            if node is None:raise ValueError('Missing interface evidence')
            parents=node['definition'].get('parents',[])
            if not ready:
                stack.append((token,True))
                stack.extend((p,False) for p in reversed(parents) if p not in self.verified)
                continue
            with self.service._phase('interface_verification'):
                result=self.service._request(dict(mode='factor_define',id=token,definition=node['definition'],lazy=True))
            self.worker=self.service.process
            native_scope=result['scope']
            if set(native_scope)!=set(node['scope']):raise ValueError('Checked factor has different scope')
            node['native_scope']=native_scope
            self.verified.add(token)
            self.metrics['native_definitions']+=1
            if token not in self.new_nodes:self.metrics['native_replays']+=1

    def check_row(self,node,index,answer):
        self.ensure(node['id'])
        key=(node['id'],index)
        if key in self.verified_rows:return
        # Native scope order need not equal the planner's sorted order.
        scope=node.get('native_scope')
        if scope is None:
            result=self.service._request(dict(mode='factor_define',id=node['id'],definition=node['definition'],lazy=True))
            scope=result['scope'];node['native_scope']=scope
        assignment={v:bool(index & (1<<(len(node['scope'])-j-1))) for j,v in enumerate(node['scope'])}
        word=''.join('1' if assignment[v] else '0' for v in scope)
        with self.service._phase('interface_verification'):
            result=self.service._request(dict(mode='factor_row',id=node['id'],row=word))
        if result['value'] is not answer:raise ValueError('Saved or proposed interface row rejected')
        self.metrics['native_row_acquisitions']+=result['acquired_rows']
        self.metrics['native_row_checks']+=1
        self.verified_rows.add(key)

    def acquire(self,node,index,depth=0):
        with self.service._phase('interface_combination'):
            return self._acquire(node,index,depth)

    def _acquire(self,node,index,depth=0):
        self.deadline.check()
        if depth>256:raise BudgetExceeded('Lazy dependency depth exceeds active cap')
        known=node['rows'][index]
        if known is not None:
            self.check_row(node,index,known)
            self.metrics['row_hits']+=1
            return known
        definition=node['definition']
        assignment={v:bool(index & (1<<(len(node['scope'])-j-1))) for j,v in enumerate(node['scope'])}
        choice=None
        if definition['kind']=='leaf':
            with self.service._phase('interface_acquisition'):
                nodes=node.get('program')
                if nodes is None:
                    nodes,_=parse_postfix(definition['bits'],self.deadline)
                    node['program']=nodes;self.metrics['parsed_nodes']+=len(nodes)
                value=evaluate(nodes,assignment)
                self.metrics['leaf_rows']+=1
        else:
            value=False
            for b in (False,True):
                assignment[definition['variable']]=b
                possible=True
                for name in definition['parents']:
                    parent=self.read(name)
                    self.metrics['table_probes']+=1
                    if not self.acquire(parent,row_index(parent['scope'],assignment),depth+1):
                        possible=False;break
                if possible:value=True;choice=b;break
            self.metrics['combination_rows']+=1
        self.check_row(node,index,value)
        node['rows'][index]=value;node['choice_values'][index]=choice
        with self.service._phase('interface_storage'),self.db:
            self.db.execute('INSERT OR IGNORE INTO interface_rows VALUES (?,?,?,?,?)',
                (self.engine,node['id'],index,int(value),None if choice is None else int(choice)))
            if all(v is not None for v in node['rows']):
                relation,raw,_=self.store.put('interface_relation',pack(node['rows']))
                evidence=dict(definition=definition,scope=node['scope'],choices=pack(node['choice_values']))
                evidence_id=self.store.put('interface_evidence',evidence)[0]
                self.db.execute('UPDATE interface_nodes SET relation=?,evidence=? WHERE engine=? AND id=?',
                    (relation,evidence_id,self.engine,node['id']))
                node['relation']=relation;self.metrics['relation_payload_bytes']+=raw
        return value

    def save(self,definition,scope,rows,choices=None):
        name=identity(definition)
        relation=pack(rows)
        node=dict(definition=definition,scope=scope,choices=pack(choices) if choices is not None else None)
        with self.service._phase('interface_storage'),self.db:
            rel,raw,_=self.store.put('interface_relation',relation)
            evidence=self.store.put('interface_evidence',node)[0]
            self.db.execute('INSERT OR IGNORE INTO interface_nodes VALUES (?,?,?,?)',(self.engine,name,evidence,rel))
        node.update(id=name,rows=rows,relation=rel,choice_values=choices if choices is not None else [None]*len(rows))
        self.new_nodes.add(name)
        self.metrics['planned_rows']+=len(rows)
        self.remember(name,node)
        # Results in this table are proposals until native checking succeeds.
        self.ensure(name)
        self.metrics['relation_payload_bytes']+=raw
        self.metrics['node_acquisitions']+=1
        return node

    def leaf(self,bits):
        nodes,_=parse_postfix(bits,self.deadline)
        self.metrics['parsed_nodes']+=len(nodes)
        scope=sorted({n[1] for n in nodes if n[0]=='var'})
        if len(scope)>self.max_interface+1:raise BudgetExceeded('Leaf exceeds interface bag cap')
        definition=dict(kind='leaf',bits=bits,scope=scope)
        found=self.read(identity(definition))
        if found is not None:
            self.metrics['node_hits']+=1;return found
        result=self.save(definition,scope,[None]*(1<<len(scope)))
        result['program']=nodes
        return result

    def constraint(self,bits):
        if not isinstance(bits,str) or any(c not in '01' for c in bits):
            raise ValueError('A constraint encoding must contain only zero and one')
        self.metrics['input_bytes']+=len(bits)
        if len(bits)>self.service.max_input_bytes:raise BudgetExceeded('Constraint exceeds input budget')
        with self.service._phase('interface_analysis'):
            groups,_,_=analyze(bits,self.deadline)
        leaves=[]
        reason=None
        try:
            for group in groups:
                for term in group['global_parts']:leaves.append(self.leaf(term)['id'])
        except BudgetExceeded as error:
            self.deadline.check();reason=str(error);leaves=[]
        with self.db:
            token=self.store.put('expansion_constraint',dict(bits=bits,leaves=leaves,fallback=reason))[0]
        if reason is None:self.bind_constraint(token)
        return token,leaves

    def bind_constraint(self,token):
        record=self.store.get(token,'expansion_constraint')
        if record.get('fallback'):raise BudgetExceeded(record['fallback'])
        for name in record['leaves']:self.ensure(name)
        if token not in self.bound:
            with self.service._phase('interface_verification'):
                checked=self.service._request(dict(mode='factor_bind',id=token,bits=record['bits'],active=record['leaves']))
            if not checked['valid']:raise ValueError('Constraint decomposition rejected')
            self.bound.add(token)
        return record['leaves']

    def eliminate(self,active,previous_order=()):
        factors={name:self.read(name) for name in active}
        if any(v is None for v in factors.values()):raise ValueError('Missing active factor')
        steps=[];order=[]
        old_order=iter(previous_order)
        while True:
            self.deadline.check()
            for q in factors.values():
                if not q['scope'] and not self.acquire(q,0):return False,None,q['id'],order
            variables=set(v for q in factors.values() for v in q['scope'])
            if not variables:break
            adjacency={v:set() for v in variables}
            for q in factors.values():
                for v in q['scope']:
                    adjacency[v].update(q['scope'])
                    self.metrics['ordering_edges']+=len(q['scope'])
            preferred=next((v for v in old_order if v in variables),None)
            with self.service._phase('interface_decomposition'):
                if preferred is not None and len(adjacency[preferred])<=self.max_interface+1:
                    variable=preferred
                else:
                    self.metrics['ordering_candidates']+=len(variables)
                    variable=min(variables,key=lambda v:(len(adjacency[v]),v))
                bag=adjacency[variable]
                if len(bag)>self.max_interface+1:raise BudgetExceeded('No small interface found within width cap')
                self.metrics['max_bag']=max(self.metrics['max_bag'],len(bag))
            bucket=[q for q in factors.values() if variable in q['scope']]
            # Equal ordered-scope relations can share behavior. Choose one proof
            # representative, but retain all acquired witnesses in the step DAG.
            unique={}
            for q in bucket:
                behavior=(tuple(q['scope']),q['relation']) if all(v is not None for v in q['rows']) else ('unknown',q['id'])
                if behavior in unique:self.metrics['semantic_duplicates']+=1
                else:unique[behavior]=q
            inputs=sorted(unique.values(),key=lambda q:q['id'])
            definition=dict(kind='project',variable=variable,parents=[q['id'] for q in inputs])
            name=identity(definition)
            with self.service._phase('interface_matching'):
                node=self.read(name)
            if node is None:
                with self.service._phase('interface_combination'):
                    scope=sorted(set(v for q in inputs for v in q['scope'])-{variable})
                    rows=[None]*(1<<len(scope));choices=[None]*len(rows)
                node=self.save(definition,scope,rows,choices)
            else:self.metrics['node_hits']+=1
            for q in bucket:del factors[q['id']]
            factors[name]=node
            order.append(variable);steps.append(node)
        assignment={}
        for node in reversed(steps):
            row=row_index(node['scope'],assignment)
            if not self.acquire(node,row):raise ValueError('Inconsistent lazy witness path')
            choice=node['choice_values'][row]
            if choice is None:raise ValueError('Unknown interface row cannot produce a witness')
            assignment[node['definition']['variable']]=choice
        witness=''.join('1' if assignment.get(i,False) else '0' for i in range(max(assignment,default=-1)+1))
        return True,witness,None,order

    def certificate(self,root):
        definitions=[];seen=set();stack=[(root,False)]
        while stack:
            name,ready=stack.pop()
            if name in seen:continue
            node=self.read(name)
            if not ready:
                stack.append((name,True));stack.extend((p,False) for p in reversed(node['definition'].get('parents',[])))
            else:
                seen.add(name);definitions.append(dict(id=name,definition=node['definition']))
        return dict(format='factor_dag',root=root,definitions=definitions)

    def run(self,active,previous_order=(),constraints=None):
        with self.service._phase('interface_planning'):
            answer,witness,root,order=self.eliminate(list(dict.fromkeys(active)),previous_order)
        if answer:
            for name in active:self.ensure(name)
        else:self.ensure(root)
        # The final context check prevents reusing a negative derivation after
        # one of its assumptions has been deleted or replaced.
        for name in active:self.ensure(name)
        with self.service._phase('interface_verification'):
            checked=self.service._request(dict(mode='factor_query_bound' if constraints is not None else 'factor_query',
                active=active,constraints=constraints,answer=answer,witness=witness,root=root))
        if not checked['valid']:raise ValueError('Checked interface answer rejected')
        certificate=None if answer else self.certificate(root)
        return dict(answer=answer,witness=witness,root=root,order=order,certificate=certificate)

    def reset_if_full(self):
        if len(self.verified)>12000 or len(self.verified_rows)>500000:
            self.service._request(dict(mode='factor_reset'))
            self.verified.clear();self.verified_rows.clear();self.bound.clear()

    def solve(self,bits):
        self.deadline=self.service._deadline or Deadline(self.service.query_timeout)
        self.metrics=counters();self.new_nodes=set();before=self.store.inserted_objects
        self.reset_if_full()
        try:
            token,active=self.constraint(bits)
            self.bind_constraint(token)
            result=self.run(active)
            with self.service._phase('interface_verification'):
                request=dict(mode='verify_witness',bits=bits,witness=result['witness']) if result['answer'] else dict(mode='verify_certificate',bits=bits,certificate=result['certificate'])
                checked=self.service._request(request)
                if not checked['valid']:raise ValueError('Original formula check rejected interface result')
        except BudgetExceeded as error:
            if self.deadline.remaining()<=0:raise
            # Width failure leaves evidence intact and delegates the original
            # query to the existing checked complete solver.
            return None,str(error),dict(self.metrics)
        self.metrics['archive_new_objects']=self.store.inserted_objects-before
        self.metrics['active_cache_nodes']=len(self.cache)
        self.metrics['unknown_rows']=sum(sum(v is None for v in q['rows']) for q in self.cache.values())
        return dict(answer=result['answer'],witness=result['witness'],certificate=result['certificate'],
            backend='interfaces',reuse_kind='witness' if result['answer'] else 'refutation',
            core_work=None,counted_work=None,counted_complete=False,nodes=None,parse_work=checked['parse_work'],
            interfaces=dict(self.metrics)),None,None

    def expand(self,base,add,remove):
        self.deadline=self.service._deadline or Deadline(self.service.query_timeout)
        self.metrics=counters();self.new_nodes=set();before=self.store.inserted_objects
        self.reset_if_full()
        root=None;previous_order=[]
        if base is not None:
            row=self.db.execute('SELECT manifest,evidence FROM expansion_states WHERE engine=? AND id=?',(self.engine,base)).fetchone()
            if row is None:raise ValueError('Unknown expansion base in this checker namespace')
            root=row['manifest'] or None
            previous_order=self.store.get(row['evidence'],'expansion_result')['order']
        if not isinstance(add,dict) or not isinstance(remove,list):raise ValueError('Expansion requires add map and remove list')
        if len(add)+len(remove)>4096:raise BudgetExceeded('Expansion delta too large')
        if any(not isinstance(k,str) or not k or len(k)>256 for k in list(add)+remove):raise ValueError('Invalid constraint name')
        if set(add)&set(remove) or len(set(remove))!=len(remove):raise ValueError('Conflicting expansion delta')
        manifest=Manifest(self.store,self.deadline,self.metrics)
        # Valid partial evidence may commit even if the entire expansion fails;
        # an answer snapshot is committed only after native verification.
        for name in remove:
            with self.db:root=manifest.update(root,name,None)
        for name,bits in add.items():
            token,_=self.constraint(bits)
            with self.db:root=manifest.update(root,name,token)
        active=[];constraints=[token for _,token in manifest.items(root)]
        try:
            for token in constraints:active.extend(self.bind_constraint(token))
            result=self.run(list(dict.fromkeys(active)),previous_order,constraints)
        except BudgetExceeded as error:
            self.deadline.check()
            bits=conjunction([self.store.get(t,'expansion_constraint')['bits'] for t in constraints])
            if len(bits)>self.service.max_input_bytes:raise BudgetExceeded('Fallback reconstruction exceeds input cap')
            result=self.service._fast_live(bits,allow_components=False,allow_interfaces=False)
            result.update(root=None,order=[],fallback_reason=str(error))
        self.metrics['archive_new_objects']=self.store.inserted_objects-before
        self.metrics['active_cache_nodes']=len(self.cache)
        self.metrics['unknown_rows']=sum(sum(v is None for v in q['rows']) for q in self.cache.values())
        with self.service._phase('interface_storage'),self.db:
            evidence=self.store.put('expansion_result',result)[0]
            state=identity(dict(engine=self.engine,manifest=root))
            self.db.execute('INSERT OR IGNORE INTO expansion_states VALUES (?,?,?,?,?,?)',
                (self.engine,state,root or '',int(result['answer']),evidence,time.time_ns()))
        return dict(state=state,answer=result['answer'],witness=result['witness'],source='interface_expansion',fallback_reason=result.get('fallback_reason'),
                    interfaces=dict(self.metrics),counted_complete=False)
