"""Exact bounded conditioning before semantic buckets, with residual DAG reuse.

Every leaf remains a fully checked bucket program, including unresolved leaves.
A split is UNSAT only with two UNSAT cofactors; SAT requires a lifted source
witness. The memo identity includes exact normalized CNF and remaining depth.
"""
from collections import Counter
from experiments import cnf_semantic_buckets as bucket
native=bucket.native
FORMAT='cnf-conditioned-buckets-v1'
DEFAULTS=dict(depth_limit=2,**bucket.DEFAULTS)


def options(values):
    if set(values)-set(DEFAULTS):raise ValueError('Unknown conditioned bucket limit')
    result={**DEFAULTS,**values}
    if any(type(v) is not int or v<(0 if k=='depth_limit' else 1) for k,v in result.items()) or result['depth_limit']>8 or result['bag_limit']>12:
        raise ValueError('Invalid conditioned bucket policy')
    return result


def cofactor(cnf,pivot,value,counts):
    return native.normalize(native.restrict_scan(cnf,{pivot:value},counts),counts)


def lift(cnf,pivot,value,child,counts):
    _,names=cofactor(cnf,pivot,value,counts)
    result={abs(l):False for c in cnf for l in c};result[pivot]=value
    result.update({name:child[i+1] for i,name in enumerate(names)})
    if not native.holds(cnf,result):raise ValueError('Invalid lifted cofactor witness')
    return result


def discover(source,counts=None,*,reuse=True,**values):
    counts=Counter() if counts is None else counts
    if type(reuse) is not bool:raise ValueError('Boolean reuse policy required')
    limits=options(values);cnf,_=native.normalize(source,counts);nodes=[];memo={};models={};attempts=[]
    args={k:v for k,v in limits.items() if k!='depth_limit'}
    def visit(raw,depth):
        source,_=native.normalize(raw,counts);key=(source,depth)
        counts['condition_lookup_calls']+=1;counts['condition_lookup_literals']+=sum(map(len,source))
        if reuse and key in memo:
            counts['condition_memo_hits']+=1;return memo[key]
        counts['condition_bucket_calls']+=1
        proof,diag=bucket.discover(source,counts,**args)
        node=dict(cnf=list(map(list,source)),depth=depth,bucket=proof,kind='leaf',status=proof['status']);model=None
        if proof['status']=='sat':model=dict(enumerate(proof['model'],1))
        if proof['status']=='unresolved' and depth:
            frequencies=Counter(abs(l) for c in source for l in c);counts['condition_pivot_literal_visits']+=sum(map(len,source))
            if frequencies:
                pivot=min(frequencies,key=lambda v:(-frequencies[v],v))
                low=visit(cofactor(source,pivot,False,counts)[0],depth-1)
                high=visit(cofactor(source,pivot,True,counts)[0],depth-1)
                status='unsat' if nodes[low]['status']==nodes[high]['status']=='unsat' else 'unresolved'
                for child,value in ((low,False),(high,True)):
                    if nodes[child]['status']=='sat':
                        status='sat';model=lift(source,pivot,value,models[child],counts);break
                node.update(kind='split',pivot=pivot,low=low,high=high,status=status);counts['condition_split_nodes']+=1
        index=len(nodes);nodes.append(node);models[index]=model;attempts.append(dict(node=index,diagnostic=diag))
        if reuse:memo[key]=index
        return index
    root=visit(cnf,limits['depth_limit']);model=models[root]
    result=dict(format=FORMAT,cnf=list(map(list,cnf)),limits=limits,reuse=reuse,nodes=nodes,root=root,status=nodes[root]['status'],model=None if model is None else [model[v] for v in sorted(model)])
    counts['condition_retained_nodes']+=len(nodes)
    check_certificate(source,result,counts)
    return result,dict(attempts=attempts,root_status=result['status'])


