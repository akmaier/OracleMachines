"""Checked, persistent variable elimination with small local interfaces.

The Python planner and saved tables are untrusted. Every new/replayed factor is
checked by the native engine; SAT is checked on all active original constraints,
and UNSAT needs an empty relation whose checked source leaves remain active.
All graph objects are immutable. Fallback handles instances exceeding width caps.
"""
from solver.active_cache import PayloadCache
from contextlib import contextmanager
from functools import wraps
import hashlib
import json
import time

from solver.components import analyze, conjunction
from solver.incremental import parse_postfix
from solver.knowledge_store import KnowledgeStore
from solver.relations import assignments, row_index, pack, unpack, project
from solver.manifests import Manifest
from solver import planning
from solver.plan_indexes import Sources, Order
from solver.symbolic import BDD
from solver.resources import BudgetExceeded, Deadline


def batched(method):
    """Commit one checked interface operation; discard volatile proposals on rollback."""
    @wraps(method)
    def run(self, *args, **kwargs):
        original=self.service._deadline
        speculative=method.__name__=='solve'
        if speculative:
            remaining=original.remaining() if original else self.service.query_timeout
            self.service._deadline=Deadline(min(1.0,remaining*0.4))
        try:
            with self.service._phase('interface_commit'), self.db:
                self.batch_depth += 1
                try:return method(self, *args, **kwargs)
                finally:self.batch_depth -= 1
        except BaseException as error:
            self.cache.clear()
            self.symbolic_roots.clear()
            if speculative and isinstance(error,BudgetExceeded):
                if original:original.check()
                return None,str(error),dict(self.metrics)
            raise
        finally:
            self.service._deadline=original
    return run


