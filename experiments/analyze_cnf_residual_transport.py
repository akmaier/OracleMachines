#!/usr/bin/env python3
"""Posthoc mismatch census and bounded support trials; no timed policy changes."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import json,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_residual_transport as study
from experiments.cnf_residual_transport import ResidualTransportSolver
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_support_plan import CausalPlan,PlanBudget,SupportBudget
from experiments.cnf_unsat_support import checked_subset
base=study.base


class Census(ResidualTransportSolver):
    def __init__(self,*args,**kwargs):
        self.census=Counter();self.best={};self.case=None
        super().__init__(*args,**kwargs)

    def _transport_reuse(self,cnf):
        mapping=self._transport_stack[-1] if self._transport_stack else None
        if self.transport_pool and cnf and () not in cnf and self._transport_probes<self.transport_probes and mapping is not None:
            target={tuple((1 if l>0 else -1)*mapping[abs(l)-1] for l in cl) for cl in cnf};tried=0
            for entry in reversed(self.transport_pool.values()):
                if entry['anchor'] not in target:continue
                tried+=1;missing=sum(cl not in target for cl in entry['clauses'])
                self.census[str(missing)]+=1
                # Descriptive only: best whole-source overlap seen in this
                # query, not a policy selected after inspecting its answer.
                rank=(missing,len(entry['clauses']),entry['origin'],tuple(mapping),cnf)
                if missing and (self.case not in self.best or rank<self.best[self.case][0]):
                    self.best[self.case]=(rank,dict(case=self.case,origin=entry['origin'],origin_names=entry['names'],
                        target=cnf,target_names=mapping,missing=missing,source_clauses=len(entry['clauses'])))
                if not missing or tried==self.transport_candidates:break
        return super()._transport_reuse(cnf)


def analyze(out):
    p=base.load(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=study.bound(p['cases']['holdout']);old=base.load(out/'holdout-mapped-0/queries.json')
    report=base.load(out/'holdout-mapped-0/report.json')
    options=dict(p['negative_limits'],**p['affine_limits'],**p['transport_limits'],plan_byte_limit=p['plan_byte_limit'])
    began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=Census(path,node_limit=p['node_limit'],**options)
        try:
            for c,previous in zip(cases,old,strict=True):
                s.case=c['case'];r=study.attempt(s,c['source'])
                assert r['status']==previous['status'] and r['metrics']==previous['metrics']
                if r['result'] is not None:
                    for f in ('answer','model','root','authority','quotient_choice'):
                        assert json.loads(json.dumps(r['result'][f]))==previous['result'][f]
            assert base.key_sha(base.encode(sorted(study.prior.native_rows(s).items())))==report['summary']['native_digest']
            assert base.key_sha(base.encode(sorted(study.affine_rows(s).items())))==report['summary']['affine_digest']
            assert sum(s.census.values())==report['summary']['counters'].get('transport_candidates',0)
            census=dict(s.census);proposals=[s.best[k][1] for k in sorted(s.best)]
        finally:s.close()
    replay_seconds=time.perf_counter()-began
    records=[];hits=[];began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';base.restore_archive(report['archive'],path);s=InputSafeAffineProbeSolver(path)
        try:
            with patch.object(s,'_expand',side_effect=AssertionError('Diagnostic must not solve')):
                for candidate in proposals:
                    tick=time.perf_counter();before=Counter(s.counts)
                    plan=CausalPlan(s,node_limit=32,literal_limit=8192,byte_limit=128*1024)
                    record=dict(candidate,status='support-miss')
                    try:
                        origin=s._read(candidate['origin'])
                        if origin is None or origin['answer']:raise ValueError('Negative checked origin required')
                        derived=plan.prepare(candidate['origin'])
                        core=[tuple((1 if l>0 else -1)*candidate['origin_names'][abs(l)-1] for l in origin['cnf'][i]) for i in derived['indices']]
                        target={tuple((1 if l>0 else -1)*candidate['target_names'][abs(l)-1] for l in cl) for cl in candidate['target']}
                        record['core_clauses']=len(core);record['core_missing']=sum(cl not in target for cl in core)
                        if not record['core_missing']:
                            plan.emit(candidate['origin']);inverse={v:i+1 for i,v in enumerate(candidate['target_names'])}
                            raw=[[inverse[abs(l)]*(1 if l>0 else -1) for l in cl] for cl in core]
                            inserted,root=checked_subset(s,candidate['target'],raw)
                            record.update(status='checked-support',root=root,inserted=inserted,
                                is_query_root=root==cases[candidate['case']]['root'])
                            hits.append(dict(source=candidate['target'],result=dict(answer=False,model=None,root=root,authority='native')))
                    except (PlanBudget,SupportBudget):record['status']='budget-stop'
                    record.update(plan_counts=dict(plan.counts),solver_counts=dict(s.counts-before),seconds=time.perf_counter()-tick)
                    records.append(record)
        finally:s.close()
        audit=study.cold(path,[dict(source=h['source']) for h in hits],[dict(status='unsat',result=h['result']) for h in hits])
        dest=out/'support-diagnostic';dest.mkdir();archive=base.archive(path,dest)
    base.write(out/'mismatch-analysis.json',dict(source=study.binding('experiments/analyze_cnf_residual_transport.py'),
        parent_archive=report['archive'],outputs_counters_and_digests_identical=True,
        missing_clause_histogram=census,candidates=sum(census.values()),records=records,
        statuses=dict(Counter(r['status'] for r in records)),replay_seconds=replay_seconds,
        support_seconds=time.perf_counter()-began,archive=archive,cold=audit,limitations=[
        'Posthoc census of exactly the mapped policy candidates; it does not change frozen decisions or compare instrumented runtime.',
        'At most one minimum-missing-clause candidate per query is tried under 32-node/8192-literal/128-KiB causal-plan limits. This is not exhaustive support or mapping discovery.',
        'Derived target refutations are residual facts. Only records explicitly matching the original query key could refute that query directly.',
        'Proof checking and transient workspace have separate uncapped costs; diagnostic archives preserve any new evidence separately from the timed union.']))
    print(base.encode(dict(candidates=sum(census.values()),statuses=dict(Counter(r['status'] for r in records)),histogram=census)),flush=True)


if __name__=='__main__':analyze(Path(sys.argv[1]))
