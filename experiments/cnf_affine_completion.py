"""Complete a small checked affine solution space against all leftover clauses.

Reuse the existing exact extraction and basis checkers. Gray-code traversal
changes one basis direction per candidate; packed leftover clauses are built
once. Only a full-source checked positive model changes native acquisition.
Negative evidence and budget misses retain the previous fallback.
"""
from collections import Counter
from experiments.cnf_cover_probe import select as previous_select
from experiments.cnf_affine_patterns import extract_affine, check_affine
from experiments.cnf_affine_clause import make_space, check_space
from experiments.cnf_residual_dag import holds


def complete(solver, source, counts=None, free_limit=8):
    if type(free_limit) is not int or not 0<=free_limit<=16:
        raise ValueError('Expected an integer free-coordinate limit between 0 and 16')
    counts=Counter() if counts is None else counts
    cnf,names,root=solver._canonical(source);n=len(names)
    counts['affine_bridge_calls']+=1
    affine=extract_affine(cnf,counts);summary=check_affine(cnf,affine,counts)
    d=n-summary['rank']
    record=dict(root=root,variables=n,free_limit=free_limit,free=d,affine=affine,
                summary=summary,status=None,space=None,rejected=[],accepted=None)
    if not summary['equation_count']:
        record['status']='no-equations';counts['affine_bridge_no_equations']+=1
        return None,record
    if summary['inconsistent']:
        record['status']='linear-conflict';counts['affine_bridge_linear_conflicts']+=1
        return None,record
    if d>free_limit:
        record['status']='free-cap';counts['affine_bridge_free_caps']+=1
        return None,record
    space=make_space(n,affine,counts);check_space(n,affine,space,counts);record['space']=space
    packed=[]
    for cid in affine['leftovers']:
        positive=negative=0
        for literal in cnf[cid]:
            counts['affine_bridge_packed_literals']+=1
            if literal>0:positive|=1<<(literal-1)
            else:negative|=1<<(-literal-1)
        packed.append((cid,positive,negative))
    candidate=space['particular']
    for index in range(1<<d):
        if index:
            direction=(index & -index).bit_length()-1
            candidate^=space['directions'][direction]
            counts['affine_bridge_basis_xors']+=1
        counts['affine_bridge_candidates']+=1
        failed=None
        for cid,positive,negative in packed:
            counts['affine_bridge_clause_checks']+=1
            if not (candidate & positive or ~candidate & negative):
                failed=cid;break
        if failed is not None:
            record['rejected'].append(failed)
            continue
        model={name:bool(candidate & (1<<i)) for i,name in enumerate(names)}
        counts['affine_bridge_model_variables']+=n
        counts['affine_bridge_model_literals']+=sum(map(len,source))
        if not holds(source,model):
            raise ValueError('Affine completion fails the full raw source')
        record['status']='model';record['accepted']=dict(index=index,mask=candidate)
        counts['affine_bridge_models']+=1
        return dict(kind='positive-model',root=root,model=[[v,model[v]] for v in names]),record
    record['status']='space-exhausted';counts['affine_bridge_exhausted']+=1
    return None,record


def select(solver, source, variable_limit=4, counts=None):
    counts=Counter() if counts is None else counts
    choice,trace=previous_select(solver,source,variable_limit,counts)
    if trace['discovery'] is None or (choice is not None and choice['kind']!='fallback-trace'):
        return choice,trace
    recovered,evidence=complete(solver,source,counts)
    trace['affine_bridge']=evidence
    if recovered is None:return choice,trace
    if choice is not None:
        counts['fallback_trace_reuses']-=1
        counts['fallback_forced_variables']-=len(trace['discovery']['fixed'])
    trace['affine_previous_reason']=trace['reason'];trace['reason']='affine-positive-model'
    return recovered,trace