def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def counters():
    return dict(input_bytes=0,parsed_nodes=0,leaf_rows=0,combination_rows=0,table_probes=0,
        node_hits=0,node_acquisitions=0,native_definitions=0,native_replays=0,native_rows=0,
        ordering_candidates=0,ordering_edges=0,max_bag=0,manifest_reads=0,manifest_writes=0,
        semantic_duplicates=0,relation_payload_bytes=0,archive_new_objects=0,row_hits=0,native_row_acquisitions=0,native_row_checks=0,
        planned_rows=0,unknown_rows=0,active_cache_nodes=0,planned_buckets=0,
        affected_buckets=0,reused_buckets=0,propagation_stops=0,dependency_updates=0,
        plan_copy_entries=0,source_comparisons=0,source_delta_reads=0,constant_delta_reads=0,plan_rebuilds=0,
        symbolic_operations=0,symbolic_nodes=0,symbolic_hits=0,symbolic_replays=0,
        symbolic_rows=0,symbolic_fallbacks=0,symbolic_collected_nodes=0,
        preflight_rejected=0,preflight_buckets=0,native_definition_batches=0)


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
    def __init__(self,service,max_interface=3,active_nodes=1024,symbolic=False):
        if not 0<=max_interface<=10:raise ValueError('Interface cap must be between zero and ten')
        self.service=service
        self.db=service.db
        self.store=KnowledgeStore(self.db,service.engine_id)
        self.engine=service.engine_id
        self.max_interface=max_interface
        self.active_nodes=active_nodes
        self.cache=PayloadCache(service.active_cache_bytes,active_nodes)
        self.verified=set()
        self.worker=None
        self.bound=set()
        self.verified_rows=set()
        self.metrics=counters()
        self.deadline=None
        self.symbolic=symbolic
        self.bdd=BDD(max_nodes=service.symbolic_node_limit)
        self.symbolic_roots={}
        self.symbolic_disabled=False
        self.batch_depth=0

    @contextmanager
    def transaction(self):
        if self.batch_depth:
            yield
        else:
            with self.db:yield

    def begin_symbolic(self):
        self.cache.refresh()
        # Every retained symbolic proposal is durable; trimming active roots is safe.
        if len(self.symbolic_roots)>self.active_nodes:
            self.symbolic_roots=dict(list(self.symbolic_roots.items())[-self.active_nodes:])
        self.bdd.begin(self.deadline)
        if len(self.bdd.nodes)>self.bdd.max_nodes//2:
            before=len(self.bdd.nodes)
            self.symbolic_roots=self.bdd.collect(self.symbolic_roots)
            self.metrics['symbolic_collected_nodes']+=before-len(self.bdd.nodes)
        self.symbolic_disabled=False

    def symbolic_root(self,node,depth=0):
        if depth>256:raise BudgetExceeded('Symbolic dependency depth exceeded')
        token=node['id']
        if token in self.symbolic_roots:return self.symbolic_roots[token]
        saved=self.db.execute('SELECT object_id FROM interface_symbolic WHERE engine=? AND id=?',
            (self.engine,token)).fetchone()
        if saved:
            root=self.bdd.restore(self.store.get(saved[0],'symbolic_relation'))
            self.metrics['symbolic_replays']+=1
        else:
            definition=node['definition']
            if definition['kind']=='leaf':
                program=node.get('program')
                if program is None:
                    program,_=parse_postfix(definition['bits'],self.deadline)
                    self.metrics['parsed_nodes']+=len(program)
                root=self.bdd.formula(program)
            else:
                root=1
                parents=definition['parents']
                for parent in parents[:-1]:
                    root=self.bdd.apply('and',root,self.symbolic_root(self.read(parent),depth+1))
                last=self.symbolic_root(self.read(parents[-1]),depth+1) if parents else 1
                root=self.bdd.and_exists(root,last,(definition['variable'],))
            with self.service._phase('interface_storage'),self.transaction():
                obj=self.store.put('symbolic_relation',self.bdd.dump(root))[0]
                self.db.execute('INSERT OR IGNORE INTO interface_symbolic VALUES (?,?,?)',(self.engine,token,obj))
        if len(self.symbolic_roots)>=self.active_nodes:self.symbolic_roots.clear()
        self.symbolic_roots[token]=root
        return root

    def symbolic_row(self,node,assignment):
        root=self.symbolic_root(node)
        value=self.bdd.evaluate(root,assignment)
        choice=None
        if value and node['definition']['kind']=='project':
            assignment=dict(assignment)
            variable=node['definition']['variable']
            for b in (False,True):
                assignment[variable]=b
                if all(self.bdd.evaluate(self.symbolic_root(self.read(p)),assignment)
                       for p in node['definition']['parents']):
                    choice=b;break
            if choice is None:raise ValueError('Symbolic projection has no supporting branch')
        self.metrics['symbolic_rows']+=1
        return value,choice

    def finish_symbolic(self):
        self.cache.refresh()
        self.metrics.update(symbolic_operations=self.bdd.work,symbolic_nodes=len(self.bdd.nodes),
                            symbolic_hits=self.bdd.hits)

    def remember(self,name,node):
        self.cache[name]=node
        if name in self.cache:self.cache.move_to_end(name)
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
        stack=[(name,False)];pending=[];scheduled=set()
        while stack:
            self.deadline.check()
            token,ready=stack.pop()
            if token in self.verified or token in scheduled:continue
            node=self.read(token)
            if node is None:raise ValueError('Missing interface evidence')
            parents=node['definition'].get('parents',[])
            if not ready:
                stack.append((token,True))
                stack.extend((p,False) for p in reversed(parents) if p not in self.verified)
                continue
            pending.append(node);scheduled.add(token)
        for offset in range(0,len(pending),128):
            batch=pending[offset:offset+128]
            with self.service._phase('interface_verification'):
                response=self.service._request(dict(mode='factor_define_many',definitions=[
                    dict(id=node['id'],definition=node['definition'],lazy=True) for node in batch]))
            results=response['results']
            if len(results)!=len(batch):raise ValueError('Incomplete native definition batch')
            self.worker=self.service.process
            self.metrics['native_definition_batches']+=1
            for node,result in zip(batch,results):
                token=node['id'];native_scope=result['scope']
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
        symbolic_result=None
        if self.symbolic and not self.symbolic_disabled:
            try:
                with self.service._phase('interface_symbolic'):
                    symbolic_result=self.symbolic_row(node,assignment)
            except (BudgetExceeded,RecursionError):
                self.deadline.check()
                self.symbolic_disabled=True;self.metrics['symbolic_fallbacks']+=1
        if symbolic_result is not None:
            value,choice=symbolic_result
        elif definition['kind']=='leaf':
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
        with self.service._phase('interface_storage'),self.transaction():
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
        with self.service._phase('interface_storage'),self.transaction():
            rel,raw,_=self.store.put('interface_relation',relation)
            evidence=self.store.put('interface_evidence',node)[0]
            self.db.execute('INSERT OR IGNORE INTO interface_nodes VALUES (?,?,?,?)',(self.engine,name,evidence,rel))
        node.update(id=name,rows=rows,relation=rel,choice_values=choices if choices is not None else [None]*len(rows))
        self.new_nodes.add(name)
        self.metrics['planned_rows']+=len(rows)
        self.remember(name,node)
        # Results in this table are proposals until native checking succeeds.
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

    def constraint(self,bits,groups=None):
        if not isinstance(bits,str) or any(c not in '01' for c in bits):
            raise ValueError('A constraint encoding must contain only zero and one')
        self.metrics['input_bytes']+=len(bits)
        if len(bits)>self.service.max_input_bytes:raise BudgetExceeded('Constraint exceeds input budget')
        if groups is None:
            with self.service._phase('interface_analysis'):
                groups,_,_=analyze(bits,self.deadline)
        leaves=[]
        reason=None
        try:
            for group in groups:
                for term in group['global_parts']:leaves.append(self.leaf(term)['id'])
        except BudgetExceeded as error:
            self.deadline.check();reason=str(error);leaves=[]
        with self.transaction():
            token=self.store.put('expansion_constraint',dict(bits=bits,leaves=leaves,fallback=reason))[0]
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

    def project_node(self,variable,names):
        bucket=[self.read(name) for name in names]
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
            scope=sorted(set(v for q in inputs for v in q['scope'])-{variable})
            node=self.save(definition,scope,[None]*(1<<len(scope)))
        else:self.metrics['node_hits']+=1
        return name

    def eliminate(self,active,previous_order=(),previous_plan=None):
        with self.service._phase('interface_decomposition'):
            if previous_plan is not None:
                try:
                    plan=planning.update(previous_plan,active,self.read,self.project_node,
                        self.max_interface,self.deadline,self.metrics)
                except BudgetExceeded:
                    self.deadline.check()
                    self.metrics['plan_rebuilds']+=1
                    plan=planning.build(active,self.read,self.project_node,
                        self.max_interface,self.deadline,self.metrics)
            else:
                plan=planning.build(active,self.read,self.project_node,
                    self.max_interface,self.deadline,self.metrics,previous_order)
        self.current_plan=plan
        for name in plan['constants']:
            self.ensure(name)
            if not self.acquire(self.read(name),0):return False,None,name,plan['order']
        assignment={}
        for variable in reversed(plan['order']):
            token=plan['buckets'].get(str(variable),{}).get('output')
            if token is None:continue
            node=self.read(token)
            row=row_index(node['scope'],assignment)
            if not self.acquire(node,row):raise ValueError('Inconsistent lazy witness path')
            choice=node['choice_values'][row]
            if choice is None:raise ValueError('Unknown interface row cannot produce a witness')
            assignment[variable]=choice
        witness=''.join('1' if assignment.get(i,False) else '0' for i in range(max(assignment,default=-1)+1))
        return True,witness,None,plan['order']

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

    def run(self,active,previous_order=(),constraints=None,previous_plan=None):
        with self.service._phase('interface_planning'):
            answer,witness,root,order=self.eliminate(active if isinstance(active,Sources) else list(dict.fromkeys(active)),previous_order,previous_plan)
        if answer:
            for name in active:self.ensure(name)
        else:self.ensure(root)
        if constraints is not None:
            for token in constraints:self.bind_constraint(token)
        # The final context check prevents reusing a negative derivation after
        # one of its assumptions has been deleted or replaced.
        for name in active:self.ensure(name)
        with self.service._phase('interface_verification'):
            checked=self.service._request(dict(mode='factor_query_bound' if constraints is not None else 'factor_query',
                active=list(active),constraints=constraints,answer=answer,witness=witness,root=root))
        if not checked['valid']:raise ValueError('Checked interface answer rejected')
        certificate=None if answer else self.certificate(root)
        return dict(answer=answer,witness=witness,root=root,order=[] if isinstance(order,Order) else order,certificate=certificate)

    def reset_if_full(self):
        if len(self.verified)>12000 or len(self.verified_rows)>500000:
            self.service._request(dict(mode='factor_reset'))
            self.verified.clear();self.verified_rows.clear();self.bound.clear()

    def preflight(self,bits):
        """Bounded, write-free simulation of the same width heuristic.

        Failure means route to a checked fallback, never a SAT/UNSAT claim.
        The speculative planner receives at most 20% of remaining query time.
        """
        local=Deadline(min(0.25,self.deadline.remaining()*0.2))
        metrics=counters();factors={}
        with self.service._phase('interface_preflight'):
            try:
                groups,_,_=analyze(bits,local)
                for group in groups:
                    for term in group['global_parts']:
                        nodes,_=parse_postfix(term,local)
                        scope=sorted({n[1] for n in nodes if n[0]=='var'})
                        if len(scope)>self.max_interface+1:
                            raise BudgetExceeded('Preflight leaf exceeds interface cap')
                        factors[str(len(factors))]=dict(scope=scope)
                def project_scope(variable,names):
                    key=str(len(factors))
                    factors[key]=dict(scope=sorted({v for n in names for v in factors[n]['scope']}-{variable}))
                    return key
                planning.build(list(factors),factors.get,project_scope,self.max_interface,local,metrics)
                self.metrics['preflight_buckets']=metrics['planned_buckets']
                return groups
            except BudgetExceeded:
                self.metrics['preflight_rejected']+=1
                self.deadline.check()
                raise BudgetExceeded('Structural preflight rejected or exhausted its reserved budget')

    @batched
    def solve(self,bits):
        self.deadline=self.service._deadline or Deadline(self.service.query_timeout)
        self.metrics=counters();self.new_nodes=set();before=self.store.inserted_objects
        self.reset_if_full()
        self.begin_symbolic()
        try:
            groups=self.preflight(bits)
            token,active=self.constraint(bits,groups)
            record=self.store.get(token,'expansion_constraint')
            if record.get('fallback'):raise BudgetExceeded(record['fallback'])
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
        self.finish_symbolic()
        self.metrics['archive_new_objects']=self.store.inserted_objects-before
        self.metrics['active_cache_nodes']=len(self.cache)
        self.metrics['unknown_rows']=sum(sum(v is None for v in q['rows']) for q in self.cache.values())
        return dict(answer=result['answer'],witness=result['witness'],certificate=result['certificate'],
            backend='interfaces',reuse_kind='witness' if result['answer'] else 'refutation',
            core_work=None,counted_work=None,counted_complete=False,nodes=None,parse_work=checked['parse_work'],
            interfaces=dict(self.metrics)),None,None

    @batched
    def expand(self,base,add,remove):
        self.deadline=self.service._deadline or Deadline(self.service.query_timeout)
        self.metrics=counters();self.new_nodes=set();before=self.store.inserted_objects
        self.reset_if_full()
        self.begin_symbolic()
        root=None;previous_order=[];previous_plan=None
        if base is not None:
            row=self.db.execute('SELECT manifest,evidence FROM expansion_states WHERE engine=? AND id=?',(self.engine,base)).fetchone()
            if row is None:raise ValueError('Unknown expansion base in this checker namespace')
            root=row['manifest'] or None
            previous_result=self.store.get(row['evidence'],'expansion_result')
            previous_order=previous_result['order']
            if previous_result.get('plan'):
                previous_plan=planning.load_plan(previous_result['plan'],self.store,self.deadline,self.metrics)
        if not isinstance(add,dict) or not isinstance(remove,list):raise ValueError('Expansion requires add map and remove list')
        if len(add)+len(remove)>4096:raise BudgetExceeded('Expansion delta too large')
        if any(not isinstance(k,str) or not k or len(k)>256 for k in list(add)+remove):raise ValueError('Invalid constraint name')
        if set(add)&set(remove) or len(set(remove))!=len(remove):raise ValueError('Conflicting expansion delta')
        manifest=Manifest(self.store,self.deadline,self.metrics)
        sources=previous_plan['active'].fork() if previous_plan and isinstance(previous_plan['active'],Sources) else None
        def change_sources(token,delta):
            if sources is None or token is None:return
            record=self.store.get(token,'expansion_constraint')
            if record.get('fallback'):raise ValueError('Fallback constraint in indexed plan')
            for leaf in record['leaves']:sources.change(leaf,delta)
        for name in remove:
            old=manifest.get(root,name)
            change_sources(old,-1)
            root=manifest.update(root,name,None)
        for name,bits in add.items():
            old=manifest.get(root,name)
            token,_=self.constraint(bits)
            record=self.store.get(token,'expansion_constraint')
            # A new unsupported factor makes this update use the complete path.
            if record.get('fallback'):sources=None
            if token!=old:
                change_sources(old,-1);change_sources(token,1)
                root=manifest.update(root,name,token)
        constraints=[token for _,token in manifest.items(root)]
        try:
            if sources is None:
                sources=Sources(manifest)
                for token in constraints:
                    record=self.store.get(token,'expansion_constraint')
                    if record.get('fallback'):raise BudgetExceeded(record['fallback'])
                    for leaf in record['leaves']:sources.change(leaf,1)
                # Legacy plans must compare their old sources during migration.
                if previous_plan is not None:previous_plan=None
            result=self.run(sources,previous_order,constraints,previous_plan)
            with self.service._phase('interface_storage'),self.transaction():
                result['plan']=planning.save_plan(self.current_plan,self.store,self.deadline,self.metrics)
        except BudgetExceeded as error:
            self.deadline.check()
            bits=conjunction([self.store.get(t,'expansion_constraint')['bits'] for t in constraints])
            if len(bits)>self.service.max_input_bytes:raise BudgetExceeded('Fallback reconstruction exceeds input cap')
            result=self.service._live(bits,mode="baseline") if self.service.backend=="lean" else self.service._fast_live(bits,allow_components=False,allow_interfaces=False)
            result.update(root=None,order=[],fallback_reason=str(error))
        self.finish_symbolic()
        self.metrics['archive_new_objects']=self.store.inserted_objects-before
        self.metrics['active_cache_nodes']=len(self.cache)
        self.metrics['unknown_rows']=sum(sum(v is None for v in q['rows']) for q in self.cache.values())
        with self.service._phase('interface_storage'),self.transaction():
            evidence=self.store.put('expansion_result',result)[0]
            state=identity(dict(engine=self.engine,manifest=root))
            self.db.execute('INSERT OR IGNORE INTO expansion_states VALUES (?,?,?,?,?,?)',
                (self.engine,state,root or '',int(result['answer']),evidence,time.time_ns()))
        return dict(state=state,answer=result['answer'],witness=result['witness'],source='interface_expansion',fallback_reason=result.get('fallback_reason'),
                    interfaces=dict(self.metrics),counted_complete=False)
