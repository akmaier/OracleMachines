"""Exact local clause-width classification of explicit Boolean relation tables.

A cover is equivalent on the same variables, without auxiliaries. An obstruction
is one excluded assignment whose every width-k restriction extends to a model.
Budget exhaustion is a third, unresolved result, never a lower-bound claim.
"""
from collections import Counter
from itertools import combinations,product
FORMAT='cnf-factor-clause-width-v1'


def validate_factor(factor):
    if type(factor) is not dict or set(factor)!={'scope','bits'}:raise ValueError('Invalid factor')
    scope=factor['scope'];bits=factor['bits']
    if type(scope) is not list or any(type(v) is not int or v<1 for v in scope) or scope!=sorted(set(scope)) or len(scope)>12:raise ValueError('Invalid factor scope')
    if type(bits) is not int or not 0<=bits<1<<(1<<len(scope)):raise ValueError('Invalid factor table')
    return scope,bits


def assignments(n):return range(1<<n)


def discover(factor,width=3,budget=65536,counts=None):
    counts=Counter() if counts is None else counts;scope,bits=validate_factor(factor);n=len(scope)
    if type(width) is not int or not 0<=width<=12 or type(budget) is not int or budget<0:raise ValueError('Invalid classification policy')
    full=(1<<(1<<n))-1;clauses=[];covered=0;spent=0
    proof=dict(format=FORMAT,scope=scope[:],bits=bits,width=width,status='unresolved',clauses=[],obstruction=None)
    if bits==full:proof['status']='cover';return proof,dict(reason='tautology',spent=0)
    if bits==0:proof.update(status='cover',clauses=[[]]);return proof,dict(reason='false',spent=0)
    if n<=width and (full^bits).bit_count()==1:
        row=(full^bits).bit_length()-1;proof.update(status='cover',clauses=[[(-v if row>>i&1 else v) for i,v in enumerate(scope)]])
        counts['clause_direct_covers']+=1
        return proof,dict(reason='single-clause',spent=0)
    masks=[sum(1<<row for row in assignments(n) if row>>i&1) for i in range(n)];counts['clause_mask_rows']+=n*(1<<n)
    for size in range(1,min(width,n)+1):
        for slots in combinations(range(n),size):
            for signs in product((-1,1),repeat=size):
                if spent>=budget:return proof,dict(reason='candidate-budget',spent=spent)
                spent+=1;counts['clause_candidates']+=1
                mask=full
                for i,sign in zip(slots,signs):mask &= masks[i] if sign<0 else full^masks[i];counts['clause_mask_intersections']+=1
                if mask & bits:continue
                clause=tuple(sign*scope[i] for i,sign in zip(slots,signs))
                if any(set(prev)<=set(clause) for prev in clauses):continue
                clauses.append(clause);covered|=mask
    if covered==full^bits:
        proof.update(status='cover',clauses=list(map(list,clauses)))
        return proof,dict(reason='exact-cover',spent=spent)
    row=next(r for r in assignments(n) if not bits>>r&1 and not covered>>r&1);witnesses=[]
    # Every smaller coordinate set extends to one of these fixed-size sets.
    for slots in combinations(range(n),min(width,n)):
        mask=sum(1<<i for i in slots)
        for witness in assignments(n):
            if spent>=budget:return proof,dict(reason='obstruction-budget',spent=spent)
            spent+=1;counts['clause_obstruction_candidates']+=1
            if bits>>witness&1 and witness&mask==row&mask:witnesses.append(witness);break
        else:raise AssertionError('Missing obstruction completion')
    proof.update(status='obstruction',obstruction=dict(row=row,witnesses=witnesses))
    return proof,dict(reason='width-obstruction',spent=spent)


def check(factor,proof,counts=None):
    counts=Counter() if counts is None else counts;scope,bits=validate_factor(factor);n=len(scope)
    if type(proof) is not dict or set(proof)!={'format','scope','bits','width','status','clauses','obstruction'} or proof['format']!=FORMAT or proof['scope']!=scope or proof['bits']!=bits:raise ValueError('Changed factor binding')
    width=proof['width'];status=proof['status'];clauses=proof['clauses'];obs=proof['obstruction']
    if type(width) is not int or not 0<=width<=12 or type(clauses) is not list:raise ValueError('Invalid width policy')
    if status=='unresolved':
        if clauses or obs is not None:raise ValueError('Unresolved classifier carries authority')
        return status
    if status=='cover':
        if obs is not None:raise ValueError('Cover has an obstruction')
        seen=set()
        for clause in clauses:
            if type(clause) is not list or len(clause)>width or any(type(l) is not int or abs(l) not in scope for l in clause) or len({abs(l) for l in clause})!=len(clause):raise ValueError('Invalid cover clause')
            key=tuple(sorted(clause))
            if key in seen:raise ValueError('Duplicate cover clause')
            seen.add(key)
        for row in assignments(n):
            values={v:bool(row>>i&1) for i,v in enumerate(scope)}
            actual=all(any(values[abs(l)]==(l>0) for l in clause) for clause in clauses)
            if actual!=bool(bits>>row&1):raise ValueError('Cover changes factor relation')
            counts['clause_cover_verified_rows']+=1;counts['clause_cover_verified_literals']+=sum(map(len,clauses))
        return status
    if status!='obstruction' or clauses or type(obs) is not dict or set(obs)!={'row','witnesses'}:raise ValueError('Invalid obstruction')
    row=obs['row'];witnesses=obs['witnesses'];sets=list(combinations(range(n),min(width,n)))
    if type(row) is not int or not 0<=row<1<<n or bits>>row&1 or type(witnesses) is not list or len(witnesses)!=len(sets):raise ValueError('Invalid excluded row or witness coverage')
    for slots,witness in zip(sets,witnesses):
        mask=sum(1<<i for i in slots)
        if type(witness) is not int or not 0<=witness<1<<n or not bits>>witness&1 or witness&mask!=row&mask:raise ValueError('Invalid local completion')
        counts['clause_obstruction_verified_witnesses']+=1
    return status


