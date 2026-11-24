#!/usr/bin/env python3
"""Audit complete-result arbitration, chronological authority and preservation."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_pool_priority as study
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.validate_cnf_ranked_binary_targets import TABLES
from experiments.cnf_partial_proof_plan import check_plan,survival
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_residual_dag import normalize
from experiments.cnf_archive_parts import split_archive,restore_archive
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
    assert (len(manifests),artifacts)==(155,13851)
    report=base.load(out/'report.json')
    assert report['protocol']==study.binding(out/'protocol.json')
    assert len(report['samples'])==24 and len(report['regressions'])==2
    trials=[];records={}
    for sample in report['samples']+report['regressions']:
        r=study.bound(sample);rows=study.bound(r['queries']);cases=study.bound(p['cases'][sample['split']])
        assert len(rows)==len(cases)==72
        records[(sample['split'],sample['mode'],sample['repeat'])]=rows
        trials.append(dict(name=f"{sample['split']}-{sample['mode']}-{sample['repeat']}",
            archive=r['archive'],cases=cases,rows=rows))
    for split in study.SPLITS:
        for mode in study.MODES:
            ref=records[(split,mode,0)]
            for repeat in range(1,4):
                for a,b in zip(ref,records[(split,mode,repeat)]):
                    for k in ('case','status','new_ids','metrics'):assert a[k]==b[k],k
            for a,b in zip(ref,records[(split,'completion',0)]):
                if a['result'] is not None and b['result'] is not None:assert a['status']==b['status']
    for mode in ('completion','reuse'):
        previous=base.load(study.PARENT/f'holdout-{mode}-0/queries.json')
        for a,b in zip(records[('exposed',mode,0)],previous):
            for k in ('status','new_ids','metrics'):assert a[k]==b[k],(mode,a['case'],k)
    previous=base.load(study.PARENT/'exposed-reuse-0/queries.json')
    for a,b in zip(records[('transfer','reuse',0)],previous):
        for k in ('status','new_ids','metrics'):assert a[k]==b[k],('transfer',a['case'],k)
    plan_audits=[];pool_audits=[]
    for (split,mode,repeat),rows in records.items():
        cases=study.bound(p['cases'][split]);earlier={}
        for c,r in zip(cases,rows):
            result=r['result'];counts=r['metrics']
            if mode=='priority':
                assert counts.get('whole_pool_gates',0)<=1
                assert counts.get('whole_pool_gates',0)==counts.get('whole_pool_misses',0)+counts.get('whole_pool_completed',0)
                assert counts.get('whole_plan_extractions',0)==counts.get('whole_pool_misses',0)
            if result is not None and 'whole_plan' in result:
                hint=result['whole_plan'];assert hint['origin'] in earlier
                check_plan(hint['plan']);canonical,_=normalize(c['source'])
                assert hint['outcome']['root']==c['root']
                assert survival(canonical,hint['plan'],Counter())==hint['outcome']['intact']
                for t in hint['plan']['templates']:
                    if t.get('open') is not True:assert check_template(t)<=earlier[hint['origin']]
                assert result['authority']=='native' and not hint['outcome']['stopped']
                plan_audits.append(dict(split=split,mode=mode,repeat=repeat,case=c['case'],origin=hint['origin'],root=c['root']))
            if result is not None and 'whole_pool' in result:
                hint=result['whole_pool'];assert mode=='priority' and hint['near_origin'] in earlier
                assert hint['route'] in ('negative-pool','witness-pool')
                assert result['answer']==(hint['route']=='witness-pool') and result['authority']=='native'
                assert counts.get('expanded_nodes',0)==0 and counts['whole_pool_completed']==1
                assert counts.get('whole_plan_extractions',0)==0 and 'whole_plan' not in result
                pool_audits.append(dict(split=split,repeat=repeat,case=c['case'],root=c['root'],**hint))
            if result is not None and result['answer'] is False and result['authority']=='native':
                earlier[result['root']]=set(normalize(c['source'])[0])
    added,alternatives=Counter(),Counter();audits=[];digests={}
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';base.restore_archive(parent['reference_union'],path)
        con=sqlite3.connect(path)
        try:initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:con.close()
        merged=deepcopy(initial);known={k for entries in initial.values() for k in entries}
        for split in study.SPLITS:
            assert p['novelty'][split]==[dict(case=c['case'],known_in_parent=c['root'] in known)
                for c in study.bound(p['cases'][split])]
        for trial in trials:
            dest=temp/'trial';base.restore_archive(trial['archive'],dest)
            stored,counts=audit(dest,trial['cases'],trial['rows'])
            digests[trial['name']]={t:base.key_sha(base.encode(sorted(entries.items()))) for t,entries in stored.items()}
            available={t:set() for t in study.TABLES}
            for c,r in zip(trial['cases'],trial['rows']):
                assert r['case']==c['case'] and r['metrics'].get('expanded_nodes',0)<=256
                for t in study.TABLES:
                    assert not available[t].intersection(r['new_ids'][t]);available[t].update(r['new_ids'][t])
                    assert available[t]<=stored[t].keys()
                if r['result'] is not None:
                    assert r['result']['root']==c['root'] and any(c['root'] in ids for ids in available.values())
            assert all(available[t]==stored[t].keys() for t in study.TABLES)
            for t,entries in stored.items():
                for k,payload in entries.items():
                    if k in merged[t]:
                        assert json.loads(payload).get('answer')==json.loads(merged[t][k]).get('answer')
                        alternatives[t]+=payload!=merged[t][k]
                    else:merged[t][k]=payload;added[t]+=1
            audits.append(dict(name=trial['name'],tables={t:len(x) for t,x in stored.items()},readers=counts))
            dest.unlink()
        con=sqlite3.connect(path)
        try:
            with con:
                for t,entries in merged.items():
                    con.executemany(f'INSERT INTO {t}(id,payload) VALUES (?,?)',[(k,v) for k,v in entries.items() if k not in initial[t]])
        finally:con.close()
        parts=[]
        for field in ('transported_partition_study','probed_partition_study','ranked_binary_targets',
                'binary_routing','bipolar_routing','prepared_cofactors','cofactor_handoff','partition_preparation',
                'binary_interactions','live_fallback','joint_backbone','consequence_priority','preimage_fusion','joint_prefix'):
            parts.extend(study.bound(parent[field]['partitions']))
        assert len(parts)==342
        stored,readers=audit(path,parts=parts)
        for t in TABLES:assert initial[t].items()<=stored[t].items() and stored[t]==merged[t]
        (out/'union').mkdir(exist_ok=True);archive=base.archive(path,out/'union')
        conversion=None
        if archive['compressed_bytes']>96*1024*1024:
            old_archive=archive;archive=split_archive(old_archive,out/'union-parts')
            tick=time.perf_counter();roundtrip=temp/'roundtrip';restore_archive(archive,roundtrip)
            assert base.sha(roundtrip)==base.sha(path)
            conversion=dict(compressed_sha256=old_archive['sha256'],
                roundtrip_seconds=time.perf_counter()-tick,roundtrip_byte_identical=True,
                reader='experiments.cnf_archive_parts.restore_archive')
            roundtrip.unlink();Path(old_archive['path']).unlink()

    sources={**p['source_fingerprints'],'experiments/validate_cnf_whole_pool_priority.py':base.sha(__file__),
        **{f:base.sha(f) for f in ('experiments/cnf_archive_parts.py','solver/test_cnf_archive_parts.py')}}
    cp=deepcopy(parent)
    cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        reference_union_reader='experiments.cnf_archive_parts.restore_archive',
        whole_pool_priority=dict(protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),
            analysis=study.binding(out/'analysis.json'),decision='Evaluate complete-pool priority before partial extraction; retain every miss, checked prefix and regression.'))
    base.write(out/'checkpoint.json',cp)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        query_audits=1728,regression_query_audits=144,preserved_tables={t:len(x) for t,x in merged.items()},
        new_records=dict(added),alternative_payload_observations=dict(alternatives),previous_partition_records=len(parts),
        readers=readers,audits=audits,archive_conversion=conversion,plan_audits=plan_audits,pool_audits=pool_audits,table_digests=digests,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,limitations=[
            'All earlier authoritative payloads are unchanged. Alternative valid proofs remain in raw trial archives.',
            'Cumulative gzip archives above 96 MiB are split into byte-bound 48 MiB files. The new backward-compatible restore helper validates descriptor, parts, concatenated gzip and database bytes; it adds no SAT authority. Old archives and policy sources remain unchanged.',
            'Per-query ID logs track four authority tables; independent replay checks and preserves all six. Parent novelty uses all six tables.',
            'Completed answers and every retained prefix node pass both native readers. Budget stops imply no verdict.',
            'Pool hits are checked native results, not predictions. Miss costs remain in the counters and serial timings.',
            'The transfer stream is a single paired regression replay and is excluded from four-repeat exposed/holdout means.',
            'Selected Python graph bytes exclude transient plans, query-log objects and native allocations. Dispatch counts exclude direct proof publications.'])
    base.write(out/'validation.json',v)
    print(base.encode({k:v[k] for k in ('passed','query_audits','regression_query_audits','preserved_tables','new_records','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
