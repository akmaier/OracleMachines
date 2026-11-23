#!/usr/bin/env python3
"""Audit preparation sharing against unchanged native bytes and the full archive."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json, sqlite3, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_template_preparation as study
from experiments import validate_cnf_ranked_binary_targets as inherited
from experiments.cnf_conditional_unit_cache import check_cache
from experiments.cnf_conditional_unit_support import match, fixed_pairs
from experiments.cnf_residual_dag import restrict
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
base = study.base
TABLES = inherited.TABLES


def validate(out):
    began = time.perf_counter()
    p = base.load(out / 'protocol.json')
    parent = study.bound(p['parent'])
    report = base.load(out / 'report.json')
    profile = base.load(out / 'profile.json')
    cases = study.bound(p['cases'])
    oldp = study.bound(p['base_protocol'])
    assert len(cases) == 19 and cases == study.bound(oldp['cases'])
    assert p['prefix'] == oldp['prefix'] and p['donor'] == oldp['donor']
    assert len(report['samples']) == 8 and report['protocol'] == study.binding(out / 'protocol.json')
    assert profile['proofs_and_routes_unchanged']
    assert profile['script_sha256'] == base.sha('experiments/profile_cnf_template_preparation.py')
    sources = dict(p['source_fingerprints'])
    assert len(sources) == 813
    for f, h in sources.items():
        assert base.sha(f) == h, f
    manifests = deepcopy(base.load(study.PARENT / 'validation.json')['parent_manifests'])
    mp = study.PARENT / 'manifest.json'
    manifests[str(mp)] = dict(sha256=base.sha(mp), artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts = 0
    for path, entry in manifests.items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items():
            assert base.sha(f) == h, f
            artifacts += 1
    assert (len(manifests), artifacts) == (143, 12684)
    reference = base.load(study.PARENT / 'pools-native-0/report.json')
    delta, prep = study.read_zip(reference['delta']), study.read_zip(reference['preparation_delta'])
    oldrows, hints = study.bound(reference['queries']), study.bound(reference['hints'])
    check_cache(hints)
    templates = [entry['template'] for entry in hints['entries']]
    samples = report['samples'] + [dict(policy='shared', repeat='profile', **profile['trial'])]
    records, reloads = {}, []
    prefix = study.read_zip(p['prefix'])
    attempts = 0
    for sample in samples:
        data = study.bound(sample)
        assert data['policy'] == sample['policy'] and data['protocol'] == report['protocol']
        assert study.read_zip(data['delta']) == delta
        assert study.read_zip(data['preparation_delta']) == prep
        tick = time.perf_counter()
        loaded = study.bound(data['hints'])
        c = Counter()
        check_cache(loaded, c)
        assert loaded == hints
        reloads.append(dict(sample=sample, seconds=time.perf_counter() - tick, counts=dict(c)))
        rows = study.bound(data['queries'])
        assert len(rows) == 114
        attempts += len(rows)
        available = {t: dict(prefix[t]) for t in study.TABLES}

        def append(additions):
            for table, entries in additions.items():
                for key, payload in entries:
                    assert key not in available[table]
                    if table == TABLES[0]:
                        proof = json.loads(payload).get('proof', {})
                        assert {proof[f] for f in ('child', 'low', 'high') if f in proof} <= available[table].keys()
                    available[table][key] = payload

        append(prep)
        for row, oldrow, (case, q) in zip(rows, oldrows, ((c, q) for c in cases for q in c['queries'])):
            for field in ('case', 'template', 'assignment', 'root', 'status', 'route', 'expanded_nodes', 'new_ids'):
                assert row[field] == oldrow[field], field
            assert (row['case'], row['template'], row['assignment']) == (case['index'], q['template'], q['assignment'])
            append({t: [[k, dict(delta[t])[k]] for k in row['new_ids'][t]] for t in study.TABLES})
            assert row['root'] in available[TABLES[0]]
            if row['route'] == 'template':
                template = templates[q['template']]
                assert match(case['source'], template)
                fixed = fixed_pairs(q['assignment'])
                assert all(fixed.get(v) == b for v, b in fixed_pairs(template['assumptions']).items())
                if sample['policy'] == 'shared':
                    assert row['counts']['templates_checked'] == 1
                    assert row['counts']['shared_template_preparations'] == 1
            assert row.get('recovery') is None and row.get('screen') is None
        for table in study.TABLES:
            assert available[table] == dict(prefix[table] + delta[table])
        assert data['summary']['statuses'] == dict(Counter(r['status'] for r in rows)) == {'sat': 11, 'unsat': 103}
        assert data['summary']['expanded_nodes'] == sum(r['expanded_nodes'] for r in rows) == 43
        records[(sample['policy'], sample['repeat'])] = rows
    assert attempts == 1026

    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        trial = temp / 'trial'
        study.restore(prefix, trial, delta)
        trial_readers = {}
        for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
            reader = cls(trial)
            try:
                for row, (case, q) in zip(oldrows, ((c, q) for c in cases for q in c['queries'])):
                    target = restrict(case['source'], dict(q['assignment']))
                    cnf, _, key = reader._canonical(target)
                    assert key == row['root']
                    assert reader._read(key, cnf)['answer'] == (row['status'] == 'sat')
                for key, payload in delta[TABLES[0]]:
                    assert reader._read(key) == json.loads(payload)
                trial_readers[cls.__name__] = dict(reader.counts)
            finally:
                reader.close()

        # Every measured delta is already in the previous verified union.
        # Reuse its immutable archive instead of writing another identical copy.
        path = temp / 'history'
        base.restore_archive(parent['reference_union'], path)
        con = sqlite3.connect(path)
        try:
            initial = {t: dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:
            con.close()
        for table, entries in delta.items():
            for key, payload in entries:
                assert key in initial[table]
                assert json.loads(payload)['answer'] == json.loads(initial[table][key])['answer']
        parts = []
        for field in ('transported_partition_study', 'probed_partition_study', 'ranked_binary_targets', 'binary_routing', 'bipolar_routing', 'prepared_cofactors', 'cofactor_handoff', 'partition_preparation', 'binary_interactions', 'live_fallback', 'joint_backbone', 'consequence_priority', 'preimage_fusion', 'joint_prefix'):
            parts.extend(study.bound(parent[field]['partitions']))
        assert len(parts) == 342
        readers = {}
        for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
            reader = cls(path)
            equiv, affine, cache = MultiEquivalenceStore(reader), TerminalStore(reader), BinaryCoreCache(reader)
            try:
                for key in initial[TABLES[0]]:
                    assert reader._read(key) is not None
                for key in initial[TABLES[1]]:
                    assert affine.read(key) is not None
                for table in TABLES[2:5]:
                    for key in initial[table]:
                        assert equiv.read(key) is not None
                for key, payload in initial[TABLES[-1]].items():
                    cache.verify(key, payload)
                for record in parts:
                    check_record(reader, record)
                for table, rows in initial.items():
                    assert rows == dict(reader.db.execute(f'SELECT id,payload FROM {table}'))
                readers[cls.__name__] = dict(reader.counts)
            finally:
                reader.close()
    base.write(out / 'hint-reload.json', dict(samples=reloads, limitations=['Separate read/binding/check cost, outside complete-worker answer replay timing.']))
    work, routes = {}, {}
    for policy in study.MODES:
        c = Counter()
        for row in records[(policy, 0)]:
            c.update(row['metrics'])
            for key, value in row['counts'].items():
                c[key.removeprefix('preliminary_')] += value
        work[policy] = dict(c)
        routes[policy] = {route: dict(attempts=sum(r['route'] == route for r in records[(policy, 0)]),
                                     mean_seconds=sum(r['seconds'] for repeat in range(4) for r in records[(policy, repeat)] if r['route'] == route) / 4)
                          for route in {r['route'] for r in records[(policy, 0)]}}
    assert work['repeated']['templates_checked'] == 173
    assert work['shared']['templates_checked'] == 102
    assert work['shared']['shared_template_preparations'] == 71
    analysis = dict(means=report['means'], groups=report['groups'], work=work, routes=routes,
                    identical_proof_bytes=True, identical_chronology=True,
                    profile=study.binding(out / 'profile.json'),
                    limitations=['Four alternating pairs of the same small supplied-guard workload; no external/general runtime or coverage claim.',
                                 'Full-worker times include hashing the frozen protocol sources and other work outside query timers. Native verification, persistence and replay are unchanged.',
                                 'Retained endpoint sizes are unchanged. The source snapshot and preparation are temporary O(L + |assignment|) data, and no transient-memory improvement is inferred.',
                                 'Instrumented cumulative profile rows overlap. Initial discovery, useful guard selection, arbitrary variable correspondence and whole-CNF composition remain unresolved.'])
    base.write(out / 'analysis.json', analysis)
    sources.update({f: base.sha(f) for f in ('experiments/profile_cnf_template_preparation.py', 'experiments/validate_cnf_template_preparation.py')})
    cp = deepcopy(parent)
    cp.update(parent_checkpoint=p['parent'], source_fingerprints=sources,
              template_preparation=dict(protocol=study.binding(out / 'protocol.json'), report=study.binding(out / 'report.json'),
                  analysis=study.binding(out / 'analysis.json'), profile=study.binding(out / 'profile.json'),
                  hint_reload=study.binding(out / 'hint-reload.json'),
                  decision='Within-call source-bound preparation removes 71 repeated checks and cofactor constructions while preserving all native bytes. Keep experimental; no end-to-end gain or broader SAT coverage claim.'))
    base.write(out / 'checkpoint.json', cp)
    v = dict(passed=True, parent_manifests=manifests, prior_artifacts_unchanged=artifacts,
             source_fingerprints=sources, query_audits=attempts, paired_attempts=912, profile_attempts=114,
             preserved_tables={t: len(rows) for t, rows in initial.items()}, new_records=0,
             archive_reused=parent['reference_union'], previous_partition_records=len(parts),
             reader_counts=readers, trial_readers=trial_readers, checkpoint=study.binding(out / 'checkpoint.json'),
             seconds=time.perf_counter() - began,
             limitations=['Every new delta exactly matches the previous pool-priority delta; the archive retains earlier authoritative payloads and all alternatives remain preserved.',
                          'Both readers replay all cumulative native/extension records and 342 previous partitions. No new proof rule, whole-input class or Lean refinement theorem.'])
    base.write(out / 'validation.json', v)
    print(base.encode({k: v[k] for k in ('passed', 'preserved_tables', 'new_records', 'query_audits', 'seconds')}), flush=True)


if __name__ == '__main__':
    validate(Path(sys.argv[1]))
