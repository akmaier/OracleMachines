#!/usr/bin/env python3
"""Audit chronological conditional transfer, persisted hints and cumulative proofs."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json, sqlite3, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_learned_conditional as study
from experiments import validate_cnf_ranked_binary_targets as inherited
from experiments.cnf_conditional_unit_cache import check_cache, FORMAT_CACHE
from experiments.cnf_learned_conditional import check_cover, check_bank
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import restrict
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
base, TABLES = study.base, inherited.TABLES


def validate(out):
    began = time.perf_counter()
    p = base.load(out / 'protocol.json'); parent = study.bound(p['parent'])
    cases = study.bound(p['cases']); report = base.load(out / 'report.json')
    assert len(cases) == 19 and len(report['samples']) == 8
    assert report['protocol'] == study.binding(out / 'protocol.json')
    oldp = study.bound(p['base_protocol'])
    assert cases == study.bound(oldp['cases']) and p['prefix'] == oldp['prefix'] and p['donor'] == oldp['donor']
    assert study.bound(p['exploration'])['script_sha256'] == base.sha('experiments/probe_cnf_learned_conditional.py')
    sources = p['source_fingerprints']; assert len(sources) == 820
    for f, h in sources.items(): assert base.sha(f) == h, f
    manifests = deepcopy(base.load(study.PARENT / 'validation.json')['parent_manifests'])
    mp = study.PARENT / 'manifest.json'
    manifests[str(mp)] = dict(sha256=base.sha(mp), artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts = 0
    for path, entry in manifests.items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f; artifacts += 1
    assert (len(manifests), artifacts) == (144, 12751)
    old = base.load(study.PARENT / 'shared-0/report.json')
    prefix = study.read_zip(p['prefix']); expected_hints = study.bound(old['hints'])
    records, deltas, reloads, audits = {}, {}, [], []
    added, alternatives = Counter(), Counter()
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory); path = temp / 'union'
        base.restore_archive(parent['reference_union'], path)
        con = sqlite3.connect(path)
        try: initial = {t: dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally: con.close()
        merged = deepcopy(initial)
        for number, sample in enumerate(report['samples']):
            data = study.bound(sample); rows = study.bound(data['queries'])
            delta = study.read_zip(data['delta']); prep = study.read_zip(data['preparation_delta'])
            policy = sample['policy']; assert data['policy'] == policy and data['protocol'] == report['protocol']
            assert len(rows) == 114
            if policy == 'baseline':
                assert delta == study.read_zip(old['delta'])
                for a, b in zip(rows, study.bound(old['queries'])):
                    for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids'): assert a[field] == b[field]
            trial = temp / f'trial-{number}'; study.restore(prefix, trial, delta)
            s = SnapshotResidualSolver(trial)
            try:
                tick = time.perf_counter(); hints = study.bound(data['hints']); c = Counter()
                donor_hints = dict(format=FORMAT_CACHE, entries=hints['entries'])
                check_cache(donor_hints, c); assert donor_hints == expected_hints
                if policy == 'learned':
                    assert hints['format'] == 'learned-conditional-cache-v1'
                    check_bank(s, hints['learned'], c)
                else: assert hints == expected_hints
                reloads.append(dict(sample=sample, seconds=time.perf_counter()-tick, counts=dict(c)))
                available = {t: dict(prefix[t]) for t in study.TABLES}; registered = []

                def append(additions):
                    for t, entries in additions.items():
                        for key, payload in entries:
                            assert key not in available[t]
                            if t == TABLES[0]:
                                proof = json.loads(payload).get('proof', {})
                                assert {proof[f] for f in ('child', 'low', 'high') if f in proof} <= available[t].keys()
                            available[t][key] = payload
                append(prep)
                for row, (case, q) in zip(rows, ((c, q) for c in cases for q in c['queries'])):
                    assert (row['case'], row['template'], row['assignment']) == (case['index'], q['template'], q['assignment'])
                    target = restrict(case['source'], dict(q['assignment'])); cnf, names, key = s._canonical(target)
                    assert key == row['root'] and row['expanded_nodes'] <= p['node_limit']
                    if row.get('learned') is not None:
                        learned = row['learned']; assert row['route'] == 'learned-cover' and row['status'] == 'unsat' and row['expanded_nodes'] == 0
                        assert learned['root'] == key and learned['origin'] in available[TABLES[0]]
                        assert any(e['origin'] == learned['origin'] and e['guard'] == learned['guard'] == sorted(q['assignment']) for e in registered)
                        assert check_cover(learned['cover']) <= clause_set(target, Counter())
                    append({t: [[k, dict(delta[t])[k]] for k in row['new_ids'][t]] for t in study.TABLES})
                    assert key in available[TABLES[0]]
                    node = s._read(key, cnf); assert node is not None and node['answer'] == (row['status'] == 'sat')
                    if policy == 'learned' and row['route'] == 'native' and row['status'] == 'unsat' and row['expanded_nodes'] >= 3:
                        registered.append(dict(origin=key, names=list(names), guard=sorted(q['assignment'])))
                for t in study.TABLES: assert available[t] == dict(prefix[t] + delta[t])
                for k, payload in delta[TABLES[0]]: assert s._read(k) == json.loads(payload)
                if policy == 'learned':
                    for entry in hints['learned']:
                        assert {k: entry[k] for k in ('origin', 'names', 'guard')} in registered
                audits.append(dict(sample=sample, counts=dict(s.counts), registered=registered))
            finally: s.close()
            # Independently replay every newly stored payload and persisted bank.
            reader = CanonicalVerifySnapshot(trial)
            try:
                for k, payload in delta[TABLES[0]]: assert reader._read(k) == json.loads(payload)
                if policy == 'learned': check_bank(reader, hints['learned'])
            finally: reader.close(); trial.unlink()
            for t, entries in delta.items():
                for k, payload in entries:
                    if k in merged[t]:
                        assert json.loads(payload)['answer'] == json.loads(merged[t][k])['answer']
                        alternatives[t] += payload != merged[t][k]
                    else: merged[t][k] = payload; added[t] += 1
            assert data['summary']['statuses'] == dict(Counter(r['status'] for r in rows)) == {'sat': 11, 'unsat': 103}
            records[(policy, sample['repeat'])], deltas[(policy, sample['repeat'])] = rows, delta
        reference = records[('baseline', 0)]
        for rows in records.values(): assert [(r['root'], r['status']) for r in rows] == [(r['root'], r['status']) for r in reference]
        for policy in study.MODES:
            for repeat in range(1, 4):
                assert deltas[(policy, repeat)] == deltas[(policy, 0)]
                for a, b in zip(records[(policy, repeat)], records[(policy, 0)]):
                    for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids'): assert a[field] == b[field]
        con = sqlite3.connect(path)
        try:
            with con:
                for t, entries in merged.items(): con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)', [(k, v) for k, v in entries.items() if k not in initial[t]])
        finally: con.close()
        parts = []
        for field in ('transported_partition_study', 'probed_partition_study', 'ranked_binary_targets', 'binary_routing', 'bipolar_routing', 'prepared_cofactors', 'cofactor_handoff', 'partition_preparation', 'binary_interactions', 'live_fallback', 'joint_backbone', 'consequence_priority', 'preimage_fusion', 'joint_prefix'):
            parts.extend(study.bound(parent[field]['partitions']))
        assert len(parts) == 342; readers = {}
        for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
            s = cls(path); equiv, affine, cache = MultiEquivalenceStore(s), TerminalStore(s), BinaryCoreCache(s)
            try:
                for t in TABLES: assert initial[t].items() <= dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
                for k in merged[TABLES[0]]: assert s._read(k) is not None
                for k in merged[TABLES[1]]: assert affine.read(k) is not None
                for t in TABLES[2:5]:
                    for k in merged[t]: assert equiv.read(k) is not None
                for k, payload in merged[TABLES[-1]].items(): cache.verify(k, payload)
                for record in parts: check_record(s, record)
                readers[cls.__name__] = dict(s.counts)
            finally: s.close()
        dest = out / 'union'; dest.mkdir(exist_ok=True); archive = base.archive(path, dest)
    base.write(out / 'hint-reload.json', dict(samples=reloads, limitations=['Read, native-origin validation and conditional-cover validation charged separately from comparative worker cold-answer replay.']))
    work = {}
    for policy in study.MODES:
        c = Counter()
        for row in records[(policy, 0)]:
            c.update(row['metrics'])
            for k, v in row['counts'].items(): c[k.removeprefix('preliminary_')] += v
        work[policy] = dict(c)
    comparisons = []
    for index, row in enumerate(reference):
        new = records[('learned', 0)][index]
        comparisons.append(dict(case=row['case'], template=row['template'], assignment=row['assignment'],
            baseline_route=row['route'], learned_route=new['route'], baseline_expansions=row['expanded_nodes'], learned_expansions=new['expanded_nodes'],
            baseline_seconds=sum(records[('baseline', i)][index]['seconds'] for i in range(4))/4,
            learned_seconds=sum(records[('learned', i)][index]['seconds'] for i in range(4))/4,
            learned_counts=new['counts'], learned=new.get('learned')))
    analysis = dict(means=report['means'], groups=report['groups'], work=work, queries=comparisons,
        next_target='Avoid extracting and expanding a conditional cover for a target already refuted by ordinary unit propagation (case 6/guard 3). Reuse or price a checked unit screen; then test whether deferred discovery amortizes across more distinct supported edits.',
        limitations=['Three new reuse routes, not three newly solved inputs: all 114 cofactors already solved under the baseline.',
            'Four paired repeats are an informed local experiment. Preparation-plus-query and retained-state costs regress despite fewer fresh expansions. Keep optional.',
            'Selected-container memory excludes native allocations and temporary work. Encoded-bank caps do not bound total Python memory. Complete-worker variation is not a robust speedup.',
            'Matching uses explicit shared source-variable coordinates and supplied guards. Automatic correspondence, useful guard discovery and uniform arbitrary-SAT bounds remain open.'])
    base.write(out / 'analysis.json', analysis)
    sources = {**sources, 'experiments/validate_cnf_learned_conditional.py': base.sha(__file__)}
    cp = deepcopy(parent); cp.update(parent_checkpoint=p['parent'], reference_union=archive, source_fingerprints=sources,
        learned_conditional=dict(protocol=study.binding(out / 'protocol.json'), report=study.binding(out / 'report.json'), analysis=study.binding(out / 'analysis.json'),
            exploration=p['exploration'], hint_reload=study.binding(out / 'hint-reload.json'),
            decision='Lazy conditional covers enable three exact chronological transfers and reduce 43 to 33 expansions, but query time and retained storage regress. Keep experimental; first prevent cover reconstruction from replacing an already cheap unit conflict.'))
    base.write(out / 'checkpoint.json', cp)
    validation = dict(passed=True, parent_manifests=manifests, prior_artifacts_unchanged=artifacts, source_fingerprints=sources,
        query_audits=sum(len(rows) for rows in records.values()), preserved_tables={t: len(rows) for t, rows in merged.items()},
        new_records=dict(added), alternative_payload_observations=dict(alternatives), previous_partition_records=len(parts),
        readers=readers, audits=audits, checkpoint=study.binding(out / 'checkpoint.json'), seconds=time.perf_counter()-began,
        limitations=['Every earlier authoritative payload remains unchanged; alternative valid payloads stay in raw deltas.',
            'Chronological candidate origins precede each target. Native recomposition and persisted hints pass both independent readers. No new native proof rule or Lean theorem.'])
    base.write(out / 'validation.json', validation)
    print(base.encode({k: validation[k] for k in ('passed', 'query_audits', 'preserved_tables', 'new_records', 'seconds')}), flush=True)


if __name__ == '__main__': validate(Path(sys.argv[1]))
