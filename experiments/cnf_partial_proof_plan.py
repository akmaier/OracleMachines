"""Retain checked conditional leaves when proof extraction has an open frontier.

An open leaf has no proof authority. The existing native partial composer solves
it under its actual target context, preserving one shared expansion budget.
The composer adapter requires exclusive synchronous use, like its source API.
"""
from collections import Counter
from unittest.mock import patch
from experiments.cnf_carried_origins import OriginIndex
from experiments.cnf_conditional_unit_support import FORMAT_HINT,check_template,fixed_pairs
from experiments.cnf_residual_dag import restrict
from experiments.cnf_clause_deletion_guard import clause_set
from experiments import cnf_leaf_handoff as composer

PLAN_FORMAT='partial-proof-plan-v1'

def extract_partial(solver,source,*,node_limit=64,literal_limit=65536):
    if any(type(v) is not int or v<1 for v in (node_limit,literal_limit)):raise ValueError('Invalid extraction limits')
    source=tuple(tuple(cl) for cl in source)
    counts=Counter();root,names,key=solver._canonical(source);start=solver._read(key,root,purpose='conditional_origin')
    if start is None or start['answer'] is not False:raise ValueError('Checked negative origin required')
    entries=[]
    index = None
    def external(l):return (1 if l>0 else -1)*names[abs(l)-1]
    def leaf(conflict,trace,guards,path,origin):
        needed={abs(l) for l in root[conflict]};kept=[]
        for lit,cid in reversed(trace):
            counts['conditional_slice_steps']+=1
            if abs(lit) not in needed:continue
            needed.remove(abs(lit));needed.update(abs(l) for l in root[cid] if l!=lit);kept.append((lit,cid))
        if not needed<=guards.keys():raise ValueError('Unclosed conditional dependency')
        kept.reverse();selected=sorted({conflict}|{cid for _,cid in kept})
        clauses=sorted(tuple(sorted(external(l) for l in root[cid])) for cid in selected);positions={cl:i for i,cl in enumerate(clauses)}
        local={cid:positions[tuple(sorted(external(l) for l in root[cid]))] for cid in selected}
        template=dict(clauses=[list(cl) for cl in clauses],assumptions=[[names[v-1],guards[v]] for v in sorted(needed)],
            trace=[[external(l),local[cid]] for l,cid in kept],conflict=local[conflict])
        check_template(template,counts);index=len(entries)
        entries.append(dict(template=template,leaf=origin,origin_canonical_indices=selected,path_assignment=[[names[v-1],b] for v,b in sorted(path.items())]))
        return dict(leaf=index)
    def hole(nodekey,reason,guards):
        counts['partial_plan_open_leaves']+=1
        counts['partial_plan_open_'+reason]+=1
        slot=len(entries)
        entries.append(dict(template=dict(open=True,clauses=[]),leaf=nodekey,reason=reason,
            path_assignment=[[names[v-1],b] for v,b in sorted(guards.items())]))
        return dict(leaf=slot)
    def walk(nodekey,mapping,fixed,guards,trace,state):
        nonlocal index
        if counts['conditional_node_visits']>=node_limit:return hole(nodekey,'node_budget',guards)
        node=solver._read(nodekey,purpose='conditional_path')
        if node is None or node['answer'] is not False:raise ValueError('Missing negative path node')
        cnf=tuple(map(tuple,node['cnf']));size=sum(map(len,cnf))
        if counts['conditional_node_literals']+size>literal_limit:return hole(nodekey,'literal_budget',guards)
        counts['conditional_node_visits']+=1;counts['conditional_node_literals']+=size
        proof=node['proof'];kind=proof['kind']
        if kind not in ('empty','units','split','component'):
            counts['conditional_unsupported_endpoints']+=1;return hole(nodekey,kind,guards)
        if state is None:
            index = OriginIndex(root, counts)
            state = index.initial
        # This global map includes clauses outside a selected component.
        # It has exactly the old full-source scan's minimum original indices.
        origins = state.by_clause
        def literal(l):return (1 if l>0 else -1)*mapping[abs(l)]
        root_ids=[origins[tuple(sorted(literal(l) for l in cl))] for cl in cnf]
        def descend(child,assignment,newguards,newtrace,subset=None):
            raw=restrict(cnf if subset is None else subset,assignment,counts)
            normalized,oldnames,actual=solver._canonical(raw)
            if actual!=child:raise ValueError('Wrong conditioned child')
            mapped={i+1:mapping[v] for i,v in enumerate(oldnames)}
            updated={**fixed,**{mapping[v]:b for v,b in assignment.items()}}
            delta = {mapping[v]: bit for v, bit in assignment.items()}
            child_state = index.advance(state, delta)
            try:
                return walk(child,mapped,updated,newguards,newtrace,child_state)
            finally:
                index.release(state, child_state)
        if kind=='empty':return leaf(root_ids[cnf.index(())],trace,guards,guards,nodekey)
        if kind=='units':
            more=trace+[(literal(l),root_ids[cid]) for l,cid in proof['trace']]
            if proof.get('conflict') is not None:return leaf(root_ids[proof['conflict']],more,guards,guards,nodekey)
            return descend(proof['child'],{abs(l):l>0 for l,_ in proof['trace']},guards,more)
        if kind=='component':return descend(proof['child'],{},guards,trace,tuple(cnf[i] for i in proof['clauses']))
        variable=proof['variable'];rawvar=mapping[variable]
        if rawvar in fixed:raise ValueError('Repeated path variable')
        children={}
        for bit,field in ((False,'low'),(True,'high')):
            children[field]=descend(proof[field],{variable:bit},{**guards,rawvar:bit},trace)
        return dict(variable=names[rawvar-1],**children)
    tree=walk(key,dict(enumerate(range(1,len(names)+1),1)),{}, {},[], None)
    return dict(format=FORMAT_HINT,source=[list(cl) for cl in source],origin=key,entries=entries,tree=tree),dict(counts)


