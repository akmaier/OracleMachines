#!/usr/bin/env python3
"""Read-only bounded literal discovery from the target, without core-bank scans."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_assumption_guard as study
from experiments.cnf_assumption_guard import probe
from experiments.cnf_residual_dag import FORMAT, propagate, restrict
from experiments.validate_cnf_assumption_guard import expected
from experiments.validate_cnf_unsat_support import bound
base = study.base


def run(out):
    started = time.perf_counter(); p = base.load(out / 'protocol.json')
    for f, h in p['source_fingerprints'].items(): assert base.sha(f) == h, f
    hp = bound(p['historical_protocol']); authority = bound(hp['parent']); trial = bound(p['historical_trial']); old_rows = bound(trial['queries'])
    results = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def read(entry, name):
            path = tmp / name; base.restore_archive(entry, path); s = study.previous.ResidualSolver(path)
            try: return study.previous.rows(s)
            finally: s.close()
        initial = read(authority['reference_union'], 'initial'); final = read(trial['archive'], 'final')
        prefixes = study.previous.history.partition_study.prefixes(initial, final, old_rows)
        for selected in p['targets']:
            cid = selected['case']; before = prefixes[cid]; old = next(r for r in old_rows if r['case'] == cid)
            path = tmp / 'probe'; shutil.copyfile(tmp / 'initial', path); s = study.previous.ResidualSolver(path)
            with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [(k, v) for k, v in before.items() if k not in initial])
            s.db.execute('PRAGMA query_only=ON')
            try:
                with patch.object(s, '_expand', side_effect=AssertionError('Discovery search')), patch.object(s, '_store', side_effect=AssertionError('Discovery publication')):
                    target, _, _, _, normal_counts, guard_counts = study.previous.prepare(s, hp, old)
                    preparation_counts = dict(s.counts); modes = []
                    for mode in ('original-binary', 'unit-residual-binary'):
                        phase = time.perf_counter(); s.counts = Counter(); discovery = Counter()
                        cnf, names, root = s._canonical(target); fixed, trace, conflict = propagate(cnf, discovery); assert conflict is None
                        scoring = cnf if mode == 'original-binary' else restrict(cnf, fixed, discovery)
                        binary = Counter(); discovery['ranking_clause_visits'] = len(scoring)
                        discovery['ranking_literal_visits'] = sum(map(len, scoring))
                        for c in scoring:
                            if len(c) == 2: binary.update(abs(l) for l in c)
                        remaining = {abs(l) for c in cnf for l in c} - set(fixed)
                        ranked = sorted(remaining, key=lambda v: (-binary[v], names[v - 1]))
                        candidates = [[sign * names[v - 1]] for v in ranked[:4] for sign in (-1, 1)]
                        counts = Counter(); choice, record = probe(s, target, candidates, 8, counts)
                        assert (choice, record) == expected(s, target, candidates, 8)
                        extra = {}
                        if choice is not None:
                            source = target if choice['kind'] == 'terminal' else [list(c) for c in target] + [choice['clause']]
                            normalized, _, key = s._canonical(source); screen = choice['screen']
                            assert screen['root'] == key and screen['conflict'] is not None
                            s._verify(key, dict(format=FORMAT, cnf=[list(c) for c in normalized], answer=False,
                                              proof=dict(kind='units', trace=screen['trace'], conflict=screen['conflict'])))
                            if choice['kind'] == 'guard':
                                reduced = restrict(target, {abs(l): l < 0 for l in choice['clause']}, counts)
                                child, _, child_key = s._canonical(reduced); known = s._read(child_key, child)
                                extra = dict(child_root=child_key, child_known=known is not None)
                        modes.append(dict(mode=mode, candidates=candidates, ranks=[dict(variable=names[v - 1], binary_incidence=binary[v]) for v in ranked],
                                          baseline_fixed=[[names[v - 1], bit] for v, bit in sorted(fixed.items())], choice=choice,
                                          probe=record, discovery_counts=dict(discovery), probe_counts=dict(counts), solver_counts=dict(s.counts),
                                          verification_included=True, seconds=time.perf_counter() - phase, **extra))
                    assert study.previous.rows(s) == before
                    results.append(dict(case=cid, prefix_digest=base.key_sha(base.encode(sorted(before.items()))), modes=modes,
                                        preparation_counts=preparation_counts, normal_counts=normal_counts, guard_counts=guard_counts))
            finally: s.close()
    result = dict(passed=True, no_acquisition=True, protocol=study.binding(out / 'protocol.json'),
                  source=study.binding(Path(__file__).resolve().relative_to(Path.cwd())), cases=results, seconds=time.perf_counter() - started,
                  limitations=['At most four variables, false then true, ranked by binary incidence with identifier tie break; already unit-fixed variables are excluded. Two posthoc ranking variants on the same three historical cases.',
                               'Original-prefix preparation remains charged; candidate generation uses target clauses only. Discovery propagation and the probe baseline are both paid. Independent reconstruction and native trace verification are included in diagnostic time, not a deployment timing.',
                               'No premise, child or composed result is published. New candidate child acquisition and net saving are unmeasured; a different forced variable can cost more. No excluded-query, efficient arbitrary-SAT or minimum-cost guarantee.'])
    base.write(out / 'discovery-probe.json', result)
    print(base.encode([dict(case=c['case'], modes=[dict(mode=m['mode'], choice=None if m['choice'] is None else m['choice'].get('clause'), probes=m['probe_counts'].get('assumption_premise_probes', 0), propagation_visits=m['discovery_counts'].get('propagation_literal_visits', 0) + m['probe_counts'].get('propagation_literal_visits', 0)) for m in c['modes']]) for c in results]), flush=True)


if __name__ == '__main__': run(Path(sys.argv[1]))
