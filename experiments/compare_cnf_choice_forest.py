#!/usr/bin/env python3
"""Frozen source-only recognition, construction and process-cold replay."""
from collections import Counter
from itertools import combinations
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import cnf_choice_forest as e
from experiments import compare_cnf_answer_certificate as previous

PARENT = Path('experiments/results/cnf-answer-certificate')
FILES = ('experiments/cnf_choice_forest.py', 'experiments/compare_cnf_choice_forest.py',
         'experiments/validate_cnf_choice_forest.py', 'solver/test_cnf_choice_forest.py')
sha, load, encode, write, binding, bound, rss = (previous.sha, previous.load, previous.encode,
    previous.write, previous.binding, previous.bound, previous.rss)
ARMS = ('matching', 'forest', 'cut2')


def freeze(out):
    out.mkdir(exist_ok=True)
    assert not (out / 'protocol.json').exists()
    parent = load(PARENT / 'checkpoint.json')
    sources = {**parent['source_fingerprints'], **{f: sha(f) for f in FILES}}
    for f, h in sources.items(): assert sha(f) == h, f
    write(out / 'protocol.json', dict(parent=binding(PARENT / 'checkpoint.json'),
        parent_manifest=binding(PARENT / 'manifest.json'),
        external=binding('experiments/results/cnf-external-cutsets/panel.json'),
        source_fingerprints=sources, seed=20261128, sizes=[4,8,16,32],
        shapes=['private-path','blocked-path','cycle','two-triangles','k4-tail','k5-tail','ternary-edit','random-tree'],
        random_tree_repeats=3, orders=[list(ARMS),list(reversed(ARMS))],
        limits=dict(recognition=e.RECOGNITION_LIMIT,pairs=e.PAIR_LIMIT,cutset=e.MAX_CUTSET),
        prior_proof_hashes=[hashlib.sha256(b.encode()).hexdigest() for b in re.findall(
            r'\\begin\{proof\}.*?\\end\{proof\}', Path('paper/bounded_domain_sat_and_amortized_reasoning.tex').read_text(), re.S)],
        scope='All 37 exposed external cases plus the retained nonclique path; 40 constructed cases generated only after source/protocol freeze, without filtering outcomes. Shapes and intended difficulties are designed controls, not representative SAT holdouts. Recognition receives only clauses.',
        accounting='Three optional routes, no fallback. Two opposite-order construction processes per route, then two process-cold read/hash/decompress/check replays per route. Record discovery including its internal check, separate checking, canonical JSON/gzip/write cost, process RSS and wall time, exact graph/cutset/branch counts. OS caches are not flushed. Panel generation, independent audits and old acquisition remain extra. Null certificates persist unknown only.',
        limitations='Exact representative feasibility, not all Boolean models. Fixed cutset at most two, greedy incomplete source recognition and explicit caps. No new complete arbitrary-CNF classification, unrestricted polynomial SAT algorithm, cross-edit search cache or production dispatcher. Historical overall coverage unchanged.'))


