"""Bounded continuation on acquired targets, with one shared admission budget.

Clear blocks advance the same source; forced blocks follow their exact child.
Every call to advance consumes a step, including reuse or exhaustion, so neither
saved paths nor a large empty frontier can hide unbounded probe iteration.
"""
from collections import Counter, deque

from experiments.cnf_coupled_pivots import FrontierIndex, AdmissionExhausted
from experiments.cnf_probe_window import choices
from experiments.cnf_route_composition import compose
from experiments.cnf_variable_elimination import _limit


def search(h, root, routes, counts, *, step_limit=8, source_limit=4, state_limit=32):
    for limit in (step_limit,source_limit,state_limit): _limit(limit)
    h.set_admission_budget(state_limit)
    index=FrontierIndex(h);todo=deque(sorted(index.frontier(root)));seen=set();visits=[];stop=None
    while todo and len(visits)<step_limit:
        source=todo.popleft()
        if compose(h,[source],routes,counts)[0][0]:
            counts['already_covered_targets_skipped']+=1;continue
        if source not in seen and len(seen)>=source_limit:
            todo.appendleft(source);stop='source_limit';break
        seen.add(source)
        kind,record,target=routes.advance(h,source,counts)
        visits.append(dict(source=source,kind=kind,offset=None if record is None else record.get('offset',0),
            status=None if record is None else record['probing']['status']))
        if record is None:continue
        if record['edge'] is None:
            # Prefix evidence is retained by advance; the next step reuses it.
            todo.appendleft(source);continue
        try:edge=h._edge(target,h._load(source)['depth'])
        except AdmissionExhausted:
            stop='admission_limit';todo.appendleft(source);break
        if edge!=record['edge']:raise ValueError('Incorrect acquired target binding')
        if kind=='probe_window':routes.add_window(h,record)
        else:routes.add_continuation(h,record)
        todo.extendleft(reversed(sorted(index.frontier(edge['key']))))
    if todo and stop is None:stop='step_limit'
    routes.refresh(h);counts.update(index.counts)
    return dict(visits=visits,stop=stop,distinct_sources=len(seen),queued_sources=list(todo))


def targets(h, learning, counts):
    """Order the three retained learned targets by smallest selected leaf first."""
    index=FrontierIndex(h);rows=[]
    for record in learning:
        if record['edge'] is None:continue
        key=record['edge']['key']
        if h._load(key) is None:raise ValueError('Pending parent target requires acquisition first')
        leaves=index.frontier(key)
        rank=min(((len({abs(l) for c in h._load(k)['cnf'] for l in c}),
                   sum(map(len,h._load(k)['cnf']))) for k in leaves),default=(0,0))
        rows.append(dict(source=record['source'],target=key,rank=list(rank)))
    counts.update(index.counts)
    return sorted(rows,key=lambda row:(row['rank'],row['source']))


def remaining(h, selected, routes, counts):
    """Follow saved forced continuations below these targets, without discovery."""
    latest={rec['source']:rec for rec in routes.windows.values()}
    for rec in routes.continuations.values():
        if rec['offset']>latest[rec['source']].get('offset',0):latest[rec['source']]=rec
    index=FrontierIndex(h);rows=[]
    for row in selected:
        root=row['target'];closed=compose(h,[root],routes,counts)[0][0];leaves=[]
        todo=deque(index.frontier(root));seen=set()
        while todo and not closed:
            source=todo.popleft()
            if source in seen:continue
            seen.add(source)
            if compose(h,[source],routes,counts)[0][0]:continue
            record=latest.get(source)
            if record is not None and record['edge'] is not None:
                child=h._load(record['edge']['key'])
                if child is not None:
                    todo.extend(index.frontier(record['edge']['key']));continue
                leaves.append(dict(source=source,pending=True,target=record['edge']['key']));continue
            node,ranked=choices(h,source,64,counts)
            used=0 if record is None else record.get('offset',0)+len(record['probing']['attempts'])//2
            leaves.append(dict(source=source,pending=False,variables=len({abs(l) for c in node['cnf'] for l in c}),
                clauses=len(node['cnf']),minimum_width=min(map(len,node['cnf'])),
                original_status=node['profile']['probing']['status'],next_offset=used,
                remaining_ranked_variables=ranked[used:]))
        rows.append(dict(source=row['source'],target=root,closed=closed,leaves=leaves))
    counts.update(index.counts)
    return rows
