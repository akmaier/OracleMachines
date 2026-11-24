#!/usr/bin/env python3
"""Verify lazy binary preparation, exact proof identity and cumulative authority."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_binary_lazy as study
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.validate_cnf_ranked_binary_targets import TABLES
from experiments.cnf_archive_parts import split_archive,restore_archive
from experiments.cnf_partial_proof_plan import check_plan,survival
from experiments.cnf_conditional_unit_support import check_template
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_binary_census import closure
from experiments.cnf_probe_binary_lazy import lazy_closure
from experiments.cnf_residual_dag import normalize
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_fresh_mixtures import attempt
base=study.base


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    manifests=deepcopy(base.load(study.PARENT/'validation.json')['parent_manifests'])
    mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(159,14390)
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    assert len(report['samples'])==24
    trials=[];records={}
    for sample in report['samples']:
        r=study.bound(sample);rows=study.bound(r['queries']);cases=study.bound(p['cases'][sample['split']])
        assert len(rows)==len(cases)==72
        records[(sample['split'],sample['mode'],sample['repeat'])]=rows
        trials.append(dict(name=f"{sample['split']}-{sample['mode']}-{sample['repeat']}",archive=r['archive'],cases=cases,rows=rows))
    for split in study.SPLITS:
        control=records[(split,'current',0)]
        for mode in study.MODES:
            ref=records[(split,mode,0)]
            for repeat in range(1,4):
                for a,b in zip(ref,records[(split,mode,repeat)]):
                    for k in ('case','status','new_ids','metrics'):assert a[k]==b[k],(split,mode,k)
            for a,b in zip(ref,control):
                if a['result'] is not None and b['result'] is not None:assert a['status']==b['status']
                c=a['metrics'];assert c['whole_handoff_peak_bytes']<=2*1024*1024
                assert c['whole_handoff_admissions']==c['whole_handoff_consumed']+c['whole_handoff_discarded']
                assert c['whole_lifetime_full_visit_envelope_peak_bytes']>=c['whole_handoff_peak_bytes']
                assert c.get('closure_calls',0)==c.get('closure_compiled_children',0)+c.get('closure_inconclusive',0)
                if mode=='current':assert c.get('closure_calls',0)==0
                else:
                    hits=c.get('closure_compiled_children',0)
                    assert hits<=c.get('closure_published_nodes',0)+c.get('closure_existing_nodes',0)<=2*hits
    for mode in ('current','closure'):
        previous=base.load(study.PARENT/f'holdout-{mode}-0/queries.json')
        for a,b in zip(records[('exposed',mode,0)],previous):
            for k in ('status','new_ids','metrics'):assert a[k]==b[k],(mode,a['case'],k)
    for split in study.SPLITS:
        for a,b in zip(records[(split,'closure',0)],records[(split,'lazy',0)]):
            for k in ('status','new_ids'):assert a[k]==b[k],(split,a['case'],k)
            if a['result'] is not None:
                assert {k:v for k,v in a['result'].items() if k not in ('metrics','seconds')}=={k:v for k,v in b['result'].items() if k not in ('metrics','seconds')}
            x,y=a['metrics'],b['metrics']
            for k in ('expanded_nodes','closure_calls','closure_compiled_children','closure_inconclusive',
                    'closure_published_nodes','closure_existing_nodes','closure_refutations'):
                assert x.get(k,0)==y.get(k,0),(split,a['case'],k)
            assert y.get('lazy_raw_calls',0)==y.get('lazy_normalizations_avoided',0)+y.get('lazy_canonical_reconstructions',0)
            assert y.get('lazy_raw_calls',0)+y.get('lazy_already_canonical_calls',0)==y.get('closure_calls',0)
            assert y.get('closure_scc_calls',0)==x.get('closure_scc_calls',0)+y.get('lazy_certificate_scc_calls',0)
    # The original discovery/recomposition metadata remains chronological.
    plan_audits=[];pool_audits=[]
    for (split,mode,repeat),rows in records.items():
        earlier={}
        for c,r in zip(study.bound(p['cases'][split]),rows):
            result=r['result'];counts=r['metrics']
            assert counts.get('whole_pool_gates',0)<=1
            assert counts.get('whole_pool_gates',0)==counts.get('whole_pool_misses',0)+counts.get('whole_pool_completed',0)
            if result is not None and 'whole_plan' in result:
                hint=result['whole_plan'];assert hint['origin'] in earlier
                check_plan(hint['plan']);canonical,_=normalize(c['source'])
                assert hint['outcome']['root']==c['root'] and not hint['outcome']['stopped']
                assert survival(canonical,hint['plan'],Counter())==hint['outcome']['intact']
                for t in hint['plan']['templates']:
                    if t.get('open') is not True:assert check_template(t)<=earlier[hint['origin']]
                plan_audits.append(dict(split=split,mode=mode,repeat=repeat,case=c['case'],origin=hint['origin']))
            if result is not None and 'whole_pool' in result:
                hint=result['whole_pool'];assert hint['near_origin'] in earlier
                assert hint['route'] in ('negative-pool','witness-pool')
                assert result['answer']==(hint['route']=='witness-pool') and result['authority']=='native'
                assert counts.get('expanded_nodes',0)==0 and 'whole_plan' not in result
                pool_audits.append(dict(split=split,mode=mode,repeat=repeat,case=c['case'],**hint))
            if result is not None and result['answer'] is False and result['authority']=='native':
                earlier[result['root']]=set(normalize(c['source'])[0])
    # Re-evaluate the preceding exposed census without changing its source or
    # search archive. Check UP bindings and compare exact certificates on hits.
    census=base.load(study.PARENT/'exploration/report.json')
    events=study.bound(census['events']);verdicts=Counter();lazy_counts=Counter()
    for e in events:
        child=tuple(map(tuple,e['child']))
        fixed,trace,conflict=native.propagate(child,Counter())
        assert conflict is None and sorted(fixed.items())==list(map(tuple,e['fixed'])) and trace==e['trace']
        canonical=(child,tuple(e['names']),e['root']);up=(fixed,trace,conflict,0)
        eager=closure(canonical,up,Counter());lazy=lazy_closure(canonical,up,lazy_counts)
        assert json.loads(base.encode(eager))==e['discovery']
        assert eager['status']==lazy['status'] and eager['nodes']==lazy['nodes']
        verdicts[lazy['status']]+=1
    assert len(events)==353 and verdicts['binary-unsat']==19
    added,alternatives=Counter(),Counter();audits=[];digests={}
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';restore_archive(parent['reference_union'],path)
        con=sqlite3.connect(path)
        try:initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:con.close()
        merged=deepcopy(initial);known={k for entries in initial.values() for k in entries}
        for split in study.SPLITS:
            assert p['novelty'][split]==[dict(case=c['case'],known_in_parent=c['root'] in known) for c in study.bound(p['cases'][split])]
        for trial in trials:
            dest=temp/'trial';restore_archive(trial['archive'],dest)
            stored,counts=audit(dest,trial['cases'],trial['rows'])
            digests[trial['name']]={t:base.key_sha(base.encode(sorted(entries.items()))) for t,entries in stored.items()}
            available={t:set() for t in study.TABLES}
            for c,r in zip(trial['cases'],trial['rows']):
                assert r['case']==c['case'] and r['metrics'].get('expanded_nodes',0)<=256
                for t in study.TABLES:
                    assert not available[t].intersection(r['new_ids'][t]);available[t].update(r['new_ids'][t])
                    assert available[t]<=stored[t].keys()
                if r['result'] is not None:assert r['result']['root']==c['root'] and any(c['root'] in ids for ids in available.values())
            assert all(available[t]==stored[t].keys() for t in study.TABLES)
            for t,entries in stored.items():
                for k,payload in entries.items():
                    if k in merged[t]:
                        assert json.loads(payload).get('answer')==json.loads(merged[t][k]).get('answer')
                        alternatives[t]+=payload!=merged[t][k]
                    else:merged[t][k]=payload;added[t]+=1
            audits.append(dict(name=trial['name'],tables={t:len(x) for t,x in stored.items()},readers=counts))
            dest.unlink();print('audited',trial['name'],flush=True)
        for split in study.SPLITS:
            for mode in study.MODES:
                expected=digests[f'{split}-{mode}-0']
                for repeat in range(4):assert digests[f'{split}-{mode}-{repeat}']==expected
        for split in study.SPLITS:
            assert digests[f'{split}-closure-0']==digests[f'{split}-lazy-0']
        con=sqlite3.connect(path)
        try:
            with con:
                for t,entries in merged.items():con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',[(k,v) for k,v in entries.items() if k not in initial[t]])
        finally:con.close()
        parts=[]
        for field in ('transported_partition_study','probed_partition_study','ranked_binary_targets',
                'binary_routing','bipolar_routing','prepared_cofactors','cofactor_handoff','partition_preparation',
                'binary_interactions','live_fallback','joint_backbone','consequence_priority','preimage_fusion','joint_prefix'):
            parts.extend(study.bound(parent[field]['partitions']))
        assert len(parts)==342
        stored,readers=audit(path,parts=parts)
        for t in TABLES:assert initial[t].items()<=stored[t].items() and stored[t]==merged[t]
        print('audited cumulative union',flush=True)
        (out/'union').mkdir(exist_ok=True);old_archive=base.archive(path,out/'union')
        archive=old_archive;conversion=None
        if archive['compressed_bytes']>96*1024*1024:
            archive=split_archive(old_archive,out/'union-parts');tick=time.perf_counter()
            roundtrip=temp/'roundtrip';restore_archive(archive,roundtrip);assert base.sha(roundtrip)==base.sha(path)
            conversion=dict(compressed_sha256=old_archive['sha256'],roundtrip_seconds=time.perf_counter()-tick,
                roundtrip_byte_identical=True,reader='experiments.cnf_archive_parts.restore_archive')
            roundtrip.unlink();Path(old_archive['path']).unlink()
    sources={**p['source_fingerprints'],'experiments/validate_cnf_probe_binary_lazy.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        probe_binary_lazy=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),analysis=study.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',cp)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        query_audits=1728,census_events=len(events),census_verdicts=dict(verdicts),census_lazy_counters=dict(lazy_counts),preserved_tables={t:len(x) for t,x in merged.items()},new_records=dict(added),
        alternative_payload_observations=dict(alternatives),previous_partition_records=len(parts),readers=readers,audits=audits,
        archive_conversion=conversion,plan_audits=plan_audits,pool_audits=pool_audits,table_digests=digests,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,limitations=[
            'Every preceding authority payload is unchanged; raw trials retain alternative proofs. All six naive/lazy table payloads and complete result contents except counters and timings are identical; controls may retain different proofs.',
            'Both native readers audit every retained node and all 342 preceding partition records. Per-query ID chronology is checked for four tables; full replay checks all six.',
            'All 353 preceding census cofactors reproduce the exact complete UP binding, binary decisions and canonical certificates. The initial test-only error querying absent lazy-created legacy tables remains preserved.',
            'Historical audit, census re-evaluation and tests are outside serial matched timings. This is not a polynomial guarantee, a lower-bound result or proof of expanded structural coverage.'])
    base.write(out/'validation.json',v)
    print(base.encode({k:v[k] for k in ('passed','query_audits','preserved_tables','new_records','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
