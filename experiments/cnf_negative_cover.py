"""Compile a covered source clause into ordinary split/unit/implication nodes.

Every literal of the source clause needs a checked negative conditioned screen.
Retained unit reasons and SCC paths are transported into an ordered split spine.
The last literal is forced by the residual source clause. No new native proof
kind, SCC solving or general search is used during publication.
"""
from collections import Counter
from copy import deepcopy
import time
from experiments.cnf_mixed_completion import select as previous_select
from experiments.cnf_residual_dag import FORMAT, restrict, propagate


def cover_candidate(source, discovery, counts=None):
    counts=Counter() if counts is None else counts
    negative={}
    for item in discovery['completions']:
        counts['cover_completion_reads']+=1
        if 'mixed' in item and item['mixed']['model'] is None:
            index=item['index'];literal=discovery['attempts'][index]['clause'][0]
            negative.setdefault(literal,index)
    if not negative:return None
    for cid,clause in enumerate(source):
        counts['cover_clause_visits']+=1;counts['cover_literal_visits']+=len(clause)
        literals=sorted(set(clause))
        if literals and not any(-l in literals for l in literals) and all(l in negative for l in literals):
            counts['cover_candidates']+=1
            return dict(clause_index=cid,clause=literals,attempts=[negative[l] for l in literals])
    return None


def select(solver,source,variable_limit=4,counts=None):
    counts=Counter() if counts is None else counts
    choice,trace=previous_select(solver,source,variable_limit,counts)
    d=trace['discovery']
    if d is None or (choice is not None and choice['kind']!='fallback-trace'):
        return choice,trace
    cover=cover_candidate(source,d,counts)
    if cover is None:return choice,trace
    if choice is not None:
        counts['fallback_trace_reuses']-=1
        counts['fallback_forced_variables']-=len(d['fixed'])
    trace['cover_previous_reason']=trace['reason'];trace['reason']='negative-cover';trace['cover']=cover
    _,_,root=solver._canonical(source)
    return dict(kind='negative-cover',root=root,**deepcopy(cover)),trace


def _check_condition(solver,source,literal,attempt,completion):
    counts=solver.counts
    if attempt['clause']!=[literal] or completion['mixed']['model'] is not None:
        raise ValueError('Wrong negative condition')
    premise=[list(c) for c in source]+[[literal]]
    counts['cover_premise_literal_payload']+=sum(map(len,premise))
    cnf,names,root=solver._canonical(premise);screen=attempt['screen']
    if screen['root']!=root or screen['conflict'] is not None:
        raise ValueError('Unbound negative premise')
    assigned={}
    for lit,cid in screen['trace']:
        if (type(lit) is not int or not lit or type(cid) is not int or not 0<=cid<len(cnf)
                or abs(lit) in assigned):raise ValueError('Invalid retained unit index')
        reason=cnf[cid];counts['cover_checked_reason_literals']+=len(reason)
        if (any(abs(l) in assigned and assigned[abs(l)]==(l>0) for l in reason)
                or [l for l in reason if abs(l) not in assigned]!=[lit]):
            raise ValueError('Retained literal is not forced')
        assigned[abs(lit)]=lit>0
    residual=restrict(cnf,assigned,counts)
    if (not residual or any(len(c)!=2 for c in residual)
            or screen['residual_literals']!=sum(map(len,residual))):
        raise ValueError('Expected a bound unit-closed binary residual')
    proof=completion['mixed']['proof'];v=proof['variable']
    variables={abs(l) for c in residual for l in c}
    if type(v) is not int or v not in variables or proof['kind']!='implications':
        raise ValueError('Invalid conditional contradiction')
    for start,end,path in ((v,-v,proof['forward']),(-v,v,proof['backward'])):
        current=start
        for nxt,cid in path:
            if (type(nxt) is not int or not nxt or type(cid) is not int or not 0<=cid<len(residual)
                    or residual[cid]!=tuple(sorted((-current,nxt)))):
                raise ValueError('Invalid retained implication edge')
            counts['cover_checked_implication_edges']+=1;current=nxt
        if current!=end:raise ValueError('Wrong contradiction endpoint')
    def raw(clause):return tuple((1 if l>0 else -1)*names[abs(l)-1] for l in clause)
    return dict(literal=literal,reasons=[raw(cnf[cid]) for _,cid in screen['trace']],
                residual=[raw(c) for c in residual],proof=proof,names=names)


def _checked_cover(solver,source,choice,discovery):
    _,_,root=solver._canonical(source)
    cid=choice['clause_index'];clause=choice['clause'];indices=choice['attempts']
    if (choice['kind']!='negative-cover' or choice['root']!=root or type(cid) is not int
            or not 0<=cid<len(source) or not clause or clause!=sorted(set(source[cid]))
            or any(-l in clause for l in clause) or len(indices)!=len(clause)
            or any(type(i) is not int or not 0<=i<len(discovery['attempts']) for i in indices)):
        raise ValueError('Unbound or incomplete source-clause cover')
    completions={c['index']:c for c in discovery['completions']}
    if len(completions)!=len(discovery['completions']):raise ValueError('Duplicate completion index')
    conditions=[]
    for literal,index in zip(clause,indices):
        if index not in completions or 'mixed' not in completions[index]:
            raise ValueError('Missing negative condition')
        conditions.append(_check_condition(solver,source,literal,discovery['attempts'][index],completions[index]))
    return conditions


