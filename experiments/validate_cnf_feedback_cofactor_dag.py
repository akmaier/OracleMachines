#!/usr/bin/env python3
"""Audit exact cofactor sharing, frozen transfer controls and source archives."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,statistics,subprocess,sys,tempfile,time,sqlite3
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_feedback_cofactor_dag as s
base=s.base;old=s.old;k=s.kernel


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(222,34259)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_feedback_cofactor_dag.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1228
    rows=old.bound(p['panel']);labels=old.bound(p['truth']);desc=old.bound(p['descriptions']);freeze=old.bound(p['freeze'])
    held,held_desc=s.panel();assert held==rows[6:] and held_desc=={key:desc[key] for key in held_desc}
    assert base.sha(out/'heldout.json')==freeze['heldout_sha256']
    previous=base.load(s.PARENT/'remaining.json')['cases'];assert rows[:6]==[dict(id='d-'+r['id'],source=r['source']) for r in previous]
    old_keys={k.native.normalize(r['source'])[0] for r in base.load(s.PARENT/'panel.json')}
    overlaps=[r['id'] for r in held if k.native.normalize(r['source'])[0] in old_keys]
    controls=[r['id'] for r in held if desc[r['id']]['family']=='clause_cube' and desc[r['id']]['variant']=='full']
    assert set(controls)=={'h00','h02','h04'}
    truth_counts=Counter()
    for r in rows:
        assert labels[r['id']]==s.truth(r['source']);truth_counts['sat' if labels[r['id']]['answer'] else 'unsat']+=1
    assert dict(truth_counts)==dict(sat=14,unsat=16)
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==16
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(4)}
    groups={};audits={};discovery={};discovery_counts={};coverage={}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];assert r['mode']==mode and r['panel']==p['panel'];groups.setdefault(mode,[]).append(r)
        assert len(r['results'])==len(rows)==len(r['cases'])
        for row,result,case in zip(rows,r['results'],r['cases']):
            key=row['id'];assert case['id']==key and result['answer']==labels[key]['answer']
            assert result['root']==k.native.token(k.native.normalize(row['source'])[0],Counter())
            if result['answer']:assert k.native.holds(row['source'],{int(a):b for a,b in result['model'].items()})
            if mode=='fresh':assert case['route']=='fresh';continue
            dest=Path(sample['path']).parent;record=base.load(dest/(key+'-certificate.json'));search=base.load(dest/(key+'-searches.json'))
            k.validate(row['source'],record,Counter());identity=mode,key
            if identity not in discovery:
                cc=Counter();limits={**p['limits'],'depth_limit':0 if mode=='flat' else 2}
                actual,history=k.discover(row['source'],cc,reuse=mode=='memo',**limits);assert (record,search)==(actual,history)
                discovery[identity]=(record,search)
                discovery_counts[identity]=cc
            else:assert (record,search)==discovery[identity]
            for name in ('cofactor_feedback_calls','cofactor_memo_hits','cofactor_retained_nodes','cofactor_lookup_calls','cofactor_lookup_literals'):
                assert case['counts'].get(name,0)==discovery_counts[identity][name]
            assert case['route']==('feedback' if record['status']=='refuted' else 'fresh')
            if case['route']=='feedback':
                assert result['authority']=='native' and not labels[key]['answer']
                assert sum(case['counts'].get(x,0) for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=p['unit_work_limit']
        archive=r['archive'];assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';s.prior.prior.previous.restore_archive(archive,db);readers=s.prior.audit(db,rows,r['results'])
                conn=sqlite3.connect(db)
                try:tables=old.tables(conn)
                finally:conn.close()
            assert r['records']==sum(map(len,tables.values()))
            assert r['record_bytes']==sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items())
            assert r['digest']=={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}
            audits[archive['sha256']]=dict(archive=archive,readers=readers)
    totals={};rss={};sizes={};counts={};case_stats={}
    for mode,rs in groups.items():
        for r in rs:
            for key in ('counts','native_counts','warm_counts','warm_native_counts','results','digest','records','record_bytes','certificate_bytes','search_bytes'):
                assert r[key]==rs[0][key],(mode,key)
        keys=('input_seconds','complete_seconds','warm_seconds','cold_seconds','persistence_seconds','records','record_bytes','certificate_bytes','search_bytes')
        totals[mode]={key:statistics.mean(r[key] for r in rs) for key in keys}
        totals[mode]['phases']={key:statistics.mean(r['phases'][key] for r in rs) for key in rs[0]['phases']}
        rss[mode]=max(r['peak_rss_bytes'] for r in rs);sizes[mode]=Path(rs[0]['archive']['path']).stat().st_size;counts[mode]=rs[0]['counts']
        cov=Counter();per=[]
        for i,row in enumerate(rows):
            key=row['id'];closed=rs[0]['cases'][i]['route']=='feedback';group='development' if key.startswith('d-') else 'second_panel'
            cov[group+'_refuted']+=closed;cov[group+'_unsat']+=not labels[key]['answer']
            if key.startswith('h') and key not in controls:
                cov['second_excluding_cube_controls_refuted']+=closed;cov['second_excluding_cube_controls_unsat']+=not labels[key]['answer']
            c=rs[0]['cases'][i]['counts'];per.append(dict(id=key,feedback=closed,truth=labels[key]['answer'],description=desc[key],
                calls=c.get('cofactor_feedback_calls',0),memo_hits=c.get('cofactor_memo_hits',0),nodes=c.get('cofactor_retained_nodes',0),
                discovery_seconds=statistics.mean(q['cases'][i].get('discovery_seconds',0) for q in rs),solve_check_seconds=statistics.mean(q['cases'][i]['solve_check_seconds'] for q in rs)))
        coverage[mode]=dict(cov);case_stats[mode]=per
    assert groups['tree'][0]['digest']==groups['memo'][0]['digest']
    assert [c['feedback'] for c in case_stats['tree']]==[c['feedback'] for c in case_stats['memo']]
    assert (coverage['memo']['development_refuted'],coverage['memo']['second_panel_refuted'])==(5,6)
    remaining=[dict(**r,description=desc[r['id']],certificate=old.binding(out/'memo-0'/(r['id']+'-certificate.json'))) for r,c in zip(rows,case_stats['memo']) if not c['truth'] and not c['feedback']]
    assert len(remaining)==5
    # Executable recurrence controls; no timing or class labels guide discovery.
    from experiments.cnf_fresh_seed_panel import cube
    recurrence=[]
    for n in range(3,7):
        for reuse in (False,True):
            cc=Counter();record,_=k.discover(cube(n),cc,reuse=reuse);d=min(2,n-3)
            assert cc['cofactor_feedback_calls']==(d+1 if reuse else 2**(d+1)-1)
            recurrence.append(dict(variables=n,reuse=reuse,calls=cc['cofactor_feedback_calls'],status=record['status']))
    strata={}
    for hits in (True,False):
        indices=[i for i,c in enumerate(case_stats['memo']) if (c['memo_hits']>0)==hits]
        seconds={m:sum(case_stats[m][i]['discovery_seconds'] for i in indices) for m in ('tree','memo')}
        strata['observed_reuse' if hits else 'no_observed_reuse']=dict(cases=len(indices),discovery_seconds=seconds,percent=100*(seconds['memo']/seconds['tree']-1))
    paired=[100*(groups['memo'][i]['complete_seconds']/groups['tree'][i]['complete_seconds']-1) for i in range(4)]
    analysis=dict(panel_size=30,truth=dict(truth_counts),coverage=coverage,second_panel_exact_prior_duplicates=overlaps,
        second_panel_analytic_cube_controls=controls,recurrence=recurrence,totals=totals,peak_rss_bytes=rss,archive_bytes=sizes,counts=counts,case_stats=case_stats,
        reuse_strata=strata,paired_complete_percent=paired,
        memo_vs_tree_percent={key:100*(totals['memo'][key]/totals['tree'][key]-1) for key in ('complete_seconds','warm_seconds','certificate_bytes','search_bytes')},
        memo_vs_fresh_factor=totals['memo']['complete_seconds']/totals['fresh']['complete_seconds'],remaining=[r['id'] for r in remaining],
        unique_archive_audits=len(audits),selected='fresh',limitations=p['limitations'])
    assert min(totals,key=lambda m:totals[m]['complete_seconds'])=='fresh'
    base.write(out/'remaining.json',dict(scope='Feedback unresolved UNSAT after bounded depth-two conditioning; fresh fallback solves all cases.',cases=remaining))
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['feedback_cofactor_dag']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining')}
    cp['feedback_cofactor_dag']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('coverage','totals','memo_vs_tree_percent','remaining','second_panel_exact_prior_duplicates')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','ea7f5b48:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';old_proofs=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old_proofs)==64 and len(proofs)==65 and proofs[:64]==old_proofs
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2226 tests in .*\n\nOK',full) and re.search(r'Ran 26 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['feedback_cofactor_dag']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2226,focused_tests=26,old_proof_blocks_unchanged=64,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1223,final_sources=len(cp['source_fingerprints']),prior_manifests=222,prior_artifacts=34259,new_native_archives=len(v['supplemental_archive_audits']),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=223,next_artifacts=34259+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
