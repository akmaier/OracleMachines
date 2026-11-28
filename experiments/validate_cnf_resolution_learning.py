#!/usr/bin/env python3
"""Reproduce learned knowledge, guarded reuse, costs and immutable lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import gzip,hashlib,json,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_resolution_learning as s
from experiments import cnf_hamming_repair as portfolio


def clean(case):return {k:v for k,v in case.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    started=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);s.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=s.sha(mp),artifacts_checked=len(s.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert s.sha(path)==entry['sha256']
        for file,h in s.load(path)['artifacts'].items():assert s.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(249,84115)
    sources=p['source_fingerprints'];assert len(sources)==1362
    for file,h in sources.items():assert s.sha(file)==h,file
    rows=s.source_rows(p);desc=s.bound(p['descriptions']);old=s.bound(p['baseline_records'])['cases'];samples=s.load(out/'comparisons.json')['samples']
    assert len(samples)==4 and {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(2)}
    reports={m:[] for m in s.MODES};certs={}
    for sample in samples:
        r=s.bound(sample);mode=sample['mode'];reports[mode].append(r);dest=Path(sample['path']).parent;proofs=[];evs=s.load(dest/'discovery.json')
        assert r['panel']==p['panel'] and len(r['cases'])==len(rows)==len(evs)==16 and all(x is None for x in evs)
        for row,case in zip(rows,r['cases']):
            assert row['id']==case['id'];proof=s.load(dest/(row['id']+'.json'));proofs.append(proof);got=s.check(row['source'],proof)
            assert json.loads(s.encode(got))==case['result'] and case['status']==('unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'))
            if sample['repeat']==0:certs[mode,row['id']]=proof
        for name,data in (('certificates',proofs),('discovery',evs),('combined',dict(proofs=proofs,evidence=evs))):
            assert json.loads(gzip.decompress((dest/(name+'.json.gz')).read_bytes()))==data and r['compressed_bytes'][name]==(dest/(name+'.json.gz')).stat().st_size
        assert r['proof_bytes']==sum((dest/(row['id']+'.json')).stat().st_size for row in rows) and r['evidence_bytes']==(dest/'discovery.json').stat().st_size
    for mode,runs in reports.items():
        ref=runs[0]
        for r in runs:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','evidence_bytes','compressed_bytes'):assert r[key]==ref[key]
            assert list(map(clean,r['cases']))==list(map(clean,ref['cases']))
        total=Counter()
        for row,case,previous in zip(rows,ref['cases'],old):
            counts=Counter();proof,ev,diag=s.discover(row['source'],mode,counts)
            assert proof==certs[mode,row['id']] and ev is None and diag==case['diagnostic'] and dict(counts)==case['discovery_counts'] and diag['expanded']<=20000
            if mode=='baseline':
                assert diag==previous['diagnostic'] and dict(counts)==previous['discovery_counts'] and case['result']==previous['result']
                assert proof['proof']==s.load(s.PARENT/'larger/linear-0'/(row['id']+'.json'))['proof']
            got=s.check(row['source'],proof,counts);assert dict(counts)==case['counts'];total.update(counts)
            z=s.load(s.PARENT/'larger/references'/(row['id']+'-z3.json'))['result']['answer']
            if got['answer'] is not None:assert got['answer']==z
        assert dict(total)==ref['counts']
        for key,n in [('warm_counts',1),('cold_counts',2)]:
            counts=Counter()
            for _ in range(n):
                for row in s.source_rows(p):s.check(row['source'],certs[mode,row['id']],counts)
            assert dict(counts)==ref[key]
    totals={};coverage={};rss={};states={}
    for mode,runs in reports.items():
        totals[mode]={k:statistics.mean(r[k] for r in runs) for k in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes','evidence_bytes')}
        totals[mode]['compressed_bytes']=runs[0]['compressed_bytes'];totals[mode]['phases']={k:statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
        coverage[mode]={kind:dict(Counter(c['status'] for c in runs[0]['cases'] if desc[c['id']]['kind']==kind)) for kind in ('original','signed-permutation','edit')}
        rss[mode]=max(r['peak_rss_bytes'] for r in runs);states[mode]=sum(c['diagnostic']['expanded'] for c in runs[0]['cases'])
    union=[];gains=[];remaining=[];knowledge=[];transport=[]
    for row,a,b in zip(rows,reports['baseline'][0]['cases'],reports['learning'][0]['cases']):
        assert a['status']=='unresolved' or b['status'] in (a['status'],'unresolved')
        answer=b['result']['answer'] if b['result']['answer'] is not None else a['result']['answer'];status='unresolved' if answer is None else ('sat' if answer else 'unsat')
        engine='learning' if b['result']['answer'] is not None else 'baseline'
        union.append(dict(id=row['id'],status=status,certificate=s.binding(out/(engine+'-0')/(row['id']+'.json')) if answer is not None else None))
        if a['status']=='unresolved' and b['status']!='unresolved':gains.append(row['id'])
        if status=='unresolved':remaining.append(dict(id=row['id'],reference_answer=s.load(s.PARENT/'larger/references'/(row['id']+'-z3.json'))['result']['answer'],diagnostic=b['diagnostic']))
        proof=certs['learning',row['id']]['proof'];widths=[len(x[2]) for x in proof['derivations']];c=b['discovery_counts']
        knowledge.append(dict(id=row['id'],status=b['status'],learned=len(widths),width_min=min(widths,default=0),width_median=statistics.median(widths) if widths else 0,width_max=max(widths,default=0),source_variables=len({abs(v) for clause in row['source'] for v in clause}),resolution_steps=c.get('learning_resolution_steps',0),learned_propagations=c.get('learned_clause_propagations',0),learned_conflicts=c.get('learned_clause_conflicts',0),nonchronological_jumps=c.get('learning_nonchronological_jumps',0)))
        names=sorted({abs(v) for clause in row['source'] for v in clause});fresh=names[-1]+101;target=row['source']+[[names[0],fresh],[-fresh]];tc=Counter();begin=time.perf_counter()
        with patch.object(s.e,'solve',side_effect=AssertionError),patch.object(s.e,'search',side_effect=AssertionError):moved=s.e.transport_knowledge(row['source'],proof,target,tc)
        seconds=time.perf_counter()-begin;got=s.e.check_result(target,moved)
        assert got['answer'] is False if proof['kind']=='unsat' else got['answer'] is None
        source_clauses=list(s.e.prior.prior.previous.capacity.canonical(row['source'],Counter()))
        if proof['derivations']:
            deleted=proof['derivations'][0][0];assert deleted<len(source_clauses);changed=[list(c) for i,c in enumerate(source_clauses) if i!=deleted]
            try:s.e.transport_knowledge(row['source'],proof,changed)
            except ValueError:rejected=True
            else:raise AssertionError('Missing source guard accepted')
        else:rejected=None
        item=dict(id=row['id'],source_binding=row['raw'],target=target,proof=moved,counts=dict(tc),seconds=seconds,deleted_guard_rejected=rejected)
        s.write(out/'transport'/(row['id']+'.json'),item);transport.append(dict(**s.binding(out/'transport'/(row['id']+'.json')),id=row['id'],kind=moved['kind'],seconds=seconds,guards=tc.get('knowledge_distinct_source_guards',0),guard_hits=tc.get('knowledge_guard_hits',0)))
    s.write(out/'coverage-union.json',dict(records=union,scope='Exposed 8 larger originals plus 8 related controls only; older completed panels remain separate.'))
    s.write(out/'remaining.json',dict(records=remaining));s.write(out/'knowledge.json',dict(records=knowledge));s.write(out/'transport.json',dict(records=transport,scope='Source plus a shared-variable binary bridge and a fresh negative unit; no fresh search, no SAT authority transported. Separate from matched workflow costs.'))
    analysis=dict(totals=totals,coverage=coverage,states=states,peak_rss_bytes=rss,gains=gains,remaining=remaining,union_counts=dict(Counter(x['status'] for x in union)),comparison_percent=100*(totals['learning']['complete_seconds']/totals['baseline']['complete_seconds']-1),paired_percent=[100*(reports['learning'][i]['complete_seconds']/reports['baseline'][i]['complete_seconds']-1) for i in range(2)],limitations=p['limitations'])
    s.write(out/'analysis.json',analysis)
    semantic=s.load(out/'semantic-audit-final.json');assert semantic==s.load(out/'semantic-audit-reproduced.json') and semantic['passed'] and semantic['counts']['queries']==8882
    external=s.bound(parent['hamming_repair']['coverage-union'])
    for row,entry in zip(s.load('experiments/results/cnf-external-cutsets/panel.json'),external['records']):assert portfolio.check_pipeline(row['source'],s.bound(entry['certificate']))['answer']==(entry['status']=='sat')
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources)
    cp['resolution_learning']={k:s.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis','coverage-union','remaining','knowledge','transport','semantic-audit-final')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,parent_native_archives_unchanged=True,prior_structural_union_unchanged=s.bound(parent['factor_conditioning']['coverage-union']),external_union_unchanged_and_rechecked=37,constructed_union_unchanged=s.bound(parent['boundary_repair']['coverage-union']),seconds=time.perf_counter()-started,checkpoint=s.binding(out/'checkpoint.json')))
    print(s.encode(analysis))


def seal(out):
    v=s.load(out/'validation.json');cp=s.load(out/'checkpoint.json');assert v['passed']
    for file,h in cp['source_fingerprints'].items():assert s.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','e67557c1:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';old=re.findall(pattern,before,re.S);proofs=re.findall(pattern,Path(paper).read_text(),re.S)
    assert len(old)==88 and proofs[:88]==old and len(proofs)==89
    assert re.search(r'Ran 2618 tests in .*\n\nOK',(out/'full-tests.log').read_text())
    assert re.search(r'Ran 26 tests in .*\n\nOK',(out/'focused-tests.log').read_text())
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    decision=s.load(out/'decision.json')
    for file,h in decision['documents'].items():assert s.sha(file)==h,file
    s.bound(decision['supplemental_checks']);cp['resolution_learning']['decision']=s.binding(out/'decision.json');s.write(out/'checkpoint.json',cp)
    v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    s.write(out/'checks.json',dict(passed=True,full_tests=2618,focused_tests=26,old_proof_blocks_unchanged=88,added_proof_blocks=1,prior_sources=1357,final_sources=1362,prior_manifests=249,prior_artifacts=84115,checkpoint=s.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}));print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=250,next_artifacts=84115+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
