#!/usr/bin/env python3
"""Compare the same source-exhaustion proof with and without history restoration."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_exhaustion_certificate import make_certificate,check_certificate
from experiments.cnf_pattern_inventory import FORMAT as PATTERN_FORMAT,encode


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(report_path,obstruction_path):
    obstruction=json.loads(obstruction_path.read_text())
    if obstruction['report_sha256']!=sha(report_path):raise ValueError('Changed report binding')
    if obstruction['portable_checker_sha256']!=sha('experiments/cnf_exhaustion_certificate.py'):
        raise ValueError('Changed portable checker')
    metadata=obstruction['certificates']
    if sha(metadata['path'])!=metadata['sha256']:raise ValueError('Changed certificate archive')
    entries=json.loads(gzip.decompress(Path(metadata['path']).read_bytes()))
    expected={row['source'] for row in obstruction['rows'] if row['exhausted']}
    if not entries or len(entries)!=len(expected) or {row['source'] for row in entries}!=expected:
        raise ValueError('Incorrect source set')
    for row in entries:
        if set(row)!={'source','certificate'}:raise ValueError('Invalid bound certificate entry')
        key=json.loads(row['source'])
        if type(key) is not list or len(key)!=4 or key[0]!=PATTERN_FORMAT:
            raise ValueError('Unexpected source key')
        if encode(key[-1])!=encode(row['certificate']['cnf']):raise ValueError('Changed source formula')
    return obstruction,entries


def replay(mode,report_path,obstruction_path):
    started=time.perf_counter();obstruction,entries=load(report_path,obstruction_path)
    loading_seconds=time.perf_counter()-started;counts=Counter();rows=[];restoration=0.0;history_bytes=0
    if mode=='history':
        from experiments.continue_cnf_reuse_frontier import restore_checkpoint
        from experiments.cnf_coupled_pivots import BudgetedInventory
        from experiments.cnf_trace_reuse import source_attempts
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td);path=tmp/'history';before=time.perf_counter()
            restore_checkpoint(report_path,path,tmp);restoration=time.perf_counter()-before
            history_bytes=path.stat().st_size;digest=sha(path);before=time.perf_counter()
            h=BudgetedInventory(path,**json.loads(report_path.read_text())['options']);h.set_admission_budget(0)
            with patch.object(h,'_discover',side_effect=AssertionError('new recognition')):
                for row in entries:
                    cnf=h._load(row['source'])['cnf'];attempts,_=source_attempts(h,row['source'],counts)
                    certificate=make_certificate(cnf,attempts)
                    if encode(certificate)!=encode(row['certificate']):raise ValueError('Different retained proof')
                    rows.append(dict(source_sha256=hashlib.sha256(row['source'].encode()).hexdigest(),
                        **check_certificate(certificate,expected_cnf=cnf,counts=counts)))
            assert not h.admitted;h.close();checking=time.perf_counter()-before;assert sha(path)==digest
    else:
        before=time.perf_counter()
        for row in entries:
            cnf=json.loads(row['source'])[-1]
            rows.append(dict(source_sha256=hashlib.sha256(row['source'].encode()).hexdigest(),
                **check_certificate(row['certificate'],expected_cnf=cnf,counts=counts)))
        checking=time.perf_counter()-before
    return dict(mode=mode,rows=rows,counts=dict(counts),loading_seconds=loading_seconds,
        restore_seconds=restoration,checking_seconds=checking,seconds=time.perf_counter()-started,
        history_database_bytes=history_bytes,certificate_bytes=obstruction['certificates']['bytes'],
        certificate_compressed_bytes=obstruction['certificates']['compressed_bytes'],new_discovery=False)


def compare(report_path,obstruction_path,out):
    started=time.perf_counter();samples=[]
    for repeat in range(2):
        for mode in (('history','compact') if repeat%2==0 else ('compact','history')):
            before=time.perf_counter()
            process=subprocess.run([sys.executable,str(Path(__file__)),'replay',mode,str(report_path),str(obstruction_path)],
                capture_output=True,text=True,check=True)
            sample=json.loads(process.stdout);sample.update(repeat=repeat,process_wall_seconds=time.perf_counter()-before)
            if samples and sample['rows']!=samples[0]['rows']:raise ValueError('Different exhaustion conclusions')
            samples.append(sample)
            print(json.dumps(dict(mode=mode,repeat=repeat,seconds=sample['process_wall_seconds'])),flush=True)
    obstruction=json.loads(obstruction_path.read_text())
    result=dict(format='source-exhaustion-replay-comparison-v1',report_sha256=sha(report_path),
        obstruction_sha256=sha(obstruction_path),fingerprints={p:sha(p) for p in (
            'experiments/cnf_exhaustion_certificate.py','experiments/compare_cnf_exhaustion_replay.py',
            'solver/test_cnf_exhaustion_certificate.py')},samples=samples,
        packing_seconds=obstruction['packing_seconds'],certificate=obstruction['certificates'],
        pipeline_seconds=time.perf_counter()-started,
        limitations=['One reused development residual; two fresh processes per mode, balanced order, OS caches not flushed.',
            'Process wall timers include Python startup, imports and teardown. In-process timers are also recorded.',
            'Compact mode verifies only the stated unit-refutation obstruction on the explicit source formula, not inventory coverage, ancestry, paired rewrites or SAT/UNSAT.',
            'History mode restores and validates inherited data, then reconstructs the identical retained proof. Compact replay requires the previously exported source-bound proof; export is charged separately.',
            'The full history is preserved. Reconstructed database size is disk space, not peak RAM; peak RAM and general runtime bounds are unmeasured.'])
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('replay');a.add_argument('mode',choices=('history','compact'));a.add_argument('report',type=Path);a.add_argument('obstruction',type=Path)
    a=sub.add_parser('compare');a.add_argument('report',type=Path);a.add_argument('obstruction',type=Path);a.add_argument('output',type=Path)
    a=p.parse_args()
    if a.command=='replay':print(json.dumps(replay(a.mode,a.report,a.obstruction)))
    else:compare(a.report,a.obstruction,a.output)
