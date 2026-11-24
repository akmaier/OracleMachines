#!/usr/bin/env python3
"""Compare shared guard-prefix selection with fixed-tree and native controls."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_stopped_origins as study
from experiments.compare_cnf_stopped_plans import erase
from experiments.cnf_guard_frontier import guard_census,make_frontier_plan,closed_mass
from experiments.cnf_partial_residual_pool import charge
base=study.base;PARENT=Path('experiments/results/cnf-stopped-origins')
MODES=('native','old','open','frontier')
FILES=('experiments/cnf_guard_frontier.py','solver/test_cnf_guard_frontier.py','experiments/compare_cnf_guard_frontier.py')


def prepare(out):
    assert not (out/'protocol.json').exists()
    parent=base.load(PARENT/'checkpoint.json');prior=base.load(PARENT/'protocol.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=study.binding(PARENT/'checkpoint.json'),
        parent_manifest=study.binding(PARENT/'manifest.json'),census=study.binding(PARENT/'census.json'),
        cases=prior['cases'],origins=prior['origins'],targets=[28,64],node_limit=256,plan_node_limit=129,
        orders=[list(MODES),list(reversed(MODES))]*2,
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
            'Exposed guards and targets from the preceding census. Both target choices and all eight origins are retained, without filtering on new outcomes. No fresh or population claim.',
            'Native and old reuse routes are controls; open and frontier share the new tree, composer, native budget and finish-on-stop policy. Open erases conditional certificates after the same construction.',
            'Every worker starts cold from the exact preceding causal origin archive. No later repeat, cumulative union or separate conditional bank is seeded.',
            'New plan loading, source containment, certificate checks, construction and erasure are inside solve timing. The source capture and extraction costs were already measured in the parent and remain additional.',
            'Native solve has different session handoff and stop-tail publication from all composer arms. Native comparisons are route diagnostics, not an isolated guard-selection effect.',
            'Uniform assignment mass per split is a heuristic. It need not correlate with search cost, native coverage or a minimum-cost tree. All uncovered regions remain open.',
            'All raw templates are retained. Dominance is measured, not used to discard alternative supports that may survive different deletions.',
            'Pending frontier state and copied contexts/certificates are not covered by the 129 output-node bound. The census separately measures retained plan size; process peak memory is not measured.']))


def census(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);records=[]
    for origin in p['origins']:
        r=base.load(PARENT/f'origin-{origin}/report.json');ts=study.bound(r['extraction'])['templates']
        target,_=study.native.normalize(cases[origin+1]['source']);counts=Counter();tick=time.perf_counter()
        plan=make_frontier_plan(target,ts,counts=counts);seconds=time.perf_counter()-tick
        old=study.bound(r['plan']);dest=out/f'origin-{origin}';dest.mkdir()
        base.write(dest/'plan.json',plan)
        record=dict(origin=origin,target=origin+1,guards=guard_census(ts),counts=dict(counts),
            construction_seconds=seconds,old_closed_mass=str(closed_mass(old)),closed_mass=str(closed_mass(plan)),
            old_plan_bytes=charge(old),plan_bytes=charge(plan),templates_used=len(plan['templates'])-1,
            plan=study.binding(dest/'plan.json'))
        base.write(dest/'report.json',record);records.append(study.binding(dest/'report.json'))
    base.write(out/'census.json',dict(protocol=study.binding(out/'protocol.json'),origins=records))


def trial(dest,out,target,mode):
    p=base.load(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    if mode in ('open','frontier'):
        original=study.recompose
        def build(solver,source,unused,budget,counts):
            origin=base.load(PARENT/f'origin-{target-1}/report.json')
            ts=study.bound(origin['extraction'])['templates']
            plan=make_frontier_plan(source,ts,counts=counts)
            if mode=='open':plan=erase(plan)
            return original(solver,source,plan,budget,counts)
        with patch.object(study,'recompose',build):study.trial(dest,PARENT,target,mode)
    else:study.trial(dest,PARENT,target,mode)


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'target-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(dest),str(out),str(target),mode],check=True)
                samples.append(dict(target=target,mode=mode,repeat=repeat,**study.binding(dest/'report.json')))
                print('finished',target,repeat,mode,flush=True)
    base.write(out/'comparisons.json',dict(protocol=study.binding(out/'protocol.json'),samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='census':census(out)
    elif action=='run':run(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
