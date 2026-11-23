#!/usr/bin/env python3
"""Exploratory exact-seed comparison of existing recognizers; no policy tuning claim."""
from collections import Counter,deque
from functools import partial
from pathlib import Path
from unittest.mock import patch
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_preparation as prior
from experiments import cnf_targeted_backbone as targeted
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_target_fallback import discover as extended
from experiments.cnf_binary_backbone import inspect_backbones
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import normalize,token,propagate,restrict
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
base=prior.base
PARENT=Path('experiments/results/cnf-partition-preparation')


def branch_seed(spec):
    prefix=prior.read_zip(spec['prefix']);trial=prior.bound(spec['trial_report']);delta=prior.read_zip(trial['delta']);wanted=set(spec['extra_ids'])
    extra={t:[[k,v] for k,v in delta[t] if t==prior.TABLES[0] and k in wanted] for t in prior.TABLES}
    assert len(extra[prior.TABLES[0]])==spec['extra_count']
    return {t:prefix[t]+extra[t] for t in prior.TABLES}


def census(cnf):
    graph={};ids=[i for i,c in enumerate(cnf) if len(c)==2]
    for cid in ids:
        a,b=cnf[cid];graph.setdefault(-a,[]).append((b,cid));graph.setdefault(-b,[]).append((a,cid))
    result=[]
    for root in sorted({l for c in cnf for v in c for l in (v,-v)}):
        par={root:None};q=deque([root]);edges=0
        while q and -root not in par:
            current=q.popleft()
            for to,cid in graph.get(current,[]):
                edges+=1
                if to not in par:par[to]=(current,cid);q.append(to)
        if -root in par:
            counts=Counter();child=restrict(cnf,{abs(root):root<0});fixed,trace,conflict=propagate(child,counts)
            result.append(dict(literal=root,edge_visits=edges,reached=len(par),surviving_forced=len(fixed),trace=trace,conflict=conflict,propagation_counts=dict(counts)))
    return dict(binary_clauses=len(ids),forced_false_roots=result,whole_false_clauses=[i for i,c in enumerate(cnf) if all(l in {r['literal'] for r in result} for l in c)])


def run(out):
    out.mkdir(exist_ok=True);spec=base.load(PARENT/'next-target.json')['branch_candidate'];seed=branch_seed(spec);cnf,_=normalize(spec['source'])
    assert token(cnf,Counter())==spec['root'];results={}
    for name,fn in (('original',targeted.inspect_targeted_backbone),('binary1',partial(discover,policy='binary1')),('total4',partial(discover,policy='total4')),('partials',inspect_backbones),('binary2',partial(extended,policy='binary2'))):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';prior.restore(seed,path);s=InputSafeAffineProbeSolver(path,node_limit=247);events=[];original=s._expand;depth=0
            def trace(c):
                nonlocal depth
                here=dict(depth=depth,cnf=[list(x) for x in c],variables=len({abs(l) for x in c for l in x}),widths=dict(Counter(map(len,c))),root=token(c,Counter()))
                events.append(here);depth+=1
                try:
                    model,proof=original(c);here.update(answer=model is not None,proof=proof);return model,proof
                finally:depth-=1
            try:
                assert s._read(spec['root']) is None
                with patch.object(targeted,'inspect_targeted_backbone',fn),patch.object(s,'_expand',trace):r=acquire(s,spec['source'],247)
                final=prior.tables(s);delta={t:final[t][len(seed[t]):] for t in prior.TABLES}
            finally:s.close()
            reader=SnapshotResidualSolver(path)
            try:
                for key,_ in delta[prior.TABLES[0]]:assert reader._read(key) is not None
                assert reader._read(spec['root'])['answer']==r['result']['answer']
            finally:reader.close()
            dest=out/name;dest.mkdir();base.write(dest/'trace.json',events);base.write(dest/'query.json',r);archive=prior.write_zip(dest/'delta.json.gz',delta)
            results[name]=dict(query=prior.binding(dest/'query.json'),trace=prior.binding(dest/'trace.json'),delta=archive,expanded_nodes=r['metrics']['expanded_nodes'],answer=r['result']['answer'])
    base.write(out/'exploration.json',dict(parent=prior.binding(PARENT/'checkpoint.json'),spec=spec,root_census=census(cnf),policies=results,
        script_sha256=base.sha(__file__),limitations=['Exploratory existing-policy comparison on one exposed branch, not held-out performance evidence. Trace wrapping changes timing.','Each fresh solver restores the exact captured persistent seed; transient pools from the original parent query are absent.','All new native nodes are independently checked and retained. No policy change or new tractable class is asserted.']))
    print(base.encode({k:{x:v[x] for x in ('expanded_nodes','answer')} for k,v in results.items()}))


if __name__=='__main__':run(Path(sys.argv[1]))
