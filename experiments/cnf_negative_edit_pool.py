"""Bounded on-demand UNSAT support reuse near previously solved root formulas.

Candidate descriptions have no proof authority. Causal supports are discovered
only after a near-edit match and materialized only if contained in the target.
Every reused/derived negative proof goes through the unchanged native checker.
"""
import time
from collections import Counter
from experiments.cnf_witness_pool import WitnessPoolSolver
from experiments.cnf_causal_support import CausalSupportExtractor


class SupportBudget(RuntimeError):pass


class BoundedCausalExtractor(CausalSupportExtractor):
    def __init__(self,*args,node_limit=256,literal_limit=131072,**kwargs):
        super().__init__(*args,**kwargs);self.node_limit=node_limit;self.literal_limit=literal_limit

    def extract(self,key):
        if key not in self.memo:
            if self.counts['support_nodes']>=self.node_limit:raise SupportBudget('Support node budget')
            node=self.solver._read(key,purpose='negative_pool_budget')
            if node is None or node['answer'] is not False:raise ValueError('Checked negative origin required')
            if self.counts['support_source_literals']+sum(map(len,node['cnf']))>self.literal_limit:
                raise SupportBudget('Support literal budget')
        return super().extract(key)


class NegativeEditPoolSolver(WitnessPoolSolver):
    def __init__(self,*args,negative_capacity=16,negative_literal_limit=4096,
                 negative_node_limit=256,negative_support_literals=131072,**kwargs):
        limits=(negative_capacity,negative_literal_limit,negative_node_limit,negative_support_literals)
        if any(type(v) is not int or v<1 for v in limits):raise ValueError('Invalid negative pool limits')
        self.negative_capacity=negative_capacity;self.negative_literal_limit=negative_literal_limit
        self.negative_node_limit=negative_node_limit;self.negative_support_literals=negative_support_literals
        self.negative_pool={};self._negative_tried=False
        super().__init__(*args,**kwargs)

    def _admit_negative(self,result):
        if result['answer'] or result.get('authority','native')!='native':return
        key=result['root'];node=self._read(key,purpose='negative_pool_admission')
        if node is None or node['answer'] is not False:raise ValueError('Missing checked negative root')
        literals=sum(map(len,node['cnf']));self.counts['negative_admission_literals']+=literals
        if node['cnf']==[[]] or literals>self.negative_literal_limit:
            self.counts['negative_admission_skips']+=1;return
        entry=self.negative_pool.pop(key,None)
        if entry is None:entry=dict(clauses=frozenset(tuple(c) for c in node['cnf']),proposal=None)
        if len(self.negative_pool)>=self.negative_capacity:
            del self.negative_pool[next(iter(self.negative_pool))];self.counts['negative_evictions']+=1
        self.negative_pool[key]=entry;self.counts['negative_admissions']+=1

    def _extract(self,key,materialize):
        extractor=BoundedCausalExtractor(self,materialize=materialize,node_limit=self.negative_node_limit,
                                         literal_limit=self.negative_support_literals)
        prefix='negative_materialize_' if materialize else 'negative_discover_'
        self.counts[prefix+'attempts']+=1
        try:return extractor.extract(key)
        except SupportBudget:
            self.counts[prefix+'budget_stops']+=1;return None
        finally:
            for k,v in extractor.counts.items():self.counts[prefix+k]+=v

    def _negative_reuse(self,cnf):
        c=self.counts;c['negative_target_literals']+=sum(map(len,cnf))
        if not cnf or () in cnf or sum(map(len,cnf))>self.negative_literal_limit:return None
        positions={clause:i for i,clause in enumerate(cnf)};members=set(positions)
        for origin,entry in reversed(self.negative_pool.items()):
            c['negative_candidates']+=1;c['negative_containment_clauses']+=len(entry['clauses'])
            # Early cutoff avoids constructing a full set difference for a miss.
            missing=0
            for clause in entry['clauses']:
                c['negative_clause_tests']+=1
                if clause not in members:
                    missing+=1
                    if missing>1:break
            if missing>1:continue
            node=self._read(origin,purpose='negative_pool_origin')
            if node is None:c['negative_stale_origins']+=1;continue
            if node['answer'] is not False:raise ValueError('Positive negative-pool origin')
            if frozenset(tuple(cl) for cl in node['cnf'])!=entry['clauses']:
                raise ValueError('Changed negative-pool origin')
            c['negative_near_matches']+=1
            if not missing:
                core=entry['clauses'];root=origin
            else:
                proposal=entry['proposal']
                if proposal is None:
                    derived=self._extract(origin,False)
                    if derived is None:return None
                    proposal=dict(root=derived['root'],clauses=frozenset(tuple(node['cnf'][i]) for i in derived['indices']))
                    entry['proposal']=proposal
                c['negative_support_clause_tests']+=len(proposal['clauses'])
                if not proposal['clauses']<=members:
                    c['negative_support_misses']+=1;return None
                root=proposal['root'];core=proposal['clauses']
                child=self._read(root,purpose='negative_pool_ready')
                if child is None:
                    derived=self._extract(origin,True)
                    if derived is None:return None
                    if derived['root']!=root:raise ValueError('Causal proposal changed during materialization')
                    child=self._read(root,purpose='negative_pool_materialized')
                if child is None or child['answer'] is not False:raise ValueError('Checked negative core required')
            # The existing subset verifier independently checks indices, exact
            # compact-name transport and the complete negative child proof.
            ids=sorted(positions[clause] for clause in core)
            c['negative_hits']+=1
            child=self._read(root,purpose='negative_pool_hit')
            if child['cnf']==[list(cl) for cl in cnf]:return child['proof']
            return dict(kind='component',clauses=ids,child=root)
        return None

    def _expand(self,cnf):
        if not self._negative_tried:
            self._negative_tried=True
            proof=self._negative_reuse(cnf)
            if proof is not None:return None,proof
        return super()._expand(cnf)

    def solve(self,source):
        tick=time.perf_counter();self._negative_tried=False
        result=super().solve(source);self._admit_negative(result)
        self.counts['negative_retained_entries']=len(self.negative_pool)
        self.counts['negative_retained_literals']=sum(sum(map(len,e['clauses'])) for e in self.negative_pool.values())
        self.counts['negative_proposal_literals']=sum(sum(map(len,e['proposal']['clauses'])) for e in self.negative_pool.values() if e['proposal'] is not None)
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-tick
        return result
