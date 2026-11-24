#!/usr/bin/env python3
"""Replay local guard proposals and append independently checked acquisitions."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,shutil,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import study_cnf_guard_probes as study
from experiments.cnf_guard_probe_census import analyse_event
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_partial_residual_pool import charge
from experiments.cnf_archive_parts import restore_archive,split_archive
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_binary_core_cache import BinaryCoreCache
base=study.base;old=study.old;TABLES=old.previous.ALL_TABLES


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent'])
    assert old.bound(p['parent_manifest'])==base.load(study.PARENT/'manifest.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp=study.PARENT/'manifest.json';manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(162,14809)
    cases=old.bound(p['cases']);report=base.load(out/'report.json')
    assert report['protocol']==old.binding(out/'protocol.json') and len(report['targets'])==len(p['origins'])==8
    summaries=[];total=Counter();times=Counter();observe_counts=Counter();certificates={};untried=set();different=set();trials=[]
    for entry,origin in zip(report['targets'],p['origins']):
        r=old.bound(entry);assert (r['origin'],r['target'])==(origin,origin+1)
        reference=old.bound(r['source_report']);assert reference==base.load(study.ORIGINS/f'origin-{origin}/report.json')
        templates=old.bound(reference['extraction'])['templates'];source,names=old.native.normalize(cases[origin+1]['source'])
        before,before_names=old.native.normalize(cases[origin]['source']);assert names==before_names
        assert all(check_template(t)<=set(before) for t in templates)
        o=old.bound(r['observation']);results=old.bound(r['results']);saved=old.bound(r['checked'])
        assert o['source']==[list(c) for c in source]
        assert o['eligible']==[i for i,t in enumerate(templates) if check_template(t)<=set(source)]
        assert len(o['eligible'])==len(templates)
        assert o['limits']==dict(events=p['event_limit'],key_bytes=p['event_key_bytes'])
        assert len(o['events'])<=p['event_limit'] and len(saved)==len(o['events'])
        assert o['key_bytes']==sum(len(e['root'].encode()) for e in o['events'])<=p['event_key_bytes']
        # charge counts distinct object identities. JSON reload loses the live
        # observer's sharing, so a byte-equality check would be invalid.
        assert type(o['event_graph_bytes']) is int and o['event_graph_bytes']>0
        reloaded_graph_bytes=charge(o['events'])
        assert not o['counts'].get('event_limit_skips',0) and not o['counts'].get('unbound_probe_calls',0)
        assert o['counts']['observed_probe_contexts']==len(o['events'])
        for k in ('status','metrics','result'):assert results['native'][k]==results['observed'][k]
        assert results['native']['status']=='unresolved' and results['native']['metrics']['expanded_nodes']==256
        assert results['native']['result'] is None
        # Both restored causal prefixes produce byte-identical SQLite files.
        for mode,a in r['archives'].items():
            assert base.sha(a['path'])==a['sha256']
            for k in ('database_bytes','database_sha256','compressed_bytes','sha256'):assert a[k]==r['archives']['native'][k]
        if origin+1 in (28,64):
            prior=base.load(study.PARENT/f'target-{origin+1}-native-0/report.json')
            assert r['native_digest']==prior['digest']
            prev=old.bound(prior['result'])['result']
            for k in ('status','metrics','result'):assert results['native'][k]==prev[k]
        counts=Counter();summary=Counter();subset_proposals=0
        for event,expected in zip(o['events'],saved):
            actual=analyse_event(source,templates,event,counts)
            summary['contexts']+=1;summary['whole_residual_contexts']+=actual['whole_residual']
            summary['contexts_with_proposals']+=bool(actual['candidates'])
            assert len(event['available'])==len(actual['candidates'])
            for q,presence in zip(actual['candidates'],event['available']):
                assert q['root']==presence['root'] and type(presence['present']) is bool
                assert presence['present'] or presence['answer'] is None
                q['present_at_event']=presence['present'];summary['proposals']+=1
                summary['tried' if q['tried'] else 'untried']+=1
                summary['different_variable']+=q['different_variable'];subset_proposals+=not actual['whole_residual']
                summary['unit_conflicts' if q['node'] is not None else 'unit_inconclusive']+=1
                if q['node'] is not None:
                    assert not presence['present'] or presence['answer'] is False
                    summary['untried_unit_conflicts']+=not q['tried']
                    summary['different_variable_unit_conflicts']+=q['different_variable']
                    summary['untried_absent_unit_conflicts']+=not q['tried'] and not presence['present']
                    if q['root'] in certificates:assert certificates[q['root']]==q['node']
                    certificates[q['root']]=q['node']
                    if not q['tried']:untried.add(q['root'])
                    if q['different_variable']:different.add(q['root'])
            assert actual==expected
        assert dict(summary)==r['summary'] and dict(counts)==r['counts']
        total.update(summary);observe_counts.update(o['counts'])
        for mode,t in r['times'].items():
            for key,value in t.items():times[f'{mode}_{key}']+=value
        times['posthoc_analysis_seconds']+=r['analysis_seconds']
        summaries.append(dict(target=origin+1,summary=dict(summary),subset_proposals=subset_proposals,
            times=r['times'],analysis_seconds=r['analysis_seconds'],key_bytes=o['key_bytes'],event_graph_bytes=o['event_graph_bytes'],
            reloaded_event_graph_bytes=reloaded_graph_bytes,
            observer_counts=o['counts'],capture_counts=o['context_capture']['counts']))
        trials.append(dict(target=origin+1,archive=r['archives']['native'],digest=r['native_digest']))
    trials.append(dict(target='conditional',archive=report['conditional_archive']))
    added={t:[] for t in TABLES};alternatives=Counter();audits=[]
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);original=temp/'parent';union=temp/'union'
        restore_archive(parent['reference_union'],original);shutil.copyfile(original,union);con=sqlite3.connect(union)
        for trial in trials:
            path=temp/'trial';restore_archive(trial['archive'],path);stored,checked=audit(path)
            if trial['target']=='conditional':
                assert {k:json.loads(v) for k,v in stored[TABLES[0]].items()}==certificates
                assert all(not stored[t] for t in TABLES[1:])
            else:assert trial['digest']=={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in stored.items()}
            with con:
                for table,rows in stored.items():
                    for root,payload in rows.items():
                        prior=con.execute(f'SELECT payload FROM {table} WHERE id=?',(root,)).fetchone()
                        if prior is None:
                            con.execute(f'INSERT INTO {table}(id,payload) VALUES (?,?)',(root,payload));added[table].append(root)
                        else:
                            assert json.loads(prior[0]).get('answer')==json.loads(payload).get('answer')
                            alternatives[table]+=prior[0]!=payload
            audits.append(dict(target=trial['target'],readers=checked));path.unlink();print('audited',trial['target'],flush=True)
        con.execute('ATTACH DATABASE ? AS prior',(str(original),))
        for t in TABLES:
            assert con.execute(f'SELECT count(*) FROM prior.{t} p LEFT JOIN main.{t} u ON p.id=u.id WHERE u.id IS NULL OR p.payload!=u.payload').fetchone()[0]==0
        tables={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES};con.close()
        readers={}
        for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
            s=cls(union);affine=TerminalStore(s);equiv=MultiEquivalenceStore(s);cache=BinaryCoreCache(s)
            try:
                for key in added[TABLES[0]]:assert s._read(key) is not None
                for key in added[TABLES[1]]:assert affine.read(key) is not None
                for t in TABLES[2:5]:
                    for key in added[t]:assert equiv.read(key) is not None
                for key in added[TABLES[-1]]:
                    payload=s.db.execute(f'SELECT payload FROM {TABLES[-1]} WHERE id=?',(key,)).fetchone()[0];cache.verify(key,payload)
                readers[cls.__name__]=dict(s.counts)
            finally:s.close()
        assert base.sha(original)==parent['reference_union']['database_sha256']
        (out/'union').mkdir();single=base.archive(union,out/'union');archive=split_archive(single,out/'union-parts')
        restored=temp/'restored';restore_archive(archive,restored);assert base.sha(restored)==base.sha(union)
        Path(single['path']).unlink()
    analysis=dict(summary=dict(total),distinct_certificates=len(certificates),distinct_untried=len(untried),
        distinct_different_variable=len(different),targets=summaries,times=dict(times),observer_counts=dict(observe_counts),
        conditional_archive=report['conditional_archive'],limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_guard_probes.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        guard_probe_census=dict(protocol=old.binding(out/'protocol.json'),report=old.binding(out/'report.json'),analysis=old.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,targets_checked=8,contexts_checked=total['contexts'],certificates_checked=len(certificates),
        audits=audits,new_records={t:len(v) for t,v in added.items()},preserved_tables=tables,alternative_payload_observations=dict(alternatives),
        readers=readers,checkpoint=old.binding(out/'checkpoint.json'),archive_roundtrip_byte_identical=True,seconds=time.perf_counter()-began,
        limitations=[
            'Incremental cumulative audit: every old six-table payload is byte-identical; new nodes and their dependencies replay through both readers. Earlier complete-history and 342-partition checks remain hash-bound, not rerun.',
            'Both readers fully check all nine distinct native/conditional worker databases. Observed/native SQLite and compressed hashes are identical for each target; all 17 raw archives remain preserved.',
            'Temporal presence is passive instrumented metadata, not a separately reconstructed transaction trace. All actual proposed child refutations and source-coordinate subset bindings are independently checked.',
            'No search-policy intervention or improvement in whole-input coverage. A locally refuted polarity gives no verdict on the opposite branch or the unrestricted SAT problem.']))
    print(base.encode(dict(passed=True,summary=dict(total),new_records={t:len(v) for t,v in added.items()},tables=tables)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
