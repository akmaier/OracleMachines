"""Share immutable first-false branch preparation, never answer authority.

This acquisition path has no guards. Independent sidecar checking reconstructs
all branches and rechecks native prerequisites using the existing checker.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import sys,time
from experiments.cnf_clause_deletion_guard import clause_set,lift
from experiments.cnf_clause_partition import FORMAT,check_record
from experiments.cnf_residual_dag import restrict
from experiments.cnf_unsat_support import checked_subset
from experiments.cnf_probed_partition import acquire
from experiments.cnf_transported_partition import target_source,prepare_support
from experiments.cnf_support_plan import CausalPlan,PlanBudget,SupportBudget


@dataclass(frozen=True,slots=True)
class Preparation:
    source:tuple
    missing:tuple
    ordered:tuple
    members:frozenset
    branches:tuple


def prepare(source,missing,counts):
    if type(missing) is not list or not missing:raise ValueError('Nonempty ordered missing clauses required')
    raw=tuple(tuple(c) for c in source);extra_raw=tuple(tuple(c) for c in missing)
    members=clause_set(raw,counts);extra=clause_set(extra_raw,counts)
    variables={abs(l) for c in members for l in c}
    if len(extra)!=len(missing) or extra&members or any(not c for c in extra):raise ValueError('Missing clauses must be distinct, nonempty and absent')
    if not {abs(l) for c in extra for l in c}<=variables:raise ValueError('Missing variables outside target')
    ordered=tuple(next(iter(clause_set([c],counts))) for c in extra_raw)
    prefix=raw;branches=[]
    for clause in ordered:
        fixed=tuple((abs(l),l<0) for l in clause)
        child=restrict(prefix,dict(fixed),counts)
        branches.append((prefix,fixed,child));prefix=prefix+(clause,)
    result=Preparation(raw,extra_raw,ordered,frozenset(members),tuple(branches))
    counts['partition_prepared_builds']+=1;counts['partition_branches_built']+=len(branches)
    counts['partition_prepared_source_literals']+=sum(map(len,raw))
    counts['partition_prepared_prefix_references']+=sum(len(b[0]) for b in branches)
    counts['partition_prepared_child_literals']+=sum(sum(map(len,b[2])) for b in branches)
    # Conservative retained graph size. Shared clauses/integers are deliberately
    # charged at every occurrence; no hash table or cache lookup is introduced.
    integer_bytes=sys.getsizeof(max(variables,default=0))
    counts['partition_prepared_sizing_variables']+=len(variables)
    def cnf_size(cnf):
        return sys.getsizeof(cnf)+sum(sys.getsizeof(c)+len(c)*integer_bytes for c in cnf)
    charge=(sys.getsizeof(result)+cnf_size(raw)+cnf_size(extra_raw)+cnf_size(ordered)
        +cnf_size(result.members)+sys.getsizeof(result.branches)
        +sum(sys.getsizeof(b)+cnf_size(b[0])+cnf_size(b[2])+sys.getsizeof(b[1])
             +sum(sys.getsizeof(pair)+sum(map(sys.getsizeof,pair)) for pair in b[1]) for b in branches))
    counts['partition_prepared_charge']=max(counts['partition_prepared_charge'],charge)
    return result


def publish_prepared(solver,prepared,core,counts):
    wanted=clause_set(core['source'],counts)
    if not wanted&prepared.members or wanted-prepared.members!=set(prepared.ordered):raise ValueError('Unbound missing-clause core')
    stronger=prepared.source+prepared.ordered;cnf,_,root=solver._canonical(stronger)
    node=solver._read(root,cnf,purpose='partition_premise')
    if node is not None:
        if node['answer'] is not False:raise ValueError('Negative strengthened premise required')
        return False,root
    _,_,key=solver._canonical(core['source'])
    if key!=core['root']:raise ValueError('Wrong core root')
    return checked_subset(solver,stronger,core['source'],counts)


def make_prepared_record(solver,prepared,stronger_root,children):
    if not children or len(children)>len(prepared.branches):raise ValueError('Invalid branch prefix')
    model=None;answer=children[-1]['answer']
    if answer:
        prefix,fixed,_=prepared.branches[len(children)-1]
        model=lift(prefix,dict(fixed),children[-1]['model'])
    result=dict(format=FORMAT,source=[list(c) for c in prepared.source],
        query_root=solver._canonical(prepared.source)[2],guards=[],
        missing_clauses=[list(c) for c in prepared.missing],stronger_root=stronger_root,
        children=[{k:deepcopy(c[k]) for k in ('root','answer','model')} for c in children],answer=answer,model=model)
    # No prepared object crosses this boundary. Rebuild and check exactly as
    # for an untrusted cold sidecar, including the premise and every child.
    check_record(solver,result)
    return result


def run(solver,candidate,mode,budget=256):
    if mode not in ('probe-native','reverse6','probe6'):raise ValueError('Invalid probe policy')
    if type(budget) is not int or budget<0:raise ValueError('Invalid total budget')
    began=time.perf_counter();counts=Counter();solver.counts=Counter();source=target_source(candidate,counts)
    report=dict(mode=mode,route='fallback',status='unresolved',result=None,reason=None,partition=None,
        expanded_nodes=0,probe=None,branches=[],descriptor=None)
    phases=Counter();plan=None;used=0;prep_counts={}
    def query(child,limit,retain=False):
        nonlocal used
        tick=time.perf_counter();r=acquire(solver,child,limit,retain_stop=retain)
        phases['acquisition']+=time.perf_counter()-tick;used+=r['metrics'].get('expanded_nodes',0)
        assert used<=budget
        return r
    def finish(r):
        report.update(result=r['result'],status=r['status'],reason=r['reason'])
    try:
        if mode!='reverse6':
            probe=query(source,min(8,budget),True);report['probe']=probe
            if probe['result'] is not None:report['route']='probe';finish(probe);return report
            if used==budget:report['route']='probe-stop';finish(probe);return report
        if mode=='probe-native':
            r=query(source,budget-used);report['branches'].append(r);finish(r);return report
        tick=time.perf_counter();solver.counts=Counter()
        plan=CausalPlan(solver,node_limit=32,literal_limit=8192,byte_limit=128*1024)
        try:plan,desc=prepare_support(solver,candidate,plan)
        except (PlanBudget,SupportBudget):desc=None
        phases['preparation']=time.perf_counter()-tick;report['descriptor']=desc
        eligible=(desc is not None and not desc['outside'] and 2<=len(desc['missing'])<=6
                  and bool(set(map(tuple,desc['source']))&set(map(tuple,source))))
        if not eligible:
            prep_counts=dict(solver.counts);r=query(source,budget-used);report['branches'].append(r);finish(r);return report
        report['route']='partition';missing=list(reversed(desc['missing']));report['missing']=missing
        tick=time.perf_counter();plan.emit(candidate['origin']);phases['plan_emission']=time.perf_counter()-tick
        tick=time.perf_counter();prepared=prepare(source,missing,counts);phases['branch_construction']=time.perf_counter()-tick
        tick=time.perf_counter();inserted,root=publish_prepared(solver,prepared,desc,counts)
        phases['premise']=time.perf_counter()-tick;report.update(stronger_root=root,premise_inserted=inserted)
        prep_counts=dict(solver.counts);branches=prepared.branches;children=[]
        for index,(_,_,child) in enumerate(branches):
            r=query(child,budget-used);r['index']=index;report['branches'].append(r)
            if r['result'] is None:finish(r);return report
            children.append(r['result'])
            if r['result']['answer']:break
        tick=time.perf_counter();before=solver.counts.copy();record=make_prepared_record(solver,prepared,root,children)
        phases['composition']=time.perf_counter()-tick;report['composition_counts']=dict(solver.counts-before)
        report.update(partition=record,result=dict(answer=record['answer'],model=record['model'],root=record['query_root'],authority=record['format']),
            status='sat' if record['answer'] else 'unsat')
        return report
    finally:
        report.update(expanded_nodes=used,counts=dict(counts),preparation_counts=prep_counts,plan_counts={} if plan is None else dict(plan.counts),
            phases=dict(phases),seconds=time.perf_counter()-began)
