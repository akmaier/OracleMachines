#!/usr/bin/env python3
"""Truth, independent ancestry, cold replay and preservation checks."""
from collections import Counter
from copy import deepcopy
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import math
import random
import re
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_answer_certificate as s


def models(source):
    names = sorted({abs(v) for c in source for v in c})
    result = []
    for bits in product((False, True), repeat=len(names)):
        model = dict(zip(names, bits))
        if all(any(model[abs(v)] == (v > 0) for v in c) for c in source): result.append(model)
    return result


def expected_projection(source, archive):
    # Reverse scan of the complete trace, independent of the projector's DFS.
    base = len(s.e.resolution.prior.prior.previous.capacity.canonical(source, Counter()))
    needed = {archive['conclusion']} if archive['kind'] == 'unsat' else set()
    kept = []
    for i in reversed(range(len(archive['derivations']))):
        if base + i in needed:
            kept.append(i)
            start, steps, _ = archive['derivations'][i]
            needed.add(start); needed.update(ref for _, ref in steps)
    kept.reverse(); mapping = {base + old: base + new for new, old in enumerate(kept)}
    remap = lambda i: i if i < base else mapping[i]
    result = deepcopy(archive)
    result['derivations'] = [[remap(archive['derivations'][i][0]),
                             [[v, remap(ref)] for v, ref in archive['derivations'][i][1]],
                             list(archive['derivations'][i][2])] for i in kept]
    if archive['kind'] == 'unsat': result['conclusion'] = remap(archive['conclusion'])
    return result


def semantic(out, name='semantic-audit.json'):
    c2 = [[v for v in x if v] for x in product((0, 1, -1), (0, 2, -2))]
    c3 = [[v for v in x if v] for x in product((0, 1, -1), (0, 2, -2), (0, 3, -3))]
    inputs = [[c for i, c in enumerate(c2) if mask >> i & 1] for mask in range(512)]
    inputs += [list(cs) for n in range(4) for cs in combinations(c3, n)]
    rng = random.Random(202611281117)
    for _ in range(64):
        names = rng.sample(range(11, 1000), 5)
        source = [[rng.choice((-1, 1)) * v for v in rng.sample(names, 3)] for _ in range(24)]
        inputs.append(source + [source[0], [names[0], -names[0]]])
    counts = Counter()
    for source in inputs:
        truth = models(source)
        base = s.watched.canonical(source, Counter())
        for cap in (0, 128):
            archive, _ = s.watched.search(source, s.watched.baseline.prior.prior.proposal(source, Counter()), node_limit=cap)
            # A valid unused trailing copy makes every nonempty normalized
            # source exercise removal, even when search learns no new clause.
            if base: archive['derivations'].append([0, [], list(base[0])])
            before = deepcopy(archive)
            proof, diag = s.e.project(source, archive)
            assert archive == before
            assert proof == expected_projection(source, archive)
            assert proof == s.e.project(source, proof)[0]
            got = s.e.resolution.check_result(source, proof)
            if got['answer'] is not None: assert got['answer'] == bool(truth)
            if cap: assert got['answer'] is not None
            if got['model'] is not None: assert got['model'] in truth
            counts[proof['kind']] += 1; counts['checked_projections'] += 1
            counts['omitted_derivations'] += diag['omitted_derivations']
            counts['retained_derivations'] += diag['retained_derivations']
    s.write(out / name, dict(passed=True, counts=dict(counts), sources=len(inputs),
        scope='512 two-variable clause sets, 3304 three-variable sets of at most three clauses, 64 sparse signed mixtures with duplicates/tautologies. Caps 0 and 128; valid unused trailing copies added deliberately. Independent full model enumeration and reverse ancestry, immutable archive and idempotence. No claim of external transfer.'))