def make_panel(p):
    rng = random.Random(p['seed'])
    rows = [dict(id=r['id'], group='external', source=r['source']) for r in bound(p['external'])]
    rows.append(dict(id='nonclique-path', group='regression', source=[[1,2,3],[4,5,6]]+[[-i,-i-1] for i in range(1,6)]))
    for size in p['sizes']:
        for shape in p['shapes']:
            for repeat in range(p['random_tree_repeats'] if shape=='random-tree' else 1):
                n = max(size, 6 if shape=='two-triangles' else 5 if shape=='k5-tail' else size)
                demands = [[1+3*i+j for j in range(3)] for i in range(n)]
                edges = {(i,i+1) for i in range(n-1)}
                if shape=='cycle': edges.add((0,n-1))
                if shape=='two-triangles': edges.update([(0,2),(3,5)])
                if shape in ('k4-tail','k5-tail'):
                    edges.update(combinations(range(4 if shape=='k4-tail' else 5),2))
                if shape=='random-tree': edges = {(rng.randrange(i),i) for i in range(1,n)}
                source = [c[:] for c in demands]
                for a,b in sorted(edges):
                    for x,y in ((x,y) for x in range(3) for y in range(3)):
                        include = x==y
                        if shape=='private-path': include = x in (1,2) and y in (1,2) and (x==y or (a%2==0 and x==1))
                        if shape=='blocked-path' and a==0 and b==1: include = True
                        if shape=='random-tree': include = rng.random()<0.55
                        if include: source.append([-demands[a][x],-demands[b][y]])
                if shape=='ternary-edit': source.append([-demands[0][0],-demands[1][0],-demands[2][0]])
                names = rng.sample(range(101,1000000),3*n)
                mapping = {v:rng.choice((-1,1))*names[v-1] for v in range(1,3*n+1)}
                source = [[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in source]
                for c in source: rng.shuffle(c)
                rng.shuffle(source)
                rows.append(dict(id=f'{size}-{shape}-{repeat}',group='constructed',shape=shape,source=source))
    return rows


def panel(out):
    assert not (out / 'panel.json').exists()
    write(out / 'panel.json', make_panel(load(out / 'protocol.json')))


def obtain(source, arm, counts):
    return e.prior.discover(source, counts) if arm=='matching' else e.discover(source, counts, cutset_limit=0 if arm=='forest' else 2)


def check(source, proof, arm, counts):
    if proof is None: return dict(answer=None,model=None)
    return (e.prior.check if arm=='matching' else e.check)(source,proof,counts)


def metrics(source, proof, arm):
    if proof is None or arm=='matching': return None
    d,g,c = e.layout(source,proof['demands'],Counter()) if not proof['empty'] else ([],{},set())
    cut = set(proof['cutset']); total=1
    for i in cut: total *= len(d[i])
    return dict(demands=len(d),edges=sum(map(len,g.values()))//2,conflicts=len(c),cutset_size=len(cut),
        remaining_edges=sum(sum(j not in cut for j in g[i]) for i in g if i not in cut)//2,
        branches_required=total,branches_completed=len(proof['branches']),
        live_entries=sum(sum(map(len,b)) for b in proof['branches'] if b is not None))


def worker(out, arm, repeat):
    started=time.perf_counter(); p=load(out/'protocol.json')
    for f in FILES: assert sha(f)==p['source_fingerprints'][f],f
    rows=load(out/'panel.json'); directory=out/f'{arm}-{repeat}'; directory.mkdir()
    cases=[]
    for row in rows:
        counts=Counter(); start=time.perf_counter(); proof,diag=obtain(row['source'],arm,counts)
        discovery=time.perf_counter()-start
        verification_counts=Counter(); start=time.perf_counter(); result=check(row['source'],proof,arm,verification_counts)
        verification=time.perf_counter()-start
        start=time.perf_counter(); data=encode(proof).encode(); encoded=time.perf_counter()-start
        start=time.perf_counter(); compressed=gzip.compress(data,mtime=0); compression=time.perf_counter()-start
        path=directory/(row['id']+'.json.gz'); start=time.perf_counter(); path.write_bytes(compressed); writing=time.perf_counter()-start
        cases.append(dict(id=row['id'],group=row['group'],result=result,diagnostic=diag,counts=dict(counts),verification_counts=dict(verification_counts),
            structure=metrics(row['source'],proof,arm),certificate=binding(path),json_bytes=len(data),gzip_bytes=len(compressed),
            phases=dict(discovery_seconds=discovery,verification_seconds=verification,encoding_seconds=encoded,compression_seconds=compression,write_seconds=writing)))
    write(directory/'report.json',dict(arm=arm,repeat=repeat,cases=cases,complete_seconds=time.perf_counter()-started,peak_rss_bytes=rss()))


def read_certificate(ref):
    data=Path(ref['path']).read_bytes(); assert hashlib.sha256(data).hexdigest()==ref['sha256']
    return json.loads(gzip.decompress(data))


def replay(out,arm,repeat):
    started=time.perf_counter(); rows=load(out/'panel.json'); report=load(out/f'{arm}-{repeat}'/'report.json'); cases=[]
    with patch.object(e,'discover',side_effect=AssertionError), patch.object(e,'choose_cutset',side_effect=AssertionError), \
         patch.object(e,'tables',side_effect=AssertionError), patch.object(e.prior,'discover',side_effect=AssertionError), \
         patch.object(e.prior.native,'solve_matching',side_effect=AssertionError):
        for row,case in zip(rows,report['cases']):
            assert row['id']==case['id']; start=time.perf_counter(); proof=read_certificate(case['certificate']); read=time.perf_counter()-start
            counts=Counter(); start=time.perf_counter(); result=check(row['source'],proof,arm,counts); verify=time.perf_counter()-start
            assert json.loads(encode(result))==case['result'] and counts==case['verification_counts']
            cases.append(dict(id=row['id'],read_seconds=read,verification_seconds=verify,result=result,counts=dict(counts)))
    write(out/f'replay-{arm}-{repeat}.json',dict(arm=arm,repeat=repeat,cases=cases,discovery_disabled=True,complete_seconds=time.perf_counter()-started,peak_rss_bytes=rss()))


def run(out):
    samples=[]
    for action in ('worker','replay'):
        for repeat,order in enumerate(load(out/'protocol.json')['orders']):
            for arm in order:
                start=time.perf_counter(); subprocess.run([sys.executable,__file__,action,str(out),arm,str(repeat)],check=True)
                path=out/f'{arm}-{repeat}'/'report.json' if action=='worker' else out/f'replay-{arm}-{repeat}.json'
                samples.append(dict(action=action,report=binding(path),process_wall_seconds=time.perf_counter()-start))
                print(action,arm,repeat,flush=True)
    write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1]; out=Path(sys.argv[2])
    if action in ('worker','replay'): globals()[action](out,sys.argv[3],int(sys.argv[4]))
    else: globals()[action](out)
