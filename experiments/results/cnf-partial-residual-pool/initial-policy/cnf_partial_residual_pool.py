"""Bounded hints from committed native residual proofs, never source verdicts.

Two retained source clauses index each candidate in compact coordinates. A hit
still requires the original native negative proof and exact target containment;
one absent clause may trigger one bounded causal plan per query. Archive-tail
admission happens only after a completed query or a native budget stop.
"""
from collections import Counter
import json,sys,time
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import FORMAT
from experiments.cnf_support_plan import CausalPlan,PlanBudget,SupportBudget
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE


def charge(value):
    seen=set()
    def visit(x):
        if id(x) in seen:return 0
        seen.add(id(x));size=sys.getsizeof(x)
        if isinstance(x,dict):return size+sum(visit(k)+visit(v) for k,v in x.items())
        if isinstance(x,(tuple,list,set,frozenset)):return size+sum(visit(v) for v in x)
        return size
    return visit(value)


class PartialResidualSolver(InputSafeAffineProbeSolver):
    def __init__(self,*args,partial_capacity=64,partial_literals=1024,partial_bytes=512*1024,
                 partial_rows=64,partial_row_bytes=256*1024,partial_probes=32,partial_candidates=4,
                 partial_support_nodes=32,partial_support_literals=8192,partial_plan_bytes=128*1024,**kwargs):
        limits=(partial_capacity,partial_literals,partial_bytes,partial_rows,partial_row_bytes,
                partial_probes,partial_candidates,partial_support_nodes,partial_support_literals,partial_plan_bytes)
        if any(type(v) is not int or v<1 for v in limits):raise ValueError('Invalid partial residual limits')
        self.partial_capacity=partial_capacity;self.partial_literals=partial_literals;self.partial_bytes=partial_bytes
        self.partial_rows=partial_rows;self.partial_row_bytes=partial_row_bytes
        self.partial_probes=partial_probes;self.partial_candidates=partial_candidates
        self.partial_support_nodes=partial_support_nodes;self.partial_support_literals=partial_support_literals
        self.partial_plan_bytes=partial_plan_bytes
        self.partial_pool={};self.partial_index={};self._partial_charge=0;self._partial_cursor=0
        self._partial_probes=0;self._partial_support_used=False
        super().__init__(*args,**kwargs);before=Counter(self.counts);began=time.perf_counter()
        try:self._refresh_partial()
        except BaseException:self.close();raise
        self.partial_setup_counts=dict(self.counts-before);self.partial_setup_seconds=time.perf_counter()-began

    def _partial_size(self):
        # Index keys can outlive the entry that first supplied their tuple.
        # Charge each anchor independently rather than assume that sharing lasts.
        return self._partial_charge+sys.getsizeof(self.partial_pool)+sys.getsizeof(self.partial_index)+sum(charge(k)+sys.getsizeof(v) for k,v in self.partial_index.items())

    def _evict_partial(self,key):
        entry=self.partial_pool.pop(key);self._partial_charge-=entry['charge']
        for anchor in entry['anchors']:
            bucket=self.partial_index[anchor];del bucket[key]
            if not bucket:del self.partial_index[anchor]

    def _hint(self,key,payload):
        c=self.counts
        try:
            node=json.loads(payload)
            if type(node) is not dict or node.get('format')!=FORMAT or node.get('answer') is not False:return
            clauses=node['cnf']
            if (type(clauses) is not list or not clauses or any(type(cl) is not list or not cl for cl in clauses)
                    or any(type(l) is not int or l==0 for cl in clauses for l in cl)):
                c['partial_invalid_hints']+=1;return
            literals=sum(map(len,clauses));c['partial_admission_literals']+=literals
            if literals>self.partial_literals:c['partial_literal_skips']+=1;return
            members=frozenset(tuple(cl) for cl in clauses)
            anchors=tuple(sorted(members,key=lambda cl:(-len(cl),cl))[:2])
        except (KeyError,TypeError,ValueError):c['partial_invalid_hints']+=1;return
        if key in self.partial_pool:self._evict_partial(key)
        entry=dict(clauses=members,anchors=anchors,charge=0);entry['charge']=charge((key,entry))
        self.partial_pool[key]=entry;self._partial_charge+=entry['charge']
        for anchor in anchors:self.partial_index.setdefault(anchor,{})[key]=None
        while self.partial_pool and (len(self.partial_pool)>self.partial_capacity or self._partial_size()>self.partial_bytes):
            self._evict_partial(next(iter(self.partial_pool)));c['partial_evictions']+=1
        c['partial_admissions']+=int(key in self.partial_pool)
        c['partial_peak_bytes']=max(c['partial_peak_bytes'],self._partial_size() if self.partial_pool else 0)
        c['partial_peak_entries']=max(c['partial_peak_entries'],len(self.partial_pool))

    def _refresh_partial(self):
        if self.db.active or self.db.in_transaction or self.db.poisoned:raise RuntimeError('Partial admission requires committed state')
        c=self.counts;c['partial_tail_queries']+=1
        rows=self.db.execute('SELECT rowid,length(CAST(id AS BLOB)),length(CAST(payload AS BLOB)) FROM cnf_residual_v1 WHERE rowid>? ORDER BY rowid DESC LIMIT ?',
                             (self._partial_cursor,self.partial_rows)).fetchall()
        if rows:self._partial_cursor=rows[0][0]
        for rowid,key_bytes,payload_bytes in reversed(rows):
            c['partial_tail_rows']+=1
            if key_bytes+payload_bytes>self.partial_row_bytes:c['partial_row_byte_skips']+=1;continue
            key,payload=self.db.execute('SELECT id,payload FROM cnf_residual_v1 WHERE rowid=?',(rowid,)).fetchone()
            c['partial_tail_read_bytes']+=key_bytes+payload_bytes
            self._hint(key,payload)

    def _partial_reuse(self,cnf):
        if not self.partial_pool or not cnf or () in cnf or self._partial_probes>=self.partial_probes:return None
        self._partial_probes+=1;c=self.counts;c['partial_probes']+=1
        candidates={}
        for clause in cnf:
            c['partial_anchor_clauses']+=1;c['partial_anchor_literals']+=len(clause)
            for key in reversed(self.partial_index.get(clause,{})):
                c['partial_index_entries']+=1;candidates.setdefault(key,None)
                if len(candidates)==self.partial_candidates:break
            if len(candidates)==self.partial_candidates:break
        if not candidates:return None
        positions={clause:i for i,clause in enumerate(cnf)}
        for key in candidates:
            c['partial_candidates']+=1;entry=self.partial_pool[key];missing=0
            for clause in entry['clauses']:
                c['partial_containment_clauses']+=1
                if clause not in positions:
                    missing+=1
                    if missing>1:break
            if missing>1:continue
            node=self._read(key,purpose='partial_origin')
            if node is None:c['partial_stale_hints']+=1;continue
            if node['answer'] is not False or frozenset(tuple(cl) for cl in node['cnf'])!=entry['clauses']:
                raise ValueError('Partial hint differs from checked source')
            core=entry['clauses'];root=key
            if missing:
                if self._partial_support_used:continue
                self._partial_support_used=True;c['partial_support_attempts']+=1
                plan=CausalPlan(self,node_limit=self.partial_support_nodes,literal_limit=self.partial_support_literals,byte_limit=self.partial_plan_bytes)
                try:
                    derived=plan.prepare(key);core=frozenset(tuple(node['cnf'][i]) for i in derived['indices'])
                    if not core<=positions.keys():c['partial_support_misses']+=1;continue
                    root=derived['root'];plan.emit(key)
                except (SupportBudget,PlanBudget):c['partial_support_budget_stops']+=1;continue
                finally:
                    for k,v in plan.counts.items():c['partial_plan_'+k]+=v
            child=self._read(root,purpose='partial_hit')
            if child is None or child['answer'] is not False:raise ValueError('Checked residual refutation required')
            c['partial_hits']+=1
            if child['cnf']==[list(cl) for cl in cnf]:return child['proof']
            return dict(kind='component',clauses=sorted(positions[cl] for cl in core),child=root)
        return None

    def _expand(self,cnf):
        proof=self._partial_reuse(cnf)
        if proof is not None:return None,proof
        return super()._expand(cnf)

    def solve(self,source):
        began=time.perf_counter();result=None;stopped=False;self._partial_probes=0;self._partial_support_used=False
        try:
            result=super().solve(source);return result
        except RuntimeError as error:
            stopped=str(error)==BUDGET_MESSAGE;raise
        finally:
            if result is not None or stopped:self._refresh_partial()
            self.counts['partial_retained_entries']=len(self.partial_pool)
            self.counts['partial_retained_bytes']=self._partial_size() if self.partial_pool else 0
            if result is not None:
                result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
