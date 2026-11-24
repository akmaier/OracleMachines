"""Bounded passive context capture for checked negatives in unfinished search.

No captured context is proof authority. Search counters, choices and native
publication are unchanged. Later extraction must independently check the source
restriction, variable map and conditional certificate. Unsupported transitions
and exhausted capture budgets are explicit misses.
"""
from collections import Counter
from unittest.mock import patch
from experiments import cnf_residual_dag as native
from experiments.cnf_cofactor_handoff import original_propagate
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_partial_residual_pool import charge


class StoppedObserver(LazyBinaryClosureSolver):
    def __init__(self, *args, capture_candidates=256, capture_slots=1000000,
                 capture_pending=4096, capture_key_bytes=4*1024*1024, **kwargs):
        if any(type(x) is not int or x < 1 for x in
               (capture_candidates,capture_slots,capture_pending,capture_key_bytes)):
            raise ValueError('Positive capture limits required')
        self.capture_limits = (capture_candidates,capture_slots,capture_pending,capture_key_bytes)
        self.observe = False
        self.capture = None
        self._observing = False
        super().__init__(*args, **kwargs)

    def _raw_meta(self, parent, assignment):
        if parent is None or any(v not in parent['mapping'] or type(b) is not bool
                                 for v,b in assignment.items()):
            return None
        if parent['up'] is None:
            self._capture_counts['unit_classifications'] += 1
            parent['up'] = (original_propagate(parent['cnf'], self._capture_counts)[0]
                            if any(len(cl)==1 for cl in parent['cnf']) else {})
        fixed, guards = dict(parent['fixed']), dict(parent['guards'])
        for v,b in assignment.items():
            source_v = parent['mapping'][v]
            if source_v in fixed and fixed[source_v] != b:
                return None
            fixed[source_v] = b
            if parent['up'].get(v) != b:
                guards[source_v] = b
        return dict(mapping=parent['mapping'], fixed=fixed, guards=guards)

    def _remember(self, raw, meta):
        if meta is None: return
        slots = sum(map(len,raw)) + len(meta['mapping']) + 2*len(meta['fixed']) + 2*len(meta['guards'])
        _,cap,pending_cap,_ = self.capture_limits
        if len(self._pending)>=pending_cap or self._pending_slots+slots>cap:
            self._capture_counts['pending_limit_skips'] += 1
            return
        old = self._pending.pop(id(raw), None)
        if old is not None: self._pending_slots -= old[2]
        self._pending[id(raw)] = (raw, meta, slots)
        self._pending_slots += slots
        self._capture_counts['pending_peak_slots'] = max(self._capture_counts['pending_peak_slots'], self._pending_slots)

    def _parent(self, cnf):
        if self._expansion_frames and self._expansion_frames[-1] is not None:
            parent = self._expansion_frames[-1]
            if cnf is parent['cnf']: return parent
        return None

    def _record(self, cnf, key, meta, route):
        if meta is None:
            self._capture_counts['unbound_negative_visits'] += 1
            return
        record = dict(key=key, mapping=sorted(meta['mapping'].items()),
            fixed=sorted(meta['fixed'].items()), guards=sorted(meta['guards'].items()), route=route)
        identity = (key,tuple(record['mapping']),tuple(record['fixed']),tuple(record['guards']))
        if identity in self._seen:
            self._capture_counts['duplicate_candidates'] += 1
            return
        cap,_,_,byte_cap = self.capture_limits
        key_bytes = len(key.encode())
        if len(self._candidates)>=cap or self._candidate_key_bytes+key_bytes>byte_cap:
            self._capture_counts['candidate_limit_skips'] += 1
            return
        self._seen.add(identity)
        self._candidates.append(record)
        self._candidate_key_bytes += key_bytes
        self._capture_counts['candidate_context_slots'] += len(record['mapping'])+2*len(record['fixed'])+2*len(record['guards'])
        self._capture_counts['captured_'+route] += 1

    def _visit(self, cnf):
        if not self._observing or self._handoff_verifying:
            return super()._visit(cnf)
        normalized,names = native.normalize(cnf,self._capture_counts)
        key = native.token(normalized,self._capture_counts)
        binding = self._pending.pop(id(cnf),None)
        meta = None
        if binding is not None:
            assert binding[0] is cnf
            self._pending_slots -= binding[2]
            meta = binding[1]
        elif not self._visit_frames and normalized==self._capture_root:
            meta = dict(mapping=dict(zip(names,range(1,len(names)+1))),fixed={},guards={})
        elif self._expansion_frames and self._expansion_frames[-1] is not None:
            parent = self._expansion_frames[-1]
            self._capture_counts['subset_clause_checks'] += len(cnf)
            if set(cnf)<=set(parent['cnf']):
                meta = dict(mapping=parent['mapping'],fixed=parent['fixed'],guards=parent['guards'])
                self._capture_counts['subset_transitions'] += 1
        if meta is not None:
            meta = dict(mapping={i+1:meta['mapping'][v] for i,v in enumerate(names)},
                        fixed=meta['fixed'],guards=meta['guards'])
        frame = dict(cnf=normalized,key=key,meta=meta)
        self._visit_frames.append(frame)
        try:
            model,actual = super()._visit(cnf)
            assert actual==key
            if model is None: self._record(normalized,key,meta,'visit')
            return model,actual
        finally:
            assert self._visit_frames.pop() is frame

    def _expand(self, cnf):
        if not self._observing: return super()._expand(cnf)
        frame = self._visit_frames[-1]
        assert frame['cnf']==cnf
        parent = None if frame['meta'] is None else dict(cnf=cnf,up=None,**frame['meta'])
        self._expansion_frames.append(parent)
        try: return super()._expand(cnf)
        finally: self._expansion_frames.pop()

    def _probe(self, cnf, variable, value):
        result = super()._probe(cnf,variable,value)
        if self._observing and result[0] is not None:
            parent = self._parent(cnf)
            meta = self._raw_meta(parent,{variable:value})
            raw = self._scan(cnf,{variable:value},self._capture_counts)
            normalized,names = native.normalize(raw,self._capture_counts)
            assert native.token(normalized,self._capture_counts)==result[0]
            if meta is not None:
                meta = dict(mapping={i+1:meta['mapping'][v] for i,v in enumerate(names)},
                            fixed=meta['fixed'],guards=meta['guards'])
            self._record(normalized,result[0],meta,'probe')
        return result

    def solve(self, source):
        if not self.observe: return super().solve(source)
        if self._observing: raise RuntimeError('Exclusive capture session required')
        source = tuple(tuple(c) for c in source)
        self._capture_counts = Counter()
        self._capture_root,_ = native.normalize(source,self._capture_counts)
        self._pending = {}; self._pending_slots = 0
        self._candidates = []; self._seen = set(); self._candidate_key_bytes = 0
        self._visit_frames = []; self._expansion_frames = []
        self._scan = native.restrict_scan
        def scan(cnf, assignment, counts=None):
            result = self._scan(cnf,assignment,counts)
            if self._observing and not self._handoff_verifying and counts is self.counts:
                self._remember(result,self._raw_meta(self._parent(cnf),assignment))
            return result
        self._observing = True
        try:
            with patch.object(native,'restrict_scan',scan):
                return super().solve(source)
        finally:
            self._observing = False
            assert not self._visit_frames and not self._expansion_frames
            self.capture = dict(source=[list(c) for c in self._capture_root],
                candidates=self._candidates,counts=dict(self._capture_counts),
                candidate_key_bytes=self._candidate_key_bytes,
                retained_candidate_bytes=charge((self._candidates,self._seen)),
                pending_end_bytes=charge(self._pending),limits=list(self.capture_limits))
            self._pending.clear(); self._seen.clear(); self._candidates=[]
