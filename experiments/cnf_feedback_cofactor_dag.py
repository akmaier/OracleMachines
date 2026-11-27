"""Bounded exact conditioning with shared, normalized feedback subproblems.

The same residual and remaining depth share one result within a discovery call.
Open/budget-limited results are never SAT authority. Internal open histories are
kept in the separate search log, not in the refutation certificate.
"""
from collections import Counter
from copy import deepcopy
from experiments import cnf_source_feedback_native as compiler
native=compiler.native;feedback=compiler.feedback
FORMAT='cnf-feedback-cofactor-dag-v1'
DEFAULTS=dict(depth_limit=2,state_limit=64,feedback_round_limit=2,pivot_limit=16,probe_limit=512,work_limit=2097152,trace_limit=256)


def options(**values):
    if set(values)-set(DEFAULTS):raise ValueError('Unknown cofactor limit')
    result={**DEFAULTS,**values}
    for key,value in result.items():
        if type(value) is not int or value<(0 if key=='depth_limit' else 1):raise ValueError('Invalid cofactor bound')
    return result


def discover(source,counts,*,reuse=True,**limits):
    if type(reuse) is not bool:raise ValueError('Boolean cofactor reuse required')
    limits=options(**limits);source,_=native.normalize(source,counts);nodes=[];memo={};attempts=[];spent=0
    args={key:value for key,value in limits.items() if key not in ('depth_limit','state_limit','feedback_round_limit')}
    args['round_limit']=limits['feedback_round_limit']
    def visit(raw,depth):
        nonlocal spent
        cnf,_=native.normalize(raw,counts);key=cnf,depth
        counts['cofactor_lookup_literals']+=sum(map(len,cnf));counts['cofactor_lookup_calls']+=1
        if reuse and key in memo:
            counts['cofactor_memo_hits']+=1;return memo[key]
        node=dict(cnf=list(map(list,cnf)),depth=depth,status='unresolved')
        attempt=None
        if spent>=limits['state_limit']:
            node['kind']='limit';counts['cofactor_budget_leaves']+=1
        else:
            spent+=1;counts['cofactor_feedback_calls']+=1
            chain,searches=feedback.discover(cnf,counts,**args)
            attempt=dict(cnf=list(map(list,cnf)),depth=depth,chain=chain,searches=searches)
            attempts.append(attempt)
            fixed,_,conflict=native.propagate(cnf,counts)
            frequencies=Counter(abs(l) for cl in cnf for l in cl if abs(l) not in fixed)
            if chain['status']=='refuted' or depth==0 or not frequencies:
                node.update(kind='feedback',chain=chain,status=chain['status'])
            else:
                pivot=min(frequencies,key=lambda v:(-frequencies[v],v))
                low=visit(native.restrict_scan(cnf,{pivot:False},counts),depth-1)
                high=visit(native.restrict_scan(cnf,{pivot:True},counts),depth-1)
                node.update(kind='split',pivot=pivot,low=low,high=high,
                    status='refuted' if nodes[low]['status']==nodes[high]['status']=='refuted' else 'unresolved')
                counts['cofactor_split_nodes']+=1
        index=len(nodes);nodes.append(node)
        if reuse:memo[key]=index
        if attempt is not None:attempt['node']=index
        return index
    root=visit(source,limits['depth_limit'])
    counts['cofactor_retained_nodes']+=len(nodes)
    return dict(format=FORMAT,source=list(map(list,source)),limits=limits,reuse=reuse,nodes=nodes,root=root,status=nodes[root]['status']),attempts


