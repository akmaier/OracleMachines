#!/usr/bin/env python3
"""Read-only validation of frozen source streams, outcomes, counts and hashes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.run_source_updates import summarize


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    path=parser.parse_args().directory
    metadata=json.loads((path/'metadata.json').read_text())
    assert digest(path/'inputs.json')==metadata['inputs_sha256']
    for name,expected in metadata['fingerprints'].items():
        assert digest(ROOT/name)==expected,('Fingerprint differs',name)
    cases=json.loads((path/'inputs.json').read_text())
    local_checks=0
    for case in cases:
        width,size=case['width'],case['size'];q=1<<width;blocks=case['layers']
        assert len(blocks)==size+1 and all(len(b)==width for b in blocks)
        ids=[v for block in blocks for v in block];assert len(ids)==len(set(ids))
        for edge,bucket in list(enumerate(case['buckets']))+[(e['edge'],e['clauses']) for e in case['edits']]:
            pairs=[]
            for x in range(q):
                for y in range(q):
                    values={v:bool(word&(1<<i)) for block,word in ((blocks[edge],x),(blocks[edge+1],y)) for i,v in enumerate(block)}
                    if all(any(values[abs(lit)]==(lit>0) for lit in clause) for clause in bucket):pairs.append((x,y))
            assert all(sum(a==x for a,b in pairs)==1 for x in range(q))
            assert all(sum(b==y for a,b in pairs)==1 for y in range(q));local_checks+=1
    runs=[json.loads(line) for line in gzip.open(path/'runs.jsonl.gz','rt')]
    assert len(runs)==48
    assert len({(r['repeat'],r['mode'],r['width'],r['size']) for r in runs})==48
    for run in runs:
        assert len(run['records'])==38
        assert run['charged_stream_ns']==run['setup_ns']+run['shutdown_ns']+sum(q['elapsed_ns'] for q in run['records'])
        assert run['worker_elapsed_ns']>=run['charged_stream_ns']
        assert run['resources']['valid_samples']>0 and run['resources']['sampled_native_peak_bytes'] is not None
        h=(run['size']-1).bit_length();cells=(1<<run['width'])**2;cap=(2*(1<<h)-1)*cells
        for record in run['records']:
            assert record['status']=='ok',record
            result=record['result'];assert result['answer']==record['expected']==(record['kind']!='negative')
            assert sum(result['phase_ns'].values())==result['wall_ns']
            if run['mode']=='source_delta' and record['kind']=='edit':
                m=result['source_updates']
                assert m['binding_visits']==m['layout_replays']==0
                assert m['patch_visits']==2*h+1
                assert m['reachability_updates']<=4*h+2
                assert m['inserted_objects']<=h+3
                assert m['native_definitions']<=h+1 and m['native_evictions']<=h+1
                assert m['native_cells']<=cap and m['peak_native_cells']<=cap+(h+1)*cells
    summary=summarize(runs)
    assert summary==json.loads((path/'summary.json').read_text())
    pilot=path.with_name('source-updates-pilot')
    assert digest(pilot/'inputs.json')==digest(path/'inputs.json')
    pilot_meta=json.loads((pilot/'metadata.json').read_text())
    assert digest(pilot/'run_source_updates.py')==pilot_meta['fingerprints']['experiments/run_source_updates.py']
    print(json.dumps(dict(runs=len(runs),queries=summary['planned'],correct=summary['completed'],
        local_bijection_checks=local_checks,unsat=sum(not q['result']['answer'] for r in runs for q in r['records']),
        fingerprints=len(metadata['fingerprints']),valid_rss_samples=summary['valid_rss_samples'],
        rss_misses=summary['rss_misses'],pilot_inputs_identical=True,source_update_bounds_passed=True),indent=2))


if __name__=='__main__':main()
