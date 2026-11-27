"""Checked binary conflicts and one signed equivalence block per incoming cofactor.

Edge-specific transport precedes shared quotient/depth bucket nodes.
"""
from collections import Counter
from experiments import cnf_symbolic_buckets as symbolic
from experiments import cnf_binary_equivalence as equivalence
conditioned=symbolic.conditioned;bucket=conditioned.bucket;native=symbolic.native
FORMAT='cnf-relation-buckets-v1'
DEFAULTS=symbolic.DEFAULTS
MODES=('units','conflict','relations')


def replay(cnf,steps,limits,counts,*,fold):
    if type(steps) is not list or len(steps)>limits['step_limit']:raise ValueError('Invalid closure steps')
    active=set(cnf);fixed={}
    for step in steps:
        if type(step) is not dict or 'kind' not in step:raise ValueError('Invalid closure rule')
        if step['kind']=='unit' and set(step)=={'kind','literal'}:
            l=step['literal']
            if type(l) is not int or not l or (l,) not in active or abs(l) in fixed:raise ValueError('Missing closure unit')
            fixed[abs(l)]=l>0;active=set(native.restrict_scan(active,{abs(l):l>0},counts));counts['closed_checked_units']+=1
        elif fold and step['kind']=='fold' and set(step)=={'kind','left','right'}:
            left=step['left'];right=step['right']
            if any(type(c) is not list or any(type(l) is not int for l in c) or c!=sorted(set(c)) for c in (left,right)):raise ValueError('Invalid closure fold')
            left=tuple(left);right=tuple(right)
            if left not in active or right not in active or left==right:raise ValueError('Missing closure fold parents')
            a=set(left)-set(right);b=set(right)-set(left)
            if len(a)!=1 or b!={-next(iter(a))}:raise ValueError('Unequal closure fold remainders')
            active.remove(left);active.remove(right);active.add(tuple(sorted(set(left)&set(right))));counts['closed_checked_folds']+=1
        else:raise ValueError('Unexpected closure transformation')
    residual,names=native.normalize(active,counts)
    return residual,names,fixed


def restore(cnf,names,fixed,model):
    result={abs(l):False for c in cnf for l in c};result.update(fixed)
    result.update({v:model[i+1] for i,v in enumerate(names)})
    if not native.holds(cnf,result):raise ValueError('Closure witness violates incoming source')
    return result


def check_binary_conflict(cnf,evidence,counts):
    binary=tuple(c for c in cnf if len(c)==2);variables={abs(l) for c in binary for l in c}
    if type(evidence) is not dict or set(evidence)!={'kind','variable','forward','backward'} or evidence['kind']!='implications':raise ValueError('Invalid binary conflict')
    v=evidence['variable']
    if type(v) is not int or v<=0 or v not in variables:raise ValueError('Invalid conflicting variable')
    for start,end,name in ((v,-v,'forward'),(-v,v,'backward')):
        path=evidence[name];current=start
        if type(path) is not list or not 1<=len(path)<=2*len(variables):raise ValueError('Invalid binary path')
        for step in path:
            if type(step) is not list or len(step)!=2:raise ValueError('Invalid binary path step')
            nxt,cid=step
            if type(nxt) is not int or not nxt or type(cid) is not int or not 0<=cid<len(binary) or binary[cid]!=tuple(sorted((-current,nxt))):raise ValueError('Unsupported conflict implication')
            current=nxt;counts['relation_checked_conflict_edges']+=1
        if current!=end:raise ValueError('Incomplete binary conflict path')


def clean_quotient(cnf,counts):
    # Substitution can create duplicate literals and tautologies. Preserve IDs
    # for witness transport, but restore clause normal form before unit indexing.
    result=set()
    for c in cnf:
        counts['relation_cleanup_literal_visits']+=len(c);items=set(c)
        if not any(-l in items for l in items):result.add(tuple(sorted(items)))
    return ((),) if () in result else tuple(sorted(result))


