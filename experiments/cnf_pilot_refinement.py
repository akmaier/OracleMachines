"""Optional two-route pilot, sharing the ordinary batch admission budget.

Try one completed nested acquisition on each of two saved choices, then rank
their remaining selected frontiers. Partial acquisitions must finish before a
pilot changes routes. Every result remains in the authoritative inventory.
Scores and restart state schedule work; only the frozen checker proves closure.
"""
import copy
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_nested_refinement import base, selected_children

FORMAT = 'two-route-pilot-v1'


class PilotRefinement(ScopedNestedRefinement):
    def __init__(self, h, root, source, state=None):
        if state is not None:
            if (type(state) is not dict or set(state) != {'format','root','source','candidates','completed','chosen','decisions','events','scores'}
                    or state['format'] != FORMAT or state['root'] != root or state['source'] != source
                    or type(state['decisions']) is not dict):
                raise ValueError('Foreign pilot state')
        super().__init__(h,root,None if state is None else state['decisions'])
        # The pilot concerns the sole source below a unary root prefix. It does
        # not attribute unrelated component work to one of its candidate arms.
        key=root;seen=set()
        while key != source:
            if key in seen:raise ValueError('Cyclic pilot prefix')
            seen.add(key);node=h._load(key)
            children=selected_children(node) if node is not None else []
            if len(children)!=1:raise ValueError('Pilot requires a unary prefix to its source')
            key=children[0]
        node=h._load(source)
        if node is None or node['kind']!='unresolved':raise ValueError('Pilot requires a stored unresolved source')
        self.source=source
        if state is None:
            self.candidates=sorted(self.by_source.get(source,()),key=self._rank)[:2]
            if len(self.candidates)!=2:raise ValueError('Pilot requires two saved alternatives')
            self.completed=0;self.chosen=None;self.events=[];self.scores=[]
            self.decisions[source]=self.candidates[0]
        else:
            cs=state['candidates'];n=state['completed'];chosen=state['chosen']
            if (type(cs) is not list or len(cs)!=2 or any(type(c) is not str for c in cs) or len(set(cs))!=2
                    or any(c not in self.by_source.get(source,()) for c in cs)
                    or type(n) is not int or not 0<=n<=2 or (chosen is not None and (chosen not in cs or n!=2))
                    or type(state['events']) is not list or type(state['scores']) is not list
                    or self.decisions.get(source) not in cs):
                raise ValueError('Invalid pilot scheduling state')
            self.candidates=list(cs);self.completed=n;self.chosen=chosen
            self.events=copy.deepcopy(state['events']);self.scores=copy.deepcopy(state['scores'])
            if not self.coverage.closed()[0]:
                expected=chosen if n==2 else cs[n]
                if expected is None or self.decisions[source]!=expected:
                    raise ValueError('Inconsistent pilot phase')

    def state(self):
        return copy.deepcopy(dict(format=FORMAT,root=self.root,source=self.source,
            candidates=self.candidates,completed=self.completed,chosen=self.chosen,
            decisions=self.decisions,events=self.events,scores=self.scores))

    def _commit(self):
        scores=[]
        for identity in self.candidates:
            self.decisions[self.source]=identity
            tasks=super().frontier()
            score=[sum(t['kind']=='pending' for t in tasks),
                   sum(t['shape']['literals'] for t in tasks),len(tasks),self.records[identity]['variable']]
            scores.append(dict(identity=identity,score=score,frontier_ids=[base.key_sha(t['source']) for t in tasks]))
        self.scores=scores;self.chosen=min(scores,key=lambda row:row['score'])['identity']
        self.decisions[self.source]=self.chosen;self.counts['pilot_commits']+=1

    def acquire(self, source, variable):
        active=self.completed<2
        before=len(self.h.admitted);probes=self.h.counts['probe_attempts'];assumptions=self.counts['bootstrap_fresh_assumptions']
        result=super().acquire(source,variable)
        if active:
            self.events.append(dict(candidate_sha256=base.key_sha(self.candidates[self.completed]),
                source_sha256=base.key_sha(source),variable=variable,record_sha256=base.key_sha(result['record']),
                pending=any(result['pending']),entered=len(self.h.admitted)-before,
                probes=self.h.counts['probe_attempts']-probes,assumptions=self.counts['bootstrap_fresh_assumptions']-assumptions))
            self.counts['pilot_operation_calls']+=1
            if not any(result['pending']):
                self.completed+=1;self.counts['pilot_completed_steps']+=1
                if not self.coverage.closed()[0]:
                    if self.completed<2:self.decisions[self.source]=self.candidates[self.completed]
                    else:self._commit()
        return result

    def batch(self, **kwargs):
        result=super().batch(**kwargs)
        result['pilot_state']=self.state()
        return result
