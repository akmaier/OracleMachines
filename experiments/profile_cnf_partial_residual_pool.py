#!/usr/bin/env python3
"""Post-timing attribution and a checked coordinate-loss counterexample."""
from collections import Counter
from itertools import product
from pathlib import Path
from unittest.mock import patch
import cProfile,json,pstats,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partial_residual_pool as study
from experiments.cnf_partial_residual_pool import PartialResidualSolver
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_unsat_support import checked_subset
base=study.base


class TimedPartial(PartialResidualSolver):
    def __init__(self,*args,**kwargs):self.phases=Counter();super().__init__(*args,**kwargs)
    def _refresh_partial(self):
        t=time.perf_counter()
        try:return super()._refresh_partial()
        finally:self.phases['admission']+=time.perf_counter()-t
    def _partial_reuse(self,cnf):
        t=time.perf_counter()
        try:return super()._partial_reuse(cnf)
        finally:self.phases['retrieval']+=time.perf_counter()-t


def coordinate_example(out):
    core=[list(c) for c in product((-1,1),(-2,2),(-3,3))]
    lifted=[[(1 if l>0 else -1)*(abs(l)+3) for l in c] for c in core]
    target=lifted+[[1,4,7],[2,5,8],[3,6,9]]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';seed=ResidualSolver(path,leaves=False,decompose=False)
        try:origin=seed.solve(core)['root']
        finally:seed.close()
        s=PartialResidualSolver(path,affine_variables=1,leaves=False,decompose=False)
        try:
            before=Counter(s.counts);cnf,_,key=s._canonical(target)
            assert s._partial_reuse(cnf) is None
            missed=dict(s.counts-before);counts=Counter()
            with patch.object(s,'_expand',side_effect=AssertionError('No fresh solving')):
                inserted,root=checked_subset(s,target,lifted,counts)
            assert inserted and root==key and s._read(root)['answer'] is False
            assert s._canonical(lifted)[2]==origin
            record=dict(core=core,target=target,transport=dict((v,v+3) for v in (1,2,3)),
                origin=origin,root=root,proposal_miss=missed,transport_counts=dict(counts),
                node=s._read(root),limitations=[
                'The order-preserving map is supplied for this diagnostic; no automatic map discovery or benchmark speedup is claimed.',
                'Literal-valued anchors in separately compacted coordinates miss this reusable core. The original subset checker validates its explicit injection.',
                'The example establishes a representation blind spot, not its frequency in the held-out random/shared mixtures.'])
        finally:s.close()
        audit=study.cold(path,[dict(source=target)],[dict(result=dict(answer=False,model=None,root=root,authority='native'),status='unsat')])
        dest=out/'coordinate-example';dest.mkdir();archive=base.archive(path,dest)
    record.update(archive=archive,cold=audit);base.write(out/'coordinate-example.json',record)


def main(out):
    p=base.load(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=study.bound(p['cases']['holdout']);expected=base.load(out/'holdout-partial-0/queries.json')
    options=dict(p['negative_limits'],**p['affine_limits'],**p['partial_limits'],plan_byte_limit=p['plan_byte_limit'])
    prof=cProfile.Profile()
    with tempfile.TemporaryDirectory() as td:
        s=TimedPartial(Path(td)/'db',node_limit=p['node_limit'],**options);tick=time.perf_counter()
        try:
            for c,old in zip(cases,expected,strict=True):
                prof.enable();r=study.attempt(s,c['source']);prof.disable()
                assert r['status']==old['status'] and r['metrics']==old['metrics']
                if r['result'] is not None:
                    for f in ('answer','model','root','authority','quotient_choice'):
                        assert json.loads(json.dumps(r['result'][f]))==old['result'][f]
            summary=base.load(out/'holdout-partial-0/report.json')['summary']
            assert base.key_sha(base.encode(sorted(study.prior.native_rows(s).items())))==summary['native_digest']
            assert base.key_sha(base.encode(sorted(study.affine_rows(s).items())))==summary['affine_digest']
            phases=dict(s.phases);elapsed=time.perf_counter()-tick
        finally:s.close()
    rows=[]
    for (filename,line,function),(primitive,calls,exclusive,cumulative,callers) in pstats.Stats(prof).stats.items():
        if '/OracleMachines/' in filename:filename=filename.split('/OracleMachines/',1)[1]
        rows.append(dict(file=filename,line=line,function=function,calls=calls,primitive=primitive,exclusive=exclusive,cumulative=cumulative))
    result=dict(source=study.binding(__file__),outputs_counters_and_digests_identical=True,profiled_seconds=elapsed,phases=phases,
        top_exclusive=sorted(rows,key=lambda r:-r['exclusive'])[:25],top_cumulative=sorted(rows,key=lambda r:-r['cumulative'])[:25],
        partial_routines=[r for r in rows if r['file']=='experiments/cnf_partial_residual_pool.py'],
        limitations=['Posthoc instrumentation changes timing; use frozen workers for policy comparisons. Inclusive phase and routine times overlap and cannot be added.'])
    base.write(out/'profile.json',result);coordinate_example(out);print(base.encode(dict(profiled_seconds=elapsed,phases=phases)),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
