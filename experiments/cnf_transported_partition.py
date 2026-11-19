"""Checked first-false composition from a transported causal support.

The caller supplies a candidate origin/map, not a verdict. All origin, core,
premise and branch evidence uses existing native and partition checkers. This
is a residual-level pilot; it does not discharge the source query's conditions.
"""
from collections import Counter
import time
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_canonical_verify import canonical_certificate
from experiments.cnf_support_plan import CausalPlan,PlanBudget,SupportBudget
from experiments.cnf_partition_screen import screen_branch,publish_screened_branch
from experiments.cnf_clause_partition import branch_sources,publish_premise,make_record
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE


def lift_names(cnf,names):
    if any(type(v) is not int or v<1 for v in names) or any(a>=b for a,b in zip(names,names[1:])):
        raise ValueError('Expected an increasing injective variable map')
    if max((abs(l) for c in cnf for l in c),default=0)!=len(names):raise ValueError('Map arity mismatch')
    return [[(1 if l>0 else -1)*names[abs(l)-1] for l in c] for c in cnf]


def target_source(candidate,counts=None):
    cnf,_,_=canonical_certificate(candidate['target'],Counter() if counts is None else counts)
    return lift_names(cnf,candidate['target_names'])


def prepare_support(solver,candidate,plan=None):
    """Prepare once, retaining the causal plan; publication remains deferred."""
    target=target_source(candidate,solver.counts);node=solver._read(candidate['origin'],purpose='transport_partition_origin')
    if node is None or node['answer']:raise ValueError('Checked negative origin required')
    lift_names(node['cnf'],candidate['origin_names'])
    plan=plan if plan is not None else CausalPlan(solver,node_limit=32,literal_limit=8192,byte_limit=128*1024)
    derived=plan.prepare(candidate['origin'])
    core=[[((1 if l>0 else -1)*candidate['origin_names'][abs(l)-1]) for l in node['cnf'][i]] for i in derived['indices']]
    if solver._canonical(core)[2]!=derived['root']:raise ValueError('Support transport changed proof identity')
    missing=sorted(set(map(tuple,core))-set(map(tuple,target)))
    outside=sorted({abs(l) for c in missing for l in c}-{abs(l) for c in target for l in c})
    descriptor=dict(origin=candidate['origin'],indices=derived['indices'],root=derived['root'],
        source=core,target=target,missing=[list(c) for c in missing],outside=outside)
    return plan,descriptor


def native_query(solver,source,budget,screen=None):
    """One native-only query with the current fallback's batching and pools.

    The generic quotient/affine root dispatch is deliberately bypassed so every
    partition child has native authority. Comparisons include this native arm
    and the current full affine policy separately.
    """
    if type(budget) is not int or budget<0:raise ValueError('Nonnegative native budget required')
    source=tuple(tuple(c) for c in source);began=time.perf_counter();old_limit=solver.node_limit
    solver.node_limit=budget;solver._negative_tried=False;solver.db.start()
    try:
        result=(ResidualSolver.solve(solver,source) if screen is None else publish_screened_branch(solver,source,screen))
        solver.db.finish()
    except BaseException:
        solver.db.abort();raise
    finally:solver.db.active=False;solver.node_limit=old_limit
    solver.counts['batch_queries']+=1;result['authority']='native';result['quotient_choice']=None
    solver._admit_negative(result);solver._peak()
    result['metrics']=dict(solver.counts);result['seconds']=time.perf_counter()-began
    return result


