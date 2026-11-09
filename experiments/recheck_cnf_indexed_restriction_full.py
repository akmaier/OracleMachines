#!/usr/bin/env python3
"""Reverse the full mode order after a mixed first total-cost result."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_indexed_restriction as study


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    # Only experiment order changes. The unchanged runner still checks every
    # previous answer/profile/archive byte and performs cold and allocation runs.
    study.MODES=dict(reversed(list(study.MODES.items())))
    study.main()
    first_dir=Path('experiments/results/cnf-indexed-restriction')
    reports=[json.loads((p/'report.json').read_text()) for p in (first_dir,args.output)]
    summaries=[json.loads((p/'summary.json').read_text()) for p in (first_dir,args.output)]
    assert reports[0]['cases']==reports[1]['cases']
    pairs={}
    for mode in ('baseline','indexed'):
        rows=[next(r for r in summary if r['mode']==mode) for summary in summaries]
        assert rows[0]['operation_metrics']==rows[1]['operation_metrics']
        assert rows[0]['archive']['storage']==rows[1]['archive']['storage']
        assert rows[0]['archive']['database_sha256']==rows[1]['archive']['database_sha256']
        pairs[mode]={k:dict(samples=[r[k] for r in rows],mean=statistics.mean(r[k] for r in rows))
                     for k in ('total_seconds','discovery_seconds','solver_seconds')}
        pairs[mode]['cold_seconds']=dict(samples=[r['archive']['audit']['seconds'] for r in rows],
            mean=statistics.mean(r['archive']['audit']['seconds'] for r in rows))
    out=dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        comparison_script_sha256=hashlib.sha256(Path(study.__file__).read_bytes()).hexdigest(),
        reports=[dict(path=str(p/'report.json'),sha256=hashlib.sha256((p/'report.json').read_bytes()).hexdigest())
                 for p in (first_dir,args.output)],
        order=['baseline','indexed','indexed','baseline'],summary=pairs,
        limitations=['Two full samples per mode balance order, but do not establish significance or industrial performance',
          'First-run regression is retained; resource variation or cache-induced process effects are not excluded',
          'Within-mode operation counters and archive hashes must repeat exactly across both full runs',
          'Each run retains separate initialization, warm/cold replay and allocation diagnostics'])
    (args.output/'order-control.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(pairs),flush=True)


if __name__=='__main__':main()
