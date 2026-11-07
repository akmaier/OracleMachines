"""Indexed elimination and affected-bucket updates.

Plans are proposals, not certificates. A fixed order routes each factor to its
first remaining variable. A changed output invalidates only its successor;
identical outputs stop propagation. Copying/serializing a snapshot and obtaining
the active source set still cost linear work and are counted separately.
"""
import heapq

from solver.resources import BudgetExceeded
from solver.manifests import Manifest


def build(active, read, project, cap, deadline, metrics, preferred=()):
    factors = {name: read(name) for name in active}
    incidence = {}
    neighbors = {}
    heap = []
    constants = set()

    def add(name):
        scope = factors[name]['scope']
        if not scope:
            constants.add(name)
        for v in scope:
            incidence.setdefault(v, set()).add(name)
            counts = neighbors.setdefault(v, {})
            for u in scope:
                counts[u] = counts.get(u, 0) + 1
                metrics['ordering_edges'] += 1

    def remove(name):
        for v in factors[name]['scope']:
            incidence[v].remove(name)
            counts = neighbors[v]
            for u in factors[name]['scope']:
                counts[u] -= 1
                if not counts[u]:
                    del counts[u]
                metrics['ordering_edges'] += 1
        del factors[name]

    for name in factors:
        deadline.check()
        add(name)
    for v in incidence:
        heapq.heappush(heap, (len(neighbors[v]), v))
    order, buckets = [], {}
    old = iter(preferred)
    while heap:
        deadline.check()
        candidate = next((v for v in old if incidence.get(v)), None)
        if candidate is not None and len(neighbors[candidate]) <= cap + 1:
            v = candidate
        else:
            while heap:
                degree, v = heapq.heappop(heap)
                metrics['ordering_candidates'] += 1
                if incidence.get(v) and degree == len(neighbors[v]):
                    break
            else:
                break
        names = sorted(incidence[v])
        touched = set(neighbors[v])
        if len(touched) > cap + 1:
            raise BudgetExceeded('No small interface found within width cap')
        metrics['max_bag'] = max(metrics['max_bag'], len(touched))
        output = project(v, names)
        for name in names:
            remove(name)
        factors[output] = read(output)
        add(output)
        for u in touched:
            if incidence.get(u):
                heapq.heappush(heap, (len(neighbors[u]), u))
        buckets[str(v)] = dict(inputs=names, output=output)
        order.append(v)
        metrics['planned_buckets'] += 1
    return dict(version=1, active=sorted(active), order=order,
                buckets=buckets, constants=sorted(constants))


def update(previous, active, read, project, cap, deadline, metrics):
    """Immutable snapshot update; width failure lets the caller rebuild an order."""
    if previous.get('version') != 1:
        raise ValueError('Unknown elimination plan version')
    order = list(previous['order'])
    if len(set(order)) != len(order):
        raise ValueError('Repeated variable in saved elimination order')
    rank = {v: i for i, v in enumerate(order)}
    old_sources, new_sources = set(previous['active']), set(active)
    added, removed = new_sources - old_sources, old_sources - new_sources
    new_variables = sorted({v for n in added for v in read(n)['scope']} - rank.keys())
    for v in new_variables:
        rank[v] = len(order)
        order.append(v)
    # Unchanged bucket lists are shared. Mutations replace an individual bucket.
    buckets = previous['buckets'].fork() if isinstance(previous['buckets'], Buckets) else dict(previous['buckets'])
    constants = set(previous['constants'])
    metrics['plan_copy_entries'] += (0 if isinstance(buckets,Buckets) else len(buckets)) + len(constants) + len(order)
    metrics['source_comparisons'] += len(old_sources) + len(new_sources)
    pending, dirty = [], set()

    def route(name, adding):
        deadline.check()
        scope = read(name)['scope']
        if not scope:
            if adding:
                constants.add(name)
            else:
                constants.discard(name)
            return
        v = min(scope, key=rank.__getitem__)
        key = str(v)
        previous_bucket = buckets.get(key, dict(inputs=[], output=None))
        inputs = set(previous_bucket['inputs'])
        if adding:
            inputs.add(name)
        else:
            inputs.discard(name)
        if inputs == set(previous_bucket['inputs']):
            return
        buckets[key] = dict(inputs=sorted(inputs), output=previous_bucket['output'])
        if v not in dirty:
            heapq.heappush(pending, (rank[v], v))
            dirty.add(v)
        metrics['dependency_updates'] += 1

    for name in sorted(removed):
        route(name, False)
    for name in sorted(added):
        route(name, True)
    while pending:
        deadline.check()
        _, v = heapq.heappop(pending)
        dirty.remove(v)
        bucket = buckets[str(v)]
        names, old_output = bucket['inputs'], bucket['output']
        bag = {u for n in names for u in read(n)['scope']}
        if len(bag) > cap + 1:
            raise BudgetExceeded('Updated order exceeds interface width cap')
        metrics['max_bag'] = max(metrics['max_bag'], len(bag))
        output = project(v, names) if names else None
        buckets[str(v)] = dict(inputs=names, output=output)
        metrics['affected_buckets'] += 1
        if output != old_output:
            if old_output is not None:
                route(old_output, False)
            if output is not None:
                route(output, True)
        else:
            metrics['propagation_stops'] += 1
    metrics['reused_buckets'] += len(order) - metrics['affected_buckets']
    return dict(version=1, active=sorted(active), order=order,
                buckets=buckets, constants=sorted(constants))


class Buckets:
    """Persistent AVL-backed bucket map; updates copy only changed search paths."""
    def __init__(self,manifest,root):
        self.manifest,self.root=manifest,root
        self.changes={}

    def fork(self):
        if self.changes:raise ValueError('Cannot fork an uncommitted plan')
        return Buckets(self.manifest,self.root)

    def get(self,key,default=None):
        if key in self.changes:return self.changes[key]
        token=self.manifest.get(self.root,key)
        return self.manifest.store.get(token,'elimination_bucket') if token else default

    def __getitem__(self,key):
        result=self.get(key)
        if result is None:raise KeyError(key)
        return result

    def __setitem__(self,key,value):self.changes[key]=value

    def persist(self):
        root=self.root
        for key,value in self.changes.items():
            token=self.manifest.store.put('elimination_bucket',value)[0]
            root=self.manifest.update(root,key,token)
        return root


def save_plan(plan,store,deadline,metrics):
    buckets=plan['buckets']
    if not isinstance(buckets,Buckets):
        indexed=Buckets(Manifest(store,deadline,metrics),None)
        indexed.changes=buckets
        buckets=indexed
    value={k:v for k,v in plan.items() if k!='buckets'}
    value.update(version=2,bucket_root=buckets.persist())
    return store.put('elimination_plan',value)[0]


def load_plan(token,store,deadline,metrics):
    plan=store.get(token,'elimination_plan')
    if plan.get('version')==2:
        plan['buckets']=Buckets(Manifest(store,deadline,metrics),plan.pop('bucket_root'))
        plan['version']=1
    return plan