def _branch_plan(solver,source,condition,external,plans):
    """Transport checked reasons/paths under stronger assignments, without SCC."""
    counts=solver.counts
    cnf,names,key=solver._canonical(restrict(source,external,counts))
    if key in plans:return key
    if () in cnf:
        plans[key]=dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False,proof=dict(kind='empty'));return key
    rename={v:i+1 for i,v in enumerate(names)};lookup={c:i for i,c in enumerate(cnf)}
    assigned={};trace=[];conflict=None
    for reason in condition['reasons']:
        counts['cover_transport_reason_literals']+=len(reason)
        if any(abs(l) in external and external[abs(l)]==(l>0) for l in reason):continue
        reduced=tuple(sorted((1 if l>0 else -1)*rename[abs(l)] for l in reason if abs(l) not in external))
        if reduced not in lookup:raise ValueError('Transported reason is absent from cofactor')
        cid=lookup[reduced]
        if any(abs(l) in assigned and assigned[abs(l)]==(l>0) for l in reduced):continue
        left=[l for l in reduced if abs(l) not in assigned]
        if not left:conflict=cid;break
        if len(left)!=1:raise ValueError('Transported reason ceased to be unit')
        assigned[abs(left[0])]=left[0]>0;trace.append([left[0],cid])
    if conflict is not None:
        proof=dict(kind='units',trace=trace,conflict=conflict)
    else:
        residual=restrict(cnf,assigned,counts)
        child,child_names,child_key=solver._canonical(residual)
        p=condition['proof'];old_names=condition['names']
        path_variables={abs(l) for path in (p['forward'],p['backward']) for _,cid in path for l in condition['residual'][cid]}
        if path_variables & set(external):
            # A fixed vertex of the contradictory cycle exposes a unit conflict.
            # Charge this bounded repair scan; never rediscover SCCs or branch.
            counts['cover_path_repairs']+=1
            fixed,repair,collision=propagate(child,counts)
            if collision is None:raise ValueError('Restricted contradiction did not unit-refute')
            origins={}
            for cid,c in enumerate(cnf):
                if any(abs(l) in assigned and assigned[abs(l)]==(l>0) for l in c):continue
                remaining=tuple(l for l in c if abs(l) not in assigned)
                origins.setdefault(remaining,cid)
            def parent_clause(c):return tuple(sorted((1 if l>0 else -1)*child_names[abs(l)-1] for l in c))
            for lit,cid in repair:
                trace.append([(1 if lit>0 else -1)*child_names[abs(lit)-1],origins[parent_clause(child[cid])]])
            proof=dict(kind='units',trace=trace,conflict=origins[parent_clause(child[collision])])
        else:
            child_rename={v:i+1 for i,v in enumerate(child_names)};child_lookup={c:i for i,c in enumerate(child)}
            def remap(raw):return (1 if raw>0 else -1)*child_rename[rename[abs(raw)]]
            def path(entries):
                translated=[]
                for nxt,cid in entries:
                    raw_clause=condition['residual'][cid];counts['cover_transport_path_literals']+=len(raw_clause)
                    mapped=tuple(sorted(remap(l) for l in raw_clause))
                    if mapped not in child_lookup:raise ValueError('Transported path clause is absent')
                    raw_nxt=(1 if nxt>0 else -1)*old_names[abs(nxt)-1]
                    translated.append([remap(raw_nxt),child_lookup[mapped]])
                return translated
            child_proof=dict(kind='implications',variable=remap(old_names[p['variable']-1]),
                forward=path(p['forward']),backward=path(p['backward']))
            plans.setdefault(child_key,dict(format=FORMAT,cnf=[list(c) for c in child],answer=False,proof=child_proof))
            if not trace:
                if key!=child_key:raise ValueError('Unjustified cofactor transition')
                return key
            proof=dict(kind='units',trace=trace,conflict=None,child=child_key)
    plans[key]=dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False,proof=proof)
    return key


def publish_cover(solver,source,choice,discovery):
    """Validate every condition, compile ordinary nodes, then publish/check them."""
    started=time.perf_counter();solver.counts=Counter()
    conditions=_checked_cover(solver,source,choice,discovery);plans={}
    def spine(index,external):
        cnf,names,key=solver._canonical(restrict(source,external,solver.counts))
        if key in plans:return key
        if () in cnf:
            plans.setdefault(key,dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False,proof=dict(kind='empty')));return key
        literal=choice['clause'][index]
        if index==len(conditions)-1:
            # All previous clause literals are false; the last one is a real unit.
            return _branch_plan(solver,source,conditions[index],external,plans)
        yes=dict(external);yes[abs(literal)]=literal>0
        high=_branch_plan(solver,source,conditions[index],yes,plans)
        no=dict(external);no[abs(literal)]=literal<0
        low=spine(index+1,no)
        variable=names.index(abs(literal))+1
        plans[key]=dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False,
            proof=dict(kind='split',variable=variable,low=low if literal>0 else high,high=high if literal>0 else low))
        return key
    root=spine(0,{})
    if root!=choice['root']:raise ValueError('Cover compiler changed its target')
    solver.counts['cover_planned_nodes']+=len(plans)
    for key,node in plans.items():
        existing=solver._read(key,node['cnf'],purpose='cover_publication')
        if existing is None:solver._store(key,node)
        elif existing['answer'] is not False:raise ValueError('Cover contradicts a checked model')
    solver.counts['negative_cover_publications']+=1
    n,b=solver.archive_storage()
    return dict(answer=False,model=None,root=root,metrics=dict(solver.counts),seconds=time.perf_counter()-started,
                archive_nodes=n,archive_payload_bytes=b)
