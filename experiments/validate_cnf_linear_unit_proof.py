#!/usr/bin/env python3
"""Reproduce proof equivalence, larger transfer and immutable lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,hashlib,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_linear_unit_proof as s
from experiments import cnf_hamming_repair as portfolio
from experiments.cnf_external_cutsets import parse_dimacs


def clean(case):return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def panel(out,repeats,old=None):
    p=s.load(out/'protocol.json');rows=s.source_rows(p);descriptions=s.bound(p['descriptions']);samples=s.load(out/'comparisons.json')['samples']
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(repeats)}
    reports={m:[] for m in s.MODES};certs={}
    for sample in samples:
        r=s.bound(sample);mode=sample['mode'];reports[mode].append(r);dest=Path(sample['path']).parent;proofs=[];evs=s.load(dest/'discovery.json')
        assert r['panel']==p['panel'] and len(r['cases'])==len(evs)==len(rows) and all(e is None for e in evs)
        for row,case in zip(rows,r['cases']):
            assert row['id']==case['id'];proof=s.load(dest/(row['id']+'.json'));proofs.append(proof);got=s.check(row['source'],proof)
            assert json.loads(s.encode(got))==case['result']
            assert case['status']==('unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'))
            if sample['repeat']==0:certs[mode,row['id']]=proof
        for name,data in (('certificates',proofs),('discovery',evs),('combined',dict(proofs=proofs,evidence=evs))):
            assert json.loads(gzip.decompress((dest/(name+'.json.gz')).read_bytes()))==data
            assert r['compressed_bytes'][name]==(dest/(name+'.json.gz')).stat().st_size
        assert r['proof_bytes']==sum((dest/(row['id']+'.json')).stat().st_size for row in rows)
        assert r['evidence_bytes']==(dest/'discovery.json').stat().st_size
    for mode,runs in reports.items():
        ref=runs[0]
        for r in runs:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','evidence_bytes','compressed_bytes'):assert r[key]==ref[key]
            assert list(map(clean,r['cases']))==list(map(clean,ref['cases']))
        total=Counter()
        for j,(row,case) in enumerate(zip(rows,ref['cases'])):
            counts=Counter();proof,ev,diag=s.discover(row['source'],mode,counts)
            assert proof==certs[mode,row['id']] and ev is None and diag==case['diagnostic'] and dict(counts)==case['discovery_counts']
            assert diag['expanded']<=20000
            if old is not None and mode=='explicit':
                assert diag==old[j]['diagnostic'] and dict(counts)==old[j]['discovery_counts'] and case['result']==old[j]['result']
                assert proof['proof']==s.load(s.PARENT/'propagated-0'/(row['id']+'.json'))['proof']
            s.check(row['source'],proof,counts);assert dict(counts)==case['counts'];total.update(counts)
        assert dict(total)==ref['counts']
        for key,n in [('warm_counts',1),('cold_counts',2)]:
            counts=Counter()
            for _ in range(n):
                for row in s.source_rows(p):s.check(row['source'],certs[mode,row['id']],counts)
            assert dict(counts)==ref[key]
    for row,a,b in zip(rows,reports['explicit'][0]['cases'],reports['linear'][0]['cases']):
        assert a['result']==b['result'] and a['diagnostic']==b['diagnostic']
        if a['status']=='unsat':assert s.e.pack(row['source'],certs['explicit',row['id']]['proof']['certificate'])==certs['linear',row['id']]['proof']['certificate']
    totals={};coverage={};rss={};states={}
    for mode,runs in reports.items():
        totals[mode]={k:statistics.mean(r[k] for r in runs) for k in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','evidence_bytes')}
        totals[mode]['compressed_bytes']=runs[0]['compressed_bytes'];totals[mode]['phases']={k:statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
        coverage[mode]={kind:dict(Counter(c['status'] for c in runs[0]['cases'] if descriptions[c['id']]['kind']==kind)) for kind in ('original','signed-permutation','edit')}
        rss[mode]=max(r['peak_rss_bytes'] for r in runs);states[mode]=sum(c['diagnostic']['expanded'] for c in runs[0]['cases'])
    return dict(totals=totals,coverage=coverage,states=states,peak_rss_bytes=rss,comparison_percent=100*(totals['linear']['complete_seconds']/totals['explicit']['complete_seconds']-1),paired_percent=[100*(reports['linear'][i]['complete_seconds']/reports['explicit'][i]['complete_seconds']-1) for i in range(repeats)]),reports,certs


def validate(out):
    started=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);s.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=s.sha(mp),artifacts_checked=len(s.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert s.sha(path)==entry['sha256']
        for file,h in s.load(path)['artifacts'].items():assert s.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(248,83640)
    sources=p['source_fingerprints'];assert len(sources)==1357
    for file,h in sources.items():assert s.sha(file)==h,file
    a,reports,certs=panel(out,4,s.bound(p['baseline_records'])['cases']);assert a['states']==dict(explicit=58118,linear=58118)
    larger=out/'larger';lp=s.bound(p['larger_protocol']);b,lr,lc=panel(larger,1);rows=s.source_rows(lp);desc=s.bound(lp['descriptions']);byid={r['id']:r for r in rows}
    selection=s.bound(lp['selection'])
    for file,h in selection['policy_files'].items():assert s.sha(file)==h,file
    for row in rows:
        d=desc[row['id']]
        if d['kind']=='original':
            assert d['index'] in selection['indices'];raw=gzip.decompress(Path(d['original_gzip']['path']).read_bytes())
            assert s.sha(d['original_gzip']['path'])==d['original_gzip']['sha256'] and len(raw)==d['original_member_bytes'] and hashlib.sha256(raw).hexdigest()==d['original_member_sha256']
            assert parse_dimacs(raw.decode())[0]==row['source']
        elif d['kind']=='edit':
            expected=[c[:] for c in byid[d['original']]['source'][1:]];next(c for c in reversed(expected) if c)[0]*=-1
            assert expected==row['source'] and d['publisher_answer'] is None
    for t in s.bound(lp['transports']):
        original=byid[t['original']]['source'];mapping={int(v):w for v,w in t['mapping'].items()};assert set(mapping)=={abs(v) for c in original for v in c} and len(set(map(abs,mapping.values())))==len(mapping)
        assert [[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in reversed(original)]==byid[t['id']]['source']
    overlap=s.load(larger/'overlaps.json')
    canonical=s.e.prior.prior.previous.capacity.canonical;prior_sets=[{canonical(r['source'],Counter()) for r in s.bound(x)} for x in overlap['prior_panels']];seen=set()
    for row in rows:
        k=canonical(row['source'],Counter());assert k not in seen and all(k not in keys for keys in prior_sets);seen.add(k)
    refs=s.load(larger/'references.json')['records'];reference={};refcounts={m:Counter() for m in ('portfolio','z3')}
    for entry in refs:
        r=s.bound(entry);source=byid[r['id']]['source'];answer=r['result']['answer'];reference[r['id'],r['mode']]=r
        if r['mode']=='portfolio' and not r.get('timeout'):assert json.loads(s.encode(portfolio.check_pipeline(source,r['proof'])))==r['result']
        if r['mode']=='z3' and answer is True:s.e.prior.prior.previous.check(source,r['proof'])
        label=desc[r['id']]['publisher_answer']
        if label is not None and answer is not None:assert label==answer
        refcounts[r['mode']]['unknown' if answer is None else ('sat' if answer else 'unsat')]+=1
    assert len(reference)==32
    gaps=[];union=[]
    for row,case in zip(rows,lr['linear'][0]['cases']):
        z=reference[row['id'],'z3'];po=reference[row['id'],'portfolio'];answer=case['result']['answer']
        if answer is not None and z['result']['answer'] is not None:assert answer==z['result']['answer']
        if answer is not None and po['result']['answer'] is not None:assert answer==po['result']['answer']
        winner=answer if answer is not None else po['result']['answer'];status='unresolved' if winner is None else ('sat' if winner else 'unsat')
        union.append(dict(id=row['id'],status=status,certificate=s.binding(larger/'linear-0'/(row['id']+'.json')) if answer is not None else (s.binding(larger/'references'/(row['id']+'-portfolio.json')) if winner is not None else None),engine='linear' if answer is not None else 'portfolio'))
        if winner is None:
            names={abs(v) for c in row['source'] for v in c};parent_map={v:v for v in names}
            def root(v):
                while parent_map[v]!=v:v=parent_map[v]
                return v
            for c in row['source']:
                for lit in c[1:]:parent_map[root(abs(lit))]=root(abs(c[0]))
            gaps.append(dict(id=row['id'],reference_answer=z['result']['answer'],diagnostic=case['diagnostic'],variables=len(names),clauses=len(row['source']),component_sizes=sorted(Counter(root(v) for v in names).values()),kind=desc[row['id']]['kind']))
    b['reference_counts']={m:dict(c) for m,c in refcounts.items()};b['union_counts']=dict(Counter(r['status'] for r in union));b['unresolved']=gaps
    s.write(larger/'coverage-union.json',dict(records=union,scope='New 8 originals and 8 related controls only. Z3 models are audited reference outputs, not structural coverage.'))
    s.write(larger/'remaining.json',dict(records=gaps))
    s.write(out/'analysis.json',dict(exposed=a,larger=b,limitations=p['limitations']))
    semantic=s.load(out/'semantic-audit.json');assert semantic==s.load(out/'semantic-audit-reproduced.json') and semantic['passed'] and semantic['counts']['queries']==8882
    external=s.bound(parent['hamming_repair']['coverage-union'])
    for row,entry in zip(s.load('experiments/results/cnf-external-cutsets/panel.json'),external['records']):assert portfolio.check_pipeline(row['source'],s.bound(entry['certificate']))['answer']==(entry['status']=='sat')
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['linear_unit_proof']={k:s.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis','semantic-audit')}
    cp['linear_unit_proof'].update({k:s.binding(larger/(k+'.json')) for k in ('coverage-union','remaining','references','acquisition','overlaps')})
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=s.bound(parent['factor_conditioning']['coverage-union']),external_union_unchanged_and_rechecked=37,constructed_union_unchanged=s.bound(parent['boundary_repair']['coverage-union']),seconds=time.perf_counter()-started,checkpoint=s.binding(out/'checkpoint.json')))
    print(s.encode(dict(exposed=a,larger=b)))


def seal(out):
    v=s.load(out/'validation.json');cp=s.load(out/'checkpoint.json');assert v['passed']
    for file,h in cp['source_fingerprints'].items():assert s.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','317c4632:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';old=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==87 and proofs[:87]==old and len(proofs)==88
    assert re.search(r'Ran 2592 tests in .*\n\nOK',(out/'full-tests.log').read_text())
    assert re.search(r'Ran 20 tests in .*\n\nOK',(out/'focused-tests.log').read_text())
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    decision=s.load(out/'decision.json')
    for file,h in decision['documents'].items():assert s.sha(file)==h,file
    s.bound(decision['supplemental_checks']);cp['linear_unit_proof']['decision']=s.binding(out/'decision.json');s.write(out/'checkpoint.json',cp)
    v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    s.write(out/'checks.json',dict(passed=True,full_tests=2592,focused_tests=20,old_proof_blocks_unchanged=87,added_proof_blocks=1,prior_sources=1351,final_sources=1357,prior_manifests=248,prior_artifacts=83640,checkpoint=s.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}));print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=249,next_artifacts=83640+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
