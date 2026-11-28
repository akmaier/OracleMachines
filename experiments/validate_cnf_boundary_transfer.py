#!/usr/bin/env python3
"""Preserve lineage and reproduce frozen external transfer without retuning."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_boundary_transfer as s
from experiments.audit_cnf_boundary_transfer import portfolio,inputs


def clean(case):return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    started=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);s.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=s.sha(mp),artifacts_checked=len(s.load(mp)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert s.sha(path)==entry['sha256'],path
        for file,h in s.load(path)['artifacts'].items():assert s.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(246,82741)
    sources=p['source_fingerprints'];assert len(sources)==1346
    for file,h in sources.items():assert s.sha(file)==h,file
    selection=s.bound(p['selection']);assert selection['policy']==p['policy']==dict(node_limit=20000,prefix_limit=10000,max_rounds=8)
    rows=s.source_rows(p);descriptions=s.bound(p['descriptions']);assert len(rows)==36
    inputs(out);acquisition=s.bound(p['acquisition']);assert acquisition['selection']==p['selection'] and len(acquisition['records'])==24
    for record in acquisition['records']:assert s.sha(record['raw']['path'])==record['raw']['sha256']
    overlaps=s.bound(p['overlaps']);prior={x['path']:{s.e.previous.capacity.canonical(r['source'],Counter()) for r in s.bound(x)} for x in overlaps['prior_panels']};seen=set()
    for row,record in zip(rows,overlaps['records']):
        key=s.e.previous.capacity.canonical(row['source'],Counter());assert record['id']==row['id'] and not record['prior_matches'] and record['same_panel_exact'] is None
        assert key not in seen and all(key not in keys for keys in prior.values());seen.add(key)
    samples=s.load(out/'comparisons.json')['samples'];assert len(samples)==8 and {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(4)}
    reports={m:[] for m in s.MODES};certs={};evidence={}
    for sample in samples:
        r=s.bound(sample);mode=sample['mode'];reports[mode].append(r);dest=Path(sample['path']).parent;proofs=[];evs=s.load(dest/'discovery.json')
        assert r['panel']==p['panel'] and len(r['cases'])==len(evs)==36
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
        for row,case in zip(rows,ref['cases']):
            counts=Counter();proof,ev,diag=s.discover(row['source'],mode,counts)
            assert proof==certs[mode,row['id']] and ev==evidence[mode,row['id']] and diag==case['diagnostic'] and dict(counts)==case['discovery_counts']
            assert diag['expanded']<=20000 and diag['expanded']==diag['prefix']['expanded']+sum(d['search']['expanded'] for d in diag['rounds'])
            got=s.check(row['source'],proof,counts);s.e.check_evidence(row['source'],ev,counts)
            assert dict(counts)==case['counts'];total.update(counts)
        assert dict(total)==ref['counts']
        for key,repeats in [('warm_counts',1),('cold_counts',2)]:
            cc=Counter()
            for _ in range(repeats):
                for row in s.source_rows(p):s.check(row['source'],certs[mode,row['id']],cc);s.e.check_evidence(row['source'],evidence[mode,row['id']],cc)
            assert dict(cc)==ref[key]
    references={};reference_counts={m:Counter() for m in ('portfolio','z3')};reference_times={m:0 for m in reference_counts};byid={r['id']:r for r in rows}
    for entry in s.load(out/'references.json')['records']:
        r=s.bound(entry);references[r['mode'],r['id']]=r;source=byid[r['id']]['source'];answer=r['result']['answer']
        if r['mode']=='portfolio' and not r.get('timeout'):assert json.loads(s.encode(portfolio.check_pipeline(source,r['proof'])))==r['result']
        if r['mode']=='z3' and answer is True:assert json.loads(s.encode(s.e.previous.check(source,r['proof'])))==r['result']
        label=descriptions[r['id']]['publisher_answer']
        if answer is not None and label is not None:assert answer==label
        reference_counts[r['mode']]['unknown' if answer is None else ('sat' if answer else 'unsat')]+=1;reference_times[r['mode']]+=r['process_seconds']
    assert len(references)==72
    totals={};coverage={};rss={};states={}
    for mode,runs in reports.items():
        totals[mode]={k:statistics.mean(r[k] for r in runs) for k in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','evidence_bytes')}
        totals[mode]['compressed_bytes']=runs[0]['compressed_bytes'];totals[mode]['phases']={k:statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
        coverage[mode]={kind:dict(Counter(c['status'] for c in runs[0]['cases'] if descriptions[c['id']]['kind']==kind)) for kind in ('original','signed-permutation','edit')}
        rss[mode]=max(r['peak_rss_bytes'] for r in runs);states[mode]=sum(c['diagnostic']['expanded'] for c in runs[0]['cases'])
    gains=[];losses=[];remaining=[];union=[];details=[]
    for row,a,b in zip(rows,reports['baseline'][0]['cases'],reports['boundary'][0]['cases']):
        key=row['id'];reference=references['z3',key]['result']['answer'];full=references['portfolio',key]['result']['answer'];entry=None
        if a['status']=='unresolved' and b['status']=='sat':gains.append(key)
        if a['status']=='sat' and b['status']=='unresolved':losses.append(key)
        for mode,c in (('baseline',a),('boundary',b)):
            if c['status']=='sat':
                assert reference is not False and full is not False
                entry=dict(id=key,status='sat',authority=mode,certificate=s.binding(out/(mode+'-0')/(key+'.json')))
        if entry is None and full is not None:
            entry=dict(id=key,status='sat' if full else 'unsat',authority='portfolio',certificate=s.binding(out/'references'/(key+'-portfolio.json')))
        if entry is None:
            entry=dict(id=key,status='unresolved',authority=None,certificate=None);remaining.append(dict(**row,reference_answer=reference,boundary_diagnostic=b['diagnostic']))
        union.append(entry)
        details.append(dict(id=key,description=descriptions[key],baseline=a['status'],boundary=b['status'],portfolio=full,reference=reference,diagnostic=b['diagnostic'],near_model=evidence['boundary',key]['seed'],conditional_exclusions=s.e.check_evidence(row['source'],evidence['boundary',key])['conditional_exclusions']))
    # Validate every transported SAT reference model against its original source.
    for tr in s.bound(p['transports']):
        ref=references['z3',tr['id']]
        if ref['result']['answer'] is True:
            model=dict(zip(ref['proof']['names'],ref['proof']['values']));mapping={int(v):w for v,w in tr['mapping'].items()};names=sorted(mapping)
            w=dict(format=s.e.previous.FORMAT,names=names,values=[model[abs(mapping[v])] if mapping[v]>0 else not model[-mapping[v]] for v in names])
            assert s.e.previous.check(byid[tr['original']]['source'],w)['answer']
    s.write(out/'remaining.json',dict(records=remaining,scope='Unresolved by both repair kernels and the independently checked unchanged portfolio. Z3 truth is diagnostic; its models are not counted as structural transfer coverage.'))
    s.write(out/'coverage-union.json',dict(records=union,scope='New panel only: union of two repair policies and separately checked existing portfolio; originals and derived controls remain separately denominated.'))
    s.write(out/'gap-diagnostics.json',dict(records=details))
    analysis=dict(totals=totals,coverage=coverage,states=states,peak_rss_bytes=rss,gains=gains,losses=losses,remaining=[r['id'] for r in remaining],union_coverage=dict(Counter(r['status'] for r in union)),reference_counts={k:dict(v) for k,v in reference_counts.items()},reference_process_seconds=reference_times,comparison_percent=100*(totals['boundary']['complete_seconds']/totals['baseline']['complete_seconds']-1),paired_percent=[100*(reports['boundary'][i]['complete_seconds']/reports['baseline'][i]['complete_seconds']-1) for i in range(4)],limitations=p['limitations'])
    s.write(out/'analysis.json',analysis)
    external=s.bound(parent['hamming_repair']['coverage-union']);external_rows=s.load('experiments/results/cnf-external-cutsets/panel.json')
    for row,entry in zip(external_rows,external['records']):assert portfolio.check_pipeline(row['source'],s.bound(entry['certificate']))['answer']==(entry['status']=='sat')
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['boundary_transfer']={k:s.binding(out/(k+'.json')) for k in ('protocol','selection','acquisition','panel','descriptions','transports','overlaps','comparisons','analysis','remaining','coverage-union','gap-diagnostics','references','input-audit')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=s.bound(parent['factor_conditioning']['coverage-union']),external_union_unchanged_and_rechecked=37,constructed_union_unchanged=s.bound(parent['boundary_repair']['coverage-union']),seconds=time.perf_counter()-started,checkpoint=s.binding(out/'checkpoint.json')))
    print(s.encode(analysis))


def seal(out):
    v=s.load(out/'validation.json');cp=s.load(out/'checkpoint.json');assert v['passed']
    for file,h in cp['source_fingerprints'].items():assert s.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','5436e7c4:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';old=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==86 and proofs==old
    assert re.search(r'Ran 2552 tests in .*\n\nOK',(out/'full-tests.log').read_text())
    assert re.search(r'Ran 6 tests in .*\n\nOK',(out/'focused-tests.log').read_text())
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    decision=s.load(out/'decision.json')
    for file,h in decision['documents'].items():assert s.sha(file)==h,file
    s.bound(decision['supplemental_checks']);cp['boundary_transfer']['decision']=s.binding(out/'decision.json');s.write(out/'checkpoint.json',cp)
    v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    s.write(out/'checks.json',dict(passed=True,full_tests=2552,focused_tests=6,old_proof_blocks_unchanged=86,added_proof_blocks=0,prior_sources=1341,final_sources=1346,prior_manifests=246,prior_artifacts=82741,checkpoint=s.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}));print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=247,next_artifacts=82741+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
