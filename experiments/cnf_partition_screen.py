"""Bounded multi-clause plan screening and reuse of checked unit traces.

The gate is a heuristic: all branches close by unit conflict, or at least two
close and one residual is smaller after propagation. No optimal-cost guarantee.
"""
from collections import Counter
from copy import deepcopy
import time
from experiments.cnf_premise_guard import PremiseGuardSelector
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_clause_partition import branch_sources,publish_premise
from experiments.cnf_residual_dag import propagate,restrict,holds,FORMAT


def screen_branch(solver,source,counts):
    cnf,_,root=solver._canonical(source);fixed,trace,conflict=propagate(cnf,counts)
    residual=() if conflict is not None else restrict(cnf,fixed,counts)
    return dict(root=root,trace=trace,conflict=conflict,residual_literals=sum(map(len,residual)))


class PartitionScreen:
    def __init__(self,cores,plan_limit=4,core_read_limit=8,max_missing=3):
        if type(plan_limit) is not int or plan_limit<0 or type(core_read_limit) is not int or core_read_limit<0 or max_missing!=3:raise ValueError('Invalid screening bounds')
        self.index=PremiseGuardSelector(cores);self.counts=Counter(self.index.counts)
        self.plan_limit=plan_limit;self.core_read_limit=core_read_limit;self.max_missing=max_missing

    def select(self,solver,target):
        self.counts['screen_calls']+=1;trace=dict(attempts=[],selected=None,core_checks=[])
        if not self.plan_limit or not self.core_read_limit:return None,trace
        members=clause_set(target,self.counts);variables={abs(l) for c in members for l in c};hits=Counter()
        for clause in members:
            ids=self.index.postings.get(clause,());hits.update(ids);self.counts['screen_posting_visits']+=len(ids)
        candidates=sorted((len(self.index.members[i])-n,i) for i,n in hits.items() if 2<=len(self.index.members[i])-n<=self.max_missing)
        baseline=screen_branch(solver,target,self.counts);trace['baseline']=baseline;self.counts['screen_baseline_probes']+=1
        best=None;best_score=None;reads=0;plans=0
        for distance,index in candidates:
            missing=[list(c) for c in sorted(self.index.members[index]-members)]
            if any(not c for c in missing) or not {abs(l) for c in missing for l in c}<=variables:continue
            if reads>=self.core_read_limit or plans>=self.plan_limit:break
            core=self.index.cores[index];cnf,_,key=solver._canonical(core['source'])
            if key!=core['root']:raise ValueError('Unbound screening core')
            node=solver._read(key,cnf,purpose='screen_core');reads+=1;self.counts['screen_core_reads']+=1
            trace['core_checks'].append(dict(core=index,ready=node is not None))
            if node is None:continue
            if node['answer'] is not False:raise ValueError('Negative screening core required')
            for order in ('forward','reverse'):
                if plans>=self.plan_limit:break
                ordered=missing if order=='forward' else list(reversed(missing));_,branches=branch_sources(target,ordered,self.counts)
                screens=[screen_branch(solver,child,self.counts) for _,_,child in branches];plans+=1;self.counts['screen_plans']+=1
                closed=sum(x['conflict'] is not None for x in screens);remaining=len(screens)-closed;literals=sum(x['residual_literals'] for x in screens)
                admitted=remaining==0 or (closed>=2 and remaining==1 and literals<baseline['residual_literals'])
                entry=dict(core=index,order=order,missing=ordered,branches=screens,terminal=closed,remaining=remaining,residual_literals=literals,admitted=admitted)
                trace['attempts'].append(entry);score=(remaining,literals,len(screens),index,order)
                if admitted and (best_score is None or score<best_score):best_score=score;best=entry;trace['selected']=len(trace['attempts'])-1
        if best is not None:self.counts['screen_admissions']+=1
        return deepcopy(best),trace


def publish_screened_branch(solver,source,screen):
    """Reuse a forced-unit prefix; the frozen verifier checks every final node."""
    start=time.perf_counter();solver.counts=Counter();cnf,names,key=solver._canonical(source)
    if screen['root']!=key:raise ValueError('Screened branch identity mismatch')
    node=solver._read(key,cnf,purpose='screened_child')
    if node is None:
        fixed={}
        for lit,cid in screen['trace']:
            if type(lit) is not int or not lit or type(cid) is not int or not 0<=cid<len(cnf) or abs(lit) in fixed:raise ValueError('Invalid retained trace')
            clause=cnf[cid];solver.counts['screen_trace_check_literals']+=len(clause)
            if lit not in clause or any(abs(x) not in fixed or fixed[abs(x)]==(x>0) for x in clause if x!=lit):raise ValueError('Unforced retained literal')
            fixed[abs(lit)]=lit>0
        conflict=screen['conflict']
        if conflict is not None or fixed:
            node=dict(format=FORMAT,cnf=[list(c) for c in cnf],answer=False)
            if conflict is not None:node['proof']=dict(kind='units',trace=deepcopy(screen['trace']),conflict=conflict)
            else:
                model,child=solver._visit(restrict(cnf,fixed,solver.counts))
                if model is None:node['proof']=dict(kind='units',trace=deepcopy(screen['trace']),child=child)
                else:
                    model={**fixed,**model};node.update(answer=True,model=[model.get(i,False) for i in range(1,len(names)+1)])
            before=solver.counts['inserted_nodes'];solver._store(key,node);solver.counts['screen_trace_publications']+=solver.counts['inserted_nodes']-before
            solver.counts['screen_traces_reused']+=1
        else:solver._visit(cnf)
        node=solver._read(key,cnf,purpose='screened_result')
    model=dict(zip(names,node['model'])) if node['answer'] else None
    if model is not None and not holds(source,model):raise ValueError('Screened model reconstruction failed')
    if model is not None:solver.counts['source_witness_literal_payload']+=sum(map(len,source))
    n,b=solver.archive_storage()
    return dict(answer=node['answer'],model=model,root=key,metrics=dict(solver.counts),seconds=time.perf_counter()-start,archive_nodes=n,archive_payload_bytes=b)
