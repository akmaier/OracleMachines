"""Spend a bounded split budget on checked guard regions with shared prefixes.

Uniform assignment mass is a selection heuristic, not a SAT cost model. The
result uses the existing partial-plan checker and native composer unchanged.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import heapq
from experiments.cnf_conditional_unit_support import check_template,fixed_pairs
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_partial_proof_plan import PLAN_FORMAT,check_plan


def guard_census(templates):
    guards=[]
    for template in templates:
        check_template(template);guards.append(frozenset(fixed_pairs(template['assumptions']).items()))
    unique=set(guards);minimal={g for g in unique if not any(h<g for h in unique)}
    adjacent=sum(len(g^h)==2 and len({v for v,b in g^h})==1
        for i,g in enumerate(sorted(minimal,key=lambda x:sorted(x)))
        for h in sorted(minimal,key=lambda x:sorted(x))[i+1:])
    prefixes={()}
    for g in guards:
        ordered=sorted(g)
        prefixes.update(tuple(ordered[:i]) for i in range(1,len(ordered)+1))
    return dict(templates=len(guards),unique_guards=len(unique),minimal_guards=len(minimal),
        dominated_guards=len(unique)-len(minimal),complementary_pairs=adjacent,
        guard_literal_occurrences=sum(map(len,guards)),sorted_prefix_nodes=len(prefixes)-1)


def closed_mass(plan):
    check_plan(plan)
    def walk(node,depth):
        if 'leaf' in node:
            return Fraction(0) if plan['templates'][node['leaf']].get('open') else Fraction(1,2**depth)
        return walk(node['low'],depth+1)+walk(node['high'],depth+1)
    return walk(plan['tree'],0)


def make_frontier_plan(target,templates,*,node_limit=129,counts=None):
    """Greedily cover an open region, then reuse its partial guard prefixes.

    Each offer closes one guard cube in an open region. Its exact uniform mass
    per added split determines priority. Sibling regions remain open and may
    receive other compatible templates. Caps reduce coverage, never authority.
    """
    if type(node_limit) is not int or not 1<=node_limit<=129:
        raise ValueError('Plan node limit must be between 1 and 129')
    c=Counter() if counts is None else counts
    templates=deepcopy(templates);members=clause_set(target,c);guards=[];eligible=[]
    for i,t in enumerate(templates):
        support=check_template(t,c);guards.append(fixed_pairs(t['assumptions']))
        c['frontier_support_clauses']+=len(support)
        if support<=members:eligible.append(i)
        else:c['frontier_invalidated_templates']+=1
    used=[];ids={};heap=[];serial=0;remaining=(node_limit-1)//2
    def close(node,index):
        if index not in ids:ids[index]=len(used);used.append(templates[index])
        node.clear();node['leaf']=ids[index];c['frontier_closed_leaves']+=1
    def offer(node,context,choices):
        nonlocal serial
        candidates=[]
        for i in choices:
            c['frontier_candidate_checks']+=1
            c['frontier_guard_pair_checks']+=len(guards[i])
            if any(v in context and context[v]!=b for v,b in guards[i].items()):continue
            rest=tuple(sorted((v,b) for v,b in guards[i].items() if v not in context))
            if not rest:close(node,i);return
            candidates.append((i,rest))
        if not candidates:return
        choices=[i for i,rest in candidates]
        # Within one region, shortest guards maximize mass per split. Choose
        # the cheaper source support on equal guard lengths; retain raw bank.
        index,rest=min(candidates,key=lambda p:(len(p[1]),sum(map(len,templates[p[0]]['clauses'])),p[0]))
        score=Fraction(1,(1<<(len(context)+len(rest)))*len(rest))
        heapq.heappush(heap,(-score,serial,node,context,choices,index,rest));serial+=1
        c['frontier_offers']+=1;c['frontier_heap_peak']=max(c['frontier_heap_peak'],len(heap))
    tree={};offer(tree,{},eligible)
    while heap:
        _,_,node,context,choices,index,rest=heapq.heappop(heap)
        if len(rest)>remaining:
            c['frontier_budget_skips']+=1;continue
        remaining-=len(rest);c['frontier_splits']+=len(rest)
        # Construct the entire chosen cube before scheduling siblings. Nodes
        # and contexts stay private until the existing checker accepts them.
        siblings=[]
        for variable,value in rest:
            low={};high={};node.update(variable=variable,low=low,high=high)
            siblings.append((low if value else high,{**context,variable:not value}))
            node=high if value else low;context={**context,variable:value}
        close(node,index)
        for sibling,ctx in siblings:offer(sibling,ctx,choices)
    open_index=None
    def fill(node):
        nonlocal open_index
        if not node:
            if open_index is None:open_index=len(used);used.append(dict(open=True,clauses=[]))
            node['leaf']=open_index;c['frontier_open_leaves']+=1
        elif 'variable' in node:fill(node['low']);fill(node['high'])
    fill(tree)
    plan=dict(format=PLAN_FORMAT,tree=tree,templates=used)
    check_plan(plan,c,node_limit=node_limit)
    return plan
