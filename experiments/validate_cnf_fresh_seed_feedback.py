#!/usr/bin/env python3
"""Audit new source-only transfer, explicit unresolved cases and cost controls."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,statistics,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_fresh_seed_feedback as s
base=s.base;old=s.old


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(221,33634)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_fresh_seed_feedback.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1223
    rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);labels=old.bound(p['truth']);assert s.panel()==(rows,desc)
    counts=Counter();refuted=[];remaining=[];families={};chain_metrics={}
    for row in rows:
        key=row['id'];assert labels[key]==s.truth(row['source']);chain=old.bound(p['chains'][key]);cc=Counter()
        s.k.validate(row['source'],chain,cc);actual,search=s.k.discover(row['source'],Counter(),**p['discovery_limits']);assert actual==chain
        answer=labels[key]['answer'];closed=chain['status']=='refuted';assert not closed or answer is False
        counts['sat' if answer else 'unsat']+=1;counts['refuted' if closed else 'unresolved']+=1
        family=desc[key]['family'];families.setdefault(family,Counter()).update(['sat' if answer else 'unsat','refuted' if closed else 'unresolved'])
        chain_metrics[key]=dict(status=chain['status'],reason=chain['reason'],levels=len(chain['levels']),bytes=Path(p['chains'][key]['path']).stat().st_size)
        if closed:refuted.append(key)
        elif not answer:remaining.append(dict(**row,description=desc[key],chain=p['chains'][key],reason=chain['reason']))
    assert dict(counts)==dict(sat=22,unsat=14,refuted=8,unresolved=28) and len(remaining)==6
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==18
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(6)}
    control=base.load(out/'timing-control.json');assert control['replaced'] and control['affected_repeat']==5
    initial=base.load(out/'comparisons-initial.json')['samples'];assert len(initial)==18
    for sample in initial:old.bound(sample)
    assert [r for r in samples if r['repeat']!=5]==[r for r in initial if r['repeat']!=5]
    assert all(r==control['replacements'][r['mode']] for r in samples if r['repeat']==5)
    groups={};audits={}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];assert r['mode']==mode and r['panel']==p['panel'];groups.setdefault(mode,[]).append(r)
        assert len(r['results'])==len(rows)==len(r['cases'])
        for row,result,case in zip(rows,r['results'],r['cases']):
            key=row['id'];assert case['id']==key and result['answer']==labels[key]['answer']
            expected=s.compiler.native.token(s.compiler.native.normalize(row['source'])[0],Counter());assert result['root']==expected
            if result['answer']:assert s.compiler.native.holds(row['source'],{int(k):v for k,v in result['model'].items()})
            expected_route='feedback' if mode!='fresh' and key in refuted else 'fresh';assert case['route']==expected_route
            if expected_route=='feedback':
                assert result['authority']=='native'
                assert sum(case['counts'].get(x,0) for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=p['unit_work_limit']
            if mode=='online':
                dest=Path(sample['path']).parent
                assert base.load(dest/(key+'-chain.json'))==old.bound(p['chains'][key])
                _,expected_search=s.k.discover(row['source'],Counter(),**p['discovery_limits'])
                assert base.load(dest/(key+'-search.json'))==expected_search
        assert r['warm_counts'].get('source_feedback_root_hits',0)==(0 if mode=='fresh' else 8)
        archive=r['archive'];assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';s.prior.previous.restore_archive(archive,db);readers=s.audit(db,rows,r['results'])
                import sqlite3
                conn=sqlite3.connect(db)
                try:tables=old.tables(conn)
                finally:conn.close()
            assert r['records']==sum(map(len,tables.values()))
            assert r['record_bytes']==sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items())
            assert r['digest']=={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}
            audits[archive['sha256']]=dict(archive=archive,readers=readers)
    totals={};rss={};sizes={};per_case={}
    for mode,rs in groups.items():
        for r in rs:
            for key in ('counts','native_counts','warm_counts','warm_native_counts','results','digest','records','record_bytes','loaded_chain_bytes','new_history_bytes'):
                assert r[key]==rs[0][key],(mode,key)
        keys=('input_seconds','complete_seconds','warm_seconds','cold_seconds','persistence_seconds','records','record_bytes','loaded_chain_bytes','new_history_bytes')
        totals[mode]={key:statistics.mean(r[key] for r in rs) for key in keys}
        totals[mode]['phases']={key:statistics.mean(r['phases'].get(key,0) for r in rs) for key in rs[0]['phases']}
        rss[mode]=max(r['peak_rss_bytes'] for r in rs);sizes[mode]=Path(rs[0]['archive']['path']).stat().st_size
        per_case[mode]={row['id']:statistics.mean(r['cases'][i]['solve_seconds'] for r in rs) for i,row in enumerate(rows)}
    assert groups['prepared'][0]['digest']==groups['online'][0]['digest']
    baseline=base.load(out/'baseline.json')
    assert all(labels[r['id']]==r['truth'] for r in baseline)
    selected='fresh';assert min(totals,key=lambda m:totals[m]['complete_seconds'])==selected
    analysis=dict(panel_size=len(rows),coverage=dict(counts),families={k:dict(v) for k,v in families.items()},refuted=sorted(refuted),remaining=[r['id'] for r in remaining],
        chain_metrics=chain_metrics,totals=totals,peak_rss_bytes=rss,archive_bytes=sizes,case_solve_seconds=per_case,selected=selected,
        prepared_vs_fresh_complete_percent=100*(totals['prepared']['complete_seconds']/totals['fresh']['complete_seconds']-1),
        online_vs_fresh_complete_factor=totals['online']['complete_seconds']/totals['fresh']['complete_seconds'],
        raw_record_growth_percent=100*(totals['prepared']['record_bytes']/totals['fresh']['record_bytes']-1),
        unique_archive_audits=len(audits),limitations=p['limitations'])
    base.write(out/'remaining.json',dict(scope='Feedback-unresolved but independently UNSAT fresh panel cases; the existing fallback solves them.',cases=remaining))
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['fresh_seed_feedback']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining')}
    cp['fresh_seed_feedback']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],remaining=analysis['remaining'],totals=totals,archive_bytes=sizes)))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','45b01fc5:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2218 tests in .*\n\nOK',full) and re.search(r'Ran 27 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['fresh_seed_feedback']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2218,focused_tests=27,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1218,final_sources=len(cp['source_fingerprints']),prior_manifests=221,prior_artifacts=33634,new_native_archives=len(v['supplemental_archive_audits']),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=222,next_artifacts=33634+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
