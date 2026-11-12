"""Bounded one-pivot deviations over an immutable, checked recognition history.

Every candidate uses exact projection with the existing growth/pair limits.
A successful child may supplement an old plan; failure excludes no SAT class.
"""
from collections import Counter, defaultdict, deque
from experiments.cnf_variable_elimination import _source, _limit
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_pattern_inventory import encode


def alternatives(cnf, selected, counts, *, pair_limit=64, candidate_limit=64, clause_growth_limit=2):
    for limit in (pair_limit,candidate_limit,clause_growth_limit): _limit(limit)
    if selected is not None and (type(selected) is not int or selected<=0):
        raise ValueError('Invalid selected pivot')
    clauses=_source(cnf,counts); positions=defaultdict(list)
    for i,c in enumerate(clauses):
        for literal in c: positions[literal].append(i); counts['index_literals']+=1
    variables=sorted({abs(l) for l in positions},key=lambda v:(len(positions[v])*len(positions[-v]),v))
    counts['candidate_budget_skips']+=max(0,len(variables)-candidate_limit); rows=[]
    for v in variables[:candidate_limit]:
        if v==selected: counts['selected_pivot_skips']+=1; continue
        positive,negative=positions[v],positions[-v]; pairs=len(positive)*len(negative)
        if pairs>pair_limit: counts['pair_budget_skips']+=1; continue
        counts['candidate_projections']+=1
        target={tuple(sorted(c)) for c in clauses if v not in c and -v not in c}
        counts['candidate_source_literals']+=sum(map(len,clauses))
        for a in positive:
            for b in negative:
                counts['constructed_pairs']+=1; counts['pair_literal_visits']+=len(clauses[a])+len(clauses[b])
                r=(clauses[a]-{v}) | (clauses[b]-{-v})
                if not any(-l in r for l in r): target.add(tuple(sorted(r)))
        target=tuple(sorted(target))
        if len(target)>len(cnf)+clause_growth_limit: counts['growth_rejections']+=1; continue
        # A cheap, sufficient-family-oriented ranking, not distance to semantic
        # tractability. All scoring scans are charged, including losing choices.
        violations=[0]*5; excess=0; literals=0
        for c in target:
            pos=sum(l>0 for l in c); neg=len(c)-pos; literals+=len(c); excess+=max(0,len(c)-2)
            for j,bad in enumerate((pos>1,neg>1,len(c)>2,neg==0,pos==0)):violations[j]+=bad
        counts['ranking_literals']+=literals
        score=(min(violations),excess,literals,pairs,v)
        rows.append(dict(variable=v,target=target,score=score,pairs=pairs))
    counts['admitted_candidates']+=len(rows)
    return sorted(rows,key=lambda r:r['score'])


def selected_pivot(node):
    for field in ('additive_elimination','clause_elimination','elimination'):
        if node.get(field,{}).get('variable') is not None:return node[field]['variable']
    raise ValueError('Missing selected elimination pivot')


def open_ancestors(h,root,limit,counts):
    """First open elimination ancestors in breadth-first selected-plan order."""
    _limit(limit); todo=deque([root]);seen=set();result=[]
    while todo and len(result)<limit:
        key=todo.popleft()
        if key in seen:continue
        seen.add(key);n=h._load(key);counts['ancestor_nodes_visited']+=1
        if n is None:raise ValueError('Missing source plan')
        if n['summary']['closed']:continue
        if n['kind']=='eliminate':result.append(key)
        if n['kind']=='and':todo.extend(e['key'] for e in n['edges'])
        elif n['kind']=='or':todo.extend(e['key'] for e in n['alternatives'][n['selected']]['edges'])
        elif 'edge' in n:todo.append(n['edge']['key'])
    return result


def verify_trial(h,record,counts):
    if type(record) is not dict or set(record)!={'source','variable','edge','summary'}:
        raise ValueError('Invalid alternative trial fields')
    if type(record['source']) is not str or type(record['variable']) is not int:
        raise ValueError('Invalid alternative source or pivot')
    node=h._load(record['source'])
    if node is None or node['kind']!='eliminate' or node['summary']['closed']:
        raise ValueError('Alternative must bind an open elimination source')
    if selected_pivot(node)==record['variable']:raise ValueError('Repeated selected pivot')
    target=check_additive_elimination(node['cnf'],dict(variable=record['variable']),counts,
        pair_limit=h.config['elimination_pair_limit'],clause_growth_limit=h.config['clause_growth_limit'])
    if target is None:raise ValueError('Missing alternative projection')
    h._check_edge(record['edge'],target,node['depth'])
    child=h._load(record['edge']['key'])
    if encode(record['summary'])!=encode(child['summary']):raise ValueError('Incorrect alternative closure')
    counts['verified_trials']+=1
    return child['summary']['closed']


def covered(h,root,verified_successes,counts,memo=None):
    """Compose already-checked old edges and separately verified closed replacements.

    The success set is an internal checked input, never a serialized certificate.
    Every retained conditioning alternative can supply a complete two-child plan.
    """
    if memo is None:memo={}
    if root in memo:return memo[root]
    n=h._load(root)
    if n is None:raise ValueError('Missing coverage node')
    counts['composition_nodes']+=1
    if n['summary']['closed'] or root in verified_successes:answer=True
    elif n['kind']=='and':answer=all(covered(h,e['key'],verified_successes,counts,memo) for e in n['edges'])
    elif n['kind']=='or':answer=any(all(covered(h,e['key'],verified_successes,counts,memo) for e in a['edges']) for a in n['alternatives'])
    elif 'edge' in n:answer=covered(h,n['edge']['key'],verified_successes,counts,memo)
    else:answer=False
    memo[root]=answer;return answer


def search(h,root,counts,*,ancestor_limit=4,trial_limit=8):
    """At most trial_limit full recognitions, round-robin over at most A ancestors.

    Enumeration/ranking and the inherited recognition pipeline have separate
    charges; this cap is not a time, memory or complete-discovery bound.
    """
    _limit(ancestor_limit);_limit(trial_limit)
    if not trial_limit:return []
    sources=open_ancestors(h,root,ancestor_limit,counts); candidates=[]
    for key in sources:
        node=h._load(key)
        rows=alternatives(node['cnf'],selected_pivot(node),counts,
            pair_limit=h.config['elimination_pair_limit'],candidate_limit=h.config['elimination_candidate_limit'],
            clause_growth_limit=h.config['clause_growth_limit'])
        candidates.append((key,rows))
    records=[];successes=set()
    for rank in range(max((len(rows) for _,rows in candidates),default=0)):
        for key,rows in candidates:
            if rank>=len(rows) or key in successes:continue
            row=rows[rank];node=h._load(key)
            # Reconstruct independently before recognition; proposals are not
            # allowed to inject a cheaper or weaker target.
            target=check_additive_elimination(node['cnf'],dict(variable=row['variable']),counts,
                pair_limit=h.config['elimination_pair_limit'],clause_growth_limit=h.config['clause_growth_limit'])
            if target!=row['target']:raise ValueError('Incorrect proposed target')
            edge=h._edge(target,node['depth']);summary=h._load(edge['key'])['summary']
            record=dict(source=key,variable=row['variable'],edge=edge,summary=summary)
            if verify_trial(h,record,counts):successes.add(key)
            records.append(record);counts['recognition_trials']+=1
            if len(records)>=trial_limit or covered(h,root,successes,counts):return records
    return records
