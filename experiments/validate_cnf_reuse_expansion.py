#!/usr/bin/env python3
"""Reproduce frozen budget outcomes, target-only replay and immutable lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import gzip, json, re, statistics, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_reuse_expansion as s
from experiments.audit_cnf_reuse_expansion import assert_prefix


def clean(case):
    return {k: v for k, v in case.items() if k not in ('acquisition_seconds', 'checking_seconds')}


def replay(out, mode):
    p = s.load(out / 'protocol.json'); counts = Counter(); answers = {}
    with patch.object(s.e, 'search', side_effect=AssertionError), patch.object(s.e, 'expand', side_effect=AssertionError), patch.object(s.e.selective, 'transport', side_effect=AssertionError), patch.object(s.e.baseline, 'search', side_effect=AssertionError):
        for row in s.source_rows(p):
            if row['expansion_case']:
                answers[row['id']] = s.check(row['source'], s.load(out / (mode + '-0') / (row['id'] + '.json')), counts)['answer']
    report = s.load(out / (mode + '-0') / 'report.json')
    assert dict(counts) == report['warm_counts']
    assert answers == {case['id']: case['result']['answer'] for case in report['cases']}
    s.write(out / ('replay-' + mode + '.json'), dict(passed=True, mode=mode, answers=answers, counts=dict(counts), search_disabled=True, transport_disabled=True))


def validate(out):
    started = time.perf_counter(); p = s.load(out / 'protocol.json'); parent = s.bound(p['parent'])
    pv = s.load(s.PARENT / 'validation.json'); manifests = deepcopy(pv['parent_manifests'])
    mp = Path(p['parent_manifest']['path']); s.bound(p['parent_manifest'])
    manifests[str(mp)] = dict(sha256=s.sha(mp), artifacts_checked=len(s.load(mp)['artifacts']))
    artifacts = 0
    for path, entry in manifests.items():
        assert s.sha(path) == entry['sha256'], path
        entries = s.load(path)['artifacts']; assert len(entries) == entry['artifacts_checked']
        for file, h in entries.items(): assert s.sha(file) == h, file
        artifacts += len(entries)
    assert (len(manifests), artifacts) == (253, 84766)
    sources = p['source_fingerprints']; assert len(sources) == 1381
    for file, h in sources.items(): assert s.sha(file) == h, file
    publications = {}
    for path in sorted(Path('publications/alphaxiv').glob('*/manifest.json')):
        entries = s.load(path)['artifacts']
        for file, h in entries.items(): assert s.sha(file) == h, file
        publications[str(path)] = dict(sha256=s.sha(path), artifacts_checked=len(entries))
    rows = [r for r in s.source_rows(p) if r['expansion_case']]; assert len(rows) == 16
    assert p['policies'] == {k: list(v) for k, v in s.POLICIES.items()}
    refs = {r['id']: s.bound(r) for r in s.bound(p['references'])['records']}
    transports = {r['id']: s.bound(r) for r in s.bound(p['transport'])['records']}
    baseline = s.bound(p['baseline_records']); samples = s.load(out / 'comparisons.json')['samples']
    assert len(samples) == 6 and {(r['mode'], r['repeat']) for r in samples} == {(m, i) for m in s.POLICIES for i in range(2)}
    reports = {m: [] for m in s.POLICIES}; proofs = {}
    for sample in samples:
        report = s.bound(sample); mode = sample['mode']; reports[mode].append(report)
        assert report['mode'] == mode and report['panel'] == p['panel'] and len(report['cases']) == len(rows)
        dest = Path(sample['path']).parent; certs = []
        for row, case in zip(rows, report['cases']):
            assert row['id'] == case['id']; proof = s.load(dest / (row['id'] + '.json')); certs.append(proof)
            got = s.check(row['source'], proof); assert json.loads(s.encode(got)) == case['result']
            assert case['status'] == ('unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'))
            if got['answer'] is not None: assert got['answer'] == refs[row['id']]['result']['answer']
            assert case['diagnostic']['expansion']['expanded'] <= s.POLICIES[mode][1]
            if s.POLICIES[mode][0]:
                known = transports[row['id']]['proof']; assert proof['derivations'][:len(known['derivations'])] == known['derivations']
            if sample['repeat'] == 0: proofs[mode, row['id']] = proof
            else: assert proof == proofs[mode, row['id']]
        for name, data in (('certificates', certs), ('discovery', [None] * 16), ('combined', dict(proofs=certs, evidence=[None] * 16))):
            assert json.loads(gzip.decompress((dest / (name + '.json.gz')).read_bytes())) == data
            assert report['compressed_bytes'][name] == (dest / (name + '.json.gz')).stat().st_size
        assert report['proof_bytes'] == sum((dest / (r['id'] + '.json')).stat().st_size for r in rows)
    for mode, runs in reports.items():
        first = runs[0]
        assert list(map(clean, first['cases'])) == list(map(clean, runs[1]['cases']))
        for key in ('counts', 'warm_counts', 'cold_counts', 'proof_bytes', 'compressed_bytes'): assert first[key] == runs[1][key]
        total = Counter()
        for row, case in zip(rows, first['cases']):
            counts = Counter(); proof, diag = s.discover(row, mode, counts)
            assert proof == proofs[mode, row['id']] and diag == case['diagnostic'] and dict(counts) == case['discovery_counts']
            s.check(row['source'], proof, counts); assert dict(counts) == case['counts']; total.update(counts)
        assert dict(total) == first['counts']
        for key, repeats in [('warm_counts', 1), ('cold_counts', 2)]:
            counts = Counter()
            for _ in range(repeats):
                for row in rows: s.check(row['source'], proofs[mode, row['id']], counts)
            assert dict(counts) == first[key]
        subprocess.run([sys.executable, __file__, 'replay', str(out), mode], check=True)
        print('Reproduced', mode, flush=True)
    for row, case, old in zip(rows, reports['reuse2000'][0]['cases'], baseline['cases']):
        assert clean(case) == clean(old)
        assert proofs['reuse2000', row['id']] == s.load(s.PARENT / 'watched-0' / (row['id'] + '.json'))
        assert_prefix(proofs['reuse2000', row['id']], proofs['reuse8000', row['id']])
    coverage = {}; totals = {}; states = {}; rss = {}
    for mode, runs in reports.items():
        coverage[mode] = dict(Counter(c['status'] for c in runs[0]['cases']))
        states[mode] = sum(c['diagnostic']['expansion']['expanded'] for c in runs[0]['cases'])
        rss[mode] = max(r['peak_rss_bytes'] for r in runs)
        totals[mode] = {k: statistics.mean(r[k] for r in runs) for k in ('complete_seconds', 'input_seconds', 'warm_seconds', 'cold_seconds', 'persistence_seconds', 'proof_bytes')}
        totals[mode]['compressed_bytes'] = runs[0]['compressed_bytes']
        totals[mode]['phases'] = {k: statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
    union = []; remaining = []; gains = []; reuse_only = []; fresh_only = []; outcomes = []
    for i, row in enumerate(rows):
        statuses = {m: reports[m][0]['cases'][i]['status'] for m in s.POLICIES}
        solved = [m for m, status in statuses.items() if status != 'unresolved']
        if statuses['reuse2000'] == 'unresolved' and statuses['reuse8000'] != 'unresolved': gains.append(row['id'])
        if statuses['reuse8000'] != 'unresolved' and statuses['fresh8000'] == 'unresolved': reuse_only.append(row['id'])
        if statuses['fresh8000'] != 'unresolved' and statuses['reuse8000'] == 'unresolved': fresh_only.append(row['id'])
        chosen = solved[-1] if solved else 'reuse8000'
        union.append(dict(id=row['id'], status=statuses[chosen], certificate=s.binding(out / (chosen + '-0') / (row['id'] + '.json'))))
        record = dict(id=row['id'], statuses=statuses, reference_answer=refs[row['id']]['result']['answer'], diagnostics={m: reports[m][0]['cases'][i]['diagnostic']['expansion'] for m in s.POLICIES})
        outcomes.append(record)
        if not solved: remaining.append(record)
    semantic = s.load(out / 'semantic-audit.json')
    assert semantic['passed'] and semantic == s.load(out / 'semantic-audit-reproduced.json')
    analysis = dict(coverage=coverage, states=states, totals=totals, peak_rss_bytes=rss,
        gains_over_reuse2000=gains, reuse_only_at_8000=reuse_only, fresh_only_at_8000=fresh_only,
        union_counts=dict(Counter(r['status'] for r in union)), remaining=remaining, outcomes=outcomes,
        baseline_matches_parent=True, increasing_budget_preserves_derivation_prefix=True,
        budget_cost_percent=100 * (totals['reuse8000']['complete_seconds'] / totals['reuse2000']['complete_seconds'] - 1),
        reuse_vs_fresh_percent=100 * (totals['reuse8000']['complete_seconds'] / totals['fresh8000']['complete_seconds'] - 1),
        paired_budget_percent=[100 * (reports['reuse8000'][i]['complete_seconds'] / reports['reuse2000'][i]['complete_seconds'] - 1) for i in range(2)],
        paired_reuse_vs_fresh_percent=[100 * (reports['reuse8000'][i]['complete_seconds'] / reports['fresh8000'][i]['complete_seconds'] - 1) for i in range(2)],
        work_counts={m: reports[m][0]['counts'] for m in s.POLICIES}, limitations=p['limitations'])
    for name, data in [('analysis', analysis), ('remaining', dict(records=remaining)), ('coverage-union', dict(records=union, scope='Historical union of the same exposed 16 targets; not a measured combined dispatcher.'))]: s.write(out / (name + '.json'), data)
    cp = deepcopy(parent); cp.update(parent_checkpoint=p['parent'], source_fingerprints=sources)
    cp['reuse_expansion'] = {k: s.binding(out / (k + '.json')) for k in ('protocol', 'comparisons', 'analysis', 'coverage-union', 'remaining', 'semantic-audit')}
    assert all(cp[k] == value for k, value in parent.items() if k not in ('parent_checkpoint', 'source_fingerprints'))
    s.write(out / 'checkpoint.json', cp)
    s.write(out / 'validation.json', dict(passed=True, parent_manifests=manifests, prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources, preserved_tables=pv['preserved_tables'], new_cumulative_records=0,
        reference_union_unchanged=True, prior_structural_union_unchanged=pv['prior_structural_union_unchanged'],
        constructed_union_unchanged=pv['constructed_union_unchanged'], publications_unchanged=publications,
        checkpoint=s.binding(out / 'checkpoint.json'), seconds=time.perf_counter() - started))
    print(s.encode({k: analysis[k] for k in ('coverage', 'gains_over_reuse2000', 'reuse_only_at_8000', 'fresh_only_at_8000', 'union_counts')}))


if __name__ == '__main__':
    if sys.argv[1] == 'replay': replay(Path(sys.argv[2]), sys.argv[3])
    else: validate(Path(sys.argv[2]))
