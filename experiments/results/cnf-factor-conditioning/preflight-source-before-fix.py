"""Checked static conditioning of exact covers of a saved factor frontier.

The prefix and factor descriptions are shared across all branches. Projection
work is charged once for the old prefix and globally across the new branches.
This is a bounded experimental certificate, not an unrestricted SAT algorithm.
"""
from collections import Counter
from itertools import combinations, product
from experiments import cnf_factor_clause_width as covers
from experiments import cnf_bucket_continuation as continuation
from experiments import cnf_selective_width_buckets as previous
bucket=continuation.bucket
native=bucket.native
FORMAT='cnf-factor-conditioning-v1'


def cutset(clauses,limit,counts):
    graph={abs(v):set() for c in clauses for v in c}
    for clause in clauses:
        for a,b in combinations(map(abs,clause),2):
            graph[a].add(b);graph[b].add(a);counts['cutset_edge_visits']+=1
    result=[]
    for _ in range(min(limit,len(graph))):
        v=min(graph,key=lambda v:(-len(graph[v]),v));result.append(v)
        counts['cutset_rank_vertices']+=len(graph)
        for u in graph[v]:graph[u].discard(v)
        del graph[v]
    return result


def cofactor(clauses,fixed,counts):
    result=[]
    for clause in clauses:
        counts['cutset_restriction_literals']+=len(clause)
        if any(abs(l) in fixed and fixed[abs(l)]==(l>0) for l in clause):continue
        result.append([l for l in clause if abs(l) not in fixed])
    return result


def prepare(source,prefix,counts):
    return covers.checked_prefix(source,prefix,counts)


def entries_check(factors,active,entries,width,counts):
    if type(entries) is not list or any(type(e) is not dict or set(e)!={'index','certificate'} or type(e['index']) is not int for e in entries) or [e['index'] for e in entries]!=sorted(active):raise ValueError('Incomplete frontier factor coverage')
    raw=[];complete=True
    for entry in entries:
        proof=entry['certificate']
        if type(proof) is not dict or proof.get('width')!=width:raise ValueError('Changed cover width')
        status=covers.check(factors[entry['index']],proof,counts)
        if status=='cover':raw.extend(proof['clauses'])
        else:complete=False
    return raw,complete


def policy(width,limit):
    if type(width) is not int or not 0<=width<=12 or type(limit) is not int or not 0<=limit<=4:raise ValueError('Invalid factor conditioning policy')


def discover(source,prefix,counts=None,*,clause_width=4,cut_limit=4,clause_budget=65536):
    counts=Counter() if counts is None else counts;policy(clause_width,cut_limit)
    if type(clause_budget) is not int or clause_budget<0:raise ValueError('Invalid cover budget')
    _,cnf,names,factors,active,spent=prepare(source,prefix,counts)
    entries=[];remaining=clause_budget;diagnostics=[]
    for i in sorted(active):
        cert,diag=covers.discover(factors[i],clause_width,remaining,counts);remaining-=diag['spent']
        entries.append(dict(index=i,certificate=cert));diagnostics.append(dict(index=i,**diag))
    raw,complete=entries_check(factors,active,entries,clause_width,counts)
    pivots=cutset(raw,cut_limit,counts) if complete else [];branches=[];branch_diags=[];models=[];statuses=[]
    if complete:
        for values in product((False,True),repeat=len(pivots)):
            fixed=dict(zip(pivots,values));child=cofactor(raw,fixed,counts);allowance=prefix['limits']['work_limit']-spent
            terminal=None;status='unresolved';model=None;diag=dict(reason='shared-work-limit',spent=0)
            if allowance>0:
                terminal,diag=bucket.discover(child,counts,bag_limit=prefix['limits']['bag_limit'],work_limit=allowance)
                got=bucket.check_certificate(child,terminal,counts);spent+=diag['spent'];status=terminal['status']
                if got['model'] is not None:
                    model={abs(v):False for c in raw for v in c};model.update(got['model']);model.update(fixed)
                    if not native.holds(raw,model):raise ValueError('Invalid cofactor model')
            branches.append(dict(values=list(values),terminal=terminal));branch_diags.append(diag);statuses.append(status);models.append(model)
    status='sat' if 'sat' in statuses else 'unsat' if statuses and all(s=='unsat' for s in statuses) else 'unresolved'
    model=None
    if status=='sat':model=covers.restore_prefix(cnf,names,prefix,factors,models[statuses.index('sat')],bucket)
    proof=dict(format=FORMAT,clause_width=clause_width,cut_limit=cut_limit,entries=entries,cutset=pivots,branches=branches,status=status,model=None if model is None else [model[v] for v in names])
    check(source,prefix,proof,counts)
    return proof,dict(factors=diagnostics,clause_spent=clause_budget-remaining,branches=branch_diags,reserved_work=spent)