def relation_restore(data,model):
    before,unit_cnf,after,mapping,conflict=data
    if model is None:return None
    if conflict:raise ValueError('Binary conflict cannot lift a model')
    if after is not None:
        lifted={abs(l):False for c in unit_cnf for l in c};lifted.update(restore(*after,model))
        for variable,signed in mapping.items():lifted[variable]=lifted[abs(signed)] if signed>0 else not lifted[abs(signed)]
        if not native.holds(unit_cnf,lifted):raise ValueError('Invalid equivalence witness')
        model=lifted
    return restore(*before,model)


def prepare_edge(raw,mode,limits,counts):
    steps,active,diag=symbolic.preprocess(raw,'units',limits,counts)
    unit_cnf,names=native.normalize(active,counts);fixed={abs(s['literal']):s['literal']>0 for s in steps}
    relation=None;after_steps=[];closed=unit_cnf;after=None;mapping={};conflict=False;after_diag=None
    if mode!='units' and unit_cnf not in ((),((),)):
        binary=tuple(c for c in unit_cnf if len(c)==2);counts['relation_binary_clause_scans']+=len(unit_cnf)
        if binary:
            counts['relation_binary_calls']+=1;_,evidence=native.two_cnf(binary,counts)
            if evidence is not None:
                check_binary_conflict(unit_cnf,evidence,counts);relation=dict(kind='conflict',evidence=evidence);closed=((),);conflict=True;counts['relation_conflicts']+=1
            elif mode=='relations':
                evidence=equivalence.discover(unit_cnf,counts)
                if evidence is not None:
                    target,mapping=equivalence.check_substitution(unit_cnf,evidence,counts);target=clean_quotient(target,counts)
                    relation=dict(kind='equivalence',evidence=evidence);counts['relation_substitutions']+=1
                    after_steps,active,after_diag=symbolic.preprocess(target,'units',limits,counts)
                    closed,after_names=native.normalize(active,counts);after_fixed={abs(s['literal']):s['literal']>0 for s in after_steps}
                    after=(target,after_names,after_fixed)
    return steps,relation,after_steps,closed,((raw,names,fixed),unit_cnf,after,mapping,conflict),dict(units=diag,after_units=after_diag)


def replay_edge(raw,steps,relation,after_steps,mode,limits,counts):
    unit_cnf,names,fixed=replay(raw,steps,limits,counts,fold=False)
    closed=unit_cnf;after=None;mapping={};conflict=False
    if type(after_steps) is not list:raise ValueError('Invalid post-substitution units')
    if relation is None:
        if after_steps:raise ValueError('Unexpected second unit trace')
    else:
        if mode=='units' or type(relation) is not dict or set(relation)!={'kind','evidence'}:raise ValueError('Invalid relation rule')
        if relation['kind']=='conflict':
            if after_steps:raise ValueError('Units after a binary conflict')
            check_binary_conflict(unit_cnf,relation['evidence'],counts);closed=((),);conflict=True
        elif relation['kind']=='equivalence' and mode=='relations':
            target,mapping=equivalence.check_substitution(unit_cnf,relation['evidence'],counts);target=clean_quotient(target,counts)
            closed,after_names,after_fixed=replay(target,after_steps,limits,counts,fold=False);after=(target,after_names,after_fixed)
        else:raise ValueError('Unexpected binary relation')
    return closed,((raw,names,fixed),unit_cnf,after,mapping,conflict)


