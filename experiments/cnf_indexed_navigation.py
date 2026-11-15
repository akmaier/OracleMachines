"""Use a complete coverage index for the original selector's closure queries.

The caller owns the checked index, immutable historical patterns and fixed
policy, and refreshes it against the COMPLETE checked routes after each append.
No mutation may occur during selection. We check root/flag/catalog binding;
these checks do not replace semantic authority or immutable-object ownership.
Queries outside the indexed original graph use full composition explicitly.
The scheduler and selected internal paths are the frozen baseline algorithms.
"""
from collections import Counter, defaultdict, deque

from experiments.cnf_coupled_pivots import FrontierIndex
from experiments.cnf_probe_window import choices
from experiments.cnf_route_composition import compose
from experiments.cnf_trace_split import verify, record_key
from experiments.cnf_incremental_coverage import catalog


def select(h, routes, evidence, roots, closed, counts, index):
    if list(roots) != index.roots or list(closed) != index.closed():
        raise ValueError('Incorrect indexed original binding or closure flags')
    if index.external != catalog(routes):
        raise ValueError('Refresh the complete coverage catalog before navigation')

    def covered(source):
        if source in index.ids:
            counts['indexed_closure_queries'] += 1
            return index.ids[source] in index.justified
        counts['outside_index_compositions'] += 1
        return compose(h, [source], routes, counts)[0][0]

    return _select(h, routes, evidence, roots, closed, counts, covered)


def _remaining(h, selected, routes, counts, covered):
    """Follow saved forced continuations below these targets, without discovery."""
    latest={rec['source']:rec for rec in routes.windows.values()}
    for rec in routes.continuations.values():
        if rec['offset']>latest[rec['source']].get('offset',0):latest[rec['source']]=rec
    index=FrontierIndex(h);rows=[]
    for row in selected:
        root=row['target'];closed=covered(root);leaves=[]
        todo=deque(index.frontier(root));seen=set()
        while todo and not closed:
            source=todo.popleft()
            if source in seen:continue
            seen.add(source)
            if covered(source):continue
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


def _frontier(h,routes,records,counts,covered):
    by_source=defaultdict(dict)
    for record in records:
        verify(h,record,counts);by_source[record['source']][record_key(record)]=record
    visited=set();active=set();leaves={};pending={};choices=[]

    def walk(key):
        if key in active:raise ValueError('Cyclic retained split frontier')
        if key in visited:return
        if h._load(key) is None:raise ValueError('Missing acquired frontier source')
        if covered(key):
            visited.add(key);counts['split_frontier_closed_skips']+=1;return
        active.add(key)
        try:
            saved=by_source.get(key)
            if saved:
                identity=min(saved);record=saved[identity]
                choices.append(dict(source=key,split=identity))
                for value,edge in zip((False,True),record['edges'],strict=True):
                    if h._load(edge['key']) is None:
                        pending[(identity,value)]=dict(source=key,split=identity,value=value,target=edge['key'])
                    else:walk(edge['key'])
            else:
                # Follow the selected internal plan and saved forced probe chain.
                row=_remaining(h,[dict(source=key,target=key)],routes,counts,covered)[0]
                for leaf in row['leaves']:
                    if leaf['pending']:
                        pending[(leaf['source'],None)]=dict(leaf);continue
                    if leaf['source']==key:leaves[key]=leaf
                    else:walk(leaf['source'])
        finally:active.remove(key)
        visited.add(key);counts['split_frontier_visited_sources']+=1

    for source in sorted(by_source):walk(source)
    return dict(leaves=sorted(leaves.values(),key=lambda row:(row['variables'],sum(map(len,h._load(row['source'])['cnf'])),row['source'])),
                pending=sorted(pending.values(),key=lambda row:(row['source'],row['target'],str(row.get('value')))),
                choices=sorted(choices,key=lambda row:row['source']))


def _select(h, routes, evidence, roots, closed, counts, covered):
    if len(evidence) != 5 or len(roots) != len(closed):
        raise ValueError('Five evidence lists and one closure flag per root required')
    retained = _frontier(h, routes, evidence[3], counts, covered)
    if retained['pending']:
        row = retained['pending'][0]
        split = next((r for r in evidence[3] if record_key(r) == row.get('split')), None)
        if 'split' in row and split is None:
            raise ValueError('Missing retained split record')
        return dict(mode='resume_retained_split' if split else 'resume_retained_probe',
                    source=row['source'], pending_split=split, pending=row,
                    selected_original_cases=[], retained=retained)
    if retained['leaves']:
        return dict(mode='retained_leaf', source=retained['leaves'][0]['source'],
                    pending_split=None, selected_original_cases=[], retained=retained)

    cases = [i for i, flag in enumerate(closed) if not flag]
    rows = _remaining(h, [dict(source=roots[i], target=roots[i]) for i in cases], routes, counts, covered)
    leaves = {}; bindings = {}
    for case, row in zip(cases, rows, strict=True):
        if row['closed'] or not row['leaves']:
            raise ValueError('Stale coverage or missing original frontier')
        for leaf in row['leaves']:
            source = leaf['source']
            if source in leaves and leaves[source] != leaf:
                raise ValueError('Inconsistent shared original leaf')
            leaves[source] = leaf
            bindings.setdefault(source, []).append(case)

    def rank(source):
        cnf = h._load(source)['cnf']
        return (not leaves[source]['pending'], len({abs(l) for c in cnf for l in c}),
                sum(map(len, cnf)), source)

    ordered = sorted(leaves, key=rank)
    navigation = dict(cases=cases, frontiers=rows,
                      ranked_sources=[dict(source=s, rank=list(rank(s)),
                                           selected_original_cases=bindings[s]) for s in ordered])
    if not ordered:
        return dict(mode='all_originals_closed', source=None, pending_split=None,
                    selected_original_cases=[], retained=retained, navigation=navigation)
    source = ordered[0]
    return dict(mode='resume_original_probe' if leaves[source]['pending'] else 'original_leaf',
                source=source, pending_split=None, leaf=leaves[source],
                selected_original_cases=bindings[source], retained=retained, navigation=navigation)
