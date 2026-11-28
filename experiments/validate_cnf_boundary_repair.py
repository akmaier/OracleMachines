#!/usr/bin/env python3
"""Reproduce boundary discovery, cold evidence checks and immutable lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_boundary_repair as s


def clean(case):return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    started=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);s.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=s.sha(mp),artifacts_checked=len(s.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert s.sha(path)==entry['sha256'],path
        for file,h in s.load(path)['artifacts'].items():assert s.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(245,82407)
    sources=p['source_fingerprints'];assert len(sources)==1341
    for file,h in sources.items():assert s.sha(file)==h,file
    rows=s.source_rows(p);truth=s.bound(p['truth']);old=s.bound(p['baseline'])['cases'];assert len(rows)==len(truth)==len(old)==32
    for row,w in zip(rows,truth):assert s.e.previous.check(row['source'],w)['answer']
    samples=s.load(out/'comparisons.json')['samples'];assert len(samples)==8 and {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(4)}
    reports={m:[] for m in s.MODES};certs={};evidence={}
    for sample in samples:
        r=s.bound(sample);mode=sample['mode'];reports[mode].append(r);dest=Path(sample['path']).parent;proofs=[];evs=s.load(dest/'discovery.json')
        assert r['panel']==p['panel'] and len(r['cases'])==len(evs)==32
        for row,case,ev in zip(rows,r['cases'],evs):
            assert row['id']==case['id'];proof=s.load(dest/(str(row['id'])+'.json'));proofs.append(proof)
            got=s.check(row['source'],proof);s.e.check_evidence(row['source'],ev)
            assert json.loads(s.encode(got))==case['result'];assert case['status']==('sat' if got['answer'] else 'unresolved')
            if sample['repeat']==0:certs[mode,row['id']]=proof;evidence[mode,row['id']]=ev
        for name,data in (('certificates',proofs),('discovery',evs),('combined',dict(proofs=proofs,evidence=evs))):
            assert json.loads(gzip.decompress((dest/(name+'.json.gz')).read_bytes()))==data
            assert r['compressed_bytes'][name]==(dest/(name+'.json.gz')).stat().st_size
        assert r['proof_bytes']==sum((dest/(str(row['id'])+'.json')).stat().st_size for row in rows)
        assert r['evidence_bytes']==(dest/'discovery.json').stat().st_size
    for mode,runs in reports.items():
        ref=runs[0]
        for r in runs:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','evidence_bytes','compressed_bytes'):assert r[key]==ref[key],(mode,key)
            assert list(map(clean,r['cases']))==list(map(clean,ref['cases']))
        total=Counter()
        for row,case,prior in zip(rows,ref['cases'],old):
            counts=Counter();proof,ev,diag=s.discover(row['source'],mode,counts)
            assert proof==certs[mode,row['id']] and ev==evidence[mode,row['id']] and diag==case['diagnostic'] and dict(counts)==case['discovery_counts']
            if mode=='baseline':
                assert diag['prefix']==prior['diagnostic']['search']['diagnostic']
                assert proof['witness']==prior['diagnostic']['search']['witness']
                assert {k:v for k,v in counts.items() if not k.startswith('boundary_')}==prior['discovery_counts']
            if prior['status']=='sat':assert proof['witness']==prior['diagnostic']['search']['witness']
            assert diag['expanded']<=p['node_limit']
            assert diag['expanded']==diag['prefix']['expanded']+sum(d['search']['expanded'] for d in diag['rounds'])
            got=s.check(row['source'],proof,counts);s.e.check_evidence(row['source'],ev,counts)
            assert dict(counts)==case['counts'];assert json.loads(s.encode(got))==case['result'];total.update(counts)
        assert dict(total)==ref['counts']
        for key,repeats in [('warm_counts',1),('cold_counts',2)]:
            cc=Counter()
            for _ in range(repeats):
                for row in s.source_rows(p):s.check(row['source'],certs[mode,row['id']],cc);s.e.check_evidence(row['source'],evidence[mode,row['id']],cc)
            assert dict(cc)==ref[key]
    totals={};coverage={};rss={};states={}
    for mode,runs in reports.items():
        totals[mode]={k:statistics.mean(r[k] for r in runs) for k in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','evidence_bytes')}
        totals[mode]['compressed_bytes']=runs[0]['compressed_bytes']
        totals[mode]['phases']={k:statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
        coverage[mode]=dict(Counter(c['status'] for c in runs[0]['cases']));rss[mode]=max(r['peak_rss_bytes'] for r in runs)
        states[mode]=sum(c['diagnostic']['expanded'] for c in runs[0]['cases'])
    gains=[];remaining=[];union=[];details=[]
    near=s.load(s.PARENT/'near-models.json')['records']
    for row,a,b in zip(rows,reports['baseline'][0]['cases'],reports['boundary'][0]['cases']):
        assert a['status']=='unresolved' or b['status']=='sat'
        binding=s.binding(out/'boundary-0'/(str(row['id'])+'.json'))
        if a['status']=='unresolved' and b['status']=='sat':
            gains.append(row['id']);ev=evidence['boundary',row['id']];retained=next(r for r in near if r['id']==row['id'])
            snapshot=[x for x in retained['snapshots'] if x['expanded']<=p['prefix_limit']][-1]
            assert ev['seed']['values']==snapshot['values']
            details.append(dict(id=row['id'],diagnostic=b['diagnostic'],near_failed=len(snapshot['false_original']),distance_from_near=sum(x!=y for x,y in zip(ev['seed']['values'],certs['boundary',row['id']]['witness']['values'])),evidence=s.binding(out/'boundary-0/discovery.json')))
        if b['status']=='unresolved':remaining.append(row['id'])
        union.append(dict(id=row['id'],status=b['status'],certificate=binding))
    assert gains==[24,25,29] and not remaining and states==dict(baseline=118552,boundary=94762)
    s.write(out/'remaining.json',dict(records=remaining,scope='This exposed repair panel is complete; fresh transfer, full-portfolio status and unrestricted efficient coverage remain unmeasured.'))
    s.write(out/'coverage-union.json',dict(records=union,scope='32 exposed constructed cases; separate from preserved external 37/37 and synthetic 182/182.'))
    s.write(out/'gap-diagnostics.json',dict(records=details,total_conditional_exclusions=sum(s.e.check_evidence(row['source'],evidence['boundary',row['id']])['conditional_exclusions'] for row in rows)))
    analysis=dict(totals=totals,coverage=coverage,states=states,peak_rss_bytes=rss,gains=gains,remaining=remaining,comparison_percent=100*(totals['boundary']['complete_seconds']/totals['baseline']['complete_seconds']-1),paired_percent=[100*(reports['boundary'][i]['complete_seconds']/reports['baseline'][i]['complete_seconds']-1) for i in range(4)],limitations=p['limitations'])
    s.write(out/'analysis.json',analysis)
    semantic=s.load(out/'semantic-audit.json');assert semantic['passed'] and semantic['counts']['exhaustive_inputs']==512 and semantic['counts']['fresh_inputs']==64
    external=s.bound(parent['hamming_repair']['coverage-union']);external_rows=s.load('experiments/results/cnf-external-cutsets/panel.json');assert len(external['records'])==len(external_rows)==37
    for row,entry in zip(external_rows,external['records']):
        assert row['id']==entry['id'];got=s.e.previous_search.baseline.check_pipeline(row['source'],s.bound(entry['certificate']))
        assert entry['status']==('sat' if got['answer'] else 'unsat') and got['answer'] is not None
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['boundary_repair']={k:s.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis','remaining','coverage-union','semantic-audit','gap-diagnostics')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=s.bound(parent['factor_conditioning']['coverage-union']),external_union_unchanged_and_rechecked=37,seconds=time.perf_counter()-started,checkpoint=s.binding(out/'checkpoint.json')))
    print(s.encode(analysis))


def seal(out):
    v=s.load(out/'validation.json');cp=s.load(out/'checkpoint.json');assert v['passed']
    for file,h in cp['source_fingerprints'].items():assert s.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','581bd5de:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';old=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==85 and proofs[:85]==old and len(proofs)==86
    full=(out/'full-tests.log').read_text();focused=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 2546 tests in .*\n\nOK',full) and re.search(r'Ran 18 tests in .*\n\nOK',focused)
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    decision=s.load(out/'decision.json')
    for file,h in decision['documents'].items():assert s.sha(file)==h,file
    s.bound(decision['supplemental_checks']);cp['boundary_repair']['decision']=s.binding(out/'decision.json');s.write(out/'checkpoint.json',cp)
    v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    s.write(out/'checks.json',dict(passed=True,full_tests=2546,focused_tests=18,old_proof_blocks_unchanged=85,added_proof_blocks=1,prior_sources=1336,final_sources=1341,prior_manifests=245,prior_artifacts=82407,checkpoint=s.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}));print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=246,next_artifacts=82407+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
