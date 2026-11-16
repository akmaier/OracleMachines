"""Optional progress gate for the second saved-route trial.

Freeze the first route's unresolved literal mass before acquisition. After its
first completed nested acquisition, skip the second trial only if that mass
strictly decreases (or the whole query is already covered). This is a scheduling
heuristic, not a cost bound. All acquisition and checking use frozen primitives.
"""
import copy
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_nested_refinement import base, selected_children

FORMAT = 'progress-gated-pilot-v1'


class ProgressPilotRefinement(ScopedNestedRefinement):
    def __init__(self, h, root, source, state=None):
        fields = {'format', 'root', 'source', 'candidates', 'completed', 'chosen',
                  'decisions', 'events', 'scores', 'baseline', 'gate'}
        if state is not None and (type(state) is not dict or set(state) != fields
                or state['format'] != FORMAT or state['root'] != root
                or state['source'] != source or type(state['decisions']) is not dict):
            raise ValueError('Foreign progress-pilot state')
        super().__init__(h, root, None if state is None else state['decisions'])
        key = root; seen = set()
        while key != source:
            if key in seen:
                raise ValueError('Cyclic pilot prefix')
            seen.add(key); node = h._load(key)
            children = selected_children(node) if node is not None else []
            if len(children) != 1:
                raise ValueError('Pilot requires a unary prefix to its source')
            key = children[0]
        node = h._load(source)
        if node is None or node['kind'] != 'unresolved':
            raise ValueError('Pilot requires a stored unresolved source')
        self.source = source
        if state is None:
            self.candidates = sorted(self.by_source.get(source, ()), key=self._rank)[:2]
            if len(self.candidates) != 2:
                raise ValueError('Pilot requires two saved alternatives')
            self.completed = 0; self.chosen = None; self.events = []; self.scores = []
            self.decisions[source] = self.candidates[0]
            self.baseline = self._score(); self.gate = None
        else:
            cs = state['candidates']; n = state['completed']; chosen = state['chosen']
            if (type(cs) is not list or len(cs) != 2 or any(type(c) is not str for c in cs)
                    or len(set(cs)) != 2 or any(c not in self.by_source.get(source, ()) for c in cs)
                    or type(n) is not int or not 0 <= n <= 2
                    or (chosen is not None and (chosen not in cs or n == 0))
                    or type(state['events']) is not list or type(state['scores']) is not list):
                raise ValueError('Invalid progress-pilot phase')
            self.candidates = list(cs); self.completed = n; self.chosen = chosen
            self.events = copy.deepcopy(state['events']); self.scores = copy.deepcopy(state['scores'])
            self.baseline = copy.deepcopy(state['baseline']); self.gate = copy.deepcopy(state['gate'])
            if not self._valid_score(self.baseline):
                raise ValueError('Invalid progress baseline')
            if n == 0:
                valid = self.gate is None and chosen is None
            else:
                g = self.gate
                valid = (type(g) is dict and set(g) == {'action', 'after'}
                         and self._valid_score(g['after']) and g['action'] in ('skip', 'explore', 'closed'))
                if valid:
                    action = g['action']; decreased = g['after'][1] < self.baseline[1]
                    valid = ((action == 'closed' and self.coverage.closed()[0])
                             or (action == 'skip' and decreased) or (action == 'explore' and not decreased))
                    if action in ('skip', 'closed'):
                        valid = valid and n == 1 and chosen == cs[0]
                    else:
                        valid = valid and ((n == 1 and chosen is None) or (n == 2 and chosen in cs))
            expected = chosen if chosen is not None else cs[n] if n < 2 else None
            if not valid or self.decisions.get(source) != expected:
                raise ValueError('Inconsistent progress-pilot state')

    @staticmethod
    def _valid_score(score):
        return type(score) is list and len(score) == 4 and all(type(v) is int and v >= 0 for v in score)

    def _score(self):
        tasks = super().frontier()
        return [sum(t['kind'] == 'pending' for t in tasks),
                sum(t['shape']['literals'] for t in tasks), len(tasks),
                self.records[self.decisions[self.source]]['variable']]

    def state(self):
        return copy.deepcopy(dict(format=FORMAT, root=self.root, source=self.source,
            candidates=self.candidates, completed=self.completed, chosen=self.chosen,
            decisions=self.decisions, events=self.events, scores=self.scores,
            baseline=self.baseline, gate=self.gate))

    def _commit(self):
        scores = []
        for identity in self.candidates:
            self.decisions[self.source] = identity
            tasks = super().frontier()
            score = [sum(t['kind'] == 'pending' for t in tasks),
                     sum(t['shape']['literals'] for t in tasks), len(tasks),
                     self.records[identity]['variable']]
            scores.append(dict(identity=identity, score=score,
                               frontier_ids=[base.key_sha(t['source']) for t in tasks]))
        self.scores = scores
        self.chosen = min(scores, key=lambda row: row['score'])['identity']
        self.decisions[self.source] = self.chosen
        self.counts['pilot_commits'] += 1

    def acquire(self, source, variable):
        active = self.chosen is None and self.completed < 2
        before = len(self.h.admitted); probes = self.h.counts['probe_attempts']
        assumptions = self.counts['bootstrap_fresh_assumptions']
        result = super().acquire(source, variable)
        if active:
            self.events.append(dict(candidate_sha256=base.key_sha(self.candidates[self.completed]),
                source_sha256=base.key_sha(source), variable=variable,
                record_sha256=base.key_sha(result['record']), pending=any(result['pending']),
                entered=len(self.h.admitted)-before, probes=self.h.counts['probe_attempts']-probes,
                assumptions=self.counts['bootstrap_fresh_assumptions']-assumptions))
            self.counts['pilot_operation_calls'] += 1
            if not any(result['pending']):
                self.completed += 1; self.counts['pilot_completed_steps'] += 1
                if self.completed == 1:
                    after = self._score()
                    action = ('closed' if self.coverage.closed()[0] else
                              'skip' if after[1] < self.baseline[1] else 'explore')
                    self.gate = dict(action=action, after=after)
                    self.counts['progress_gate_' + action] += 1
                    if action in ('skip', 'closed'):
                        self.chosen = self.candidates[0]
                    else:
                        self.decisions[self.source] = self.candidates[1]
                else:
                    self._commit()
        return result

    def batch(self, **kwargs):
        result = super().batch(**kwargs)
        result['pilot_state'] = self.state()
        return result
