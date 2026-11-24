#!/usr/bin/env python3
"""Verify binary closure, unchanged census prefixes, and all cumulative authority."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json,sqlite3,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_binary_closure as study
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.validate_cnf_ranked_binary_targets import TABLES
from experiments.cnf_archive_parts import split_archive,restore_archive
from experiments.cnf_partial_proof_plan import check_plan,survival
from experiments.cnf_conditional_unit_support import check_template
from experiments import cnf_residual_dag as native
from experiments.cnf_probe_binary_census import closure
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
    assert (len(manifests),artifacts)==(158,14286)
    report=base.load(out/'report.json');assert report['protocol']==study.binding(out/'protocol.json')
    assert len(report['samples'])==16
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
    previous=base.load(study.PARENT/'holdout-transfer-0/queries.json')
    for a,b in zip(records[('exposed','current',0)],previous):
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
    census=base.load(out/'exploration/report.json');ep=study.bound(census['protocol'])
    assert ep['parent']==p['parent']
    for f,h in ep['source_fingerprints'].items():assert base.sha(f)==h,f
    diagnostic_rows=study.bound(census['queries']);events=study.bound(census['events'])
    assert len(diagnostic_rows)==68 and ep['targets']==[37,61,67]
    assert ep['cases']==study.bound(p['cases']['exposed'])[:68]
    for a,b in zip(diagnostic_rows,records[('exposed','current',0)]):
        assert (a['status'],a['metrics'])==(b['status'],b['metrics'])
    verdicts=Counter();event_counts=Counter()
    for e in events:
        assert e['case'] in ep['targets'];event_counts[e['case']]+=1
        probe_parent=tuple(map(tuple,e['parent']));assert normalize(probe_parent)[0]==probe_parent
        raw=native.restrict_scan(probe_parent,{e['variable']:e['value']},Counter())
        child,names=normalize(raw);key=native.token(child,Counter())
        assert (child,names,key)==(tuple(map(tuple,e['child'])),tuple(e['names']),e['root'])
        fixed,trace,conflict=native.propagate(child,Counter());assert conflict is None
        assert sorted(fixed.items())==list(map(tuple,e['fixed'])) and trace==e['trace']
        counts=Counter();got=closure((child,names,key),(fixed,trace,conflict,0),counts)
        assert json.loads(base.encode(got))==e['discovery'] and dict(counts)==e['counts']
        residual=normalize(native.restrict_scan(child,fixed,Counter()))[0]
        assert residual==tuple(map(tuple,e['discovery']['residual']))
        assert all(len(c)>=2 for c in residual)
        binary=tuple(c for c in residual if len(c)==2)
        model,proof=native.two_cnf(binary,Counter())
        assert (proof is not None)==(e['discovery']['status']=='binary-unsat')
        if model is not None:assert native.holds(binary,model)
        verdicts[e['discovery']['status']]+=1
        if e['discovery']['nodes']:assert e['discovery']['nodes'][-1]['key']==e['root']
    assert len(events)==353 and verdicts['binary-unsat']==19
    assert dict(event_counts)=={37:112,61:115,67:126}
    # These native proofs are isolated from search, so the exact census prefix
    # remains a valid control even when a candidate was not visited there.
    trials.append(dict(name='census-search',archive=census['search_archive'],cases=ep['cases'],rows=diagnostic_rows,diagnostic=True))
    trials.append(dict(name='census-proofs',archive=census['proof_archive'],cases=[],rows=[],diagnostic=True))
    added,alternatives=Counter(),Counter();audits=[];digests={}
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);path=temp/'union';restore_archive(parent['reference_union'],path)
        control=study.CLASSES['current'](temp/'census-control',node_limit=256)
        try:
            for c,old in zip(ep['cases'],diagnostic_rows):
                got=attempt(control,c['source'])
                assert (got['status'],got['metrics'])==(old['status'],old['metrics'])
            present={n for n, in control.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            exact_prefix={t:dict(control.db.execute(f'SELECT id,payload FROM {t}')) if t in present else {} for t in TABLES}
        finally:control.close()
        con=sqlite3.connect(path)
        try:initial={t:dict(con.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:con.close()
        merged=deepcopy(initial);known={k for entries in initial.values() for k in entries}
        for split in study.SPLITS:
            assert p['novelty'][split]==[dict(case=c['case'],known_in_parent=c['root'] in known) for c in study.bound(p['cases'][split])]
        for trial in trials:
            dest=temp/'trial';restore_archive(trial['archive'],dest)
            stored,counts=audit(dest,trial['cases'],trial['rows'])
            if trial['name']=='census-search':assert stored==exact_prefix
            if trial['name']=='census-proofs':
                for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                    checker=cls(dest)
                    try:
                        for event in events:
                            for item in event['discovery']['nodes']:
                                checker._verify(item['key'],item['node'])
                                assert checker._read(item['key'])['answer'] is False
                    finally:checker.close()
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
                    if trial['name']=='census-search':assert k in initial[t]
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
    sources={**p['source_fingerprints'],'experiments/validate_cnf_probe_binary_closure.py':base.sha(__file__)}
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        probe_binary_closure=dict(census=study.binding(out/'exploration/report.json'),protocol=study.binding(out/'protocol.json'),report=study.binding(out/'report.json'),analysis=study.binding(out/'analysis.json')))
    base.write(out/'checkpoint.json',cp)
    v=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        query_audits=1152,diagnostic_query_audits=68,census_exact_prefix_replay_queries=68,census_events=len(events),census_verdicts=dict(verdicts),preserved_tables={t:len(x) for t,x in merged.items()},new_records=dict(added),
        alternative_payload_observations=dict(alternatives),previous_partition_records=len(parts),readers=readers,audits=audits,
        archive_conversion=conversion,plan_audits=plan_audits,pool_audits=pool_audits,table_digests=digests,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,limitations=[
            'Every preceding authority payload is unchanged; raw trial archives preserve alternative proofs. Per-policy repeats have identical payloads; different policies may legitimately retain different proofs.',
            'Two readers verify all retained nodes, including budget-stopped prefixes, all isolated census certificates and all 342 prior partitions. Per-query ID logs track four tables; independent replay checks all six.',
            'The 353 census events reproduce exact source conditioning and UP. Separate binary decisions validate both misses and hits; the original chronological search and its counters remain unchanged.',
            'Census certificates do not imply the parent source is UNSAT, and satisfiable binary subsets do not decide their full cofactors. Every published new negative uses original native proof rules.',
            'Native dispatch cap 256 is not a bound on compiled probe certificates, checking, total runtime or memory. All new publication and recognition costs are charged.',
            'Cumulative audit and compression are outside matched means; the enlarged union preserves history rather than demonstrating bounded or compressed logical storage.'])
    base.write(out/'validation.json',v)
    print(base.encode({k:v[k] for k in ('passed','query_audits','diagnostic_query_audits','preserved_tables','new_records','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
