"""Complete bounded affine spaces at the existing whole-input acquisition gate.

Reuse the already extracted equations. Positive models enter the unchanged
native checker; exhaustion uses the existing separate affine-negative authority.
No native certificate depends on an extension result.
"""
from collections import Counter
import time
from experiments.cnf_ordered_probe import OrderedProbeSolver
from experiments.cnf_affine_probe import bounded_extract
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_affine_clause import make_space, check_space
from experiments.cnf_affine_negative import FORMAT as AFFINE_FORMAT, FREE_LIMIT
from experiments.cnf_residual_dag import FORMAT as NATIVE_FORMAT, holds
from experiments.cnf_support_plan import PlannedNegativeSolver


def complete_prepared(cnf, root, affine, counts, free_limit):
    """Reuse a source-bound extraction; check its whole affine solution space."""
    if type(free_limit) is not int or not 0 <= free_limit <= FREE_LIMIT:
        raise ValueError('Completion limit exceeds the existing authority')
    n=max((abs(l) for cl in cnf for l in cl),default=0)
    summary=check_affine(cnf,affine,counts)
    d=n-summary['rank']
    record=dict(root=root,variables=n,free=d,free_limit=free_limit,affine=affine,
        summary=summary,space=None,rejected=[],accepted=None,status=None)
    counts['whole_affine_checked_completions']+=1
    if not summary['equation_count'] or summary['inconsistent'] or d>free_limit:
        raise ValueError('Completion requires a consistent, eligible affine core')
    space=make_space(n,affine,counts)
    check_space(n,affine,space,counts)
    record['space']=space
    packed=[]
    for cid in affine['leftovers']:
        positive=negative=0
        for lit in cnf[cid]:
            counts['whole_affine_packed_literals']+=1
            if lit>0:positive|=1<<(lit-1)
            else:negative|=1<<(-lit-1)
        packed.append((cid,positive,negative))
    candidate=space['particular']
    for index in range(1<<d):
        if index:
            candidate^=space['directions'][(index & -index).bit_length()-1]
            counts['whole_affine_basis_xors']+=1
        counts['whole_affine_candidates']+=1
        failed=None
        for cid,positive,negative in packed:
            counts['whole_affine_clause_checks']+=1
            if not (candidate & positive or ~candidate & negative):failed=cid;break
        if failed is not None:
            record['rejected'].append(failed)
            continue
        model={v:bool(candidate & (1<<(v-1))) for v in range(1,n+1)}
        counts['whole_affine_model_check_literals']+=sum(map(len,cnf))
        if not holds(cnf,model):raise ValueError('Completion model fails the full CNF')
        record.update(status='model',accepted=dict(index=index,mask=candidate))
        counts['whole_affine_models']+=1
        return model,record
    record['status']='space-exhausted'
    counts['whole_affine_exhaustions']+=1
    return None,record


class WholeAffineSolver(OrderedProbeSolver):
    def __init__(self,*args,completion_free_limit=FREE_LIMIT,**kwargs):
        if type(completion_free_limit) is not int or not 0<=completion_free_limit<=FREE_LIMIT:
            raise ValueError('Completion limit exceeds the existing authority')
        self.completion_free_limit=completion_free_limit
        super().__init__(*args,**kwargs)

    def _whole_solve(self,source):
        if self.db.active or self.db.poisoned or self.db.in_transaction:
            raise RuntimeError('Affine completion requires an owned healthy idle connection')
        self.counts=Counter();cnf,names,root=self._canonical(source);model=None
        node=self.affine.read(root,cnf) if self.reuse else None
        if node is not None:self.counts['affine_probe_exact_hits']+=1
        else:
            known=self.reuse and (self._read(root,cnf) is not None or self.equivalences.read(root) is not None)
            if known:self.counts['affine_probe_known_skips']+=1
            else:
                size=sum(map(len,cnf));self.counts['affine_probe_size_literals']+=size
                if len(names)>self.affine_variables or len(cnf)>self.affine_clauses or size>self.affine_literals:
                    self.counts['affine_probe_size_skips']+=1
                else:
                    self.counts['affine_probe_attempts']+=1
                    affine=bounded_extract(cnf,self.counts,self.affine_xors);evidence=None
                    if affine is not None:
                        if any(r['mask']==0 and r['rhs']==1 for r in affine['reductions']):
                            evidence=dict(root=root,status='linear-conflict',affine=affine)
                        elif not affine['equations']:
                            self.counts['whole_affine_no_equation_skips']+=1
                        else:
                            # Eligibility is not authority. The completion checks
                            # extraction and rank before using any space or model.
                            rank=sum(bool(r['mask']) for r in affine['reductions'])
                            self.counts['whole_affine_rank_rows']+=len(affine['reductions'])
                            if len(names)-rank>self.completion_free_limit:
                                self.counts['whole_affine_free_cap_skips']+=1
                            else:
                                model,evidence=complete_prepared(cnf,root,affine,self.counts,self.completion_free_limit)
                    if evidence is not None and model is None:
                        before=Counter(self.counts)
                        try:self.affine.publish(cnf,evidence)
                        finally:self.counts.update(before)
                        node=self.affine.read(root,cnf)
                        self.counts['affine_probe_conflicts' if evidence['status']=='linear-conflict' else 'whole_affine_negative_publications']+=1
                    elif model is not None:
                        external={name:model[i] for i,name in enumerate(names,1)}
                        self.counts['whole_affine_raw_witness_literals']+=sum(map(len,source))
                        if not holds(source,external):raise ValueError('Completion model fails the raw source')
                        self._store(root,dict(format=NATIVE_FORMAT,cnf=[list(cl) for cl in cnf],
                            answer=True,model=[model[i] for i in range(1,len(names)+1)]))
                        self.counts['whole_affine_positive_publications']+=1
                    else:self.counts['affine_probe_misses']+=1
        if node is None and model is None:
            before=Counter(self.counts)
            try:result=PlannedNegativeSolver.solve(self,source)
            finally:self.counts.update(before)
        else:
            nodes,payload=self.archive_storage()
            result=dict(answer=model is not None,
                model=None if model is None else {name:model[i] for i,name in enumerate(names,1)},
                root=root,authority=AFFINE_FORMAT if model is None else 'native',quotient_choice=None,
                archive_nodes=nodes,archive_payload_bytes=payload)
        result['affine_archive_nodes'],result['affine_archive_payload_bytes']=self.affine.storage()
        return result

    def solve(self,source):
        began=time.perf_counter();source=tuple(tuple(clause) for clause in source)
        try:result=self._whole_solve(source)
        finally:
            self.counts['affine_input_snapshot_clauses']+=len(source)
            self.counts['affine_input_snapshot_literals']+=sum(map(len,source))
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        return result