PREFIX_FORMAT='cnf-factor-clause-prefix-v1'


def checked_prefix(source,prefix,counts):
    from experiments import cnf_bucket_continuation as continuation
    bucket=continuation.bucket
    if type(prefix) is not dict or prefix.get('status')!='unresolved':raise ValueError('Expected unresolved source prefix')
    bucket.check_certificate(source,prefix,counts);cnf,names=bucket.native.normalize(source,counts)
    if any(len(c)>prefix['limits']['bag_limit'] for c in cnf):raise ValueError('Prefix has unmaterialized wide clauses')
    factors,active,spent=continuation.materialize(cnf,prefix['steps'],counts)
    if spent>prefix['limits']['work_limit']:raise ValueError('Prefix exceeds projection budget')
    return bucket,cnf,names,factors,active,spent


def restore_prefix(cnf,names,prefix,factors,model,bucket):
    values={v:False for v in range(1,len(names)+1)};values.update(model)
    for step in reversed(prefix['steps']):
        boundary=sorted({v for i in step['inputs'] for v in factors[i]['scope']}-{step['variable']})
        row=sum(int(values[v])<<i for i,v in enumerate(boundary));values[step['variable']]=bool(step['choices']>>row&1)
    if not bucket.native.holds(cnf,values):raise ValueError('Invalid restored prefix model')
    return {name:values[i+1] for i,name in enumerate(names)}


def discover_prefix(source,prefix,width=4,budget=65536,counts=None):
    counts=Counter() if counts is None else counts
    if type(width) is not int or not 0<=width<=12 or type(budget) is not int or budget<0:raise ValueError('Invalid classification policy')
    bucket,cnf,names,factors,active,spent=checked_prefix(source,prefix,counts)
    entries=[];diagnostics=[];remaining=budget;raw=[];complete=True
    for i in sorted(active):
        proof,diag=discover(factors[i],width,remaining,counts);remaining-=diag['spent'];check(factors[i],proof,counts)
        entries.append(dict(index=i,certificate=proof));diagnostics.append(dict(index=i,**diag))
        if proof['status']=='cover':raw.extend(proof['clauses'])
        else:complete=False
    terminal=None;status='unresolved';model=None;terminal_diag=None
    if complete and spent<prefix['limits']['work_limit']:
        terminal,terminal_diag=bucket.discover(raw,counts,bag_limit=prefix['limits']['bag_limit'],work_limit=prefix['limits']['work_limit']-spent)
        result=bucket.check_certificate(raw,terminal,counts);status=terminal['status']
        if result['model'] is not None:model=restore_prefix(cnf,names,prefix,factors,result['model'],bucket)
    proof=dict(format=PREFIX_FORMAT,width=width,entries=entries,terminal=terminal,status=status,model=None if model is None else [model[v] for v in names])
    check_prefix(source,prefix,proof,counts)
    return proof,dict(factors=diagnostics,spent=budget-remaining,terminal=terminal_diag)


def check_prefix(source,prefix,proof,counts=None):
    counts=Counter() if counts is None else counts
    bucket,cnf,names,factors,active,spent=checked_prefix(source,prefix,counts)
    if type(proof) is not dict or set(proof)!={'format','width','entries','terminal','status','model'} or proof['format']!=PREFIX_FORMAT or type(proof['width']) is not int or not 0<=proof['width']<=12 or type(proof['entries']) is not list:raise ValueError('Invalid factorization certificate')
    entries=proof['entries']
    if any(type(e) is not dict or set(e)!={'index','certificate'} or type(e['index']) is not int for e in entries) or [e['index'] for e in entries]!=sorted(active):raise ValueError('Incomplete active-factor coverage')
    raw=[];complete=True
    for entry in entries:
        certificate=entry['certificate']
        if type(certificate) is not dict or certificate.get('width')!=proof['width']:raise ValueError('Changed factor width policy')
        status=check(factors[entry['index']],certificate,counts)
        if status=='cover':raw.extend(certificate['clauses'])
        else:complete=False
    terminal=proof['terminal'];status='unresolved';model=None
    if terminal is not None:
        remaining=prefix['limits']['work_limit']-spent
        if not complete or remaining<1 or type(terminal) is not dict or terminal.get('limits')!={'bag_limit':prefix['limits']['bag_limit'],'work_limit':remaining} or terminal.get('reduce') is not True:raise ValueError('Unjustified terminal or reset projection allowance')
        result=bucket.check_certificate(raw,terminal,counts)
        from experiments.cnf_bucket_continuation import materialize
        normalized,_=bucket.native.normalize(raw,counts);_,_,new_spent=materialize(normalized,terminal['steps'],counts)
        if new_spent>remaining:raise ValueError('Terminal exceeds remaining projection allowance')
        status=terminal['status']
        if result['model'] is not None:model=restore_prefix(cnf,names,prefix,factors,result['model'],bucket)
    expected=None if model is None else [model[v] for v in names]
    if proof['status']!=status or proof['model']!=expected or (expected is not None and any(type(v) is not bool for v in proof['model'])):raise ValueError('Changed continuation verdict or witness')
    return dict(answer=None if status=='unresolved' else status=='sat',model=model)
