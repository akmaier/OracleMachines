"""Feed checked pair consequences through bounded, source-bound refinement rounds."""
from collections import Counter
from experiments import cnf_selective_probes as prior
from experiments import cnf_pair_probe_learning as joint
probes=prior.probes;binary=prior.binary;relations=prior.relations
symbolic=prior.symbolic;conditioned=prior.conditioned;bucket=prior.bucket;native=prior.native
replay=prior.replay;restore=prior.restore;relation_restore=prior.relation_restore
restart_cursor=prior.restart_cursor;advance=prior.advance
FORMAT='cnf-pair-feedback-buckets-v1'
DEFAULTS={**prior.DEFAULTS,'pair_limit':256,'learn_limit':32}
MODES=('base','larger','feedback')


def base_options(limits):return {k:v for k,v in limits.items() if k in prior.DEFAULTS}


def options(values):
    if set(values)-set(DEFAULTS):raise ValueError('Unknown joint limit')
    result={**prior.options(base_options(values)),**{k:values.get(k,DEFAULTS[k]) for k in ('pair_limit','learn_limit')}}
    if any(type(result[k]) is not int or not 1<=result[k]<=2048 for k in ('pair_limit','learn_limit')):raise ValueError('Invalid joint limit')
    return result


def policy(mode,limits):
    if mode not in MODES:raise ValueError('Invalid feedback mode')
    multiplier=2 if mode=='larger' else 1
    return (2 if mode=='feedback' else 1),dict(pair_limit=multiplier*limits['pair_limit'],learn_limit=multiplier*limits['learn_limit'])


def terminal_transport(source,terminal,counts):
    """Reconstruct transport only after the entire depth-zero terminal is checked."""
    cnf,names=native.normalize(source,counts)
    residual,transport,fixed=replay(cnf,terminal['prefix'],terminal['limits'],counts,fold=True)
    if len(terminal['nodes'])!=1 or len(terminal['edges'])!=1:raise ValueError('Nonlinear feedback terminal')
    edge=terminal['edges'][terminal['root']]
    if edge['cnf']!=list(map(list,residual)):raise ValueError('Wrong feedback edge source')
    closed,data=prior.replay_edge(residual,edge['units'],edge['relation'],edge['after_units'],edge['rounds'],edge['probe_rounds'],edge['tail'],edge['continuation'],'restart',terminal['limits'],counts)
    if edge['residual']!=list(map(list,closed)):raise ValueError('Changed feedback residual')
    counts['feedback_transport_reconstructions']+=1
    return closed,(cnf,names,transport,fixed,data)


def lift_terminal(data,model):
    cnf,names,transport,fixed,edge_data=data
    lifted=restore(cnf,transport,fixed,relation_restore(edge_data,model))
    return {name:lifted[i+1] for i,name in enumerate(names)}


def discover_refinement(source,mode,limits,counts):
    maximum,pair_options=policy(mode,limits);current=source;rounds=[];diagnostics=[];transports=[];reason='round-limit';status='unresolved';model=None
    for i in range(maximum):
        evidence,jdiag=joint.discover(current,counts,mode='shared',**pair_options)
        learned=joint.check(current,evidence,counts,**pair_options)
        diagnostic=dict(pair=jdiag);diagnostics.append(diagnostic)
        if not learned:reason='no-new-clause';break
        augmented=relations.clean_quotient(current+learned,counts)
        terminal,td=prior.discover(augmented,counts,mode='restart',**{**base_options(limits),'depth_limit':0})
        got=prior.check_certificate(augmented,terminal,counts);status=terminal['status'];model=got['model']
        rounds.append(dict(evidence=evidence,terminal=terminal));diagnostic['terminal']=td
        counts['feedback_accepted_rounds']+=1
        if terminal['status']!='unresolved':reason='decided';break
        if i+1<maximum:
            current,data=terminal_transport(augmented,terminal,counts);transports.append(data)
    if model is not None:
        for data in reversed(transports):model=lift_terminal(data,model)
        if not native.holds(source,model):raise ValueError('Invalid discovered feedback witness')
    return (dict(rounds=rounds) if rounds else None),dict(rounds=diagnostics,reason=reason),status,model


