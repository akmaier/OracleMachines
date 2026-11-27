#!/usr/bin/env python3
"""Recheck capacity coverage, complete costs, source lineage and cold replay."""
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
import gzip, json, re, statistics, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_capacity_core as s
base=s.base; old=s.old


def clean(case):
    return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    started=time.perf_counter(); p=base.load(out/'protocol.json'); parent=old.bound(p['parent'])
    pv=base.load(s.PARENT/'validation.json'); manifests=deepcopy(pv['parent_manifests'])
    mp=Path(p['parent_manifest']['path']); old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path, entry in manifests.items():
        assert base.sha(path)==entry['sha256'],path
        for file,h in base.load(path)['artifacts'].items(): assert base.sha(file)==h,file; artifacts+=1
    assert (len(manifests),artifacts)==(241,80996)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_capacity_core.py':base.sha(__file__)}
    for file,h in sources.items(): assert base.sha(file)==h,file
    assert len(sources)==1321
    rows=old.bound(p['panel']); desc=old.bound(p['descriptions']); assert len(rows)==37
    samples=base.load(out/'comparisons.json')['samples']; assert len(samples)==8
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(4)}
    reports={m:[] for m in s.MODES}; certs={}
    for sample in samples:
        r=old.bound(sample); mode=sample['mode']; reports[mode].append(r); dest=Path(sample['path']).parent
        assert r['panel']==p['panel'] and len(r['cases'])==37
        proofs=[]
        with s.verified.installed(s.verified.VerifiedOperators()):
            for row,case in zip(rows,r['cases']):
                assert row['id']==case['id']; proof=base.load(dest/(row['id']+'.json')); proofs.append(proof)
                got=s.e.check_pipeline(s.prior.source(row),proof)
                assert json.loads(base.encode(got))==case['result']
                expected=desc[row['id']]['publisher_answer']
                if expected is not None and got['answer'] is not None: assert got['answer']==expected
                if sample['repeat']==0: certs[mode,row['id']]=proof
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==proofs
        assert r['proof_bytes']==sum((dest/(row['id']+'.json')).stat().st_size for row in rows)
        assert r['compressed_bytes']==(dest/'certificates.json.gz').stat().st_size
    for mode, runs in reports.items():
        ref=runs[0]
        for r in runs:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','compressed_bytes','cache_sessions'):
                assert r[key]==ref[key],(mode,key)
            assert list(map(clean,r['cases']))==list(map(clean,ref['cases']))
        counts=Counter()
        with s.verified.installed(s.verified.VerifiedOperators()):
            for row,case in zip(rows,ref['cases']):
                cc=Counter(); proof,diag=s.e.pipeline(s.prior.source(row),cc,enabled=mode=='capacity')
                got=s.e.check_pipeline(row['source'],proof,cc)
                assert proof==certs[mode,row['id']] and diag==case['diagnostic'] and dict(cc)==case['counts']
                assert json.loads(base.encode(got))==case['result']; counts.update(cc)
        assert dict(counts)==ref['counts']
        for key,repeats in [('warm_counts',1),('cold_counts',2)]:
            cc=Counter()
            for _ in range(repeats):
                with s.verified.installed(s.verified.VerifiedOperators()):
                    for row in rows: s.e.check_pipeline(s.prior.source(row),certs[mode,row['id']],cc)
            assert dict(cc)==ref[key]
    # Baseline proof payloads remain identical to the previous checkpoint.
    for row in rows:
        a=certs['baseline',row['id']]; b=certs['capacity',row['id']]
        assert a==dict(kind='external',proof=base.load(s.PARENT/'expanded-0'/(row['id']+'.json')))
        if b['kind']=='external': assert b==a
    totals={}; coverage={}; rss={}; per_case={}
    for mode,runs in reports.items():
        totals[mode]={key:statistics.mean(r[key] for r in runs) for key in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','compressed_bytes')}
        totals[mode]['phases']={key:statistics.mean(r['phases'][key] for r in runs) for key in runs[0]['phases']}
        rss[mode]=max(r['peak_rss_bytes'] for r in runs); groups=defaultdict(Counter); per=[]
        for j,(row,case) in enumerate(zip(rows,runs[0]['cases'])):
            d=desc[row['id']]
            for key in ('all',d['kind'],d['kind']+':'+d['group']):
                groups[key][case['status']]+=1; groups[key]['cases']+=1; groups[key]['certified']+=case['status']!='unresolved'
            per.append(dict(id=row['id'],status=case['status'],kind=d['kind'],group=d['group'],certificate_kind=certs[mode,row['id']]['kind'],acquisition_seconds=statistics.mean(r['cases'][j]['acquisition_seconds'] for r in runs),checking_seconds=statistics.mean(r['cases'][j]['checking_seconds'] for r in runs)))
        coverage[mode]={k:dict(v) for k,v in groups.items()}; per_case[mode]=per
    gains=[]; remaining=[]; union=[]
    for row,a,b in zip(rows,reports['baseline'][0]['cases'],reports['capacity'][0]['cases']):
        assert a['status']=='unresolved' or a['status']==b['status']
        binding=old.binding(out/'capacity-0'/(row['id']+'.json'))
        if a['status']=='unresolved' and b['status']!='unresolved': gains.append(row['id'])
        if b['status']=='unresolved': remaining.append(dict(**row,description=desc[row['id']],certificate=binding,diagnostic=b['diagnostic']))
        union.append(dict(id=row['id'],status=b['status'],certificate=binding,kind=certs['capacity',row['id']]['kind']))
    base.write(out/'remaining.json',dict(records=remaining))
    base.write(out/'coverage-union.json',dict(records=union,scope='External 25 originals and 12 derived controls, separate from unchanged synthetic 182/182 union.'))
    analysis=dict(totals=totals,coverage=coverage,peak_rss_bytes=rss,cases=per_case,gains=gains,remaining=[r['id'] for r in remaining],comparison_percent=100*(totals['capacity']['complete_seconds']/totals['baseline']['complete_seconds']-1),paired_percent=[100*(reports['capacity'][i]['complete_seconds']/reports['baseline'][i]['complete_seconds']-1) for i in range(4)],limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    semantic=base.load(out/'semantic-audit.json'); assert semantic['passed']
    assert semantic['counts']['invalidated_deleted_support']==22 and semantic['counts']['mixture_inputs']==48
    cp=deepcopy(parent); cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['capacity_core']={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis','remaining','coverage-union','semantic-audit')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=old.bound(parent['factor_conditioning']['coverage-union']),seconds=time.perf_counter()-started,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode({k:analysis[k] for k in ('totals','coverage','peak_rss_bytes','gains','remaining','comparison_percent','paired_percent')}))


def seal(out):
    v=base.load(out/'validation.json'); cp=base.load(out/'checkpoint.json'); assert v['passed']
    for file,h in cp['source_fingerprints'].items(): assert base.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before=subprocess.check_output(['git','show','33f5a36c:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    old_proofs=re.findall(pattern,before,re.S); proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old_proofs)==82 and proofs[:-1]==old_proofs and len(proofs)==83
    full=(out/'full-tests.log').read_text(); focused=(out/'focused-tests.log').read_text(); latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2467 tests in .*\n\nOK',full) and re.search(r'Ran 20 tests in .*\n\nOK',focused)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    decision=base.load(out/'decision.json')
    for file,h in decision['documents'].items(): assert base.sha(file)==h,file
    old.bound(decision['supplemental_checks'])
    cp['capacity_core']['decision']=old.binding(out/'decision.json'); base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json'); base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2467,focused_tests=20,old_proof_blocks_unchanged=82,added_proof_blocks=1,manuscript_pages=int(re.search(r'\((\d+)pages,',re.sub(r'\s+','',latex))[1]),prior_sources=1316,final_sources=1321,prior_manifests=241,prior_artifacts=80996,checkpoint=old.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes(); original=Path(str(file)+'.raw.gz')
        if not original.exists(): original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=242,next_artifacts=80996+len(files))))


if __name__=='__main__': globals()[sys.argv[1]](Path(sys.argv[2]))
