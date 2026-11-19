"""Bounded automatic SAT candidates; complete target checking is the authority.

Vectors are indexed by compact variable count, not by supplied family or donor
labels. Applying a vector to another CNF claims no semantic equivalence. Every
hit satisfies that whole canonical CNF and is checked again on native publication.
"""
from collections import Counter
import json,sys,time
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_residual_dag import FORMAT


class WitnessPoolSolver(BatchedPublicationSolver):
    def __init__(self,*args,pool_capacity=64,candidate_limit=4,max_variables=4096,seed_rows=64,**kwargs):
        if (any(type(v) is not int for v in (pool_capacity,candidate_limit,max_variables,seed_rows))
                or not 1<=candidate_limit<=pool_capacity or max_variables<1 or seed_rows<0):
            raise ValueError('Invalid witness pool limits')
        self.pool_capacity=pool_capacity;self.candidate_limit=candidate_limit
        self.max_witness_variables=max_variables;self.seed_rows=seed_rows
        self.witness_pool={};self._witness_charge=0
        super().__init__(*args,**kwargs);tick=time.perf_counter()
        try:
            # Only hints are reconstructed. Untrusted bytes never authenticate
            # a donor or target; malformed hints can be ignored safely.
            for payload, in self.db.execute('SELECT payload FROM (SELECT rowid,payload FROM cnf_residual_v1 ORDER BY rowid DESC LIMIT ?) ORDER BY rowid',(seed_rows,)):
                self.counts['witness_seed_rows']+=1;self.counts['witness_seed_payload_bytes']+=len(payload.encode())
                try:node=json.loads(payload)
                except (TypeError,ValueError):self.counts['witness_seed_invalid']+=1;continue
                if type(node) is dict and node.get('format')==FORMAT and node.get('answer') is True:
                    self._admit(node.get('model'))
            self.witness_setup_counts=dict(self.counts)
            self.witness_setup_seconds=time.perf_counter()-tick
        except BaseException:self.close();raise

    @staticmethod
    def _charge(entry):
        return sys.getsizeof(entry)+sum(sys.getsizeof(v) for v in entry)+sys.getsizeof(None)

    def _peak(self):
        self.counts['witness_peak_entries']=max(self.counts['witness_peak_entries'],len(self.witness_pool))
        self.counts['witness_peak_bytes']=max(self.counts['witness_peak_bytes'],sys.getsizeof(self.witness_pool)+self._witness_charge)
        assert len(self.witness_pool)<=self.pool_capacity

    def _admit(self,model):
        if type(model) is not list or len(model)>self.max_witness_variables:
            self.counts['witness_admission_skips']+=1;return
        if any(type(b) is not bool for b in model):self.counts['witness_admission_skips']+=1;return
        packed=bytearray((len(model)+7)//8)
        for i,b in enumerate(model):
            if b:packed[i//8]|=1<<(i%8)
        key=(len(model),bytes(packed));self.counts['witness_packed_variables']+=len(model)
        if key in self.witness_pool:
            del self.witness_pool[key];self._witness_charge-=self._charge(key)
            self.counts['witness_refreshes']+=1
        elif len(self.witness_pool)>=self.pool_capacity:
            old=next(iter(self.witness_pool));del self.witness_pool[old];self._witness_charge-=self._charge(old)
            self.counts['witness_evictions']+=1
        self.witness_pool[key]=None;self._witness_charge+=self._charge(key)
        self.counts['witness_admissions']+=1;self._peak()

    def _store(self,key,node):
        super()._store(key,node)
        if node['answer']:self._admit(node['model'])

    def _expand(self,cnf):
        if self.witness_pool and cnf and () not in cnf:
            c=self.counts;c['witness_probes']+=1;c['witness_shape_literals']+=sum(map(len,cnf))
            variables=max(abs(lit) for clause in cnf for lit in clause);tried=0
            for (n,packed) in reversed(self.witness_pool):
                c['witness_index_entries']+=1
                if n!=variables:continue
                tried+=1;c['witness_candidates']+=1;valid=True
                for clause in cnf:
                    c['witness_checked_clauses']+=1;satisfied=False
                    for literal in clause:
                        c['witness_literal_tests']+=1;i=abs(literal)-1
                        if bool(packed[i//8] & (1<<(i%8)))==(literal>0):satisfied=True;break
                    if not satisfied:valid=False;break
                if valid:
                    c['witness_hits']+=1;c['witness_model_variables']+=n
                    return {i+1:bool(packed[i//8] & (1<<(i%8))) for i in range(n)},None
                if tried==self.candidate_limit:break
            c['witness_misses']+=1
        return super()._expand(cnf)

    def solve(self,source):
        tick=time.perf_counter()
        try:result=super().solve(source)
        finally:self._peak()
        result['metrics']=dict(self.counts);result['seconds']=time.perf_counter()-tick
        return result
