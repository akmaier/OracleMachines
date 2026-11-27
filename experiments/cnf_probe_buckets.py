"""Full-CNF failed-literal closure with reusable immutable occurrence indexes."""
from collections import Counter,deque
from experiments import cnf_iterated_forcing as prior
symbolic=prior.symbolic;conditioned=prior.conditioned;bucket=prior.bucket;native=prior.native
replay=prior.replay;restore=prior.restore
FORMAT='cnf-probe-buckets-v1'
DEFAULTS={**prior.DEFAULTS,'probe_limit':128,'probe_round_limit':8}
MODES=('binary','scan','indexed')


def options(values):
    if set(values)-set(DEFAULTS):raise ValueError('Unknown probe limit')
    result={**prior.options({k:v for k,v in values.items() if k not in ('probe_limit','probe_round_limit')}),**{k:values.get(k,DEFAULTS[k]) for k in ('probe_limit','probe_round_limit')}}
    if any(type(result[k]) is not int or not 1<=result[k]<=512 for k in ('probe_limit','probe_round_limit')):raise ValueError('Invalid probe limit')
    return result


def scan_probe(cnf,assumption,counts):
    fixed={abs(assumption):assumption>0};trace=[];changed=True
    while changed:
        changed=False
        for cid,clause in enumerate(cnf):
            counts['probe_scan_literals']+=len(clause)
            if any(abs(l) in fixed and fixed[abs(l)]==(l>0) for l in clause):continue
            pending=[l for l in clause if abs(l) not in fixed]
            if not pending:return dict(assumption=assumption,trace=trace,conflict=cid)
            if len(pending)==1:
                l=pending[0];fixed[abs(l)]=l>0;trace.append([l,cid]);changed=True
    return None


def prepare_index(cnf,counts):
    occ={};units=[];empty=None
    for cid,c in enumerate(cnf):
        for l in c:occ.setdefault(l,[]).append(cid);counts['probe_index_build_literals']+=1
        if len(c)==1:units.append((c[0],cid))
        if not c:empty=cid
    counts['probe_index_builds']+=1
    return {l:tuple(ids) for l,ids in occ.items()},tuple(units),empty


def indexed_probe(cnf,assumption,index,counts):
    occ,initial,empty=index;fixed={};trace=[];pending={};satisfied=set();queue=deque([(assumption,None),*initial])
    if empty is not None:return dict(assumption=assumption,trace=trace,conflict=empty)
    while queue:
        l,reason=queue.popleft()
        if reason in satisfied:continue
        if abs(l) in fixed:
            if fixed[abs(l)]!=(l>0):return dict(assumption=assumption,trace=trace,conflict=reason)
            continue
        fixed[abs(l)]=l>0
        if reason is not None:trace.append([l,reason])
        for cid in occ.get(l,()):satisfied.add(cid);counts['probe_index_occurrence_visits']+=1
        for cid in occ.get(-l,()):
            counts['probe_index_occurrence_visits']+=1
            if cid in satisfied:continue
            remaining=pending.get(cid,len(cnf[cid]))-1;pending[cid]=remaining
            if remaining==0:return dict(assumption=assumption,trace=trace,conflict=cid)
            if remaining==1:
                clause=cnf[cid];counts['probe_unit_reason_scans']+=len(clause)
                unassigned=[a for a in clause if abs(a) not in fixed]
                assert len(unassigned)==1
                queue.append((unassigned[0],cid))
    return None


def check_probe(cnf,proof,counts):
    if type(proof) is not dict or set(proof)!={'assumption','trace','conflict'}:raise ValueError('Invalid failed probe')
    assumption=proof['assumption'];variables={abs(l) for c in cnf for l in c}
    if type(assumption) is not int or abs(assumption) not in variables:raise ValueError('Invalid probe assumption')
    fixed={abs(assumption):assumption>0};trace=proof['trace'];conflict=proof['conflict']
    if type(trace) is not list or len(trace)>=len(variables):raise ValueError('Invalid probe trace')
    def clause(cid):
        if type(cid) is not int or not 0<=cid<len(cnf):raise ValueError('Invalid probe clause')
        counts['probe_checked_literals']+=len(cnf[cid]);return cnf[cid]
    for step in trace:
        if type(step) is not list or len(step)!=2:raise ValueError('Invalid probe step')
        l,cid=step;c=clause(cid)
        if type(l) is not int or not l or abs(l) in fixed or any(abs(a) in fixed and fixed[abs(a)]==(a>0) for a in c) or [a for a in c if abs(a) not in fixed]!=[l]:raise ValueError('Unsupported probe unit')
        fixed[abs(l)]=l>0
    c=clause(conflict)
    if not all(abs(l) in fixed and fixed[abs(l)]!=(l>0) for l in c):raise ValueError('Unsupported probe conflict')
    counts['probe_checked_failures']+=1
    return -assumption


