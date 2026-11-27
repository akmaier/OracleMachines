"""Bounded exact Boolean bucket projection with checked semantic support removal.

All rows are complete. Equal cofactors permit dropping a boundary coordinate,
but witness choices retain the full pre-reduction boundary. This is a separate
experimental JSON authority, not a change to native or Lean factor formats.
"""
from collections import Counter
from experiments import cnf_residual_dag as native
FORMAT='cnf-semantic-buckets-v1'
DEFAULTS=dict(bag_limit=8,work_limit=262144)


def leaf(clause):
    scope=sorted(map(abs,clause));forbidden=sum(1<<i for i,v in enumerate(scope) if -v in clause)
    return dict(scope=scope,bits=((1<<(1<<len(scope)))-1) ^ (1<<forbidden))


def project(inputs,variable,counts):
    boundary=sorted({v for f in inputs for v in f['scope']}-{variable});slots={v:i for i,v in enumerate(boundary)}
    layouts=[[(None if v==variable else slots[v]) for v in f['scope']] for f in inputs]
    bits=choices=0
    for row in range(1<<len(boundary)):
        for value in (False,True):
            good=True
            for factor,layout in zip(inputs,layouts):
                index=sum((int(value) if slot is None else (row>>slot)&1)<<i for i,slot in enumerate(layout))
                counts['bucket_table_probes']+=1
                if not (factor['bits']>>index & 1):good=False;break
            if good:
                bits |= 1<<row
                if value:choices |= 1<<row
                break
        counts['bucket_projected_rows']+=1
    return boundary,bits,choices


def reduce_support(scope,bits,counts):
    keep=[];n=len(scope)
    for i in range(n):
        essential=False
        for row in range(1<<n):
            if row>>i & 1:continue
            counts['bucket_support_pair_checks']+=1
            if ((bits>>row) ^ (bits>>(row|(1<<i)))) & 1:essential=True;break
        if essential:keep.append(i)
    result=0
    for row in range(1<<len(keep)):
        original=sum(((row>>i)&1)<<slot for i,slot in enumerate(keep))
        if bits>>original & 1:result |= 1<<row
        counts['bucket_compacted_rows']+=1
    counts['bucket_removed_coordinates']+=n-len(keep)
    return [scope[i] for i in keep],result


def evaluate(factor,assignment):
    index=sum(int(assignment[v])<<i for i,v in enumerate(factor['scope']))
    return bool(factor['bits']>>index & 1)


def cache_key(inputs,variable,reduce):
    bag=sorted({v for f in inputs for v in f['scope']});slots={v:i for i,v in enumerate(bag)}
    return (reduce,slots[variable],tuple(sorted((tuple(slots[v] for v in f['scope']),f['bits']) for f in inputs)))


def discover(source,counts=None,*,reduce=True,cache=None,**limits):
    counts=Counter() if counts is None else counts
    if set(limits)-set(DEFAULTS):raise ValueError('Unknown bucket limit')
    limits={**DEFAULTS,**limits}
    if type(reduce) is not bool or any(type(v) is not int or v<1 for v in limits.values()) or limits['bag_limit']>12:
        raise ValueError('Invalid bucket policy')
    cnf,names=native.normalize(source,counts);steps=[];factors=[];active=set();spent=0
    proof=dict(format=FORMAT,cnf=list(map(list,cnf)),reduce=reduce,limits=limits,steps=steps,status='unresolved',model=None)
    # Admission precedes materializing any wide clause relation.
    if any(len(c)>limits['bag_limit'] for c in cnf):return proof,dict(reason='leaf-width',spent=0)
    for c in cnf:
        active.add(len(factors));factors.append(leaf(c));counts['bucket_leaf_rows']+=1<<len(c)
    while True:
        if any(factors[i]['bits']==0 for i in active):proof['status']='unsat';break
        variables=sorted({v for i in active for v in factors[i]['scope']})
        if not variables:proof['status']='sat';break
        candidates=[]
        for v in variables:
            ids=sorted(i for i in active if v in factors[i]['scope']);bag={x for i in ids for x in factors[i]['scope']}
            counts['bucket_planning_scope_visits']+=sum(len(factors[i]['scope']) for i in ids)
            candidates.append((len(bag),len(ids),v,ids))
        width,_,variable,ids=min(candidates)
        if width>limits['bag_limit']:return proof,dict(reason='bag-width',width=width,spent=spent)
        inputs=[factors[i] for i in ids];cost=(1<<width)*len(ids);boundary=sorted({v for f in inputs for v in f['scope']}-{variable})
        key=cache_key(inputs,variable,reduce);counts['bucket_lookup_factors']+=len(inputs);counts['bucket_lookup_scope_visits']+=sum(len(f['scope']) for f in inputs)
        if cache is not None and key in cache:
            # Cached data is a proposal, checked by the full certificate verifier
            # before any verdict is accepted. No caller can bypass that check.
            slots,outbits,choices=cache[key];outscope=[boundary[i] for i in slots];counts['bucket_operator_hits']+=1
        else:
            if spent+cost>limits['work_limit']:return proof,dict(reason='row-work',spent=spent,next_cost=cost)
            spent+=cost;counts['bucket_reserved_probe_work']+=cost
            _,bits,choices=project(inputs,variable,counts)
            outscope,outbits=reduce_support(boundary,bits,counts) if reduce else (boundary,bits)
            if cache is not None:cache[key]=(tuple(boundary.index(v) for v in outscope),outbits,choices)
            counts['bucket_operator_misses']+=1
        steps.append(dict(variable=variable,inputs=ids,scope=outscope,bits=outbits,choices=choices))
        active.difference_update(ids);active.add(len(factors));factors.append(dict(scope=outscope,bits=outbits))
    if proof['status']=='sat':
        model={v:False for v in range(1,len(names)+1)}
        for step in reversed(steps):
            boundary=sorted({v for i in step['inputs'] for v in factors[i]['scope']}-{step['variable']})
            index=sum(int(model[v])<<i for i,v in enumerate(boundary));model[step['variable']]=bool(step['choices']>>index & 1)
        proof['model']=[model[v] for v in range(1,len(names)+1)]
    # Independent exhaustive local checking also covers every cache hit.
    check_certificate(source,proof,counts)
    return proof,dict(reason='complete',spent=spent)