def check(source,prefix,proof,counts=None):
    counts=Counter() if counts is None else counts
    _,cnf,names,factors,active,spent=prepare(source,prefix,counts)
    if type(proof) is not dict or set(proof)!={'format','clause_width','cut_limit','entries','cutset','branches','status','model'} or proof['format']!=FORMAT:raise ValueError('Invalid conditioning certificate')
    policy(proof['clause_width'],proof['cut_limit'])
    raw,complete=entries_check(factors,active,proof['entries'],proof['clause_width'],counts)
    pivots=proof['cutset'];branches=proof['branches'];variables={abs(v) for c in raw for v in c}
    if type(pivots) is not list or any(type(v) is not int or v not in variables for v in pivots) or len(set(pivots))!=len(pivots) or len(pivots)>proof['cut_limit'] or type(branches) is not list:raise ValueError('Invalid cutset')
    # The checker need not rerun the heuristic. Any declared bounded cutset is
    # sound, but its entire Boolean partition must be present in canonical order.
    expected=list(product((False,True),repeat=len(pivots))) if complete else []
    if not complete and pivots or len(branches)!=len(expected):raise ValueError('Incomplete Boolean partition')
    statuses=[];models=[]
    for values,branch in zip(expected,branches):
        if type(branch) is not dict or set(branch)!={'values','terminal'} or type(branch['values']) is not list or any(type(v) is not bool for v in branch['values']) or branch['values']!=list(values):raise ValueError('Changed branch assignment')
        fixed=dict(zip(pivots,values));child=cofactor(raw,fixed,counts);terminal=branch['terminal'];status='unresolved';model=None
        if terminal is not None:
            allowance=prefix['limits']['work_limit']-spent
            if allowance<1 or type(terminal) is not dict or terminal.get('limits')!={'bag_limit':prefix['limits']['bag_limit'],'work_limit':allowance} or terminal.get('reduce') is not True:raise ValueError('Reset shared projection allowance')
            got=bucket.check_certificate(child,terminal,counts);normalized,_=native.normalize(child,counts)
            if any(len(c)>prefix['limits']['bag_limit'] for c in normalized):work=0
            else:_,_,work=continuation.materialize(normalized,terminal['steps'],counts)
            spent+=work
            if spent>prefix['limits']['work_limit']:raise ValueError('Exceeded shared projection allowance')
            status=terminal['status']
            if got['model'] is not None:
                model={v:False for v in variables};model.update(got['model']);model.update(fixed)
                if not native.holds(raw,model):raise ValueError('Changed cofactor witness')
        statuses.append(status);models.append(model);counts['cutset_checked_branches']+=1
    status='sat' if 'sat' in statuses else 'unsat' if statuses and all(s=='unsat' for s in statuses) else 'unresolved'
    model=None if status!='sat' else covers.restore_prefix(cnf,names,prefix,factors,models[statuses.index('sat')],bucket)
    expected_model=None if model is None else [model[v] for v in names]
    if proof['status']!=status or proof['model']!=expected_model or (model is not None and (type(proof['model']) is not list or any(type(v) is not bool for v in proof['model']))):raise ValueError('Changed conditioned verdict or source witness')
    return dict(answer=None if status=='unresolved' else status=='sat',model=model)


