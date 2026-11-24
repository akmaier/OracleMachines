"""Select a bounded guard-guided variable at existing ordinary probe sites.

Hints carry no authority: the unchanged lazy probe checks the actual cofactor.
Coordinates reuse the native canonicalization result; no event graphs or extra
unit propagation are retained. The adapter requires an exclusive synchronous
session, like the inherited preparation handoff.
"""
from collections import Counter
from copy import deepcopy
from unittest.mock import patch
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_probe_handoff import (discover,compile_cover,check_path,
    prefer_ordinary,force_all,TargetedBackboneMixin)
from experiments.cnf_conditional_unit_support import check_template,fixed_pairs
from experiments.cnf_partial_residual_pool import charge


class GuardProbeSolver(LazyBinaryClosureSolver):
    def __init__(self,*args,templates=(),guard_mode='guided',guard_checks=100000,
                 tracking_slots=1000000,tracking_pending=4096,**kwargs):
        if guard_mode not in ('tracking','variable','guided'):raise ValueError('Invalid guard mode')
        if any(type(n) is not int or n<1 for n in (guard_checks,tracking_slots,tracking_pending)):
            raise ValueError('Positive guard/tracking limits required')
        self.guard_templates=deepcopy(list(templates));self.guard_mode=guard_mode
        self.guard_checks=guard_checks;self.tracking_slots=tracking_slots;self.tracking_pending=tracking_pending
        self.guard_active=False;self.guard_summary=None
        super().__init__(*args,**kwargs)

    def _remember_guard(self,raw,parent,assignment):
        if parent is None or any(v not in parent['mapping'] or type(b) is not bool for v,b in assignment.items()):return
        fixed=dict(parent['fixed']);self.guard_counts['fixed_copy_entries']+=len(fixed)
        for v,b in assignment.items():
            source=parent['mapping'][v]
            if source in fixed and fixed[source]!=b:return
            fixed[source]=b
        slots=sum(map(len,raw))+len(parent['mapping'])+2*len(fixed)
        if len(self.guard_pending)>=self.tracking_pending or self.guard_held+slots>self.tracking_slots:
            self.guard_counts['pending_limit_skips']+=1;return
        prior=self.guard_pending.pop(id(raw),None)
        if prior is not None:self.guard_held-=prior['slots']
        self.guard_pending[id(raw)]=dict(raw=raw,mapping=parent['mapping'],fixed=fixed,slots=slots,owner=parent)
        self.guard_held+=slots;parent['pending'].append(id(raw))
        self.guard_counts['pending_peak_slots']=max(self.guard_counts['pending_peak_slots'],self.guard_held)

    def _visit(self,cnf):
        if not self.guard_active or self._handoff_verifying:return super()._visit(cnf)
        binding=self.guard_pending.pop(id(cnf),None)
        if binding is not None:
            assert binding['raw'] is cnf;self.guard_held-=binding['slots']
        elif self.guard_parents and self.guard_parents[-1] is not None:
            parent=self.guard_parents[-1];self.guard_counts['subset_clause_checks']+=len(cnf)
            if set(cnf)<=set(parent['cnf']):
                binding=dict(mapping=parent['mapping'],fixed=parent['fixed'])
                self.guard_counts['subset_transitions']+=1
        frame=dict(raw=cnf,binding=binding,root=not self.guard_frames,canonical=None,meta=None)
        self.guard_frames.append(frame)
        try:return super()._visit(cnf)
        finally:assert self.guard_frames.pop() is frame

    def _canonical(self,cnf):
        result=super()._canonical(cnf)
        if self.guard_active and not self._handoff_verifying and self.guard_frames:
            frame=self.guard_frames[-1]
            if cnf is frame['raw'] and frame['canonical'] is None:
                normalized,names,_=result;frame['canonical']=normalized;binding=frame['binding']
                if frame['root'] and normalized==self.guard_source:
                    frame['meta']=dict(mapping={i:i for i in range(1,len(names)+1)},fixed={})
                elif binding is not None and all(v in binding['mapping'] for v in names):
                    frame['meta']=dict(mapping={i+1:binding['mapping'][v] for i,v in enumerate(names)},fixed=binding['fixed'])
                self.guard_counts['mapped_name_entries']+=len(names)
        return result

    def _expand(self,cnf):
        if not self.guard_active or self._handoff_verifying:return super()._expand(cnf)
        frame=self.guard_frames[-1] if self.guard_frames else None
        parent=None if frame is None or frame['canonical']!=cnf or frame['meta'] is None else dict(cnf=cnf,pending=[],**frame['meta'])
        self.guard_parents.append(parent)
        try:return super()._expand(cnf)
        finally:
            assert self.guard_parents.pop() is parent
            if parent is not None:
                for ident in parent['pending']:
                    item=self.guard_pending.get(ident)
                    if item is not None and item['owner'] is parent:
                        self.guard_held-=item['slots'];del self.guard_pending[ident]
                        self.guard_counts['retired_pending']+=1

    def _guard_choice(self,cnf,ordinary):
        c=self.guard_counts;c['probe_sites']+=1
        if self.guard_mode=='tracking':return ordinary,(False,True)
        parent=self.guard_parents[-1] if self.guard_parents else None
        if parent is None or parent['cnf'] is not cnf:
            c['unbound_sites']+=1;return ordinary,(False,True)
        inverse={v:k for k,v in parent['mapping'].items()};fixed=parent['fixed'];choice=None
        for guard in self.guard_compiled:
            if c['guard_checks']>=self.guard_checks:
                c['guard_budget_sites']+=1;break
            c['guard_checks']+=1;missing=None;eligible=True
            for v,b in guard:
                c['guard_pair_checks']+=1
                if v in fixed:
                    if fixed[v]!=b:eligible=False;break
                elif missing is not None:eligible=False;break
                else:missing=(v,b)
            if not eligible or missing is None or missing[0] not in inverse:continue
            offer=(inverse[missing[0]],missing[1]);c['guard_matches']+=1
            if choice is None or offer<choice:choice=offer
        if choice is None:return ordinary,(False,True)
        variable,value=choice;c['guard_selected_sites']+=1;c['changed_variables']+=variable!=ordinary
        if self.guard_mode=='variable':return variable,(False,True)
        c['true_first_sites']+=value
        return variable,(value,not value)

    def _expand_prepared(self,cnf):
        if not self.guard_active:return super()._expand_prepared(cnf)
        # Mirror the frozen handoff dispatch, changing only probe selection.
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
                        ordinary=min(frequency,key=lambda v:(-frequency[v],v));c['whole_probe_candidates']+=1
                        variable,values=self._guard_choice(cnf,ordinary);offers={}
                        try:
                            for value in values:
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
        if self.guard_active:raise RuntimeError('Exclusive guard session required')
        source=tuple(tuple(cl) for cl in source);self.guard_counts=Counter()
        self.guard_source,_=native.normalize(source,self.guard_counts);members=set(self.guard_source)
        self.guard_compiled=[]
        for template in self.guard_templates:
            support=check_template(template,self.guard_counts)
            self.guard_counts['containment_clauses']+=len(support)
            if support<=members:self.guard_compiled.append(tuple(fixed_pairs(template['assumptions']).items()))
            else:self.guard_counts['deleted_supports']+=1
        self.guard_frames=[];self.guard_parents=[];self.guard_pending={};self.guard_held=0
        scan=native.restrict_scan
        def tracked(cnf,assignment,counts=None):
            raw=scan(cnf,assignment,counts)
            if self.guard_active and not self._handoff_verifying and counts is self.counts:
                parent=self.guard_parents[-1] if self.guard_parents else None
                if parent is not None and cnf is parent['cnf']:self._remember_guard(raw,parent,assignment)
            return raw
        self.guard_active=True
        try:
            with patch.object(native,'restrict_scan',tracked):return super().solve(source)
        finally:
            self.guard_active=False
            assert not self.guard_frames and not self.guard_parents and not self.guard_pending and self.guard_held==0
            self.guard_summary=dict(mode=self.guard_mode,eligible=len(self.guard_compiled),counts=dict(self.guard_counts),
                bank_bytes=charge((self.guard_templates,self.guard_compiled)),pending_end=0,
                limits=dict(guard_checks=self.guard_checks,tracking_slots=self.tracking_slots,tracking_pending=self.tracking_pending))
