#!/usr/bin/env python3
"""Replay boundary completeness, measured streams and immutable result lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,sqlite3,statistics,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_boundary as s
base=s.base;old=s.old;k=s.k


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(223,35068)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_affine_boundary.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1233
    rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);labels=old.bound(p['truth']);freeze=old.bound(p['freeze'])
    held,hd=s.panel();assert held==rows[5:] and hd=={key:desc[key] for key in hd};assert base.sha(out/'heldout.json')==freeze['sha256']
    previous=base.load(s.PARENT/'remaining.json')['cases'];assert rows[:5]==[dict(id='d-'+r['id'],source=r['source']) for r in previous]
    for r in rows:assert labels[r['id']]==json.loads(base.encode(s.oracle(r['source'])))
    old_keys={k.native.normalize(r['source'])[0] for r in base.load(s.PARENT/'panel.json')}
    overlaps=[r['id'] for r in held if k.native.normalize(r['source'])[0] in old_keys]
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==18
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(6)}
    groups={};audits={};coverage={};totals={};cases={};rss={};sizes={}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];dest=Path(sample['path']).parent;groups.setdefault(mode,[]).append(report)
        assert report['panel']==p['panel'] and not report['warm_changed'];assert len(report['cases'])==len(report['results'])==33
        stored={};fallback_rows=[];fallback_results=[];certs={}
        for row,result,case in zip(rows,report['results'],report['cases']):
            key=row['id'];assert case['id']==key and result['answer']==labels[key]['answer']
            if result['answer']:assert k.native.holds(row['source'],{int(v):b for v,b in result['model'].items()})
            assert result['root']==k.native.token(k.native.normalize(row['source'])[0],Counter())
            if mode!='fresh':
                cc=Counter();cnf,_=k.native.normalize(row['source'],cc);root=k.native.token(cnf,cc)
                if root in stored:
                    proof=stored[root];diagnostic=dict(status='exact-proof-reuse');cc['boundary_stream_proof_hits']+=1
                else:
                    proof,diagnostic=(k.discover if mode=='boundary' else s.full_discover)(row['source'],cc)
                assert diagnostic==case['diagnostic']==base.load(dest/(key+'-diagnostic.json'))
                if proof is not None:
                    disk=base.load(dest/report['stored'][root]);assert json.loads(base.encode(proof))==disk
                    stored[root]=proof;certs[report['stored'][root]]=disk
                    answer=(k.check_certificate if mode=='boundary' else s.check_full)(row['source'],disk,cc)
                    assert answer['answer']==result['answer'] and case['route']==mode
                else:assert case['route']=='fresh'
                assert dict(cc)==case['counts'],(mode,key)
            if case['route']=='fresh':fallback_rows.append(row);fallback_results.append(result)
        assert base.encode(json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes())))==base.encode(certs)
        assert report['certificate_bytes']==sum((dest/f).stat().st_size for f in report['stored'].values())
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';db.write_bytes(gzip.decompress(Path(archive['path']).read_bytes()));assert base.sha(db)==archive['database_sha256']
                readers=s.prior.prior.audit(db,fallback_rows,fallback_results);conn=sqlite3.connect(db)
                try:tables=old.tables(conn)
                finally:conn.close()
            assert report['records']==sum(map(len,tables.values()))
            assert report['record_bytes']==sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items())
            assert report['digest']=={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}
            audits[archive['sha256']]=dict(archive=archive,readers=readers)
    for mode,reports in groups.items():
        r=reports[0]
        for q in reports:
            for key in ('results','counts','solver_counts','warm_counts','cold_counts','records','record_bytes','stored','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes','digest'):
                assert q[key]==r[key],(mode,key)
        keys=('complete_seconds','input_seconds','cold_seconds','warm_seconds','persistence_seconds','records','record_bytes','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes')
        totals[mode]={key:statistics.mean(q[key] for q in reports) for key in keys}
        totals[mode]['phases']={key:statistics.mean(q['phases'][key] for q in reports) for key in r['phases']}
        rss[mode]=max(q['peak_rss_bytes'] for q in reports);sizes[mode]=r['archive']['compressed_bytes']+r['certificate_compressed_bytes']
        cov=Counter();per=[]
        for i,(row,case) in enumerate(zip(rows,r['cases'])):
            key=row['id'];cohort='development' if key.startswith('d-') else 'repeats' if 'repeat_of' in desc[key] else 'unique_panel'
            cov[cohort+'_cases']+=1;cov[cohort+'_direct']+=case['route']!='fresh';cov[cohort+'_sat']+=labels[key]['answer']
            per.append(dict(id=key,description=desc[key],diagnostic=case['diagnostic'],answer=labels[key]['answer'],route=case['route'],counts=case['counts'],
                discovery_seconds=statistics.mean(q['cases'][i].get('discovery_seconds',0) for q in reports),solve_check_seconds=statistics.mean(q['cases'][i]['solve_check_seconds'] for q in reports)))
        coverage[mode]=dict(cov);cases[mode]=per
    gains=[r['id'] for r,f,b in zip(rows,cases['full'],cases['boundary']) if f['route']=='fresh' and b['route']=='boundary']
    assert gains==['b06','b12','b07','b22','b06r'];assert coverage['boundary']['unique_panel_direct']==18
    remaining=[dict(**row,description=desc[row['id']],truth=labels[row['id']],reason=case['diagnostic']) for row,case in zip(rows,cases['boundary']) if case['route']=='fresh']
    analysis=dict(panel_size=33,truth=dict(Counter('sat' if labels[r['id']]['answer'] else 'unsat' for r in rows)),coverage=coverage,
        exact_prior_duplicates=overlaps,new_direct_cases=gains,remaining=[r['id'] for r in remaining],totals=totals,peak_rss_bytes=rss,combined_compressed_bytes=sizes,case_stats=cases,
        boundary_vs_percent={m:100*(totals['boundary']['complete_seconds']/totals[m]['complete_seconds']-1) for m in ('fresh','full')},
        paired_vs_fresh_percent=[100*(groups['boundary'][i]['complete_seconds']/groups['fresh'][i]['complete_seconds']-1) for i in range(6)],
        unique_archive_audits=len(audits),selected=min(totals,key=lambda m:totals[m]['complete_seconds']),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);base.write(out/'remaining.json',dict(scope='Boundary acquisition misses; current fallback decides all. Repeats are not separate structural gaps.',cases=remaining))
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['affine_boundary']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining')}
    cp['affine_boundary']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('coverage','boundary_vs_percent','new_direct_cases','remaining','exact_prior_duplicates')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','22cb7992:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';oldproofs=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(oldproofs)==65 and len(proofs)==66 and proofs[:65]==oldproofs
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2234 tests in .*\n\nOK',full) and re.search(r'Ran 37 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['affine_boundary']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2234,focused_tests=37,old_proof_blocks_unchanged=65,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1228,final_sources=1233,prior_manifests=223,prior_artifacts=35068,checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=224,next_artifacts=35068+len(files))))


if __name__=='__main__':
    globals()[sys.argv[1]](Path(sys.argv[2]))