def check_certificate(source,proof,counts=None):
    counts=Counter() if counts is None else counts;cnf,names=native.normalize(source,counts)
    required={'format','cnf','limits','reuse','nodes','root','status','model'}
    if type(proof) is not dict or set(proof)!=required or proof['format']!=FORMAT or proof['cnf']!=list(map(list,cnf)) or type(proof['reuse']) is not bool:
        raise ValueError('Invalid conditioned source or format')
    if type(proof['limits']) is not dict or set(proof['limits'])!=set(DEFAULTS):raise ValueError('Invalid conditioned limits')
    limits=options(proof['limits']);nodes=proof['nodes'];root=proof['root'];known=set();models={}
    if type(nodes) is not list or not nodes or len(nodes)>(1<<(limits['depth_limit']+1))-1 or type(root) is not int or root!=len(nodes)-1:
        raise ValueError('Invalid conditioned graph')
    for i,node in enumerate(nodes):
        common={'cnf','depth','bucket','kind','status'}
        if type(node) is not dict or not common<=set(node):raise ValueError('Invalid conditioned node')
        local,_=native.normalize(node['cnf'],counts);depth=node['depth'];kind=node['kind']
        if node['cnf']!=list(map(list,local)) or type(depth) is not int or not 0<=depth<=limits['depth_limit']:
            raise ValueError('Invalid canonical residual or depth')
        if proof['reuse'] and (local,depth) in known:raise ValueError('Duplicate memoized residual')
        known.add((local,depth))
        if type(node['bucket']) is not dict or node['bucket'].get('limits')!={k:v for k,v in limits.items() if k!='depth_limit'} or node['bucket'].get('reduce') is not True:
            raise ValueError('Changed bucket leaf policy')
        result=bucket.check_certificate(local,node['bucket'],counts);status=node['bucket']['status'];model=result['model']
        if kind=='leaf' and set(node)==common:pass
        elif kind=='split' and set(node)==common|{'pivot','low','high'}:
            pivot=node['pivot']
            if status!='unresolved' or not depth or type(pivot) is not int or pivot not in {abs(l) for c in local for l in c}:
                raise ValueError('Invalid conditioning pivot')
            for side,value in (('low',False),('high',True)):
                child=node[side]
                if type(child) is not int or not 0<=child<i:raise ValueError('Cyclic or forward cofactor')
                expected,_=cofactor(local,pivot,value,counts)
                if nodes[child]['cnf']!=list(map(list,expected)) or nodes[child]['depth']!=depth-1:
                    raise ValueError('Wrong cofactor edge or depth')
            low=node['low'];high=node['high'];status='unsat' if nodes[low]['status']==nodes[high]['status']=='unsat' else 'unresolved';model=None
            for child,value in ((low,False),(high,True)):
                if nodes[child]['status']=='sat':
                    status='sat';model=lift(local,pivot,value,models[child],counts);break
        else:raise ValueError('Unknown conditioned rule')
        if node['status']!=status:raise ValueError('Wrong conditioned verdict')
        models[i]=model;counts['condition_checked_nodes']+=1
    reachable=set();todo=[root]
    while todo:
        i=todo.pop()
        if i in reachable:continue
        reachable.add(i)
        if nodes[i]['kind']=='split':todo.extend((nodes[i]['low'],nodes[i]['high']))
    if len(reachable)!=len(nodes) or nodes[root]['cnf']!=proof['cnf'] or nodes[root]['depth']!=limits['depth_limit'] or proof['status']!=nodes[root]['status']:
        raise ValueError('Invalid root or unreachable node')
    model=models[root];expected=None if model is None else [model[v] for v in sorted(model)]
    if proof['model']!=expected or (expected is not None and (type(proof['model']) is not list or any(type(v) is not bool for v in proof['model']))):
        raise ValueError('Changed root witness')
    if model is not None and not native.holds(cnf,model):raise ValueError('Invalid original witness')
    return dict(answer=None if proof['status']=='unresolved' else proof['status']=='sat',model=None if model is None else {name:model[i+1] for i,name in enumerate(names)})
