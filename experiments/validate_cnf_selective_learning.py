#!/usr/bin/env python3
"""Reproduce edited-input expansion, proof survival, replay and immutable lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,statistics,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_selective_learning as s
from experiments import audit_cnf_selective_learning as audit


def clean(c):return {k:v for k,v in c.items() if k not in ('acquisition_seconds','checking_seconds')}


def validate(out):
    start=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json');manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);s.bound(p['parent_manifest']);manifests[str(mp)]=dict(sha256=s.sha(mp),artifacts_checked=len(s.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert s.sha(path)==entry['sha256']
        for file,h in s.load(path)['artifacts'].items():assert s.sha(file)==h,file;artifacts+=1
    assert (len(manifests),artifacts)==(250,84291)
    sources=p['source_fingerprints'];assert len(sources)==1367
    for file,h in sources.items():assert s.sha(file)==h,file
    rows=s.source_rows(p);assert len(rows)==32;selected=[r for r in rows if r['expansion_case']];assert len(selected)==16
    refs={r['id']:s.bound(r) for r in s.load(out/'references.json')['records']}
    for row in rows:
        old,proof=s.parent_data(row,Counter());base=s.e.canonical(old,Counter());deleted=proof['derivations'][0][0];assert row['deleted_index']==deleted
        expected=[list(c) for i,c in enumerate(base) if i!=deleted];names=sorted({abs(v) for c in old for v in c})
        if row['kind']=='bridge':expected += [[names[0],names[-1]+101],[-(names[-1]+101)]]
        assert row['source']==expected and row['expansion_case']==(proof['kind']=='unsat')
        if refs[row['id']]['proof']:s.e.prior.prior.prior.previous.check(row['source'],refs[row['id']]['proof'])
    samples=s.load(out/'comparisons.json')['samples'];assert len(samples)==4 and {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(2)}
    reports={m:[] for m in s.MODES};proofs={}
    for sample in samples:
        report=s.bound(sample);mode=sample['mode'];reports[mode].append(report);dest=Path(sample['path']).parent;certs=[]
        assert report['panel']==p['panel'] and len(report['cases'])==16
        for row,case in zip(selected,report['cases']):
            assert row['id']==case['id'];proof=s.load(dest/(row['id']+'.json'));certs.append(proof);got=s.check(row['source'],proof);assert s.encode(got)==s.encode(case['result'])
            assert case['status']==('unresolved' if got['answer'] is None else ('sat' if got['answer'] else 'unsat'))
            if got['answer'] is not None:assert got['answer']==refs[row['id']]['result']['answer']
            if sample['repeat']==0:proofs[mode,row['id']]=proof
        # Decode using the standard JSON parser; compression is evidence, not authority.
        import json
        for name,data in (('certificates',certs),('discovery',[None]*16),('combined',dict(proofs=certs,evidence=[None]*16))):
            assert json.loads(gzip.decompress((dest/(name+'.json.gz')).read_bytes()))==data
            assert report['compressed_bytes'][name]==(dest/(name+'.json.gz')).stat().st_size
        assert report['proof_bytes']==sum((dest/(r['id']+'.json')).stat().st_size for r in selected)
    for mode,runs in reports.items():
        ref=runs[0]
        for report in runs:
            for key in ('counts','warm_counts','cold_counts','proof_bytes','compressed_bytes'):assert ref[key]==report[key]
            assert list(map(clean,ref['cases']))==list(map(clean,report['cases']))
        total=Counter()
        for row,case in zip(selected,ref['cases']):
            counts=Counter();proof,diag=s.discover(row,mode,counts);assert proof==proofs[mode,row['id']] and diag==case['diagnostic'] and dict(counts)==case['discovery_counts']
            expanded=diag['expanded'] if mode=='fresh' else diag['expansion']['expanded'];assert expanded<=s.LIMIT
            s.check(row['source'],proof,counts);assert dict(counts)==case['counts'];total.update(counts)
        assert dict(total)==ref['counts']
        for key,repeats in (('warm_counts',1),('cold_counts',2)):
            counts=Counter()
            for _ in range(repeats):
                for row in selected:s.check(row['source'],proofs[mode,row['id']],counts)
            assert dict(counts)==ref[key]
    trans=s.load(out/'transport.json')['records'];assert len(trans)==32
    for row,entry in zip(rows,trans):
        item=s.bound(entry);assert row['id']==entry['id'] and item['whole_guard_rejected'];old,proof=s.parent_data(row,Counter())
        expected=audit.expected_survival(old,proof,row['source']);assert item['survival']['retained_indices']==expected
        assert len(expected)==entry['retained'] and len(proof['derivations'])==entry['original'] and entry['discarded']+entry['retained']==entry['original']
        got=s.check(row['source'],item['proof']);assert got['answer'] in (False,None)
        if got['answer'] is False:assert refs[row['id']]['result']['answer'] is False
    totals={};coverage={};states={};rss={}
    for mode,runs in reports.items():
        totals[mode]={k:statistics.mean(r[k] for r in runs) for k in ('complete_seconds','input_seconds','warm_seconds','cold_seconds','persistence_seconds','proof_bytes')}
        totals[mode]['compressed_bytes']=runs[0]['compressed_bytes'];totals[mode]['phases']={k:statistics.mean(r['phases'][k] for r in runs) for k in runs[0]['phases']}
        coverage[mode]=dict(Counter(c['status'] for c in runs[0]['cases']));states[mode]=sum((c['diagnostic'] if mode=='fresh' else c['diagnostic']['expansion'])['expanded'] for c in runs[0]['cases']);rss[mode]=max(r['peak_rss_bytes'] for r in runs)
    union=[];gains=[];losses=[];remaining=[]
    for row,a,b in zip(selected,reports['fresh'][0]['cases'],reports['reuse'][0]['cases']):
        if a['status']=='unresolved' and b['status']!='unresolved':gains.append(row['id'])
        if a['status']!='unresolved' and b['status']=='unresolved':losses.append(row['id'])
        mode='reuse' if b['status']!='unresolved' else 'fresh';case=b if mode=='reuse' else a
        union.append(dict(id=row['id'],status=case['status'],certificate=s.binding(out/(mode+'-0')/(row['id']+'.json'))))
        if case['status']=='unresolved':remaining.append(dict(id=row['id'],kind=row['kind'],parent=row['parent_id'],reference_answer=refs[row['id']]['result']['answer'],retained=next(x['retained'] for x in trans if x['id']==row['id']),diagnostic=case['diagnostic']))
    analysis=dict(coverage=coverage,union_counts=dict(Counter(r['status'] for r in union)),gains=gains,losses=losses,remaining=remaining,totals=totals,states=states,peak_rss_bytes=rss,comparison_percent=100*(totals['reuse']['complete_seconds']/totals['fresh']['complete_seconds']-1),paired_percent=[100*(reports['reuse'][i]['complete_seconds']/reports['fresh'][i]['complete_seconds']-1) for i in range(2)],transport=dict(cases=32,whole_guard_rejected=32,nonempty=sum(x['retained']>0 for x in trans),original=sum(x['original'] for x in trans),retained=sum(x['retained'] for x in trans),retained_min=min(x['retained'] for x in trans),retained_max=max(x['retained'] for x in trans),statuses=dict(Counter(x['status'] for x in trans))),reference_counts=dict(Counter('unknown' if x['result']['answer'] is None else ('sat' if x['result']['answer'] else 'unsat') for x in refs.values())),historical_parent_workflow=s.binding(s.PARENT/'analysis.json'),limitations=p['limitations'])
    for name,data in [('analysis',analysis),('coverage-union',dict(records=union,scope='16 edited targets from previously refuted parents; old panels remain separate.')),('remaining',dict(records=remaining))]:s.write(out/(name+'.json'),data)
    semantic=s.load(out/'semantic-audit.json');assert semantic['passed'] and semantic==s.load(out/'semantic-audit-reproduced.json')
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources);cp['selective_learning']={k:s.binding(out/(k+'.json')) for k in ('protocol','comparisons','analysis','coverage-union','remaining','transport','references','semantic-audit')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp);s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,preserved_tables=pv['preserved_tables'],new_cumulative_records=0,reference_union_unchanged=cp['reference_union']==parent['reference_union'],prior_structural_union_unchanged=pv['prior_structural_union_unchanged'],constructed_union_unchanged=pv['constructed_union_unchanged'],checkpoint=s.binding(out/'checkpoint.json'),seconds=time.perf_counter()-start));print(s.encode(analysis))


def seal(out):
    p=s.load(out/'protocol.json');v=s.load(out/'validation.json');cp=s.load(out/'checkpoint.json');assert v['passed']
    for file,h in p['source_fingerprints'].items():assert s.sha(file)==h,file
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','e9e4f61f:'+paper],text=True);pat=r'\\begin\{proof\}.*?\\end\{proof\}';old=re.findall(pat,before,re.S);new=re.findall(pat,Path(paper).read_text(),re.S);assert len(old)==89 and new[:89]==old and len(new)==90
    for name,n in (('full-tests.log',2640),('focused-tests.log',22)):assert re.search(r'Ran '+str(n)+r' tests in .*\n\nOK',(out/name).read_text())
    for name in ('latex-reviewed.log','latex-final.log'):assert not re.search(r'Warning|Overfull|Underfull|^!',(out/name).read_text(),re.M)
    decision=s.load(out/'decision.json')
    for file,h in decision['documents'].items():assert s.sha(file)==h,file
    s.bound(decision['supplemental_checks']);cp['selective_learning']['decision']=s.binding(out/'decision.json');s.write(out/'checkpoint.json',cp);v['checkpoint']=s.binding(out/'checkpoint.json');s.write(out/'validation.json',v)
    s.write(out/'checks.json',dict(passed=True,full_tests=2640,focused_tests=22,old_proof_blocks_unchanged=89,added_proof_blocks=1,prior_sources=1362,final_sources=1367,prior_manifests=250,prior_artifacts=84291,checkpoint=s.binding(out/'checkpoint.json')))
    for file in out.rglob('*.log'):
        raw=file.read_bytes();original=Path(str(file)+'.raw.gz')
        if not original.exists():original.write_bytes(gzip.compress(raw,mtime=0))
        file.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json' and '__pycache__' not in f.parts)
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in files}));print(s.encode(dict(sealed=True,artifacts=len(files),next_manifests=251,next_artifacts=84291+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