def validate(out):
    started = time.perf_counter(); p = s.load(out / 'protocol.json'); parent = s.bound(p['parent'])
    pv = s.load(s.PARENT / 'validation.json'); manifests = deepcopy(pv['parent_manifests'])
    pm = s.bound(p['parent_manifest'])
    manifests[p['parent_manifest']['path']] = dict(sha256=p['parent_manifest']['sha256'], artifacts_checked=len(pm['artifacts']))
    checked = {}; entries = 0
    for path, item in manifests.items():
        assert s.sha(path) == item['sha256'], path
        artifacts = s.load(path)['artifacts']; assert len(artifacts) == item['artifacts_checked']
        for f, h in artifacts.items():
            if f not in checked: checked[f] = s.sha(f)
            assert checked[f] == h, f
        entries += len(artifacts)
    for f, h in p['source_fingerprints'].items(): assert s.sha(f) == h, f
    assert all(p['source_fingerprints'][f] == h for f, h in parent['source_fingerprints'].items())
    proof_hashes = [hashlib.sha256(block.encode()).hexdigest() for block in re.findall(
        r'\\begin\{proof\}.*?\\end\{proof\}', Path('paper/bounded_domain_sat_and_amortized_reasoning.tex').read_text(), re.S)]
    assert proof_hashes[:len(p['prior_proof_hashes'])] == p['prior_proof_hashes']
    publications = {}
    for path in sorted(Path('publications/alphaxiv').glob('*/manifest.json')):
        artifacts = s.load(path)['artifacts']
        for f, h in artifacts.items(): assert s.sha(f) == h, f
        publications[str(path)] = dict(sha256=s.sha(path), artifacts_checked=len(artifacts))
    rows = {r['id']: r for r in s.prior.source_rows(p)}
    construction = s.load(out / 'construction.json')
    assert construction['protocol'] == s.binding(out / 'protocol.json')
    assert len(construction['cases']) == len(p['cases']) == 32
    records = []; counts_by_arm = {arm: Counter() for arm in ('full', 'answer')}
    for frozen, case in zip(p['cases'], construction['cases']):
        assert all(case[k] == v for k, v in frozen.items())
        archive = s.bound(case['archive']); source = rows[case['id']]['source']
        counts = Counter(); proof, diag = s.e.project(source, archive, counts)
        assert proof == expected_projection(source, archive)
        assert counts == case['counts'] and diag == case['diagnostic']
        assert archive == s.bound(case['archive'])
        for arm, expected in [('full', archive), ('answer', proof)]:
            stored = s.read_certificate(case['certificates'][arm]); assert stored == expected
            data = s.encode(stored).encode()
            assert len(data) == case['sizes'][arm]['json_bytes']
            assert hashlib.sha256(data).hexdigest() == case['sizes'][arm]['json_sha256']
            assert Path(case['certificates'][arm]['path']).stat().st_size == case['sizes'][arm]['gzip_bytes']
            got = s.e.resolution.check_result(source, stored, counts_by_arm[arm])
            assert json.loads(s.encode(got)) == case['expected']
        records.append(dict(key=case['key'], kind=case['kind'], origin=case['origin'],
                            variables=len({abs(v) for c in source for v in c}),
                            clauses=len(s.watched.canonical(source, Counter())), **diag))
    reports = {arm: [] for arm in counts_by_arm}
    for sample in s.load(out / 'comparisons.json')['samples']:
        report = s.bound(sample['report']); arm = report['arm']
        assert report['counts'] == counts_by_arm[arm]
        assert report['search_transport_projection_disabled']
        assert [r['key'] for r in report['cases']] == [c['key'] for c in construction['cases']]
        for r, c in zip(report['cases'], construction['cases']):
            assert r['result'] == c['expected'] and r['kind'] == c['kind']
        report['process_wall_seconds'] = sample['process_wall_seconds']; reports[arm].append(report)
    assert all(len(v) == 2 for v in reports.values())
    strata = {}
    for origin in ('fresh8000', 'reuse8000'):
        selected = [c for c in construction['cases'] if c['origin'] == origin]
        group = dict(coverage=dict(Counter(c['kind'] for c in selected)), arms={})
        for arm, runs in reports.items():
            by_kind = {}
            for kind in ('sat', 'unsat', 'unknown'):
                by_kind[kind] = dict(
                    cases=sum(c['kind'] == kind for c in selected),
                    json_bytes=sum(c['sizes'][arm]['json_bytes'] for c in selected if c['kind'] == kind),
                    gzip_bytes=sum(c['sizes'][arm]['gzip_bytes'] for c in selected if c['kind'] == kind),
                    replay_seconds=statistics.mean(sum(c['complete_seconds'] for c in r['cases'] if c['origin'] == origin and c['kind'] == kind) for r in runs))
            group['arms'][arm] = dict(
                json_bytes=sum(c['sizes'][arm]['json_bytes'] for c in selected),
                gzip_bytes=sum(c['sizes'][arm]['gzip_bytes'] for c in selected),
                replay_seconds=statistics.mean(sum(c['complete_seconds'] for c in r['cases'] if c['origin'] == origin) for r in runs),
                by_kind=by_kind)
        group['projection_seconds'] = sum(c['phases']['projection_including_both_checks_seconds'] for c in selected)
        group['incremental_answer_preparation_seconds'] = sum(sum(v for k, v in c['phases'].items() if not k.startswith('full_')) for c in selected)
        saved = group['arms']['full']['replay_seconds'] - group['arms']['answer']['replay_seconds']
        group['estimated_replays_to_repay_preparation'] = math.ceil(group['incremental_answer_preparation_seconds'] / saved) if saved > 0 else None
        group['archive_plus_answer_json_bytes'] = sum(group['arms'][a]['json_bytes'] for a in ('full', 'answer'))
        group['archive_plus_answer_gzip_bytes'] = sum(group['arms'][a]['gzip_bytes'] for a in ('full', 'answer'))
        strata[origin] = group
    semantic = s.load(out / 'semantic-audit.json')
    assert semantic['passed'] and semantic == s.load(out / 'semantic-audit-reproduced.json')
    analysis = dict(strata=strata, records=records, construction_seconds=construction['complete_seconds'],
        construction_peak_rss_bytes=construction['peak_rss_bytes'],
        replay={a: dict(worker_seconds=statistics.mean(r['complete_seconds'] for r in runs),
                        process_wall_seconds=statistics.mean(r['process_wall_seconds'] for r in runs),
                        peak_rss_bytes=max(r['peak_rss_bytes'] for r in runs)) for a, runs in reports.items()},
        limitations=p['limitations'], accounting=p['accounting'], no_new_answers=True)
    s.write(out / 'analysis.json', analysis)
    cp = deepcopy(parent); cp.update(parent_checkpoint=p['parent'], source_fingerprints=p['source_fingerprints'])
    cp['answer_certificate'] = {k: s.binding(out / (k + '.json')) for k in ('protocol', 'construction', 'comparisons', 'analysis', 'semantic-audit')}
    assert all(cp[k] == v for k, v in parent.items() if k not in ('parent_checkpoint', 'source_fingerprints'))
    s.write(out / 'checkpoint.json', cp)
    s.write(out / 'validation.json', dict(passed=True, parent_manifests=manifests,
        prior_artifacts_unchanged=entries, unique_prior_artifacts_checked=len(checked),
        source_fingerprints=p['source_fingerprints'], publications_unchanged=publications,
        prior_proofs_preserved=len(p['prior_proof_hashes']), current_proofs=len(proof_hashes),
        preserved_tables=pv['preserved_tables'], prior_structural_union_unchanged=pv['prior_structural_union_unchanged'],
        constructed_union_unchanged=pv['constructed_union_unchanged'], checkpoint=s.binding(out / 'checkpoint.json'),
        seconds=time.perf_counter()-started))
    print(s.encode(dict(strata=strata, replay=analysis['replay'], prior_manifests=len(manifests), prior_artifacts=entries)))


if __name__ == '__main__':
    action = sys.argv[1]; out = Path(sys.argv[2])
    if action == 'semantic': semantic(out, sys.argv[3] if len(sys.argv) > 3 else 'semantic-audit.json')
    else: globals()[action](out)
