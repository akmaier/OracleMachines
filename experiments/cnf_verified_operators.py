"""Ephemeral exact-operator verification reuse for isolated experiments.

No certificate may seed a bank. Entries are immutable descriptions inserted only
by the independent row checker. Scope/incident/source/witness checks run on hits.
The temporary legacy-module hook is restricted to a single-threaded experiment,
restored on exit, and is never installed by production code or persisted.
"""
from collections import Counter, OrderedDict
from contextlib import contextmanager
import sys, threading
from experiments import cnf_semantic_buckets as bucket
native=bucket.native
leaf=bucket.leaf
evaluate=bucket.evaluate
FORMAT=bucket.FORMAT
DEFAULTS=bucket.DEFAULTS
LEGACY_CHECK=bucket.check_certificate


def storage_size(value):
    # Conservative Python object footprint: repeated references count again.
    return sys.getsizeof(value)+sum(storage_size(x) for x in value) if type(value) is tuple else sys.getsizeof(value)


class VerifiedOperators:
    def __init__(self,max_entries=4096,max_bytes=4*1024*1024):
        if type(max_entries) is not int or max_entries<0 or type(max_bytes) is not int or max_bytes<0:raise ValueError('Invalid cache bounds')
        self.max_entries=max_entries;self.max_bytes=max_bytes;self._entries=OrderedDict();self._bytes=0
        self.peak_entries=0;self.peak_bytes=0

    def _key(self,inputs,pivot,reduce,scope,bits,choices,counts):
        bag=sorted({v for f in inputs for v in f['scope']});slots={v:i for i,v in enumerate(bag)}
        counts['verified_operator_key_factors']+=len(inputs)
        counts['verified_operator_key_scope_visits']+=sum(len(f['scope']) for f in inputs)+len(scope)
        return (reduce,slots[pivot],tuple(sorted((tuple(slots[v] for v in f['scope']),f['bits']) for f in inputs)),tuple(slots[v] for v in scope),bits,choices)

    def _contains(self,key,counts):
        hit=key in self._entries;counts['verified_operator_hits' if hit else 'verified_operator_misses']+=1
        return hit

    def _remember(self,key,counts):
        # Only the checker below calls this after every relation and choice row passes.
        size=storage_size(key)+sys.getsizeof(0)
        if not self.max_entries or size>self.max_bytes:counts['verified_operator_unretained']+=1;return
        while len(self._entries)>=self.max_entries or self._bytes+size>self.max_bytes:
            _,old=self._entries.popitem(last=False);self._bytes-=old;counts['verified_operator_evictions']+=1
        self._entries[key]=size;self._bytes+=size
        self.peak_entries=max(self.peak_entries,len(self._entries));self.peak_bytes=max(self.peak_bytes,self._bytes)
        counts['verified_operator_insertions']+=1

    def stats(self):
        return dict(entries=len(self._entries),key_bytes=self._bytes,peak_entries=self.peak_entries,peak_key_bytes=self.peak_bytes,max_entries=self.max_entries,max_bytes=self.max_bytes)


@contextmanager
def installed(session):
    """An experimental adapter; do not use with concurrent/nested execution."""
    if session is not None and type(session) is not VerifiedOperators:raise ValueError('Invalid verifier session')
    if threading.current_thread() is not threading.main_thread() or threading.active_count()!=1:raise RuntimeError('Verifier hook requires an isolated single-threaded process')
    if bucket.check_certificate is not LEGACY_CHECK:raise RuntimeError('Nested or changed verifier hook')
    def checked(source,proof,counts=None):return check_certificate(source,proof,counts,session=session)
    bucket.check_certificate=checked
    try:yield
    finally:bucket.check_certificate=LEGACY_CHECK