def check_certificate(source,proof,counts=None):
    """Recompute each bucket using dictionaries, check support and witness lift."""
    counts=Counter() if counts is None else counts;cnf,names=native.normalize(source,counts)
    if (type(proof) is not dict or set(proof)!={'format','cnf','reduce','limits','steps','status','model'}
            or proof['format']!=FORMAT or proof['cnf']!=list(map(list,cnf)) or type(proof['reduce']) is not bool):
        raise ValueError('Invalid source-bound bucket certificate')
    limits=proof['limits']
    if (type(limits) is not dict or set(limits)!=set(DEFAULTS) or any(type(v) is not int or v<1 for v in limits.values())
            or limits['bag_limit']>12 or type(proof['steps']) is not list):raise ValueError('Invalid bucket limits')
    if any(len(c)>limits['bag_limit'] for c in cnf):
        if proof['steps'] or proof['status']!='unresolved' or proof['model'] is not None:raise ValueError('Wide uncomputed leaf has a verdict')
        return dict(answer=None,model=None)
    factors=[leaf(c) for c in cnf];active=set(range(len(factors)));eliminated=set()
    for step in proof['steps']:
        if type(step) is not dict or set(step)!={'variable','inputs','scope','bits','choices'}:raise ValueError('Invalid bucket step')
        v=step['variable'];ids=step['inputs'];scope=step['scope'];bits=step['bits'];choices=step['choices']
        if type(v) is not int or v in eliminated or type(ids) is not list or any(type(i) is not int for i in ids):raise ValueError('Invalid eliminated variable')
        expected=sorted(i for i in active if v in factors[i]['scope'])
        if not ids or ids!=expected:raise ValueError('Incomplete incident bucket')
        boundary=sorted({x for i in ids for x in factors[i]['scope']}-{v})
        if len(boundary)+1>limits['bag_limit']:raise ValueError('Oversized bucket')
        if (type(scope) is not list or any(type(x) is not int for x in scope) or scope!=sorted(set(scope)) or not set(scope)<=set(boundary)
                or type(bits) is not int or not 0<=bits<1<<(1<<len(scope))
                or type(choices) is not int or not 0<=choices<1<<(1<<len(boundary))):raise ValueError('Invalid relation encoding')
        if not proof['reduce'] and scope!=boundary:raise ValueError('Unexpected scope reduction')
        for row in range(1<<len(boundary)):
            assignment={x:bool(row>>i & 1) for i,x in enumerate(boundary)};feasible=[]
            for value in (False,True):
                assignment[v]=value;outcomes=[]
                for i in ids:
                    outcomes.append(evaluate(factors[i],assignment));counts['bucket_verify_table_probes']+=1
                if all(outcomes):feasible.append(value)
            output=evaluate(dict(scope=scope,bits=bits),assignment)
            if output!=bool(feasible):raise ValueError('Changed projected relation or omitted dependence')
            choice=bool(choices>>row & 1)
            if feasible and choice!=feasible[0] or not feasible and choice:raise ValueError('Invalid reconstruction choice')
            counts['bucket_verified_rows']+=1
        active.difference_update(ids);active.add(len(factors));factors.append(dict(scope=scope,bits=bits));eliminated.add(v)
        counts['bucket_checked_steps']+=1
    status=proof['status'];model=proof['model']
    if status=='unresolved':
        if model is not None:raise ValueError('Open bucket has a model')
        return dict(answer=None,model=None)
    if status=='unsat':
        if model is not None or not any(factors[i]['bits']==0 for i in active):raise ValueError('Missing empty relation')
        return dict(answer=False,model=None)
    if status!='sat' or any(factors[i]['scope'] or factors[i]['bits']!=1 for i in active):raise ValueError('Nonterminal bucket SAT claim')
    if type(model) is not list or len(model)!=len(names) or any(type(v) is not bool for v in model):raise ValueError('Incomplete SAT witness')
    assignment={i:v for i,v in enumerate(model,1)}
    if not native.holds(cnf,assignment):raise ValueError('Reconstructed witness violates source')
    return dict(answer=True,model={name:model[i] for i,name in enumerate(names)})
