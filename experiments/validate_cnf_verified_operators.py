#!/usr/bin/env python3
"""Check immutable lineage, certificate equivalence and charged verifier reuse."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,sqlite3,statistics,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_verified_operators as s
base=s.base;old=s.old;k=s.k


def invariant_counts(c):
    return {name:value for name,value in c.items() if not name.startswith('verified_operator_') and name not in ('bucket_verified_rows','bucket_verify_table_probes')}


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(237,73288)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_verified_operators.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1304
    rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);labels=old.bound(p['truth'])
    assert rows==base.load(s.PARENT/'panel.json') and desc==base.load(s.PARENT/'descriptions.json') and labels==base.load(s.PARENT/'truth.json') and len(rows)==182
    previous=base.load(s.PARENT/'two-0/report.json');samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==25
    assert {(q['mode'],q['repeat']) for q in samples}=={(m,i) for m in s.MODES for i in range(5)}
    groups={};audits={};coverage={};totals={};sizes={};rss={};cache={}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];dest=Path(sample['path']).parent;groups.setdefault(mode,[]).append(report)
        assert report['panel']==p['panel'] and len(report['cases'])==len(report['results'])==182
        fallback_rows=[];fallback_results=[];certs={}
        for row,result,case in zip(rows,report['results'],report['cases']):
            assert case['id']==row['id'] and result['answer']==labels[row['id']]['answer']
            if result['answer']:assert k.native.holds(row['source'],{int(v):b for v,b in result['model'].items()})
            root=k.native.token(k.native.normalize(row['source'])[0],Counter());assert result['root']==root
            if mode!='fresh':
                disk=base.load(dest/report['stored'][root]);oldproof=base.load(s.PARENT/'two-0'/previous['stored'][root]);assert disk==oldproof
                assert case['route']==('fresh' if disk['status']=='unresolved' else 'bucket');certs[report['stored'][root]]=disk
                if sample['repeat']==0:
                    got=k.check_certificate(row['source'],disk)
                    if got['answer'] is not None:assert got['answer']==result['answer']
            if case['route']=='fresh':fallback_rows.append(row);fallback_results.append(result)
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==certs
        assert report['certificate_bytes']==sum((dest/f).stat().st_size for f in report['stored'].values())
        for stats in report['cache_sessions']:
            assert stats['max_entries']==4096 and stats['max_bytes']==4194304
            assert stats['entries']<=stats['peak_entries']<=4096 and stats['key_bytes']<=stats['peak_key_bytes']<=4194304
        if mode=='pass':assert [x['phase'] for x in report['cache_sessions']]==['discovery','warm','cold-0','cold-1']
        elif mode=='query':assert len(report['cache_sessions'])==4*182
        else:assert not report['cache_sessions']
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';db.write_bytes(gzip.decompress(Path(archive['path']).read_bytes()));assert base.sha(db)==archive['database_sha256']
                readers=s.FALLBACK.audit(db,fallback_rows,fallback_results);conn=sqlite3.connect(db)
                try:tables=old.tables(conn)
                finally:conn.close()
            assert report['records']==sum(map(len,tables.values())) and report['record_bytes']==sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items())
            assert report['digest']=={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}
            audits[archive['sha256']]=dict(archive=archive,readers=readers)
    # Regenerate complete acquisition and all checking phases once per policy;
    # independent legacy replay above never installs the new checker hook.
    for mode,reports in groups.items():
        r=reports[0]
        for q in reports:
            for key in ('results','counts','solver_counts','warm_counts','cold_counts','records','record_bytes','stored','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes','digest','cache_sessions'):assert q[key]==r[key],(mode,key)
        if mode!='fresh':
            engine=s.Engine(mode,p['cache_limits']);stored={};total=Counter()
            for row,case in zip(rows,r['cases']):
                cc=Counter();engine.query();cnf,_=k.native.normalize(row['source'],cc);root=k.native.token(cnf,cc)
                if root in stored:proof=stored[root];diag=dict(reason='exact-program-reuse');cc['bucket_source_hits']+=1
                else:proof,diag=engine.discover(row['source'],cc,mode='two',**p['limits'])
                assert proof==base.load(out/(mode+'-0')/r['stored'][root])
                assert diag==case['diagnostic'];stored[root]=proof;engine.check_certificate(row['source'],proof,cc);assert dict(cc)==case['counts'];total.update(cc)
            assert dict(total)==r['counts']
            wc=Counter();engine.phase('warm')
            for row in rows:
                engine.query();cnf,_=k.native.normalize(row['source'],wc);root=k.native.token(cnf,wc);engine.check_certificate(row['source'],stored[root],wc)
            assert dict(wc)==r['warm_counts']
            cold=Counter()
            for replay in range(2):
                engine.phase('cold-'+str(replay))
                for row in rows:
                    engine.query();cnf,_=k.native.normalize(row['source'],cold);root=k.native.token(cnf,cold);engine.check_certificate(row['source'],stored[root],cold)
            assert dict(cold)==r['cold_counts'] and engine.finish()==r['cache_sessions']
        keys=('complete_seconds','input_seconds','cold_seconds','warm_seconds','persistence_seconds','records','record_bytes','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes')
        totals[mode]={key:statistics.mean(q[key] for q in reports) for key in keys};totals[mode]['phases']={key:statistics.mean(q['phases'][key] for q in reports) for key in r['phases']}
        sizes[mode]=r['archive']['compressed_bytes']+r['certificate_compressed_bytes'];rss[mode]=max(q['peak_rss_bytes'] for q in reports)
        coverage[mode]=sum(c['route']=='bucket' for c in r['cases'])
        cache[mode]=dict(max_entries=max((x['peak_entries'] for x in r['cache_sessions']),default=0),max_key_bytes=max((x['peak_key_bytes'] for x in r['cache_sessions']),default=0),sessions=len(r['cache_sessions']))
    legacy=groups['legacy'][0]
    for mode in ('off','query','pass'):
        r=groups[mode][0];assert r['results']==legacy['results']
        for key in ('counts','warm_counts','cold_counts'):
            assert invariant_counts(r[key])==invariant_counts(legacy[key]),(mode,key)
            assert r[key].get('bucket_verified_rows',0)+r[key].get('verified_operator_saved_rows',0)==legacy[key].get('bucket_verified_rows',0)
            assert r[key].get('bucket_verify_table_probes',0)+r[key].get('verified_operator_saved_probes',0)==legacy[key].get('bucket_verify_table_probes',0)
            if mode=='off':assert r[key]==legacy[key]
        assert r['digest']==legacy['digest'] and r['certificate_bytes']==legacy['certificate_bytes'] and r['certificate_compressed_bytes']==legacy['certificate_compressed_bytes']
    comparisons=[(a+'_vs_'+b,a,b) for a,b in [('off','legacy'),('query','legacy'),('pass','legacy'),('pass','query'),('pass','off'),('pass','fresh')]]
    analysis=dict(panel_size=182,coverage=coverage,remaining=[r['id'] for r,c in zip(rows,legacy['cases']) if c['route']=='fresh'],totals=totals,peak_rss_bytes=rss,combined_compressed_bytes=sizes,cache=cache,
        comparisons_percent={name:100*(totals[a]['complete_seconds']/totals[b]['complete_seconds']-1) for name,a,b in comparisons},paired_percent={name:[100*(groups[a][i]['complete_seconds']/groups[b][i]['complete_seconds']-1) for i in range(5)] for name,a,b in comparisons},counts={m:{key:qs[0][key] for key in ('counts','warm_counts','cold_counts')} for m,qs in groups.items()},unique_archive_audits=len(audits),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['verified_operators']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis')};cp['verified_operators']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('coverage','comparisons_percent','paired_percent','remaining','cache')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','328e1615:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';oldproofs=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(oldproofs)==79 and len(proofs)==80 and proofs[:79]==oldproofs
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2401 tests in .*\n\nOK',full) and re.search(r'Ran 33 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['verified_operators']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2401,focused_tests=33,old_proof_blocks_unchanged=79,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+)pages,',re.sub(r'\s+','',latex))[1]),prior_sources=1300,final_sources=1304,prior_manifests=237,prior_artifacts=73288,checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();original=Path(str(f)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts);base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=238,next_artifacts=73288+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
