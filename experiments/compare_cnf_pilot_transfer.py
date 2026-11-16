#!/usr/bin/env python3
"""Transfer the frozen two-route pilot and control to the next bound original."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_pilot_refinement as previous
from experiments.cnf_pilot_refinement import PilotRefinement
from experiments.cnf_saved_split_reuse import candidates
base=previous.base
PARENT=Path('experiments/results/cnf-pilot-refinement')


def run(out):
    out.mkdir(exist_ok=False);cp=base.load(PARENT/'checkpoint.json');validation=base.load(PARENT/'validation.json')
    sources=dict(validation['source_fingerprints'])
    for path,digest in sources.items():assert base.sha(path)==digest,path
    sources['experiments/compare_cnf_pilot_transfer.py']=base.sha(__file__)
    protocol=base.load(PARENT/'protocol.json');target=base.load(PARENT/'next-discovery.json')
    protocol.update(checkpoint=previous.binding(PARENT/'checkpoint.json'),target=previous.binding(PARENT/'next-discovery.json'),
        queries=cp['queries'],source_fingerprints=sources,inherited_policy=previous.binding(PARENT/'protocol.json'))
    protocol['limitations']=[s.replace('Case 11','Case 13') for s in protocol['limitations']]
    protocol['limitations'].append('Transfer uses byte-identical scheduler, worker, checker and validator sources; no budget or policy tuning.')
    tick=time.perf_counter();queries=base.load(cp['queries']['path']);root=queries[target['case']]['roots'][0]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';base.restore_archive(cp['archive'],path);before=base.sha(path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            with base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('preflight admission')),patch.object(base.split,'discover_simplification',side_effect=AssertionError('preflight assumption')):
                s=PilotRefinement(h,root,target['source']);assert not s.coverage.closed()[0]
                preflight=dict(case=target['case'],source_sha256=base.key_sha(target['source']),unary_prefix_accepted=True,
                    candidates=candidates(s,target['source']),pilot_variables=[s.records[k]['variable'] for k in s.candidates],no_acquisition=True)
        finally:h.close();assert base.sha(path)==before
    preflight['seconds']=time.perf_counter()-tick;base.write(out/'preflight.json',preflight)
    protocol['preflight']=previous.binding(out/'preflight.json');base.write(out/'protocol.json',protocol)
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**previous.binding(dest/'report.json')))
    summary={}
    for mode in previous.MODES:
        trials=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_raw']
        fixed=[k for k in a if k not in timed and k!='mode']
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed}}
    base.write(out/'report.json',dict(protocol_sha256=base.sha(out/'protocol.json'),samples=samples,summary=summary))
    print(base.encode({m:{k:v for k,v in s.items() if k not in ('initial','final_registry')} for m,s in summary.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':previous.worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
