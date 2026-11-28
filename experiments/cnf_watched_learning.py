"""Experimental two-watched-literal propagation with unchanged proof checking.

All clauses remain active. Watch movement changes scheduling work only: minimum
actual clause order, complete proposal, activity, decisions and proof format
remain those of cnf_resolution_learning. No production default changes.
"""
from collections import Counter
from experiments import cnf_resolution_learning as baseline
from experiments import cnf_selective_learning as selective
prior=baseline.prior
FORMAT=baseline.FORMAT
NODE_LIMIT=baseline.NODE_LIMIT
check_result=baseline.check_result
canonical=selective.canonical


def search(source, seed, counts=None, *, node_limit=NODE_LIMIT):
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0:raise ValueError('Invalid learning budget')
    initial,names,model=prior.prior.prepare(source,seed,0,counts);base=len(initial);seed_model=dict(model)
    clauses=[];occurrence={v:[] for v in names};satisfied=[];bad=set();agenda=set();lookup={}
    watches=[];watching={lit:[] for v in names for lit in (v,-v)}
    fixed={};reason={};level={};position={};trail=[];limits=[];derivations=[];expanded=0;max_fixed=0

    def false(lit):
        return abs(lit) in fixed and fixed[abs(lit)]!=(lit>0)

    def add(c):
        i=len(clauses);clauses.append(c);lookup[c]=i
        satisfied.append(sum(model[abs(v)]==(v>0) for v in c))
        for lit in c:occurrence[abs(lit)].append((i,lit>0))
        counts['learning_index_occurrences']+=len(c)
        if not satisfied[i]:bad.add(i)
        # Learned clauses are inserted at conflict. Watch the highest levels,
        # including the asserting literal, before the ensuing backjump.
        slots=sorted(range(len(c)),key=lambda j:(-level.get(abs(c[j]),-1),-position.get(abs(c[j]),-1),j))[:2]
        watches.append(slots)
        for slot,j in enumerate(slots):watching[c[j]].append((i,slot))
        counts['watch_initial_literals']+=len(c);counts['watch_initial_links']+=len(slots)
        if len(c)<=1:agenda.add(i)
        return i

    def notify_false(lit):
        pending=watching[lit];j=0
        while j<len(pending):
            i,slot=pending[j];c=clauses[i];ws=watches[i];counts['watch_visits']+=1
            if len(ws)==1:agenda.add(i);j+=1;continue
            other=c[ws[1-slot]]
            if abs(other) in fixed and not false(other):
                counts['watch_satisfied_skips']+=1;j+=1;continue
            replacement=None
            for k,candidate in enumerate(c):
                counts['watch_candidate_literals']+=1
                if k not in ws and not false(candidate):replacement=k;break
            if replacement is None:
                agenda.add(i);j+=1
            else:
                ws[slot]=replacement;pending[j]=pending[-1];pending.pop()
                watching[c[replacement]].append((i,slot));counts['watch_moves']+=1

    for c in initial:add(c)
    initial_failed=best_failed=len(bad)
    activity={v:0.0 for v in names};increment=1.0;phase=dict(seed_model)

    def assign(v,value,premise):
        assert v not in fixed
        phase[v]=value;fixed[v]=value;reason[v]=premise;level[v]=len(limits);position[v]=len(trail);trail.append(v);model[v]=value
        if value!=seed_model[v]:
            counts['watch_model_assignment_occurrences']+=len(occurrence[v])
            for i,positive in occurrence[v]:
                satisfied[i]+=1 if value==positive else -1
                if satisfied[i]:bad.discard(i)
                else:bad.add(i)
        notify_false(-v if value else v)

    def backtrack(target):
        mark=limits[target]
        while len(trail)>mark:
            v=trail.pop();value=fixed.pop(v);del reason[v],level[v],position[v];model[v]=seed_model[v]
            if value!=seed_model[v]:
                counts['watch_model_undo_occurrences']+=len(occurrence[v])
                for i,positive in occurrence[v]:
                    satisfied[i]+=-1 if value==positive else 1
                    if satisfied[i]:bad.discard(i)
                    else:bad.add(i)
        del limits[target:]

    def finish(kind,conclusion=None):
        witness=dict(format=prior.prior.previous.FORMAT,names=names,values=[model[v] for v in names]) if kind=='sat' else None
        proof=dict(format=FORMAT,kind=kind,witness=witness,derivations=derivations,conclusion=conclusion)
        check_result(source,proof,counts)
        return proof,dict(reason=kind,node_limit=node_limit,expanded=expanded,initial_failed=initial_failed,best_failed=best_failed,maximum_committed=max_fixed,learned=len(derivations),learned_literals=sum(len(x[2]) for x in derivations))

    while expanded<node_limit:
        expanded+=1;counts['learning_contexts']+=1;conflict=None
        while agenda:
            counts['watch_agenda_candidates']+=len(agenda);i=min(agenda);agenda.remove(i);counts['watch_agenda_selections']+=1
            # Lazy removal of satisfied/stale entries preserves the minimum
            # actual unit/conflict clause chosen by the reference engine.
            available=[];is_satisfied=False
            for lit in clauses[i]:
                counts['watch_agenda_literals']+=1
                if abs(lit) not in fixed:available.append(lit)
                elif fixed[abs(lit)]==(lit>0):is_satisfied=True;break
            if is_satisfied or len(available)>1:
                counts['watch_stale_candidates']+=1;continue
            if not available:conflict=i;break
            lit=available[0]
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
            agenda.add(cid)
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



def expand(target, knowledge, counts=None, *, node_limit=NODE_LIMIT):
    """Search an equivalent augmented CNF; substitute checked premises back."""
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0:raise ValueError('Invalid expansion budget')
    got=check_result(target,knowledge,counts)
    if got['answer'] is False:
        return knowledge,dict(reason='retained-refutation',expanded=0,node_limit=node_limit,reused=len(knowledge['derivations']))
    base=canonical(target,counts);records=[[a,[[v,p] for v,p in steps],c[:]] for a,steps,c in knowledge['derivations']]
    where={c:i for i,c in enumerate(base)}
    for i,record in enumerate(records):where.setdefault(tuple(record[2]),len(base)+i)
    augmented=[list(c) for c in target]+[r[2][:] for r in records]
    counts['selective_augmented_literals']+=sum(len(c) for c in augmented)
    inputs=canonical(augmented,counts);mapping=[where[c] for c in inputs]
    # Keep the ordinary target proposal fixed. Learned constraints affect search,
    # not the proposal policy; their variables occur in retained target premises.
    seed=baseline.prior.prior.proposal(target,counts)
    discovered,diag=search(augmented,seed,counts,node_limit=node_limit)
    for start,steps,clause in discovered['derivations']:
        counts['selective_composition_edges']+=1+len(steps)
        mapping.append(len(base)+len(records))
        records.append([mapping[start],[[v,mapping[parent]] for v,parent in steps],clause[:]])
    result=dict(format=FORMAT,kind=discovered['kind'],witness=discovered['witness'],derivations=records,conclusion=mapping[discovered['conclusion']] if discovered['conclusion'] is not None else None)
    check_result(target,result,counts)
    return result,dict(diag,reused=len(knowledge['derivations']))


def solve(source, proof, target, counts=None, *, node_limit=NODE_LIMIT):
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0:raise ValueError('Invalid expansion budget')
    knowledge,survival=selective.transport(source,proof,target,counts)
    result,diag=expand(target,knowledge,counts,node_limit=node_limit)
    return result,dict(survival=survival,expansion=diag)
