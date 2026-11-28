#!/usr/bin/env python3
"""Independent small truth audit, frozen-transfer reproduction and lineage."""
from collections import Counter
from copy import deepcopy
from itertools import product, combinations
from pathlib import Path
from unittest.mock import patch
import gzip, json, random, statistics, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_reuse_transfer as s
from experiments.audit_cnf_selective_learning import expected_survival, models, references
from experiments.validate_cnf_reuse_expansion import clean


def semantic(out):
    c2 = [[v for v in x if v] for x in product((0, 1, -1), (0, 2, -2))]
    c3 = [[v for v in x if v] for x in product((0, 1, -1), (0, 2, -2), (0, 3, -3))]
    inputs = [[c for i, c in enumerate(c2) if mask >> i & 1] for mask in range(512)]
    inputs += [list(cs) for n in range(4) for cs in combinations(c3, n)]
    rng = random.Random(202611281015)
    for _ in range(64):
        names = rng.sample(range(11, 100), 5)
        source = [[rng.choice((-1, 1)) * v for v in rng.sample(names, 3)] for _ in range(15)]
        inputs.append(source + [source[0], [names[0], -names[0]]])
    counts = Counter()
    for source in inputs:
        seed = s.e.baseline.prior.prior.proposal(source, Counter())
        parent, _ = s.e.search(source, seed, node_limit=2)
        counts['parent_' + parent['kind']] += 1
        _, variants = s.edits(source, parent)
        for kind, target in variants:
            truth = models(target); counts['targets'] += 1
            known, diag = s.e.selective.transport(source, parent, target)
            assert diag['retained_indices'] == expected_survival(source, parent, target)
            for _, _, clause in known['derivations']:
                assert all(any(m[abs(v)] == (v > 0) for v in clause) for m in truth)
                counts['consequence_checks'] += 1
            for mode in ('fresh8000', 'reuse8000'):
                with patch.object(s, 'parent_data', return_value=(source, parent)):
                    proof, _ = s.discover({'source': target}, mode, Counter())
                answer = s.check(target, proof)['answer']; assert answer == bool(truth)
                counts['checked_outcomes'] += 1; counts[proof['kind']] += 1
                if mode == 'reuse8000': assert proof['derivations'][:len(known['derivations'])] == known['derivations']
    assert all(counts['parent_' + k] for k in ('sat', 'unsat', 'unknown'))
    s.write(out / 'semantic-audit.json', dict(passed=True, counts=dict(counts),
        scope='All 512 two-variable clause sets, 3304 up-to-three-clause three-variable sets, 64 sparse mixtures. Parent cap two covers SAT/UNSAT/unknown; both fixed edits, both target modes at 8000. Exhaustive truth and explicit transitive support sets are independent checks, not independent external samples.'))


def replay(out, mode):
    p = s.load(out / ('parents.json' if mode == 'parent20000' else 'protocol.json'))
    counts = Counter(); answers = {}
    with patch.object(s.e, 'search', side_effect=AssertionError), patch.object(s.e, 'expand', side_effect=AssertionError), patch.object(s.e.selective, 'transport', side_effect=AssertionError), patch.object(s.e.baseline, 'search', side_effect=AssertionError):
        for row in s.source_rows(p):
            answers[row['id']] = s.check(row['source'], s.load(out / (mode + '-0') / (row['id'] + '.json')), counts)['answer']
    report = s.load(out / (mode + '-0') / 'report.json')
    assert dict(counts) == report['warm_counts']
    assert answers == {c['id']: c['result']['answer'] for c in report['cases']}
    s.write(out / ('replay-' + mode + '.json'), dict(passed=True, answers=answers, counts=dict(counts), search_disabled=True, transport_disabled=True))


def interaction(source):
    names = {abs(v) for c in source for v in c}; parent = {v: v for v in names}
    def root(v):
        while parent[v] != v: parent[v] = parent[parent[v]]; v = parent[v]
        return v
    for clause in source:
        for v in clause[1:]: parent[root(abs(v))] = root(abs(clause[0]))
    return dict(variables=len(names), clauses=len(s.e.canonical(source, Counter())),
                component_sizes=sorted(Counter(root(v) for v in names).values()))


