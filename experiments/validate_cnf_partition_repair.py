#!/usr/bin/env python3
"""Reproduce partition repair, retained unions and all preserved source evidence."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import ast,gzip,json,marshal,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_repair as s


def clean(case):return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    started=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);s.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=s.sha(mp),artifacts_checked=len(s.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert s.sha(path)==entry['sha256'],path
        for file,h in s.load(path)['artifacts'].items():assert s.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(244,82078)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_partition_repair.py':s.sha(__file__)}
    assert len(sources)==1336
    for file,h in sources.items():assert s.sha(file)==h,file
    if 'formatting_amendment' in p:
        amendment=s.bound(p['formatting_amendment'])
        before=gzip.decompress(Path(amendment['original_source']['path']).read_bytes());after=Path(amendment['final_source']['path']).read_bytes()
        for entry in (amendment['original_source'],amendment['final_source']):assert s.sha(entry['path'])==entry['sha256']
        assert before.rstrip()+b'\n'==after and ast.dump(ast.parse(before))==ast.dump(ast.parse(after))
        filename=amendment['final_source']['path']
        assert marshal.dumps(compile(before,filename,'exec'))==marshal.dumps(compile(after,filename,'exec'))
        original=s.bound(amendment['original_protocol'])
        assert all(p[k]==v for k,v in original.items() if k!='source_fingerprints')
    rows=s.source_rows(p);truth=s.bound(p['truth']);old=s.bound(p['baseline_records'])['records'];assert len(rows)==len(truth)==len(old)==32
    for row,w in zip(rows,truth):assert s.e.previous.check(row['source'],w)['answer']
    samples=s.load(out/'comparisons.json')['samples'];assert len(samples)==8 and {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(4)}
    reports={m:[] for m in s.MODES};certs={}
    for sample in samples:
        r=s.bound(sample);mode=sample['mode'];reports[mode].append(r);dest=Path(sample['path']).parent;proofs=[]
        assert r['panel']==p['panel'] and len(r['cases'])==32
        for row,case in zip(rows,r['cases']):
            assert row['id']==case['id'];proof=s.load(dest/(str(row['id'])+'.json'));proofs.append(proof)
            got=s.check(row['source'],proof);assert json.loads(s.encode(got))==case['result']
            assert case['status']==('sat' if got['answer'] else 'unresolved')
            if sample['repeat']==0:certs[mode,row['id']]=proof
        assert json.loads(gzip.decompress((dest/'certificates.json.gz').read_bytes()))==proofs
        assert r['proof_bytes']==sum((dest/(str(row['id'])+'.json')).stat().st_size for row in rows)
        assert r['compressed_bytes']==(dest/'certificates.json.gz').stat().st_size
    for mode,runs in reports.items():
        ref=runs[0]
        for r in runs:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','compressed_bytes'):assert r[key]==ref[key],(mode,key)
            assert list(map(clean,r['cases']))==list(map(clean,ref['cases']))
        total=Counter()
        for row,case,prior in zip(rows,ref['cases'],old):
            counts=Counter();proof,diag=s.discover(row['source'],mode,counts)
            assert proof==certs[mode,row['id']] and diag==case['diagnostic'] and dict(counts)==case['discovery_counts']
            if mode=='baseline':assert diag['search']==prior['result'] and dict(counts)==prior['counts']
            got=s.check(row['source'],proof,counts);assert dict(counts)==case['counts'];assert json.loads(s.encode(got))==case['result'];total.update(counts)
        assert dict(total)==ref['counts']
        for key,repeats in [('warm_counts',1),('cold_counts',2)]:
            cc=Counter()
            for _ in range(repeats):
                for row in s.source_rows(p):s.check(row['source'],certs[mode,row['id']],cc)
            assert dict(cc)==ref[key]
    totals={};coverage={};rss={};states={}
    for mode,runs in reports.items():
        totals[mode]={k:statistics.mean(r[k] for r in runs) for k in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','compressed_bytes')}
        totals[mode]['phases']={k:statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
        coverage[mode]=dict(Counter(c['status'] for c in runs[0]['cases']));rss[mode]=max(r['peak_rss_bytes'] for r in runs)
        states[mode]=sum(c['diagnostic']['search']['diagnostic']['expanded'] for c in runs[0]['cases'])
    gains=[];remaining=[];union=[]
    for row,a,b in zip(rows,reports['baseline'][0]['cases'],reports['partition'][0]['cases']):
        assert a['status']=='unresolved' or b['status']=='sat'
        binding=s.binding(out/'partition-0'/(str(row['id'])+'.json'))
        if a['status']=='unresolved' and b['status']=='sat':gains.append(row['id'])
        if b['status']=='unresolved':remaining.append(dict(**row,certificate=binding,diagnostic=b['diagnostic']))
        union.append(dict(id=row['id'],status=b['status'],certificate=binding))
    assert gains==[3,9,19,22,23,28,30] and [r['id'] for r in remaining]==[24,25,29]
    s.write(out/'remaining.json',dict(records=remaining,scope='Repair-only unresolved cases; the full portfolio was not evaluated on this constructed panel.'))
    s.write(out/'coverage-union.json',dict(records=union,scope='32 exposed constructed cases; distinct from preserved external 37/37 and synthetic 182/182 unions.'))
    analysis=dict(totals=totals,coverage=coverage,states=states,peak_rss_bytes=rss,gains=gains,remaining=[r['id'] for r in remaining],comparison_percent=100*(totals['partition']['complete_seconds']/totals['baseline']['complete_seconds']-1),paired_percent=[100*(reports['partition'][i]['complete_seconds']/reports['baseline'][i]['complete_seconds']-1) for i in range(4)],limitations=p['limitations'])
    s.write(out/'analysis.json',analysis)
    semantic=s.load(out/'semantic-audit.json');assert semantic['passed'] and semantic['counts']['fresh_inputs']==64 and semantic['checked_reuses']==semantic['invalidated_witnesses']==39
    d=s.load(out/'distance-diagnostic.json');assert d['minimum_distance']==26
    assert s.e.check_exclusion(d['source'],s.load(out/'radius-25-exclusion.json'))==dict(no_model_within_radius=True,radius=25,global_unsat=False)
    w=s.load(out/'distance-26-witness.json');assert s.e.previous.check(d['source'],w)['answer'] and sum(a!=b for a,b in zip(w['values'],d['seed']['values']))==26
    external=s.bound(parent['hamming_repair']['coverage-union'])
    external_rows=s.load('experiments/results/cnf-external-cutsets/panel.json');assert len(external['records'])==len(external_rows)==37
    for row,entry in zip(external_rows,external['records']):
        assert row['id']==entry['id'];got=s.e.baseline.check_pipeline(row['source'],s.bound(entry['certificate']))
        assert entry['status']==('sat' if got['answer'] else 'unsat') and got['answer'] is not None
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['partition_repair']={k:s.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis','remaining','coverage-union','semantic-audit','distance-diagnostic','radius-25-exclusion','distance-26-witness')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=s.bound(parent['factor_conditioning']['coverage-union']),external_union_unchanged_and_rechecked=37,seconds=time.perf_counter()-started,checkpoint=s.binding(out/'checkpoint.json')))
    print(s.encode(analysis))


def seal(out):
    v=s.load(out/'validation.json');cp=s.load(out/'checkpoint.json');assert v['passed']
    for file,h in cp['source_fingerprints'].items():assert s.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','c0d736c7:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';old=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==84 and proofs[:84]==old and len(proofs)==85
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2528 tests in .*\n\nOK',full) and re.search(r'Ran 23 tests in .*\n\nOK',focused)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    decision=s.load(out/'decision.json')
    for file,h in decision['documents'].items():assert s.sha(file)==h,file
    s.bound(decision['supplemental_checks']);cp['partition_repair']['decision']=s.binding(out/'decision.json');s.write(out/'checkpoint.json',cp)
    v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    s.write(out/'checks.json',dict(passed=True,full_tests=2528,focused_tests=23,old_proof_blocks_unchanged=84,added_proof_blocks=1,prior_sources=1331,final_sources=1336,prior_manifests=244,prior_artifacts=82078,checkpoint=s.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}));print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=245,next_artifacts=82078+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