def frontier(source,context,target,counts=None):
    """Reconstruct the exact saved frontier from its checked whole-root context."""
    counts=Counter() if counts is None else counts
    previous.check_certificate(source,context,counts)
    if type(target) is not int or not 0<=target<len(context['nodes']):raise ValueError('Invalid frontier target')
    node=context['nodes'][target]
    if node['kind']!='leaf' or node['status']!='unresolved' or node['refinement'] is None:raise ValueError('Target is not an open refined leaf')
    current=node['cnf'];transports=[];prefix=node['bucket'];ref=node['refinement']
    for rnd in ref['rounds']:
        learned=previous.joint.check(current,rnd['evidence'],counts,**previous.policy(context['mode'],context['limits'])[1])
        augmented=previous.relations.clean_quotient(current+learned,counts)
        current,data=previous.terminal_transport(augmented,rnd['terminal'],counts);transports.append(data)
        current=list(map(list,current));prefix=rnd['terminal']['nodes'][-1]['bucket']
    wide=ref['widen']
    combined={**prefix,'limits':{**prefix['limits'],'bag_limit':prefix['limits']['bag_limit']+1},'steps':prefix['steps']+wide['steps'],'status':wide['status'],'model':wide['model']}
    bucket.check_certificate(current,combined,counts)
    return current,combined,transports


def lift_root(source,context,target,leaf_source,leaf_prefix,leaf_result,counts=None):
    """Transport a checked frontier SAT witness; verify it against the root CNF.

    Unresolved/UNSAT leaf outcomes do not by themselves close an old root. This
    adapter deliberately grants only SAT authority from an explicit full model.
    """
    counts=Counter() if counts is None else counts
    current,prefix,transports=frontier(source,context,target,counts)
    if list(map(list,current))!=list(map(list,leaf_source)) or prefix!=leaf_prefix:raise ValueError('Frontier is not bound to root context')
    if leaf_result['answer'] is not True:return dict(answer=None,model=None)
    model=leaf_result['model']
    if not native.holds(current,model):raise ValueError('Invalid frontier model')
    for data in reversed(transports):model=previous.lift_terminal(data,model)
    if not native.holds(context['nodes'][target]['cnf'],model):raise ValueError('Invalid refined leaf transport')
    models={target:model}
    def edge_model(index):
        edge=context['edges'][index]
        closed,data=previous.prior.replay_edge(tuple(map(tuple,edge['cnf'])),edge['units'],edge['relation'],edge['after_units'],edge['rounds'],edge['probe_rounds'],edge['tail'],edge['continuation'],'restart',context['limits'],counts)
        if list(map(list,closed))!=context['nodes'][edge['target']]['cnf']:raise ValueError('Changed root edge')
        result=previous.relation_restore(data,models[edge['target']])
        if not native.holds(edge['cnf'],result):raise ValueError('Invalid root edge transport')
        return result
    for i,node in enumerate(context['nodes']):
        if i in models or node['kind']!='split':continue
        for side,value in (('low',False),('high',True)):
            edge=node[side]
            if context['edges'][edge]['target'] in models:
                models[i]=previous.conditioned.lift(tuple(map(tuple,node['cnf'])),node['pivot'],value,edge_model(edge),counts);break
    root=context['root']
    if context['edges'][root]['target'] not in models:raise ValueError('Frontier has no path to root')
    cnf,names=native.normalize(source,counts);_,transport,fixed=previous.replay(cnf,context['prefix'],context['limits'],counts,fold=True)
    model=previous.restore(cnf,transport,fixed,edge_model(root));result={name:model[i+1] for i,name in enumerate(names)}
    if not native.holds(source,result):raise ValueError('Invalid original root witness')
    return dict(answer=True,model=result)
