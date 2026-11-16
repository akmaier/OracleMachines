#!/usr/bin/env python3
"""Read-only replay of a checkpoint's separately bound supplemental CNFs."""
from collections import Counter
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap as base


def check(checkpoint_path):
    started=time.perf_counter();checkpoint=base.load(checkpoint_path)
    def bound(name):
        entry=checkpoint[name]
        if base.sha(entry['path'])!=entry['sha256']:raise ValueError('Changed '+name)
        return base.load(entry['path'])
    queries=bound('supplemental_queries');proof=bound('supplemental_proof');protocol=bound('protocol')
    for path,digest in checkpoint['source_fingerprints'].items():
        if base.sha(path)!=digest:raise ValueError('Changed source '+path)
    if any(type(q['closed']) is not bool for q in queries):raise ValueError('Nonboolean coverage claim')
    roots=[q['root'] for q in queries if q['closed']]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'history';base.restore_archive(checkpoint['archive'],path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            h.db.execute('PRAGMA query_only=ON')
            with (base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')),
                  patch.object(base.split,'discover_simplification',side_effect=AssertionError('assumption'))):
                for q in queries:
                    if h._canonical(q['source'],0)[2]!=q['root']:raise ValueError('Unbound supplemental query')
                    if q['closed'] and h._load(q['root']) is None:raise ValueError('Missing positive root')
                identities={s['rule']['id'] for s in proof['steps'] if s['rule']['kind']==base.split.KIND}
                records=[]
                for identity in sorted(identities):
                    row=h.db.execute(f'SELECT payload FROM {base.split.TABLE} WHERE id=?',(identity,)).fetchone()
                    if row is None:raise ValueError('Missing split')
                    record=base.load_json(row[0])
                    if base.split.record_key(record)!=identity:raise ValueError('Unbound split')
                    records.append(record)
                replay=base.split.verify_positive(h,proof,roots,records,Counter())
        finally:
            h.close()
            if base.sha(path)!=checkpoint['archive']['database_sha256']:raise ValueError('Changed archive')
    return dict(checkpoint_sha256=base.sha(checkpoint_path),queries=len(queries),positive_roots=len(roots),
        positive_steps=len(replay.justified),split_records=len(records),no_acquisition=True,no_negative_claim=True,
        seconds=time.perf_counter()-started,checker_sha256=base.sha(__file__))


if __name__=='__main__':
    result=check(Path(sys.argv[1]));base.write(sys.argv[2],result);print(base.encode(result))
