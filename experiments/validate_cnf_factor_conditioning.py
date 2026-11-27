#!/usr/bin/env python3
"""Check cutset certificates, root coverage and immutable experimental lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_factor_conditioning as s
base=s.base;old=s.old


def validate(out):
    started=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json');manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest']);manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for file,h in base.load(path)['artifacts'].items():assert base.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(239,80405)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_factor_conditioning.py':base.sha(__file__)}
    for file,h in sources.items():assert base.sha(file)==h,file
    assert len(sources)==1312
    rows=old.bound(p['panel']);contexts={r['root_id']:old.bound(r['context']) for r in rows};assert len(rows)==3
    assert [{k:r[k] for k in ('id','root_id','node','source','prefix')} for r in rows]==base.load(s.PARENT/'panel.json')
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==32
    assert {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(8)}
    groups={}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];groups.setdefault(mode,[]).append(r);dest=Path(sample['path']).parent;proofs=[]
        assert r['panel']==p['panel'] and len(r['cases'])==3
        with s.verified.installed(s.verified.VerifiedOperators()):
            for row,case in zip(rows,r['cases']):
                assert row['id']==case['id'];proof=base.load(dest/(row['id']+'.json'));proofs.append(proof)
                got=s.check(row,contexts[row['root_id']],mode,proof,Counter());assert json.loads(base.encode(got))==case['result']
                if got['root']['answer']:assert s.f.native.holds(row['root_source'],got['root']['model'])
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==proofs
        assert r['proof_bytes']==sum((dest/(row['id']+'.json')).stat().st_size for row in rows)
        assert r['compressed_bytes']==(dest/'certificates.json.gz').stat().st_size and len(r['cache_sessions'])==4
    for mode,reports in groups.items():
        reference=reports[0]
        for r in reports:
            for key in ('cases','counts','warm_counts','cold_counts','proof_bytes','compressed_bytes','cache_sessions'):assert r[key]==reference[key],(mode,key)
        counts=Counter()
        with s.verified.installed(s.verified.VerifiedOperators()):
            for row,case in zip(rows,reference['cases']):
                cc=Counter();proof,diag=s.acquire(row,mode,cc);got=s.check(row,contexts[row['root_id']],mode,proof,cc)
                assert proof==base.load(out/(mode+'-0')/(row['id']+'.json')) and diag==case['diagnostic'] and json.loads(base.encode(got))==case['result'] and dict(cc)==case['counts'];counts.update(cc)
        assert dict(counts)==reference['counts']
        for label,repeats in [('warm_counts',1),('cold_counts',2)]:
            counts=Counter()
            for _ in range(repeats):
                with s.verified.installed(s.verified.VerifiedOperators()):
                    for row in rows:s.check(row,contexts[row['root_id']],mode,base.load(out/(mode+'-0')/(row['id']+'.json')),counts)
            assert dict(counts)==reference[label]
    # Revalidate the old 180 authorities and add only newly checked root models.
    olddir=Path('experiments/results/cnf-verified-operators');oldpanel=base.load(olddir/'panel.json');report=base.load(olddir/'pass-0/report.json');coverage=[];new={}
    with s.verified.installed(s.verified.VerifiedOperators()):
        for row in rows:
            proof=base.load(out/'cut4-0'/(row['id']+'.json'));got=s.check(row,contexts[row['root_id']],'cut4',proof,Counter())
            if got['root']['answer']:new[row['root_id']]=(row,got['root'],old.binding(out/'cut4-0'/(row['id']+'.json')))
        for row,case in zip(oldpanel,report['cases']):
            assert row['id']==case['id'];key=s.f.native.token(s.f.native.normalize(row['source'])[0],Counter());path=olddir/'pass-0'/report['stored'][key];proof=base.load(path);got=s.f.previous.check_certificate(row['source'],proof)
            entry=dict(id=row['id'],prior=old.binding(path),answer=got['answer'],route='retained')
            if got['answer'] is None:
                front,result,binding=new[row['id']];assert row['source']==front['root_source'];assert s.f.native.holds(row['source'],result['model'])
                entry.update(answer=True,route='new-root-model',frontier=front['id'],conditioning=binding,context=front['context'],model=result['model'])
            coverage.append(entry)
    assert len(coverage)==182 and sum(r['route']=='retained' for r in coverage)==180 and len(new)==2 and all(r['answer'] is not None for r in coverage)
    base.write(out/'coverage-union.json',dict(records=coverage,scope='Independently rechecked union of 180 retained authorities and two transported original-source SAT witnesses. No new complete-pipeline timing or external-distribution coverage claim.'))
    totals={};rss={};statuses={};newroots={};branches={}
    for mode,reports in groups.items():
        r=reports[0];totals[mode]={key:statistics.mean(x[key] for x in reports) for key in ('complete_stage_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','compressed_bytes')};totals[mode]['phases']={key:statistics.mean(x['phases'][key] for x in reports) for key in r['phases']};rss[mode]=max(x['peak_rss_bytes'] for x in reports);statuses[mode]=[x['status'] for x in r['cases']];newroots[mode]=sorted({row['root_id'] for row,case in zip(rows,r['cases']) if case['result']['root']['answer']})
        if mode=='wide':continue
        branches[mode]=[]
        for row,case in zip(rows,r['cases']):
            proof=base.load(out/(mode+'-0')/(row['id']+'.json'));outcomes=Counter(b['terminal']['status'] if b['terminal'] is not None else 'unresolved' for b in proof['branches'])
            branches[mode].append(dict(id=row['id'],cutset=proof['cutset'],outcomes=dict(outcomes),reserved_work=case['diagnostic']['reserved_work'],projected_steps=sum(len(b['terminal']['steps']) for b in proof['branches'] if b['terminal'] is not None)))
    comparisons=[('cut4','wide'),('cut4','cut0'),('cut4','cut2'),('cut2','cut0')]
    analysis=dict(totals=totals,peak_rss_bytes=rss,statuses=statuses,new_roots=newroots,branches=branches,counts={mode:{key:r[0][key] for key in ('counts','warm_counts','cold_counts')} for mode,r in groups.items()},comparisons_percent={a+'_vs_'+b:100*(totals[a]['complete_stage_seconds']/totals[b]['complete_stage_seconds']-1) for a,b in comparisons},paired_percent={a+'_vs_'+b:[100*(groups[a][i]['complete_stage_seconds']/groups[b][i]['complete_stage_seconds']-1) for i in range(8)] for a,b in comparisons},limitations=p['limitations'],retained_root_coverage=180,union_root_coverage=182,root_panel_size=182)
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources);cp['factor_conditioning']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','coverage-union')};base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,seconds=time.perf_counter()-started,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('totals','statuses','new_roots','branches','comparisons_percent','paired_percent')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for file,h in cp['source_fingerprints'].items():assert base.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','6590dd04:'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}';previous=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S);assert len(previous)==81 and len(proofs)==82 and proofs[:81]==previous
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2431 tests in .*\n\nOK',full) and re.search(r'Ran 16 tests in .*\n\nOK',focused)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['factor_conditioning']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2431,focused_tests=16,old_proof_blocks_unchanged=81,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+)pages,',re.sub(r'\s+','',latex))[1]),prior_sources=1308,final_sources=1312,prior_manifests=239,prior_artifacts=80405,checkpoint=old.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(file for file in out.rglob('*') if file.is_file() and file.name!='manifest.json' and '__pycache__' not in file.parts);base.write(out/'manifest.json',dict(artifacts={str(file):base.sha(file) for file in files}));print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=240,next_artifacts=80405+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
