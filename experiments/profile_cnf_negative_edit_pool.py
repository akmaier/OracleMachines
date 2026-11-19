#!/usr/bin/env python3
"""Post-timing phase profile; require the frozen negative-policy results/counters."""
from collections import Counter
from pathlib import Path
import cProfile,json,pstats,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_negative_edit_pool as study
from experiments.cnf_negative_edit_pool import NegativeEditPoolSolver
base=study.base


class TimedNegative(NegativeEditPoolSolver):
    def __init__(self,*args,**kwargs):
        self.phase_seconds=Counter();super().__init__(*args,**kwargs)
    def _extract(self,key,materialize):
        tick=time.perf_counter()
        try:return super()._extract(key,materialize)
        finally:self.phase_seconds['materialization' if materialize else 'discovery']+=time.perf_counter()-tick


def main(out):
    p=base.load(out/'protocol.json');profiles={}
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]);expected=base.load(out/f'{split}-negative-0/queries.json');prof=cProfile.Profile()
        with tempfile.TemporaryDirectory() as td:
            s=TimedNegative(Path(td)/'db',node_limit=p['node_limit'],**p['negative_limits']);tick=time.perf_counter()
            try:
                for c,old in zip(cases,expected):
                    prof.enable();r=study.attempt(s,c['source']);prof.disable()
                    assert r['status']==old['status'] and r['metrics']==old['metrics']
                    if r['result'] is not None:
                        for f in ('answer','model','root','authority','quotient_choice'):assert json.loads(json.dumps(r['result'][f]))==old['result'][f]
                elapsed=time.perf_counter()-tick;phases=dict(s.phase_seconds)
                summary=base.load(out/f'{split}-negative-0/report.json')['summary']
                assert base.key_sha(base.encode(sorted(study.prior.native_rows(s).items())))==summary['native_digest']
            finally:s.close()
        stats=pstats.Stats(prof);rows=[]
        for (filename,line,function),(primitive,calls,exclusive,cumulative,callers) in stats.stats.items():
            if '/OracleMachines/' in filename:filename=filename.split('/OracleMachines/',1)[1]
            rows.append(dict(file=filename,line=line,function=function,calls=calls,primitive=primitive,exclusive=exclusive,cumulative=cumulative))
        profiles[split]=dict(outputs_and_counters_identical=True,phase_seconds=phases,profiled_seconds=elapsed,
            top_exclusive=sorted(rows,key=lambda r:-r['exclusive'])[:30],top_cumulative=sorted(rows,key=lambda r:-r['cumulative'])[:30])
    base.write(out/'profile.json',dict(source=study.binding(__file__),profiles=profiles,
        limitations=['Posthoc cProfile instrumentation changes timing; no overlap with matched timed workers. Inclusive phase and routine times overlap and must not be added.',
        'Exact statuses, models, counters and native payload digest match the frozen negative arm. This profile attributes overhead; it is not a measured faster variant.']))
    print(base.encode({s:dict(phase_seconds=v['phase_seconds'],profiled_seconds=v['profiled_seconds']) for s,v in profiles.items()}),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
