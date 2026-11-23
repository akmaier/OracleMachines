"""Use one missing clause of a guarded unit refutation as checked guidance.

If K AND C is false under a and K is contained in G, every model of G under a
falsifies C. Solve that restriction; compile all excluded alternatives using the
unit template. All conclusions are ordinary native proofs or checked witnesses.
"""
from collections import Counter
import time
from experiments.cnf_conditional_unit_support import check_template,fixed_pairs,materialize
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import restrict,holds,FORMAT
from experiments.cnf_probed_partition import acquire


def proposal(source,template,context,counts=None,*,max_width=3):
    c=Counter() if counts is None else counts
    if type(max_width) is not int or max_width<1:raise ValueError('Invalid width limit')
    wanted=check_template(template,c);fixed=fixed_pairs(context);assumptions=fixed_pairs(template['assumptions'])
    if any(fixed.get(v)!=b for v,b in assumptions.items()):raise ValueError('Context must extend template assumptions')
    members=clause_set(source,c);missing=sorted(wanted-members);c['recovery_membership_clauses']+=len(wanted)
    if len(missing)!=1:return None
    residual=restrict(missing,fixed,c)
    if not residual or not residual[0] or len(residual[0])>max_width:return None
    live_variables={abs(l) for cl in restrict(source,fixed,c) for l in cl}
    if not {abs(l) for l in residual[0]}<=live_variables:return None
    return dict(missing=list(missing[0]),forced=[[abs(l),l<0] for l in residual[0]])


def recover(solver,source,template,context,screen,budget,counts=None):
    """Return None if guidance adds no value; an acquisition stop stays unknown.

    The supplied screen is checked against the full target before any solving.
    Native unit propagation is retained, followed by at most three new forced
    variables. Cold replay needs no new proof rule or hint authority.
    """
    began=time.perf_counter();c=Counter() if counts is None else counts
    if type(budget) is not int or budget<0:raise ValueError('Invalid native budget')
    source=tuple(tuple(cl) for cl in source);context=fixed_pairs(context)
    plan=proposal(source,template,[[v,b] for v,b in context.items()],c)
    if plan is None:return None
    target=restrict(source,context,c);cnf,names,key=solver._canonical(target)
    if screen['root']!=key or screen['conflict'] is not None:raise ValueError('Expected nonconflicting bound screen')
    local={};trace=screen['trace']
    for step in trace:
        if type(step) is not list or len(step)!=2:raise ValueError('Invalid retained step')
        l,i=step
        if type(l) is not int or not l or type(i) is not int or not 0<=i<len(cnf) or abs(l) in local:raise ValueError('Invalid retained reason')
        cl=cnf[i];c['recovery_trace_check_literals']+=len(cl)
        if l not in cl or any(abs(x) not in local or local[abs(x)]==(x>0) for x in cl if x!=l):raise ValueError('Unforced retained step')
        local[abs(l)]=l>0
    fixed={**context,**{names[v-1]:b for v,b in local.items()}}
    forced=[]
    for v,b in plan['forced']:
        if v in fixed:
            if fixed[v]!=b:raise ValueError('Screen contradicts forced clause; use native fallback')
        else:forced.append((v,b))
    if not forced:c['recovery_no_new_forces']+=1;return None
    c['recovery_new_forces']+=len(forced);live_fixed={**fixed,**dict(forced)}
    before=dict(solver.counts);child=acquire(solver,restrict(source,live_fixed,c),budget,retain_stop=True)
    acquisition=dict(solver.counts);solver.counts=Counter(before);solver.counts.update(acquisition)
    report=dict(plan=plan,forced=[[v,b] for v,b in forced],child=child,result=None,status=child['status'],excluded=[])
    if child['result'] is None:
        report['seconds']=time.perf_counter()-began;return report
    if child['result']['answer']:
        model={**live_fixed,**child['result']['model']}
        # Assign vanished variables as false, then check the complete cofactor.
        witness={v:model.get(v,False) for v in names}
        c['recovery_witness_literals']+=sum(map(len,target))
        if not holds(target,witness):raise ValueError('Recovery witness does not satisfy the full target')
        solver._store(key,dict(format=FORMAT,cnf=[list(cl) for cl in cnf],answer=True,model=[witness[v] for v in names]))
    else:
        live=child['result']['root'];stronger=[list(cl) for cl in source]+[plan['missing']]
        for index in reversed(range(len(forced))):
            v,b=forced[index];parent_fixed={**fixed,**dict(forced[:index])}
            parent,oldnames,parent_key=solver._canonical(restrict(source,parent_fixed,c))
            if v not in oldnames:
                if parent_key!=live:raise ValueError('Disappearing variable changed the child identity')
                c['recovery_disappeared_forces']+=1;continue
            excluded=materialize(solver,stronger,template,context=[[w,bit] for w,bit in sorted({**parent_fixed,v:not b}.items())],counts=c)
            # The missing clause is satisfied in the excluded branch and drops.
            expected=solver._canonical(restrict(source,{**parent_fixed,v:not b},c))[2]
            if excluded['root']!=expected:raise ValueError('Excluded branch retained a missing premise')
            report['excluded'].append(excluded['root']);variable=oldnames.index(v)+1
            solver._store(parent_key,dict(format=FORMAT,cnf=[list(cl) for cl in parent],answer=False,
                proof=dict(kind='split',variable=variable,low=excluded['root'] if b else live,high=live if b else excluded['root'])))
            live=parent_key
        if trace:
            solver._store(key,dict(format=FORMAT,cnf=[list(cl) for cl in cnf],answer=False,proof=dict(kind='units',trace=trace,child=live)))
        elif live!=key:raise ValueError('Recovery did not reach the requested root')
    node=solver._read(key,cnf,purpose='recovery_final')
    report['result']=dict(root=key,answer=node['answer'],model=dict(zip(names,node['model'])) if node['answer'] else None)
    report['seconds']=time.perf_counter()-began;return report
