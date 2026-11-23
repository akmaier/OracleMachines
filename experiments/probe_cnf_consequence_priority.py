#!/usr/bin/env python3
"""Diagnostic matched-seed continuations; observation never grants authority."""
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_backbone as prior
from experiments.cnf_joint_backbone import JointBackboneSolver,SingleFromJointSolver,discover
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import normalize,token,restrict,propagate
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
base=prior.base;PARENT=Path('experiments/results/cnf-joint-backbone')


def inspect(cnf,solver):
    counts=Counter();proof,cover,paths=discover(cnf,counts);freq=Counter(abs(l) for c in cnf for l in c)
    var=min(freq,key=lambda v:(-freq[v],v)) if freq else None;children=[]
    if paths and var is not None:
        for value in (False,True):
            child,names=normalize(restrict(cnf,{var:value}));key=token(child,Counter());row=solver.db.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone()
            fixed,trace,conflict=propagate(child,Counter())
            children.append(dict(value=value,root=key,stored_answer=None if row is None else json.loads(row[0])['answer'],variables=len(names),units=len(fixed),conflict=conflict,remaining_literals=sum(map(len,restrict(child,fixed)))))
    return dict(source=[list(c) for c in cnf],root=token(cnf,Counter()),variables=len(freq),widths=dict(Counter(map(len,cnf))),
        paths=paths,subset_refutation=proof is not None,clause_cover=cover is not None,ordinary_variable=var,ordinary_children=children)


def run(out):
    p=base.load(PARENT/'protocol.json');cases=prior.bound(p['cases']);prefix=p['prefixes']['61']['archive'];seed=prior.read_zip(prefix);rows=[]
    cs=[c for c in cases if (c['split'],c['case'])==('novel',61)]
    for mode,cls in (('binary1',InputSafeAffineProbeSolver),('single',SingleFromJointSolver),('joint',JointBackboneSolver)):
        events=[];queries=[]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';prior.restore(seed,path);s=cls(path);original=s._expand;query_index=None
            def observed(cnf):
                entry=inspect(cnf,s);entry['query_index']=query_index;events.append(entry);return original(cnf)
            kernel=prior.previous.previous
            try:
                with patch.object(s,'_expand',observed),patch.object(kernel.targeted,'inspect_targeted_backbone',partial(kernel.first,policy='binary1')):
                    for query_index,c in enumerate(cs):
                        q=kernel.prepared_run(s,c['candidate'],'probe6',256);q.update(root=c['root'],variant=c['variant']);queries.append(q)
                final=prior.tables(s);delta={t:final[t][len(seed[t]):] for t in prior.TABLES}
            finally:s.close()
            rd=SnapshotResidualSolver(path)
            try:
                for key,value in delta[prior.TABLES[0]]:assert rd._read(key) is not None
                for q in queries:assert q['result'] is not None and rd._read(q['root'])['answer']==q['result']['answer']
            finally:rd.close()
        dest=out/mode;dest.mkdir(exist_ok=True);base.write(dest/'queries.json',queries);base.write(dest/'events.json',events);archive=prior.write_zip(dest/'delta.json.gz',delta)
        if mode!='single':
            trial=base.load(PARENT/f'novel-61-{mode}-0/report.json');assert prior.read_zip(archive)==prior.read_zip(trial['delta'])
            assert [r['expanded_nodes'] for r in queries]==[r['expanded_nodes'] for r in prior.bound(trial['queries'])]
        rows.append(dict(mode=mode,prefix=prefix,queries=prior.binding(dest/'queries.json'),events=prior.binding(dest/'events.json'),delta=archive))
        print(mode,[(q['variant'],q['expanded_nodes']) for q in queries],flush=True)
        for e in events:
            if e['paths']:print(e['query_index'],e['variables'],[x['literal'] for x in e['paths']],e['ordinary_variable'],[{k:v for k,v in c.items() if k!='root'} for c in e['ordinary_children']],flush=True)
    base.write(out/'exploration.json',dict(parent=prior.binding(PARENT/'checkpoint.json'),script_sha256=base.sha(__file__),rows=rows,limitations=[
        'Posthoc exposed case61; extra discovery, database-presence and propagation observations are diagnostic only and excluded from a speed claim. Stored-answer fields are observations, not checked authority.',
        'Baseline and joint count/delta outputs match frozen prior trials. Single-selected outputs are independently checked and retained for cumulative merge.']))


if __name__=='__main__':run(Path(sys.argv[1]))