def check_refinement(source,ref,mode,limits,counts):
    maximum,pair_options=policy(mode,limits)
    if type(ref) is not dict or set(ref)!={'rounds'} or type(ref['rounds']) is not list or not 1<=len(ref['rounds'])<=maximum:raise ValueError('Invalid feedback rounds')
    current=source;transports=[];status='unresolved';model=None
    for i,rnd in enumerate(ref['rounds']):
        if type(rnd) is not dict or set(rnd)!={'evidence','terminal'}:raise ValueError('Invalid feedback round')
        learned=joint.check(current,rnd['evidence'],counts,**pair_options)
        if not learned:raise ValueError('Empty feedback round')
        augmented=relations.clean_quotient(current+learned,counts);terminal=rnd['terminal']
        if type(terminal) is not dict or terminal.get('mode')!='restart' or terminal.get('limits')!={**base_options(limits),'depth_limit':0}:raise ValueError('Changed feedback terminal policy')
        got=prior.check_certificate(augmented,terminal,counts);status=terminal['status'];model=got['model']
        counts['feedback_checked_rounds']+=1
        if i+1<len(ref['rounds']):
            if status!='unresolved':raise ValueError('Feedback after decided terminal')
            current,data=terminal_transport(augmented,terminal,counts);transports.append(data)
    if model is not None:
        for data in reversed(transports):model=lift_terminal(data,model)
        if not native.holds(source,model):raise ValueError('Invalid feedback source witness')
    return status,model


def discover(source,counts=None,*,mode='feedback',**values):
    if mode not in MODES:raise ValueError('Invalid closure mode')
    counts=Counter() if counts is None else counts;limits=options(values);cnf,names=native.normalize(source,counts)
    prefix,active,pdiag=symbolic.preprocess(cnf,'fold',limits,counts);residual,transport=native.normalize(active,counts)
    prefix_fixed={abs(s['literal']):s['literal']>0 for s in prefix if s['kind']=='unit'}
    nodes=[];edges=[];memo={};models={};edge_models={};attempts=[];edge_diagnostics=[]
    def visit(raw,depth):
        raw,_=native.normalize(raw,counts)
        steps,relation,after_steps,rounds,probe_rounds,tail,closed,transport_data,diag,cursor=prior.prepare_edge(raw,'restart',base_options(limits),counts)
        extension=[];extra=[];gate=None;gate_diag=None
        if diag['probes']['reason']=='probe-limit' and closed not in ((),((),)):
            gate,gate_diag=bucket.discover(closed,counts,**{k:limits[k] for k in bucket.DEFAULTS});counts['continuation_gate_calls']+=1
            if gate['status']=='unresolved':
                before=closed
                if cursor is not None and cursor.cnf!=closed:cursor=None;counts['continuation_cursor_invalidations']+=1
                if cursor is not None:cursor=restart_cursor(cursor,counts)
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
            refinement=None
            status=proof['status'];model=dict(enumerate(proof['model'],1)) if status=='sat' else None
            if status=='unresolved' and depth==0:
                refinement,fd,status,model=discover_refinement(closed,mode,limits,counts)
                bdiag={**bdiag,'feedback':fd}
            node=dict(cnf=list(map(list,closed)),depth=depth,bucket=proof,refinement=refinement,kind='leaf',status=status)
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
        closed,transport_data=prior.replay_edge(raw,edge['units'],edge['relation'],edge['after_units'],edge['rounds'],edge['probe_rounds'],edge['tail'],edge['continuation'],'restart',base_options(limits),counts)
        if edge['residual']!=list(map(list,closed)) or nodes[target].get('cnf')!=edge['residual'] or nodes[target].get('depth')!=depth:raise ValueError('Wrong closed target')
        edge_data.append(transport_data);counts['closed_checked_edges']+=1
    models={};known=set()
    def edge_model(e):
        model=models[edges[e]['target']]
        return relation_restore(edge_data[e],model)
    for i,node in enumerate(nodes):
        common={'cnf','depth','bucket','refinement','kind','status'}
        if not common<=set(node):raise ValueError('Invalid closed node')
        local,_=native.normalize(node['cnf'],counts);depth=node['depth'];kind=node['kind']
        if node['cnf']!=list(map(list,local)) or type(depth) is not int or not 0<=depth<=limits['depth_limit']:raise ValueError('Invalid closed node identity')
        if (local,depth) in known:raise ValueError('Duplicate shared closed residual')
        known.add((local,depth))
        if type(node['bucket']) is not dict or node['bucket'].get('limits')!={k:limits[k] for k in bucket.DEFAULTS} or node['bucket'].get('reduce') is not True:raise ValueError('Changed closed bucket policy')
        result=bucket.check_certificate(local,node['bucket'],counts);status=node['bucket']['status'];model=result['model']
        ref=node['refinement']
        if ref is not None:
            if depth!=0 or kind!='leaf' or status!='unresolved':raise ValueError('Invalid feedback refinement')
            status,model=check_refinement(local,ref,mode,limits,counts)
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
