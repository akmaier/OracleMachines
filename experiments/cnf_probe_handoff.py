"""Pass inconclusive whole-clause preparation to the exact selected child.

Offers are private, immutable and expansion-local. Parent identity, assignment
and counters bind restriction reuse; raw identity binds normalization reuse.
The existing one-use propagation dispatcher is disabled during verification.
This experimental adapter requires an exclusive synchronous solver session.
"""
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import patch
import time
from experiments import cnf_residual_dag as native
from experiments import cnf_cofactor_handoff as prepared
from experiments.cnf_whole_pool_priority import WholePoolPrioritySolver
from experiments.cnf_ordered_probe import (discover,compile_cover,check_path,
    prefer_ordinary,force_all,TargetedBackboneMixin,OrderedProbeMixin)


def prepare(cnf,variable,value,counts):
    # Same private invariant and operations as cnf_ordered_probe._prepare,
    # additionally retaining the already computed raw restriction.
    if type(variable) is not int or variable<=0 or type(value) is not bool:
        raise ValueError('Positive variable and Boolean value required')
    raw=native.restrict(cnf,{variable:value},counts)
    counts['ordered_probe_preparations']+=1
    counts['ordered_probe_reused_literals']+=sum(map(len,raw))
    counts['ordered_probe_reused_clauses']+=len(raw)
    clauses=set(raw)
    if () in clauses:child,names=((),),()
    else:
        names=tuple(sorted({abs(l) for c in clauses for l in c}))
        counts['ordered_probe_support_literals']+=sum(map(len,clauses))
        rename={v:i+1 for i,v in enumerate(names)}
        child=tuple(sorted(tuple(rename[abs(l)]*(1 if l>0 else -1) for l in c) for c in clauses))
        counts['ordered_probe_mapped_literals']+=sum(map(len,child))
    return raw,(child,names,native.token(child,counts))


class ProbeHandoffMixin(OrderedProbeMixin):
    def _expand(self,cnf):
        return self._expand_prepared(cnf)


