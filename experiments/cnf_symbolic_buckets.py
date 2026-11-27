"""Checked complementary-clause folding and incremental unit preprocessing.

Only clauses with exactly equal remainders and opposite pivot literals may be
replaced by the remainder. General resolvents cannot replace their parents.
Occurrence and deletion-signature indexes update only affected clauses.
"""
from collections import Counter
import heapq
from experiments import cnf_conditioned_buckets as conditioned
native=conditioned.native
FORMAT='cnf-symbolic-buckets-v1'
DEFAULTS=dict(**conditioned.DEFAULTS,step_limit=512,index_work_limit=262144)
MODES=('base','units','fold')


def options(values):
    if set(values)-set(DEFAULTS):raise ValueError('Unknown symbolic limit')
    result={**DEFAULTS,**values}
    conditioned.options({k:v for k,v in result.items() if k in conditioned.DEFAULTS})
    if any(type(result[k]) is not int or result[k]<1 for k in ('step_limit','index_work_limit')):raise ValueError('Invalid symbolic limits')
    return result


def preprocess(cnf,mode,limits,counts):
    if mode=='base':return [],set(cnf),dict(reason='disabled',spent=0)
    active=set();occ={};signatures={};units=[];pairs=[];steps=[];spent=0
    def weight(c):return len(c)+(len(c)**2 if mode=='fold' else 0)
    def add(c):
        if c in active:return
        active.add(c)
        for l in c:occ.setdefault(l,set()).add(c);counts['symbolic_index_literal_updates']+=1
        if len(c)==1:heapq.heappush(units,c[0])
        if mode=='fold':
            for i,l in enumerate(c):
                key=(c[:i]+c[i+1:],abs(l));entry=signatures.setdefault(key,{})
                entry[l>0]=c;counts['symbolic_signature_literal_visits']+=len(c)
                if len(entry)==2:heapq.heappush(pairs,key)
    def remove(c):
        active.remove(c)
        for l in c:
            occ[l].remove(c);counts['symbolic_index_literal_updates']+=1
            if not occ[l]:del occ[l]
        if mode=='fold':
            for i,l in enumerate(c):
                key=(c[:i]+c[i+1:],abs(l));entry=signatures[key];del entry[l>0]
                if not entry:del signatures[key]
                counts['symbolic_signature_literal_visits']+=len(c)
    setup=sum(weight(c) for c in cnf);counts['symbolic_admission_literals']+=sum(map(len,cnf))
    if setup>limits['index_work_limit']:return [],set(cnf),dict(reason='initial-index-work',spent=0,next_cost=setup)
    spent=setup
    for c in cnf:add(c)
    reason='fixed-point'
    while () not in active:
        if len(steps)>=limits['step_limit']:reason='step-limit';break
        while units and (units[0],) not in active:heapq.heappop(units);counts['symbolic_stale_units']+=1
        if units:
            literal=units[0];affected=sorted(occ.get(literal,set())|occ.get(-literal,set()))
            new={tuple(l for l in c if l!=-literal) for c in affected if literal not in c}
            counts['symbolic_affected_clause_literals']+=sum(map(len,affected))
            action=dict(kind='unit',literal=literal)
        else:
            while pairs and len(signatures.get(pairs[0],{}))!=2:heapq.heappop(pairs);counts['symbolic_stale_pairs']+=1
            if not pairs:break
            core,pivot=pairs[0];entry=signatures[(core,pivot)];affected=sorted(entry.values());new={core}
            counts['symbolic_pair_lookups']+=1
            action=dict(kind='fold',left=list(affected[0]),right=list(affected[1]))
        fresh=new-(active-set(affected));cost=sum(weight(c) for c in affected)+sum(weight(c) for c in fresh)
        if spent+cost>limits['index_work_limit']:reason='index-work';break
        spent+=cost
        for c in affected:remove(c)
        for c in sorted(fresh):add(c)
        steps.append(action);counts['symbolic_'+action['kind']+'_steps']+=1
    if () in active:reason='empty-clause'
    counts['symbolic_reserved_index_work']+=spent;counts['symbolic_remaining_clauses']+=len(active)
    return steps,active,dict(reason=reason,spent=spent)


