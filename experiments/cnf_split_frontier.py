"""Follow retained external splits instead of restarting their open parents.

This is a deterministic scheduling view of saved proof routes, not a minimum
backdoor or a coverage certificate. Existing composition remains authoritative.
Multiple saved splits are alternatives; choose their lexicographically first
identity and retain both branch obligations. Missing children remain explicit.
"""
from collections import Counter,defaultdict

from experiments.cnf_trace_split import verify,record_key
from experiments.cnf_route_composition import compose
from experiments.cnf_target_probe import remaining


def frontier(h,routes,records,counts):
    by_source=defaultdict(dict)
    for record in records:
        verify(h,record,counts);by_source[record['source']][record_key(record)]=record
    visited=set();active=set();leaves={};pending={};choices=[]

    def walk(key):
        if key in active:raise ValueError('Cyclic retained split frontier')
        if key in visited:return
        if h._load(key) is None:raise ValueError('Missing acquired frontier source')
        if compose(h,[key],routes,counts)[0][0]:
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
                row=remaining(h,[dict(source=key,target=key)],routes,counts)[0]
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
