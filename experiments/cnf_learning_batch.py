"""Fair continuation of retained learning bases under one shared state budget."""
from collections import Counter,deque
import time

from experiments.cnf_coupled_pivots import AdmissionExhausted
from experiments.cnf_learning_continuation import record_key
from experiments.cnf_route_composition import compose
from experiments.cnf_variable_elimination import _limit


def selection(h,routes,counts):
    blocks=routes.learned_blocks;rows=[]
    for identity,base in blocks.bases.items():
        node=h._load(base['source']);cnf=node['cnf'];rank=[len({abs(l) for c in cnf for l in c}),sum(map(len,cnf))]
        reason='ready';offset=None;remaining=None
        if base['probing']['status']!='clear':reason='successful_base'
        elif compose(h,[base['source']],routes,counts)[0][0]:reason='covered'
        else:
            _,_,ranked=blocks.context(h,identity,counts)
            saved=sorted((r for r in blocks.records.values() if r['base_sha256']==identity),key=lambda r:r['offset'])
            latest=saved[-1] if saved else None
            if latest is not None and latest['edge'] is not None:
                reason='pending' if h._load(latest['edge']['key']) is None else 'acquired_open_target'
                offset=latest['offset']
            else:
                offset=latest['offset']+len(latest['probing']['attempts'])//2 if latest else 4
                remaining=max(0,len(ranked)-offset)
                if not remaining:reason='exhausted'
        rows.append(dict(base_sha256=identity,source=base['source'],rank=rank,reason=reason,next_offset=offset,remaining=remaining))
    return sorted(rows,key=lambda row:(row['reason']!='pending',row['rank'],row['base_sha256']))


def acquire(h,target,depth,*,total_limit,target_limit):
    """Temporarily cap additional distinct admissions; never reset shared history."""
    for limit in (total_limit,target_limit):_limit(limit)
    before=set(h.admitted);h.admission_limit=min(total_limit,len(before)+target_limit)
    edge=None;pending=False
    try:edge=h._edge(target,depth)
    except AdmissionExhausted:pending=True
    finally:h.admission_limit=total_limit
    added=h.admitted-before
    if len(added)>target_limit or len(h.admitted)>total_limit:raise ValueError('Exceeded shared admission budget')
    return edge,pending,added


def search(h,routes,chosen,counts,on_record,*,step_limit=144,state_limit=128,target_limit=32):
    for limit in (step_limit,state_limit,target_limit):_limit(limit)
    h.set_admission_budget(state_limit);blocks=routes.learned_blocks
    todo=deque(row['base_sha256'] for row in chosen if row['reason'] in ('ready','pending'))
    visits=[];skipped=[];recognitions=[];discovery_seconds=recognition_seconds=0.0
    while todo and len(visits)<step_limit:
        identity=todo.popleft();base=blocks.bases[identity]
        if compose(h,[base['source']],routes,counts)[0][0]:skipped.append(identity);continue
        before=set(blocks.records);started=time.perf_counter();record,target=blocks.advance(h,identity,counts)
        discovery_seconds+=time.perf_counter()-started
        visit=dict(base_sha256=identity,offset=None if record is None else record['offset'],
                   status=None if record is None else record['probing']['status'],new=False)
        if record is None:visits.append(visit);continue
        visit['new']=record_key(record) not in before
        if visit['new']:on_record(record)
        visits.append(visit)
        if record['edge'] is None:todo.append(identity);continue
        started=time.perf_counter();edge,pending,added=acquire(h,target,h._load(base['source'])['depth'],
            total_limit=state_limit,target_limit=target_limit)
        recognition_seconds+=time.perf_counter()-started
        if not pending and edge!=record['edge']:raise ValueError('Incorrect acquired learned child')
        recognitions.append(dict(base_sha256=identity,offset=record['offset'],pending=pending,admitted=sorted(added)))
        routes.refresh_learning(h)
    routes.refresh_learning(h)
    return dict(visits=visits,skipped_covered=skipped,recognitions=recognitions,queued=list(todo),
        discovery_seconds=discovery_seconds,recognition_seconds=recognition_seconds)
