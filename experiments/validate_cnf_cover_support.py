#!/usr/bin/env python3
"""Audit support-only composition, prior preservation, and the reuse stream."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cover_support as study
from experiments.cnf_archive_parts import restore_archive
from experiments.validate_cnf_whole_proof_reuse import audit
from experiments.cnf_guard_cover_support import select_support
from experiments.cnf_guard_shortening_gap import evidence
base=study.base;old=study.old


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    assert pv['passed'] and p['parent_manifest']==old.binding(study.PARENT/'manifest.json')
    manifests=deepcopy(pv['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(172,16947)
    extra=('experiments/validate_cnf_cover_support.py','experiments/cnf_guard_shortening_gap.py')
    sources={**p['source_fingerprints'],**{f:base.sha(f) for f in extra}}
    for f,h in sources.items():assert base.sha(f)==h,f
    cases=[old.bound(x) for x in p['cases']];proposals=old.bound(p['proposals'])
    assert len(cases)==26 and len(proposals['records'])==22
    assert Counter(r['status'] for r in proposals['records'])==dict(selected=18,duplicate=4)
    assert all(not r['missing_support'] and r['present_after_query'] for r in proposals['records'])
    assert len([r for r in proposals['records'] if r['category']=='relaxed'])==7
    comparison=base.load(out/'comparisons.json');assert comparison['protocol']==old.binding(out/'protocol.json')
    groups={};audits={};archives=[];support_roots={}
    def inspect(report,source,result):
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] in audits:return
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';restore_archive(archive,path);assert base.sha(path)==archive['database_sha256']
            stored,readers=audit(path,[dict(source=source)],[result])
            assert report['authority_tables']=={t:len(rows) for t,rows in stored.items()}
            assert report['digest']=={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in stored.items()}
            assert report['record_bytes']==sum(len(k.encode())+len(v.encode()) for rows in stored.values() for k,v in rows.items())
        audits[archive['sha256']]=dict(archive=archive,authority_tables=report['authority_tables'],readers=readers)
        archives.append(archive)
    for sample in comparison['samples']:
        r=old.bound(sample);index=sample['index'];case=cases[index];mode=sample['mode'];repeat=sample['repeat']
        assert r['protocol']==comparison['protocol'] and r['case']==p['cases'][index] and r['mode']==mode
        assert r['result']['status']=='unsat' and r['result']['result']['root']==case['root']
        assert r['category']==case['category']
        inspect(r,case['source'],r['result'])
        if mode=='support':
            c=Counter();support,ids,needed,used=select_support(case['source'],case['hints'],case['graph'],case['cover'],c,
                **{k:p['discovery'][k] for k in ('width_limit','path_limit')})
            for k,v in c.items():assert r['counts'].get(k,0)>=v
            assert r['warm_counts']['enclosing_root_hits']==1 and r['warm_counts'].get('support_wrappers',0)==0
            if len(support)<len(case['source']):
                assert r['counts']['support_wrappers']==1 and r['counts']['support_root_publications']==1
            else:assert r['counts']['full_support_fallbacks']==1
            support_roots[index]=dict(source_clauses=len(case['source']),source_literals=sum(map(len,case['source'])),
                selected_clauses=len(support),selected_literals=sum(map(len,support)))
        groups.setdefault((index,mode),[]).append((r,repeat))
    assert len(comparison['samples'])==156 and set(groups)=={(i,m) for i in range(len(cases)) for m in study.MODES}
    for key,rows in groups.items():
        assert len(rows)==2 and {repeat for _,repeat in rows}=={0,1}
        a,b=rows[0][0],rows[1][0]
        assert a['digest']==b['digest'] and a['archive']['database_sha256']==b['archive']['database_sha256']
        assert a['counts']==b['counts'] and a['native_counts']==b['native_counts'] and a['warm_counts']==b['warm_counts']
    # Preserve the matched earlier native/full controls, including alternative
    # ordinary authority tables; timing-only solve_seconds differs.
    prior=old.bound(parent['guard_covers']['closures']);control_checks=[]
    by_event={(r['target'],r['event']):r for r in prior['records'] if r['status']=='compiled'}
    for i,case in enumerate(cases):
        if case['category']!='bounded':continue
        previous=by_event[(case['target'],case['event'])]
        for mode,oldmode in (('fresh','fresh'),('full','cover')):
            ref=old.bound(previous['arms'][oldmode]);r=groups[(i,mode)][0][0]
            assert ref['archive']['database_sha256']==r['archive']['database_sha256']
            assert ref['record_bytes']==r['record_bytes'] and ref['authority_tables']==r['authority_tables']
            control_checks.append(dict(case=case['name'],mode=mode,authority=previous['arms'][oldmode]))
    summary=[];aggregates={};charged=Counter()
    for i,case in enumerate(cases):
        row=dict(name=case['name'],category=case['category'],support=support_roots[i],arms={})
        if case['category']!='controlled':
            row['common_preparation_seconds']=case['support_seconds']+case['discovery_seconds']
            charged[case['category']]+=row['common_preparation_seconds']
        else:row['common_preparation_seconds']=case['supplied_preparation_seconds']
        for mode in study.MODES:
            rs=[r for r,_ in groups[(i,mode)]];r=rs[0]
            data={k:r[k] for k in ('record_bytes','authority_tables','counts')}
            data.update({'mean_'+k:sum(r[k] for r in rs)/len(rs) for k in
                ('setup_seconds','solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','peak_rss_bytes')})
            data['database_bytes']=r['archive']['database_bytes'];data['compressed_bytes']=r['archive']['compressed_bytes']
            row['arms'][mode]=data
            ag=aggregates.setdefault(case['category'],{}).setdefault(mode,Counter())
            ag.update({k:v for k,v in data.items() if type(v) in (int,float)})
            ag['records']+=sum(data['authority_tables'].values())
        summary.append(row)
    stream=base.load(out/'stream.json');assert stream['protocol']==comparison['protocol'] and len(stream['rows'])==16
    stream_summary={};stream_rows={};stream_checks=[]
    for binding in stream['rows']:
        r=old.bound(binding);inspect(r,r['source'],r['result']);mode=r['mode']
        assert r['result']['status']=='unsat'
        previous=stream_rows.get(mode)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'now';restore_archive(r['archive'],path)
            import sqlite3
            con=sqlite3.connect(path)
            try:now=old.tables(con)
            finally:con.close()
        if previous is not None:
            for t,rows in previous.items():assert rows.items()<=now[t].items()
            assert r['added']=={t:len(now[t])-len(previous[t]) for t in now}
        stream_rows[mode]=now
        if mode=='support' and not r['case'].endswith('-0'):
            assert r['counts']['support_root_hits']==1 and r['counts']['support_wrappers']==1
            assert sum(r['added'].values())==1 and r['counts'].get('published_nodes',0)==0
        ag=stream_summary.setdefault(mode,dict(solve_seconds=0.0,cold_seconds=0.0,complete_seconds=0.0,support_hits=0))
        for k in ('solve_seconds','cold_seconds','complete_seconds'):ag[k]+=r[k]
        ag.update(final_record_bytes=r['record_bytes'],final_records=sum(r['authority_tables'].values()),final_database_bytes=r['archive']['database_bytes'])
        ag['support_hits']+=r['counts'].get('support_root_hits',0)
        stream_checks.append(dict(case=r['case'],mode=mode,added=sum(r['added'].values()),counts=r['counts']))
    gap=base.load(out/'shortening-gap.json')
    assert Path(gap['source']['path']).resolve()==Path('experiments/cnf_guard_shortening_gap.py').resolve()
    assert gap['source']['sha256']==base.sha('experiments/cnf_guard_shortening_gap.py')
    assert base.encode(gap['evidence'])==base.encode(evidence())
    limitations=p['limitations']+[
        'All seven formerly unverified relaxed-budget proposals are supported and distinct, but their roots are already retained by ordinary search. No new final result is claimed.',
        'Cold full/ordinary controls for the original eleven cases reproduce the earlier database bytes exactly. New support proofs and all alternatives remain separate checkpoint-linked archives, with no change to the cumulative bank.',
        'Selection uses the first supplied support for each used guard and all clauses named by that template. No minimal core, optimal path, minimum proof, universal canonical form or per-process physical-memory bound is established.',
        'The six-variable shortening counterexample is exhaustively checked over 1024 assignment/subset pairs. It identifies a recognizer gap, not a new live policy, complete-solver failure or efficiency result.']
    base.write(out/'analysis.json',dict(summary=summary,aggregates=aggregates,common_preparation_seconds=dict(charged),
        stream=stream_summary,stream_checks=stream_checks,proposals=proposals['records'],limitations=limitations))
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        guard_cover_support={**{k:old.binding(out/(k+'.json')) for k in ('protocol','proposals','comparisons','stream','analysis','shortening-gap')},
                             'supplemental_archives':archives})
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],
        preserved_tables=pv['preserved_tables'],new_cumulative_records=0,comparison_trials=156,
        controls_unchanged=control_checks,supplemental_archive_audits=list(audits.values()),
        checkpoint=old.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began,limitations=limitations))
    print(base.encode(dict(passed=True,aggregates=aggregates,common_preparation_seconds=charged,stream=stream_summary,
        supplemental_archives=len(audits),sources=len(sources))),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
