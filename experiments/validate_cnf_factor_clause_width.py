#!/usr/bin/env python3
"""Replay the factor-width partition, exact recomposition and immutable lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_factor_clause_width as s
base=s.base;old=s.old;f=s.f


def validate(out):
    started=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json');manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest']);manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for file,h in base.load(path)['artifacts'].items():assert base.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(238,80208)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_factor_clause_width.py':base.sha(__file__)}
    for file,h in sources.items():assert base.sha(file)==h,file
    assert len(sources)==1308
    rows=old.bound(p['panel']);frontier=old.bound(p['frontier'])
    assert rows==[dict(id=r['id']+':'+str(r['node']),root_id=r['id'],node=r['node'],source=r['source'],prefix=r['prefix']) for r in frontier['records']]
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==32
    assert {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(8)}
    groups={};census=[];summary=Counter();details=[]
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];groups.setdefault(mode,[]).append(r);dest=Path(sample['path']).parent;proofs=[]
        assert r['panel']==p['panel'] and len(r['cases'])==3
        for row,case in zip(rows,r['cases']):
            assert row['id']==case['id'];proof=base.load(dest/(row['id']+'.json'));proofs.append(proof)
            assert s.check(row,mode,proof,Counter())==case['result']
            if case['result']['answer']:assert s.continuation.native.holds(row['source'],{int(v):x for v,x in case['result']['model'].items()})
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==proofs
        assert r['proof_bytes']==sum((dest/(row['id']+'.json')).stat().st_size for row in rows)
        assert r['compressed_bytes']==(dest/'certificates.json.gz').stat().st_size and len(r['cache_sessions'])==4
    for mode,reports in groups.items():
        reference=reports[0]
        for r in reports:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','compressed_bytes','cache_sessions'):assert r[key]==reference[key],(mode,key)
            for x,y in zip(r['cases'],reference['cases']):
                for key in ('id','status','result','diagnostic','counts'):assert x[key]==y[key],(mode,key)
        counts=Counter()
        with s.verified.installed(s.verified.VerifiedOperators()):
            for row,case in zip(rows,reference['cases']):
                cc=Counter();proof,diag=s.acquire(row,mode,cc);got=s.check(row,mode,proof,cc)
                assert proof==base.load(out/(mode+'-0')/(row['id']+'.json')) and diag==case['diagnostic'] and got==case['result'] and dict(cc)==case['counts'];counts.update(cc)
        assert dict(counts)==reference['counts']
        for label,repeats in [('warm_counts',1),('cold_counts',2)]:
            counts=Counter()
            for _ in range(repeats):
                with s.verified.installed(s.verified.VerifiedOperators()):
                    for row in rows:s.check(row,mode,base.load(out/(mode+'-0')/(row['id']+'.json')),counts)
            assert dict(counts)==reference[label]
    # Complete same-variable width census for every active factor, with negative
    # certificates independently checked; this is outside matched stage timing.
    for row in rows:
        _,_,_,factors,active,spent=f.checked_prefix(row['source'],row['prefix'],Counter());per=Counter()
        for index in sorted(active):
            factor=factors[index];certificates=[];minimum=None
            for width in range(5):
                proof,diag=f.discover(factor,width);status=f.check(factor,proof);certificates.append(dict(proof=proof,diagnostic=diag));per['width_'+str(width)+'_'+status]+=1
                if minimum is None and status=='cover':minimum=width
            assert minimum is not None
            summary['minimum_'+str(minimum)]+=1;summary['factors']+=1
            if len(factor['scope'])>3 and factor['bits'].bit_count()<(1<<len(factor['scope']))-1:summary['dense_factors']+=1;summary['dense_minimum_'+str(minimum)]+=1
            census.append(dict(id=row['id'],index=index,factor=factor,minimum_width=minimum,certificates=certificates))
        details.append(dict(id=row['id'],counts=dict(per),prefix_spent=spent))
    base.write(out/'width-census.json',dict(records=census,summary=dict(summary),frontiers=details,scope='Post-hoc exhaustive widths zero through four on all active explicit factors. Every cover and every width obstruction checked. Representation bound excludes auxiliary variables and external constraints; it is not a solver-time lower bound.'))
    totals={};rss={};statuses={};progress={}
    for mode,reports in groups.items():
        r=reports[0];totals[mode]={key:statistics.mean(x[key] for x in reports) for key in ('complete_stage_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','compressed_bytes')};totals[mode]['phases']={key:statistics.mean(x['phases'][key] for x in reports) for key in r['phases']};rss[mode]=max(x['peak_rss_bytes'] for x in reports);statuses[mode]=[x['status'] for x in r['cases']]
        progress[mode]=[]
        for row,case in zip(rows,r['cases']):
            proof=base.load(out/(mode+'-0')/(row['id']+'.json'));terminal=proof.get('terminal') if mode.startswith('clause') else proof if mode=='wide' else None
            progress[mode].append(dict(id=row['id'],steps=0 if terminal is None else len(terminal['steps']),status=case['status'],diagnostic=case['diagnostic']))
    comparisons=[('clause3','hold'),('clause4','hold'),('clause4','wide'),('clause4','clause3')]
    analysis=dict(totals=totals,peak_rss_bytes=rss,statuses=statuses,progress=progress,census=dict(summary),counts={mode:{key:r[0][key] for key in ('counts','warm_counts','cold_counts')} for mode,r in groups.items()},comparisons_percent={a+'_vs_'+b:100*(totals[a]['complete_stage_seconds']/totals[b]['complete_stage_seconds']-1) for a,b in comparisons},paired_percent={a+'_vs_'+b:[100*(groups[a][i]['complete_stage_seconds']/groups[b][i]['complete_stage_seconds']-1) for i in range(8)] for a,b in comparisons},limitations=p['limitations'],root_coverage_unchanged=180,root_panel_size=182)
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources);cp['factor_clause_width']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','width-census')};base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,seconds=time.perf_counter()-started,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('totals','statuses','census','comparisons_percent','paired_percent')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for file,h in cp['source_fingerprints'].items():assert base.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','8f847075:'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}';previous=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S);assert len(previous)==80 and len(proofs)==81 and proofs[:80]==previous
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2415 tests in .*\n\nOK',full) and re.search(r'Ran 14 tests in .*\n\nOK',focused)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['factor_clause_width']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2415,focused_tests=14,old_proof_blocks_unchanged=80,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+)pages,',re.sub(r'\s+','',latex))[1]),prior_sources=1304,final_sources=1308,prior_manifests=238,prior_artifacts=80208,checkpoint=old.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(file for file in out.rglob('*') if file.is_file() and file.name!='manifest.json' and '__pycache__' not in file.parts);base.write(out/'manifest.json',dict(artifacts={str(file):base.sha(file) for file in files}));print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=239,next_artifacts=80208+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