def check_certificate(source,proof,counts=None,*,session=None):
    """Retain occurrence checks; reuse only independently verified exact operators."""
    counts=Counter() if counts is None else counts;cnf,names=native.normalize(source,counts)
    if (type(proof) is not dict or set(proof)!={'format','cnf','reduce','limits','steps','status','model'}
            or proof['format']!=FORMAT or proof['cnf']!=list(map(list,cnf)) or type(proof['reduce']) is not bool):
        raise ValueError('Invalid source-bound bucket certificate')
    limits=proof['limits']
    if (type(limits) is not dict or set(limits)!=set(DEFAULTS) or any(type(v) is not int or v<1 for v in limits.values())
            or limits['bag_limit']>12 or type(proof['steps']) is not list):raise ValueError('Invalid bucket limits')
    if any(len(c)>limits['bag_limit'] for c in cnf):
        if proof['steps'] or proof['status']!='unresolved' or proof['model'] is not None:raise ValueError('Wide uncomputed leaf has a verdict')
        return dict(answer=None,model=None)
    factors=[leaf(c) for c in cnf];active=set(range(len(factors)));eliminated=set()
    for step in proof['steps']:
        if type(step) is not dict or set(step)!={'variable','inputs','scope','bits','choices'}:raise ValueError('Invalid bucket step')
        v=step['variable'];ids=step['inputs'];scope=step['scope'];bits=step['bits'];choices=step['choices']
        if type(v) is not int or v in eliminated or type(ids) is not list or any(type(i) is not int for i in ids):raise ValueError('Invalid eliminated variable')
        expected=sorted(i for i in active if v in factors[i]['scope'])
        if not ids or ids!=expected:raise ValueError('Incomplete incident bucket')
        boundary=sorted({x for i in ids for x in factors[i]['scope']}-{v})
        if len(boundary)+1>limits['bag_limit']:raise ValueError('Oversized bucket')
        if (type(scope) is not list or any(type(x) is not int for x in scope) or scope!=sorted(set(scope)) or not set(scope)<=set(boundary)
                or type(bits) is not int or not 0<=bits<1<<(1<<len(scope))
                or type(choices) is not int or not 0<=choices<1<<(1<<len(boundary))):raise ValueError('Invalid relation encoding')
        if not proof['reduce'] and scope!=boundary:raise ValueError('Unexpected scope reduction')
        inputs=[factors[i] for i in ids]
        key=None if session is None else session._key(inputs,v,proof['reduce'],scope,bits,choices,counts)
        hit=session is not None and session._contains(key,counts)
        if hit:
            counts['verified_operator_saved_rows']+=1<<len(boundary)
            counts['verified_operator_saved_nonconstant_rows' if scope else 'verified_operator_saved_constant_rows']+=1<<len(boundary)
            counts['verified_operator_saved_probes']+=2*(1<<len(boundary))*len(ids)
        else:
            for row in range(1<<len(boundary)):
                assignment={x:bool(row>>i & 1) for i,x in enumerate(boundary)};feasible=[]
                for value in (False,True):
                    assignment[v]=value;outcomes=[]
                    for i in ids:
                        outcomes.append(evaluate(factors[i],assignment));counts['bucket_verify_table_probes']+=1
                    if all(outcomes):feasible.append(value)
                output=evaluate(dict(scope=scope,bits=bits),assignment)
                if output!=bool(feasible):raise ValueError('Changed projected relation or omitted dependence')
                choice=bool(choices>>row & 1)
                if feasible and choice!=feasible[0] or not feasible and choice:raise ValueError('Invalid reconstruction choice')
                counts['bucket_verified_rows']+=1
            if session is not None:session._remember(key,counts)
        active.difference_update(ids);active.add(len(factors));factors.append(dict(scope=scope,bits=bits));eliminated.add(v)
        counts['bucket_checked_steps']+=1
    status=proof['status'];model=proof['model']
    if status=='unresolved':
        if model is not None:raise ValueError('Open bucket has a model')
        return dict(answer=None,model=None)
    if status=='unsat':
        if model is not None or not any(factors[i]['bits']==0 for i in active):raise ValueError('Missing empty relation')
        return dict(answer=False,model=None)
    if status!='sat' or any(factors[i]['scope'] or factors[i]['bits']!=1 for i in active):raise ValueError('Nonterminal bucket SAT claim')
    if type(model) is not list or len(model)!=len(names) or any(type(v) is not bool for v in model):raise ValueError('Incomplete SAT witness')
    assignment={i:v for i,v in enumerate(model,1)}
    if not native.holds(cnf,assignment):raise ValueError('Reconstructed witness violates source')
    return dict(answer=True,model={name:model[i] for i,name in enumerate(names)})
