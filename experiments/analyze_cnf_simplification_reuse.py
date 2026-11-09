#!/usr/bin/env python3
"""Observe checker inputs without changing acceptance; not a timing benchmark."""
from collections import Counter, OrderedDict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_indexed_restriction_inventory import IndexedRestrictionInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_simplification import check_simplification


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    input_path = Path('experiments/results/cnf-indexed-restriction/report.json')
    report = json.loads(input_path.read_text())
    reference = {r['case']: r for r in report['records'] if r['mode'] == 'indexed'}
    indices = [858, 875, 907, 970, 1042, 1061, 1194, 977, 1044, 1185, 1289, 1368]
    rows = []
    for i in indices:
        totals = Counter(); callers = Counter(); objects = {}; clauses = {}
        sources = set(); checks = set(); caches = {n: OrderedDict() for n in (65536, 262144, 1048576)}
        sizes = Counter(); simulated = {n: Counter() for n in caches}
        pending = {}
        def observe(frame, event, result):
            if frame.f_code is not check_simplification.__code__:
                return
            if event == 'call':
                local = frame.f_locals; cnf = local['cnf']; cert = local['certificate']
                totals['calls'] += 1; callers[frame.f_back.f_code.co_name] += 1
                literals = sum(map(len, cnf)); totals['input_literals'] += literals
                totals['input_clauses'] += len(cnf)
                totals['unit_assignments'] += len(cert['units'])
                totals['conflicts'] += cert['conflict'] is not None
                totals['empty_unit_traces'] += not cert['units']
                totals['no_unit_reconstruction_literals'] += literals if not cert['units'] and cert['conflict'] is None else 0
                totals['pure_rounds'] += len(cert['pure_rounds'])
                totals['same_source_object_calls'] += id(cnf) in objects
                objects[id(cnf)] = cnf
                for clause in cnf:
                    totals['repeated_clause_object_positions'] += id(clause) in clauses
                    clauses[id(clause)] = clause
                source = encode(cnf); sources.add(source)
                key = encode([cnf, cert, local['units'], local['pure']])
                totals['key_bytes'] += len(key)
                totals['repeated_exact_checks'] += key in checks; checks.add(key)
                pending[id(frame)] = (key, literals)
            elif event == 'return':
                key, literals = pending.pop(id(frame))
                if result is None:
                    totals['exceptions'] += 1
                    return
                target, fixed = result; saved = encode([target, sorted(fixed.items())])
                weight = len(key) + len(saved)
                for limit, cache in caches.items():
                    stats = simulated[limit]
                    if key in cache:
                        stats['hits'] += 1; stats['hit_input_literals'] += literals
                        cache.move_to_end(key)
                    else:
                        stats['misses'] += 1
                        if weight > limit:
                            stats['oversize'] += 1
                            continue
                        while sizes[limit] + weight > limit:
                            _, old = cache.popitem(last=False); sizes[limit] -= old
                            stats['evictions'] += 1
                        cache[key] = weight; sizes[limit] += weight
                        stats['admissions'] += 1
        with tempfile.TemporaryDirectory() as tmp:
            h = IndexedRestrictionInventory(Path(tmp)/'history.db', max_depth=2, probe_limit=4, learn_limit=4)
            sys.setprofile(observe)
            try:
                found = h.inspect(report['cases'][i]['source'])
            finally:
                sys.setprofile(None)
            expected = reference[i]['discovery']
            assert found['summary'] == expected['summary']
            assert encode(found['profile']) == encode(expected['profile'])
            assert hashlib.sha256(found['root']['key'].encode()).hexdigest() == expected['root_hash']
            h.close()
        rows.append(dict(case=i, totals=dict(totals), callers=dict(callers), distinct_sources=len(sources),
                         distinct_objects=len(objects), distinct_clause_objects=len(clauses),
                         distinct_checks=len(checks), simulated_caches=simulated))
    result = dict(rows=rows, indices=indices,
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        input_report_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitations=['Instrumented observer retains inputs and serializes full keys; no timing or memory claims',
          'Simulated cache does not establish a safe implementation or charge lookup, guard and decoding overhead',
          'Original checker still accepts every result; profiles, roots and summaries match the saved corpus',
          'Selected twelve sources, not full-corpus coverage or a new tractable SAT class'])
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(rows[6], indent=2), flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]))
