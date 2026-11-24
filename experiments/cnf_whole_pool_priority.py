"""Give an existing complete result precedence over a partial proof plan.

The gate runs only after the unchanged near-origin selection becomes eligible.
It uses the existing checked negative/model pools. A miss conveys no verdict,
retains its preparation cost, and continues with the original partial policy.
The parent implementation is frozen with its earlier experiment; this local
method mirrors that policy so its archived source remains reproducible.
"""
from collections import Counter
from experiments.cnf_whole_proof_reuse import WholeProofReuseSolver
from experiments.cnf_partial_proof_plan import extract_partial,make_plan,survival,recompose
from experiments.cnf_pool_priority import try_pools
from experiments.cnf_residual_dag import holds
from experiments.cnf_fresh_mixtures import BUDGET_MESSAGE


class WholePoolPrioritySolver(WholeProofReuseSolver):
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
            # A near match makes partial reconstruction eligible, but an
            # existing complete proof or checked witness takes precedence.
            # Misses may prepare causal hints; their work is retained and a
            # later native fallback may repeat them. No miss cache is assumed.
            self.counts['whole_pool_gates']+=1
            route=try_pools(self,cnf,root)
            if route is not None:
                result=self._read(root,cnf,purpose='whole_pool_result')
                if result is None:raise ValueError('Missing checked pool result')
                model=dict(zip(names,result['model'])) if result['answer'] else None
                if model is not None:
                    self.counts['whole_pool_raw_witness_literals']+=sum(map(len,source))
                    if not holds(source,model):raise ValueError('Pool model fails raw source')
                nodes,payload=self.archive_storage()
                self.counts['whole_pool_completed']+=1
                return dict(answer=result['answer'],model=model,root=root,authority='native',quotient_choice=None,
                    archive_nodes=nodes,archive_payload_bytes=payload,
                    whole_pool=dict(route=route,near_origin=origin))
            self.counts['whole_pool_misses']+=1
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

