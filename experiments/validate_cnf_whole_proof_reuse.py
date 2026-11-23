#!/usr/bin/env python3
"""Audit automatic partial proof reuse and preserve all earlier authority."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json, sqlite3, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_proof_reuse as study
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
from experiments.cnf_clause_partition import check_record
from experiments.validate_cnf_ranked_binary_targets import TABLES
base = study.base


def audit(path, cases=(), rows=(), parts=()):
    before = base.sha(path)
    audits = {}
    for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
        s = cls(path)
        equiv, affine, cache = MultiEquivalenceStore(s), TerminalStore(s), BinaryCoreCache(s)
        try:
            present = {name for name, in s.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            stored = {t: dict(s.db.execute(f'SELECT id,payload FROM {t}')) if t in present else {} for t in TABLES}
            for key, payload in stored[TABLES[0]].items():
                assert s._read(key) == json.loads(payload)
            for key in stored[TABLES[1]]:
                assert affine.read(key) is not None
            for table in TABLES[2:5]:
                for key in stored[table]: assert equiv.read(key) is not None
            for key, payload in stored[TABLES[-1]].items(): cache.verify(key, payload)
            for c, r in zip(cases, rows):
                if r['result'] is not None:
                    study.harness.check_answer(s, equiv, c['source'], r['result'], affine)
                else:
                    assert r['status']=='unresolved' and r['metrics']['expanded_nodes']==256
            for record in parts: check_record(s, record)
            audits[cls.__name__] = dict(s.counts)
        finally: s.close()
    assert base.sha(path)==before
    return stored, audits


def validate(out):
    began = time.perf_counter()
    p = base.load(out/'protocol.json'); parent = study.bound(p['parent'])
    sources = p['source_fingerprints']
    for f, h in sources.items(): assert base.sha(f)==h, f
    manifests = deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp = study.PARENT/'manifest.json'
    manifests[str(mp)] = dict(sha256=base.sha(mp), artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts = 0
    for path, entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f, h in base.load(path)['artifacts'].items(): assert base.sha(f)==h, f; artifacts+=1
    assert (len(manifests), artifacts)==(154, 13713)
    report = base.load(out/'report.json')
    assert report['protocol']==study.binding(out/'protocol.json') and len(report['samples'])==24
    trials = []
    records = {}
    for sample in report['samples']:
        r = study.bound(sample); rows = study.bound(r['queries'])
        cases = study.bound(p['cases'][sample['split']])
        assert len(rows)==len(cases)==72
        records[(sample['split'], sample['mode'], sample['repeat'])] = rows
        trials.append(dict(name=f"{sample['split']}-{sample['mode']}-{sample['repeat']}",
            archive=r['archive'], cases=cases, rows=rows))
    for split in study.SPLITS:
        for mode in study.MODES:
            ref = records[(split, mode, 0)]
            for repeat in range(1, 4):
                for a, b in zip(ref, records[(split, mode, repeat)]):
                    for k in ('case', 'status', 'new_ids', 'metrics'): assert a[k]==b[k], k
            for a, b in zip(ref, records[(split, 'current', 0)]):
                if a['result'] is not None and b['result'] is not None:
                    assert a['status']==b['status']
    # The exposed binary/ordered controls must reproduce the previous stream.
    for mode in ('current','completion'):
        prior_rows=base.load(study.PARENT/f'holdout-{mode}-0/queries.json')
        for x,y in zip(records[('exposed',mode,0)],prior_rows):
            for k in ('status','new_ids','metrics'):assert x[k]==y[k],(mode,x['case'],k)
    plan_audits=[]
    from experiments.cnf_partial_proof_plan import check_plan,survival
    from experiments.cnf_conditional_unit_support import check_template
    from experiments.cnf_residual_dag import normalize
    for split in study.SPLITS:
        for repeat in range(4):
            cases=study.bound(p['cases'][split]);earlier={}
            for c,r in zip(cases,records[(split,'reuse',repeat)]):
                if r['result'] is not None and 'whole_plan' in r['result']:
                    hint=r['result']['whole_plan'];assert hint['origin'] in earlier
                    check_plan(hint['plan'])
                    canonical,_=normalize(c['source'])
                    assert hint['outcome']['root']==c['root']
                    assert survival(canonical,hint['plan'],Counter())==hint['outcome']['intact']
                    for template in hint['plan']['templates']:
                        if template.get('open') is not True:
                            assert check_template(template)<=earlier[hint['origin']]
                    assert r['result']['authority']=='native' and not hint['outcome']['stopped']
                    assert r['metrics']['whole_plan_attempts']==1 and r['metrics'].get('expanded_nodes',0)<=256
                    plan_audits.append(dict(split=split,repeat=repeat,case=r['case'],root=c['root'],
                        origin=hint['origin'],answer=r['result']['answer'],metrics=r['metrics']))
                if r['result'] is not None and r['result']['answer'] is False and r['result']['authority']=='native':
                    earlier[r['result']['root']]=set(normalize(c['source'])[0])
    e=base.load(out/'exploration/inspection.json')
    prefix=base.load(out/'exploration/prefix-queries.json')
    exposed=study.bound(p['cases']['exposed'])
    for row,old in zip(prefix,records[('exposed','completion',0)]):
        assert (row['status'],row['metrics'])==(old['status'],old['metrics'])
    assert len(prefix)==70
    trials.extend([
        dict(name='exploration-prefix',archive=e['prefix_archive'],cases=exposed[:70],rows=prefix),
        dict(name='exploration-default-cover-failure',archive=e['after_archive'],cases=[],rows=[]),
        dict(name='exploration-partial-plan',archive=base.load(out/'exploration/partial-archive.json'),cases=[],rows=[]),
        dict(name='exploration-default-budget',archive=base.load(out/'exploration/online-after/archive.json'),
            cases=exposed,rows=base.load(out/'exploration/online-prototype.json'))])
    for r in base.load(out/'profiling.json')['pool_checks']:
        trials.append(dict(name=f"exploration-pool-{r['split']}-{r['case']}",archive=r['archive'],cases=[],rows=[]))
    added, alternatives = Counter(), Counter(); audits=[]; table_digests={}
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td); path=temp/'union'
        base.restore_archive(parent['reference_union'], path)
        con=sqlite3.connect(path)
        try: initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally: con.close()
        merged=deepcopy(initial)
        known={k for entries in initial.values() for k in entries}
        for split in study.SPLITS:
            assert p['novelty'][split]==[dict(case=c['case'],known_in_parent=c['root'] in known)
                for c in study.bound(p['cases'][split])]
        for trial in trials:
            dest=temp/'trial'
            base.restore_archive(trial['archive'], dest)
            stored, counts=audit(dest, trial['cases'], trial['rows'])
            if trial['name']=='exploration-prefix':
                from experiments.cnf_carried_origins import extract
                from experiments.cnf_partial_proof_plan import extract_partial
                reader=CanonicalVerifySnapshot(dest)
                try:
                    bundle,work=extract(reader,e['origin']['source'],node_limit=512,literal_limit=524288)
                    assert dict(bundle=bundle,counts=work)==base.load(out/'exploration/expanded-bundle.json')
                    bundle,work=extract_partial(reader,e['origin']['source'])
                    prototype=base.load(out/'exploration/partial-plan-prototype.json')
                    assert (bundle,work)==(prototype['bundle'],prototype['work'])
                finally:reader.close()
            table_digests[trial['name']]={t:base.key_sha(base.encode(sorted(entries.items()))) for t,entries in stored.items()}
            available={t:set() for t in study.TABLES}
            if not trial['name'].startswith('exploration-'):
                for c, r in zip(trial['cases'], trial['rows']):
                    assert r['case']==c['case'] and r['metrics'].get('expanded_nodes',0)<=256
                    for t in study.TABLES:
                        assert not available[t].intersection(r['new_ids'][t])
                        available[t].update(r['new_ids'][t])
                        assert available[t]<=stored[t].keys()
                    if r['result'] is not None:
                        assert r['result']['root']==c['root']
                        assert any(c['root'] in keys for keys in available.values())
                assert all(available[t]==stored[t].keys() for t in study.TABLES)
            for t, entries in stored.items():
                for k, payload in entries.items():
                    if k in merged[t]:
                        assert json.loads(payload).get('answer')==json.loads(merged[t][k]).get('answer')
                        alternatives[t]+=payload!=merged[t][k]
                    else: merged[t][k]=payload; added[t]+=1
            audits.append(dict(name=trial['name'], tables={t:len(x) for t,x in stored.items()}, readers=counts))
            dest.unlink()
        con=sqlite3.connect(path)
        try:
            with con:
                for t, entries in merged.items():
                    con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',
                        [(k,v) for k,v in entries.items() if k not in initial[t]])
        finally: con.close()
        parts=[]
        for field in ('transported_partition_study','probed_partition_study','ranked_binary_targets',
                'binary_routing','bipolar_routing','prepared_cofactors','cofactor_handoff','partition_preparation',
                'binary_interactions','live_fallback','joint_backbone','consequence_priority','preimage_fusion','joint_prefix'):
            parts.extend(study.bound(parent[field]['partitions']))
        assert len(parts)==342
        stored, readers=audit(path, parts=parts)
        for t in TABLES: assert initial[t].items()<=stored[t].items() and stored[t]==merged[t]
        (out/'union').mkdir(exist_ok=True)
        archive=base.archive(path, out/'union')
    sources={**sources, 'experiments/validate_cnf_whole_proof_reuse.py':base.sha(__file__)}
    cp=deepcopy(parent)
    cp.update(parent_checkpoint=p['parent'], reference_union=archive, source_fingerprints=sources,
        whole_proof_reuse=dict(protocol=study.binding(out/'protocol.json'), report=study.binding(out/'report.json'),
            analysis=study.binding(out/'analysis.json'), decision='Retain open proof frontiers as search plans with checked surviving unit supports; price automatic recognition and preserve every unresolved result.'))
    base.write(out/'checkpoint.json', cp)
    v=dict(passed=True, parent_manifests=manifests, prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources, query_audits=sum(len(t['rows']) for t in trials if not t['name'].startswith('exploration-')), exploration_query_audits=142,
        preserved_tables={t:len(x) for t,x in merged.items()}, new_records=dict(added),
        alternative_payload_observations=dict(alternatives), previous_partition_records=len(parts),
        readers=readers, audits=audits, plan_audits=plan_audits, table_digests=table_digests, checkpoint=study.binding(out/'checkpoint.json'), seconds=time.perf_counter()-began,
        limitations=['All earlier authoritative payloads are unchanged. Alternative valid payloads remain in raw trial archives.',
            'Inherited per-query ID logs track four authority tables; this independent audit replays and preserves all six tables, including v1 equivalences and binary discovery. Parent novelty is rechecked against all six.',
            'Completed roots and every persisted prefix node pass two native readers; budget stops have no inferred verdict.',
            'The exploratory online prototype used the inherited 100000-dispatch default and is excluded from every matched comparison. Its independently checked results are preserved separately.',
            'The selected Python graph excludes transient plans, query-log objects and native/transient allocations. Dispatch counts omit lookahead publication; time and publication metrics are separate.'])
    base.write(out/'validation.json', v)
    print(base.encode({k:v[k] for k in ('passed','query_audits','preserved_tables','new_records','seconds')}), flush=True)


if __name__=='__main__': validate(Path(sys.argv[1]))
