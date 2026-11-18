"""Bounded pure-normalization reuse from child acquisition to negative checking.

Only _visit produces entries and only _negative_child looks them up. A hit
substitutes a pure immutable triple; the original child-key/UNSAT checks remain.
No result is authenticated by this memo, and it never survives a source query.
"""
import sys,time
from experiments.cnf_publication_batches import BatchedPublicationSolver


class ProofNormalizationSolver(BatchedPublicationSolver):
    def __init__(self,*args,proof_memo_bytes=128*1024,**kwargs):
        if type(proof_memo_bytes) is not int or proof_memo_bytes<sys.getsizeof({}):
            raise ValueError('Proof memo must hold at least an empty dictionary')
        self.proof_memo_bytes=proof_memo_bytes;self._proof_memo=None;self._proof_payload=0
        self._producer_input=None;self._consumer_input=None
        super().__init__(*args,**kwargs)

    def _charge(self,raw,result):
        cnf,names,key=result
        # The ordinary normalizer has already validated every producer literal.
        # Bound all raw/name integer objects, including tautologies/empty collapse.
        maximum=max((max(map(abs,c),default=0) for c in raw),default=0)
        raw_int=sys.getsizeof(maximum);normal_int=sys.getsizeof(len(names))
        self.counts['proof_memo_sizing_literals']+=sum(map(len,raw))
        self.counts['proof_memo_sizing_clauses']+=len(raw)+len(cnf)
        return (sys.getsizeof(raw)+sum(sys.getsizeof(c)+len(c)*raw_int for c in raw)
            +sys.getsizeof(result)+sys.getsizeof(cnf)+sum(sys.getsizeof(c)+len(c)*normal_int for c in cnf)
            +sys.getsizeof(names)+len(names)*raw_int+sys.getsizeof(key)
            +sys.getsizeof((result,0))+sys.getsizeof(self.proof_memo_bytes))

    def _peak(self):
        size=sys.getsizeof(self._proof_memo)+self._proof_payload
        if size>self.proof_memo_bytes:raise AssertionError('Proof memo exceeds retained-object cap')
        c=self.counts;c['proof_memo_peak_bytes']=max(c['proof_memo_peak_bytes'],size)
        c['proof_memo_peak_entries']=max(c['proof_memo_peak_entries'],len(self._proof_memo))

    def _canonical(self,cnf):
        if self._proof_memo is None:return super()._canonical(cnf)
        if cnf is self._consumer_input:
            self._consumer_input=None;raw=tuple(tuple(c) for c in cnf);c=self.counts
            c['proof_memo_lookups']+=1;c['proof_memo_consumer_literals']+=sum(map(len,raw))
            # Python compares True/1.0 equal to 1: reject before any memo hit.
            if any(type(lit) is not int or not lit for clause in raw for lit in clause):
                raise ValueError('CNF literals must be nonzero integers')
            entry=self._proof_memo.get(raw)
            if entry is not None:
                c['proof_memo_hits']+=1;c['proof_memo_reused_literals']+=sum(map(len,raw))
                return entry[0]
            c['proof_memo_misses']+=1;return super()._canonical(raw)
        if cnf is self._producer_input:
            self._producer_input=None;raw=tuple(tuple(c) for c in cnf)
            result=super()._canonical(raw);c=self.counts;c['proof_memo_producers']+=1
            c['proof_memo_producer_snapshot_clauses']+=len(raw)
            c['proof_memo_producer_snapshot_literals']+=sum(map(len,raw))
            charge=self._charge(raw,result)
            if charge+sys.getsizeof({})>self.proof_memo_bytes:
                c['proof_memo_oversized_skips']+=1;self._peak();return result
            previous=self._proof_memo.get(raw)
            if previous is not None:self._proof_payload-=previous[1];c['proof_memo_replacements']+=1
            self._proof_memo[raw]=(result,charge);self._proof_payload+=charge;c['proof_memo_admissions']+=1
            while self._proof_memo and sys.getsizeof(self._proof_memo)+self._proof_payload>self.proof_memo_bytes:
                _,old=self._proof_memo.pop(next(iter(self._proof_memo)))
                self._proof_payload-=old;c['proof_memo_evictions']+=1
            if not self._proof_memo and sys.getsizeof(self._proof_memo)>self.proof_memo_bytes:self._proof_memo={}
            self._peak();return result
        return super()._canonical(cnf)

    def _visit(self,cnf):
        prior=self._producer_input;self._producer_input=cnf
        try:return super()._visit(cnf)
        finally:self._producer_input=prior

    def _negative_child(self,child_key,cnf):
        prior=self._consumer_input;self._consumer_input=cnf
        try:return super()._negative_child(child_key,cnf)
        finally:self._consumer_input=prior

    def solve(self,source):
        if self._proof_memo is not None:raise RuntimeError('Nested proof-memo query')
        began=time.perf_counter();self._proof_memo={};self._proof_payload=0
        try:result=super().solve(source)
        finally:
            self.counts['proof_memo_cleared_entries']+=len(self._proof_memo)
            self._proof_memo=None;self._proof_payload=0
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-began
        result['proof_memo_capacity']=self.proof_memo_bytes
        return result
