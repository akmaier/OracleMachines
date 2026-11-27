#!/usr/bin/env python3
"""Replay per-cofactor unit closure, transport edges and preserved lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,sqlite3,statistics,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_closed_buckets as s
base=s.base;old=s.old;k=s.k


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(227,38630)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_closed_buckets.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1253
    rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);labels=old.bound(p['truth']);freeze=old.bound(p['freeze'])
    held,hd=s.panel();assert held==rows[20:] and hd=={key:desc[key] for key in hd};assert base.sha(out/'heldout.json')==freeze['sha256']
    prev=base.load(s.PARENT/'remaining.json')['cases'];assert rows[:20]==[dict(id='d-'+r['id'],source=r['source']) for r in prev if 'repeat_of' not in r['description']]
    for r in rows:assert labels[r['id']]==json.loads(base.encode(s.oracle(r['source'])))
    prior_keys={k.native.normalize(r['source'])[0] for r in base.load(s.PARENT/'panel.json')}
    overlaps=[r['id'] for r in held if k.native.normalize(r['source'])[0] in prior_keys]
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==16
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(4)}
    groups={};audits={};coverage={};totals={};cases={};rss={};sizes={};structural={}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];dest=Path(sample['path']).parent;groups.setdefault(mode,[]).append(report)
        assert report['panel']==p['panel'] and len(report['cases'])==len(report['results'])==48
        stored={};fallback_rows=[];fallback_results=[];certs={};shape=Counter()
        for row,result,case in zip(rows,report['results'],report['cases']):
            key=row['id'];assert case['id']==key and result['answer']==labels[key]['answer']
            if result['answer']:assert k.native.holds(row['source'],{int(v):b for v,b in result['model'].items()})
            assert result['root']==k.native.token(k.native.normalize(row['source'])[0],Counter())
            if mode!='fresh':
                cc=Counter();cnf,_=k.native.normalize(row['source'],cc);root=k.native.token(cnf,cc)
                if root in stored:
                    proof=stored[root];diag=dict(reason='exact-program-reuse');cc['bucket_source_hits']+=1
                else:
                    proof,diag=k.discover(row['source'],cc,mode=mode,**p['limits'])
                    shape['nodes']+=len(proof['nodes']);shape['edges']+=len(proof['edges'])
                    for step in proof['prefix']:shape['prefix_'+step['kind']+'_steps']+=1
                    incoming={}
                    for edge in proof['edges']:
                        shape['edge_unit_steps']+=len(edge['units']);incoming.setdefault(edge['target'],[]).append(edge)
                    for target,es in incoming.items():
                        if len(es)>1:
                            shape['shared_targets']+=1
                            if len({base.encode(e['cnf']) for e in es})>1:
                                shape['distinct_raw_merges']+=1
                                shape['constant_raw_merges' if proof['nodes'][target]['cnf'] in ([],[[]]) else 'nonconstant_raw_merges']+=1
                    for node in proof['nodes']:
                        shape[node['kind']+'_nodes']+=1;shape['bucket_steps']+=len(node['bucket']['steps'])
                        if node['kind']=='leaf':shape['leaf_'+node['status']]+=1
                assert diag==case['diagnostic']==base.load(dest/(key+'-diagnostic.json'))
                disk=base.load(dest/report['stored'][root]);assert proof==disk
                stored[root]=proof;certs[report['stored'][root]]=disk
                got=k.check_certificate(row['source'],disk,cc)
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
            for key in ('results','counts','solver_counts','warm_counts','cold_counts','records','record_bytes','stored','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes','digest'):
                assert q[key]==r[key],(mode,key)
        keys=('complete_seconds','input_seconds','cold_seconds','warm_seconds','persistence_seconds','records','record_bytes','certificate_bytes','certificate_compressed_bytes','diagnostic_bytes')
        totals[mode]={key:statistics.mean(q[key] for q in reports) for key in keys}
        totals[mode]['phases']={key:statistics.mean(q['phases'][key] for q in reports) for key in r['phases']}
        rss[mode]=max(q['peak_rss_bytes'] for q in reports);sizes[mode]=r['archive']['compressed_bytes']+r['certificate_compressed_bytes']
        cov=Counter();per=[]
        for i,(row,case) in enumerate(zip(rows,r['cases'])):
            key=row['id'];cohort='development' if key.startswith('d-') else 'repeats' if 'repeat_of' in desc[key] else 'unique_panel'
            cov[cohort+'_cases']+=1;cov[cohort+'_direct']+=case['route']=='bucket';cov[cohort+'_sat']+=labels[key]['answer']
            per.append(dict(id=key,description=desc[key],diagnostic=case['diagnostic'],answer=labels[key]['answer'],route=case['route'],counts=case['counts'],
                discovery_seconds=statistics.mean(q['cases'][i].get('discovery_seconds',0) for q in reports),solve_check_seconds=statistics.mean(q['cases'][i]['solve_check_seconds'] for q in reports)))
        coverage[mode]=dict(cov);cases[mode]=per
    assert (coverage['root']['development_direct'],coverage['root']['unique_panel_direct'],coverage['root']['repeats_direct'])==(0,12,3)
    assert coverage['tree']==coverage['closed']
    assert (coverage['closed']['development_direct'],coverage['closed']['unique_panel_direct'],coverage['closed']['repeats_direct'])==(6,17,3)
    gains=[row['id'] for row,a,b in zip(rows,cases['root'],cases['closed']) if a['route']=='fresh' and b['route']=='bucket']
    losses=[row['id'] for row,a,b in zip(rows,cases['root'],cases['closed']) if a['route']=='bucket' and b['route']=='fresh']
    remaining=[]
    for row,case in zip(rows,cases['closed']):
        if case['route']!='fresh':continue
        root=k.native.token(k.native.normalize(row['source'])[0],Counter());proof=base.load(out/'closed-0'/groups['closed'][0]['stored'][root])
        diagnostic=case['diagnostic']
        if 'attempts' not in diagnostic:_,diagnostic=k.discover(row['source'],mode='closed',**p['limits'])
        nodes=proof['nodes']
        terminal=[dict(node=x['node'],depth=nodes[x['node']]['depth'],**x['diagnostic']) for x in diagnostic['attempts'] if nodes[x['node']]['kind']=='leaf' and nodes[x['node']]['status']=='unresolved']
        assert terminal and all(x['depth']==0 for x in terminal)
        remaining.append(dict(**row,description=desc[row['id']],truth=labels[row['id']],unresolved_leaves=terminal))
    comparisons=(('closed_vs_root','closed','root'),('closed_vs_tree','closed','tree'),('closed_vs_fresh','closed','fresh'))
    analysis=dict(panel_size=48,truth=dict(Counter('sat' if labels[r['id']]['answer'] else 'unsat' for r in rows)),coverage=coverage,exact_prior_duplicates=overlaps,
        new_direct_cases=gains,coverage_losses=losses,remaining=[r['id'] for r in remaining],totals=totals,peak_rss_bytes=rss,combined_compressed_bytes=sizes,case_stats=cases,structural=structural,
        counts={m:rs[0]['counts'] for m,rs in groups.items()},reuse_cases=[c['id'] for c in cases['closed'] if c['counts'].get('closed_memo_hits',0)],
        comparisons_percent={name:100*(totals[a]['complete_seconds']/totals[b]['complete_seconds']-1) for name,a,b in comparisons},
        paired_percent={name:[100*(groups[a][i]['complete_seconds']/groups[b][i]['complete_seconds']-1) for i in range(4)] for name,a,b in comparisons},
        unique_archive_audits=len(audits),selected=min(totals,key=lambda m:totals[m]['complete_seconds']),limitations=p['limitations'])
    reused=set(analysis['reuse_cases']);strata={}
    for group in ('reused','no_new_reuse'):
        ids={c['id'] for c in cases['tree'] if ((c['id'] in reused)==(group=='reused'))};stats={'cases':len(ids)}
        for phase in ('discovery_seconds','solve_check_seconds'):
            values={m:sum(c[phase] for c in cases[m] if c['id'] in ids) for m in ('tree','closed')}
            stats[phase]={**values,'percent':100*(values['closed']/values['tree']-1)}
        strata[group]=stats
    analysis['observed_reuse_strata']=strata
    unique_remaining=[r for r in remaining if 'repeat_of' not in r['description']];leaves=[x for r in unique_remaining for x in r['unresolved_leaves']]
    analysis['remaining_shape']=dict(unique_sources=len(unique_remaining),repeated_queries=len(remaining)-len(unique_remaining),unknown_leaves=len(leaves),
        width_counts=dict(Counter(str(x.get('width')) for x in leaves)),reasons=dict(Counter(x['reason'] for x in leaves)),zero_work_leaves=sum(x['spent']==0 for x in leaves),positive_work_leaves=sum(x['spent']>0 for x in leaves))
    # Post-hoc structural diagnostic only; matched acquisition never reads it.
    from experiments import cnf_binary_equivalence as eq
    profile=[];pc=Counter();profile_start=time.perf_counter();summary=Counter()
    for row in unique_remaining:
        root=k.native.token(k.native.normalize(row['source'])[0],Counter());file=out/'closed-0'/groups['closed'][0]['stored'][root];proof=base.load(file)
        for item in row['unresolved_leaves']:
            node=proof['nodes'][item['node']];cnf=tuple(map(tuple,node['cnf']));fixed,trace,conflict=k.native.propagate(cnf,pc)
            components=k.native.components(cnf,pc);binary=tuple(c for c in cnf if len(c)==2);_,binary_proof=k.native.two_cnf(binary,pc)
            if binary_proof is not None:
                v=binary_proof['variable']
                for start,end,name in ((v,-v,'forward'),(-v,v,'backward')):
                    current=start
                    for nxt,cid in binary_proof[name]:
                        assert binary[cid]==tuple(sorted((-current,nxt)));current=nxt
                    assert current==end
            evidence=eq.discover(cnf,pc);merged=0;quotient=None
            if evidence is not None:quotient,mapping=eq.check_substitution(cnf,evidence,pc);merged=len(mapping)-1
            horn=all(sum(l>0 for l in c)<=1 for c in cnf);dual=all(sum(l<0 for l in c)<=1 for c in cnf)
            summary.update(dict(leaves=1,with_units=bool(fixed),unit_conflicts=conflict is not None,disconnected=len(components)>1,binary_conflicts=binary_proof is not None,equivalence_blocks=evidence is not None,merged_variable_occurrences=merged,horn=horn,dual_horn=dual))
            profile.append(dict(id=row['id'],proof=old.binding(file),node=item['node'],fixed=fixed,trace=trace,conflict=conflict,components=len(components),binary_proof=binary_proof,equivalence=evidence,quotient=quotient,horn=horn,dual_horn=dual))
    base.write(out/'remaining-structure-profile.json',dict(summary=dict(summary),records=profile,counts=dict(pc),seconds=time.perf_counter()-profile_start,scope='Post-hoc source-bound unit/component/binary-SCC diagnostics with checked implication paths and equivalence substitutions; not used by the measured acquisition and not additional root authority.'))
    analysis['remaining_structure_profile']=dict(summary)
    assert analysis['selected']=='fresh'
    base.write(out/'analysis.json',analysis);base.write(out/'remaining.json',dict(scope='Per-cofactor unit closure leaves unresolved closed buckets; existing fallback decides all.',cases=remaining))
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['closed_buckets']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining','remaining-structure-profile')}
    cp['closed_buckets']['supplemental_archives']=[a['archive'] for a in audits.values()];base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],
        preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('coverage','comparisons_percent','paired_percent','remaining','structural','reuse_cases','new_direct_cases','exact_prior_duplicates')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','db843605:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';oldproofs=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(oldproofs)==69 and len(proofs)==70 and proofs[:69]==oldproofs
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2266 tests in .*\n\nOK',full) and re.search(r'Ran 24 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['closed_buckets']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2266,focused_tests=24,old_proof_blocks_unchanged=69,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1248,final_sources=1253,prior_manifests=227,prior_artifacts=38630,checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=228,next_artifacts=38630+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
