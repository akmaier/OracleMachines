#!/usr/bin/env python3
"""Supplemental equal-budget evaluation of all four saved frontier pairs.

Chosen after the first-ranked pair left one 35-variable residual. Every pair
starts from the identical full history, with exactly one 32-admission batch.
"""
from collections import Counter
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiments.continue_cnf_transfer_split as study
from experiments.cnf_trace_reuse import read_attempt
from experiments.cnf_route_composition import compose
from experiments.cnf_expanded_coverage import owner


def run(out,parent):
    out.mkdir(exist_ok=False);frozen=study.load(parent/'frozen.json');selection=study.load(parent/'selection.json')
    frozen.update(parent_experiment=dict(path=str(parent/'report.json'),sha256=study.sha(parent/'report.json')),
        selection_sha256=study.sha(parent/'selection.json'),
        supplemental_rationale='The first ranked pair closed only one branch. Compare all saved alternatives to expose ranking errors and measure their actual acquisition costs.',
        max_batches=1,orders=[list(range(4)),list(reversed(range(4)))])
    frozen['source_fingerprints'][__file__.replace(str(Path.cwd())+'/', '')]=study.sha(__file__)
    study.write(out/'frozen.json',frozen);samples=[]
    for repeat,order in enumerate(frozen['orders']):
        for i in order:
            record=selection['ranked'][i]['record'];destination=out/f'pair-{i}-{repeat}';destination.mkdir()
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'history';tick=time.perf_counter();study.restore_archive(frozen['parent_archive'],path)
                h=study.CompleteAdmissionInventory(path,**frozen['options']);h.set_admission_budget(0)
                try:
                    old=study.rows(h)
                    with study.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('Acquisition forbidden')):
                        for key in old:assert owner(h,key)._load(key) is not None
                        study.verify(h,record,Counter())
                    startup=time.perf_counter()-tick
                    variable=read_attempt(h,record['source'],record['references'][0],Counter())['variable']
                    result=study.advance(h,record,32)
                    assert old.items()<=study.rows(h).items()
                    roots=[record['source'],frozen['original_root']]
                    closed,_=compose(h,roots,study.new_routes(h,record),Counter())
                    result.update(index=i,repeat=repeat,variable=variable,rank=selection['ranked'][i]['rank'],
                        record=record,roots=roots,closed=closed,frontier=study.frontier(h,record),startup_seconds=startup,
                        initial_patterns=len(old),row_digest=study.key_sha(study.encode(sorted(study.rows(h).items()))))
                finally:h.close()
                result['archive']=study.archive(path,destination)
                result['cold']=study.replay(path,frozen['options'],record,roots,closed)
                study.write(destination/'report.json',result)
                samples.append(dict(index=i,repeat=repeat,path=str(destination/'report.json'),sha256=study.sha(destination/'report.json')))
                print(study.json.dumps(dict(variable=variable,closed=closed,entered=result['entered'],stored=result['stored'],
                    probes=result['probes'],pending=sum(b['pending'] for b in result['branches']),
                    frontier=[l['shape'] for c in result['frontier'] for l in c.get('leaves',[])])),flush=True)
    summary=[]
    for i in range(4):
        a=[study.load(s['path']) for s in samples if s['index']==i]
        assert a[0]['row_digest']==a[1]['row_digest']
        r=a[0];leaves=[l for c in r['frontier'] for l in c.get('leaves',[])]
        summary.append(dict(index=i,variable=r['variable'],rank=r['rank'],closed=r['closed'],
            entered=r['entered'],stored=r['stored'],probes=r['probes'],
            pending=sum(b['pending'] for b in r['branches']),unresolved=len(leaves),
            shapes=[l['shape'] for l in leaves],unresolved_literals=sum(l['shape']['literals']*l['multiplicity'] for l in leaves),
            mean_startup_seconds=sum(x['startup_seconds'] for x in a)/2,
            mean_expansion_seconds=sum(x['seconds'] for x in a)/2,
            database_bytes=r['archive']['database_bytes'],compressed_bytes=r['archive']['compressed_bytes']))
    study.write(out/'report.json',dict(frozen_sha256=study.sha(out/'frozen.json'),samples=samples,summary=summary))
    print(study.json.dumps(summary),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
