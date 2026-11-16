"""Optional bounded refinement of an existing checked conditioning plan.

Heuristic decisions select work, never certify closure. Nested choices follow
stored reductions and commit to one saved split per unresolved source. Exact
canonical leaves are expanded once even when reached along several branches.
Every semantic step and final proof uses the frozen bootstrap/inventory checkers.
"""
from collections import Counter, defaultdict
import json
import time
from experiments import compare_cnf_bootstrap as base
from experiments.cnf_coupled_pivots import selected_children, FrontierIndex
from experiments.cnf_incremental_coverage import CoverageIndex
from experiments.cnf_split_registry import SplitRegistry


class NestedRefinement:
    def __init__(self, h, root, decisions=None):
        self.h, self.root = h, root
        if h._load(root) is None:
            raise ValueError('Missing refinement root')
        self.registry = SplitRegistry(h)
        self.counts = Counter()
        self.coverage = CoverageIndex(h, [root], self.registry, self.counts)
        self.records = {}
        self.by_source = defaultdict(list)
        for identity, payload in h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'):
            self._remember(identity, json.loads(payload))
        self.decisions = dict(decisions or {})
        for source, identity in self.decisions.items():
            if identity not in self.records or self.records[identity]['source'] != source:
                raise ValueError('Unbound saved refinement choice')
            if h._load(source)['kind'] != 'unresolved':
                raise ValueError('Refinement choice must name an unresolved source')
        self.internal = FrontierIndex(h)

    def _remember(self, identity, record):
        if base.split.record_key(record) != identity:
            raise ValueError('Foreign refinement record')
        if identity in self.records:
            if base.encode(self.records[identity]) != base.encode(record):
                raise ValueError('Changed refinement record')
            return
        self.records[identity] = json.loads(base.encode(record))
        self.by_source[record['source']].append(identity)

    def refresh(self):
        self.registry.refresh()
        self.coverage.refresh(self.h, self.registry, self.counts)

    def _rank(self, identity):
        # Existing reductions are inspected; no fresh recognition or lookahead.
        record = self.records[identity];weight = 0;missing = 0
        for branch in record['branches']:
            key = branch['edge']['key']
            if self.h._load(key) is None:
                missing += 1
            else:
                weight += self.internal.literals(self.internal.frontier(key))
        return (missing, weight, record['variable'])

    def frontier(self):
        """Selected AND obligations; saved choices survive subsequent expansion.

        Closure uses the complete checked route graph. The selected frontier is
        a work policy, not a claim that other alternatives are impossible.
        """
        tasks = [];seen = set();active = set();depth_seen = 0
        closed = {self.coverage.keys[i] for i in self.coverage.justified}
        def visit(key, depth):
            nonlocal depth_seen
            depth_seen = max(depth_seen, depth)
            if key in active:raise ValueError('Cyclic selected refinement plan')
            if key in closed:return
            if key in seen:
                self.counts['shared_frontier_visits_avoided'] += 1
                return
            seen.add(key);active.add(key)
            try:
                node = self.h._load(key)
                if node is None:raise ValueError('Unbound selected refinement child')
                if node['kind'] != 'unresolved':
                    for child in selected_children(node):visit(child, depth)
                    return
                if key not in self.decisions and self.by_source.get(key):
                    self.decisions[key] = min(self.by_source[key], key=self._rank)
                    self.counts['saved_splits_selected'] += 1
                identity = self.decisions.get(key)
                if identity is None:
                    tasks.append(dict(kind='leaf',source=key,depth=depth,shape=node['profile']['shape']))
                else:
                    record = self.records[identity]
                    if any(self.h._load(b['edge']['key']) is None for b in record['branches']):
                        tasks.append(dict(kind='pending',source=key,record=identity,depth=depth,shape=node['profile']['shape']))
                    else:
                        for branch in record['branches']:visit(branch['edge']['key'], depth+1)
            finally:active.remove(key)
        visit(self.root, 0)
        self.counts['frontier_walks'] += 1
        self.counts['maximum_external_depth'] = max(self.counts['maximum_external_depth'], depth_seen)
        return sorted(tasks, key=lambda t:(t['kind']!='pending',t['shape']['variables'],t['shape']['literals'],t['source']))

    def acquire(self, source, variable):
        record = base.split.acquire_record(self.h, source, variable, self.counts)
        identity = base.split.record_key(record);self._remember(identity, record)
        self.decisions[source] = identity
        pending = base.acquire(self.h, record)
        self.refresh()
        return dict(source=source,variable=variable,record=identity,pending=pending)

    def batch(self, *, state_limit=128, pair_limit=16):
        """Resume a bounded selected tree; both partial children remain persisted."""
        for value in (state_limit,pair_limit):
            if type(value) is not int or value < 0:raise ValueError('Nonnegative budget required')
        tick = time.perf_counter();h = self.h;h.set_admission_budget(state_limit);h.counts = Counter()
        before = base.rows(h);old_counts = Counter(self.counts);operations=[];reason='pair_limit'
        for _ in range(pair_limit):
            if self.coverage.closed()[0]:reason='closed';break
            tasks = self.frontier()
            if not tasks:raise ValueError('Open selected plan has no work obligation')
            task = tasks[0]
            if task['kind']=='pending':variable=self.records[task['record']]['variable']
            else:
                variables=base.split.choices(h,task['source'],self.counts,1)
                if not variables:raise ValueError('Unresolved source has no conditioning variable')
                variable=variables[0]
            operation=self.acquire(task['source'],variable);operation['selected_depth']=task['depth']
            operations.append(operation)
            if any(operation['pending']):reason='state_limit';break
        if self.coverage.closed()[0]:reason='closed'
        after = base.rows(h);fresh=set(after)-set(before)
        if not before.items() <= after.items() or not fresh <= h.admitted or len(h.admitted)>state_limit:
            raise ValueError('Invalid append/admission accounting')
        frontier=self.frontier()
        return dict(operations=operations,reason=reason,closed=self.coverage.closed()[0],
            entered=len(h.admitted),stored=len(fresh),probes=h.counts['probe_attempts'],
            admitted_ids=sorted(map(base.key_sha,h.admitted)),stored_ids=sorted(map(base.key_sha,fresh)),
            recognition_counts=dict(h.counts),selection_counts=dict(self.counts-old_counts),
            frontier=frontier,decisions=dict(self.decisions),seconds=time.perf_counter()-tick)
