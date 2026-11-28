#!/usr/bin/env python3
"""Independent message projections, exhaustive truth and preserved lineage."""
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
from experiments import compare_cnf_choice_separator as s


def models(source):
    names=sorted({abs(v) for c in source for v in c});truth=[]
    for values in product((False,True),repeat=len(names)):
        model=dict(zip(names,values))
        if all(any(model[abs(v)]==(v>0) for v in c) for c in source):truth.append(model)
    return truth


def semantic(out,name='semantic-audit.json'):
    counts=Counter();clauses=[[v*sign for v,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=2)]
    inputs=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)]
    clauses3=[[v*sign for v,sign in enumerate(signs,1) if sign] for signs in product((-1,0,1),repeat=3)]
    inputs += [list(rows) for n in range(4) for rows in combinations(clauses3,n)]
    rng=random.Random(845)
    for _ in range(64):
        mapping={v:rng.choice((-1,1))*w for v,w in zip((1,2,3),rng.sample(range(100,1000),3))}
        row=rng.sample(clauses3,rng.randrange(1,8));source=[[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in row]
        inputs.append(source+source[:1]+[[1001,-1001]])
    for source in inputs:
        truth=models(source);proof,_=s.e.discover(source);counts['arbitrary_inputs']+=1
        if proof is not None:
            got=s.e.check(source,proof);counts['arbitrary_certificates']+=1
            if got['answer'] is not None:assert got['answer']==bool(truth)
            if got['model'] is not None:assert got['model'] in truth
    demands=[[1,2],[3,4],[5,6]];owner={v:i for i,d in enumerate(demands) for v in d}
    pairs=[(a,b) for a in range(1,7) for b in range(a+1,7) if owner[a]!=owner[b]]
    choices=list(product(*demands))
    for mask in range(1<<len(pairs)):
        excluded=[pair for i,pair in enumerate(pairs) if mask>>i&1]
        source=demands+[[-a,-b] for a,b in excluded]
        if mask%2:source += [[-1,-2],[-3,-4],[-5,-6]]
        truth=models(source)
        for order in ([0,1,2],[2,1,0]):
            domains,graph,conflicts=s.e.prior.layout(source,demands,Counter())
            seps,children=s.e.plan(graph,order,Counter());rank={v:i for i,v in enumerate(order)}
            tables=[];relations=[];subtrees=[]
            for i,v in enumerate(order):
                table=s.e.make_table(i,domains,order,seps,children,relations,conflicts,Counter())
                inside={v}
                for child in children[i]:inside.update(subtrees[child])
                subtrees.append(inside)
                # Independently existentially project raw exclusion constraints
                # owned by this eliminated subtree, enumerating all representatives.
                owned=[(a,b) for a,b in excluded if min((owner[a],owner[b]),key=rank.__getitem__) in inside]
                expected={tuple(choice[w] for w in seps[i]) for choice in choices
                          if all(a not in choice or b not in choice for a,b in owned)}
                assert {tuple(row) for row in table}==expected
                tables.append(table);relations.append(expected);counts['independent_message_projections']+=1
            for length in range(4):
                proof=dict(format=s.e.FORMAT,empty=False,demands=demands,order=order,tables=tables[:length])
                got=s.e.check(source,proof)
                expected=False if any(not t for t in tables[:length]) else bool(truth) if length==3 else None
                assert got['answer'] is expected
                if got['answer'] is False:assert not truth
                if got['model'] is not None:assert got['model'] in truth
                counts['prefix_checks']+=1
        counts['conflict_sources']+=1
    s.write(out/name,dict(passed=True,counts=dict(counts),scope='3880 small CNFs: all 512 two-variable clause sets, 3304 three-variable sets of at most three clauses, and 64 signed sparse mixtures. All 4096 cross-conflict subsets of three binary demands, alternating internal exclusions, two reversed elimination orders, independent existential projection of each raw-constraint subtree, and all four message-prefix lengths.'))


def validate(out):
    started=time.perf_counter();p=s.load(out/'protocol.json');parent=s.bound(p['parent']);pv=s.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);pm=s.bound(p['parent_manifest'])
    manifests[p['parent_manifest']['path']]=dict(sha256=p['parent_manifest']['sha256'],artifacts_checked=len(pm['artifacts']))
    checked={};entries=0
    for path,item in manifests.items():
        assert s.sha(path)==item['sha256'],path
        artifacts=s.load(path)['artifacts'];assert len(artifacts)==item['artifacts_checked']
        for f,h in artifacts.items():
            if f not in checked:checked[f]=s.sha(f)
            assert checked[f]==h,f
        entries+=len(artifacts)
    for f,h in p['source_fingerprints'].items():assert s.sha(f)==h,f
    assert all(p['source_fingerprints'][f]==h for f,h in parent['source_fingerprints'].items())
    proof_hashes=[hashlib.sha256(b.encode()).hexdigest() for b in re.findall(r'\\begin\{proof\}.*?\\end\{proof\}',Path('paper/bounded_domain_sat_and_amortized_reasoning.tex').read_text(),re.S)]
    assert proof_hashes[:len(p['prior_proof_hashes'])]==p['prior_proof_hashes']
    publications={}
    for path in sorted(Path('publications/alphaxiv').glob('*/manifest.json')):
        artifacts=s.load(path)['artifacts']
        for f,h in artifacts.items():assert s.sha(f)==h,f
        publications[str(path)]=dict(sha256=s.sha(path),artifacts_checked=len(artifacts))
    rows=s.load(out/'panel.json');assert len(rows)==94 and rows==s.make_panel(p)
    assert [r['source'] for r in rows[:78]]==[r['source'] for r in s.bound(p['old_panel'])]
    reports={};replays={};timings={}
    for sample in s.load(out/'comparisons.json')['samples']:
        report=s.bound(sample['report']);arm=report['arm'];repeat=report['repeat']
        (reports if sample['action']=='worker' else replays)[arm,repeat]=report
        timings[sample['action'],arm,repeat]=sample['process_wall_seconds']
        assert [r['id'] for r in report['cases']]==[r['id'] for r in rows]
    summary={};groups=('external','regression','exposed-controls','fresh-controls')
    for arm in s.ARMS:
        runs=[reports[arm,i] for i in (0,1)]
        for row,c0,c1 in zip(rows,runs[0]['cases'],runs[1]['cases']):
            for k in ('result','counts','verification_counts','diagnostic','json_bytes','gzip_bytes'):assert c0[k]==c1[k],(arm,row['id'],k)
            proof=s.read_certificate(c0['certificate']);assert proof==s.read_certificate(c1['certificate'])
            counts=Counter();reproduced,diag=s.obtain(row['source'],arm,counts)
            assert reproduced==proof and diag==c0['diagnostic'] and counts==c0['counts']
            counts=Counter();got=s.check(row['source'],proof,arm,counts)
            assert json.loads(s.encode(got))==c0['result'] and counts==c0['verification_counts']
            assert len(s.encode(proof).encode())==c0['json_bytes']
            assert Path(c0['certificate']['path']).stat().st_size==c0['gzip_bytes']
        for i in (0,1):
            assert replays[arm,i]['constructors_disabled']
            for c,r in zip(runs[i]['cases'],replays[arm,i]['cases']):assert c['id']==r['id'] and c['result']==r['result'] and c['verification_counts']==r['counts']
        strata={}
        for group in groups:
            cases=[c for c in runs[0]['cases'] if c['group']==group]
            strata[group]=dict(cases=len(cases),sat=sum(c['result']['answer'] is True for c in cases),
                unsat=sum(c['result']['answer'] is False for c in cases),unknown=sum(c['result']['answer'] is None for c in cases))
        phases={k:statistics.mean(sum(c['phases'][k] for c in r['cases']) for r in runs) for k in runs[0]['cases'][0]['phases']}
        summary[arm]=dict(strata=strata,phases=phases,json_bytes=sum(c['json_bytes'] for c in runs[0]['cases']),gzip_bytes=sum(c['gzip_bytes'] for c in runs[0]['cases']),
            peak_rss_bytes=max(r['peak_rss_bytes'] for r in runs),process_wall_seconds=statistics.mean(timings['worker',arm,i] for i in (0,1)),
            cold_worker_seconds=statistics.mean(replays[arm,i]['complete_seconds'] for i in (0,1)),cold_process_seconds=statistics.mean(timings['replay',arm,i] for i in (0,1)),
            cold_peak_rss_bytes=max(replays[arm,i]['peak_rss_bytes'] for i in (0,1)))
    overlaps={}
    for group in groups:
        counts=Counter()
        for a,b in zip(reports['cut2',0]['cases'],reports['separator',0]['cases']):
            if a['group']!=group:continue
            x=a['result']['answer'];y=b['result']['answer']
            if x is not None and y is not None:assert x==y
            counts['both' if x is not None and y is not None else 'cut2_only' if x is not None else 'separator_only' if y is not None else 'neither']+=1
        overlaps[group]=dict(counts)
    old=s.load(s.PARENT/'cut2-0/report.json')['cases']
    for before,after in zip(old,reports['cut2',0]['cases']):
        assert before['id']==after['id'] and before['result']==after['result'] and before['counts']==after['counts'] and before['diagnostic']==after['diagnostic']
    semantic=s.load(out/'semantic-audit.json');assert semantic['passed'] and semantic==s.load(out/'semantic-audit-reproduced.json')
    details=[dict(id=c['id'],group=c['group'],answer=c['result']['answer'],diagnostic=c['diagnostic']) for c in reports['separator',0]['cases']]
    analysis=dict(arms=summary,overlaps=overlaps,separator_details=details,accounting=p['accounting'],limitations=p['limitations'],prior_overall_coverage_unchanged=True)
    s.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=p['source_fingerprints'])
    cp['choice_separator']={k:s.binding(out/(k+'.json')) for k in ('protocol','panel','comparisons','analysis','semantic-audit')}
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    s.write(out/'checkpoint.json',cp)
    s.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=entries,unique_prior_artifacts_checked=len(checked),
        source_fingerprints=p['source_fingerprints'],publications_unchanged=publications,prior_proofs_preserved=len(p['prior_proof_hashes']),current_proofs=len(proof_hashes),
        prior_structural_union_unchanged=True,constructed_union_unchanged=True,preserved_tables=pv['preserved_tables'],complete_seconds=time.perf_counter()-started))


def manifest(out):s.write(out/'manifest.json',dict(artifacts={str(f):s.sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.name!='manifest.json'}))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='semantic':semantic(out,sys.argv[3] if len(sys.argv)>3 else 'semantic-audit.json')
    else:globals()[action](out)
