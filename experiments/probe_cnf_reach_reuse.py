#!/usr/bin/env python3
"""Initial bounded discovery inventory, keeping improvements and regressions."""
from collections import Counter
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_context as prior
from experiments import cnf_shortening_reach_reuse as candidate
base=prior.base;old=prior.old


def run(out):
    parent=base.load('experiments/results/cnf-shortening-context/checkpoint.json')
    p=old.bound(parent['guard_covers']['protocol']);refs=old.bound(parent['guard_shortening']['census'])['records'];rows=[];started=time.perf_counter()
    for target,binding in zip(p['targets'],p['inputs']):
        source=prior.native.normalize(old.bound(p['cases'])[target]['source'])[0]
        templates=old.bound(old.bound(binding)['extraction'])['templates'];selected=[r for r in refs if r['target']==target]
        events=old.bound(selected[0]['events'])['events']
        for ref in selected:
            c=Counter();tick=time.perf_counter();local,hints,_=prior.previous.local_hints(source,templates,events[ref['event']],c)
            binding_seconds=time.perf_counter()-tick;c=Counter();tick=time.perf_counter()
            program=candidate.discover(local,[h['template'] for h in hints],c,**prior.previous.LIMITS)
            rows.append(dict(target=target,event=ref['event'],old=ref['program'],new=program,counts=dict(c),binding_seconds=binding_seconds,discovery_seconds=time.perf_counter()-tick))
        print(base.encode(dict(target=target,statuses=Counter(r['new']['reason'] for r in rows))),flush=True)
    base.write(out/'probe.json',dict(rows=rows,seconds=time.perf_counter()-started,
        source_fingerprints={f:base.sha(f) for f in ('experiments/cnf_shortening_reach_reuse.py','solver/test_cnf_shortening_reach_reuse.py','experiments/probe_cnf_reach_reuse.py')}))


if __name__=='__main__':run(Path(sys.argv[1]))