def make_plan(bundle):
    return dict(format=PLAN_FORMAT,tree=bundle['tree'],templates=[e['template'] for e in bundle['entries']])


def check_plan(plan,counts=None,node_limit=129):
    c=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<1:raise ValueError('Invalid plan bound')
    if type(plan) is not dict or set(plan)!={'format','tree','templates'} or plan['format']!=PLAN_FORMAT:
        raise ValueError('Invalid partial proof plan')
    ts=plan['templates']
    if type(ts) is not list or not 1<=len(ts)<=node_limit:raise ValueError('Invalid plan leaves')
    for t in ts:
        if type(t) is dict and t.get('open') is True:
            if set(t)!={'open','clauses'} or t['clauses']!=[]:raise ValueError('Open leaf is not a certificate')
        else:check_template(t,c)
    visited=0;leaves=set()
    def walk(node,fixed):
        nonlocal visited
        visited+=1
        if visited>node_limit or type(node) is not dict:raise ValueError('Oversized or invalid plan tree')
        if set(node)=={'leaf'}:
            i=node['leaf']
            if type(i) is not int or not 0<=i<len(ts):raise ValueError('Invalid plan leaf')
            if ts[i].get('open') is not True:
                if any(fixed.get(v)!=bit for v,bit in fixed_pairs(ts[i]['assumptions']).items()):
                    raise ValueError('Plan path does not imply support assumptions')
            leaves.add(i)
        elif set(node)=={'variable','low','high'}:
            v=node['variable']
            if type(v) is not int or v<=0 or v in fixed:raise ValueError('Invalid plan split')
            walk(node['low'],{**fixed,v:False});walk(node['high'],{**fixed,v:True})
        else:raise ValueError('Incomplete plan tree')
    walk(plan['tree'],{})
    if leaves!=set(range(len(ts))):raise ValueError('Unused plan leaves')
    c['partial_plan_checked_tree_nodes']+=visited


def survival(target,plan,counts):
    check_plan(plan,counts);members=clause_set(target,counts)
    return [False if t.get('open') is True else check_template(t,counts)<=members for t in plan['templates']]


def recompose(solver,target,plan,budget,counts=None):
    # A plan marker retains a zero-length clauses field for the composer's
    # payload accounting, but never passes as a template or an intact leaf.
    # The untouched composer independently verifies every resulting native node.
    with patch.object(composer,'survival',survival):
        return composer.recompose(solver,target,plan,budget,counts=counts)
