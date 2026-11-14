#!/usr/bin/env python3
"""Export one positive data bundle, then compare complete cold preparation/replay.

Each timed sample runs in a new process. Bundle workers run outside the repo and
receive only the bundle and an independent requested-claim file, plus checker
code. The old lineage is needed for production and full controls, never replay.
"""
from collections import Counter
from contextlib import ExitStack,contextmanager
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_positive_primitives import verify_positive
from experiments.cnf_positive_bundle import collect_bundle,replay_bundle,bound_roots
from experiments.cnf_expanded_coverage import checked_inventory
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_trace_reuse import archive_json,read_archive
from experiments.compare_cnf_probe_continuation import sha,digests

PARENT=Path('experiments/results/cnf-reused-branch/report.json')
PREVIOUS=Path('experiments/results/cnf-positive-primitives/report.json')
EXPANDED=Path('experiments/results/cnf-expanded-coverage/report.json')
FILES=['experiments/cnf_positive_bundle.py','experiments/compare_cnf_positive_bundle.py',
       'solver/test_cnf_positive_bundle.py']


@contextmanager
def no_discovery():
    with ExitStack() as stack:
        stack.enter_context(patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('new recognition')))
        for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes',
                     'experiments.cnf_learning_continuation.discover_equivalence_probes',
                     'experiments.cnf_affine_clause.discover'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        yield


def full_worker(claim):
    from experiments.continue_cnf_reused_branch import restore_checkpoint
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history'
        parent,*evidence=restore_checkpoint(PARENT,path,tmp)
        assert encode(parent['options'])==encode(claim['options'])
        sources=[parent['cases'][i]['source'] for i in claim['case_indices']]
        assert encode(sources)==encode(claim['sources'])
        proof=read_archive(json.loads(EXPANDED.read_text())['expanded_certificate'])
        h=BudgetedInventory(path,**claim['options']);h.set_admission_budget(0)
        h.db.execute('PRAGMA query_only=ON');claimed=bound_roots(h,sources)
        prepared=time.perf_counter();counts=Counter()
        with no_discovery():verify_positive(h,proof,claimed,evidence,counts)
        replayed=time.perf_counter();_,accounting=checked_inventory(h)
        result=dict(preparation_seconds=prepared-started,replay_seconds=replayed-prepared,
            temporary_database_bytes=path.stat().st_size,roots=len(claimed),steps=len(proof['steps']),
            historical=accounting,counts=dict(counts),evidence_counts=[len(x) for x in evidence])
        assert not h.admitted;h.close()
    result['operation_seconds']=time.perf_counter()-started
    return result


def bundle_worker(bundle_path,claim):
    started=time.perf_counter()
    bundle=json.loads(gzip.decompress(bundle_path.read_bytes()))
    loaded=time.perf_counter()
    # Fail if a future consumer accidentally starts consulting the old lineage.
    with no_discovery(),patch('experiments.continue_cnf_reused_branch.restore_checkpoint',
                              side_effect=AssertionError('lineage restore during bundle replay')):
        result=replay_bundle(bundle,claim['sources'],claim['options'])
    result['bundle_load_seconds']=loaded-started
    result['operation_seconds']=time.perf_counter()-started
    result['evidence_counts']=[len(x) for x in bundle['evidence']]
    return result


