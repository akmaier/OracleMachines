"""Resumable affine-negative lookup and explicit terminal-first chain replay.

Native acquisition remains unchanged. Only versioned chain checking can use the
extension; after its terminal has been checked, it need not read an alternative
native derivation of that same terminal.
"""
from collections import Counter
from copy import deepcopy
import time

from experiments.cnf_affine_negative import NegativeStore, CHAIN, compose, check_composed
from experiments import compare_cnf_affine_negative as pilot


class TerminalStore(NegativeStore):
    def view(self): return _TerminalView(self, super().view())


class _TerminalView:
    def __init__(self, store, legacy): self.store, self.legacy = store, legacy
    def _canonical(self, source): return self.store.solver._canonical(source)
    def _read(self, root, expected=None, purpose='search'):
        if purpose=='chain_child' and root in self.store.checked:
            self.store.solver.counts['affine_terminal_native_reads_avoided'] += 1
            return self.store.read(root, expected)
        return self.legacy._read(root, expected, purpose)


def store_for(solver):
    if not hasattr(solver,'_affine_terminal_store'):
        solver._affine_terminal_store=TerminalStore(solver)
    return solver._affine_terminal_store


class NegativeChainBank:
    """Checked exact-source negative conclusions in an owned append-only session."""
    def __init__(self, store, records):
        self.store=store;self.entries=set();self.counts=Counter()
        for record in deepcopy(records):
            result=check_composed(store,record)
            if result['answer'] is not False:raise ValueError('Expected negative chain')
            self.entries.add(result['root']);self.counts['affine_chains_checked']+=1
    def lookup(self,source):
        root=self.store.solver._canonical(source)[2];self.counts['affine_chain_lookups']+=1
        if root not in self.entries:return None
        self.counts['affine_chain_hits']+=1
        return dict(root=root,answer=False,model=None)


def evaluate(s,source,target,guards,eligible=True,limit=4):
    if type(limit) is not int or limit != 4:
        raise ValueError('This session version uses the fixed four-variable discovery policy')
    started=time.perf_counter();store=store_for(s)
    tick=time.perf_counter();hit=store.lookup(target);lookup_seconds=time.perf_counter()-tick;lookup_metrics=dict(s.counts)
    if hit is not None:
        tick=time.perf_counter();before=Counter(s.counts);record=compose(store,source,guards,hit)
        r=dict(record=record,admission=None,local_choice=None,child=hit,probe_counts={},probe_metrics={},
               selection_seconds=0.,child_seconds=0.,composition_seconds=time.perf_counter()-tick,
               composition_metrics=dict(s.counts-before),extension=True)
    elif eligible:
        r=pilot.evaluate(s,store,source,target,guards,'negative')
    else:
        r=pilot.prior.evaluate(s,source,target,guards,'affine',False,limit);r['extension']=False
    r.setdefault('admission',None);r.setdefault('local_choice',None)
    r.setdefault('local_eligible',eligible)
    r.setdefault('local_probe',None if r['admission'] is None else r['admission']['discovery'])
    for k,v in dict(premise=None,premise_seconds=0.,guard_counts={},guard_metrics={}).items():r.setdefault(k,v)
    r.update(extension_lookup_hit=hit is not None,extension_lookup_seconds=lookup_seconds,
             extension_lookup_metrics=lookup_metrics,evaluation_seconds=time.perf_counter()-started)
    return r
