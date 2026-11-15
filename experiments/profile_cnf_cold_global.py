#!/usr/bin/env python3
"""Attribute complete cold global checking on the saved frontier without discovery."""
import cProfile
import json
from pathlib import Path
import pstats
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_copyless_sequence import (
    restore_checkpoint, BudgetedInventory, read_archive, sha, digests, FILES)
from experiments.cnf_expansion_session import ExpansionSession
from experiments.cnf_session_query import query

BASE = Path('experiments/results/cnf-copyless-sequence/report.json')


def profiled(out, name, action):
    profiler = cProfile.Profile()
    tick = time.perf_counter()
    profiler.enable()
    try:
        result = action()
    finally:
        profiler.disable()
    seconds = time.perf_counter() - tick
    profiler.dump_stats(str(out / (name + '.pstats')))
    stats = pstats.Stats(profiler)
    functions = []
    for (file, line, function), (primitive, calls, own, cumulative, _) in stats.stats.items():
        functions.append(dict(file=file, line=line, function=function,
            primitive_calls=primitive, calls=calls, own_seconds=own,
            cumulative_seconds=cumulative))
    with (out / (name + '.txt')).open('w') as stream:
        pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats('cumulative').print_stats(45)
    return result, dict(seconds=seconds,
        functions=sorted(functions, key=lambda row: -row['cumulative_seconds']))


def run(out):
    out.mkdir(exist_ok=False)
    start = time.perf_counter()
    r = dict(parent=dict(path=str(BASE), sha256=sha(BASE)),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        fingerprints={p:sha(p) for p in ['experiments/profile_cnf_cold_global.py', *FILES]})
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); history = tmp / 'history'; tick = time.perf_counter()
        parent, *evidence = restore_checkpoint(BASE, history, tmp)
        r['restore_seconds'] = time.perf_counter() - tick
        before = sha(history); bridges = read_archive(parent['bridges'])
        print(json.dumps(dict(restored=True, seconds=r['restore_seconds'])), flush=True)
        with patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('new discovery')):
            h = BudgetedInventory(history, **parent['options']); h.set_admission_budget(0)
            try:
                session, r['construction'] = profiled(out, 'construction', lambda: ExpansionSession(h, evidence, bridges))
                r['construction_cache'] = dict(checked=len(h.checked), prepared=len(h.prepared.checked))
                roots = [h._canonical(c['source'], h.config['max_depth'])[2] for c in parent['cases']]
                (result, selected, plans), r['query'] = profiled(out, 'query', lambda: query(session, evidence, bridges, roots))
                assert result['closed'] == [parent['final_closed'], parent['without_growth_closed']]
                assert selected == read_archive(parent['next_selection'])
                assert plans[0] == read_archive(parent['certificate'])
                assert not h.admitted and h.db.total_changes == 0
                r.update(covered=sum(result['closed'][0]), queries=result,
                    next_selection_matches=True, certificate_matches=True,
                    inventory_counts=dict(h.counts), prepared_counts=dict(h.prepared.counts))
            finally:
                h.close()
        assert sha(history) == before and digests(history) == parent['logical_table_digests']
        r.update(database_unchanged=True, database_sha256=before, database_bytes=history.stat().st_size)
    r.update(seconds=time.perf_counter()-start,
        scope='One instrumented cold construction and complete global query on the unchanged checkpoint. No acquisition or new coverage. cProfile times are diagnostic; cumulative times overlap and cannot be summed. No comparative speedup is established.')
    (out/'report.json').write_text(json.dumps(r, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(covered=r['covered'], construction=r['construction']['seconds'], query=r['query']['seconds'], seconds=r['seconds'])), flush=True)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