def discover(source,counts=None,*,mode='fold',**values):
    if mode not in MODES:raise ValueError('Invalid symbolic mode')
    counts=Counter() if counts is None else counts;limits=options(values);cnf,names=native.normalize(source,counts)
    steps,active,diag=preprocess(cnf,mode,limits,counts);residual,transport=native.normalize(active,counts)
    terminal,search=conditioned.discover(residual,counts,reuse=True,**{k:v for k,v in limits.items() if k in conditioned.DEFAULTS})
    model=None
    if terminal['status']=='sat':
        assignment={v:False for v in range(1,len(names)+1)}
        for step in steps:
            if step['kind']=='unit':assignment[abs(step['literal'])]=step['literal']>0
        assignment.update({v:terminal['model'][i] for i,v in enumerate(transport)})
        model=[assignment[v] for v in range(1,len(names)+1)]
    proof=dict(format=FORMAT,cnf=list(map(list,cnf)),mode=mode,limits=limits,steps=steps,residual=list(map(list,residual)),terminal=terminal,status=terminal['status'],model=model)
    check_certificate(source,proof,counts)
    return proof,dict(preprocessing=diag,conditioned=search)


def check_certificate(source,proof,counts=None):
    counts=Counter() if counts is None else counts;cnf,names=native.normalize(source,counts)
    fields={'format','cnf','mode','limits','steps','residual','terminal','status','model'}
    if type(proof) is not dict or set(proof)!=fields or proof['format']!=FORMAT or proof['cnf']!=list(map(list,cnf)) or proof['mode'] not in MODES:
        raise ValueError('Invalid symbolic source or format')
    if type(proof['limits']) is not dict or set(proof['limits'])!=set(DEFAULTS):raise ValueError('Invalid symbolic policy')
    limits=options(proof['limits']);steps=proof['steps'];mode=proof['mode'];active=set(cnf);fixed={}
    if type(steps) is not list or len(steps)>limits['step_limit'] or (mode=='base' and steps):raise ValueError('Invalid symbolic program')
    for step in steps:
        if type(step) is not dict or 'kind' not in step:raise ValueError('Invalid symbolic step')
        if step['kind']=='unit' and set(step)=={'kind','literal'}:
            l=step['literal']
            if type(l) is not int or not l or (l,) not in active or abs(l) in fixed:raise ValueError('Missing active unit')
            fixed[abs(l)]=l>0
            # Independent full scan; discovery uses a maintained occurrence index.
            active=set(native.restrict_scan(active,{abs(l):l>0},counts))
            counts['symbolic_checked_units']+=1
        elif step['kind']=='fold' and set(step)=={'kind','left','right'} and mode=='fold':
            left=step['left'];right=step['right']
            if any(type(c) is not list or any(type(l) is not int for l in c) or c!=sorted(set(c)) for c in (left,right)):
                raise ValueError('Invalid fold parents')
            left=tuple(left);right=tuple(right)
            if left not in active or right not in active or left==right:raise ValueError('Missing fold parent')
            a=set(left)-set(right);b=set(right)-set(left)
            if len(a)!=1 or b!={-next(iter(a))}:raise ValueError('Unequal fold remainders')
            core=tuple(sorted(set(left)&set(right)));active.remove(left);active.remove(right);active.add(core)
            counts['symbolic_checked_folds']+=1;counts['symbolic_verify_fold_literals']+=len(left)+len(right)
        else:raise ValueError('Unknown symbolic rule')
    residual,transport=native.normalize(active,counts)
    if proof['residual']!=list(map(list,residual)) or type(proof['terminal']) is not dict or proof['terminal'].get('limits')!={k:v for k,v in limits.items() if k in conditioned.DEFAULTS} or proof['terminal'].get('reuse') is not True:
        raise ValueError('Changed symbolic residual or terminal policy')
    result=conditioned.check_certificate(residual,proof['terminal'],counts)
    if proof['status']!=proof['terminal']['status']:raise ValueError('Changed symbolic verdict')
    model=proof['model']
    if result['answer'] is not True:
        if model is not None:raise ValueError('Unexpected symbolic model')
        return dict(answer=result['answer'],model=None)
    assignment={v:False for v in range(1,len(names)+1)};assignment.update(fixed)
    assignment.update({v:result['model'][i+1] for i,v in enumerate(transport)})
    expected=[assignment[v] for v in range(1,len(names)+1)]
    if type(model) is not list or any(type(v) is not bool for v in model) or model!=expected or not native.holds(cnf,assignment):raise ValueError('Invalid symbolic source witness')
    return dict(answer=True,model={name:model[i] for i,name in enumerate(names)})