def discover(source,counts=None,*,mode='relations',**values):
    if mode not in MODES:raise ValueError('Invalid closure mode')
    counts=Counter() if counts is None else counts;limits=symbolic.options(values);cnf,names=native.normalize(source,counts)
    prefix,active,pdiag=symbolic.preprocess(cnf,'fold',limits,counts);residual,transport=native.normalize(active,counts)
    prefix_fixed={abs(s['literal']):s['literal']>0 for s in prefix if s['kind']=='unit'}
    nodes=[];edges=[];memo={};models={};edge_models={};attempts=[];edge_diagnostics=[]
    def visit(raw,depth):
        raw,_=native.normalize(raw,counts)
        steps,relation,after_steps,closed,transport_data,diag=prepare_edge(raw,mode,limits,counts)
        key=closed,depth;counts['closed_lookup_calls']+=1;counts['closed_lookup_literals']+=sum(map(len,closed))
        if key in memo:
            target=memo[key];counts['closed_memo_hits']+=1
        else:
            counts['closed_bucket_calls']+=1
            proof,bdiag=bucket.discover(closed,counts,**{k:limits[k] for k in bucket.DEFAULTS})
            node=dict(cnf=list(map(list,closed)),depth=depth,bucket=proof,kind='leaf',status=proof['status'])
            model=dict(enumerate(proof['model'],1)) if proof['status']=='sat' else None
            if proof['status']=='unresolved' and depth:
                frequencies=Counter(abs(l) for c in closed for l in c);counts['closed_pivot_literals']+=sum(map(len,closed))
                pivot=min(frequencies,key=lambda v:(-frequencies[v],v))
                low=visit(conditioned.cofactor(closed,pivot,False,counts)[0],depth-1)
                high=visit(conditioned.cofactor(closed,pivot,True,counts)[0],depth-1)
                low_status=nodes[edges[low]['target']]['status'];high_status=nodes[edges[high]['target']]['status']
                status='unsat' if low_status==high_status=='unsat' else 'unresolved'
                for e,value in ((low,False),(high,True)):
                    if nodes[edges[e]['target']]['status']=='sat':
                        status='sat';model=conditioned.lift(closed,pivot,value,edge_models[e],counts);break
                node.update(kind='split',pivot=pivot,low=low,high=high,status=status);counts['closed_split_nodes']+=1
            target=len(nodes);nodes.append(node);models[target]=model;attempts.append(dict(node=target,diagnostic=bdiag))
            memo[key]=target
        edge=dict(cnf=list(map(list,raw)),depth=depth,units=steps,relation=relation,after_units=after_steps,residual=list(map(list,closed)),target=target)
        e=len(edges);edges.append(edge);edge_models[e]=relation_restore(transport_data,models[target]);edge_diagnostics.append(dict(edge=e,diagnostic=diag))
        counts['closed_transport_edges']+=1
        return e
    root=visit(residual,limits['depth_limit']);status=nodes[edges[root]['target']]['status'];model=None
    if status=='sat':
        lifted=restore(cnf,transport,prefix_fixed,edge_models[root]);model=[lifted[v] for v in range(1,len(names)+1)]
    proof=dict(format=FORMAT,cnf=list(map(list,cnf)),limits=limits,mode=mode,prefix=prefix,residual=list(map(list,residual)),nodes=nodes,edges=edges,root=root,status=status,model=model)
    counts['closed_retained_nodes']+=len(nodes);check_certificate(source,proof,counts)
    return proof,dict(preprocessing=pdiag,attempts=attempts,edges=edge_diagnostics)