def run(solver,candidate,mode,budget=256):
    if mode not in ('forward','reverse','screen'):raise ValueError('Unknown partition policy')
    if type(budget) is not int or budget<0:raise ValueError('Nonnegative native budget required')
    began=time.perf_counter();solver.counts=Counter();counts=Counter();target=target_source(candidate,counts)
    report=dict(mode=mode,status='unresolved',result=None,partition=None,descriptor=None,
        screens=[],branches=[],reason=None,expanded_nodes=0)
    plan=None;phase=Counter();phase_counts={}
    try:
        tick=time.perf_counter();baseline=screen_branch(solver,target,counts) if mode=='screen' else None
        phase['baseline_screen']=time.perf_counter()-tick;report['baseline_screen']=baseline
        if baseline is not None and baseline['conflict'] is not None:
            report['route']='terminal';phase_counts['preparation_solver']=dict(solver.counts)
            tick=time.perf_counter()
            try:result=native_query(solver,target,budget,baseline)
            finally:phase['query']=time.perf_counter()-tick
            report['branches'].append(dict(result=result))
        else:
            tick=time.perf_counter()
            plan=CausalPlan(solver,node_limit=32,literal_limit=8192,byte_limit=128*1024)
            try:plan,desc=prepare_support(solver,candidate,plan)
            except (PlanBudget,SupportBudget):
                desc=None;report['reason']='support-budget'
            phase['support_prepare']=time.perf_counter()-tick;report['descriptor']=desc
            missing=[] if desc is None else desc['missing']
            eligible=desc is not None and not desc['outside'] and 2<=len(missing)<=5 and bool(set(map(tuple,desc['source']))&set(map(tuple,target)))
            chosen=None
            if eligible:
                if mode!='screen':chosen=dict(missing=missing if mode=='forward' else list(reversed(missing)),screens=None)
                else:
                    tick=time.perf_counter();best_score=None
                    for order in ('forward','reverse'):
                        ordered=missing if order=='forward' else list(reversed(missing))
                        branches=branch_sources(target,ordered,counts)[1]
                        screens=[screen_branch(solver,child,counts) for _,_,child in branches]
                        closed=sum(s['conflict'] is not None for s in screens);remaining=len(screens)-closed
                        literals=sum(s['residual_literals'] for s in screens)
                        admitted=remaining==0 or (remaining==1 and closed>=2 and literals<baseline['residual_literals'])
                        report['screens'].append(dict(order=order,missing=ordered,branches=screens,admitted=admitted))
                        score=(remaining,literals,order)
                        if admitted and (best_score is None or score<best_score):chosen=dict(missing=ordered,screens=screens);best_score=score
                    phase['plan_screen']=time.perf_counter()-tick
            if chosen is None:
                report['route']='fallback';phase_counts['preparation_solver']=dict(solver.counts)
                tick=time.perf_counter()
                try:result=native_query(solver,target,budget)
                finally:phase['query']=time.perf_counter()-tick
                report['branches'].append(dict(result=result))
            else:
                report['route']='partition';tick=time.perf_counter()
                # Materialize exactly the retained support plan, then check the
                # strengthened premise. No SAT acquisition occurs in this phase.
                plan.emit(candidate['origin'])
                inserted,root=publish_premise(solver,target,desc,chosen['missing'],counts)
                phase['premise']=time.perf_counter()-tick
                report.update(premise_inserted=inserted,stronger_root=root,missing=chosen['missing'])
                phase_counts['preparation_solver']=dict(solver.counts)
                tick=time.perf_counter();branches=branch_sources(target,chosen['missing'],counts)[1]
                phase['branch_construction']=time.perf_counter()-tick;children=[];used=0
                for i,(_,_,child_source) in enumerate(branches):
                    tick=time.perf_counter()
                    try:
                        child=native_query(solver,child_source,budget-used,None if chosen['screens'] is None else chosen['screens'][i])
                    except RuntimeError as error:
                        if str(error)!=BUDGET_MESSAGE:raise
                        used+=solver.counts['expanded_nodes'];report['expanded_nodes']=used
                        report['branches'].append(dict(index=i,stopped=True,metrics=dict(solver.counts)))
                        raise
                    finally:phase['query']+=time.perf_counter()-tick
                    children.append(child);used+=child['metrics'].get('expanded_nodes',0)
                    report['expanded_nodes']=used;report['branches'].append(dict(index=i,result=child))
                    if child['answer']:break
                tick=time.perf_counter();before=solver.counts.copy()
                record=make_record(solver,target,[],chosen['missing'],root,children)
                phase_counts['composition_solver']=dict(solver.counts-before)
                phase['composition']=time.perf_counter()-tick
                report['partition']=record;result=dict(answer=record['answer'],model=record['model'],root=record['query_root'],authority=record['format'])
        report['result']=result;report['status']='sat' if result['answer'] else 'unsat'
        if report['route']!='partition':report['expanded_nodes']=result['metrics'].get('expanded_nodes',0)
    except RuntimeError as error:
        if str(error)!=BUDGET_MESSAGE:raise
        report['reason']=str(error)
        if report.get('route')!='partition':
            report['expanded_nodes']=solver.counts.get('expanded_nodes',0)
            report['branches'].append(dict(stopped=True,metrics=dict(solver.counts)))
    finally:
        report.update(plan_counts={} if plan is None else dict(plan.counts),counts=dict(counts),phase_counts=phase_counts,
            phases=dict(phase),seconds=time.perf_counter()-began)
    assert report['expanded_nodes']<=budget
    return report
