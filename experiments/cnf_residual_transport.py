"""Bounded untrusted variable-map hints; native proofs remain the authority.

The search visit is the native visit with a scoped normalization-map stack.
Only order-preserving variable transport and whole-clause containment are tried.
Metadata is committed separately, after the native batch is idle; a hint can
never authenticate a verdict or lift a branch assumption to its parent.
"""
from collections import Counter
import hashlib,json,sys,time
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_canonical_verify import canonical_certificate
from experiments.cnf_residual_dag import FORMAT
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_partial_residual_pool import charge

TABLE='cnf_residual_transport_hints_v1'


class ResidualTransportSolver(InputSafeAffineProbeSolver):
    def __init__(self,*args,transport=True,transport_capacity=32,transport_bytes=512*1024,
                 transport_stage_limit=32,transport_probes=32,transport_candidates=4,
                 transport_literals=1024,transport_variables=256,transport_depth=128,
                 transport_map_bytes=512*1024,**kwargs):
        limits=(transport_capacity,transport_bytes,transport_stage_limit,transport_probes,
                transport_candidates,transport_literals,transport_variables,transport_depth,transport_map_bytes)
        if type(transport) is not bool or any(type(v) is not int or v<1 for v in limits):
            raise ValueError('Invalid transport limits')
        self.transport=transport;self.transport_capacity=transport_capacity;self.transport_bytes=transport_bytes
        self.transport_stage_limit=transport_stage_limit;self.transport_probes=transport_probes
        self.transport_candidates=transport_candidates;self.transport_literals=transport_literals
        self.transport_variables=transport_variables;self.transport_depth=transport_depth
        self.transport_map_bytes=transport_map_bytes
        self.transport_pool={};self._transport_charge=0;self._transport_stage={};self._stage_charge=0
        self._transport_stack=[];self._map_charge=0;self._root_names=None;self._capture_root=False
        self._transport_probes=0;self._transport_staged=0;self.transport_publication_hook=None
        super().__init__(*args,**kwargs);began=time.perf_counter();before=Counter(self.counts)
        try:
            with self.db:self.db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            # IDs and SQL length metadata precede payload decoding. Inspection
            # itself can touch pages and is not a total storage-I/O bound.
            rows=self.db.execute(f'SELECT rowid,id,length(CAST(payload AS BLOB)) FROM {TABLE} ORDER BY rowid DESC LIMIT ?',
                                 (transport_capacity,)).fetchall()
            for rowid,key,size in reversed(rows):
                self.counts['transport_seed_rows']+=1
                if size>65536:self.counts['transport_seed_size_skips']+=1;continue
                payload=self.db.execute(f'SELECT payload FROM {TABLE} WHERE rowid=?',(rowid,)).fetchone()[0]
                self.counts['transport_seed_bytes']+=size
                try:entry=self._decode_hint(key,payload)
                except (ValueError,TypeError,KeyError,IndexError):
                    self.counts['transport_invalid_hints']+=1;continue
                self._transport_charge=self._bounded_add(self.transport_pool,self._transport_charge,key,entry)
            self.transport_setup_counts=dict(self.counts-before)
            self.transport_setup_seconds=time.perf_counter()-began
        except BaseException:self.close();raise

    def _canonical(self,cnf):
        result=super()._canonical(cnf)
        if self._capture_root:
            self._capture_root=False;names=result[1]
            # This is the outer source canonicalization, before any checker or
            # quotient traversal. Huge/sparse integer input remains valid SAT.
            if len(names)<=self.transport_variables and all(v.bit_length()<=64 for v in names):
                self._root_names=names
        return result

    def _bounded_add(self,pool,total,key,entry):
        if key in pool:return total
        pool[key]=entry;total+=entry['charge']
        while pool and (len(pool)>self.transport_capacity or total+sys.getsizeof(pool)>self.transport_bytes):
            old=next(iter(pool));total-=pool.pop(old)['charge'];self.counts['transport_evictions']+=1
        return total

    def _entry(self,origin,names,cnf,payload):
        if not names or len(names)>self.transport_variables or any(type(v) is not int or v<1 or v.bit_length()>64 for v in names):
            raise ValueError('Invalid transport names')
        if any(a>=b for a,b in zip(names,names[1:])):raise ValueError('Transport must preserve order')
        if not cnf or () in cnf or sum(map(len,cnf))>self.transport_literals:
            raise ValueError('Ineligible hint CNF')
        if max(abs(l) for cl in cnf for l in cl)!=len(names):raise ValueError('Map arity mismatch')
        variables=names if self.transport else tuple(range(1,len(names)+1))
        clauses=tuple(tuple((1 if l>0 else -1)*variables[abs(l)-1] for l in cl) for cl in cnf)
        anchor=min(clauses,key=lambda cl:(-len(cl),cl))
        key=hashlib.sha256(payload.encode()).hexdigest()
        entry=dict(origin=origin,names=names,clauses=clauses,anchor=anchor,payload=payload,charge=0)
        entry['charge']=charge((key,entry));return key,entry

    def _decode_hint(self,key,payload):
        if hashlib.sha256(payload.encode()).hexdigest()!=key:raise ValueError('Hint hash mismatch')
        hint=json.loads(payload);origin=hint['origin'];names=tuple(hint['names'])
        if type(origin) is not str or not origin.startswith(FORMAT+':'):raise ValueError('Invalid origin key')
        cnf,_,expected=canonical_certificate(json.loads(origin[len(FORMAT)+1:]),self.counts)
        if expected!=origin:raise ValueError('Noncanonical hint origin')
        actual,entry=self._entry(origin,names,cnf,payload)
        if actual!=key:raise ValueError('Changed hint identity')
        return entry

    def _stage_transport(self,key,node,names):
        if names is None or node['answer'] or self._transport_staged>=self.transport_stage_limit:return
        proof=node['proof'];kind=proof['kind']
        if not (kind in ('split','component','positive-subsumption-v1') or kind=='units' and 'child' in proof):return
        cnf=tuple(tuple(c) for c in node['cnf']);literals=sum(map(len,cnf))
        self.counts['transport_admission_literals']+=literals
        if not names or () in cnf or literals>self.transport_literals:return
        payload=json.dumps(dict(origin=key,names=names),sort_keys=True,separators=(',',':'))
        if len(payload.encode())>65536:return
        hint,entry=self._entry(key,names,cnf,payload)
        if hint in self.transport_pool or hint in self._transport_stage:return
        self._transport_staged+=1;self.counts['transport_staged']+=1
        self._stage_charge=self._bounded_add(self._transport_stage,self._stage_charge,hint,entry)
        self.counts['transport_stage_peak_bytes']=max(self.counts['transport_stage_peak_bytes'],
            self._stage_charge+sys.getsizeof(self._transport_stage) if self._transport_stage else 0)

    def _finish_transport(self):
        if self.db.active or self.db.in_transaction or self.db.poisoned:raise RuntimeError('Transport admission requires committed state')
        pool=dict(self.transport_pool);total=self._transport_charge
        for key,entry in self._transport_stage.items():
            self.counts['transport_commit_lookups']+=1
            if self.db.execute('SELECT 1 FROM cnf_residual_v1 WHERE id=?',(entry['origin'],)).fetchone() is None:
                self.counts['transport_rolled_back_hints']+=1;continue
            total=self._bounded_add(pool,total,key,entry)
        # Hint metadata is mutable and bounded, separate from append-only proofs.
        # The previous memory snapshot remains in place if this transaction fails.
        rows={key for key, in self.db.execute(f'SELECT id FROM {TABLE}')}
        removed=rows-pool.keys();added=pool.keys()-rows
        if removed or added:
            with self.db:
                for key in sorted(removed):self.db.execute(f'DELETE FROM {TABLE} WHERE id=?',(key,))
                for key,entry in pool.items():
                    if key in added:
                        self.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)',(key,entry['payload']))
                        self.counts['transport_metadata_written_bytes']+=len(key)+len(entry['payload'].encode())
                if self.transport_publication_hook is not None:self.transport_publication_hook('before_commit')
            self.counts['transport_metadata_commits']+=1
        self.transport_pool=pool;self._transport_charge=total

    def _visit(self,cnf):
        # Native visit semantics are unchanged; maps live only on search edges,
        # never on nested certificate-checker _canonical calls.
        self.counts['visits']+=1;normalized,names,key=self._canonical(cnf)
        parent=self._transport_stack[-1] if self._transport_stack else self._root_names
        mapping=None;size=0
        if parent is not None and len(self._transport_stack)<self.transport_depth:
            mapping=tuple(parent[v-1] for v in names)
            size=sys.getsizeof(mapping)+sum(sys.getsizeof(v) for v in mapping)
            self.counts['transport_composed_variables']+=len(names)
            if self._map_charge+size>self.transport_map_bytes:mapping=None;size=0
        self._transport_stack.append(mapping);self._map_charge+=size
        self.counts['transport_map_peak_bytes']=max(self.counts['transport_map_peak_bytes'],self._map_charge)
        try:
            node=self._read(key,normalized) if self.reuse else None
            if node is None:
                if self.counts['expanded_nodes']>=self.node_limit:raise RuntimeError(BUDGET_MESSAGE)
                self.counts['expanded_nodes']+=1;model,proof=self._expand(normalized)
                node=dict(format=FORMAT,cnf=[list(c) for c in normalized],answer=model is not None)
                if model is not None:
                    local_count=max((abs(l) for c in normalized for l in c),default=0)
                    node['model']=[model.get(i,False) for i in range(1,local_count+1)]
                else:node['proof']=proof
                self._store(key,node)
            self._stage_transport(key,node,mapping)
            model={old:node['model'][i] for i,old in enumerate(names)} if node['answer'] else None
            return model,key
        finally:self._transport_stack.pop();self._map_charge-=size

    def _transport_reuse(self,cnf):
        if not self.transport_pool or not cnf or () in cnf or self._transport_probes>=self.transport_probes:return None
        mapping=self._transport_stack[-1] if self._transport_stack else None
        if mapping is None:return None
        self._transport_probes+=1;self.counts['transport_probes']+=1
        variables=mapping if self.transport else tuple(range(1,len(mapping)+1))
        positions={tuple((1 if l>0 else -1)*variables[abs(l)-1] for l in cl):i for i,cl in enumerate(cnf)}
        self.counts['transport_target_literals']+=sum(map(len,cnf));tried=0
        for entry in reversed(self.transport_pool.values()):
            self.counts['transport_index_entries']+=1
            if entry['anchor'] not in positions:continue
            tried+=1;self.counts['transport_candidates']+=1;contained=True
            for clause in entry['clauses']:
                self.counts['transport_containment_clauses']+=1
                if clause not in positions:contained=False;break
            if contained:
                ids=sorted(positions[cl] for cl in entry['clauses'])
                small,_,child=self._canonical([cnf[i] for i in ids])
                if child!=entry['origin']:raise ValueError('Transport changed native proof identity')
                node=self._read(child,small,purpose='transport_origin')
                if node is None:self.counts['transport_stale_hints']+=1
                elif node['answer']:self.counts['transport_positive_hints']+=1
                else:
                    self.counts['transport_hits']+=1
                    if node['cnf']==[list(cl) for cl in cnf]:return node['proof']
                    return dict(kind='component',clauses=ids,child=child)
            if tried==self.transport_candidates:break
        return None

    def _expand(self,cnf):
        proof=self._transport_reuse(cnf)
        return (None,proof) if proof is not None else super()._expand(cnf)

    def solve(self,source):
        if self._transport_stack:raise RuntimeError('Reentrant transport query')
        began=time.perf_counter();self._root_names=None;self._capture_root=True
        self._transport_probes=0;self._transport_staged=0;result=None;stopped=False
        try:
            result=super().solve(source);return result
        except RuntimeError as error:stopped=str(error)==BUDGET_MESSAGE;raise
        finally:
            self._capture_root=False
            try:
                if result is not None or stopped:self._finish_transport()
            finally:
                self._transport_stage={};self._stage_charge=0;self._root_names=None
                self.counts['transport_retained_entries']=len(self.transport_pool)
                self.counts['transport_retained_bytes']=self._transport_charge+sys.getsizeof(self.transport_pool) if self.transport_pool else 0
                if result is not None:result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