class ProbeHandoffSolver(WholePoolPrioritySolver,ProbeHandoffMixin):
    def __init__(self,*args,handoff_bytes=256*1024,**kwargs):
        if type(handoff_bytes) is not int or handoff_bytes<0:raise ValueError('Invalid handoff capacity')
        self.handoff_bytes=handoff_bytes;self._handoff_held=0;self._handoff_canonical=None
        self._waiting_offer=None;self._handoff_active=False;self._handoff_verifying=0
        self.handoff_summary=None
        super().__init__(*args,**kwargs)

    def _offer(self,raw,canonical,up):
        if not self.handoff_bytes:return None
        frozen=None if up is None else (tuple(up[0].items()),tuple(map(tuple,up[1])),up[2],up[3])
        self.counts['handoff_trace_freeze_entries']+=0 if up is None else len(up[0])+len(up[1])
        offer=prepared._Offer(raw,canonical,frozen)
        charge=prepared.CofactorHandoffSolver._charge_offer(self,offer)
        if self._handoff_held+charge>self.handoff_bytes:
            self.counts['handoff_capacity_skips']+=1;self.handoff_summary['oversized']+=1;return None
        offer=replace(offer,charge=charge);self._handoff_held+=charge
        self.counts['handoff_admissions']+=1;self.handoff_summary['admissions']+=1
        self.handoff_summary['peak_bytes']=max(self.handoff_summary['peak_bytes'],self._handoff_held)
        return offer

    def _probe(self,cnf,variable,value):
        c=self.counts;c['bipolar_true_probes' if value else 'bipolar_false_probes']+=1
        raw,canonical=prepare(cnf,variable,value,c);child,names,key=canonical
        old=self._read(key,child,purpose='bipolar_cofactor') if self.reuse else None
        if old is not None:
            c['bipolar_cached_negative' if not old['answer'] else 'bipolar_cached_positive']+=1
            return (key,None) if not old['answer'] else (None,self._offer(raw,canonical,None))
        local=Counter();fixed,trace,conflict=prepared.original_propagate(child,local)
        c.update({'bipolar_'+k:v for k,v in local.items()});c['bipolar_probe_trace_entries']+=len(trace)
        if conflict is None:
            c['bipolar_no_conflict']+=1
            return None,self._offer(raw,canonical,(fixed,trace,conflict,local.get('propagation_literal_visits',0)))
        self._store(key,dict(format=native.FORMAT,cnf=[list(cl) for cl in child],answer=False,
            proof=dict(kind='units',trace=trace,conflict=conflict)))
        c['bipolar_compiled_children']+=1
        return key,None

    def _discard(self,offer):
        self._handoff_held-=offer.charge
        self.counts['handoff_discarded']+=1;self.handoff_summary['discarded']+=1

    @contextmanager
    def _continuation(self,parent,variable,offers):
        owner=self.counts
        def consume(cnf,assignment,counts):
            if (not self._handoff_verifying and cnf is parent and counts is owner and
                    type(assignment) is dict and set(assignment)=={variable} and
                    type(assignment[variable]) is bool and assignment[variable] in offers):
                if self._waiting_offer is not None:raise RuntimeError('Unconsumed cofactor handoff')
                offer=offers.pop(assignment[variable]);self._waiting_offer=offer
                counts['handoff_restriction_reuses']+=1
                counts['handoff_avoided_restriction_literals']+=sum(map(len,parent))
                return offer.raw
            return native.restrict_scan(cnf,assignment,counts)
        try:
            with native.restriction_engine(consume):yield
        finally:
            # An unvisited prepared restriction is still only a hint.
            if self._waiting_offer is not None:
                self._discard(self._waiting_offer);self._waiting_offer=None
            for offer in offers.values():self._discard(offer)
            offers.clear()

    def _canonical(self,cnf):
        offer=self._handoff_canonical
        if not self._handoff_verifying and offer is not None and cnf is offer.raw:
            self._handoff_canonical=None
            self.counts['handoff_canonical_reuses']+=1
            self.counts['handoff_avoided_normalization_literals']+=sum(map(len,cnf))
            return offer.canonical
        return super()._canonical(cnf)

    def _visit(self,cnf):
        offer=self._waiting_offer
        if offer is None or cnf is not offer.raw or self._handoff_verifying:return super()._visit(cnf)
        self._waiting_offer=None;prior=self._handoff_canonical;self._handoff_canonical=offer
        token=prepared._PROPAGATION.set(None if offer.propagation is None else
            (offer.canonical[0],self.counts,offer.propagation))
        self.counts['handoff_selected']+=1;self.handoff_summary['consumed']+=1
        try:return super()._visit(cnf)
        finally:
            self._handoff_canonical=prior;prepared._PROPAGATION.reset(token)
            self._handoff_held-=offer.charge

    def _verify(self,key,node):
        self._handoff_verifying+=1;token=prepared._PROPAGATION.set(None)
        try:return super()._verify(key,node)
        finally:prepared._PROPAGATION.reset(token);self._handoff_verifying-=1

    def _expand_prepared(self,cnf):
        if not self._handoff_active:return OrderedProbeMixin._expand(self,cnf)
        if self.leaves:
            proof,cover,parts=discover(cnf,self.counts)
            if proof is not None:return None,proof
            if cover is not None:return None,compile_cover(self,cnf,cover)
            if parts:
                for evidence in parts:check_path(cnf,evidence,self.counts)
                preferred=prefer_ordinary(self,cnf,parts)
                if preferred is not None:return preferred
                return force_all(self,cnf,parts)
            c=self.counts
            if not cnf or any(len(cl)<2 for cl in cnf):c['whole_probe_unit_skips']+=1
            else:
                size=sum(map(len,cnf));c['whole_probe_size_literals']+=size
                if len(cnf)>4096 or size>16384:c['whole_probe_size_skips']+=1
                else:
                    frequency=Counter(abs(l) for cl in cnf for l in cl);c['whole_probe_ranking_literals']+=size
                    if len(frequency)>256:c['whole_probe_size_skips']+=1
                    else:
                        variable=min(frequency,key=lambda v:(-frequency[v],v));c['whole_probe_candidates']+=1
                        offers={}
                        # Install only after probing, so a probe cannot consume
                        # another probe's offer or change its own preparation.
                        try:
                            for value in (False,True):
                                excluded,offer=self._probe(cnf,variable,value)
                                if offer is not None:offers[value]=offer
                                if excluded is None:continue
                                c['whole_probe_selections']+=1
                                with self._continuation(cnf,variable,offers):
                                    model,live=self._visit(native.restrict(cnf,{variable:not value},c))
                                if model is not None:
                                    c['whole_probe_positive_lifts']+=1;return {variable:not value,**model},None
                                return None,dict(kind='split',variable=variable,
                                    low=live if value else excluded,high=excluded if value else live)
                            c['whole_probe_misses']+=1
                            with self._continuation(cnf,variable,offers):
                                return super(TargetedBackboneMixin,self)._expand(cnf)
                        finally:
                            for offer in offers.values():self._discard(offer)
                            offers.clear()
        return super(TargetedBackboneMixin,self)._expand(cnf)

    def solve(self,source):
        if self._handoff_active or native._restriction_engine.get() is not None:
            raise RuntimeError('Handoff requires an exclusive session with ordinary restriction')
        began=time.perf_counter();self._handoff_active=True
        self.handoff_summary=dict(peak_bytes=0,admissions=0,oversized=0,consumed=0,discarded=0)
        try:
            with patch.object(native,'propagate',prepared.handoff_propagate):result=super().solve(source)
        finally:
            self._handoff_active=False
            assert self._handoff_held==0 and self._waiting_offer is None and self._handoff_canonical is None
            assert self._handoff_verifying==0
            for k,v in self.handoff_summary.items():self.counts['whole_handoff_'+k]=v
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        return result
