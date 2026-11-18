"""Bounded, query-local reuse of exact canonicalization result triples.

Every lookup snapshots and validates literals. No cached result authenticates a
certificate. Bounds apply to retained cache objects after each operation, not
transient input/result construction, allocator overhead or the whole solver.
"""
from contextlib import contextmanager
import sys,time
from experiments.cnf_known_quotient import KnownQuotientSolver


class QueryCanonicalSolver(KnownQuotientSolver):
    def __init__(self,*args,canonical_cache_bytes=128*1024,**kwargs):
        if (type(canonical_cache_bytes) is not int or canonical_cache_bytes<0
                or 0<canonical_cache_bytes<sys.getsizeof({})):
            raise ValueError('Cache capacity must be zero or at least an empty dictionary')
        self.canonical_cache_bytes=canonical_cache_bytes;self.canonical_cache=None;self.canonical_payload=0
        super().__init__(*args,**kwargs)

    def _entry_charge(self,raw,result,max_literal):
        # Tuple containers have measured sizes. Each input/name integer is bounded
        # by the largest validated input integer, each normalized integer by the
        # name count. Overcount shared integers/tuples rather than retaining a
        # second graph of identity bookkeeping for every entry.
        normalized,names,text=result;raw_int=sys.getsizeof(max_literal);normal_int=sys.getsizeof(len(names))
        self.counts['canonical_cache_sized_clauses']+=len(raw)+len(normalized)
        raw_size=sys.getsizeof(raw)+sum(sys.getsizeof(c)+len(c)*raw_int for c in raw)
        normal_size=sys.getsizeof(normalized)+sum(sys.getsizeof(c)+len(c)*normal_int for c in normalized)
        names_size=sys.getsizeof(names)+len(names)*raw_int
        return raw_size+sys.getsizeof(result)+normal_size+names_size+sys.getsizeof(text)+sys.getsizeof((result,0))+sys.getsizeof(self.canonical_cache_bytes)

    def _note_retained(self):
        c=self.counts;size=sys.getsizeof(self.canonical_cache)+self.canonical_payload
        if size>self.canonical_cache_bytes:raise AssertionError('Retained canonical cache exceeds capacity')
        c['canonical_cache_peak_bytes']=max(c['canonical_cache_peak_bytes'],size)
        c['canonical_cache_peak_entries']=max(c['canonical_cache_peak_entries'],len(self.canonical_cache))

    @contextmanager
    def canonical_session(self):
        if self.canonical_cache is not None:raise RuntimeError('Nested canonical cache session')
        if not self.canonical_cache_bytes:
            yield;return
        self.canonical_cache={};self.canonical_payload=0
        try:yield
        finally:
            self.counts['canonical_cache_cleared_entries']+=len(self.canonical_cache)
            self.canonical_cache=None;self.canonical_payload=0

    def _canonical(self,cnf):
        if self.canonical_cache is None:return super()._canonical(cnf)
        c=self.counts;c['canonical_cache_calls']+=1;clauses=[];max_literal=0
        for clause in cnf:
            # Retain the original sequence contract: normalize also requires len.
            length=len(clause);frozen=tuple(clause);c['canonical_cache_snapshot_clauses']+=1
            c['canonical_cache_snapshot_literals']+=length
            for lit in frozen:
                c['canonical_cache_validated_literals']+=1
                if type(lit) is not int or lit==0:raise ValueError('CNF literals must be nonzero integers')
                max_literal=max(max_literal,abs(lit))
            clauses.append(frozen)
        key=tuple(clauses);c['canonical_cache_lookups']+=1
        entry=self.canonical_cache.get(key)
        if entry is not None:
            c['canonical_cache_hits']+=1
            c['canonical_cache_reused_literals']+=sum(map(len,key))
            return entry[0]
        c['canonical_cache_misses']+=1;result=super()._canonical(key)
        # The stored value is (result, charge). An admitted charge is at most the
        # capacity, so the capacity integer's size bounds its integer object.
        charge=self._entry_charge(key,result,max_literal)
        if charge+sys.getsizeof({})>self.canonical_cache_bytes:
            c['canonical_cache_oversized_skips']+=1;self._note_retained();return result
        self.canonical_cache[key]=(result,charge);self.canonical_payload+=charge
        c['canonical_cache_insertions']+=1
        # FIFO bounds bookkeeping cost; hits do not allocate a second recency index.
        while self.canonical_cache and sys.getsizeof(self.canonical_cache)+self.canonical_payload>self.canonical_cache_bytes:
            oldest=next(iter(self.canonical_cache));_,old_charge=self.canonical_cache.pop(oldest)
            self.canonical_payload-=old_charge;c['canonical_cache_evictions']+=1
        if not self.canonical_cache and sys.getsizeof(self.canonical_cache)>self.canonical_cache_bytes:
            self.canonical_cache={};c['canonical_cache_empty_rebuilds']+=1
        self._note_retained();return result

    def solve(self,source):
        began=time.perf_counter()
        with self.canonical_session():result=super().solve(source)
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        result['canonical_cache_capacity']=self.canonical_cache_bytes
        return result
