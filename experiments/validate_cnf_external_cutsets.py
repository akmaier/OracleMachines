#!/usr/bin/env python3
"""Audit frozen external data, full certificates, costs and immutable lineage."""
from collections import Counter,defaultdict
from copy import deepcopy
from pathlib import Path
import gzip,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_external_cutsets as s
base=s.base;old=s.old


def clean_case(case):return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    started=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json');manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest']);manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for file,h in base.load(path)['artifacts'].items():assert base.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(240,80609)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_external_cutsets.py':base.sha(__file__)}
    for file,h in sources.items():assert base.sha(file)==h,file
    assert len(sources)==1316
    selection=old.bound(p['selection']);acquisition=old.bound(p['acquisition']);rows=old.bound(p['panel']);desc=old.bound(p['descriptions']);overlaps=old.bound(p['overlaps']);assert acquisition['selection_sha256']==p['selection']['sha256'] and len(rows)==37 and len(acquisition['records'])==25
    for row in rows:assert s.source(row)==row['source']
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==8 and {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(4)}
    groups={};certs={}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];groups.setdefault(mode,[]).append(r);dest=Path(sample['path']).parent;proofs=[]
        assert r['panel']==p['panel'] and len(r['cases'])==37
        with s.verified.installed(s.verified.VerifiedOperators()):
            for row,case in zip(rows,r['cases']):
                assert row['id']==case['id'];proof=base.load(dest/(row['id']+'.json'));proofs.append(proof)
                got=s.e.check(s.source(row),proof);assert json.loads(base.encode(got))==case['result']
                if got['answer']:assert s.e.native.holds(row['source'],got['model'])
                expected=desc[row['id']]['publisher_answer']
                if got['answer'] is not None and expected is not None:assert got['answer']==expected,(row['id'],'publisher mismatch')
                if sample['repeat']==0:certs[mode,row['id']]=proof
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==proofs
        assert r['proof_bytes']==sum((dest/(row['id']+'.json')).stat().st_size for row in rows)
        assert r['compressed_bytes']==(dest/'certificates.json.gz').stat().st_size and len(r['cache_sessions'])==4
    for mode,reports in groups.items():
        reference=reports[0]
        for r in reports:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','compressed_bytes','cache_sessions'):assert r[key]==reference[key],(mode,key)
            assert list(map(clean_case,r['cases']))==list(map(clean_case,reference['cases']))
        counts=Counter()
        with s.verified.installed(s.verified.VerifiedOperators()):
            for row,case in zip(rows,reference['cases']):
                cc=Counter();proof,diag=s.e.discover(s.source(row),cc,expand=mode=='expanded');got=s.e.check(row['source'],proof,cc)
                assert proof==certs[mode,row['id']] and diag==case['diagnostic'] and json.loads(base.encode(got))==case['result'] and dict(cc)==case['counts'];counts.update(cc)
        assert dict(counts)==reference['counts']
        for label,repeats in [('warm_counts',1),('cold_counts',2)]:
            counts=Counter()
            for _ in range(repeats):
                with s.verified.installed(s.verified.VerifiedOperators()):
                    for row in rows:s.e.check(s.source(row),certs[mode,row['id']],counts)
            assert dict(counts)==reference[label]
    for row in rows:assert certs['baseline',row['id']]['context']==certs['expanded',row['id']]['context']
    totals={};rss={};coverage={};cases={};gains=[];remaining=[]
    for mode,reports in groups.items():
        r=reports[0];totals[mode]={key:statistics.mean(x[key] for x in reports) for key in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','compressed_bytes')};totals[mode]['phases']={key:statistics.mean(x['phases'][key] for x in reports) for key in r['phases']};rss[mode]=max(x['peak_rss_bytes'] for x in reports)
        strata=defaultdict(Counter);per=[]
        for row,case in zip(rows,r['cases']):
            d=desc[row['id']];status=case['status']
            for key in ('all',d['kind'],d['kind']+':'+d['group']):strata[key][status]+=1;strata[key]['cases']+=1;strata[key]['certified']+=status!='unresolved'
            per.append(dict(id=row['id'],kind=d['kind'],group=d['group'],status=status,acquisition_seconds=statistics.mean(x['cases'][len(per)]['acquisition_seconds'] for x in reports),checking_seconds=statistics.mean(x['cases'][len(per)]['checking_seconds'] for x in reports)))
        coverage[mode]={k:dict(v) for k,v in strata.items()};cases[mode]=per
    for row,a,b in zip(rows,groups['baseline'][0]['cases'],groups['expanded'][0]['cases']):
        assert a['status']=='unresolved' or b['status']==a['status']
        if a['status']=='unresolved' and b['status']!='unresolved':gains.append(row['id'])
        if b['status']!='unresolved':continue
        proof=certs['expanded',row['id']];details=[]
        for attempt,diag in zip(proof['attempts'],b['diagnostic']['expansion']):
            cert=attempt['certificate'];record=dict(target=attempt['target'],reason=diag['reason'])
            if cert is not None:
                counts=Counter(x['certificate']['status'] for x in cert['entries']);record.update(factor_classification=dict(counts),cutset=cert['cutset'],branch_statuses=dict(Counter(x['terminal']['status'] if x['terminal'] else 'unresolved' for x in cert['branches'])),diagnostic=diag['diagnostic'])
            details.append(record)
        remaining.append(dict(id=row['id'],source=row['source'],description=desc[row['id']],certificate=old.binding(out/'expanded-0'/(row['id']+'.json')),attempts=details))
    base.write(out/'remaining.json',dict(records=remaining,scope='Source-bound unresolved external/derived inputs; publisher labels do not close them. Candidate-budget failure is separate from checked same-variable width obstruction.'))
    analysis=dict(totals=totals,peak_rss_bytes=rss,coverage=coverage,cases=cases,gains=gains,remaining=[r['id'] for r in remaining],comparison_percent=100*(totals['expanded']['complete_seconds']/totals['baseline']['complete_seconds']-1),paired_percent=[100*(groups['expanded'][i]['complete_seconds']/groups['baseline'][i]['complete_seconds']-1) for i in range(4)],counts={mode:{key:r[0][key] for key in ('counts','warm_counts','cold_counts')} for mode,r in groups.items()},limitations=p['limitations'],prior_union_unchanged=182)
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources);cp['external_cutsets']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining','acquisition','overlaps')};base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=old.bound(parent['factor_conditioning']['coverage-union']),seconds=time.perf_counter()-started,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({key:analysis[key] for key in ('totals','coverage','gains','remaining','comparison_percent','paired_percent')}))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for file,h in cp['source_fingerprints'].items():assert base.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','a41b2129:'+paper],text=True);pattern=r'\\begin\{proof\}.*?\\end\{proof\}';previous=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S);assert len(previous)==82 and proofs==previous
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2447 tests in .*\n\nOK',full) and re.search(r'Ran 16 tests in .*\n\nOK',focused)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['external_cutsets']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2447,focused_tests=16,old_proof_blocks_unchanged=82,added_proof_blocks=0,manuscript_pages=int(re.search(r'\((\d+)pages,',re.sub(r'\s+','',latex))[1]),prior_sources=1312,final_sources=1316,prior_manifests=240,prior_artifacts=80609,checkpoint=old.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(file for file in out.rglob('*') if file.is_file() and file.name!='manifest.json' and '__pycache__' not in file.parts);base.write(out/'manifest.json',dict(artifacts={str(file):base.sha(file) for file in files}));print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=241,next_artifacts=80609+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