def validate(source,result,counts):
    result=deepcopy(result);source,_=native.normalize(source,counts)
    if type(result) is not dict or set(result)!={'format','source','limits','reuse','nodes','root','status'} or result['format']!=FORMAT:
        raise ValueError('Invalid cofactor certificate')
    if result['source']!=list(map(list,source)) or type(result['reuse']) is not bool or type(result['limits']) is not dict or set(result['limits'])!=set(DEFAULTS):
        raise ValueError('Changed cofactor source or policy')
    limits=options(**result['limits']);nodes=result['nodes'];root=result['root']
    if type(nodes) is not list or not nodes or type(root) is not int or root!=len(nodes)-1:raise ValueError('Invalid cofactor root')
    known=set();computed=0
    for i,node in enumerate(nodes):
        if type(node) is not dict or not {'kind','cnf','depth','status'}<=set(node):raise ValueError('Invalid cofactor node')
        cnf,_=native.normalize(node['cnf'],counts);depth=node['depth'];kind=node['kind']
        if node['cnf']!=list(map(list,cnf)) or type(depth) is not int or not 0<=depth<=limits['depth_limit']:
            raise ValueError('Invalid canonical cofactor or depth')
        identity=cnf,depth
        if result['reuse'] and identity in known:raise ValueError('Duplicate memoized cofactor')
        known.add(identity);computed+=kind!='limit'
        common={'kind','cnf','depth','status'}
        if kind=='limit' and set(node)==common:status='unresolved'
        elif kind=='feedback' and set(node)==common|{'chain'}:
            feedback.validate(cnf,node['chain'],counts);status=node['chain']['status']
        elif kind=='split' and set(node)==common|{'pivot','low','high'}:
            pivot=node['pivot']
            if depth==0 or type(pivot) is not int or pivot not in {abs(l) for cl in cnf for l in cl}:raise ValueError('Invalid partition pivot')
            for side,bit in (('low',False),('high',True)):
                child=node[side]
                if type(child) is not int or not 0<=child<i:raise ValueError('Cyclic or forward cofactor edge')
                expected,_=native.normalize(native.restrict_scan(cnf,{pivot:bit},counts),counts)
                if nodes[child]['cnf']!=list(map(list,expected)) or nodes[child]['depth']!=depth-1:raise ValueError('Wrong partition child')
            status='refuted' if nodes[node['low']]['status']==nodes[node['high']]['status']=='refuted' else 'unresolved'
        else:raise ValueError('Unknown cofactor rule')
        if node['status']!=status:raise ValueError('Wrong cofactor status')
        counts['cofactor_checked_nodes']+=1
    if computed>limits['state_limit']:raise ValueError('Exceeded cofactor state limit')
    if nodes[root]['cnf']!=result['source'] or nodes[root]['depth']!=limits['depth_limit'] or result['status']!=nodes[root]['status']:
        raise ValueError('Changed cofactor root binding')
    reachable=set();todo=[root]
    while todo:
        i=todo.pop()
        if i in reachable:continue
        reachable.add(i)
        if nodes[i]['kind']=='split':todo.extend((nodes[i]['low'],nodes[i]['high']))
    if len(reachable)!=len(nodes):raise ValueError('Unreachable cofactor state')
    return source,result


def compile_program(solver,source,result,counts,*,unit_work_limit=262144,unit_trace_limit=256):
    compiler.checked_options('all',unit_work_limit,unit_trace_limit)
    source,result=validate(source,result,counts)
    if result['status']!='refuted':raise ValueError('Both partition sides must be refuted')
    root=native.token(source,counts);nodes=result['nodes'];remaining=unit_work_limit
    # All incoming provenance was checked before any persistent root reuse.
    def emit(index):
        nonlocal remaining
        node=nodes[index];cnf=tuple(map(tuple,node['cnf']));key=native.token(cnf,counts)
        old=solver._read(key,cnf,purpose='cofactor_native')
        if old is not None:
            if old['answer'] is not False:raise ValueError('Contradictory cofactor cache')
            counts['cofactor_native_hits']+=1;return key
        if node['kind']=='feedback':
            local=Counter();key=compiler.compile_program(solver,cnf,node['chain'],local,
                shortcut='all' if remaining else 'off',unit_work_limit=max(1,remaining),unit_trace_limit=unit_trace_limit)
            spent=sum(local[x] for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))
            if spent>remaining:raise ValueError('Exceeded shared cofactor shortcut allowance')
            remaining-=spent;counts.update(local);counts['cofactor_native_leaf_compilations']+=1
        else:
            low=emit(node['low']);high=emit(node['high'])
            solver._store(key,dict(format=native.FORMAT,cnf=node['cnf'],answer=False,
                proof=dict(kind='split',variable=node['pivot'],low=low,high=high)))
            counts['cofactor_native_splits']+=1
        return key
    actual=emit(result['root'])
    if actual!=root:raise ValueError('Changed native partition root')
    return root