def prepare_edge(raw,mode,limits,counts):
    steps,relation,after_steps,rounds,current,base_data,base_diag=prior.prepare_edge(raw,'closure',limits,counts)
    records=[];transports=[];diagnostics=[];spent=0;reason='disabled' if mode=='binary' else 'round-limit'
    for _ in range(0 if mode=='binary' else limits['probe_round_limit']):
        if current in ((),((),)):reason='constant';break
        if spent>=limits['probe_limit']:reason='probe-limit';break
        vs=sorted({abs(l) for c in current for l in c});starts=[l for v in vs for l in (v,-v)];failures=[]
        index=prepare_index(current,counts) if mode=='indexed' else None;attempted=0
        for assumption in starts:
            if spent>=limits['probe_limit']:break
            ev=indexed_probe(current,assumption,index,counts) if mode=='indexed' else scan_probe(current,assumption,counts)
            spent+=1;attempted+=1;counts['probe_attempts']+=1
            if ev is not None:check_probe(current,ev,counts);failures.append(ev)
        diag=dict(probes=attempted,failures=len(failures),truncated=attempted<len(starts));diagnostics.append(diag)
        if not failures:reason='probe-limit' if diag['truncated'] else 'no-failed-literal';break
        augmented=prior.prior.prior.clean_quotient(current+tuple((-ev['assumption'],) for ev in failures),counts)
        units,active,udiag=symbolic.preprocess(augmented,'units',limits,counts)
        closed,names=native.normalize(active,counts);fixed={abs(s['literal']):s['literal']>0 for s in units};progress=prior.variables(current)-prior.variables(closed)
        records.append(dict(failures=failures,units=units));transports.append((augmented,names,fixed));diag.update(units=udiag,variables_removed=progress)
        counts['probe_accepted_rounds']+=1;counts['probe_removed_variables']+=progress;current=closed
        if progress<=0:reason='no-variable-progress';break
    return steps,relation,after_steps,rounds,records,current,(base_data,transports),dict(binary=base_diag,probes=diagnostics,spent=spent,reason=reason)


def replay_edge(raw,steps,relation,after_steps,rounds,records,mode,limits,counts):
    current,base_data=prior.replay_edge(raw,steps,relation,after_steps,rounds,'closure',limits,counts)
    if type(records) is not list or len(records)>min(limits['probe_round_limit'],prior.variables(current)) or (mode=='binary' and records):raise ValueError('Invalid probe rounds')
    transports=[];total=0
    for i,r in enumerate(records):
        if type(r) is not dict or set(r)!={'failures','units'} or type(r['failures']) is not list or not r['failures']:raise ValueError('Invalid probe round')
        literals=[check_probe(current,ev,counts) for ev in r['failures']];total+=len(literals)
        if len(set(literals))!=len(literals) or total>limits['probe_limit']:raise ValueError('Duplicate or excessive failed probes')
        augmented=prior.prior.prior.clean_quotient(current+tuple((l,) for l in literals),counts)
        closed,names,fixed=replay(augmented,r['units'],limits,counts,fold=False)
        if i+1<len(records) and prior.variables(closed)>=prior.variables(current):raise ValueError('Nonprogressing probe round')
        transports.append((augmented,names,fixed));current=closed;counts['probe_checked_rounds']+=1
    return current,(base_data,transports)


def relation_restore(data,model):
    base_data,transports=data
    if model is None:return None
    for transport in reversed(transports):model=restore(*transport,model)
    return prior.relation_restore(base_data,model)


def discover(source,counts=None,*,mode='indexed',**values):
    if mode not in MODES:raise ValueError('Invalid closure mode')
    counts=Counter() if counts is None else counts;limits=options(values);cnf,names=native.normalize(source,counts)
    prefix,active,pdiag=symbolic.preprocess(cnf,'fold',limits,counts);residual,transport=native.normalize(active,counts)
    prefix_fixed={abs(s['literal']):s['literal']>0 for s in prefix if s['kind']=='unit'}
    nodes=[];edges=[];memo={};models={};edge_models={};attempts=[];edge_diagnostics=[]
    def visit(raw,depth):
        raw,_=native.normalize(raw,counts)
        steps,relation,after_steps,rounds,probe_rounds,closed,transport_data,diag=prepare_edge(raw,mode,limits,counts)
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
        edge=dict(cnf=list(map(list,raw)),depth=depth,units=steps,relation=relation,after_units=after_steps,rounds=rounds,probe_rounds=probe_rounds,residual=list(map(list,closed)),target=target)
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
    limits=options(proof['limits']);mode=proof['mode'];nodes=proof['nodes'];edges=proof['edges'];root=proof['root']
    maximum=(1<<(limits['depth_limit']+1))-1
    if type(nodes) is not list or not 1<=len(nodes)<=maximum or any(type(n) is not dict for n in nodes) or type(edges) is not list or not 1<=len(edges)<=maximum or type(root) is not int or root!=len(edges)-1:raise ValueError('Invalid closed graph')
    residual,transport,prefix_fixed=replay(cnf,proof['prefix'],limits,counts,fold=True)
    if proof['residual']!=list(map(list,residual)):raise ValueError('Changed prefix residual')
    edge_data=[]
    for edge in edges:
        if type(edge) is not dict or set(edge)!={'cnf','depth','units','relation','after_units','rounds','probe_rounds','residual','target'}:raise ValueError('Invalid transport edge')
        raw,_=native.normalize(edge['cnf'],counts);depth=edge['depth'];target=edge['target']
        if edge['cnf']!=list(map(list,raw)) or type(depth) is not int or not 0<=depth<=limits['depth_limit'] or type(target) is not int or not 0<=target<len(nodes):raise ValueError('Invalid transport identity')
        closed,transport_data=replay_edge(raw,edge['units'],edge['relation'],edge['after_units'],edge['rounds'],edge['probe_rounds'],mode,limits,counts)
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
