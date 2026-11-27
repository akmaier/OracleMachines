"""Continue capped failed-literal acquisition only after an unresolved bucket.

Ephemeral exact-source cursors reuse a clear probe prefix and occurrence index.
They never certify a SAT answer or exhaustion and are absent from cold authority.
"""
from collections import Counter
from dataclasses import dataclass
from experiments import cnf_probe_relations as prior
probes=prior.prior;binary=probes.prior;relations=prior.relations
symbolic=prior.symbolic;conditioned=prior.conditioned;bucket=prior.bucket;native=prior.native
replay=prior.replay;restore=prior.restore
FORMAT='cnf-selective-probes-v1'
DEFAULTS={**prior.DEFAULTS,'continuation_limit':128}
MODES=('base','eager','restart','resume')


def options(values):
    if set(values)-set(DEFAULTS):raise ValueError('Unknown continuation limit')
    result={**prior.options({k:v for k,v in values.items() if k!='continuation_limit'}),'continuation_limit':values.get('continuation_limit',128)}
    if type(result['continuation_limit']) is not int or result['continuation_limit']<1 or result['probe_limit']+result['continuation_limit']>512:raise ValueError('Invalid continuation allowance')
    return result


@dataclass(frozen=True)
class Cursor:
    cnf: tuple
    starts: tuple
    offset: int
    index: tuple


def restart_cursor(cursor,counts):
    index=probes.prepare_index(cursor.cnf,counts)
    for assumption in cursor.starts[:cursor.offset]:
        counts['continuation_repeated_attempts']+=1
        if probes.indexed_probe(cursor.cnf,assumption,index,counts) is not None:raise ValueError('Clear prefix changed')
    return Cursor(cursor.cnf,cursor.starts,cursor.offset,index)


def advance(current,allowance,rounds_left,limits,counts,cursor=None):
    records=[];transports=[];diagnostics=[];spent=0;reason='round-limit';saved=None
    if cursor is not None and cursor.cnf!=current:raise ValueError('Cursor source changed')
    for _ in range(rounds_left):
        if current in ((),((),)):reason='constant';break
        if spent>=allowance:reason='probe-limit';break
        vs=sorted({abs(l) for c in current for l in c});starts=tuple(l for v in vs for l in (v,-v))
        if cursor is not None:
            if cursor.starts!=starts or type(cursor.offset) is not int or not 0<=cursor.offset<len(starts):raise ValueError('Invalid cursor schedule')
            offset=cursor.offset;index=cursor.index;counts['continuation_cursor_uses']+=1;counts['continuation_skipped_attempts']+=offset;cursor=None
        else:offset=0;index=probes.prepare_index(current,counts)
        failures=[];attempted=0
        for assumption in starts[offset:]:
            if spent>=allowance:break
            ev=probes.indexed_probe(current,assumption,index,counts)
            spent+=1;attempted+=1;counts['probe_attempts']+=1
            if ev is not None:probes.check_probe(current,ev,counts);failures.append(ev)
        end=offset+attempted;truncated=end<len(starts)
        diag=dict(probes=attempted,failures=len(failures),truncated=truncated,offset=offset);diagnostics.append(diag)
        if not failures:
            reason='probe-limit' if truncated else 'no-failed-literal'
            if truncated:saved=Cursor(current,starts,end,index)
            break
        augmented=relations.clean_quotient(current+tuple((-ev['assumption'],) for ev in failures),counts)
        units,active,udiag=symbolic.preprocess(augmented,'units',limits,counts)
        closed,names=native.normalize(active,counts);fixed={abs(s['literal']):s['literal']>0 for s in units};progress=binary.variables(current)-binary.variables(closed)
        records.append(dict(failures=failures,units=units));transports.append((augmented,names,fixed));diag.update(units=udiag,variables_removed=progress)
        counts['probe_accepted_rounds']+=1;counts['probe_removed_variables']+=progress;current=closed
        if progress<=0:reason='no-variable-progress';break
    return records,current,transports,dict(probes=diagnostics,spent=spent,reason=reason),saved


def prepare_edge(raw,mode,limits,counts):
    steps,relation,after_steps,rounds,current,binary_data,bdiag=binary.prepare_edge(raw,'closure',limits,counts)
    allowance=limits['probe_limit']+(limits['continuation_limit'] if mode=='eager' else 0)
    records,current,transports,pdiag,cursor=advance(current,allowance,limits['probe_round_limit'],limits,counts)
    pdiag['binary']=bdiag;tail=None;tail_data=None;tail_diag=None
    if current not in ((),((),)):
        counts['post_probe_relation_searches']+=1
        units,ev,after,closed,data,tail_diag=relations.prepare_edge(current,'relations',limits,counts)
        if units or ev is not None or after:
            if closed not in ((),((),)) and binary.variables(closed)>=binary.variables(current):raise ValueError('Nonprogressing relation')
            tail=dict(units=units,relation=ev,after_units=after);tail_data=data
            counts['post_probe_transforms']+=1;counts['post_probe_removed_variables']+=binary.variables(current)-binary.variables(closed);current=closed
        elif closed!=current:raise ValueError('Unrecorded relation change')
    return steps,relation,after_steps,rounds,records,tail,current,((binary_data,transports),tail_data),dict(probes=pdiag,post_relation=tail_diag,continuation=None),cursor


