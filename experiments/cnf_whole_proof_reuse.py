"""Discover a partial branch plan from an earlier near-matching native refutation.

Only canonical clauses and earlier checked root proofs select an origin. Plans
are transient hints. Every successful result and retained stopped prefix passes
the unchanged native checker; cold replay needs no plan or new proof authority.
"""
from collections import Counter
import time
from experiments.cnf_whole_affine import WholeAffineSolver
from experiments.cnf_partial_proof_plan import extract_partial,make_plan,survival,recompose
from experiments.cnf_residual_dag import holds
from experiments.cnf_fresh_mixtures import BUDGET_MESSAGE


class WholeProofReuseSolver(WholeAffineSolver):
    def __init__(self,*args,whole_plan_nodes=64,whole_plan_literals=65536,**kwargs):
        if (type(whole_plan_nodes) is not int or not 1<=whole_plan_nodes<=64 or
                type(whole_plan_literals) is not int or not 1<=whole_plan_literals<=65536):
            raise ValueError('Invalid whole-proof extraction limits')
        self.whole_plan_nodes=whole_plan_nodes;self.whole_plan_literals=whole_plan_literals
        super().__init__(*args,**kwargs)

    def _try_whole_plan(self,source):
        cnf,names,root=self._canonical(source)
        if not self.reuse:return None
        if (self._read(root,cnf) is not None or self.affine.read(root,cnf) is not None or
                self.equivalences.read(root) is not None):
            self.counts['whole_plan_known_skips']+=1;return None
        literals=sum(map(len,cnf));self.counts['whole_plan_size_literals']+=literals
        if not cnf or () in cnf or literals>self.negative_literal_limit:return None
        members=set(cnf)
        for origin,entry in reversed(self.negative_pool.items()):
            self.counts['whole_plan_candidates_scanned']+=1
            missing=0;overlap=0
            for clause in entry['clauses']:
                self.counts['whole_plan_clause_tests']+=1
                if clause in members:overlap+=1
                else:
                    missing+=1
                    if missing>1:break
            if missing!=1 or not overlap:continue
            node=self._read(origin,purpose='whole_plan_origin')
            if node is None:continue
            if node['answer'] is not False or frozenset(map(tuple,node['cnf']))!=entry['clauses']:
                raise ValueError('Unbound whole-proof origin')
            self.counts['whole_plan_extractions']+=1
            bundle,work=extract_partial(self,node['cnf'],node_limit=self.whole_plan_nodes,
                literal_limit=self.whole_plan_literals)
            self.counts.update(work);plan=make_plan(bundle);extra=Counter()
            intact=survival(cnf,plan,extra)
            if not any(intact):
                self.counts.update(extra);self.counts['whole_plan_empty_skips']+=1
                return None
            self.counts['whole_plan_selected_intact']+=sum(intact)
            self.counts['whole_plan_selected_leaves']+=len(intact)
            before=Counter(self.counts)
            try:outcome=recompose(self,cnf,plan,self.node_limit,extra)
            finally:self.counts.update(before);self.counts.update(extra)
            self.counts['whole_plan_attempts']+=1
            if outcome['stopped']:
                self.counts['whole_plan_stops']+=1
                raise RuntimeError(BUDGET_MESSAGE)
            result=self._read(root,cnf,purpose='whole_plan_result')
            if result is None:raise ValueError('Missing checked recomposed root')
            model=dict(zip(names,result['model'])) if result['answer'] else None
            if model is not None:
                self.counts['whole_plan_raw_witness_literals']+=sum(map(len,source))
                if not holds(source,model):raise ValueError('Recomposed model fails raw source')
            nodes,payload=self.archive_storage();self.counts['whole_plan_completed']+=1
            return dict(answer=result['answer'],model=model,root=root,authority='native',quotient_choice=None,
                archive_nodes=nodes,archive_payload_bytes=payload,
                whole_plan=dict(origin=origin,plan=plan,outcome=outcome))
        return None

    def solve(self,source):
        began=time.perf_counter();source=tuple(tuple(clause) for clause in source)
        if self.db.active or self.db.poisoned or self.db.in_transaction:
            raise RuntimeError('Whole-proof reuse requires an owned healthy idle connection')
        self.counts=Counter()
        try:
            result=self._try_whole_plan(source)
            if result is None:
                before=Counter(self.counts)
                try:result=super().solve(source)
                finally:self.counts.update(before)
            result['affine_archive_nodes'],result['affine_archive_payload_bytes']=self.affine.storage()
        finally:
            self.counts['whole_plan_input_snapshot_clauses']+=len(source)
            self.counts['whole_plan_input_snapshot_literals']+=sum(map(len,source))
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        return result
