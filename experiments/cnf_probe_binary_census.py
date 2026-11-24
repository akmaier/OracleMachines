"""Inspect unit-consistent probes for a source-bound binary contradiction.

Discovery is pure: it does not mutate the search solver or certify a parent.
Returned native nodes require the existing independent verifier before use.
The observer preserves the original search, including its counters and budget.
"""
from collections import Counter
import time
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_lifetime import ProbeLifetimeSolver


def closure(canonical,up,counts):
    """Reuse a complete nonconflicting UP result on this exact canonical CNF."""
    child,names,key=canonical
    fixed,trace,conflict,_=up
    if conflict is not None:raise ValueError('Expected a nonconflicting probe')
    counts['closure_calls']+=1
    if fixed:
        raw=native.restrict_scan(child,fixed,counts)
        residual,_=native.normalize(raw,counts)
        residual_key=native.token(residual,counts)
    else:residual,residual_key=child,key
    ids=[];positive=negative=False
    for i,c in enumerate(residual):
        counts['closure_width_checks']+=1
        if len(c)<2:
            return dict(status='not-unit-closed',residual=residual,root=residual_key,nodes=[])
        if len(c)==2:
            ids.append(i);counts['closure_binary_literals']+=2
            positive|=all(l>0 for l in c);negative|=all(l<0 for l in c)
    result=dict(status='no-binary' if not ids else 'uniform-binary',
        residual=residual,root=residual_key,binary_clauses=len(ids),nodes=[])
    if not (positive and negative):return result
    counts['closure_scc_calls']+=1
    model,proof=native.two_cnf(tuple(residual[i] for i in ids),counts)
    if proof is None:result['status']='binary-sat';return result
    counts['closure_refutations']+=1
    for label in ('forward','backward'):
        proof[label]=[[literal,ids[cid]] for literal,cid in proof[label]]
        counts['closure_path_edges']+=len(proof[label])
    result['status']='binary-unsat'
    result['nodes'].append(dict(key=residual_key,node=dict(format=native.FORMAT,
        cnf=[list(c) for c in residual],answer=False,proof=proof)))
    if fixed:
        result['nodes'].append(dict(key=key,node=dict(format=native.FORMAT,
            cnf=[list(c) for c in child],answer=False,
            proof=dict(kind='units',trace=[list(p) for p in trace],child=residual_key))))
    return result


class BinaryCensusSolver(ProbeLifetimeSolver):
    """Observe only designated queries; never publish a census result in search."""
    def __init__(self,*args,**kwargs):
        self.observe=False;self.events=[];self._probe_context=None
        super().__init__(*args,**kwargs)

    def _probe(self,cnf,variable,value):
        prior=self._probe_context;self._probe_context=(cnf,variable,value)
        try:return super()._probe(cnf,variable,value)
        finally:self._probe_context=prior

    def _offer(self,raw,canonical,up):
        if self.observe and up is not None:
            parent,variable,value=self._probe_context
            counts=Counter();tick=time.perf_counter();found=closure(canonical,up,counts)
            seconds=time.perf_counter()-tick
            # All arrays are copied for the record; nothing stored here is a
            # mutable search object, and its counters are a separate Counter.
            self.events.append(dict(parent=[list(c) for c in parent],variable=variable,value=value,
                child=[list(c) for c in canonical[0]],names=list(canonical[1]),root=canonical[2],
                fixed=[[v,b] for v,b in sorted(up[0].items())],trace=[list(p) for p in up[1]],
                discovery=found,counts=dict(counts),seconds=seconds))
        return super()._offer(raw,canonical,up)
