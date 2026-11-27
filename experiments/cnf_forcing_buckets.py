"""One-way binary forcing with optional sharing of clause-supported path edges."""
from collections import Counter
from experiments import cnf_relation_buckets as prior
symbolic=prior.symbolic;conditioned=prior.conditioned;bucket=prior.bucket;native=prior.native
replay=prior.replay;restore=prior.restore
FORMAT='cnf-forcing-buckets-v1'
DEFAULTS=prior.DEFAULTS
MODES=('relations','paths','shared')


def pack_paths(paths,mode):
    if not paths:return None
    if mode=='paths':return dict(kind=mode,paths=paths)
    edges=[];intern={};result=[]
    for item in paths:
        current=-item['literal'];ids=[]
        for nxt,cid in item['path']:
            edge=current,nxt,cid
            if edge not in intern:intern[edge]=len(edges);edges.append(list(edge))
            ids.append(intern[edge]);current=nxt
        result.append(dict(literal=item['literal'],path=ids))
    return dict(kind=mode,edges=edges,paths=result)


def discover_forcing(cnf,mode,limits,counts):
    if mode=='relations' or cnf in ((),((),)):return None,dict(reason='disabled-or-constant',spent=0,searches=0)
    binary=tuple(c for c in cnf if len(c)==2);counts['forcing_clause_scans']+=len(cnf);graph={}
    for cid,(a,b) in enumerate(binary):
        for u,v in ((-a,b),(-b,a)):graph.setdefault(u,[]).append((v,cid));counts['forcing_graph_build_edges']+=1
    starts=sorted({l for c in binary for l in c}|{-l for c in binary for l in c});spent=0;paths=[];searches=0;reason='complete'
    for start in starts:
        if spent>=limits['work_limit']:reason='work-limit';break
        parents={start:None};todo=[start];at=0;stopped=False;searches+=1;counts['forcing_searches']+=1
        while at<len(todo) and -start not in parents and not stopped:
            u=todo[at];at+=1
            for v,cid in graph.get(u,()):
                if spent>=limits['work_limit']:stopped=True;reason='work-limit';break
                spent+=1;counts['forcing_graph_edge_visits']+=1
                if v not in parents:parents[v]=(u,cid);todo.append(v)
        if -start in parents:
            path=[];current=-start
            while current!=start:
                previous,cid=parents[current];path.append([current,cid]);current=previous
            path.reverse();paths.append(dict(literal=-start,path=path));counts['forcing_discovered_literals']+=1;counts['forcing_discovered_path_edges']+=len(path)
        if stopped:break
    return pack_paths(paths,mode),dict(reason=reason,spent=spent,searches=searches)


def check_forcing(cnf,evidence,mode,limits,counts):
    if evidence is None:return ()
    if mode not in ('paths','shared') or type(evidence) is not dict or evidence.get('kind')!=mode or set(evidence)!=({'kind','paths'} if mode=='paths' else {'kind','paths','edges'}):raise ValueError('Invalid forcing format')
    binary=tuple(c for c in cnf if len(c)==2);variables={abs(l) for c in binary for l in c};paths=evidence['paths'];pool=evidence.get('edges',[])
    def support(edge):
        if type(edge) is not list or len(edge)!=3:raise ValueError('Invalid forcing edge')
        u,v,cid=edge
        if type(u) is not int or not u or type(v) is not int or not v or type(cid) is not int or not 0<=cid<len(binary) or binary[cid]!=tuple(sorted((-u,v))):raise ValueError('Unsupported forcing edge')
        counts['forcing_checked_support_edges']+=1
    if type(paths) is not list or not 1<=len(paths)<=2*len(variables):raise ValueError('Invalid forcing paths')
    if mode=='shared':
        if type(pool) is not list or not 1<=len(pool)<=limits['work_limit']:raise ValueError('Invalid forcing edge pool')
        unique=set()
        for edge in pool:
            support(edge)
            if tuple(edge) in unique:raise ValueError('Duplicate forcing pool edge')
            unique.add(tuple(edge))
    forced=set();used=set();total=0
    for item in paths:
        if type(item) is not dict or set(item)!={'literal','path'}:raise ValueError('Invalid forcing path record')
        l=item['literal'];path=item['path']
        if type(l) is not int or not l or abs(l) not in variables or l in forced or type(path) is not list or not 1<=len(path)<=2*len(variables):raise ValueError('Invalid forced literal/path')
        current=-l;total+=len(path)
        if total>limits['work_limit']:raise ValueError('Oversized forcing evidence')
        for step in path:
            if mode=='paths':
                if type(step) is not list or len(step)!=2:raise ValueError('Invalid forcing path step')
                nxt,cid=step;support([current,nxt,cid])
            else:
                if type(step) is not int or not 0<=step<len(pool):raise ValueError('Invalid forcing edge reference')
                u,nxt,_=pool[step]
                if u!=current:raise ValueError('Disconnected forcing path')
                used.add(step)
            current=nxt;counts['forcing_path_walk_edges']+=1
        if current!=l:raise ValueError('Wrong forcing endpoint')
        forced.add(l)
    if mode=='shared' and used!=set(range(len(pool))):raise ValueError('Unused forcing pool edges')
    counts['forcing_checked_literals']+=len(forced)
    return tuple(sorted(forced))


