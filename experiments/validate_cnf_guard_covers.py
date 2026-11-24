#!/usr/bin/env python3
"""Preserve prior authority and audit independently compiled cover witnesses."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_covers as study
from experiments.validate_cnf_guard_context import semantic
from experiments import cnf_residual_dag as native
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_archive_parts import restore_archive
from experiments.validate_cnf_whole_proof_reuse import audit
base=study.base;old=study.old
EXTRA=('experiments/study_cnf_guard_covers.py','experiments/close_cnf_guard_covers.py',
       'solver/test_cnf_guard_cover_census.py','experiments/validate_cnf_guard_covers.py')


def audit_archive(report, checked):
    a=report['archive'];assert base.sha(a['path'])==a['sha256']
    if a['sha256'] in checked:return
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';restore_archive(a,path);assert base.sha(path)==a['database_sha256']
        if 'query' in report:
            tick=time.perf_counter();query=report['query']
            stored,counts=audit(path,[dict(source=query['source'])],[query['verdict']])
            readers=dict(combined=time.perf_counter()-tick)
            keys=[key for rows in stored.values() for key in rows]
            assert {t:len(rows) for t,rows in stored.items()}==report['authority_tables']
        else:
            readers={}
            for cls in (native.ResidualSolver,CanonicalVerifySnapshot):
                tick=time.perf_counter();s=cls(path)
                try:
                    keys=[r[0] for r in s.db.execute('SELECT id FROM cnf_residual_v1 ORDER BY id')]
                    for key in keys:assert s._read(key) is not None
                    if report['root'] is not None:assert not s._read(report['root'])['answer']
                finally:s.close()
                readers[cls.__name__]=time.perf_counter()-tick
        assert len(keys)==report['nodes']
    checked[a['sha256']]=dict(archive=a,nodes=len(keys),readers_seconds=readers)


def validate(out):
    started=time.perf_counter();serial=out/'serial';p=base.load(serial/'protocol.json');parent=old.bound(p['parent'])
    pv=base.load(study.PARENT/'validation.json');assert pv['passed']
    manifests=deepcopy(pv['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(171,16500)
    sources={**p['source_fingerprints'],**{f:base.sha(f) for f in EXTRA}}
    for f,h in sources.items():assert base.sha(f)==h,f
    known={}
    for sample in base.load(study.PARENT/'comparisons.json')['samples']:
        if sample['mode']=='context' and sample['repeat']==0:
            r=old.bound(sample);known[r['target']]=(r,old.bound(r['result']))
    groups={};reused=[];event_totals=Counter();event_count=0
    for directory in (out,serial):
        pp=base.load(directory/'protocol.json');comparison=base.load(directory/'comparisons.json')
        assert pp==p and comparison['protocol']==old.binding(directory/'protocol.json')
        seen=set()
        for sample in comparison['samples']:
            r=old.bound(sample);v=old.bound(r['result']);target=sample['target'];ref,rv=known[target]
            assert r['protocol']==comparison['protocol'] and r['target']==target and r['mode']==sample['mode']
            assert semantic(v)==semantic(rv)
            for f in ('digest','added','payload_bytes','native_checked_bytes'):assert r[f]==ref[f],(target,f)
            for f in ('database_bytes','database_sha256','compressed_bytes','sha256'):assert r['archive'][f]==ref['archive'][f],(target,f)
            assert base.sha(r['archive']['path'])==r['archive']['sha256']
            key=(target,sample['mode'],sample['repeat']);assert key not in seen;seen.add(key)
            if sample['mode']=='census':
                events=old.bound(r['events']);other=base.load(out/f'target-{target}-census-0/events.json')
                assert events['events']==other['events']
                if directory==serial and sample['repeat']==0:
                    event_count+=len(events['events'])
                    for event in events['events']:event_totals.update(event['counts'])
            if directory==serial:groups.setdefault((target,sample['mode']),[]).append((r,v))
        assert len(seen)==32 and seen=={(t,m,r) for t in p['targets'] for m in study.MODES for r in (0,1)}
        reused.append(dict(comparisons=old.binding(directory/'comparisons.json'),authority=old.binding(study.PARENT/'validation.json'),identical_trials=32))
    ag={};summary={}
    for (target,mode),values in groups.items():
        r,v=values[0];c=Counter()
        for metric in ('solve_seconds','complete_seconds','cold_seconds','warm_seconds','peak_rss_bytes'):
            c['mean_'+metric]=sum(x[metric] for x,_ in values)/len(values)
        if mode=='census':
            c['mean_observation_seconds']=sum(old.bound(x['events'])['observation_seconds'] for x,_ in values)/len(values)
            c['mean_event_bytes']=sum(x['event_bytes'] for x,_ in values)/len(values)
        c['database_bytes']=r['archive']['database_bytes'];c['native_checked_bytes']=r['native_checked_bytes']
        ag.setdefault(mode,Counter()).update(c);summary.setdefault(str(target),{})[mode]=dict(c)
        assert v['result']['status']=='unresolved'
    audits={};controlled=[]
    for directory in (out,serial):
        d=base.load(directory/'controlled.json');protocol=old.bound(d['protocol'])
        assert protocol['source']['sha256']==base.sha('experiments/study_cnf_guard_covers.py')
        assert len(d['rows'])==16 and len(d['misses'])==3
        for miss in d['misses']:
            assert miss['native_result']['answer'] is True
            model={int(k):v for k,v in miss['native_result']['model'].items()}
            assert all(type(v) is bool for v in model.values()) and native.holds(miss['source'],model)
        for case in d['rows']:
            row=dict(width=case['width'],variant=case['variant'],repeat=case['repeat'],preparation_seconds=case['preparation_seconds'],arms={})
            for mode,binding in case['arms'].items():
                r=old.bound(binding);assert r['status']=='unsat';audit_archive(r,audits)
                row['arms'][mode]={k:r[k] for k in ('solve_seconds','warm_seconds','nodes','record_bytes','charged_acquisition_and_solve_seconds','cold_readers_seconds','persistence_seconds')}
            if directory==serial:controlled.append(row)
    closures=base.load(serial/'closures.json');clp=old.bound(closures['protocol'])
    assert clp['source']['sha256']==base.sha('experiments/close_cnf_guard_covers.py')
    assert clp['comparisons']==old.binding(serial/'comparisons.json') and closures['census_counts']==dict(event_totals)
    closure_summary=Counter();local_rows=[]
    for row in closures['records']:
        closure_summary[row['status']]+=1;closure_summary['already_closed_sites']+=row['site_closed']
        if row['status']!='compiled':continue
        assert not row['missing_support'];arms={}
        for mode,binding in row['arms'].items():
            r=old.bound(binding);audit_archive(r,audits)
            arms[mode]={k:r[k] for k in ('status','solve_seconds','nodes','record_bytes','cold_readers_seconds','persistence_seconds')}
        if not row['site_closed']:closure_summary['distinct_old_inconclusive_roots']+=1
        if not row['present_after_native_query']:closure_summary['distinct_roots_absent_after_query']+=1
        local_rows.append(dict(target=row['target'],event=row['event'],old_site_closed=row['site_closed'],present_after_native_query=row['present_after_native_query'],
            support_seconds=row['support_seconds'],arms=arms))
    analysis=dict(summary=summary,aggregates=ag,events=event_count,event_counts=dict(event_totals),
        closure_summary=dict(closure_summary),local_comparisons=local_rows,controlled=controlled,
        expanded_discovery=dict(events=len(closures['expanded_discovery']),
            candidates=sum(e['cover'] is not None for e in closures['expanded_discovery']),
            seconds=sum(e['seconds'] for e in closures['expanded_discovery']),
            limitation=closures['expanded_discovery_limitation']),
        limitations=p['limitations']+clp['limitations']+[
            'Initial comparisons and controlled timings are preserved but excluded from reported timing aggregates because tests overlapped part of that run. Serial workers ran after both initial comparisons and tests finished.',
            'Peak RSS includes retained diagnostic events and is reported as a sum of per-case means, not a simultaneous peak. Per-event peak_reach_vertices are not additive memory bounds.',
            'Cumulative bank is unchanged. Newly checked standalone native proof archives are checkpoint-referenced supplemental banks, not automatically loaded into live search or merged into the causal prefix.'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        guard_covers=dict(protocol=old.binding(serial/'protocol.json'),comparisons=old.binding(serial/'comparisons.json'),
            initial_comparisons=old.binding(out/'comparisons.json'),controlled=old.binding(serial/'controlled.json'),
            closures=old.binding(serial/'closures.json'),analysis=old.binding(out/'analysis.json'),
            supplemental_archives=[a['archive'] for a in audits.values()]))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],
        preserved_tables=pv['preserved_tables'],new_cumulative_records=0,reused_query_audits=reused,
        supplemental_archive_audits=list(audits.values()),checkpoint=old.binding(out/'checkpoint.json'),
        seconds=time.perf_counter()-started,limitations=analysis['limitations']))
    print(base.encode(dict(passed=True,events=event_count,closure_summary=closure_summary,aggregates=ag,
                          supplemental_archives=len(audits),sources=len(sources))),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
