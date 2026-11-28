#!/usr/bin/env python3
"""Independent truth/representative audits and evidence preservation."""
from collections import Counter
from copy import deepcopy
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import random
import re
import statistics
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_choice_forest as s


def models(source):
    names=sorted({abs(v) for c in source for v in c})
    return [dict(zip(names,values)) for values in product((False,True),repeat=len(names))
            if all(any(dict(zip(names,values))[abs(v)]==(v>0) for v in c) for c in source)]


def semantic(out,name='semantic-audit.json'):
    counts=Counter(); clauses=[[v*sign for v,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=2)]
    inputs=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
    clauses3=[[v*sign for v,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=3)]
    inputs += [list(rows) for n in range(4) for rows in combinations(clauses3,n)]
    rng=random.Random(844)
    for _ in range(64):
        mapping={v:rng.choice((-1,1))*w for v,w in zip((1,2,3),rng.sample(range(100,1000),3))}
        row=rng.sample(clauses3,rng.randrange(1,8))
        source=[[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in row]
        inputs.append(source+source[:1]+[[1001,-1001]])
    for source in inputs:
        truth=models(source); proof,_=s.e.discover(source)
        counts['arbitrary_inputs']+=1
        if proof is not None:
            got=s.e.check(source,proof); counts['arbitrary_certificates']+=1
            if got['answer'] is not None: assert got['answer']==bool(truth)
            if got['model'] is not None: assert got['model'] in truth
    demands=[[1,2],[3,4],[5,6]]
    pairs=[(a,b) for a in range(1,7) for b in range(a+1,7) if (a-1)//2!=(b-1)//2]
    for mask in range(1<<len(pairs)):
        source=demands+[[-a,-b] for i,(a,b) in enumerate(pairs) if mask>>i&1]
        # Internal exclusions must also be harmless under normalization.
        if mask%2: source += [[-1,-2],[-3,-4],[-5,-6]]
        truth=models(source)
        representatives=[choice for choice in product(*demands)
                         if all(any((abs(v) in choice)==(v>0) for v in c) for c in source)]
        assert bool(truth)==bool(representatives)
        domains,graph,conflicts=s.e.layout(source,demands,Counter()); cut=[0]
        tree=s.e.forest(graph,cut,Counter())
        full=[s.e.tables(domains,cut,values,conflicts,tree,Counter(),[10000]) for values in product(domains[0])]
        for length in range(3):
            proof=dict(format=s.e.FORMAT,empty=False,demands=demands,cutset=cut,branches=full[:length])
            got=s.e.check(source,proof)
            feasible=any(choice[0] in demands[0][:length] for choice in representatives)
            expected=True if feasible else False if length==2 else None
            assert got['answer'] is expected
            if got['model'] is not None: assert got['model'] in truth
            counts['representative_prefix_checks']+=1
        counts['conflict_sources']+=1
    s.write(out/name,dict(passed=True,counts=dict(counts),scope='3880 arbitrary small formulas, including all 512 two-variable clause sets and 3304 three-variable sets of at most three clauses; 64 sparse signed edits. All 4096 cross-conflict subsets of three binary demands, alternating internal exclusions, exhaustive Boolean and representative truth, and all three branch-prefix lengths.'))


def validate(out):
    started=time.perf_counter(); p=s.load(out/'protocol.json'); parent=s.bound(p['parent'])
    manifests=deepcopy(s.load(s.PARENT/'validation.json')['parent_manifests']); pm=s.bound(p['parent_manifest'])
    manifests[p['parent_manifest']['path']]=dict(sha256=p['parent_manifest']['sha256'],artifacts_checked=len(pm['artifacts']))
    checked={}; entries=0
    for path,item in manifests.items():
        assert s.sha(path)==item['sha256'],path
        artifacts=s.load(path)['artifacts']; assert len(artifacts)==item['artifacts_checked']
        for f,h in artifacts.items():
            if f not in checked: checked[f]=s.sha(f)
            assert checked[f]==h,f
        entries+=len(artifacts)
    for f,h in p['source_fingerprints'].items(): assert s.sha(f)==h,f
    assert all(p['source_fingerprints'][f]==h for f,h in parent['source_fingerprints'].items())
    proof_hashes=[hashlib.sha256(b.encode()).hexdigest() for b in re.findall(r'\\begin\{proof\}.*?\\end\{proof\}',Path('paper/bounded_domain_sat_and_amortized_reasoning.tex').read_text(),re.S)]
    assert proof_hashes[:len(p['prior_proof_hashes'])]==p['prior_proof_hashes']
    publications={}
    for path in sorted(Path('publications/alphaxiv').glob('*/manifest.json')):
        artifacts=s.load(path)['artifacts']
        for f,h in artifacts.items(): assert s.sha(f)==h,f
        publications[str(path)]=dict(sha256=s.sha(path),artifacts_checked=len(artifacts))
    rows=s.load(out/'panel.json'); assert len(rows)==78
    assert rows==s.make_panel(p)
    assert [r['source'] for r in rows[:37]]==[r['source'] for r in s.bound(p['external'])]
    reports={}; replays={}; timings={}
    for sample in s.load(out/'comparisons.json')['samples']:
        report=s.bound(sample['report']); arm=report['arm']; repeat=report['repeat']
        (reports if sample['action']=='worker' else replays)[arm,repeat]=report
        timings[sample['action'],arm,repeat]=sample['process_wall_seconds']
        assert [r['id'] for r in report['cases']]==[r['id'] for r in rows]
    summary={}
    for arm in s.ARMS:
        runs=[reports[arm,i] for i in (0,1)]
        for row,c0,c1 in zip(rows,runs[0]['cases'],runs[1]['cases']):
            for k in ('result','counts','verification_counts','diagnostic','structure','json_bytes','gzip_bytes'): assert c0[k]==c1[k],(arm,row['id'],k)
            proof=s.read_certificate(c0['certificate']); assert proof==s.read_certificate(c1['certificate'])
            counts=Counter(); reproduced,diag=s.obtain(row['source'],arm,counts)
            assert reproduced==proof and diag==c0['diagnostic'] and counts==c0['counts']
            counts=Counter(); got=s.check(row['source'],proof,arm,counts)
            assert json.loads(s.encode(got))==c0['result'] and counts==c0['verification_counts']
            assert s.metrics(row['source'],proof,arm)==c0['structure']
            assert len(s.encode(proof).encode())==c0['json_bytes']
            for i in (0,1): assert replays[arm,i]['discovery_disabled']
        for i in (0,1):
            for c,r in zip(runs[i]['cases'],replays[arm,i]['cases']):
                assert c['id']==r['id'] and c['result']==r['result'] and c['verification_counts']==r['counts']
        strata={}
        for group in ('external','regression','constructed'):
            cases=[c for c in runs[0]['cases'] if c['group']==group]
            strata[group]=dict(cases=len(cases),sat=sum(c['result']['answer'] is True for c in cases),
                unsat=sum(c['result']['answer'] is False for c in cases),unknown=sum(c['result']['answer'] is None for c in cases),
                exact_descriptions=sum(c['structure'] is not None for c in cases))
        phases={k:statistics.mean(sum(c['phases'][k] for c in r['cases']) for r in runs) for k in runs[0]['cases'][0]['phases']}
        summary[arm]=dict(strata=strata,phases=phases,json_bytes=sum(c['json_bytes'] for c in runs[0]['cases']),
            gzip_bytes=sum(c['gzip_bytes'] for c in runs[0]['cases']),peak_rss_bytes=max(r['peak_rss_bytes'] for r in runs),
            process_wall_seconds=statistics.mean(timings['worker',arm,i] for i in (0,1)),
            cold_worker_seconds=statistics.mean(replays[arm,i]['complete_seconds'] for i in (0,1)),
            cold_process_seconds=statistics.mean(timings['replay',arm,i] for i in (0,1)),
            cold_peak_rss_bytes=max(replays[arm,i]['peak_rss_bytes'] for i in (0,1)))
    overlaps={}
    for group in ('external','regression','constructed'):
        pairs=[(a,b) for a,b in zip(reports['matching',0]['cases'],reports['cut2',0]['cases']) if a['group']==group]
        counts=Counter()
        for a,b in pairs:
            x=a['result']['answer']; y=b['result']['answer']
            if x is not None and y is not None: assert x==y
            counts['both' if x is not None and y is not None else 'matching_only' if x is not None else 'cut2_only' if y is not None else 'neither']+=1
        overlaps[group]=dict(counts)
    informative=[c for c in reports['cut2',0]['cases'] if c['id'] in ('e012','e013','e014','e015','e031')]
    assert len(informative)==5
    semantic=s.load(out/'semantic-audit.json'); assert semantic['passed'] and semantic==s.load(out/'semantic-audit-reproduced.json')
    analysis=dict(arms=summary,overlaps=overlaps,retained_nonclique_cases=informative,
        accounting=p['accounting'],limitations=p['limitations'],prior_overall_coverage_unchanged=True)
    s.write(out/'analysis.json',analysis)
    cp=deepcopy(parent); cp.update(parent_checkpoint=p['parent'],source_fingerprints=p['source_fingerprints'])
    cp['choice_forest']={k:s.binding(out/(k+'.json')) for k in ('protocol','panel','comparisons','analysis','semantic-audit')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=entries,
        unique_prior_artifacts_checked=len(checked),source_fingerprints=p['source_fingerprints'],publications_unchanged=publications,
        prior_proofs_preserved=len(p['prior_proof_hashes']),current_proofs=len(proof_hashes),
        prior_structural_union_unchanged=True,constructed_union_unchanged=True,preserved_tables={k:v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints')},
        complete_seconds=time.perf_counter()-started))


def manifest(out):
    s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='manifest.json'}))


if __name__=='__main__':
    action=sys.argv[1]; out=Path(sys.argv[2])
    if action=='semantic': semantic(out,sys.argv[3] if len(sys.argv)>3 else 'semantic-audit.json')
    else: globals()[action](out)
