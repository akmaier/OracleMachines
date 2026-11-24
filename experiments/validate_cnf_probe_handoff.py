#!/usr/bin/env python3
"""Replay every authority, preserve chronology, and compare exact handoff bytes."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_handoff as study
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.validate_cnf_ranked_binary_targets import TABLES
from experiments.cnf_archive_parts import split_archive,restore_archive
from experiments.cnf_partial_proof_plan import check_plan,survival
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_residual_dag import normalize
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
    assert (len(manifests),artifacts)==(156,13984)
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    assert len(report['samples'])==24
    trials=[];records={}
    for sample in report['samples']:
        r=study.bound(sample);rows=study.bound(r['queries']);cases=study.bound(p['cases'][sample['split']])
        assert len(rows)==len(cases)==72
        records[(sample['split'],sample['mode'],sample['repeat'])]=rows
        trials.append(dict(name=f"{sample['split']}-{sample['mode']}-{sample['repeat']}",archive=r['archive'],cases=cases,rows=rows))
    for split in study.SPLITS:
        control=records[(split,'priority',0)]
        for mode in study.MODES:
            ref=records[(split,mode,0)]
            for repeat in range(1,4):
                for a,b in zip(ref,records[(split,mode,repeat)]):
                    for k in ('case','status','new_ids','metrics'):assert a[k]==b[k],(split,mode,k)
            for a,b in zip(ref,control):
                for k in ('status','new_ids'):assert a[k]==b[k],(split,mode,a['case'],k)
                assert a['metrics'].get('expanded_nodes',0)==b['metrics'].get('expanded_nodes',0)
                if a['result'] is not None:
                    for k in ('answer','model','root','authority','whole_plan','whole_pool'):
                        assert a['result'].get(k)==b['result'].get(k),(split,mode,a['case'],k)
                if mode!='priority':
                    c=a['metrics']
                    assert c['whole_handoff_peak_bytes']<=p['capacities'][mode]
                    assert c['whole_handoff_admissions']==c['whole_handoff_consumed']+c['whole_handoff_discarded']
                    assert c.get('handoff_canonical_reuses',0)==c.get('handoff_selected',0)
                    assert c.get('handoff_propagation_reuses',0)<=c.get('handoff_selected',0)
    previous=base.load(study.PARENT/'holdout-priority-0/queries.json')
    for a,b in zip(records[('exposed','priority',0)],previous):
        for k in ('status','new_ids','metrics'):assert a[k]==b[k],(a['case'],k)
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
    for folder,mode in (('exploration','small'),('exploration-large','large')):
        e=base.load(out/folder/'inspection.json');rows=study.bound(e['queries'])
        assert e['parent']==p['parent'] and len(rows)==41
        assert e['cases']==study.bound(p['cases']['exposed'])[:41]
        for a,b in zip(rows,records[('exposed',mode,0)]):assert (a['status'],a['metrics'])==(b['status'],b['metrics'])
        trials.append(dict(name=folder,archive=e['archive'],cases=e['cases'],rows=rows,diagnostic=True))
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
                if trial.get('diagnostic'):continue
                for t in study.TABLES:
                    assert not available[t].intersection(r['new_ids'][t]);available[t].update(r['new_ids'][t])
                    assert available[t]<=stored[t].keys()
                if r['result'] is not None:assert r['result']['root']==c['root'] and any(c['root'] in ids for ids in available.values())
            if not trial.get('diagnostic'):assert all(available[t]==stored[t].keys() for t in study.TABLES)
            for t,entries in stored.items():
                for k,payload in entries.items():
                    if trial.get('diagnostic'):assert k in initial[t]
                    if k in merged[t]:
                        assert json.loads(payload).get('answer')==json.loads(merged[t][k]).get('answer')
                        alternatives[t]+=payload!=merged[t][k]
                    else:merged[t][k]=payload;added[t]+=1
            audits.append(dict(name=trial['name'],tables={t:len(x) for t,x in stored.items()},readers=counts))
            dest.unlink();print('audited',trial['name'],flush=True)
        for split in study.SPLITS:
            expected=digests[f'{split}-priority-0']
            for mode in study.MODES:
                for repeat in range(4):assert digests[f'{split}-{mode}-{repeat}']==expected
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
    sources={**p['source_fingerprints'],'experiments/validate_cnf_probe_handoff.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        probe_handoff=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),analysis=study.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',cp)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        query_audits=1728,diagnostic_query_audits=82,preserved_tables={t:len(x) for t,x in merged.items()},new_records=dict(added),
        alternative_payload_observations=dict(alternatives),previous_partition_records=len(parts),readers=readers,audits=audits,
        archive_conversion=conversion,plan_audits=plan_audits,pool_audits=pool_audits,table_digests=digests,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,limitations=[
            'Every preceding authority payload is unchanged; raw archives preserve alternative proofs. All six table payloads are byte-identical across the three arms of each matched stream.',
            'Two readers verify all retained nodes, including budget-stopped prefixes, and all 342 prior partitions. Per-query ID logs track four authority tables; independent replay checks all six.',
            'No nonconflicting propagation or local preparation offer confers verdict authority. Exact correspondence tests and unchanged proof checkers are separate obligations.',
            'Selected handoff-payload charge is not total RSS. Retained ancestor offers may block useful descendant admissions. Complete-worker and solve timings include all attempted handoff work.',
            'Cumulative validation, compression, diagnostics and profiling are outside matched means; transport chunking does not reduce logical storage growth.'])
    base.write(out/'validation.json',v)
    print(base.encode({k:v[k] for k in ('passed','query_audits','diagnostic_query_audits','preserved_tables','new_records','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
