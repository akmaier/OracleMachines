#!/usr/bin/env python3
"""Read-only causal support and single-assumption probes at original prefixes."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import json, shutil, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditioned_core as study
from experiments.cnf_causal_support import slice_trace
from experiments.cnf_residual_dag import FORMAT, propagate, restrict
from experiments.validate_cnf_unsat_support import bound
base = study.base


def checked_slice(s, source, node):
    cnf, names, root = s._canonical(source)
    s._verify(root, node)
    proof = node['proof']
    assert proof['kind'] == 'units' and proof.get('conflict') is not None
    counts = Counter()
    needed = {abs(l) for l in cnf[proof['conflict']]}
    trace = slice_trace(cnf, proof['trace'], needed, counts)
    sliced = deepcopy(node)
    sliced['proof']['trace'] = trace
    s._verify(root, sliced)
    ids = sorted({proof['conflict']} | {cid for _, cid in trace})
    support = [[(1 if l > 0 else -1) * names[abs(l) - 1] for l in cnf[i]] for i in ids]
    return dict(root=root, trace=trace, conflict=proof['conflict'], support=support,
                full_trace_steps=len(proof['trace']), counts=dict(counts))


def run(out):
    start = time.perf_counter()
    p = base.load(out / 'protocol.json')
    for f, h in p['source_fingerprints'].items():
        assert base.sha(f) == h, f
    hp = bound(p['historical_protocol'])
    authority = bound(hp['parent'])
    trial = bound(p['historical_trial'])
    old_rows = bound(trial['queries'])
    results = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def read(entry, name):
            path = tmp / name
            base.restore_archive(entry, path)
            s = study.ResidualSolver(path)
            try:
                return study.rows(s)
            finally:
                s.close()
        initial = read(authority['reference_union'], 'initial')
        final = read(trial['archive'], 'final')
        prefixes = study.history.partition_study.prefixes(initial, final, old_rows)
        for selected in p['targets']:
            cid = selected['case']
            old = next(r for r in old_rows if r['case'] == cid)
            before = prefixes[cid]
            path = tmp / 'probe'
            shutil.copyfile(tmp / 'initial', path)
            s = study.ResidualSolver(path)
            with s.db:
                s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',
                                [(k, v) for k, v in before.items() if k not in initial])
            s.db.execute('PRAGMA query_only=ON')
            try:
                with patch.object(s, '_expand', side_effect=AssertionError('Probe search')), \
                     patch.object(s, '_store', side_effect=AssertionError('Probe publication')):
                    target, _, _, _, ordinary_counts, guard_counts = study.prepare(s, hp, old)
                    report_path = out / f'{cid}-direct-forward/report.json'
                    report = base.load(report_path)
                    assert report['prefix_digest'] == base.key_sha(base.encode(sorted(before.items())))
                    record = bound(report['records'])[0]
                    delta = dict(bound(report['delta']))
                    source = [list(c) for c in target] + selected['missing']
                    node = json.loads(delta[record['stronger_root']])
                    sliced = checked_slice(s, source, node)
                    members = {tuple(sorted(c)) for c in target}
                    assumptions = [c for c in sliced['support'] if tuple(sorted(c)) not in members]
                    assert {tuple(sorted(c)) for c in assumptions} <= {tuple(sorted(c)) for c in selected['missing']}
                    sliced['used_assumptions'] = assumptions
                    sliced['target_support'] = [c for c in sliced['support'] if tuple(sorted(c)) in members]
                    probes = []
                    for clause in selected['missing']:
                        source = [list(c) for c in target] + [clause]
                        cnf, _, root = s._canonical(source)
                        counts = Counter()
                        fixed, trace, conflict = propagate(cnf, counts)
                        result = dict(assumption=clause, root=root, trace=trace, conflict=conflict,
                                      counts=dict(counts), unit_refuted=conflict is not None)
                        if conflict is not None:
                            node = dict(format=FORMAT, cnf=[list(c) for c in cnf], answer=False,
                                        proof=dict(kind='units', trace=trace, conflict=conflict))
                            result['support'] = checked_slice(s, source, node)
                            # If T AND C is false, every model of T falsifies C.
                            assignment = {abs(l): l < 0 for l in clause}
                            child = restrict(target, assignment, counts)
                            child_cnf, _, child_root = s._canonical(child)
                            saved = s._read(child_root, child_cnf)
                            result.update(remaining_root=child_root, remaining_known=saved is not None,
                                          remaining_answer=None if saved is None else saved['answer'])
                        result['counts'] = dict(counts)
                        probes.append(result)
                    assert study.rows(s) == before
                    results.append(dict(case=cid, report=study.binding(report_path), prefix_digest=report['prefix_digest'],
                                        premise_slice=sliced, single_assumptions=probes, solver_counts=dict(s.counts),
                                        ordinary_counts=ordinary_counts, guard_counts=guard_counts))
            finally:
                s.close()
    result = dict(protocol=study.binding(out / 'protocol.json'), source=study.binding(Path(__file__).resolve().relative_to(Path.cwd())),
                  passed=True, no_acquisition=True, cases=results, seconds=time.perf_counter() - start,
                  limitation='Posthoc read-only proposals on three selected historical prefixes. Native verification checks every refutation and sliced trace, but no new premise or remaining-child proof is published. Single-assumption propagation failure proves nothing about satisfiability or entailment. No minimum-support, fresh-input, selector-cost or runtime improvement claim.')
    base.write(out / 'assumption-reduction-probe.json', result)
    print(base.encode([dict(case=r['case'], used_assumptions=r['premise_slice']['used_assumptions'],
                           single_unit_refutations=[p['assumption'] for p in r['single_assumptions'] if p['unit_refuted']])
                       for r in results]), flush=True)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