def check_certificate(source,proof,counts=None):
    counts=Counter() if counts is None else counts;cnf,names=native.normalize(source,counts)
    fields={'format','cnf','limits','mode','prefix','residual','nodes','edges','root','status','model'}
    if type(proof) is not dict or set(proof)!=fields or proof['format']!=FORMAT or proof['cnf']!=list(map(list,cnf)) or proof['mode'] not in MODES:raise ValueError('Invalid closed source or format')
    if type(proof['limits']) is not dict or set(proof['limits'])!=set(DEFAULTS):raise ValueError('Invalid closed policy')
    limits=symbolic.options(proof['limits']);mode=proof['mode'];nodes=proof['nodes'];edges=proof['edges'];root=proof['root']
    maximum=(1<<(limits['depth_limit']+1))-1
    if type(nodes) is not list or not 1<=len(nodes)<=maximum or any(type(n) is not dict for n in nodes) or type(edges) is not list or not 1<=len(edges)<=maximum or type(root) is not int or root!=len(edges)-1:raise ValueError('Invalid closed graph')
    residual,transport,prefix_fixed=replay(cnf,proof['prefix'],limits,counts,fold=True)
    if proof['residual']!=list(map(list,residual)):raise ValueError('Changed prefix residual')
    edge_data=[]
    for edge in edges:
        if type(edge) is not dict or set(edge)!={'cnf','depth','units','relation','after_units','residual','target'}:raise ValueError('Invalid transport edge')
        raw,_=native.normalize(edge['cnf'],counts);depth=edge['depth'];target=edge['target']
        if edge['cnf']!=list(map(list,raw)) or type(depth) is not int or not 0<=depth<=limits['depth_limit'] or type(target) is not int or not 0<=target<len(nodes):raise ValueError('Invalid transport identity')
        closed,transport_data=replay_edge(raw,edge['units'],edge['relation'],edge['after_units'],mode,limits,counts)
        if edge['residual']!=list(map(list,closed)) or nodes[target].get('cnf')!=edge['residual'] or nodes[target].get('depth')!=depth:raise ValueError('Wrong closed target')
        edge_data.append(transport_data);counts['closed_checked_edges']+=1
    models={};known=set()
    def edge_model(e):
        model=models[edges[e]['target']]
        return relation_restore(edge_data[e],model)
    for i,node in enumerate(nodes):
        common={'cnf','depth','bucket','kind','status'}
        if not common<=set(node):raise ValueError('Invalid closed node')
        local,_=native.normalize(node['cnf'],counts);depth=node['depth'];kind=node['kind']
        if node['cnf']!=list(map(list,local)) or type(depth) is not int or not 0<=depth<=limits['depth_limit']:raise ValueError('Invalid closed node identity')
        if (local,depth) in known:raise ValueError('Duplicate shared closed residual')
        known.add((local,depth))
        if type(node['bucket']) is not dict or node['bucket'].get('limits')!={k:limits[k] for k in bucket.DEFAULTS} or node['bucket'].get('reduce') is not True:raise ValueError('Changed closed bucket policy')
        result=bucket.check_certificate(local,node['bucket'],counts);status=node['bucket']['status'];model=result['model']
        if kind=='leaf' and set(node)==common:pass
        elif kind=='split' and set(node)==common|{'pivot','low','high'}:
            pivot=node['pivot']
            if status!='unresolved' or not depth or type(pivot) is not int or pivot not in {abs(l) for c in local for l in c}:raise ValueError('Invalid closed split')
            for side,value in (('low',False),('high',True)):
                e=node[side]
                if type(e) is not int or not 0<=e<len(edges) or edges[e]['target']>=i:raise ValueError('Cyclic or forward closed edge')
                expected,_=conditioned.cofactor(local,pivot,value,counts)
                if edges[e]['cnf']!=list(map(list,expected)) or edges[e]['depth']!=depth-1:raise ValueError('Wrong incoming cofactor')
            low=node['low'];high=node['high'];status='unsat' if nodes[edges[low]['target']]['status']==nodes[edges[high]['target']]['status']=='unsat' else 'unresolved';model=None
            for e,value in ((low,False),(high,True)):
                if nodes[edges[e]['target']]['status']=='sat':
                    status='sat';model=conditioned.lift(local,pivot,value,edge_model(e),counts);break
        else:raise ValueError('Unknown closed rule')
        if node['status']!=status:raise ValueError('Wrong closed verdict')
        models[i]=model;counts['closed_checked_nodes']+=1
    reachable_edges=set();reachable_nodes=set();todo=[root]
    while todo:
        e=todo.pop();reachable_edges.add(e);target=edges[e]['target']
        if target in reachable_nodes:continue
        reachable_nodes.add(target)
        if nodes[target]['kind']=='split':todo.extend((nodes[target]['low'],nodes[target]['high']))
    target=edges[root]['target']
    if len(reachable_edges)!=len(edges) or len(reachable_nodes)!=len(nodes) or edges[root]['cnf']!=proof['residual'] or edges[root]['depth']!=limits['depth_limit'] or target!=len(nodes)-1 or proof['status']!=nodes[target]['status']:raise ValueError('Changed closed root or unreachable evidence')
    # Check every SAT edge transport, including a branch not used by the root witness.
    for e in range(len(edges)):edge_model(e)
    model=edge_model(root)
    if model is None:
        if proof['model'] is not None:raise ValueError('Unexpected closed root witness')
    else:
        model=restore(cnf,transport,prefix_fixed,model);expected=[model[v] for v in range(1,len(names)+1)]
        if type(proof['model']) is not list or any(type(v) is not bool for v in proof['model']) or proof['model']!=expected:raise ValueError('Invalid closed root witness')
    return dict(answer=None if proof['status']=='unresolved' else proof['status']=='sat',model=None if model is None else {name:model[i+1] for i,name in enumerate(names)})
