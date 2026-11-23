#!/usr/bin/env python3
"""Record why other guarded supports miss and test missing-clause guidance."""
from collections import Counter
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_unit_support as prior
from experiments.cnf_conditional_unit_support import match
from experiments.cnf_conditional_recovery import proposal,recover
from experiments.cnf_residual_dag import restrict,propagate
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_preimage_fusion import fused_preimages
from experiments.cnf_joint_prefix import reused_joint_prefix
base=prior.base;PARENT=Path('experiments/results/cnf-conditional-unit-support')


def run(out):
    out.mkdir(exist_ok=True);p=base.load(PARENT/'protocol.json');trial=base.load(PARENT/'templates-0/report.json');rs=prior.bound(trial['queries']);cases=prior.bound(p['cases']);templates=[e['template'] for e in base.load(PARENT/'templates.json')['entries']]
    prefix=prior.read_zip(p['prefix']);prepared=prior.read_zip(trial['preparation_delta']);delta=prior.read_zip(trial['delta']);extra={t:list(prepared[t]) for t in prior.TABLES};observations=[]
    with tempfile.TemporaryDirectory() as td:
        for index,r in enumerate(rs):
            if r['route']=='native':
                source=cases[r['case']]['source'];fixed=dict(r['assignment']);template=templates[r['template']];c=Counter()
                contained=[i for i,t in enumerate(templates) if match(source,t,c)]
                compatible=[i for i in contained if not any(v in fixed and fixed[v]!=b for v,b in templates[i]['assumptions'])]
                extend=[i for i in compatible if all(fixed.get(v)==b for v,b in templates[i]['assumptions'])]
                cofactor=restrict(source,fixed,c);up,trace,conflict=propagate(cofactor,c);plan=proposal(source,template,r['assignment'],c)
                proposed=[] if plan is None else [[v,b] for v,b in plan['forced'] if v not in up]
                observation=dict(position=index,case=r['case'],template=r['template'],assignment=r['assignment'],source=source,baseline=r,
                    contained=contained,compatible=compatible,extending=extend,unit_trace=trace,unit_conflict=conflict,plan=plan,new_forces=proposed,recognition_counts=dict(c),
                    prefix=p['prefix'],extra_ids={t:[k for k,v in rows] for t,rows in extra.items()})
                if conflict is None and proposed:
                    path=Path(td)/f'trial{index}';prior.restore(prefix,path,extra);s=ConsequencePrioritySolver(path)
                    try:
                        with fused_preimages(),reused_joint_prefix():
                            screen=screen_branch(s,cofactor,c);s.counts=Counter();tick=time.perf_counter();result=recover(s,source,template,r['assignment'],screen,256,c);seconds=time.perf_counter()-tick
                        assert result['status']==r['status'];final=prior.tables(s)
                        generated={t:final[t][len(prefix[t])+len(extra[t]):] for t in prior.TABLES}
                        observation.update(recovery=result,seconds=seconds,counts=dict(c),metrics=dict(s.counts),delta=prior.write_zip(out/f'probe-{index}-delta.json.gz',generated))
                    finally:s.close()
                observations.append(observation)
            for t in prior.TABLES:extra[t].extend([[k,dict(delta[t])[k]] for k in r['new_ids'][t]])
    base.write(out/'exploration.json',dict(script_sha256=base.sha(__file__),parent=prior.binding(PARENT/'checkpoint.json'),trial=prior.binding(PARENT/'templates-0/report.json'),observations=observations,
        limitations=['Supplied guards and exposed misses. Other template matching is a failed candidate, not a new coverage result.',
        'Each recovery probe restores the historical prefix plus original preparation and preceding query rows. Rebuilt warm pools can differ from the original process, so these timings are exploratory only. No cumulative final union seeds a probe.']))
    print(base.encode([dict(case=r['case'],template=r['template'],new_forces=r['new_forces'],status=r['baseline']['status'],baseline_expansions=r['baseline']['expanded_nodes'],recovery_expansions=r.get('recovery',{}).get('child',{}).get('metrics',{}).get('expanded_nodes')) for r in observations]),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
