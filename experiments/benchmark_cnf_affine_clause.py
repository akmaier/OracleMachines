#!/usr/bin/env python3
"""Matched fresh/reuse costs for one exact family; no whole-solver speedup claim."""
from collections import Counter
import argparse
import gzip
import itertools
import json
from pathlib import Path
import random
import statistics
import sys
import time
import tracemalloc
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.cnf_affine_clause import discover, check_certificate
from experiments.cnf_affine_patterns import extract_affine, check_affine
from experiments.cnf_residual_dag import normalize
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_probe_continuation import sha
from experiments.compare_cnf_trace_reuse import archive_json, read_archive


def parity(variables, rhs):
    return [[-v if b else v for v,b in zip(variables,bits)]
        for bits in itertools.product((0,1),repeat=len(variables)) if sum(bits)%2 != rhs]


def work(raw, counts, prior=None):
    cnf, _ = normalize(raw, counts); cnf = list(map(list,cnf))
    if prior is None: return discover(cnf,counts)
    return discover(cnf,counts,affine=prior['affine'],space=prior['decision']['space'])


def measure(raw, prior, repeats):
    times=[]; counters=[]; result=None
    for _ in range(repeats):
        counts=Counter(); start=time.perf_counter(); result=work(raw,counts,prior)
        times.append(time.perf_counter()-start); counters.append(dict(counts))
    assert all(c==counters[0] for c in counters)
    # Separate allocation observation; tracemalloc is not in the timed samples.
    tracemalloc.start(); memory_result=work(raw,Counter(),prior); _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert memory_result==result
    return result,dict(seconds=times,median_seconds=statistics.median(times),counts=counters[0],python_peak_traced_bytes=peak)


def run(out):
    out.mkdir(exist_ok=False); started=time.perf_counter(); rng=random.Random(2026111316); rows=[]; artifacts=[]
    for n in (12,24,48,96):
        base=sum((parity(range(i,i+3),0) for i in range(1,n+1,3)),[])
        for kind,raw in [('repair',base+[list(range(1,n+1))]),
                ('particular',base+[list(range(-n,0))]),
                ('unsat',[[-1],[-2],[1,2]]+sum((parity(range(i,i+3),0) for i in range(3,n,3)),[]))]:
            # Random labels and order remove a privileged syntactic presentation.
            support=sorted({abs(l) for c in raw for l in c}); labels=rng.sample(range(100,10000),len(support))
            mapping=dict(zip(support,labels)); raw=[[mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(raw)]
            start=time.perf_counter(); seed=work(raw,Counter()); seed_seconds=time.perf_counter()-start
            assert seed is not None and check_certificate(seed)['sat']==(kind!='unsat')
            arms={}
            # Both arms normalize, verify exact extraction, check complete spaces,
            # check the decision and copy the same proof. Only acquisition differs.
            for name,prior in [('fresh',None),('reuse',seed)]:
                result,arms[name]=measure(raw,prior,9);assert result==seed
            packed=encode(seed).encode(); start=time.perf_counter(); zipped=gzip.compress(packed,mtime=0)
            serialization_seconds=time.perf_counter()-start
            space=seed['decision']['space']; answer=check_certificate(seed)
            row=dict(size=n,variables=answer['variables'],kind=kind,rank=answer['rank'],seed_seconds=seed_seconds,
                arms=arms,proof_bytes=len(packed),proof_gzip_bytes=len(zipped),compression_seconds=serialization_seconds,
                vectors=len(space['directions'])+1,vector_bit_lengths=sum(v.bit_length() for v in [space['particular'],*space['directions']]))
            # Add a second wide clause: a sound abstention, not an UNSAT answer.
            bad=seed['cnf']+[list(range(1,answer['variables']))]
            if all(set(c)!=set(bad[-1]) for c in seed['cnf']):
                start=time.perf_counter(); a=extract_affine(bad,Counter()); summary=check_affine(bad,a,Counter())
                assert summary['leftover_clauses']>1 and discover(bad,affine=a) is None
                row['second_clause_control']=dict(leftovers=summary['leftover_clauses'],seconds=time.perf_counter()-start)
            rows.append(row);artifacts.append(dict(raw=raw,proof=seed))
    # Same variable binding and same equations, but a changed sole clause.
    a=artifacts[0]['proof']; changed=[list(c) for c in a['cnf']]; cid=a['affine']['leftovers'][0]
    changed[cid]=[-l for l in changed[cid]]
    counts=Counter(); start=time.perf_counter(); b=discover(changed,counts,space=a['decision']['space'])
    edited=dict(seconds=time.perf_counter()-start,counts=dict(counts),sat=check_certificate(b)['sat'])
    artifacts.append(dict(raw=changed,proof=b))
    report=dict(format='affine-one-clause-matched-cost-v1',fingerprints={f:sha(f) for f in
        ('experiments/cnf_affine_clause.py','experiments/benchmark_cnf_affine_clause.py')},rows=rows,clause_edit=edited,
        certificates=archive_json(out/'certificates.json.gz',artifacts),seconds=time.perf_counter()-started,
        limitations=['Generated restricted-family cases, not a representative arbitrary-SAT benchmark.',
            'Warm exact-source reuse presupposes paid seed acquisition; changing the CNF requires a fresh bound extraction certificate.',
            'The edit arm reuses only the checked solution space and pays extraction/checking of its new source.',
            'Python traced allocation peaks are local calls, not process RSS or whole-history peak RAM.',
            'The affine row and nullspace representations are polynomial, while CNF parity inputs can already be exponentially large.',
            'Matched local timing includes normalization and proof construction/checking but excludes filesystem/history reconstruction; storage and cold replay are separate.'])
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(cases=len(rows),seconds=report['seconds'])),flush=True)


def replay(out):
    start=time.perf_counter();r=json.loads((out/'report.json').read_text());counts=Counter()
    for f,digest in r['fingerprints'].items(): assert sha(f)==digest
    with patch('experiments.cnf_affine_clause.extract_affine',side_effect=AssertionError('discovery')):
        artifacts=read_archive(r['certificates'])
        for row in artifacts:
            # Compare normalized formulas since one edited source preserves clause order.
            normalized,_=normalize(row['raw'],counts); cnf,_=normalize(row['proof']['cnf'],counts)
            assert normalized==cnf;check_certificate(row['proof'],counts=counts)
    result=dict(report_sha256=sha(out/'report.json'),certificates=len(artifacts),new_discovery=False,
        seconds=time.perf_counter()-start,counts=dict(counts))
    (out/'cold-replay.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--replay',action='store_true')
    a=p.parse_args();(replay if a.replay else run)(a.output)