def validate(out):
    started = time.perf_counter(); p = s.load(out / 'protocol.json'); parent = s.bound(p['parent'])
    selection = s.bound(p['selection']); assert p['source_fingerprints'] == selection['source_fingerprints']
    assert selection['indices'] == [60, 80] and p['policies'] == {k: list(v) for k, v in s.POLICIES.items()}
    pv = s.load(s.PARENT / 'validation.json'); manifests = deepcopy(pv['parent_manifests'])
    mp = Path(p['parent_manifest']['path']); s.bound(p['parent_manifest'])
    manifests[str(mp)] = dict(sha256=s.sha(mp), artifacts_checked=len(s.load(mp)['artifacts']))
    artifacts = 0
    for path, entry in manifests.items():
        assert s.sha(path) == entry['sha256'], path
        entries = s.load(path)['artifacts']; assert len(entries) == entry['artifacts_checked']
        for f, h in entries.items(): assert s.sha(f) == h, f
        artifacts += len(entries)
    assert (len(manifests), artifacts) == (254, 84935)
    assert len(p['source_fingerprints']) == 1384
    for f, h in p['source_fingerprints'].items(): assert s.sha(f) == h, f
    publications = {}
    for path in sorted(Path('publications/alphaxiv').glob('*/manifest.json')):
        entries = s.load(path)['artifacts']
        for f, h in entries.items(): assert s.sha(f) == h, f
        publications[str(path)] = dict(sha256=s.sha(path), artifacts_checked=len(entries))
    pp = s.bound(p['parents']); parents = s.source_rows(pp); rows = s.source_rows(p)
    assert len(parents) == 8 and len(rows) == 16
    acq = s.load(out / 'acquisition.json'); assert acq['selection'] == p['selection']
    prior = {b['path']: {s.e.canonical(r['source'], Counter()) for r in s.bound(b)} for b in selection['prior_panels']}
    overlaps = []; seen = set()
    for i, (row, record) in enumerate(zip(parents, acq['records'])):
        assert row['id'] == record['id'] and record['index'] == selection['indices'][i % 2]
        assert record['archive'] == selection['groups'][i // 2]['archive']
        s.bound(p['parent_acquisition'])
        rawpath = record['original_gzip']['path']; assert s.sha(rawpath) == record['original_gzip']['sha256']
        raw = gzip.decompress(Path(rawpath).read_bytes())
        assert len(raw) == record['original_bytes'] and s.hashlib.sha256(raw).hexdigest() == record['original_sha256']
        assert s.parse_dimacs(raw.decode()) == (row['source'], record['header'])
        key = s.e.canonical(row['source'], Counter()); matches = [f for f, keys in prior.items() if key in keys]
        overlaps.append(dict(id=row['id'], prior_matches=matches, same_panel_exact=key in seen))
        assert not matches and key not in seen; seen.add(key)
        proof = s.load(out / 'parent20000-0' / (row['id'] + '.json'))
        got = s.check(row['source'], proof)
        if got['answer'] is not None: assert got['answer'] == record['publisher_answer']
        deleted, variants = s.edits(row['source'], proof)
        for target, (kind, source) in zip(rows[2*i:2*i+2], variants):
            assert target['source'] == source and target['kind'] == kind and target['deleted_index'] == deleted
            assert target['parent_id'] == row['id'] and target['parent_kind'] == proof['kind']
            assert s.parent_data(target, Counter()) == (row['source'], proof)
    assert overlaps == s.load(out / 'overlaps.json')['records']
    refs = {r['id']: s.bound(r) for r in s.load(out / 'references.json')['records']}; assert set(refs) == {r['id'] for r in rows}
    samples = s.load(out / 'comparisons.json')['samples']
    assert [(r['mode'], r['repeat']) for r in samples] == [(m, i) for i, order in enumerate(p['orders']) for m in order]
    samples = [dict(**p['parent_acquisition'], mode='parent20000', repeat=0)] + samples
    reports = {m: [] for m in s.POLICIES}; proofs = {}; survival = []
    for sample in samples:
        report = s.bound(sample); mode = sample['mode']; reports[mode].append(report)
        selected = parents if mode == 'parent20000' else rows; protocol = pp if mode == 'parent20000' else p
        assert report['mode'] == mode and report['panel'] == protocol['panel']
        assert len(report['cases']) == len(selected)
        dest = Path(sample['path']).parent; certs = []
        for row, case in zip(selected, report['cases']):
            assert row['id'] == case['id']; proof = s.load(dest / (row['id'] + '.json')); certs.append(proof)
            got = s.check(row['source'], proof); assert json.loads(s.encode(got)) == case['result']
            assert case['status'] == ('unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'))
            assert case['diagnostic']['expansion']['expanded'] <= s.POLICIES[mode][1]
            if mode != 'parent20000':
                ref = refs[row['id']]
                if ref['proof']: s.e.baseline.prior.prior.previous.check(row['source'], ref['proof'])
                if got['answer'] is not None and ref['result']['answer'] is not None: assert got['answer'] == ref['result']['answer']
            if mode == 'reuse8000':
                source, oldproof = s.parent_data(row, Counter()); known, diag = s.e.selective.transport(source, oldproof, row['source'])
                assert diag['retained_indices'] == expected_survival(source, oldproof, row['source'])
                assert proof['derivations'][:len(known['derivations'])] == known['derivations']
                assert diag == case['diagnostic']['survival']
                if sample['repeat'] == 0: survival.append(dict(id=row['id'], parent_kind=oldproof['kind'], original=len(oldproof['derivations']), retained=len(known['derivations']), discarded=len(diag['discarded_indices']), interaction=interaction(row['source'])))
            if sample['repeat'] == 0: proofs[mode, row['id']] = proof
            else: assert proof == proofs[mode, row['id']]
        for name, data in (('certificates', certs), ('discovery', [None]*len(selected)), ('combined', dict(proofs=certs, evidence=[None]*len(selected)))):
            assert json.loads(gzip.decompress((dest / (name + '.json.gz')).read_bytes())) == data
            assert report['compressed_bytes'][name] == (dest / (name + '.json.gz')).stat().st_size
        assert report['proof_bytes'] == sum((dest / (r['id'] + '.json')).stat().st_size for r in selected)
    totals = {}; coverage = {}; states = {}; rss = {}
    for mode, runs in reports.items():
        first = runs[0]; selected = parents if mode == 'parent20000' else rows
        if len(runs) > 1:
            assert list(map(clean, first['cases'])) == list(map(clean, runs[1]['cases']))
            for k in ('counts', 'warm_counts', 'cold_counts', 'proof_bytes', 'compressed_bytes'): assert first[k] == runs[1][k]
        total = Counter()
        for row, case in zip(selected, first['cases']):
            counts = Counter(); proof, diag = s.discover(row, mode, counts)
            assert proof == proofs[mode, row['id']] and diag == case['diagnostic'] and dict(counts) == case['discovery_counts']
            s.check(row['source'], proof, counts); assert dict(counts) == case['counts']; total.update(counts)
        assert dict(total) == first['counts']
        for k, repeats in [('warm_counts', 1), ('cold_counts', 2)]:
            counts = Counter()
            for _ in range(repeats):
                for row in selected: s.check(row['source'], proofs[mode, row['id']], counts)
            assert dict(counts) == first[k]
        subprocess.run([sys.executable, __file__, 'replay', str(out), mode], check=True)
        coverage[mode] = dict(Counter(c['status'] for c in first['cases']))
        states[mode] = sum(c['diagnostic']['expansion']['expanded'] for c in first['cases'])
        rss[mode] = max(r['peak_rss_bytes'] for r in runs)
        totals[mode] = {k: statistics.mean(r[k] for r in runs) for k in ('complete_seconds', 'input_seconds', 'warm_seconds', 'cold_seconds', 'persistence_seconds', 'proof_bytes')}
        totals[mode]['compressed_bytes'] = first['compressed_bytes']
        totals[mode]['phases'] = {k: statistics.mean(r['phases'][k] for r in runs) for k in first['phases']}
        print('Reproduced', mode, flush=True)
    union = []; remaining = []; reuse_only = []; fresh_only = []; outcomes = []; strata = {}
    for i, row in enumerate(rows):
        statuses = {m: reports[m][0]['cases'][i]['status'] for m in ('fresh8000', 'reuse8000')}
        solved = [m for m, status in statuses.items() if status != 'unresolved']
        if solved == ['reuse8000']: reuse_only.append(row['id'])
        if solved == ['fresh8000']: fresh_only.append(row['id'])
        chosen = solved[-1] if solved else 'reuse8000'
        union.append(dict(id=row['id'], status=statuses[chosen], certificate=s.binding(out / (chosen + '-0') / (row['id'] + '.json'))))
        record = dict(id=row['id'], parent_id=row['parent_id'], parent_kind=row['parent_kind'], kind=row['kind'], statuses=statuses,
            reference_answer=refs[row['id']]['result']['answer'], interaction=interaction(row['source']),
            diagnostics={m: reports[m][0]['cases'][i]['diagnostic'] for m in statuses})
        outcomes.append(record)
        if not solved: remaining.append(record)
        stratum = strata.setdefault(row['parent_kind'], {m: Counter() for m in statuses})
        for m, status in statuses.items(): stratum[m][status] += 1
    semantic = s.load(out / 'semantic-audit.json'); assert semantic['passed'] and semantic == s.load(out / 'semantic-audit-reproduced.json')
    analysis = dict(coverage=coverage, strata=strata, states=states, totals=totals, peak_rss_bytes=rss,
        reuse_only=reuse_only, fresh_only=fresh_only, overlap_solved=sum(all(v != 'unresolved' for v in r['statuses'].values()) for r in outcomes),
        union_counts=dict(Counter(r['status'] for r in union)), remaining=remaining, outcomes=outcomes, survival=survival,
        parent_plus_reuse_seconds=totals['parent20000']['complete_seconds']+totals['reuse8000']['complete_seconds'],
        reuse_vs_fresh_percent=100*(totals['reuse8000']['complete_seconds']/totals['fresh8000']['complete_seconds']-1),
        limitations=p['limitations'])
    for name, data in [('analysis', analysis), ('remaining', dict(records=remaining)), ('coverage-union', dict(records=union, scope='Historical union on sixteen related targets; not an efficient class or measured dispatcher.'))]: s.write(out / (name + '.json'), data)
    cp = deepcopy(parent); cp.update(parent_checkpoint=p['parent'], source_fingerprints=p['source_fingerprints'])
    cp['reuse_transfer'] = {k: s.binding(out / (k + '.json')) for k in ('protocol', 'selection', 'acquisition', 'overlaps', 'comparisons', 'analysis', 'coverage-union', 'remaining', 'semantic-audit', 'references')}
    assert all(cp[k] == value for k, value in parent.items() if k not in ('parent_checkpoint', 'source_fingerprints'))
    s.write(out / 'checkpoint.json', cp)
    s.write(out / 'validation.json', dict(passed=True, parent_manifests=manifests, prior_artifacts_unchanged=artifacts,
        source_fingerprints=p['source_fingerprints'], preserved_tables=pv['preserved_tables'], new_cumulative_records=0,
        reference_union_unchanged=True, prior_structural_union_unchanged=pv['prior_structural_union_unchanged'],
        constructed_union_unchanged=pv['constructed_union_unchanged'], publications_unchanged=publications,
        checkpoint=s.binding(out / 'checkpoint.json'), seconds=time.perf_counter()-started))
    print(s.encode({k: analysis[k] for k in ('coverage', 'strata', 'reuse_only', 'fresh_only', 'union_counts')}))


if __name__ == '__main__':
    if sys.argv[1] == 'replay': replay(Path(sys.argv[2]), sys.argv[3])
    else: globals()[sys.argv[1]](Path(sys.argv[2]))
