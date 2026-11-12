"""Compare early and near-frontier pivot deviations, reusing checked trials.

The frontier policy ranks by longest selected open path to a terminal node.
It changes only search order; no old proof or recognizer policy is overwritten.
"""
from collections import defaultdict, deque
from experiments.cnf_pivot_alternatives import (
    alternatives, open_ancestors, selected_pivot, verify_trial, covered)
from experiments.cnf_interacting_pivots import rank_interactions
from experiments.cnf_variable_elimination import _limit
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_pattern_inventory import encode


def frontier_ancestors(h, root, limit, counts):
    """Select at most limit elimination nodes closest to selected open terminals.

    All selected open nodes are visited. Heights are longest-path distances,
    with breadth-first discovery order breaking ties. Shared children count
    once per parent; no variable-renaming or semantic quotient is inferred.
    """
    _limit(limit)
    if not limit:return []
    todo=deque([root]);seen=set();nodes={};children={};parents=defaultdict(list)
    while todo:
        key=todo.popleft()
        if key in seen:continue
        seen.add(key);node=h._load(key);counts['ancestor_nodes_visited']+=1
        if node is None:raise ValueError('Missing source plan')
        if node['summary']['closed']:continue
        nodes[key]=node
        if node['kind']=='and':edges=node['edges']
        elif node['kind']=='or':edges=node['alternatives'][node['selected']]['edges']
        elif 'edge' in node:edges=[node['edge']]
        elif node['kind']=='unresolved':edges=[]
        else:raise ValueError('Unknown open plan kind')
        children[key]=list(dict.fromkeys(e['key'] for e in edges))
        counts['ancestor_edges_visited']+=len(edges);todo.extend(children[key])
    for key,edges in children.items():
        children[key]=[child for child in edges if child in nodes]
        for child in children[key]:parents[child].append(key)
    pending={key:len(edges) for key,edges in children.items()}
    queue=deque(key for key,n in pending.items() if n==0);heights={};maximum=defaultdict(int)
    while queue:
        key=queue.popleft();heights[key]=maximum[key]
        for parent in parents[key]:
            maximum[parent]=max(maximum[parent],heights[key]+1);pending[parent]-=1
            if pending[parent]==0:queue.append(parent)
    if len(heights)!=len(nodes):raise ValueError('Cyclic selected plan')
    candidates=[key for key in nodes if nodes[key]['kind']=='eliminate']
    # Python's stable sort retains BFS insertion order at equal height.
    candidates.sort(key=lambda key:heights[key]);selected=candidates[:limit]
    counts['available_elimination_ancestors']+=len(candidates)
    counts['selected_ancestor_heights']+=sum(heights[key] for key in selected)
    counts['selected_ancestors']+=len(selected)
    return selected


def search(h,root,counts,known_trials,*,policy='frontier',ancestor_limit=4,trial_limit=8):
    """At most T new trial recognitions; exact old trials do not spend that cap.

    Caller persists returned records and supplies a mapping of previous trials.
    Cache hits are independently checked before use; failed hits only skip that
    same source/pivot/configuration, not other continuations of the target.
    """
    _limit(ancestor_limit);_limit(trial_limit)
    if policy not in ('early','frontier'):raise ValueError('Unknown ancestor policy')
    if not trial_limit:return []
    select=open_ancestors if policy=='early' else frontier_ancestors
    sources=select(h,root,ancestor_limit,counts);candidates=[]
    for key in sources:
        node=h._load(key);pivot=selected_pivot(node)
        rows=alternatives(node['cnf'],pivot,counts,pair_limit=h.config['elimination_pair_limit'],
            candidate_limit=h.config['elimination_candidate_limit'],clause_growth_limit=h.config['clause_growth_limit'])
        rows,neighbors=rank_interactions(node['cnf'],pivot,rows,counts)
        candidates.append((key,rows,neighbors))
    records=[];successes=set()
    for rank in range(max((len(rows) for _,rows,_ in candidates),default=0)):
        for key,rows,neighbors in candidates:
            if rank>=len(rows) or key in successes:continue
            row=rows[rank];identity=encode([key,row['variable']])
            if identity in known_trials:
                record=known_trials[identity]
                if record['source']!=key or record['variable']!=row['variable']:
                    raise ValueError('Incorrect cached trial binding')
                if verify_trial(h,record,counts):successes.add(key)
                counts['reused_trials']+=1
            else:
                node=h._load(key)
                target=check_additive_elimination(node['cnf'],dict(variable=row['variable']),counts,
                    pair_limit=h.config['elimination_pair_limit'],clause_growth_limit=h.config['clause_growth_limit'])
                if target!=row['target']:raise ValueError('Incorrect proposed target')
                edge=h._edge(target,node['depth']);summary=h._load(edge['key'])['summary']
                record=dict(source=key,variable=row['variable'],edge=edge,summary=summary)
                if verify_trial(h,record,counts):successes.add(key)
                records.append(record);counts['recognition_trials']+=1
                counts['interacting_trials' if row['variable'] in neighbors else 'independent_trials']+=1
            if len(records)>=trial_limit or covered(h,root,successes,counts):return records
    return records
