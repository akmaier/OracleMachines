#!/usr/bin/env python3
"""Charge initial hashing and refresh across a real, already checked append.

This isolates digest bookkeeping; it does not time fresh expansion or claim an
end-to-end gain from guarded reuse. Inputs are bound to the comparison report.
"""
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_guarded_digests import BASE, restore_base, sha, digests, unpack
from experiments.compare_cnf_probe_continuation import TABLES
from experiments.cnf_digest_worker import full_snapshot
from experiments.cnf_guarded_digests import GuardedDigests


def append_on_owned_connection(db, delta):
    source=sqlite3.connect(f'file:{delta}?mode=ro',uri=True)
    try:
        with db:
            for table in TABLES:
                for key,payload in source.execute(f'SELECT id,payload FROM {table} ORDER BY rowid'):
                    old=db.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()
                    if old is not None and old!=(payload,):raise ValueError('Conflicting append')
                    db.execute(f'INSERT OR IGNORE INTO {table} VALUES (?,?)',(key,payload))
    finally:source.close()


def run(out):
    started=time.perf_counter(); report=json.loads((out/'report.json').read_text())
    for path,digest in report['fingerprints'].items():assert sha(path)==digest
    assert Path(report['parent']['path'])==BASE and sha(BASE)==report['parent']['sha256']
    result=dict(report_sha256=sha(out/'report.json'),repeats=3,arms=[],
        fingerprint=sha(__file__),limitations=[
            'Replay of the exact saved append; fresh discovery, route maintenance and coverage are excluded from this isolated timing.',
            'Initial full hashing, file copy, append and refresh are included in each sequence; reconstruction and independent audit are reported separately.',
            'The additional unchanged snapshot measures an idle-read opportunity, not an extra expansion step.',
            'Three reversed-order repetitions share OS caches and do not establish a general speedup or peak-RAM bound.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); tick=time.perf_counter()
        parent,*_=restore_base(BASE,tmp/'seed',tmp)
        result['restore_seconds']=time.perf_counter()-tick
        assert digests(tmp/'seed')==report['seed_table_digests']
        delta=report['delta'];assert sha(delta['path'])==delta['sha256']
        unpack(delta['path'],tmp/'delta',delta['database_sha256'])
        with sqlite3.connect(tmp/'delta') as db:
            added={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES}
        result['added_rows']=added
        result['seed_sha256']=sha(tmp/'seed')
        for repeat in range(result['repeats']):
            for mode in (('full','guarded') if repeat%2==0 else ('guarded','full')):
                sequence=time.perf_counter();history=tmp/f'{repeat}-{mode}'
                tick=time.perf_counter();shutil.copyfile(tmp/'seed',history);copy_seconds=time.perf_counter()-tick
                db=sqlite3.connect(history)
                try:
                    cache=GuardedDigests(db) if mode=='guarded' else None
                    snapshot=cache.snapshot if cache else lambda:full_snapshot(db)
                    initial,initial_cost=snapshot()
                    assert initial==report['seed_table_digests']
                    tick=time.perf_counter();append_on_owned_connection(db,tmp/'delta');append_seconds=time.perf_counter()-tick
                    current,refresh_cost=snapshot()
                    assert current==report['logical_table_digests']
                    if cache:
                        assert refresh_cost['added_rows']==added
                        assert set(refresh_cost['scanned_tables'])=={t for t,n in added.items() if n}
                    work_seconds=time.perf_counter()-sequence
                    same,idle_cost=snapshot();assert same==current
                    if cache:assert not idle_cost['scanned_tables']
                    total_seconds=time.perf_counter()-sequence
                finally:db.close()
                # Independent new-connection full scan is outside the timed arm.
                tick=time.perf_counter();assert digests(history)==current
                audit_seconds=time.perf_counter()-tick
                row=dict(repeat=repeat,mode=mode,copy_seconds=copy_seconds,
                    initial=initial_cost,append_seconds=append_seconds,refresh=refresh_cost,idle=idle_cost,
                    work_seconds=work_seconds,total_seconds=total_seconds,audit_seconds=audit_seconds)
                result['arms'].append(row)
                print(json.dumps(dict(repeat=repeat,mode=mode,work_seconds=work_seconds,
                    refresh_seconds=refresh_cost['seconds'],idle_seconds=idle_cost['seconds'])),flush=True)
        assert sha(tmp/'seed')==result['seed_sha256']
    result.update(passed=True,seconds=time.perf_counter()-started)
    (out/'digest-refresh.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':run(Path(sys.argv[1]))
