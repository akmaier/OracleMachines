#!/usr/bin/env python3
"""Replay complete bucket programs, operator proposals and preservation lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,sqlite3,statistics,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_semantic_buckets as s
base=s.base;old=s.old;k=s.k


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(224,35821)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_semantic_buckets.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1238
    rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);labels=old.bound(p['truth']);freeze=old.bound(p['freeze'])
    held,hd=s.panel();assert held==rows[6:] and hd=={key:desc[key] for key in hd};assert base.sha(out/'heldout.json')==freeze['sha256']
    prev=base.load(s.PARENT/'remaining.json')['cases'];assert rows[:6]==[dict(id='d-'+r['id'],source=r['source']) for r in prev if 'repeat_of' not in r['description']]
    for r in rows:assert labels[r['id']]==json.loads(base.encode(s.oracle(r['source'])))
    prior_keys={k.native.normalize(r['source'])[0] for r in base.load(s.PARENT/'panel.json')}
    overlaps=[r['id'] for r in held if k.native.normalize(r['source'])[0] in prior_keys]
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==16
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(4)}
    groups={};audits={};coverage={};totals={};cases={};rss={};sizes={};structural={}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];dest=Path(sample['path']).parent;groups.setdefault(mode,[]).append(report)
        assert report['panel']==p['panel'] and len(report['cases'])==len(report['results'])==34
        stored={};operators={};fallback_rows=[];fallback_results=[];certs={};shape=Counter()
        for row,result,case in zip(rows,report['results'],report['cases']):
            key=row['id'];assert case['id']==key and result['answer']==labels[key]['answer']
            if result['answer']:assert k.native.holds(row['source'],{int(v):b for v,b in result['model'].items()})
            assert result['root']==k.native.token(k.native.normalize(row['source'])[0],Counter())
            if mode!='fresh':
                cc=Counter();cnf,_=k.native.normalize(row['source'],cc);root=k.native.token(cnf,cc)
                if root in stored:
                    proof=stored[root];diag=dict(reason='exact-program-reuse');cc['bucket_source_hits']+=1
                else:
                    proof,diag=k.discover(row['source'],cc,reduce=mode!='raw',cache=operators if mode=='shared' else None,**p['limits'])
                    shape['steps']+=len(proof['steps']);factors=[k.leaf(c) for c in cnf]
                    for step in proof['steps']:
                        full={v for i in step['inputs'] for v in factors[i]['scope']}-{step['variable']}
                        shape['full_boundary_rows']+=1<<len(full);shape['retained_relation_rows']+=1<<len(step['scope'])
                        shape['removed_coordinates']+=len(full)-len(step['scope']);shape['choice_rows']+=1<<len(full)
                        removed=len(full)-len(step['scope'])
                        if removed:
                            kind='constant' if step['bits'] in (0,(1<<(1<<len(step['scope'])))-1) else 'nonconstant'
                            shape[kind+'_reduced_steps']+=1;shape[kind+'_removed_coordinates']+=removed
                        factors.append(dict(scope=step['scope'],bits=step['bits']))
                assert diag==case['diagnostic']==base.load(dest/(key+'-diagnostic.json'))
                disk=base.load(dest/report['stored'][root]);assert proof==disk
                stored[root]=proof;certs[report['stored'][root]]=disk
                got=k.check_certificate(row['source'],disk,cc)
                assert case['route']==('bucket' if got['answer'] is not None else 'fresh')
                if got['answer'] is not None:assert got['answer']==result['answer']
                assert dict(cc)==case['counts'],(mode,key)
            if case['route']=='fresh':fallback_rows.append(row);fallback_results.append(result)
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==certs
        cache_records=[dict(key=key,value=value) for key,value in sorted(operators.items())]
        assert json.loads(gzip.decompress((dest/'operators.json.gz').read_bytes()))==json.loads(base.encode(cache_records))
        assert report['operator_entries']==len(operators) and report['operator_encoded_bytes']==len(base.encode(cache_records).encode())
        assert report['certificate_bytes']==sum((dest/f).stat().st_size for f in report['stored'].values())
        if mode not in structural:structural[mode]=dict(shape)
        else:assert structural[mode]==dict(shape)
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';db.write_bytes(gzip.decompress(Path(archive['path']).read_bytes()));assert base.sha(db)==archive['database_sha256']
                readers=s.prior.prior.prior.audit(db,fallback_rows,fallback_results);conn=sqlite3.connect(db)
                try:tables=old.tables(conn)
                finally:conn.close()
            assert report['records']==sum(map(len,tables.values()))
            assert report['record_bytes']==sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items())
            assert report['digest']=={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}
            audits[archive['sha256']]=dict(archive=archive,readers=readers)
    for mode,reports in groups.items():
        r=reports[0]
        for q in reports:
            for key in ('results','counts','solver_counts','warm_counts','cold_counts','records','record_bytes','stored','certificate_bytes','certificate_compressed_bytes','operator_entries','operator_encoded_bytes','operator_compressed_bytes','diagnostic_bytes','digest'):
                assert q[key]==r[key],(mode,key)
        keys=('complete_seconds','input_seconds','cold_seconds','warm_seconds','persistence_seconds','records','record_bytes','certificate_bytes','certificate_compressed_bytes','operator_encoded_bytes','operator_compressed_bytes','diagnostic_bytes')
        totals[mode]={key:statistics.mean(q[key] for q in reports) for key in keys}
        totals[mode]['phases']={key:statistics.mean(q['phases'][key] for q in reports) for key in r['phases']}
        rss[mode]=max(q['peak_rss_bytes'] for q in reports);sizes[mode]=r['archive']['compressed_bytes']+r['certificate_compressed_bytes']+r['operator_compressed_bytes']
        cov=Counter();per=[]
        for i,(row,case) in enumerate(zip(rows,r['cases'])):
            key=row['id'];cohort='development' if key.startswith('d-') else 'repeats' if 'repeat_of' in desc[key] else 'unique_panel'
            cov[cohort+'_cases']+=1;cov[cohort+'_direct']+=case['route']=='bucket';cov[cohort+'_sat']+=labels[key]['answer']
            per.append(dict(id=key,description=desc[key],diagnostic=case['diagnostic'],answer=labels[key]['answer'],route=case['route'],counts=case['counts'],
                discovery_seconds=statistics.mean(q['cases'][i].get('discovery_seconds',0) for q in reports),solve_check_seconds=statistics.mean(q['cases'][i]['solve_check_seconds'] for q in reports)))
        coverage[mode]=dict(cov);cases[mode]=per
    assert coverage['raw']==coverage['reduced']==coverage['shared']
    assert (coverage['shared']['development_direct'],coverage['shared']['unique_panel_direct'],coverage['shared']['repeats_direct'])==(2,18,4)
    assert groups['reduced'][0]['stored']==groups['shared'][0]['stored']
    for file in groups['reduced'][0]['stored'].values():assert base.sha(out/'reduced-0'/file)==base.sha(out/'shared-0'/file)
    remaining=[dict(**row,description=desc[row['id']],truth=labels[row['id']],reason=case['diagnostic']) for row,case in zip(rows,cases['shared']) if case['route']=='fresh']
    assert len(remaining)==10 and all(r['reason']['reason']=='bag-width' and r['reason']['spent']==0 for r in remaining)
    analysis=dict(panel_size=34,truth=dict(Counter('sat' if labels[r['id']]['answer'] else 'unsat' for r in rows)),coverage=coverage,exact_prior_duplicates=overlaps,
        remaining=[r['id'] for r in remaining],totals=totals,peak_rss_bytes=rss,combined_compressed_bytes=sizes,case_stats=cases,structural=structural,
        counts={m:rs[0]['counts'] for m,rs in groups.items()},
        comparisons_percent={name:100*(totals[a]['complete_seconds']/totals[b]['complete_seconds']-1) for name,a,b in (('reduced_vs_raw','reduced','raw'),('shared_vs_reduced','shared','reduced'),('shared_vs_fresh','shared','fresh'))},
        paired_percent={name:[100*(groups[a][i]['complete_seconds']/groups[b][i]['complete_seconds']-1) for i in range(4)] for name,a,b in (('reduced_vs_raw','reduced','raw'),('shared_vs_reduced','shared','reduced'),('shared_vs_fresh','shared','fresh'))},
        unique_archive_audits=len(audits),selected=min(totals,key=lambda m:totals[m]['complete_seconds']),limitations=p['limitations'])
    assert analysis['selected']=='fresh'
    base.write(out/'analysis.json',analysis);base.write(out/'remaining.json',dict(scope='Initial complete incident buckets exceed width eight; no semantic reduction starts. Existing fallback decides all.',cases=remaining))
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['semantic_buckets']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining')}
    cp['semantic_buckets']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],
        preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('coverage','comparisons_percent','remaining','structural','exact_prior_duplicates')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','8fe48c30:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';oldproofs=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(oldproofs)==66 and len(proofs)==67 and proofs[:66]==oldproofs
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2242 tests in .*\n\nOK',full) and re.search(r'Ran 21 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['semantic_buckets']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2242,focused_tests=21,old_proof_blocks_unchanged=66,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1233,final_sources=1238,prior_manifests=224,prior_artifacts=35821,checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=225,next_artifacts=35821+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
