"""Experimental source-checked first-UIP clause learning and backjumping.

This is standard conflict-driven search, not a new tractable SAT class. Every
stored exclusion has an explicit resolution derivation. No learned clause is
trusted across a source edit without checking its premises and claimed result.
"""
from collections import Counter
from experiments import cnf_unit_partition as prior
FORMAT='cnf-resolution-learning-v1'
NODE_LIMIT=20000


def checked_clauses(source, derivations, counts=None):
    counts=Counter() if counts is None else counts
    clauses=list(prior.prior.previous.capacity.canonical(source,counts))
    if type(derivations) is not list:raise ValueError('Invalid derivation list')
    def get(index):
        if type(index) is not int or not 0<=index<len(clauses):raise ValueError('Invalid or forward clause reference')
        counts['resolution_check_literal_charge']+=len(clauses[index]);return set(clauses[index])
    for entry in derivations:
        if type(entry) is not list or len(entry)!=3 or type(entry[1]) is not list or type(entry[2]) is not list:raise ValueError('Invalid resolution record')
        current=get(entry[0])
        for step in entry[1]:
            if type(step) is not list or len(step)!=2 or type(step[0]) is not int or step[0]<=0:raise ValueError('Invalid resolution pivot')
            v=step[0];other=get(step[1]);counts['resolution_check_literal_charge']+=len(current)
            if v in current and -v in other:a,b=v,-v
            elif -v in current and v in other:a,b=-v,v
            else:raise ValueError('Missing complementary pivot')
            current=(current-{a})|(other-{b})
            if any(-lit in current for lit in current):raise ValueError('Tautological claimed exclusion')
            counts['resolution_steps_checked']+=1
        claimed=entry[2]
        if any(type(v) is not int or not v for v in claimed) or claimed!=sorted(current):raise ValueError('Changed learned clause')
        clauses.append(tuple(claimed));counts['resolution_lemmas_checked']+=1
    return clauses


def check_result(source, proof, counts=None):
    counts=Counter() if counts is None else counts
    if type(proof) is not dict or set(proof)!={'format','kind','witness','derivations','conclusion'} or proof['format']!=FORMAT:raise ValueError('Invalid learning certificate')
    clauses=checked_clauses(source,proof['derivations'],counts)
    if proof['kind']=='sat' and proof['conclusion'] is None:return prior.prior.previous.check(source,proof['witness'],counts)
    if proof['kind']=='unsat' and proof['witness'] is None:
        i=proof['conclusion']
        if type(i) is not int or not 0<=i<len(clauses) or clauses[i]:raise ValueError('Missing empty-clause conclusion')
        return dict(answer=False,model=None)
    if proof['kind']=='unknown' and proof['witness'] is None and proof['conclusion'] is None:return dict(answer=None,model=None)
    raise ValueError('Invalid learning verdict')