def run(out):
    from experiments.continue_cnf_reused_branch import restore_checkpoint
    started=time.perf_counter();out.mkdir(exist_ok=False)
    r=dict(format='positive-bundle-study-v1',
        parent=dict(path=str(PARENT),sha256=sha(PARENT)),
        previous_study=dict(path=str(PREVIOUS),sha256=sha(PREVIOUS)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={p:sha(p) for p in FILES},limitations=[
            'A self-contained positive-proof data bundle, not a complete discovery catalog, archive audit or expansion checkpoint.',
            'All five sidecar lists are retained, including unused records; no minimum-size or portable-checker-code claim.',
            'The unchanged original archive is retained; the bundle adds storage while reducing the data needed for this replay.',
            'No active open-frontier dependencies or new structural coverage are added in this experiment.',
            'Two repetitions in reversed order, new processes but shared operating-system caches; no confidence interval.',
            'No peak-RAM measurement. Logical payload and temporary SQLite size are not total process memory.',
            'Every consumer semantically verifies the data again; no persisted validation cache or warm-replay repair.',
            'Capture and compression are paid by the producer; historical restoration is still required to produce the first bundle.',
            'The claims are the same 58/83 adaptively reused development inputs, not a fresh holdout or unrestricted SAT guarantee.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history';tick=time.perf_counter()
        parent,*evidence=restore_checkpoint(PARENT,path,tmp)
        r['producer_restore_seconds']=time.perf_counter()-tick
        r['inventory_sha256']=sha(path);r['logical_table_digests']=digests(path)
        assert r['logical_table_digests']==parent['logical_table_digests']
        r['original_database_bytes']=path.stat().st_size
        previous=json.loads(EXPANDED.read_text());proof=read_archive(previous['expanded_certificate'])
        claim=dict(sources=[c['source'] for c,closed in zip(parent['cases'],parent['final_closed'],strict=True) if closed],
            options=parent['options'],case_indices=[i for i,c in enumerate(parent['final_closed']) if c],
            scope='positive-proof-only')
        claims_path=out/'claims.json';claims_path.write_text(encode(claim)+'\n')
        r['claims']=dict(path=str(claims_path),sha256=sha(claims_path),bytes=claims_path.stat().st_size)
        h=BudgetedInventory(path,**parent['options']);h.set_admission_budget(0);h.db.execute('PRAGMA query_only=ON')
        tick=time.perf_counter();counts=Counter()
        with no_discovery():bundle,reads=collect_bundle(h,proof,claim['sources'],parent['options'],evidence,counts)
        r['capture_seconds']=time.perf_counter()-tick;r['capture_counts']=reads;r['proof_counts']=dict(counts)
        r['historical']=checked_inventory(h)[1];h.close()
        r['row_counts']={t:len(rows) for t,rows in bundle['rows'].items()}
        r['logical_row_bytes']={t:dict(keys=sum(len(k.encode()) for k,v in rows),
             payloads=sum(len(v.encode()) for k,v in rows)) for t,rows in bundle['rows'].items()}
        r['evidence_counts']=[len(x) for x in evidence]
        r['evidence_json_bytes']=len(encode(evidence).encode())
        tick=time.perf_counter();r['bundle']=archive_json(out/'positive-bundle.json.gz',bundle)
        r['serialization_compression_seconds']=time.perf_counter()-tick
        assert sha(path)==r['inventory_sha256'] and digests(path)==r['logical_table_digests']
        r['history_bytes_unchanged']=True
        print(json.dumps(dict(phase='bundle exported',rows=r['row_counts'],bundle=r['bundle'],capture_seconds=r['capture_seconds'])),flush=True)
        # Both independent modes run in fresh Python processes. Only the full
        # worker starts in the repo; bundle workers cannot resolve old paths.
        samples=[]
        for repeat,order in enumerate((('full','bundle'),('bundle','full'))):
            for mode in order:
                print(json.dumps(dict(repeat=repeat,mode=mode,phase='fresh process')),flush=True)
                command=[sys.executable,str(Path(__file__).resolve()),'--worker',mode,
                    '--claims',str(claims_path.resolve())]
                if mode=='bundle':command+=['--input',str(Path(r['bundle']['path']).resolve())]
                tick=time.perf_counter()
                process=subprocess.run(command,cwd=ROOT if mode=='full' else tmp,text=True,capture_output=True)
                elapsed=time.perf_counter()-tick
                if process.returncode:
                    (out/f'failed-{mode}-{repeat}.txt').write_text(process.stdout+process.stderr)
                    raise RuntimeError('Fresh worker failed; preserved its output')
                sample=json.loads(process.stdout);sample.update(mode=mode,repeat=repeat,process_seconds=elapsed)
                assert sample['roots']==58 and sample['steps']==2748 and sample['historical']==r['historical']
                assert sample['evidence_counts']==r['evidence_counts']
                if mode=='bundle':assert sample['rows']==r['row_counts']
                samples.append(sample)
                print(json.dumps({k:sample[k] for k in ('mode','preparation_seconds','replay_seconds','operation_seconds','process_seconds','temporary_database_bytes')}),flush=True)
        r['samples']=samples
        r['summary']={mode:{key:sum(s[key] for s in samples if s['mode']==mode)/2
            for key in ('preparation_seconds','replay_seconds','operation_seconds','process_seconds','temporary_database_bytes')}
            for mode in ('full','bundle')}
        r['process_reduction_fraction']=1-r['summary']['bundle']['process_seconds']/r['summary']['full']['process_seconds']
        r['no_fresh_discovery']=True;r['bundle_replays_without_lineage']=True
    r['pipeline_seconds']=time.perf_counter()-started
    (out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(summary=r['summary'],pipeline_seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path,nargs='?')
    p.add_argument('--worker',choices=('full','bundle'));p.add_argument('--claims',type=Path);p.add_argument('--input',type=Path)
    a=p.parse_args()
    if a.worker:
        claim=json.loads(a.claims.read_text())
        result=full_worker(claim) if a.worker=='full' else bundle_worker(a.input,claim)
        print(json.dumps(result))
    else:run(a.output)