def replay_edge(raw,steps,relation,after_steps,rounds,records,tail,extension,mode,limits,counts):
    initial={**limits,'probe_limit':limits['probe_limit']+(limits['continuation_limit'] if mode=='eager' else 0)}
    current,data=prior.replay_edge(raw,steps,relation,after_steps,rounds,records,tail,'relations',initial,counts)
    if type(extension) is not list or len(records)+len(extension)>limits['probe_round_limit'] or (extension and mode not in ('restart','resume')):raise ValueError('Invalid continuation rounds')
    extra=[];total=0
    for i,r in enumerate(extension):
        if type(r) is not dict or set(r)!={'failures','units'} or type(r['failures']) is not list or not r['failures']:raise ValueError('Invalid continuation round')
        literals=[probes.check_probe(current,ev,counts) for ev in r['failures']];total+=len(literals)
        if len(set(literals))!=len(literals) or total>limits['continuation_limit']:raise ValueError('Excessive continuation failures')
        augmented=relations.clean_quotient(current+tuple((l,) for l in literals),counts)
        closed,names,fixed=replay(augmented,r['units'],limits,counts,fold=False)
        if i+1<len(extension) and binary.variables(closed)>=binary.variables(current):raise ValueError('Nonprogressing continuation round')
        extra.append((augmented,names,fixed));current=closed;counts['continuation_checked_rounds']+=1
    return current,(data,extra)


def relation_restore(data,model):
    initial,extra=data
    if model is None:return None
    for transport in reversed(extra):model=restore(*transport,model)
    return prior.relation_restore(initial,model)


def discover(source,counts=None,*,mode='resume',**values):
    if mode not in MODES:raise ValueError('Invalid closure mode')
    counts=Counter() if counts is None else counts;limits=options(values);cnf,names=native.normalize(source,counts)
    prefix,active,pdiag=symbolic.preprocess(cnf,'fold',limits,counts);residual,transport=native.normalize(active,counts)
    prefix_fixed={abs(s['literal']):s['literal']>0 for s in prefix if s['kind']=='unit'}
    nodes=[];edges=[];memo={};models={};edge_models={};attempts=[];edge_diagnostics=[]
    def visit(raw,depth):
        raw,_=native.normalize(raw,counts)
        steps,relation,after_steps,rounds,probe_rounds,tail,closed,transport_data,diag,cursor=prepare_edge(raw,mode,limits,counts)
        extension=[];extra=[];gate=None;gate_diag=None
        if mode in ('restart','resume') and diag['probes']['reason']=='probe-limit' and closed not in ((),((),)):
            gate,gate_diag=bucket.discover(closed,counts,**{k:limits[k] for k in bucket.DEFAULTS});counts['continuation_gate_calls']+=1
            if gate['status']=='unresolved':
                before=closed
                if cursor is not None and cursor.cnf!=closed:cursor=None;counts['continuation_cursor_invalidations']+=1
                if mode=='resume' and cursor is not None:counts['continuation_index_reuses']+=1
                if mode=='restart' and cursor is not None:cursor=restart_cursor(cursor,counts)
                extension,closed,extra,ediag,_=advance(closed,limits['continuation_limit'],limits['probe_round_limit']-len(probe_rounds),limits,counts,cursor)
                counts['continuation_attempts']+=ediag['spent'];diag['continuation']=ediag
                if closed!=before:gate=None
        diag['gate']=gate_diag
        transport_data=(transport_data,extra)
        key=closed,depth;counts['closed_lookup_calls']+=1;counts['closed_lookup_literals']+=sum(map(len,closed))
        if key in memo:
            target=memo[key];counts['closed_memo_hits']+=1
        else:
            counts['closed_bucket_calls']+=1
            proof,bdiag=(gate,gate_diag) if gate is not None else bucket.discover(closed,counts,**{k:limits[k] for k in bucket.DEFAULTS})
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
        edge=dict(cnf=list(map(list,raw)),depth=depth,units=steps,relation=relation,after_units=after_steps,rounds=rounds,probe_rounds=probe_rounds,tail=tail,continuation=extension,residual=list(map(list,closed)),target=target)
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
        if type(edge) is not dict or set(edge)!={'cnf','depth','units','relation','after_units','rounds','probe_rounds','tail','continuation','residual','target'}:raise ValueError('Invalid transport edge')
        raw,_=native.normalize(edge['cnf'],counts);depth=edge['depth'];target=edge['target']
        if edge['cnf']!=list(map(list,raw)) or type(depth) is not int or not 0<=depth<=limits['depth_limit'] or type(target) is not int or not 0<=target<len(nodes):raise ValueError('Invalid transport identity')
        closed,transport_data=replay_edge(raw,edge['units'],edge['relation'],edge['after_units'],edge['rounds'],edge['probe_rounds'],edge['tail'],edge['continuation'],mode,limits,counts)
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
