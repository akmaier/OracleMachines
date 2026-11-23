#!/usr/bin/env python3
"""Reproduce the exact earlier prefix before inspecting an unresolved edit."""
from collections import Counter
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_affine as parent
from experiments.cnf_whole_affine import WholeAffineSolver
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_carried_origins import extract
from experiments.cnf_conditional_unit_support import ExtractionBudget
from experiments.cnf_learned_conditional import COVER_FORMAT,check_cover
from experiments.cnf_leaf_handoff import survival,recompose
base=parent.base


def inspect(out):
    p=base.load(parent.PARENT.parent/'cnf-whole-affine/protocol.json')
    cases=parent.bound(p['cases']['holdout'])
    expected=base.load('experiments/results/cnf-whole-affine/holdout-completion-0/queries.json')
    out.mkdir(parents=True,exist_ok=True);trials=[];prefix=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=WholeAffineSolver(path,node_limit=256)
        try:
            for c,row in zip(cases[:70],expected[:70]):
                r=attempt(s,c['source'])
                assert (r['status'],r['metrics'])==(row['status'],row['metrics'])
                prefix.append(dict(case=c['case'],**r))
            base.write(out/'prefix-queries.json',prefix)
            (out/'prefix').mkdir();archive=base.archive(path,out/'prefix')
            for node_limit,literal_limit in ((64,65536),(512,524288)):
                counts=Counter();tick=time.perf_counter();s.counts=Counter()
                trial=dict(node_limit=node_limit,literal_limit=literal_limit)
                try:
                    bundle,work=extract(s,cases[69]['source'],node_limit=node_limit,literal_limit=literal_limit)
                    cover=dict(format=COVER_FORMAT,templates=[x['template'] for x in bundle['entries']],tree=bundle['tree'])
                    check_cover(cover,counts)
                    intact=survival(cases[70]['source'],cover,counts)
                    trial.update(status='complete',bundle=bundle,counts=work,intact=intact)
                except (ExtractionBudget,ValueError) as e:
                    trial.update(status='unavailable',reason=str(e))
                trial.update(seconds=time.perf_counter()-tick,solver_counts=dict(s.counts),check_counts=dict(counts))
                trials.append(trial)
                if trial['status']=='complete':
                    counts=Counter();tick=time.perf_counter()
                    result=recompose(s,cases[70]['source'],cover,256,counts=counts)
                    trial.update(recomposition=result,recomposition_seconds=time.perf_counter()-tick,
                        recomposition_counts=dict(counts),acquisition_counts=dict(s.counts))
                    break
            (out/'after').mkdir();after=base.archive(path,out/'after')
        finally:s.close()
    base.write(out/'inspection.json',dict(parent=parent.binding('experiments/results/cnf-whole-affine/checkpoint.json'),
        prefix_archive=archive,after_archive=after,origin=cases[69],target=cases[70],trials=trials,
        limitations=['Exact prefix through case 69 only; no target or later answers are seeded.',
            'Posthoc targeted diagnostic with supplied earlier case; it is not an automatic online policy or matched timing result.',
            'Larger extraction is attempted only after preserving the default-cap failure. All records use existing native proof checking.']))
    print(base.encode([dict(status=t['status'],seconds=t['seconds'],reason=t.get('reason'),
        leaves=len(t.get('intact',[])),intact=sum(t.get('intact',[])),recomposition=t.get('recomposition')) for t in trials]),flush=True)


if __name__=='__main__':inspect(Path(sys.argv[1]))
