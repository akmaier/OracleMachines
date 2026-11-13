"""Budgeted cofactor acquisition with explicit pending branch obligations."""
from collections import Counter

from experiments.cnf_learning_batch import acquire
from experiments.cnf_trace_split import verify,attach
from experiments.cnf_route_composition import compose
from experiments.cnf_variable_elimination import _limit
from experiments.continue_cnf_learning import target_state


def leaves(h,routes):
    state=target_state(h,routes)
    unique={leaf['source']:leaf for row in state['remaining'] for leaf in row['leaves'] if not leaf['pending']}
    return sorted(unique.values(),key=lambda row:(row['variables'],sum(map(len,h._load(row['source'])['cnf'])),row['source']))


def acquire_pair(h,record,*,state_limit,pair_limit):
    for limit in (state_limit,pair_limit):_limit(limit)
    targets,_=verify(h,record,Counter());before=set(h.admitted);branches=[]
    for target,expected in zip(targets,record['edges'],strict=True):
        left=pair_limit-len(h.admitted-before)
        edge,pending,added=acquire(h,target,h._load(record['source'])['depth'],total_limit=state_limit,target_limit=left)
        if not pending and edge!=expected:raise ValueError('Incorrect acquired cofactor')
        branches.append(dict(pending=pending,admitted=sorted(added)))
    return dict(branches=branches,admitted=sorted(h.admitted-before))


def run(h,routes,records,*,state_limit=128,pair_limit=32):
    for limit in (state_limit,pair_limit):_limit(limit)
    h.set_admission_budget(state_limit);rows=[]
    for record in records:
        if compose(h,[record['source']],routes,Counter())[0][0]:
            rows.append(dict(source=record['source'],skipped_covered=True,branches=[],admitted=[]));continue
        result=acquire_pair(h,record,state_limit=state_limit,pair_limit=pair_limit)
        rows.append(dict(source=record['source'],skipped_covered=False,**result))
        routes.refresh(h);routes.refresh_learning(h);attach(h,routes,record,Counter())
    # A later cofactor may finish a child that was pending earlier.
    for record in records:attach(h,routes,record,Counter())
    return rows


def children(h,routes,records):
    """Retain both branch obligations, including selected old-plan frontiers."""
    from experiments.cnf_target_probe import remaining
    result=[]
    for record in records:
        row=dict(source=record['source'],closed=compose(h,[record['source']],routes,Counter())[0][0],children=[])
        for value,edge in zip((False,True),record['edges'],strict=True):
            item=dict(value=value,key=edge['key'],pending=h._load(edge['key']) is None)
            if not item['pending']:
                item['frontier']=remaining(h,[dict(source=record['source'],target=edge['key'])],routes,Counter())[0]
            row['children'].append(item)
        result.append(row)
    return result
