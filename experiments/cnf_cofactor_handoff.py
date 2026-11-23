"""Direct, one-use cofactor preparation passed to the selected native child.

No content-indexed memo. A solver-owned immutable offer supplies normalization
and optional propagation only to its actual child. Discovery priority and all
certificate checks remain unchanged. Offers carry no answer authority.
"""
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass,replace
import sys
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import FORMAT,propagate as original_propagate,restrict
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_backbone import check_path,excluded_child
from experiments.cnf_binary_clause_cover import compile_cover
from experiments.cnf_targeted_backbone import TargetedBackboneMixin

_PROPAGATION=ContextVar('oracle_cofactor_handoff',default=None)


@dataclass(frozen=True,slots=True)
class _Offer:
    raw:tuple
    canonical:tuple
    propagation:tuple|None
    charge:int=0


def handoff_propagate(cnf,counts):
    pending=_PROPAGATION.get()
    if pending is not None and cnf is pending[0] and counts is pending[1]:
        _PROPAGATION.set(None)  # Consume before any nested work.
        fixed,trace,conflict,visits=pending[2]
        counts['handoff_propagation_reuses']+=1
        counts['handoff_avoided_propagation_literals']+=visits
        counts['handoff_trace_copy_entries']+=len(fixed)+len(trace)
        return dict(fixed),[list(pair) for pair in trace],conflict
    return original_propagate(cnf,counts)


class CofactorHandoffSolver(InputSafeAffineProbeSolver):
    def __init__(self,*args,handoff_bytes=256*1024,**kwargs):
        if type(handoff_bytes) is not int or handoff_bytes<0:raise ValueError('Invalid handoff capacity')
        self.handoff_bytes=handoff_bytes;self._offer=None;self._handoff_canonical=None
        self._handoff_held=0;self._handoff_active=False;self.handoff_summary=None
        super().__init__(*args,**kwargs)

    @contextmanager
    def handoff_session(self):
        if self._handoff_active or self._handoff_held:raise RuntimeError('Nested handoff session')
        self._handoff_active=True
        self.handoff_summary=dict(peak_bytes=0,admissions=0,oversized=0,consumed=0,discarded=0)
        try:yield
        finally:
            self._clear_offer();self._handoff_active=False
            assert self._handoff_held==0 and self._handoff_canonical is None

    def _charge_offer(self,offer):
        raw=offer.raw;cnf,names,key=offer.canonical
        maximum=max((max(map(abs,c),default=0) for c in raw),default=0)
        a=sys.getsizeof(maximum);b=sys.getsizeof(len(names))
        self.counts['handoff_sizing_literals']+=sum(map(len,raw))
        charge=(sys.getsizeof(offer)+sys.getsizeof(self.handoff_bytes)
            +sys.getsizeof(raw)+sum(sys.getsizeof(c)+len(c)*a for c in raw)
            +sys.getsizeof(offer.canonical)+sys.getsizeof(cnf)+sum(sys.getsizeof(c)+len(c)*b for c in cnf)
            +sys.getsizeof(names)+len(names)*a+sys.getsizeof(key))
        up=offer.propagation
        if up is None:return charge+sys.getsizeof(None)
        fixed,trace,conflict,visits=up
        return (charge+sys.getsizeof(up)+sys.getsizeof(conflict)+sys.getsizeof(visits)
            +sum(sys.getsizeof(rows)+sum(sys.getsizeof(pair)+sum(map(sys.getsizeof,pair)) for pair in rows) for rows in (fixed,trace)))

    def _retain_offer(self,raw,canonical,up):
        if not self._handoff_active or not self.handoff_bytes:return
        assert self._offer is None
        frozen=None if up is None else (tuple(up[0].items()),tuple(map(tuple,up[1])),up[2],up[3])
        self.counts['handoff_trace_freeze_entries']+=0 if up is None else len(up[0])+len(up[1])
        offer=_Offer(raw,canonical,frozen);charge=self._charge_offer(offer)
        if charge+self._handoff_held>self.handoff_bytes:
            self.counts['handoff_capacity_skips']+=1;self.handoff_summary['oversized']+=1;return
        self._offer=replace(offer,charge=charge);self._handoff_held+=charge
        self.counts['handoff_admissions']+=1;self.handoff_summary['admissions']+=1
        self.handoff_summary['peak_bytes']=max(self.handoff_summary['peak_bytes'],self._handoff_held)
        assert self._handoff_held<=self.handoff_bytes

    def _clear_offer(self):
        if self._offer is not None:
            self._handoff_held-=self._offer.charge;self._offer=None
            self.counts['handoff_discarded']+=1;self.handoff_summary['discarded']+=1
        assert self._handoff_held>=0

    def _canonical(self,cnf):
        offer=self._handoff_canonical
        if offer is not None and cnf is offer.raw:
            self._handoff_canonical=None
            self.counts['handoff_canonical_reuses']+=1
            self.counts['handoff_avoided_normalization_literals']+=sum(map(len,cnf))
            return offer.canonical
        return super()._canonical(cnf)

    def _visit_offer(self,offer):
        if offer is None or offer is not self._offer:raise ValueError('Not the current solver-owned offer')
        self._offer=None;prior=self._handoff_canonical;self._handoff_canonical=offer
        up=(offer.canonical[0],self.counts,offer.propagation) if offer.propagation is not None else None
        marker=_PROPAGATION.set(up)
        self.counts['handoff_selected']+=1;self.handoff_summary['consumed']+=1
        try:return self._visit(offer.raw)
        finally:
            self._handoff_canonical=prior;_PROPAGATION.reset(marker)
            self._handoff_held-=offer.charge;assert self._handoff_held>=0

    def _probe_cofactor(self,cnf,variable,value,*,retain=False):
        if type(value) is not bool:raise ValueError('Boolean probe value required')
        c=self.counts;c['bipolar_true_probes' if value else 'bipolar_false_probes']+=1
        raw=restrict(cnf,{variable:value},c);canonical=self._canonical(raw);child,names,key=canonical
        old=self._read(key,child,purpose='bipolar_cofactor') if self.reuse else None
        if old is not None:
            c['bipolar_cached_negative' if not old['answer'] else 'bipolar_cached_positive']+=1
            if old['answer'] and retain:self._retain_offer(raw,canonical,None)
            return key if old['answer'] is False else None
        local=Counter();fixed,trace,conflict=original_propagate(child,local)
        c.update({'bipolar_'+k:v for k,v in local.items()});c['bipolar_probe_trace_entries']+=len(trace)
        if conflict is None:
            c['bipolar_no_conflict']+=1
            if retain:self._retain_offer(raw,canonical,(fixed,trace,conflict,local.get('propagation_literal_visits',0)))
            return None
        self._store(key,dict(format=FORMAT,cnf=[list(cl) for cl in child],answer=False,
            proof=dict(kind='units',trace=trace,conflict=conflict)))
        c['bipolar_compiled_children']+=1
        return key


