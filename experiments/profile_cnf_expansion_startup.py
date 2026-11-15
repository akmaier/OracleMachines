#!/usr/bin/env python3
"""Separate startup costs on the retained append-export checkpoint, without solving."""
from collections import Counter
import copy
import cProfile
import json
from pathlib import Path
import pstats
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_append_export import (
    restore_checkpoint, BudgetedInventory, routes_for, full, sha, digests,
    read_archive, checked_inventory, FILES)
from experiments.cnf_pattern_activation import PatternActivationMaintenance
from experiments.cnf_append_delta import AppendDelta

BASE = Path('experiments/results/cnf-append-export-checked/report.json')


def run(out):
    out.mkdir(exist_ok=False); start=time.perf_counter()
    report=dict(parent=dict(path=str(BASE),sha256=sha(BASE)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={p:sha(p) for p in [__file__,*FILES]},samples=[])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); seed=tmp/'seed'; tick=time.perf_counter()
        parent,*evidence=restore_checkpoint(BASE,seed,tmp)
        report['restore_seconds']=time.perf_counter()-tick
        bridges=read_archive(parent['bridges']); root=parent['source']; before=sha(seed)
        for repeat in range(2):
            row=dict(repeat=repeat,profiled=bool(repeat)); started=time.perf_counter()
            history=tmp/f'history-{repeat}'; tick=time.perf_counter(); shutil.copyfile(seed,history)
            row['clone_seconds']=time.perf_counter()-tick; tick=time.perf_counter()
            assert digests(seed)==parent['logical_table_digests']
            row['seed_digests_seconds']=time.perf_counter()-tick; tick=time.perf_counter()
            h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
            row['inventory_open_seconds']=time.perf_counter()-tick
            try:
                tick=time.perf_counter(); saved=copy.deepcopy(evidence[3]); ev=copy.deepcopy(evidence); bs=copy.deepcopy(bridges)
                row['sidecar_copy_seconds']=time.perf_counter()-tick; tick=time.perf_counter()
                boundary=AppendDelta(h.db)
                row['export_boundary_seconds']=time.perf_counter()-tick
                profiler=cProfile.Profile(); tick=time.perf_counter()
                if repeat:profiler.enable()
                maintained=PatternActivationMaintenance(h,ev,bs,routes_for)
                if repeat:profiler.disable()
                row['checked_routes_seconds']=time.perf_counter()-tick; tick=time.perf_counter()
                closed,plans,_=full(h,[root],maintained.routes)
                row['focus_coverage_seconds']=time.perf_counter()-tick
                assert closed[0]==[False] and not h.admitted and h.db.total_changes==boundary.changes
                row['preparation_seconds']=time.perf_counter()-started
                row['index']=maintained.statistics(); row['checked_inventory']=checked_inventory(h)[1]
                row['inventory_counts']=dict(h.counts)
                if repeat:
                    profiler.dump_stats(str(out/'route-startup.pstats'))
                    with (out/'route-startup.txt').open('w') as f:
                        pstats.Stats(profiler,stream=f).strip_dirs().sort_stats('cumulative').print_stats(55)
                print(json.dumps({k:v for k,v in row.items() if k.endswith('_seconds')}),flush=True)
                report['samples'].append(row)
            finally:h.close()
            assert sha(history)==before
        assert sha(seed)==before
        report['seed_database_sha256']=before;report['seed_bytes']=seed.stat().st_size
    report['seconds']=time.perf_counter()-start
    report['scope']='Two startup samples, second instrumented only during route construction. No fresh acquisition, persistence delta or coverage change. cProfile timings are diagnostic, not performance-comparison measurements.'
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':run(Path(sys.argv[1]))
