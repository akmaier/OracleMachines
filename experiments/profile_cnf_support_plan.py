#!/usr/bin/env python3
"""Post-timing profile of unchanged negative reuse and planned proof emission."""
from collections import Counter
from pathlib import Path
import cProfile,json,pstats,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_support_plan as study
from experiments.cnf_support_plan import PlannedNegativeSolver
from experiments.cnf_negative_edit_pool import NegativeEditPoolSolver
from experiments.cnf_residual_dag import normalize,token
from experiments.cnf_affine_patterns import extract_affine,check_affine
from experiments.cnf_affine_negative import compile_proof,check_negative
base=study.base


class TimedPhases:
    def __init__(self,*args,**kwargs):
        self.phase_seconds=Counter();super().__init__(*args,**kwargs)
    def _extract(self,key,materialize):
        tick=time.perf_counter()
        try:return super()._extract(key,materialize)
        finally:self.phase_seconds['materialization' if materialize else 'discovery']+=time.perf_counter()-tick


class TimedNegative(TimedPhases,NegativeEditPoolSolver):pass
class TimedPlan(TimedPhases,PlannedNegativeSolver):pass


def frontier(out,p):
    cases=study.bound(p['cases']['holdout']);queries=base.load(out/'holdout-plan-0/queries.json')
    report=base.load(out/'holdout-plan-0/report.json');groups={};stops=[];affine=[];tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';base.restore_archive(report['archive'],path);con=sqlite3.connect(path)
        try:
            available={key for key, in con.execute('SELECT id FROM cnf_residual_v1')}
            for c,r in zip(cases,queries):
                g=groups.setdefault(c['family'],Counter());g['seconds']+=r['seconds'];g['expansions']+=r['metrics'].get('expanded_nodes',0)
                g['budget_stops']+=int(r['status']=='unresolved')
                if r['status']=='unresolved':
                    answers=Counter(json.loads(con.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone()[0])['answer'] for key in r['new_ids']['cnf_residual_v1'])
                    stops.append(dict(case=c['case'],root=c['root'],family=c['family'],variant=c['variant'],size=c['size'],seconds=r['seconds'],
                        committed_negative=answers[False],committed_positive=answers[True],discarded_pending=r['metrics'].get('batch_discarded_checks_records',0),root_known_at_end=c['root'] in available))
        finally:con.close()
    # Apply an existing source-bound recognizer to every input, not selected labels.
    # This is posthoc evidence for the next experiment, not a change to timed search.
    for c,r in zip(cases,queries):
        t=time.perf_counter();counts=Counter();cnf,names=normalize(c['source'],counts);root=token(cnf,counts);assert root==c['root']
        certificate=extract_affine(cnf,counts);summary=check_affine(cnf,certificate,counts);proof=None
        if summary['inconsistent']:
            proof=compile_proof(dict(status='linear-conflict',affine=certificate));check_negative(cnf,len(names),proof,counts)
            assert r['status']!='sat'
        affine.append(dict(case=c['case'],root=root,native_status=r['status'],summary=summary,affine=certificate,negative_proof=proof,metrics=dict(counts),seconds=time.perf_counter()-t))
    base.write(out/'affine-screen.json',dict(cases=p['cases']['holdout'],records=affine,
        checked_negative=sum(r['negative_proof'] is not None for r in affine),budget_stops_refuted=sum(r['negative_proof'] is not None and r['native_status']=='unresolved' for r in affine),
        seconds=sum(r['seconds'] for r in affine),limitations=['Existing explicit-parity extraction and independent affine-negative checker, applied posthoc to all inputs without generator labels.',
        'A consistent extracted subsystem gives no verdict for its leftover CNF. Original native unknowns remain unchanged; this path was not integrated or timed as part of the solver.']))
    result=dict(groups={k:dict(v) for k,v in groups.items()},budget_stops=stops,unknown_attempt_seconds=sum(r['seconds'] for r in stops),
        total_query_seconds=sum(r['seconds'] for r in queries),end_missing_roots=sorted({c['root'] for c in cases if c['root'] not in available}),
        affine_screen=study.binding(out/'affine-screen.json'),seconds=time.perf_counter()-tick,
        limitations=['Committed residual proofs are not unconditioned refutations of the budget-stopped source. Cross-edit recomposition requires checked source/assumption transport.',
        'Root-only negative admission excludes incomplete source queries. Partial-prefix and affine integration are future candidates, not measured improvements in this trial.'])
    base.write(out/'frontier.json',result)


def main(out):
    p=base.load(out/'protocol.json');profiles={}
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    # Match both variants on the fresh split after every benchmark worker ends.
    split='holdout';cases=study.bound(p['cases'][split])
    for mode,cls in (('negative',TimedNegative),('plan',TimedPlan)):
        expected=base.load(out/f'{split}-{mode}-0/queries.json');prof=cProfile.Profile()
        with tempfile.TemporaryDirectory() as td:
            options=dict(p['negative_limits'])
            if mode=='plan':options['plan_byte_limit']=p['plan_byte_limit']
            s=cls(Path(td)/'db',node_limit=p['node_limit'],**options);tick=time.perf_counter()
            try:
                for c,old in zip(cases,expected):
                    prof.enable();r=study.attempt(s,c['source']);prof.disable()
                    assert r['status']==old['status'] and r['metrics']==old['metrics']
                    if r['result'] is not None:
                        for f in ('answer','model','root','authority','quotient_choice'):
                            assert json.loads(json.dumps(r['result'][f]))==old['result'][f]
                elapsed=time.perf_counter()-tick;phases=dict(s.phase_seconds)
                summary=base.load(out/f'{split}-{mode}-0/report.json')['summary']
                assert base.key_sha(base.encode(sorted(study.prior.native_rows(s).items())))==summary['native_digest']
            finally:s.close()
        stats=pstats.Stats(prof);rows=[]
        for (filename,line,function),(primitive,calls,exclusive,cumulative,callers) in stats.stats.items():
            if '/OracleMachines/' in filename:filename=filename.split('/OracleMachines/',1)[1]
            rows.append(dict(file=filename,line=line,function=function,calls=calls,primitive=primitive,exclusive=exclusive,cumulative=cumulative))
        profiles[mode]=dict(outputs_and_counters_identical=True,phase_seconds=phases,profiled_seconds=elapsed,
            top_exclusive=sorted(rows,key=lambda r:-r['exclusive'])[:30],top_cumulative=sorted(rows,key=lambda r:-r['cumulative'])[:30],
            plan_routines=[r for r in rows if r['file']=='experiments/cnf_support_plan.py'])
    base.write(out/'profile.json',dict(source=study.binding('experiments/profile_cnf_support_plan.py'),split=split,profiles=profiles,
        limitations=['Posthoc serial cProfile runs change timing; no overlap with matched workers. Phase/routine inclusive times overlap and cannot be added.',
        'Statuses, semantic result fields, counters and native payload digest match each frozen variant. Only the matched worker times measure the policy comparison.']))
    frontier(out,p)
    print(base.encode({m:dict(phase_seconds=v['phase_seconds'],profiled_seconds=v['profiled_seconds']) for m,v in profiles.items()}),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
