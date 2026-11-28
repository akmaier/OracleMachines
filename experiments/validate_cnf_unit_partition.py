#!/usr/bin/env python3
"""Reproduce unit propagation, complete certificates and preserved evidence."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,hashlib,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_unit_partition as s
from experiments import cnf_hamming_repair as portfolio


def clean(case):return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    started=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);s.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=s.sha(mp),artifacts_checked=len(s.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert s.sha(path)==entry['sha256'],path
        for file,h in s.load(path)['artifacts'].items():assert s.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(247,83273)
    sources=p['source_fingerprints'];assert len(sources)==1351
    for file,h in sources.items():assert s.sha(file)==h,file
    assert s.sha(p['baseline_script']['path'])==p['baseline_script']['sha256']
    rows=s.source_rows(p);descriptions=s.bound(p['descriptions']);old=s.bound(p['baseline_records'])['cases'];assert len(rows)==len(old)==36
    samples=s.load(out/'comparisons.json')['samples'];assert len(samples)==8 and {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(4)}
    reports={m:[] for m in s.MODES};certs={};evidence={}
    for sample in samples:
        r=s.bound(sample);mode=sample['mode'];reports[mode].append(r);dest=Path(sample['path']).parent;proofs=[];evs=s.load(dest/'discovery.json')
        assert r['panel']==p['panel'] and len(r['cases'])==len(evs)==36
        for row,case,ev in zip(rows,r['cases'],evs):
            assert row['id']==case['id'];proof=s.load(dest/(row['id']+'.json'));proofs.append(proof)
            got=s.check(row['source'],proof);s.check_evidence(row['source'],ev)
            assert json.loads(s.encode(got))==case['result'];assert case['status']==('unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'))
            if sample['repeat']==0:certs[mode,row['id']]=proof;evidence[mode,row['id']]=ev
        for name,data in (('certificates',proofs),('discovery',evs),('combined',dict(proofs=proofs,evidence=evs))):
            assert json.loads(gzip.decompress((dest/(name+'.json.gz')).read_bytes()))==data
            assert r['compressed_bytes'][name]==(dest/(name+'.json.gz')).stat().st_size
        assert r['proof_bytes']==sum((dest/(row['id']+'.json')).stat().st_size for row in rows)
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
            assert diag['total_states' if mode=='baseline' else 'expanded']<=p['node_limit']
            if mode=='baseline':
                assert diag==prior['diagnostic'] and dict(counts)==prior['discovery_counts']
                assert proof['proof']==s.load(s.PARENT/'root-export'/(row['id']+'.json'))
            got=s.check(row['source'],proof,counts);s.check_evidence(row['source'],ev,counts)
            assert dict(counts)==case['counts'];total.update(counts)
            reference=s.load(s.PARENT/'references'/(row['id']+'-z3.json'))['result']['answer']
            if got['answer'] is not None:assert got['answer']==reference
        assert dict(total)==ref['counts']
        for key,repeats in [('warm_counts',1),('cold_counts',2)]:
            cc=Counter()
            for _ in range(repeats):
                for row in s.source_rows(p):s.check(row['source'],certs[mode,row['id']],cc);s.check_evidence(row['source'],evidence[mode,row['id']],cc)
            assert dict(cc)==ref[key]
    totals={};coverage={};rss={};states={}
    for mode,runs in reports.items():
        totals[mode]={k:statistics.mean(r[k] for r in runs) for k in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','evidence_bytes')}
        totals[mode]['compressed_bytes']=runs[0]['compressed_bytes'];totals[mode]['phases']={k:statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
        coverage[mode]={kind:dict(Counter(c['status'] for c in runs[0]['cases'] if descriptions[c['id']]['kind']==kind)) for kind in ('original','signed-permutation','edit')}
        rss[mode]=max(r['peak_rss_bytes'] for r in runs);states[mode]=sum(c['diagnostic']['total_states' if mode=='baseline' else 'expanded'] for c in runs[0]['cases'])
    gains=[];remaining=[];union=[];details=[];prior_union=s.bound(p['previous_union'])['records']
    for row,a,b,previous in zip(rows,reports['baseline'][0]['cases'],reports['propagated'][0]['cases'],prior_union):
        assert row['id']==previous['id'];assert a['status']=='unresolved' or a['status']==b['status']
        if a['status']=='unresolved' and b['status']!='unresolved':gains.append(row['id'])
        if b['status']=='unresolved':remaining.append(row['id'])
        union.append(dict(id=row['id'],status=b['status'],certificate=s.binding(out/'propagated-0'/(row['id']+'.json'))))
        proof=certs['propagated',row['id']]['proof']
        details.append(dict(id=row['id'],status=b['status'],prior_union=previous['status'],diagnostic=b['diagnostic'],unit_forced_keeps=b['discovery_counts'].get('unit_forced_keeps',0),unit_forced_flips=b['discovery_counts'].get('unit_forced_flips',0),refutation_contexts=len(proof['certificate']['nodes']) if proof['kind']=='unsat' else 0))
    assert not remaining and len(gains)==18 and sum(d['prior_union']=='unresolved' for d in details)==14
    s.write(out/'remaining.json',dict(records=remaining,scope='Exposed 36-input panel complete under the new search; fresh transfer and unrestricted efficient coverage remain open.'))
    s.write(out/'coverage-union.json',dict(records=union,scope='This panel alone: 24 originals plus 12 related controls. Prior external, constructed and synthetic unions remain separate.'))
    s.write(out/'gap-diagnostics.json',dict(records=details,prior_union_gains=[d['id'] for d in details if d['prior_union']=='unresolved']))
    analysis=dict(totals=totals,coverage=coverage,states=states,peak_rss_bytes=rss,gains=gains,remaining=remaining,prior_union_gains=14,comparison_percent=100*(totals['propagated']['complete_seconds']/totals['baseline']['complete_seconds']-1),paired_percent=[100*(reports['propagated'][i]['complete_seconds']/reports['baseline'][i]['complete_seconds']-1) for i in range(4)],limitations=p['limitations'])
    s.write(out/'analysis.json',analysis)
    semantic=s.load(out/'semantic-audit-final.json');assert semantic['passed'] and semantic['counts']['two_inputs']==512 and semantic['counts']['fresh_inputs']==128 and len(semantic['constructed'])==32
    old_probe=s.load(out/'exploration.json');raw=gzip.decompress((out/'exploratory-core.py.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==old_probe['source']['sha256']
    external=s.bound(parent['hamming_repair']['coverage-union']);external_rows=s.load('experiments/results/cnf-external-cutsets/panel.json')
    for row,entry in zip(external_rows,external['records']):assert portfolio.check_pipeline(row['source'],s.bound(entry['certificate']))['answer']==(entry['status']=='sat')
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['unit_partition']={k:s.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis','remaining','coverage-union','gap-diagnostics','semantic-audit-final')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=s.bound(parent['factor_conditioning']['coverage-union']),external_union_unchanged_and_rechecked=37,constructed_union_unchanged=s.bound(parent['boundary_repair']['coverage-union']),seconds=time.perf_counter()-started,checkpoint=s.binding(out/'checkpoint.json')))
    print(s.encode(analysis))


def seal(out):
    v=s.load(out/'validation.json');cp=s.load(out/'checkpoint.json');assert v['passed']
    for file,h in cp['source_fingerprints'].items():assert s.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','db9c7862:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';old=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==86 and proofs[:86]==old and len(proofs)==87
    assert re.search(r'Ran 2572 tests in .*\n\nOK',(out/'full-tests.log').read_text())
    assert re.search(r'Ran 20 tests in .*\n\nOK',(out/'focused-tests.log').read_text())
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    decision=s.load(out/'decision.json')
    for file,h in decision['documents'].items():assert s.sha(file)==h,file
    s.bound(decision['supplemental_checks']);cp['unit_partition']['decision']=s.binding(out/'decision.json');s.write(out/'checkpoint.json',cp)
    v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    s.write(out/'checks.json',dict(passed=True,full_tests=2572,focused_tests=20,old_proof_blocks_unchanged=86,added_proof_blocks=1,prior_sources=1346,final_sources=1351,prior_manifests=247,prior_artifacts=83273,checkpoint=s.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}));print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=248,next_artifacts=83273+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
