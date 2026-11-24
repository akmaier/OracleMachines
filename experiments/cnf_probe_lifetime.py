"""Retire consumed handoff references, separating cleanup from budget transfer.

A mutable private lease becomes an empty tombstone after its consumers finish.
Native search still owns the data it needs. The old full-visit charge is reported
as a separate envelope when early release admits more pending preparation.
"""
from dataclasses import dataclass
from contextvars import ContextVar
from unittest.mock import patch
import time
from experiments import cnf_residual_dag as native
from experiments import cnf_cofactor_handoff as prepared
from experiments.cnf_probe_handoff import ProbeHandoffSolver

_UP=ContextVar('oracle_probe_lifetime',default=None)


@dataclass(slots=True)
class _Lease:
    raw:tuple|None
    canonical:tuple|None
    propagation:tuple|None
    charge:int=0
    retired:bool=False


def propagate(cnf,counts):
    pending=_UP.get()
    if pending is None or cnf is not pending[0] or counts is not pending[1]:
        return prepared.original_propagate(cnf,counts)
    _UP.set(None)  # Drop the active binding before any nested work.
    solver,lease=pending[2:]
    assert not lease.retired and lease.canonical is None and lease.raw is None
    fixed,trace,conflict,visits=lease.propagation
    counts['handoff_propagation_reuses']+=1
    counts['handoff_avoided_propagation_literals']+=visits
    counts['handoff_trace_copy_entries']+=len(fixed)+len(trace)
    result=dict(fixed),[list(pair) for pair in trace],conflict
    solver._retire(lease,'propagation')
    return result


class ProbeLifetimeSolver(ProbeHandoffSolver):
    def __init__(self,*args,release_early=True,**kwargs):
        if type(release_early) is not bool:raise ValueError('Boolean release policy required')
        self.release_early=release_early;self._transferred_held=0;self.lifetime_summary=None
        super().__init__(*args,**kwargs)

    def _peaks(self):
        s=self.lifetime_summary
        s['transferred_peak_bytes']=max(s['transferred_peak_bytes'],self._transferred_held)
        s['full_visit_envelope_peak_bytes']=max(s['full_visit_envelope_peak_bytes'],self._handoff_held+self._transferred_held)

    def _offer(self,raw,canonical,up):
        if not self.handoff_bytes:return None
        frozen=None if up is None else (tuple(up[0].items()),tuple(map(tuple,up[1])),up[2],up[3])
        self.counts['handoff_trace_freeze_entries']+=0 if up is None else len(up[0])+len(up[1])
        lease=_Lease(raw,canonical,frozen)
        charge=prepared.CofactorHandoffSolver._charge_offer(self,lease)
        if self._handoff_held+charge>self.handoff_bytes:
            self.counts['handoff_capacity_skips']+=1;self.handoff_summary['oversized']+=1;return None
        lease.charge=charge;self._handoff_held+=charge
        self.counts['handoff_admissions']+=1;self.handoff_summary['admissions']+=1
        self.handoff_summary['peak_bytes']=max(self.handoff_summary['peak_bytes'],self._handoff_held)
        self._peaks();return lease

    def _retire(self,lease,phase):
        assert not lease.retired and lease.charge>0
        lease.raw=lease.canonical=lease.propagation=None;lease.retired=True
        self.lifetime_summary[phase+'_retirements']+=1
        if self.release_early and phase in ('canonical','propagation'):
            self._handoff_held-=lease.charge;self._transferred_held+=lease.charge;lease.charge=0
            self._peaks()

    def _discard(self,lease):
        self._retire(lease,'discard');self._handoff_held-=lease.charge;lease.charge=0
        self.counts['handoff_discarded']+=1;self.handoff_summary['discarded']+=1

    def _canonical(self,cnf):
        lease=self._handoff_canonical
        if not self._handoff_verifying and lease is not None and cnf is lease.raw:
            assert not lease.retired
            self._handoff_canonical=None
            self.counts['handoff_canonical_reuses']+=1
            self.counts['handoff_avoided_normalization_literals']+=sum(map(len,cnf))
            result=lease.canonical
            # The native visit receives this triple. The lease no longer owns
            # a raw/canonical binding that could serve another consumer.
            lease.raw=lease.canonical=None
            if lease.propagation is None:self._retire(lease,'canonical')
            return result
        return super()._canonical(cnf)

    def _visit(self,cnf):
        lease=self._waiting_offer
        if lease is None or cnf is not lease.raw or self._handoff_verifying:return super()._visit(cnf)
        assert not lease.retired
        self._waiting_offer=None;prior=self._handoff_canonical;self._handoff_canonical=lease
        charge=lease.charge
        marker=_UP.set(None if lease.propagation is None else (lease.canonical[0],self.counts,self,lease))
        self.counts['handoff_selected']+=1;self.handoff_summary['consumed']+=1
        try:
            # Bypass only the earlier immutable offer's full-visit ownership;
            # the original native visit, pool/discovery order and checks remain.
            return super(ProbeHandoffSolver,self)._visit(cnf)
        finally:
            self._handoff_canonical=prior;_UP.reset(marker)
            if not lease.retired:self._retire(lease,'visit')
            if lease.charge:
                self._handoff_held-=lease.charge;lease.charge=0
            else:
                assert self.release_early;self._transferred_held-=charge
            assert self._handoff_held>=0 and self._transferred_held>=0

    def _verify(self,key,node):
        marker=_UP.set(None)
        try:return super()._verify(key,node)
        finally:_UP.reset(marker)

    def solve(self,source):
        if self._handoff_active or native._restriction_engine.get() is not None or _UP.get() is not None:
            raise RuntimeError('Lifetime handoff requires an exclusive ordinary-restriction session')
        began=time.perf_counter();self._handoff_active=True
        self.handoff_summary=dict(peak_bytes=0,admissions=0,oversized=0,consumed=0,discarded=0)
        self.lifetime_summary=dict(transferred_peak_bytes=0,full_visit_envelope_peak_bytes=0,
            canonical_retirements=0,propagation_retirements=0,visit_retirements=0,discard_retirements=0)
        try:
            with patch.object(native,'propagate',propagate):result=super(ProbeHandoffSolver,self).solve(source)
        finally:
            self._handoff_active=False
            assert self._handoff_held==self._transferred_held==0
            assert self._waiting_offer is None and self._handoff_canonical is None and self._handoff_verifying==0
            for k,v in self.handoff_summary.items():self.counts['whole_handoff_'+k]=v
            for k,v in self.lifetime_summary.items():self.counts['whole_lifetime_'+k]=v
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        return result
