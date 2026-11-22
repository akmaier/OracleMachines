"""Query-local pure normalization reuse, produced only by cofactor probes.

This narrows the earlier general/proof-normalization memos to probe producers
and native visit/negative-child consumers. Every original proof check remains.
The memo is bounded, ephemeral, and cannot authenticate any SAT/UNSAT answer.
"""
from contextlib import contextmanager
import sys
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_bipolar_routing import probe_child as original_probe_child


class PreparedCofactorSolver(InputSafeAffineProbeSolver):
    def __init__(self,*args,cofactor_bytes=256*1024,**kwargs):
        if type(cofactor_bytes) is not int or cofactor_bytes<sys.getsizeof({}):
            raise ValueError('Cofactor capacity must hold an empty dictionary')
        self.cofactor_bytes=cofactor_bytes;self._cofactors=None;self._cofactor_payload=0
        self._cofactor_producer=False;self._cofactor_consumer=None;self.cofactor_summary=None
        super().__init__(*args,**kwargs)

    @contextmanager
    def cofactor_session(self):
        if self._cofactors is not None:raise RuntimeError('Nested cofactor session')
        self._cofactors={};self._cofactor_payload=0
        self.cofactor_summary=dict(peak_bytes=sys.getsizeof({}),peak_entries=0,hits=0,admissions=0,evictions=0,oversized=0)
        try:yield
        finally:
            self.cofactor_summary['cleared_entries']=len(self._cofactors)
            self._cofactors=None;self._cofactor_payload=0
            self._cofactor_producer=False;self._cofactor_consumer=None

    def _note_cofactors(self):
        size=sys.getsizeof(self._cofactors)+self._cofactor_payload
        assert size<=self.cofactor_bytes
        self.cofactor_summary['peak_bytes']=max(size,self.cofactor_summary['peak_bytes'])
        self.cofactor_summary['peak_entries']=max(len(self._cofactors),self.cofactor_summary['peak_entries'])
        self.counts['prepared_cofactor_peak_bytes']=max(size,self.counts['prepared_cofactor_peak_bytes'])

    def _cofactor_charge(self,raw,result):
        cnf,names,key=result;maximum=max((max(map(abs,c),default=0) for c in raw),default=0)
        a=sys.getsizeof(maximum);b=sys.getsizeof(len(names));self.counts['prepared_cofactor_sizing_literals']+=sum(map(len,raw))
        return (sys.getsizeof(raw)+sum(sys.getsizeof(c)+len(c)*a for c in raw)
            +sys.getsizeof(result)+sys.getsizeof(cnf)+sum(sys.getsizeof(c)+len(c)*b for c in cnf)
            +sys.getsizeof(names)+len(names)*a+sys.getsizeof(key)
            +sys.getsizeof((result,0))+sys.getsizeof(self.cofactor_bytes))

    def _canonical(self,cnf):
        if self._cofactors is None:return super()._canonical(cnf)
        if self._cofactor_producer:
            self._cofactor_producer=False;raw=tuple(tuple(c) for c in cnf);result=super()._canonical(raw)
            self.counts['prepared_cofactor_producers']+=1
            self.counts['prepared_cofactor_snapshot_literals']+=sum(map(len,raw))
            charge=self._cofactor_charge(raw,result)
            if charge+sys.getsizeof({})>self.cofactor_bytes:
                self.counts['prepared_cofactor_oversized']+=1;self.cofactor_summary['oversized']+=1
                self._note_cofactors();return result
            old=self._cofactors.get(raw)
            if old is not None:self._cofactor_payload-=old[1]
            self._cofactors[raw]=(result,charge);self._cofactor_payload+=charge
            self.counts['prepared_cofactor_admissions']+=1;self.cofactor_summary['admissions']+=1
            while self._cofactors and sys.getsizeof(self._cofactors)+self._cofactor_payload>self.cofactor_bytes:
                _,amount=self._cofactors.pop(next(iter(self._cofactors)));self._cofactor_payload-=amount
                self.counts['prepared_cofactor_evictions']+=1;self.cofactor_summary['evictions']+=1
            if not self._cofactors and sys.getsizeof(self._cofactors)>self.cofactor_bytes:self._cofactors={}
            self._note_cofactors();return result
        if cnf is self._cofactor_consumer:
            self._cofactor_consumer=None
            # With no produced entry there is no lookup/snapshot tax.
            if not self._cofactors:return super()._canonical(cnf)
            raw=tuple(tuple(c) for c in cnf);self.counts['prepared_cofactor_lookups']+=1
            self.counts['prepared_cofactor_consumer_literals']+=sum(map(len,raw))
            if any(type(l) is not int or not l for c in raw for l in c):raise ValueError('CNF literals must be nonzero integers')
            entry=self._cofactors.get(raw)
            if entry is not None:
                self.counts['prepared_cofactor_hits']+=1;self.cofactor_summary['hits']+=1
                self.counts['prepared_cofactor_reused_literals']+=sum(map(len,raw))
                return entry[0]
            self.counts['prepared_cofactor_misses']+=1
            return super()._canonical(raw)
        return super()._canonical(cnf)

    def _visit(self,cnf):
        prior=self._cofactor_consumer;self._cofactor_consumer=cnf
        try:return super()._visit(cnf)
        finally:self._cofactor_consumer=prior

    def _negative_child(self,key,cnf):
        prior=self._cofactor_consumer;self._cofactor_consumer=cnf
        try:return super()._negative_child(key,cnf)
        finally:self._cofactor_consumer=prior

    def prepare_probe(self,cnf,variable,value):
        prior=self._cofactor_producer;self._cofactor_producer=True
        try:return original_probe_child(self,cnf,variable,value)
        finally:self._cofactor_producer=prior


def prepared_probe_child(solver,cnf,variable,value):
    return solver.prepare_probe(cnf,variable,value)
