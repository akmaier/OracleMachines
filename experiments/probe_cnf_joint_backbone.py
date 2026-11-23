#!/usr/bin/env python3
"""Full diagnostic reachability census on an exact saved branch; not timed search."""
from collections import Counter,deque
from functools import partial
from pathlib import Path
from unittest.mock import patch
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_live_fallback as prior
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,token
from experiments.cnf_binary_backbone import check_path
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
base=prior.base;PARENT=Path('experiments/results/cnf-live-fallback')


def seed(spec):
    prefix=prior.read_zip(spec['prefix']);trial=prior.bound(spec['trial']);delta=prior.read_zip(trial['delta'])
    extra={t:[[k,v] for k,v in delta[t] if k in set(spec['extra_ids'][t])] for t in prior.TABLES}
    for t in prior.TABLES:assert len(extra[t])==len(spec['extra_ids'][t])
    return {t:prefix[t]+extra[t] for t in prior.TABLES}


def census(cnf):
    graph={};freq=Counter(abs(l) for c in cnf if len(c)==2 for l in c)
    for cid,c in enumerate(cnf):
        if len(c)==2:
            a,b=c;graph.setdefault(-a,[]).append((b,cid));graph.setdefault(-b,[]).append((a,cid))
    ranked=sorted(freq,key=lambda v:(-freq[v],v));paths={};closures={}
    for root in sorted(graph):
        par={root:None};q=deque([root])
        while q:
            current=q.popleft()
            for nxt,cid in graph.get(current,()):
                if nxt not in par:par[nxt]=(current,cid);q.append(nxt)
        closures[root]=set(par)
        if -root in par:
            chain=[];current=-root
            while current!=root:
                prev,cid=par[current];chain.append([current,cid]);current=prev
            evidence=dict(literal=root,path=list(reversed(chain)));check_path(cnf,evidence,Counter());paths[root]=evidence
    return dict(variables=len({abs(l) for c in cnf for l in c}),widths=dict(Counter(map(len,cnf))),
        forced=[dict(evidence=e,rank=ranked.index(abs(l))+1,covered_forced=sorted(k for k in paths if -k in closures.get(-l,{-l}))) for l,e in paths.items()],
        first_ranks=ranked[:12])


def run(out):
    out.mkdir(exist_ok=True);capture=next(c for c in base.load(PARENT/'next-target.json')['captures'] if c['split']=='novel')
    spec=dict(capture['acquisitions'][2],trial=capture['trial']);prefix=seed(spec);events=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';prior.restore(prefix,path);s=InputSafeAffineProbeSolver(path);original=s._expand
        def traced(cnf):
            events.append(dict(source=[list(c) for c in cnf],root=token(cnf,Counter()),census=census(cnf)))
            return original(cnf)
        try:
            assert s._read(spec['root']) is None
            with patch.object(prior.previous.targeted,'inspect_targeted_backbone',partial(prior.previous.first,policy='binary1')),patch.object(s,'_expand',traced):r=acquire(s,spec['source'],spec['effective_budget'])
            final=prior.tables(s);delta={t:final[t][len(prefix[t]):] for t in prior.TABLES}
        finally:s.close()
        rd=SnapshotResidualSolver(path)
        try:
            for k,v in delta[prior.TABLES[0]]:assert rd._read(k) is not None
            assert rd._read(spec['root'])['answer']==r['result']['answer']
        finally:rd.close()
        base.write(out/'census.json',events);base.write(out/'exploration-query.json',r);archive=prior.write_zip(out/'exploration-delta.json.gz',delta)
    base.write(out/'exploration.json',dict(parent=prior.binding(PARENT/'checkpoint.json'),spec=spec,census=prior.binding(out/'census.json'),query=prior.binding(out/'exploration-query.json'),delta=archive,script_sha256=base.sha(__file__),limitations=[
        'Complete reachability census is diagnostic only, run on an exposed saved branch. Its work is not part of a claimed bounded recognizer or held-out evaluation.',
        'The seed includes only the captured prefix and earlier trial rows. All emitted proofs are independently checked and retained. The final union containing the answer is never seeded.']))
    print(base.encode(dict(expansions=r['metrics']['expanded_nodes'],events=[dict(variables=e['census']['variables'],forced=[dict(literal=f['evidence']['literal'],rank=f['rank'],covered=f['covered_forced']) for f in e['census']['forced']]) for e in events])))


if __name__=='__main__':run(Path(sys.argv[1]))