def search(source, seed, counts=None, *, node_limit=NODE_LIMIT):
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0:raise ValueError('Invalid learning budget')
    initial,names,model=prior.prior.prepare(source,seed,0,counts);base=len(initial);seed_model=dict(model)
    clauses=[];occurrence={v:[] for v in names};satisfied=[];free_count=[];fixed_true=[];bad=set();agenda=set();lookup={}
    fixed={};reason={};level={};position={};trail=[];limits=[];derivations=[];expanded=0;max_fixed=0

    def refresh(i):
        if not fixed_true[i] and free_count[i]<=1:agenda.add(i)
        else:agenda.discard(i)
        if satisfied[i]:bad.discard(i)
        else:bad.add(i)

    def add(c):
        i=len(clauses);clauses.append(c);lookup[c]=i
        satisfied.append(sum(model[abs(v)]==(v>0) for v in c));free_count.append(sum(abs(v) not in fixed for v in c));fixed_true.append(sum(abs(v) in fixed and fixed[abs(v)]==(v>0) for v in c))
        for lit in c:occurrence[abs(lit)].append((i,lit>0));counts['learning_index_occurrences']+=1
        refresh(i);return i

    for c in initial:add(c)
    initial_failed=best_failed=len(bad)
    activity={v:0.0 for v in names};increment=1.0;phase=dict(seed_model)

    def assign(v,value,premise):
        assert v not in fixed
        phase[v]=value;fixed[v]=value;reason[v]=premise;level[v]=len(limits);position[v]=len(trail);trail.append(v);model[v]=value
        flipped=value!=seed_model[v]
        for i,positive in occurrence[v]:
            counts['learning_assignment_occurrences']+=1;free_count[i]-=1;fixed_true[i]+=value==positive
            if flipped:satisfied[i]+=1 if value==positive else -1
            refresh(i)

    def backtrack(target):
        mark=limits[target]
        while len(trail)>mark:
            v=trail.pop();value=fixed.pop(v);flipped=value!=seed_model[v];del reason[v],level[v],position[v];model[v]=seed_model[v]
            for i,positive in occurrence[v]:
                counts['learning_undo_occurrences']+=1;free_count[i]+=1;fixed_true[i]-=value==positive
                if flipped:satisfied[i]+=-1 if value==positive else 1
                refresh(i)
        del limits[target:]

    def finish(kind,conclusion=None):
        witness=dict(format=prior.prior.previous.FORMAT,names=names,values=[model[v] for v in names]) if kind=='sat' else None
        proof=dict(format=FORMAT,kind=kind,witness=witness,derivations=derivations,conclusion=conclusion)
        check_result(source,proof,counts)
        return proof,dict(reason=kind,node_limit=node_limit,expanded=expanded,initial_failed=initial_failed,best_failed=best_failed,maximum_committed=max_fixed,learned=len(derivations),learned_literals=sum(len(x[2]) for x in derivations))

    while expanded<node_limit:
        expanded+=1;counts['learning_contexts']+=1;conflict=None
        while agenda:
            counts['learning_agenda_candidates']+=len(agenda);i=min(agenda);counts['learning_agenda_selections']+=1
            if not free_count[i]:conflict=i;break
            counts['learning_unit_literal_charge']+=len(clauses[i]);lit=next(v for v in clauses[i] if abs(v) not in fixed)
            assign(abs(lit),lit>0,i);counts['learning_propagations']+=1
            if i>=base:counts['learned_clause_propagations']+=1
        # Compare false-clause counts only on the unchanged original source.
        counts['learning_failed_scan']+=len(bad);best_failed=min(best_failed,sum(i<base for i in bad));max_fixed=max(max_fixed,len(fixed))
        if conflict is not None:
            counts['learning_conflicts']+=1
            if conflict>=base:counts['learned_clause_conflicts']+=1
            current=set(clauses[conflict]);steps=[];dl=len(limits)
            while True:
                counts['learning_analysis_literal_charge']+=len(current)
                for lit in current:activity[abs(lit)]+=increment;counts['learning_activity_bumps']+=1
                at=[abs(lit) for lit in current if level[abs(lit)]==dl]
                if (dl and len(at)==1) or (not dl and not current):break
                assert at
                v=max(at,key=lambda v:position[v]);rid=reason[v];assert rid is not None
                other=set(clauses[rid]);counts['learning_resolution_literal_charge']+=len(current)+len(other)
                pivot=v if v in current else -v;assert -pivot in other
                current=(current-{pivot})|(other-{-pivot});assert not any(-lit in current for lit in current)
                steps.append([v,rid]);counts['learning_resolution_steps']+=1
            increment/=0.95
            if increment>1e100:
                for v in names:activity[v]*=1e-100
                increment*=1e-100;counts['learning_activity_rescales']+=1
            learned=tuple(sorted(current))
            if learned in lookup:
                cid=lookup[learned];counts['learning_duplicate_clauses']+=1
            else:
                cid=add(learned);derivations.append([conflict,steps,list(learned)]);counts['learning_new_clauses']+=1
            if not learned:return finish('unsat',cid)
            target=max((level[abs(lit)] for lit in learned if level[abs(lit)]<dl),default=0)
            if target<dl-1:counts['learning_nonchronological_jumps']+=1
            counts['learning_levels_removed']+=dl-target;backtrack(target)
            assert cid in agenda
            continue
        if not bad:return finish('sat')
        choices=[]
        for i in sorted(bad):
            counts['learning_false_literal_charge']+=len(clauses[i]);available=tuple(sorted(abs(v) for v in clauses[i] if abs(v) not in fixed));choices.append((len(available),available,i))
        choices.sort();assert choices[0][0]>=2
        def gain(v):
            score=0
            for i,positive in occurrence[v]:
                counts['learning_gain_occurrences']+=1
                score+=(satisfied[i]==0) if model[v]!=positive else -(satisfied[i]==1)
            return score
        counts['learning_activity_candidates']+=len(names)
        eligible=[v for v in names if v not in fixed];active=min(eligible,key=lambda v:(-activity[v],v))
        v=active if activity[active]>0 else min(choices[0][1],key=lambda v:(-gain(v),v))
        limits.append(len(trail));assign(v,phase[v],None);counts['learning_decisions']+=1
    return finish('unknown')


def solve(source, counts=None, *, node_limit=NODE_LIMIT):
    counts=Counter() if counts is None else counts
    return search(source,prior.prior.proposal(source,counts),counts,node_limit=node_limit)


def transport_knowledge(source, proof, target, counts=None):
    """Reuse checked clauses only under exact retained-source-premise guards.

    Clause indices may change and unused source clauses may disappear. SAT
    authority is never transported; nonnegative knowledge returns unknown.
    """
    counts=Counter() if counts is None else counts
    check_result(source,proof,counts)
    old=list(prior.prior.previous.capacity.canonical(source,counts));new=list(prior.prior.previous.capacity.canonical(target,counts));where={c:i for i,c in enumerate(new)}
    guards={};n=len(old);m=len(new)
    def ref(index):
        if index>=n:return m+index-n
        if index in guards:
            counts['knowledge_guard_hits']+=1;return guards[index]
        counts['knowledge_guard_literal_charge']+=len(old[index])
        if old[index] not in where:raise ValueError('Missing source premise for knowledge reuse')
        guards[index]=where[old[index]];return guards[index]
    records=[]
    for start,steps,clause in proof['derivations']:
        records.append([ref(start),[[v,ref(parent)] for v,parent in steps],clause[:]])
    negative=proof['kind']=='unsat'
    moved=dict(format=FORMAT,kind='unsat' if negative else 'unknown',witness=None,derivations=records,conclusion=ref(proof['conclusion']) if negative else None)
    check_result(target,moved,counts);counts['knowledge_distinct_source_guards']+=len(guards)
    return moved
