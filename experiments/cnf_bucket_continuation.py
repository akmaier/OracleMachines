"""Extend a checked semantic-bucket prefix without repeating its projection work."""
from collections import Counter
from copy import deepcopy
from experiments import cnf_semantic_buckets as bucket
native=bucket.native


def materialize(cnf,steps,counts):
    factors=[bucket.leaf(c) for c in cnf];active=set(range(len(factors)));spent=0
    counts['widen_materialized_leaf_rows']+=sum(1<<len(c) for c in cnf)
    for step in steps:
        bag={v for i in step['inputs'] for v in factors[i]['scope']}
        spent+=(1<<len(bag))*len(step['inputs'])
        active.difference_update(step['inputs']);active.add(len(factors));factors.append(dict(scope=step['scope'][:],bits=step['bits']))
        counts['widen_materialized_steps']+=1
    return factors,active,spent


def check(source,prefix,extension,counts=None):
    counts=Counter() if counts is None else counts
    if type(prefix) is not dict or prefix.get('status')!='unresolved' or prefix.get('reduce') is not True:raise ValueError('Invalid widening prefix')
    if type(extension) is not dict or set(extension)!={'steps','status','model'} or type(extension['steps']) is not list:raise ValueError('Invalid widening suffix')
    limits={**prefix['limits'],'bag_limit':prefix['limits']['bag_limit']+1}
    if limits['bag_limit']>12:raise ValueError('Widening exceeds supported width')
    proof={**prefix,'limits':limits,'steps':prefix['steps']+extension['steps'],'status':extension['status'],'model':extension['model']}
    got=bucket.check_certificate(source,proof,counts)
    cnf,_=native.normalize(source,counts)
    if not any(len(c)>limits['bag_limit'] for c in cnf):
        _,_,spent=materialize(cnf,proof['steps'],counts)
        if spent>limits['work_limit']:raise ValueError('Widening exceeds total projection allowance')
    counts['widen_checked_suffix_steps']+=len(extension['steps'])
    return got


def discover(source,prefix,counts=None,*,mode='resume'):
    counts=Counter() if counts is None else counts
    if mode not in ('restart','resume') or prefix.get('status')!='unresolved' or prefix.get('reduce') is not True:raise ValueError('Invalid widening mode or prefix')
    limits={**prefix['limits'],'bag_limit':prefix['limits']['bag_limit']+1}
    if limits['bag_limit']>12:raise ValueError('Widening exceeds supported width')
    n=len(prefix['steps'])
    if mode=='restart':
        proof,diag=bucket.discover(source,counts,**limits)
        if proof['steps'][:n]!=prefix['steps']:raise ValueError('Restart does not extend the supplied prefix')
        counts['widen_repeated_projection_steps']+=n
    else:
        # Prefix data is only used after independent source-bound validation.
        bucket.check_certificate(source,prefix,counts)
        cnf,names=native.normalize(source,counts);proof=deepcopy(prefix);proof['limits']=limits
        steps=proof['steps'];spent=0;diag=dict(reason='leaf-width',spent=0)
        if not any(len(c)>limits['bag_limit'] for c in cnf):
            factors,active,spent=materialize(cnf,steps,counts)
            if spent>limits['work_limit']:raise ValueError('Prefix exceeds total projection allowance')
            counts['widen_reused_projection_steps']+=n;counts['widen_reused_reserved_work']+=spent
            while True:
                if any(factors[i]['bits']==0 for i in active):proof['status']='unsat';diag=dict(reason='complete',spent=spent);break
                variables=sorted({v for i in active for v in factors[i]['scope']})
                if not variables:proof['status']='sat';diag=dict(reason='complete',spent=spent);break
                candidates=[]
                for v in variables:
                    ids=sorted(i for i in active if v in factors[i]['scope']);bag={x for i in ids for x in factors[i]['scope']}
                    counts['bucket_planning_scope_visits']+=sum(len(factors[i]['scope']) for i in ids);candidates.append((len(bag),len(ids),v,ids))
                width,_,variable,ids=min(candidates)
                if width>limits['bag_limit']:diag=dict(reason='bag-width',width=width,spent=spent);break
                inputs=[factors[i] for i in ids];cost=(1<<width)*len(ids)
                if spent+cost>limits['work_limit']:diag=dict(reason='row-work',spent=spent,next_cost=cost);break
                spent+=cost;counts['bucket_reserved_probe_work']+=cost
                boundary,bits,choices=bucket.project(inputs,variable,counts);scope,bits=bucket.reduce_support(boundary,bits,counts)
                steps.append(dict(variable=variable,inputs=ids,scope=scope,bits=bits,choices=choices));active.difference_update(ids);active.add(len(factors));factors.append(dict(scope=scope,bits=bits));counts['widen_new_projection_steps']+=1
            if proof['status']=='sat':
                model={v:False for v in range(1,len(names)+1)}
                for step in reversed(steps):
                    boundary=sorted({v for i in step['inputs'] for v in factors[i]['scope']}-{step['variable']})
                    index=sum(int(model[v])<<i for i,v in enumerate(boundary));model[step['variable']]=bool(step['choices']>>index & 1)
                proof['model']=[model[v] for v in range(1,len(names)+1)]
    # Match the existing restart engine's internal final check.
    if mode=='resume' and proof['status']!='unresolved':bucket.check_certificate(source,proof,counts)
    extension=dict(steps=proof['steps'][n:],status=proof['status'],model=proof['model'])
    got=check(source,prefix,extension,counts)
    return extension,diag,got
