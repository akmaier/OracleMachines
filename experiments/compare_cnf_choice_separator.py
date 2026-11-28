#!/usr/bin/env python3
"""Frozen separator recognition against the preceding conditioned forests."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import gzip
import hashlib
import json
import random
import re
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_choice_separator as e
from experiments import compare_cnf_choice_forest as previous

PARENT=Path('experiments/results/cnf-choice-forest')
FILES=('experiments/cnf_choice_separator.py','experiments/compare_cnf_choice_separator.py',
       'experiments/validate_cnf_choice_separator.py','solver/test_cnf_choice_separator.py')
sha,load,encode,write,binding,bound,rss=(previous.sha,previous.load,previous.encode,previous.write,previous.binding,previous.bound,previous.rss)
ARMS=('cut2','separator')


def freeze(out):
    out.mkdir(exist_ok=True); assert not (out/'protocol.json').exists()
    parent=load(PARENT/'checkpoint.json')
    sources={**parent['source_fingerprints'],**{f:sha(f) for f in FILES}}
    for f,h in sources.items():assert sha(f)==h,f
    write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),
        old_panel=binding(PARENT/'panel.json'),source_fingerprints=sources,seed=2026112813,sizes=[8,16,24,32],
        shapes=['ladder','triangles','mixed-domains','ternary-edit'],orders=[list(ARMS),list(reversed(ARMS))],
        limits=dict(states=e.STATE_LIMIT,bag_states=e.BAG_LIMIT,order_pair_tests=e.ORDER_LIMIT),
        prior_proof_hashes=[hashlib.sha256(b.encode()).hexdigest() for b in re.findall(r'\\begin\{proof\}.*?\\end\{proof\}',Path('paper/bounded_domain_sat_and_amortized_reasoning.tex').read_text(),re.S)],
        scope='All 78 previous cases, preserving their exposed status, plus 16 signed sparse controls generated only after freeze without outcome filtering. Fixed min-fill order; no width optimality claim. Pre-freeze graph-only pilot on exposed inputs found largest bag charges 2187--59049 and plan charges 15042--141654 for the five nonclique cases. Limits deliberately include these exposed descriptions; fresh controls, not those five, test frozen transfer.',
        accounting='Two opposite-order fresh construction processes per route, plus four constructor-disabled process-cold replays. Source-only recognition; no fallback or labels. Discovery includes internal checking; extra checking, encoding, compression, writing, graph width, planned/reserved states, live rows, RSS and process wall time recorded separately. No OS cache flush. Audits, panel preparation and all prior acquisition/storage are additional.',
        limitations='Complete projection only for fully checked signed-demand/exclusion descriptions. Greedy source extraction and min-fill order are incomplete. Fixed state/order caps do not bound total parsing, verification, storage or lifetime work. Tables are exponential in separator size, not a polynomial unrestricted SAT algorithm. No cross-edit cache, optimal decomposition or production default change.'))


def make_panel(p):
    rows=[{**row,'group':'exposed-controls' if row['group']=='constructed' else row['group']} for row in bound(p['old_panel'])]
    rng=random.Random(p['seed'])
    for n in p['sizes']:
        for shape in p['shapes']:
            widths=[3+(shape=='mixed-domains' and i%2==0) for i in range(n)]
            demands=[];start=1
            for width in widths: demands.append(list(range(start,start+width)));start+=width
            half=n//2
            edges={(i,i+1) for i in range(half-1)}|{(half+i,half+i+1) for i in range(half-1)}|{(i,half+i) for i in range(half)}
            if shape=='triangles':edges={(i,i+j) for i in range(n) for j in (1,2) if i+j<n}
            source=[c[:] for c in demands]
            for a,b in sorted(edges):
                for x in range(widths[a]):
                    for y in range(widths[b]):
                        include=x==y
                        if shape=='mixed-domains':include=include or rng.random()<0.15
                        if include:source.append([-demands[a][x],-demands[b][y]])
            if shape=='ternary-edit':source.append([-demands[0][0],-demands[1][0],-demands[2][0]])
            names=rng.sample(range(100001,10000000),start-1)
            mapping={v:rng.choice((-1,1))*names[v-1] for v in range(1,start)}
            source=[[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in source]
            for c in source:rng.shuffle(c)
            rng.shuffle(source)
            rows.append(dict(id=f'fresh-{n}-{shape}',group='fresh-controls',shape=shape,source=source))
    return rows


def panel(out):
    assert not (out/'panel.json').exists();write(out/'panel.json',make_panel(load(out/'protocol.json')))


def obtain(source,arm,counts):return (e.discover if arm=='separator' else e.prior.discover)(source,counts)


def check(source,proof,arm,counts):
    if proof is None:return dict(answer=None,model=None)
    return (e.check if arm=='separator' else e.prior.check)(source,proof,counts)


def worker(out,arm,repeat):
    started=time.perf_counter();p=load(out/'protocol.json')
    for f in FILES:assert sha(f)==p['source_fingerprints'][f],f
    rows=load(out/'panel.json');directory=out/f'{arm}-{repeat}';directory.mkdir();cases=[]
    for row in rows:
        counts=Counter();start=time.perf_counter();proof,diag=obtain(row['source'],arm,counts);discovery=time.perf_counter()-start
        verification_counts=Counter();start=time.perf_counter();result=check(row['source'],proof,arm,verification_counts);verification=time.perf_counter()-start
        start=time.perf_counter();data=encode(proof).encode();encoding=time.perf_counter()-start
        start=time.perf_counter();compressed=gzip.compress(data,mtime=0);compression=time.perf_counter()-start
        path=directory/(row['id']+'.json.gz');start=time.perf_counter();path.write_bytes(compressed);writing=time.perf_counter()-start
        cases.append(dict(id=row['id'],group=row['group'],result=result,diagnostic=diag,counts=dict(counts),verification_counts=dict(verification_counts),
            certificate=binding(path),json_bytes=len(data),gzip_bytes=len(compressed),
            phases=dict(discovery_seconds=discovery,verification_seconds=verification,encoding_seconds=encoding,compression_seconds=compression,write_seconds=writing)))
    write(directory/'report.json',dict(arm=arm,repeat=repeat,cases=cases,complete_seconds=time.perf_counter()-started,peak_rss_bytes=rss()))


read_certificate=previous.read_certificate


def replay(out,arm,repeat):
    started=time.perf_counter();rows=load(out/'panel.json');report=load(out/f'{arm}-{repeat}'/'report.json');cases=[]
    with patch.object(e,'discover',side_effect=AssertionError),patch.object(e,'min_fill',side_effect=AssertionError), \
         patch.object(e,'make_table',side_effect=AssertionError),patch.object(e.prior,'discover',side_effect=AssertionError), \
         patch.object(e.prior,'choose_cutset',side_effect=AssertionError),patch.object(e.prior,'tables',side_effect=AssertionError):
        for row,c in zip(rows,report['cases']):
            assert row['id']==c['id'];start=time.perf_counter();proof=read_certificate(c['certificate']);reading=time.perf_counter()-start
            counts=Counter();start=time.perf_counter();result=check(row['source'],proof,arm,counts);checking=time.perf_counter()-start
            assert json.loads(encode(result))==c['result'] and counts==c['verification_counts']
            cases.append(dict(id=row['id'],result=result,counts=dict(counts),read_seconds=reading,verification_seconds=checking))
    write(out/f'replay-{arm}-{repeat}.json',dict(arm=arm,repeat=repeat,cases=cases,constructors_disabled=True,complete_seconds=time.perf_counter()-started,peak_rss_bytes=rss()))


def run(out):
    samples=[]
    for action in ('worker','replay'):
        for repeat,order in enumerate(load(out/'protocol.json')['orders']):
            for arm in order:
                start=time.perf_counter();subprocess.run([sys.executable,__file__,action,str(out),arm,str(repeat)],check=True)
                path=out/f'{arm}-{repeat}'/'report.json' if action=='worker' else out/f'replay-{arm}-{repeat}.json'
                samples.append(dict(action=action,report=binding(path),process_wall_seconds=time.perf_counter()-start))
                print(action,arm,repeat,flush=True)
    write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action in ('worker','replay'):globals()[action](out,sys.argv[3],int(sys.argv[4]))
    else:globals()[action](out)