def prepare_edge(raw,mode,limits,counts):
    steps,relation,after_steps,base_cnf,base_data,base_diag=prior.prepare_edge(raw,'relations',limits,counts)
    forcing,fdiag=discover_forcing(base_cnf,mode,limits,counts);literals=check_forcing(base_cnf,forcing,mode,limits,counts)
    closed=base_cnf;force_steps=[];after=None;udiag=None
    if literals:
        augmented=prior.clean_quotient(base_cnf+tuple((l,) for l in literals),counts)
        force_steps,active,udiag=symbolic.preprocess(augmented,'units',limits,counts)
        closed,names=native.normalize(active,counts);fixed={abs(s['literal']):s['literal']>0 for s in force_steps};after=(augmented,names,fixed)
    return steps,relation,after_steps,forcing,force_steps,closed,(base_data,after),dict(relation=base_diag,forcing=fdiag,forced_units=udiag)


def replay_edge(raw,steps,relation,after_steps,forcing,force_steps,mode,limits,counts):
    base_cnf,base_data=prior.replay_edge(raw,steps,relation,after_steps,'relations',limits,counts)
    literals=check_forcing(base_cnf,forcing,mode,limits,counts);closed=base_cnf;after=None
    if type(force_steps) is not list:raise ValueError('Invalid forced-unit steps')
    if literals:
        augmented=prior.clean_quotient(base_cnf+tuple((l,) for l in literals),counts)
        closed,names,fixed=replay(augmented,force_steps,limits,counts,fold=False);after=(augmented,names,fixed)
    elif force_steps:raise ValueError('Unexpected forced-unit steps')
    return closed,(base_data,after)


def relation_restore(data,model):
    base_data,after=data
    if model is None:return None
    if after is not None:model=restore(*after,model)
    return prior.relation_restore(base_data,model)


def discover(source,counts=None,*,mode='shared',**values):
    if mode not in MODES:raise ValueError('Invalid closure mode')
    counts=Counter() if counts is None else counts;limits=symbolic.options(values);cnf,names=native.normalize(source,counts)
    prefix,active,pdiag=symbolic.preprocess(cnf,'fold',limits,counts);residual,transport=native.normalize(active,counts)
    prefix_fixed={abs(s['literal']):s['literal']>0 for s in prefix if s['kind']=='unit'}
    nodes=[];edges=[];memo={};models={};edge_models={};attempts=[];edge_diagnostics=[]
    def visit(raw,depth):
        raw,_=native.normalize(raw,counts)
        steps,relation,after_steps,forcing,force_steps,closed,transport_data,diag=prepare_edge(raw,mode,limits,counts)
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
        edge=dict(cnf=list(map(list,raw)),depth=depth,units=steps,relation=relation,after_units=after_steps,forcing=forcing,forced_units=force_steps,residual=list(map(list,closed)),target=target)
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
        if type(edge) is not dict or set(edge)!={'cnf','depth','units','relation','after_units','forcing','forced_units','residual','target'}:raise ValueError('Invalid transport edge')
        raw,_=native.normalize(edge['cnf'],counts);depth=edge['depth'];target=edge['target']
        if edge['cnf']!=list(map(list,raw)) or type(depth) is not int or not 0<=depth<=limits['depth_limit'] or type(target) is not int or not 0<=target<len(nodes):raise ValueError('Invalid transport identity')
        closed,transport_data=replay_edge(raw,edge['units'],edge['relation'],edge['after_units'],edge['forcing'],edge['forced_units'],mode,limits,counts)
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
