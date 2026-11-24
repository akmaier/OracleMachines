#!/usr/bin/env python3
"""Exposed cold diagnostics with the same-tree, certificate-free control."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import subprocess, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_stopped_origins as study
from experiments.cnf_partial_proof_plan import check_plan
base=study.base
MODES=('native','open','plan')


def erase(plan):
    result=deepcopy(plan)
    result['templates']=[dict(open=True,clauses=[]) for _ in result['templates']]
    check_plan(result)
    return result


def prepare(out):
    path=out/'comparison-protocol.json'; assert not path.exists()
    base.write(path,dict(census=study.binding(out/'census.json'),
        source_fingerprints={**base.load(out/'protocol.json')['source_fingerprints'],
            'experiments/compare_cnf_stopped_plans.py':base.sha(__file__)},
        targets=list(study.TARGETS),orders=[list(MODES),list(reversed(MODES))]*2,
        limitations=[
            'Exposed diagnostic, two provisioned origins. The eight-origin census selection and artifacts remain unchanged.',
            'Open and plan use exactly the same tree, source prefix, composer, native budget and transaction policy. Open removes every conditional certificate; it retains the discovery-derived branching order.',
            'Native uses the ordinary solve session. Unlike both composer arms, it enables the solve-session handoff and aborts the last pending publication batch on a budget stop. Native comparisons are route diagnostics, not an isolated support effect.',
            'All arms start cold from the exact causal source-prefix archive, with no future query or separately materialized conditional proofs seeded.',
            'Source capture, extraction, construction, serialization and prefix storage are separately recorded in the census. Trial solve and worker times exclude those acquisition costs.']))


def trial(dest,out,target,mode):
    p=base.load(out/'comparison-protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    if mode=='open':
        original=study.recompose
        def without_support(solver,source,plan,budget,counts):
            return original(solver,source,erase(plan),budget,counts)
        with patch.object(study,'recompose',without_support):study.trial(dest,out,target,mode)
    else:study.trial(dest,out,target,mode)


def run(out):
    p=base.load(out/'comparison-protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'comparison-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(dest),str(out),str(target),mode],check=True)
                samples.append(dict(target=target,mode=mode,repeat=repeat,**study.binding(dest/'report.json')))
                print('finished',target,repeat,mode,flush=True)
    base.write(out/'comparisons.json',dict(protocol=study.binding(out/'comparison-protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
