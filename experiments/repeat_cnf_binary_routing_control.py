#!/usr/bin/env python3
"""Repeat the entire last timing pair after a brief diagnostic overlap."""
from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_routing as study
base=study.base


def repeat(out):
    p=base.load(out/'protocol.json');report=base.load(out/'report.json')
    assert not (out/'first-pass-report.json').exists()
    base.write(out/'first-pass-report.json',report);changes=[]
    for rep,order in enumerate(p['orders']):
        for mode in order:
            sample=next(s for s in report['samples'] if (s['split'],s['case'],s['mode'],s['repeat'])==('novel',61,mode,rep))
            old=dict(sample);dest=out/f'novel-61-{mode}-{rep}-serial'
            subprocess.run([sys.executable,study.__file__,'worker',str(dest),str(out/'protocol.json'),'novel','61',mode],check=True)
            new=study.binding(dest/'report.json');a=study.bound(old);b=study.bound(new)
            for field in ('delta_digest','expanded_nodes','new_records','statuses'):assert a['summary'][field]==b['summary'][field]
            assert a['partitions']['sha256']==b['partitions']['sha256']
            for x,y in zip(study.bound(a['queries']),study.bound(b['queries']),strict=True):
                for field in ('new_ids','status','expanded_nodes','partition'):assert x[field]==y[field]
            sample.update(new);changes.append(dict(old=old,new=dict(sample)))
        print('repeated novel61 order',rep,flush=True)
    base.write(out/'report.json',report)
    base.write(out/'timing-repeat.json',dict(first=study.binding(out/'first-pass-report.json'),final=study.binding(out/'report.json'),changes=changes,
        script_sha256=base.sha(__file__),reason='A 0.34-second diagnostic ran while the final novel61 order was active. Repeat the whole novel61 stratum in both orders after it ends; retain all original artifacts. No faster-sample selection.',
        limitations=['Both orders and all policies are replaced together. Proof deltas, decisions, branch counts and partitions are identical; original timing values remain available.']))


if __name__=='__main__':repeat(Path(sys.argv[1]))