def handoff_expand(self,cnf):
    if self.leaves:
        proof,cover,partials=discover(cnf,self.counts,policy='binary1')
        if proof is not None:return None,proof
        if cover is not None:return None,compile_cover(self,cnf,cover)
        evidence=partials[0] if partials else None
        if evidence is not None:
            check_path(cnf,evidence,self.counts)
            literal=evidence['literal'];variable=abs(literal)
            frequencies=Counter(abs(l) for c in cnf for l in c);literals=sum(map(len,cnf))
            self.counts['bipolar_ranking_literals']+=literals
            default=min(frequencies,key=lambda v:(-frequencies[v],v))
            if default!=variable:
                if len(frequencies)<=256 and len(cnf)<=4096 and literals<=16384:
                    # Only a false miss can become the selected, already
                    # prepared child after the following true refutation.
                    try:
                        for value in (False,True):
                            excluded=self._probe_cofactor(cnf,default,value,retain=not value)
                            if excluded is not None:
                                self.counts['bipolar_default_selections']+=1
                                if value and self._offer is not None:
                                    model,live=self._visit_offer(self._offer)
                                else:
                                    self._clear_offer()
                                    model,live=self._visit(restrict(cnf,{default:not value},self.counts))
                                if model is not None:
                                    self.counts['bipolar_positive_lifts']+=1
                                    return {default:not value,**model},None
                                return None,dict(kind='split',variable=default,
                                    low=live if value else excluded,high=excluded if value else live)
                    finally:self._clear_offer()
                else:self.counts['bipolar_size_skips']+=1
            else:self.counts['bipolar_same_variable_skips']+=1
            self.counts['binary_backbone_selections']+=1
            model,live=self._visit(restrict(cnf,{variable:literal<0},self.counts))
            if model is not None:
                self.counts['binary_backbone_positive_lifts']+=1
                return {variable:literal<0,**model},None
            excluded=excluded_child(self,cnf,evidence)
            self.counts['binary_backbone_negative_splits']+=1
            return None,dict(kind='split',variable=variable,low=live if literal>0 else excluded,high=excluded if literal>0 else live)
    return super(TargetedBackboneMixin,self)._expand(cnf)
