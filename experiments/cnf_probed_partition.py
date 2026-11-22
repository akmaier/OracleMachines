"""Preserve a checked native probe before optional six-clause partitioning.

The probe is a bounded acquisition, not a cost oracle. Its completed proof nodes
survive a budget stop; incomplete roots confer no authority. All calls share one
native-expansion budget and use the existing proof and partition checkers.
"""
from collections import Counter
import time
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_transported_partition import target_source,prepare_support
from experiments.cnf_support_plan import CausalPlan,PlanBudget,SupportBudget
from experiments.cnf_clause_partition import branch_sources,publish_premise,make_record
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE


def acquire(solver,source,budget,*,retain_stop=False):
    if type(budget) is not int or budget<0:raise ValueError('Invalid native budget')
    began=time.perf_counter();source=tuple(tuple(c) for c in source);old=solver.node_limit
    solver.db.start();solver.node_limit=budget;solver._negative_tried=False;result=None;stopped=False
    try:
        try:result=ResidualSolver.solve(solver,source)
        except RuntimeError as error:
            if str(error)!=BUDGET_MESSAGE:raise
            stopped=True
            if retain_stop:
                # Every pending node was independently checked before insertion;
                # no incomplete parent is stored. Commit that dependency prefix.
                solver.counts['probe_retained_pending_records']=len(solver.db.pending)
                solver.db.finish();solver.counts['probe_budget_prefix_commits']+=1
            else:solver.db.abort()
        else:solver.db.finish()
    except BaseException:
        solver.db.abort();raise
    finally:solver.db.active=False;solver.node_limit=old
    solver._peak();solver.counts['probe_acquisition_calls']+=1
    if result is not None:
        result.update(authority='native',quotient_choice=None);solver._admit_negative(result)
        result['metrics']=dict(solver.counts)
    return dict(result=result,status='unresolved' if stopped else 'sat' if result['answer'] else 'unsat',
        reason=BUDGET_MESSAGE if stopped else None,metrics=dict(solver.counts),seconds=time.perf_counter()-began)


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
        tick=time.perf_counter();plan.emit(candidate['origin']);inserted,root=publish_premise(solver,source,desc,missing,counts)
        phases['premise']=time.perf_counter()-tick;report.update(stronger_root=root,premise_inserted=inserted)
        prep_counts=dict(solver.counts);tick=time.perf_counter();branches=branch_sources(source,missing,counts)[1]
        phases['branch_construction']=time.perf_counter()-tick;children=[]
        for index,(_,_,child) in enumerate(branches):
            r=query(child,budget-used);r['index']=index;report['branches'].append(r)
            if r['result'] is None:finish(r);return report
            children.append(r['result'])
            if r['result']['answer']:break
        tick=time.perf_counter();before=solver.counts.copy();record=make_record(solver,source,[],missing,root,children)
        phases['composition']=time.perf_counter()-tick;report['composition_counts']=dict(solver.counts-before)
        report.update(partition=record,result=dict(answer=record['answer'],model=record['model'],root=record['query_root'],authority=record['format']),
            status='sat' if record['answer'] else 'unsat')
        return report
    finally:
        report.update(expanded_nodes=used,counts=dict(counts),preparation_counts=prep_counts,plan_counts={} if plan is None else dict(plan.counts),
            phases=dict(phases),seconds=time.perf_counter()-began)
