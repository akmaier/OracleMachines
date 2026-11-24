"""Observe guard-guided probe opportunities without changing native search.

Guard matching proposes a local cofactor. Only an independent unit certificate
on that actual cofactor can establish its negativity; a full-source support may
not survive a component/subset transition. No proposals enter the live solver.
"""
from collections import Counter
from copy import deepcopy
import json
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_observer import StoppedObserver
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_conditional_unit_support import check_template,fixed_pairs
from experiments.cnf_partial_residual_pool import charge


def decode_key(key):
    prefix=native.FORMAT+':'
    if type(key) is not str or not key.startswith(prefix):raise ValueError('Invalid native key')
    cnf=tuple(map(tuple,json.loads(key[len(prefix):])))
    if native.normalize(cnf)[0]!=cnf or native.token(cnf,Counter())!=key:raise ValueError('Noncanonical key')
    return cnf


def proposals(templates,eligible,mapping,fixed,counts):
    inverse={v:k for k,v in mapping.items()};choices={}
    for i in eligible:
        guards=fixed_pairs(templates[i]['assumptions']);counts['guard_candidate_checks']+=1
        counts['guard_pair_checks']+=len(guards)
        if any(v in fixed and fixed[v]!=b for v,b in guards.items()):
            counts['guard_incompatible']+=1;continue
        missing=[(v,b) for v,b in guards.items() if v not in fixed]
        if not missing:counts['guard_already_implied']+=1;continue
        if len(missing)!=1:counts['guard_multiple_missing']+=1;continue
        v,b=missing[0]
        if v not in inverse:counts['guard_missing_absent_variable']+=1;continue
        choices.setdefault((inverse[v],b),[]).append(i)
    return [dict(variable=v,value=b,templates=indices) for (v,b),indices in sorted(choices.items())]


def analyse_event(source,templates,event,counts=None):
    c=Counter() if counts is None else counts;source=tuple(map(tuple,source));members=set(source)
    if native.normalize(source)[0]!=source:raise ValueError('Canonical source required')
    eligible=[i for i,t in enumerate(templates) if check_template(t,c)<=members]
    local=decode_key(event['root']);mapping=dict(event['mapping']);fixed=fixed_pairs(event['fixed'])
    variables={abs(l) for cl in source for l in cl};local_variables={abs(l) for cl in local for l in cl}
    if (len(mapping)!=len(event['mapping']) or set(mapping)!=local_variables or
        any(type(v) is not int or v<=0 or type(w) is not int or w not in variables for v,w in mapping.items()) or
        len(set(mapping.values()))!=len(mapping) or not fixed.keys()<=variables or
        set(mapping.values())&fixed.keys()):raise ValueError('Invalid residual coordinates')
    image={tuple(sorted(mapping[abs(l)]*(1 if l>0 else -1) for l in cl)) for cl in local}
    residual=set(native.restrict_scan(source,fixed,c))
    if not image<=residual:raise ValueError('Residual is not a conditioned source subset')
    candidates=proposals(templates,eligible,mapping,fixed,c)
    if candidates!=event['proposals']:raise ValueError('Changed guard proposals')
    tried={(q['variable'],q['value']) for q in event['tried']};result=[]
    for item in candidates:
        child,names=native.normalize(native.restrict_scan(local,{item['variable']:item['value']},c),c)
        _,trace,conflict=native.propagate(child,c);root=native.token(child,c)
        node=None if conflict is None else dict(format=native.FORMAT,cnf=[list(cl) for cl in child],
            answer=False,proof=dict(kind='units',trace=trace,conflict=conflict))
        result.append(dict(**item,root=root,node=node,tried=(item['variable'],item['value']) in tried,
            different_variable=all(q['variable']!=item['variable'] for q in event['tried'])))
    return dict(whole_residual=image==residual,candidates=result)


class GuardProbeObserver(StoppedObserver):
    def __init__(self,*args,templates=(),event_limit=256,event_key_bytes=8*1024*1024,**kwargs):
        if any(type(n) is not int or n<1 for n in (event_limit,event_key_bytes)):raise ValueError('Positive event bounds required')
        self.guard_templates=deepcopy(list(templates));self.event_limit=event_limit;self.event_key_limit=event_key_bytes
        self.guard_report=None
        super().__init__(*args,**kwargs);self.observe=True

    def _record(self,*args):
        # Preserve source-coordinate tracking, without collecting another bank
        # of source negatives; the preceding origin bank remains the only hint.
        pass

    def _probe(self,cnf,variable,value):
        event=None
        if self._observing and not self._handoff_verifying:
            parent=self._parent(cnf)
            if parent is None:self.guard_counts['unbound_probe_calls']+=1
            else:
                if '_guard_event' not in parent:
                    self.guard_counts['observed_probe_contexts']+=1
                    key=native.token(cnf,self.guard_counts);size=len(key.encode())
                    if len(self.guard_events)>=self.event_limit or self.guard_key_bytes+size>self.event_key_limit:
                        self.guard_counts['event_limit_skips']+=1;parent['_guard_event']=None
                    else:
                        choices=proposals(self.guard_templates,self.guard_eligible,parent['mapping'],parent['fixed'],self.guard_counts)
                        available=[]
                        for choice in choices:
                            child,_=native.normalize(native.restrict_scan(cnf,{choice['variable']:choice['value']},self.guard_counts),self.guard_counts)
                            child_key=native.token(child,self.guard_counts)
                            # Read-only presence lookup, before the ordinary
                            # probe. Never call _read or warm its checked cache.
                            row=self.db.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(child_key,)).fetchone()
                            self.guard_counts['guard_presence_lookups']+=1
                            available.append(dict(root=child_key,present=row is not None,
                                answer=None if row is None else json.loads(row[0])['answer']))
                        event=dict(root=key,mapping=sorted([list(p) for p in parent['mapping'].items()]),
                            fixed=sorted([list(p) for p in parent['fixed'].items()]),proposals=choices,available=available,tried=[])
                        self.guard_events.append(event);self.guard_key_bytes+=size;parent['_guard_event']=event
                event=parent['_guard_event']
        # Bypass only the old observer's negative-record bookkeeping. This is
        # exactly the live lazy solver probe; proposals neither call it nor
        # change its selected variable, retained cache or publication order.
        result=LazyBinaryClosureSolver._probe(self,cnf,variable,value)
        if event is not None:event['tried'].append(dict(variable=variable,value=value,excluded=result[0]))
        return result

    def solve(self,source):
        source=tuple(tuple(c) for c in source);self.guard_counts=Counter();self.guard_events=[];self.guard_key_bytes=0
        canonical,_=native.normalize(source,self.guard_counts);members=set(canonical)
        self.guard_eligible=[i for i,t in enumerate(self.guard_templates) if check_template(t,self.guard_counts)<=members]
        try:return super().solve(source)
        finally:
            self.guard_report=dict(source=[list(c) for c in canonical],eligible=self.guard_eligible,events=self.guard_events,
                counts=dict(self.guard_counts),key_bytes=self.guard_key_bytes,event_graph_bytes=charge(self.guard_events),
                context_capture=self.capture,limits=dict(events=self.event_limit,key_bytes=self.event_key_limit))
