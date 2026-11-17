"""Stop partition discovery when the unsplit target already has a unit conflict.

This preserves the frozen nonterminal policy and still charges prepared-index
setup, initial propagation and native proof verification. No minimum-cost claim.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_premise_guard import PremiseGuardSelector
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_clause_partition import branch_sources
from experiments.cnf_partition_screen import screen_branch,publish_screened_branch


class TerminalFirstScreen:
    def __init__(self,cores,plan_limit=4,core_read_limit=8,max_missing=3):
        if type(plan_limit) is not int or plan_limit<0 or type(core_read_limit) is not int or core_read_limit<0 or max_missing!=3:raise ValueError('Invalid screening bounds')
        self.index=PremiseGuardSelector(cores);self.counts=Counter(self.index.counts)
        self.plan_limit=plan_limit;self.core_read_limit=core_read_limit;self.max_missing=max_missing

    def select(self,solver,target):
        self.counts['screen_calls']+=1;trace=dict(attempts=[],selected=None,core_checks=[])
        if not self.plan_limit or not self.core_read_limit:return None,trace
        baseline=screen_branch(solver,target,self.counts);trace['baseline']=baseline;self.counts['screen_baseline_probes']+=1
        trace['terminal']=baseline['conflict'] is not None
        if trace['terminal']:
            self.counts['screen_terminal_targets']+=1
            return None,trace
        members=clause_set(target,self.counts);variables={abs(l) for c in members for l in c};hits=Counter()
        for clause in members:
            ids=self.index.postings.get(clause,());hits.update(ids);self.counts['screen_posting_visits']+=len(ids)
        candidates=sorted((len(self.index.members[i])-n,i) for i,n in hits.items() if 2<=len(self.index.members[i])-n<=self.max_missing)
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
