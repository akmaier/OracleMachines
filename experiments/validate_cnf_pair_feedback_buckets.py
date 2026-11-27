#!/usr/bin/env python3
"""Replay bounded feedback evidence, compare controls and preserve prior lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,sqlite3,statistics,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_pair_feedback_buckets as s
base=s.base;old=s.old;k=s.k


def refinement_rounds(node,mode):
    ref=node['refinement']
    return [] if ref is None else ref['rounds'] if mode=='feedback' else [ref]


def last_node(node,mode):
    rounds=refinement_rounds(node,mode)
    return rounds[-1]['terminal']['nodes'][-1] if rounds else node


def shape_counts(proof,mode):
    c=Counter(nodes=len(proof['nodes']),edges=len(proof['edges']));incoming={}
    for edge in proof['edges']:incoming.setdefault(edge['target'],[]).append(edge)
    for target,edges in incoming.items():
        if len(edges)>1:
            c['shared_targets']+=1
            if len({base.encode(e['cnf']) for e in edges})>1:c['constant_raw_merges' if proof['nodes'][target]['cnf'] in ([],[[]]) else 'nonconstant_raw_merges']+=1
    for node in proof['nodes']:
        c[node['kind']+'_nodes']+=1;c['outer_bucket_steps']+=len(node['bucket']['steps'])
        rounds=refinement_rounds(node,mode)
        if rounds:
            c['refinements']+=1;c['rounds_'+str(len(rounds))]+=1;c['refined_'+node['status']]+=1
        for i,rnd in enumerate(rounds):
            ev=rnd['evidence'];term=rnd['terminal'];c['pair_clauses']+=len(ev['clauses']);c['pair_prefixes']+=len(ev['prefixes']);c['pair_evidence_bytes']+=len(base.encode(ev).encode())
            c['terminal_nodes']+=len(term['nodes']);c['terminal_bucket_steps']+=sum(len(n['bucket']['steps']) for n in term['nodes'])
            c['round_'+str(i+1)+'_clauses']+=len(ev['clauses']);c['round_'+str(i+1)+'_'+term['status']]+=1
    return c


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(235,57145)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_pair_feedback_buckets.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1294
    rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);labels=old.bound(p['truth']);freeze=old.bound(p['freeze'])
    held,hd=s.panel();prev=base.load(s.PARENT/'panel.json')
    assert len(prev)==138 and rows[:138]==[dict(id='d-'+r['id'],source=r['source']) for r in prev]
    assert held==rows[138:] and hd=={key:desc[key] for key in hd};assert base.sha(out/'heldout.json')==freeze['sha256']
    for r in rows:assert labels[r['id']]==json.loads(base.encode(s.oracle(r['source'])))
    prior_keys={k.native.normalize(r['source'])[0] for r in prev};overlaps=[r['id'] for r in held if k.native.normalize(r['source'])[0] in prior_keys]
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==16
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(4)}
    groups={};audits={};coverage={};totals={};cases={};rss={};sizes={};structural={}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];dest=Path(sample['path']).parent;groups.setdefault(mode,[]).append(report)
        engine,options=s.engine_options(mode,p['limits'])
        assert report['panel']==p['panel'] and len(report['cases'])==len(report['results'])==160
        stored={};fallback_rows=[];fallback_results=[];certs={};shape=Counter()
        for row,result,case in zip(rows,report['results'],report['cases']):
            key=row['id'];assert case['id']==key and result['answer']==labels[key]['answer']
            if result['answer']:assert k.native.holds(row['source'],{int(v):b for v,b in result['model'].items()})
            assert result['root']==k.native.token(k.native.normalize(row['source'])[0],Counter())
            if mode!='fresh':
                cc=Counter();cnf,_=k.native.normalize(row['source'],cc);root=k.native.token(cnf,cc)
                if root in stored:proof=stored[root];diag=dict(reason='exact-program-reuse');cc['bucket_source_hits']+=1
                else:
                    proof,diag=engine.discover(row['source'],cc,**options);shape.update(shape_counts(proof,mode))
                assert diag==case['diagnostic']==base.load(dest/(key+'-diagnostic.json'))
                disk=base.load(dest/report['stored'][root]);assert proof==disk
                if mode=='base' and sample['repeat']==0 and key.startswith('d-'):
                    oldreport=base.load(s.PARENT/'shared-0/report.json');oldproof=base.load(s.PARENT/'shared-0'/oldreport['stored'][root]);assert disk==oldproof
                assert cc['pair_attempts']<=(1<<p['limits']['depth_limit'])*p['limits']['pair_limit']*(1 if mode=='base' else 2)
                assert cc['pair_learned_clauses']<=(1<<p['limits']['depth_limit'])*p['limits']['learn_limit']*(1 if mode=='base' else 2)
                stored[root]=proof;certs[report['stored'][root]]=disk;got=engine.check_certificate(row['source'],disk,cc)
                assert case['route']==('bucket' if got['answer'] is not None else 'fresh')
                if got['answer'] is not None:assert got['answer']==result['answer']
                assert dict(cc)==case['counts'],(mode,key)
            if case['route']=='fresh':fallback_rows.append(row);fallback_results.append(result)
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==certs
        assert report['certificate_bytes']==sum((dest/f).stat().st_size for f in report['stored'].values())
        if mode not in structural:structural[mode]=dict(shape)
        else:assert structural[mode]==dict(shape)
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';db.write_bytes(gzip.decompress(Path(archive['path']).read_bytes()));assert base.sha(db)==archive['database_sha256']
                readers=s.FALLBACK.audit(db,fallback_rows,fallback_results);conn=sqlite3.connect(db)
                try:tables=old.tables(conn)
                finally:conn.close()
            assert report['records']==sum(map(len,tables.values()))
            assert report['record_bytes']==sum(len(a.encode())+len(b.encode()) for t in tables.values() for a,b in t.items())
            assert report['digest']=={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}
            audits[archive['sha256']]=dict(archive=archive,readers=readers)
    for mode,reports in groups.items():
        r=reports[0]
        for q in reports:
            for key in ('results','counts','solver_counts','warm_counts','cold_counts','records','record_bytes','stored','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes','digest'):assert q[key]==r[key],(mode,key)
        keys=('complete_seconds','input_seconds','cold_seconds','warm_seconds','persistence_seconds','records','record_bytes','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes')
        totals[mode]={key:statistics.mean(q[key] for q in reports) for key in keys};totals[mode]['phases']={key:statistics.mean(q['phases'][key] for q in reports) for key in r['phases']}
        rss[mode]=max(q['peak_rss_bytes'] for q in reports);sizes[mode]=r['archive']['compressed_bytes']+r['certificate_compressed_bytes']
        cov=Counter();per=[]
        for i,(row,case) in enumerate(zip(rows,r['cases'])):
            key=row['id'];cohort='previous_panel' if key.startswith('d-') else 'repeats' if 'repeat_of' in desc[key] else 'unique_panel'
            cov[cohort+'_cases']+=1;cov[cohort+'_direct']+=case['route']=='bucket';cov[cohort+'_sat']+=labels[key]['answer']
            per.append(dict(id=key,answer=labels[key]['answer'],route=case['route'],counts=case['counts'],discovery_seconds=statistics.mean(q['cases'][i].get('discovery_seconds',0) for q in reports),solve_check_seconds=statistics.mean(q['cases'][i]['solve_check_seconds'] for q in reports)))
        coverage[mode]=dict(cov);cases[mode]=per
    comparisons=(('feedback_vs_base','feedback','base'),('feedback_vs_larger','feedback','larger'),('feedback_vs_fresh','feedback','fresh'))
    gains={mode:[row['id'] for row,a,b in zip(rows,cases['base'],cases[mode]) if a['route']=='fresh' and b['route']=='bucket'] for mode in ('larger','feedback')}
    losses={mode:[row['id'] for row,a,b in zip(rows,cases['base'],cases[mode]) if a['route']=='bucket' and b['route']=='fresh'] for mode in ('larger','feedback')}
    remaining=[];diagnostics=[];pc=Counter();summary=Counter();profile_start=time.perf_counter()
    for row,case in zip(rows,groups['feedback'][0]['cases']):
        if case['route']!='fresh':continue
        root=k.native.token(k.native.normalize(row['source'])[0],Counter());file=out/'feedback-0'/groups['feedback'][0]['stored'][root];proof=base.load(file)
        leaves=[]
        for i,node in enumerate(proof['nodes']):
            if node['kind']!='leaf' or node['status']!='unresolved':continue
            final=last_node(node,'feedback');cnf=tuple(map(tuple,final['cnf']));counts=Counter()
            _,bd=k.bucket.discover(cnf,counts,**{key:p['limits'][key] for key in k.bucket.DEFAULTS})
            record=dict(node=i,rounds=len(refinement_rounds(node,'feedback')),source=list(map(list,cnf)),width=bd.get('width'),reason=bd['reason'],spent=bd['spent'])
            leaves.append(record)
            if 'repeat_of' in desc[row['id']]:continue
            starts=[l for v in sorted({abs(l) for c in cnf for l in c}) for l in (v,-v)];idx=k.probes.prepare_index(cnf,pc);failed=[]
            for l in starts:
                ev=k.probes.indexed_probe(cnf,l,idx,pc)
                if ev is not None:k.probes.check_probe(cnf,ev,pc);failed.append(ev)
            ev,diag=k.joint.discover(cnf,pc,mode='shared',pair_limit=256,learn_limit=32);learned=k.joint.check(cnf,ev,pc,pair_limit=256,learn_limit=32)
            terminal=None;status='unresolved'
            if learned:
                augmented=k.relations.clean_quotient(cnf+learned,pc);terminal,_=k.prior.discover(augmented,pc,mode='restart',**{**k.base_options(p['limits']),'depth_limit':0})
                got=k.prior.check_certificate(augmented,terminal,pc);status=terminal['status']
                if got['answer']:assert k.native.holds(cnf,got['model'])
            summary.update(dict(leaves=1,single_probes=len(starts),single_failures=len(failed),new_clauses=len(learned),next_pair_certified=status!='unresolved'));summary['stop_'+diag['reason']]+=1
            diagnostics.append(dict(id=row['id'],proof=old.binding(file),**record,single_failures=failed,pair_evidence=ev,pair_diagnostic=diag,terminal=terminal,status=status))
        assert leaves
        remaining.append(dict(**row,description=desc[row['id']],truth=labels[row['id']],proof=old.binding(file),unresolved_leaves=leaves))
    unique=[r for r in remaining if 'repeat_of' not in r['description']];leaves=[x for r in unique for x in r['unresolved_leaves']]
    analysis=dict(panel_size=len(rows),truth=dict(Counter('sat' if labels[r['id']]['answer'] else 'unsat' for r in rows)),coverage=coverage,exact_prior_duplicates=overlaps,new_direct_cases=gains,coverage_losses=losses,remaining=[r['id'] for r in remaining],totals=totals,peak_rss_bytes=rss,combined_compressed_bytes=sizes,case_stats=cases,structural=structural,counts={m:rs[0]['counts'] for m,rs in groups.items()},
        comparisons_percent={name:100*(totals[a]['complete_seconds']/totals[b]['complete_seconds']-1) for name,a,b in comparisons},paired_percent={name:[100*(groups[a][i]['complete_seconds']/groups[b][i]['complete_seconds']-1) for i in range(4)] for name,a,b in comparisons},unique_archive_audits=len(audits),selected=min(totals,key=lambda m:totals[m]['complete_seconds']),limitations=p['limitations'],
        remaining_shape=dict(unique_sources=len(unique),repeated_queries=len(remaining)-len(unique),unknown_leaves=len(leaves),width_counts=dict(Counter(str(x['width']) for x in leaves)),zero_work_leaves=sum(x['spent']==0 for x in leaves)),remaining_profile=dict(summary))
    base.write(out/'remaining-profile.json',dict(summary=dict(summary),records=diagnostics,counts=dict(pc),seconds=time.perf_counter()-profile_start,scope='Post-hoc diagnostics only, on exact final residuals. All single starts enumerated; returned failures checked. One further bounded pair batch and terminal checked. No additional root coverage claim.'))
    base.write(out/'analysis.json',analysis);base.write(out/'remaining.json',dict(scope='Unresolved bounded certificates; common fallback decides all sources.',cases=remaining))
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['pair_feedback_buckets']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining','remaining-profile')};cp['pair_feedback_buckets']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('coverage','comparisons_percent','paired_percent','remaining','structural','new_direct_cases','exact_prior_duplicates','remaining_profile')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','aac7c370:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';oldproofs=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(oldproofs)==77 and len(proofs)==78 and proofs[:77]==oldproofs
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2368 tests in .*\n\nOK',full) and re.search(r'Ran 30 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['pair_feedback_buckets']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2368,focused_tests=30,old_proof_blocks_unchanged=77,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+)pages,',re.sub(r'\s+','',latex))[1]),prior_sources=1289,final_sources=1294,prior_manifests=235,prior_artifacts=57145,checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=236,next_artifacts=57145+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
