"""Exact conditioning routes from retained clear source-assumption traces.

Both polarities are mandatory for structural coverage, even when one branch is
already SAT. References share saved unit reasons; children retain their own
canonical variable transports. No new assumption propagation is needed here.
"""
from collections import Counter

from experiments.cnf_trace_reuse import source_attempts,read_attempt,check_pair
from experiments.cnf_simplification import check_simplification
from experiments.cnf_residual_dag import restrict,holds
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import compose
from experiments.cnf_variable_elimination import _limit


def record_key(record):return encode([record['source'],record['references']])


def branches(h,source,references,counts):
    node=h._load(source)
    if node is None or node['kind']!='unresolved':raise ValueError('Expected unresolved split source')
    if type(references) is not list or len(references)!=2:raise ValueError('Both source polarities are required')
    attempts=[read_attempt(h,source,ref,counts) for ref in references]
    check_pair(node['cnf'],attempts,counts);targets=[];fixed=[]
    for attempt in attempts:
        assignment={attempt['variable']:attempt['value']}
        target,closure=check_simplification(restrict(node['cnf'],assignment,counts),attempt['certificate'],counts,pure=False)
        assignment.update(closure)
        if not {abs(l) for c in target for l in c} < {abs(l) for c in node['cnf'] for l in c}:
            raise ValueError('Split cofactor must strictly reduce support')
        targets.append(target);fixed.append(assignment)
    return node,targets,fixed


def make_record(h,source,references,counts):
    node,targets,_=branches(h,source,references,counts);edges=[]
    for target in targets:
        _,names,key=h._canonical(target,node['depth']);edges.append(dict(key=key,names=names))
    return dict(source=source,references=references,edges=edges)


def verify(h,record,counts):
    if type(record) is not dict or set(record)!={'source','references','edges'} or type(record['source']) is not str:
        raise ValueError('Invalid trace-split fields')
    if type(record['edges']) is not list or len(record['edges'])!=2:raise ValueError('Split must bind both children')
    node,targets,fixed=branches(h,record['source'],record['references'],counts)
    for target,edge in zip(targets,record['edges'],strict=True):
        _,names,key=h._canonical(target,node['depth'])
        if encode(edge)!=encode(dict(key=key,names=names)):raise ValueError('Incorrect split child binding')
    counts['verified_trace_splits']+=1
    return targets,fixed


def attach(h,routes,record,counts):
    verify(h,record,counts)
    if any(h._load(edge['key']) is None for edge in record['edges']):return False
    item=(dict(kind='trace_split',id=record_key(record)),[edge['key'] for edge in record['edges']])
    if item not in routes.by_source[record['source']]:routes.by_source[record['source']].append(item)
    return True


def candidates(h,source,routes,counts,*,candidate_limit=8):
    _limit(candidate_limit)
    if not candidate_limit:return []
    attempts,refs=source_attempts(h,source,counts);rows=[]
    for i in range(0,min(len(refs),2*candidate_limit),2):
        record=make_record(h,source,refs[i:i+2],counts);targets,_=verify(h,record,counts)
        unique={edge['key'] for edge in record['edges']};present={key for key in unique if h._load(key) is not None}
        closed={key for key in present if compose(h,[key],routes,counts)[0][0]}
        rank=[len(unique-closed),len(unique-present),max(len({abs(l) for c in target for l in c}) for target in targets),
              sum(sum(map(len,target)) for target in targets),attempts[i]['variable']]
        rows.append(dict(record=record,rank=rank,present=sorted(present),closed=sorted(closed)))
    counts['split_candidates_ranked']+=len(rows)
    return sorted(rows,key=lambda row:(row['rank'],record_key(row['record'])))


def lift(h,record,value,child_model):
    if type(value) is not bool:raise ValueError('Split branch value must be Boolean')
    _,fixed=verify(h,record,Counter());edge=record['edges'][int(value)];child=h._load(edge['key'])
    if (child is None or any(i not in child_model or type(child_model[i]) is not bool for i in range(1,len(edge['names'])+1))
            or not holds(child['cnf'],child_model)):
        raise ValueError('Invalid split child model')
    source=h._load(record['source'])['cnf'];result={abs(l):False for c in source for l in c}
    result.update((v,child_model[i]) for i,v in enumerate(edge['names'],1));result.update(fixed[int(value)])
    if not holds(source,result):raise ValueError('Split lift violates complete source')
    return result
