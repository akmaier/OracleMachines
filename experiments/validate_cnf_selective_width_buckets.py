#!/usr/bin/env python3
"""Audit selective width expansion and resumed projection prefixes."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,sqlite3,statistics,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_selective_width_buckets as s
base=s.base;old=s.old;k=s.k


def refinement_rounds(node,mode):
    ref=node['refinement']
    return [] if ref is None else ref['rounds'] if mode!='single' else [ref]


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
        if mode in ('one','two','restart') and node['refinement'] is not None and node['refinement']['widen'] is not None:
            wide=node['refinement']['widen'];prefix=last_node(node,mode)['bucket']
            c['widenings']+=1;c['widen_'+wide['status']]+=1;c['widen_prefix_steps']+=len(prefix['steps']);c['widen_suffix_steps']+=len(wide['steps'])
            c['widen_suffix_step_bytes']+=len(base.encode(wide['steps']).encode());c['duplicated_full_step_bytes']+=len(base.encode(prefix['steps']+wide['steps']).encode())
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
    assert (len(manifests),artifacts)==(236,60847)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_selective_width_buckets.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1300
    rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);labels=old.bound(p['truth']);freeze=old.bound(p['freeze'])
    held,hd=s.panel();prev=base.load(s.PARENT/'panel.json')
    assert len(prev)==160 and rows[:160]==[dict(id='d-'+r['id'],source=r['source']) for r in prev]
    assert held==rows[160:] and hd=={key:desc[key] for key in hd};assert base.sha(out/'heldout.json')==freeze['sha256']
    for r in rows:assert labels[r['id']]==json.loads(base.encode(s.oracle(r['source'])))
    prior_keys={k.native.normalize(r['source'])[0] for r in prev};overlaps=[r['id'] for r in held if k.native.normalize(r['source'])[0] in prior_keys]
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==36
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(6)}
    groups={};audits={};coverage={};totals={};cases={};rss={};sizes={};structural={}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];dest=Path(sample['path']).parent;groups.setdefault(mode,[]).append(report)
        engine,options=s.engine_options(mode,p['limits'])
        assert report['panel']==p['panel'] and len(report['cases'])==len(report['results'])==182
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
                if mode in ('single','feedback') and sample['repeat']==0 and key.startswith('d-'):
                    folder='base-0' if mode=='single' else 'feedback-0';oldreport=base.load(s.PARENT/folder/'report.json');oldproof=base.load(s.PARENT/folder/oldreport['stored'][root]);assert disk==oldproof
                assert cc['pair_attempts']<=(1<<p['limits']['depth_limit'])*p['limits']['pair_limit']*(2 if mode in ('feedback','two') else 1)
                assert cc['pair_learned_clauses']<=(1<<p['limits']['depth_limit'])*p['limits']['learn_limit']*(2 if mode in ('feedback','two') else 1)
                if mode=='one' and sample['repeat']==0:
                    other=base.load(out/'restart-0'/report['stored'][root]);other['mode']='one';assert disk==other
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
    comparisons=(('one_vs_single','one','single'),('one_vs_feedback','one','feedback'),('one_vs_restart','one','restart'),('one_vs_fresh','one','fresh'),('two_vs_feedback','two','feedback'),('two_vs_one','two','one'),('two_vs_fresh','two','fresh'))
    gains={};losses={}
    for mode in ('one','two'):
        for control in ('single','feedback'):
            name=mode+'_vs_'+control
            gains[name]=[row['id'] for row,a,b in zip(rows,cases[control],cases[mode]) if a['route']=='fresh' and b['route']=='bucket']
            losses[name]=[row['id'] for row,a,b in zip(rows,cases[control],cases[mode]) if a['route']=='bucket' and b['route']=='fresh']
    remaining=[];diagnostics=[];pc=Counter();summary=Counter();profile_start=time.perf_counter()
    for row,case in zip(rows,groups['two'][0]['cases']):
        if case['route']!='fresh':continue
        root=k.native.token(k.native.normalize(row['source'])[0],Counter());file=out/'two-0'/groups['two'][0]['stored'][root];proof=base.load(file)
        leaves=[]
        for i,node in enumerate(proof['nodes']):
            if node['kind']!='leaf' or node['status']!='unresolved':continue
            ref=node['refinement'];final=last_node(node,'two');cnf=tuple(map(tuple,final['cnf']));prefix=final['bucket'];wide=ref['widen']
            combined={**prefix,'limits':{**prefix['limits'],'bag_limit':prefix['limits']['bag_limit']+1},'steps':prefix['steps']+wide['steps'],'status':wide['status'],'model':wide['model']}
            assert all(len(c)<=combined['limits']['bag_limit'] for c in cnf)
            k.bucket.check_certificate(cnf,combined,pc);factors,active,spent=k.continuation.materialize(cnf,combined['steps'],pc)
            candidates=[]
            for v in sorted({v for j in active for v in factors[j]['scope']}):
                ids=sorted(j for j in active if v in factors[j]['scope']);bag=sorted({w for j in ids for w in factors[j]['scope']});candidates.append((len(bag),len(ids),v,ids,bag))
            width,_,variable,ids,bag=min(candidates)
            next_cost=(1<<width)*len(ids);reason='bag-width' if width>combined['limits']['bag_limit'] else 'row-work' if spent+next_cost>combined['limits']['work_limit'] else 'unexpected'
            assert reason!='unexpected'
            record=dict(reason=reason,next_cost=next_cost,node=i,rounds=len(refinement_rounds(node,'two')),source=list(map(list,cnf)),width=width,spent=spent,active_factors=[dict(index=j,**factors[j]) for j in sorted(active)],next_variable=variable,next_inputs=ids,next_bag=bag)
            leaves.append(record)
            if 'repeat_of' in desc[row['id']]:continue
            start=time.perf_counter();next_extension,nd,got=k.continuation.discover(cnf,combined,pc);k.continuation.check(cnf,combined,next_extension,pc)
            if got['answer']:assert k.native.holds(cnf,got['model'])
            summary.update(dict(leaves=1,active_factors=len(active),active_variables=len({v for j in active for v in factors[j]['scope']}),next_width_certified=got['answer'] is not None));summary['next_'+next_extension['status']]+=1
            diagnostics.append(dict(id=row['id'],proof=old.binding(file),**record,prefix=combined,next_extension=next_extension,next_diagnostic=nd,next_seconds=time.perf_counter()-start))
        assert leaves
        remaining.append(dict(**row,description=desc[row['id']],truth=labels[row['id']],proof=old.binding(file),unresolved_leaves=leaves))
    unique=[r for r in remaining if 'repeat_of' not in r['description']];leaves=[x for r in unique for x in r['unresolved_leaves']]
    analysis=dict(panel_size=len(rows),truth=dict(Counter('sat' if labels[r['id']]['answer'] else 'unsat' for r in rows)),coverage=coverage,exact_prior_duplicates=overlaps,new_direct_cases=gains,coverage_losses=losses,remaining=[r['id'] for r in remaining],totals=totals,peak_rss_bytes=rss,combined_compressed_bytes=sizes,case_stats=cases,structural=structural,counts={m:rs[0]['counts'] for m,rs in groups.items()},
        comparisons_percent={name:100*(totals[a]['complete_seconds']/totals[b]['complete_seconds']-1) for name,a,b in comparisons},paired_percent={name:[100*(groups[a][i]['complete_seconds']/groups[b][i]['complete_seconds']-1) for i in range(6)] for name,a,b in comparisons},unique_archive_audits=len(audits),selected=min(totals,key=lambda m:totals[m]['complete_seconds']),limitations=p['limitations'],
        remaining_shape=dict(unique_sources=len(unique),repeated_queries=len(remaining)-len(unique),unknown_leaves=len(leaves),width_counts=dict(Counter(str(x['width']) for x in leaves)),zero_work_leaves=sum(x['spent']==0 for x in leaves)),remaining_profile=dict(summary))
    base.write(out/'remaining-profile.json',dict(summary=dict(summary),records=diagnostics,counts=dict(pc),seconds=time.perf_counter()-profile_start,scope='Post-hoc exact active-factor frontier after all retained width-nine projections. One additional width with total prefix work charged; checked leaf verdicts only, not new root coverage or measured costs. These active factors are not CNF residual clauses.'))
    base.write(out/'analysis.json',analysis);base.write(out/'remaining.json',dict(scope='Unresolved bounded certificates; common fallback decides all sources.',cases=remaining))
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['selective_width_buckets']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining','remaining-profile')};cp['selective_width_buckets']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('coverage','comparisons_percent','paired_percent','remaining','structural','new_direct_cases','exact_prior_duplicates','remaining_profile')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','7f9a5cdb:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';oldproofs=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(oldproofs)==78 and len(proofs)==79 and proofs[:78]==oldproofs
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2385 tests in .*\n\nOK',full) and re.search(r'Ran 30 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['selective_width_buckets']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2385,focused_tests=30,old_proof_blocks_unchanged=78,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+)pages,',re.sub(r'\s+','',latex))[1]),prior_sources=1294,final_sources=1300,prior_manifests=236,prior_artifacts=60847,checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=237,next_artifacts=60847+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
