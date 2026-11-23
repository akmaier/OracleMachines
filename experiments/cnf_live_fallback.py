"""Keep the native stack live while deciding probe fallback, with no new authority.

The owner must use the solver exclusively for the synchronous call. Completed
proofs commit at the budget boundary; unsupported routing unwinds as before.
No incomplete frame escapes the call or survives process termination.
"""
from collections import Counter
import time
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import FORMAT
from experiments.cnf_larger_mixtures import BUDGET_MESSAGE
from experiments.cnf_probed_partition import acquire
from experiments.cnf_partition_preparation import prepare,publish_prepared,make_prepared_record
from experiments.cnf_transported_partition import target_source,prepare_support
from experiments.cnf_support_plan import CausalPlan,PlanBudget,SupportBudget


class ContinuationSolver(InputSafeAffineProbeSolver):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._budget_hook=None;self._continuation_active=False;self._continuation_deciding=False

    def _visit(self,cnf):
        # Identical to the inherited native visitor except the guarded handoff.
        # The callback runs after canonical lookup and before charging expansion.
        if self._continuation_deciding:raise RuntimeError('Search inside continuation routing')
        self.counts['visits']+=1
        normalized,names,key=self._canonical(cnf)
        node=self._read(key,normalized) if self.reuse else None
        if node is None:
            if self.counts['expanded_nodes']>=self.node_limit:
                hook=self._budget_hook
                if hook is None or not hook():raise RuntimeError(BUDGET_MESSAGE)
                if self.counts['expanded_nodes']>=self.node_limit:raise RuntimeError(BUDGET_MESSAGE)
            self.counts['expanded_nodes']+=1
            model,proof=self._expand(normalized)
            node={'format':FORMAT,'cnf':[list(c) for c in normalized],'answer':model is not None}
            if model is not None:
                local_count=max((abs(l) for c in normalized for l in c),default=0)
                node['model']=[model.get(i,False) for i in range(1,local_count+1)]
            else:node['proof']=proof
            self._store(key,node)
        model=({old:node['model'][i] for i,old in enumerate(names)} if node['answer'] else None)
        return model,key


def run(solver,candidate,mode,budget=256,*,observe=None):
    if mode not in ('probe-native','reverse6','probe6'):raise ValueError('Invalid probe policy')
    if type(budget) is not int or budget<0:raise ValueError('Invalid total budget')
    if not isinstance(solver,ContinuationSolver):raise TypeError('Continuation solver required')
    if solver._continuation_active:raise RuntimeError('Nested continuation query')
    began=time.perf_counter();counts=Counter();solver.counts=Counter();source=target_source(candidate,counts)
    report=dict(mode=mode,route='fallback',status='unresolved',result=None,reason=None,partition=None,
        expanded_nodes=0,probe=None,branches=[],descriptor=None)
    phases=Counter();plan=None;used=0;prep_counts={};prepared_control=False;resumed=False;desc=None
    probe_snapshot=None
    def control():
        nonlocal plan,desc,prep_counts,prepared_control,resumed,probe_snapshot
        # The only suspension point is the original pre-expansion budget guard.
        # Publish complete children before inspecting the supplied candidate.
        solver._budget_hook=None
        solver.db.finish();solver.db.active=False;solver._peak()
        probe_snapshot=dict(result=None,status='unresolved',reason=BUDGET_MESSAGE,
            metrics=dict(solver.counts),seconds=time.perf_counter()-began)
        search_counts=solver.counts
        try:
            solver._continuation_deciding=True;solver.counts=Counter()
            if mode!='probe-native':
                tick=time.perf_counter()
                plan=CausalPlan(solver,node_limit=32,literal_limit=8192,byte_limit=128*1024)
                try:plan,desc=prepare_support(solver,candidate,plan)
                except (PlanBudget,SupportBudget):desc=None
                phases['preparation']=time.perf_counter()-tick
                report['descriptor']=desc;prepared_control=True
            prep_counts=dict(solver.counts)
            eligible=(desc is not None and not desc['outside'] and 2<=len(desc['missing'])<=6
                and bool(set(map(tuple,desc['source']))&set(map(tuple,source))))
            if observe is not None:observe(solver,eligible)
        finally:
            solver.counts=search_counts;solver._continuation_deciding=False
        if eligible:return False
        solver.node_limit=budget;solver.db.start();resumed=True
        solver.counts['continuation_resumptions']+=1
        return True
    def query(child,limit,retain=False):
        nonlocal used
        tick=time.perf_counter();before_preparation=phases['preparation']
        r=acquire(solver,child,limit,retain_stop=retain)
        phases['acquisition']+=time.perf_counter()-tick-(phases['preparation']-before_preparation)
        used+=r['metrics'].get('expanded_nodes',0)
        assert used<=budget
        return r
    def finish(r):
        report.update(result=r['result'],status=r['status'],reason=r['reason'])
    solver._continuation_active=True
    try:
        if mode!='reverse6':
            if budget>8:solver._budget_hook=control
            probe=query(source,min(8,budget),True);solver._budget_hook=None
            if resumed:
                report.update(route='resumed',probe=probe_snapshot,resumed_query=probe)
                finish(probe);return report
            report['probe']=probe
            if probe['result'] is not None:report['route']='probe';finish(probe);return report
            if used==budget:report['route']='probe-stop';finish(probe);return report
        if mode=='probe-native':
            r=query(source,budget-used);report['branches'].append(r);finish(r);return report
        if not prepared_control:
            tick=time.perf_counter();solver.counts=Counter()
            plan=CausalPlan(solver,node_limit=32,literal_limit=8192,byte_limit=128*1024)
            try:plan,desc=prepare_support(solver,candidate,plan)
            except (PlanBudget,SupportBudget):desc=None
            phases['preparation']=time.perf_counter()-tick;report['descriptor']=desc
        else:solver.counts=Counter(prep_counts)
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
        solver._budget_hook=None;solver._continuation_active=False;solver._continuation_deciding=False
        report.update(expanded_nodes=used,counts=dict(counts),preparation_counts=prep_counts,plan_counts={} if plan is None else dict(plan.counts),
            phases=dict(phases),seconds=time.perf_counter()-began)
