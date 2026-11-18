"""Exact normalization with checked local order and order-preserving renaming.

No invariant is assumed from a caller. Sorted clauses use a two-pointer
tautology check; other clauses use the original set/sort path. Global clause
deduplication, support sorting, compact names and full-key serialization remain.
"""
from collections import Counter
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_residual_dag import token


def normalize_ordered(cnf, counts=None):
    c=Counter() if counts is None else counts
    c['ordered_calls']+=1;clauses=set()
    for clause in cnf:
        raw=tuple(clause);c['normalization_literal_visits']+=len(raw)
        c['ordered_snapshot_literals']+=len(raw);c['ordered_clauses']+=1
        ordered=True;last=None
        for lit in raw:
            if type(lit) is not int or not lit:
                raise ValueError('CNF literals must be nonzero integers')
            if last is not None and lit<=last:ordered=False
            last=lit
        if ordered:
            c['ordered_fast_clauses']+=1;c['ordered_fast_literals']+=len(raw)
            low=0;high=len(raw)-1;tautology=False
            while low<high and raw[low]<0<raw[high]:
                c['ordered_pair_steps']+=1;total=raw[low]+raw[high]
                if total==0:tautology=True;break
                if total<0:low+=1
                else:high-=1
            if not tautology:
                clauses.add(raw);c['ordered_initial_sorts_avoided']+=1
        else:
            c['ordered_fallback_clauses']+=1;c['ordered_fallback_literals']+=len(raw)
            items=set(raw)
            if not any(-lit in items for lit in items):clauses.add(tuple(sorted(items)))
    # Validate the entire input before empty-clause collapse, as before.
    if () in clauses:return ((),),()
    names=tuple(sorted({abs(lit) for clause in clauses for lit in clause}))
    rename={v:i+1 for i,v in enumerate(names)}
    # x -> sign(x)*rank(abs(x)) is strictly increasing on the signed support.
    # Every surviving clause is sorted, including clauses from the fallback.
    c['ordered_mapped_sorts_avoided']+=len(clauses)
    c['ordered_mapped_literals']+=sum(map(len,clauses))
    result=tuple(sorted(tuple(rename[abs(lit)]*(1 if lit>0 else -1)
                              for lit in clause) for clause in clauses))
    return result,names


class OrderedNormalizationSolver(BatchedPublicationSolver):
    def _canonical(self,cnf):
        pending=self._verification_canonical
        if pending is not None and cnf is pending[0]:return super()._canonical(cnf)
        normalized,names=normalize_ordered(cnf,self.counts)
        return normalized,names,token(normalized,self.counts)
