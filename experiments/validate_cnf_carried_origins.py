#!/usr/bin/env python3
"""Audit carried original-clause maps, exact extracted bundles and prior proofs."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json, sqlite3, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_carried_origins as study
from experiments import validate_cnf_ranked_binary_targets as inherited
from experiments.cnf_conditional_unit_cache import check_cache, FORMAT_CACHE
from experiments.cnf_learned_conditional import check_cover, check_bank, origin_source
from experiments.cnf_clause_deletion_guard import clause_set
from experiments.cnf_residual_dag import restrict, propagate
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
from experiments.cnf_conditional_unit_support import extract as prior_extract
from experiments.cnf_carried_origins import extract as carried_extract
base, TABLES = study.base, inherited.TABLES


def validate(out):
    began = time.perf_counter()
    p = base.load(out / 'protocol.json'); parent = study.bound(p['parent'])
    cases = study.bound(p['cases']); report = base.load(out / 'report.json')
    assert len(cases) == 23 and len(report['samples']) == 12
    assert report['protocol'] == study.binding(out / 'protocol.json')
    oldp = study.bound(p['base_protocol'])
    assert cases == study.bound(oldp['cases']) and p['prefix'] == oldp['prefix'] and p['donor'] == oldp['donor']
    sources = p['source_fingerprints']; assert len(sources) == 842
    for f, h in sources.items(): assert base.sha(f) == h, f
    manifests = deepcopy(base.load(study.PARENT / 'validation.json')['parent_manifests'])
    mp = study.PARENT / 'manifest.json'
    manifests[str(mp)] = dict(sha256=base.sha(mp), artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts = 0
    for path, entry in manifests.items():
        assert base.sha(path) == entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f) == h, f; artifacts += 1
    assert (len(manifests), artifacts) == (148, 13095)
    old = base.load(study.PARENT / 'baseline-0/report.json')
    prefix = study.read_zip(p['prefix']); expected_hints = study.bound(old['hints'])
    records, deltas, reloads, audits = {}, {}, [], []
    extraction_audits = []
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
            assert len(rows) == 138
            if policy in ('baseline', 'prepared'):
                previous = base.load(study.PARENT / f'{policy}-0/report.json')
                for a, b in zip(rows, study.bound(previous['queries'])):
                    for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids'): assert a[field] == b[field]
            trial = temp / f'trial-{number}'; study.restore(prefix, trial, delta)
            s = SnapshotResidualSolver(trial)
            try:
                tick = time.perf_counter(); hints = study.bound(data['hints']); c = Counter()
                donor_hints = dict(format=FORMAT_CACHE, entries=hints['entries'])
                check_cache(donor_hints, c); assert donor_hints == expected_hints
                if policy != 'baseline':
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
                    partial = row.get('partial')
                    if partial is not None:
                        assert policy in ('prepared', 'carried') and row['route'] == 'partial-cover'
                        assert partial['root'] == key and not partial['stopped']
                        origins = [e for e in registered if e['origin'] == partial['origin'] and e['guard'] == partial['guard'] == sorted(q['assignment'])]
                        assert origins and partial['origin'] in available[TABLES[0]]
                        assert check_cover(partial['cover']) <= clause_set(origin_source(s, origins[0]), Counter())
                        intact = [clause_set(t['clauses'], Counter()) <= clause_set(target, Counter()) for t in partial['cover']['templates']]
                        assert intact == partial['intact'] and any(intact) and not all(intact)
                        for event in partial['leaves']:
                            context = dict(event['context'])
                            local, _, actual = s._canonical(restrict(target, context))
                            assert actual == event['root']
                            leaf = partial['cover']['templates'][event['leaf']]
                            assert all(context.get(v) == b for v, b in leaf['assumptions'])
                            if event['route'] == 'support': assert intact[event['leaf']]
                            else: assert event['route'] == 'native' and not intact[event['leaf']]
                        assert sum(e.get('expanded_nodes', 0) for e in partial['leaves']) == row['expanded_nodes']
                    append({t: [[k, dict(delta[t])[k]] for k in row['new_ids'][t]] for t in study.TABLES})
                    assert key in available[TABLES[0]]
                    node = s._read(key, cnf); assert node is not None and node['answer'] == (row['status'] == 'sat')
                    screen = row.get('screen')
                    if screen is not None:
                        _, trace, conflict = propagate(cnf, Counter())
                        assert screen == dict(root=key, trace=trace, conflict=conflict)
                        if row['route'] == 'unit-conflict':
                            assert conflict is not None and row['expanded_nodes'] == 0
                            assert node['proof'] == dict(kind='units', trace=trace, conflict=conflict)
                        else:
                            assert conflict is None and row['route'] in ('unit-fallback', 'learned-cover', 'partial-cover')
                    assert not row.get('stopped', False)
                    if policy != 'baseline' and row['route'] in ('native', 'unit-fallback') and row['status'] == 'unsat' and row['expanded_nodes'] >= 3:
                        registered.append(dict(origin=key, names=list(names), guard=sorted(q['assignment'])))
                for t in study.TABLES: assert available[t] == dict(prefix[t] + delta[t])
                for k, payload in delta[TABLES[0]]: assert s._read(k) == json.loads(payload)
                if policy != 'baseline':
                    for entry in hints['learned']:
                        assert {k: entry[k] for k in ('origin', 'names', 'guard')} in registered
                if policy == 'carried':
                    for entry in hints['learned']:
                        if entry['cover'] is None: continue
                        source = origin_source(s, entry)
                        old_bundle, old_counts = prior_extract(s, source)
                        new_bundle, new_counts = carried_extract(s, source)
                        assert old_bundle == new_bundle
                        assert entry['cover']['tree'] == new_bundle['tree']
                        assert entry['cover']['templates'] == [x['template'] for x in new_bundle['entries']]
                        extraction_audits.append(dict(sample=sample, origin=entry['origin'],
                            source=source, bundle=new_bundle, previous_counts=old_counts, carried_counts=new_counts))
                audits.append(dict(sample=sample, counts=dict(s.counts), registered=registered))
            finally: s.close()
            # Independently replay every newly stored payload and persisted bank.
            reader = CanonicalVerifySnapshot(trial)
            try:
                for k, payload in delta[TABLES[0]]: assert reader._read(k) == json.loads(payload)
                if policy != 'baseline': check_bank(reader, hints['learned'])
            finally: reader.close(); trial.unlink()
            for t, entries in delta.items():
                for k, payload in entries:
                    if k in merged[t]:
                        assert json.loads(payload)['answer'] == json.loads(merged[t][k])['answer']
                        alternatives[t] += payload != merged[t][k]
                    else: merged[t][k] = payload; added[t] += 1
            assert data['summary']['statuses'] == dict(Counter(r['status'] for r in rows)) == {'sat': 13, 'unsat': 125}
            records[(policy, sample['repeat'])], deltas[(policy, sample['repeat'])] = rows, delta
        reference = records[('baseline', 0)]
        for rows in records.values(): assert [(r['root'], r['status']) for r in rows] == [(r['root'], r['status']) for r in reference]
        for policy in study.MODES:
            for repeat in range(1, 4):
                assert deltas[(policy, repeat)] == deltas[(policy, 0)]
                for a, b in zip(records[(policy, repeat)], records[(policy, 0)]):
                    for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids'): assert a[field] == b[field]
        for repeat in range(4):
            assert deltas[('prepared', repeat)] == deltas[('carried', repeat)]
            a = base.load(out / f'prepared-{repeat}/report.json')
            b = base.load(out / f'carried-{repeat}/report.json')
            assert study.bound(a['hints']) == study.bound(b['hints'])
            for left, right in zip(records[('prepared', repeat)], records[('carried', repeat)]):
                for field in ('root', 'status', 'route', 'expanded_nodes', 'new_ids', 'partial', 'learned', 'screen'):
                    assert left.get(field) == right.get(field), field
                for field in ('verified_nodes', 'inserted_nodes', 'inserted_bytes', 'certificate_serialized_bytes'):
                    assert left['metrics'].get(field, 0) == right['metrics'].get(field, 0), field
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
        if added:
            dest = out / 'union'; dest.mkdir(exist_ok=True); archive = base.archive(path, dest)
        else: archive = parent['reference_union']
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
        variants = {}
        for policy in study.MODES:
            new = records[(policy, 0)][index]
            variants[policy] = dict(route=new['route'], expanded_nodes=new['expanded_nodes'],
                seconds=sum(records[(policy, i)][index]['seconds'] for i in range(4))/4,
                counts=new['counts'], learned=new.get('learned'), screen=new.get('screen'), partial=new.get('partial'))
        comparisons.append(dict(case=row['case'], template=row['template'], assignment=row['assignment'], variants=variants))
    analysis = dict(means=report['means'], groups=report['groups'], work=work, queries=comparisons,
        next_target='Rank the remaining acquisition, native verification and branch-construction costs after origin-index reuse; preserve cold positive and negative regressions when selecting the next coverage improvement.',
        limitations=['These exposed edits test a precise partial-support pattern, not a new whole-input classification or unrestricted efficiency theorem.',
            'Four alternating serial repeats charge the existing donor, recognition, cover extraction, publication, persistence and cold replay. Supplied guards and variable correspondence remain open.',
            'Native expansion dispatches omit checked support publication and split assembly, which are separately charged.',
            'Retained container counts exclude temporary and native allocations. Serialized bank caps are not total memory bounds.'])
    base.write(out / 'analysis.json', analysis)
    sources = {**sources, 'experiments/validate_cnf_carried_origins.py': base.sha(__file__)}
    cp = deepcopy(parent); cp.update(parent_checkpoint=p['parent'], reference_union=archive, source_fingerprints=sources,
        carried_origins=dict(protocol=study.binding(out / 'protocol.json'), report=study.binding(out / 'report.json'), analysis=study.binding(out / 'analysis.json'),
            hint_reload=study.binding(out / 'hint-reload.json'),
            decision='Indexed origin carry preserves exact conditional supports and all native proof payloads. Charge the index and copied map containers, then select the next bottleneck from total-cost measurements; no automatic correspondence or unrestricted bound is established.'))
    base.write(out / 'checkpoint.json', cp)
    validation = dict(passed=True, parent_manifests=manifests, prior_artifacts_unchanged=artifacts, source_fingerprints=sources,
        query_audits=sum(len(rows) for rows in records.values()), preserved_tables={t: len(rows) for t, rows in merged.items()},
        new_records=dict(added), alternative_payload_observations=dict(alternatives), previous_partition_records=len(parts),
        readers=readers, audits=audits, extraction_audits=extraction_audits, checkpoint=study.binding(out / 'checkpoint.json'), seconds=time.perf_counter()-began,
        limitations=['Every earlier authoritative payload remains unchanged; alternative valid payloads stay in raw deltas.',
            'Chronological candidate origins precede each target. Native recomposition and persisted hints pass both independent readers. No new native proof rule or Lean theorem.'])
    base.write(out / 'validation.json', validation)
    print(base.encode({k: validation[k] for k in ('passed', 'query_audits', 'preserved_tables', 'new_records', 'seconds')}), flush=True)


if __name__ == '__main__': validate(Path(sys.argv[1]))
