#!/usr/bin/env python3
"""Reproduce the retrospective binary-core opportunity census and untimed checks."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_subset as study
from experiments.cnf_binary_subset import BinarySubsetSolver
from experiments.cnf_residual_dag import ResidualSolver,two_cnf,holds
base=study.base


def diagnose(out):
    parent=study.PARENT;report=base.load(parent/'session-0/report.json')
    queries=study.bound(report['queries']);cases=base.load(parent/'cases.json')['cases'];diagnosis=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'old';base.restore_archive(report['archive'],path);s=ResidualSolver(path)
        try:rows={base.key_sha(k):(k,base.load_json(v)) for k,v in study.native.rows(s).items()}
        finally:s.close()
    for row,case in zip(queries,cases):
        examined=negative=positive=0;details=[]
        for key in row['new_ids']:
            _,node=rows[key];cnf=node['cnf'];ids=[i for i,c in enumerate(cnf) if len(c)==2]
            if not ids or len(ids)==len(cnf) or any(len(c)<2 for c in cnf):continue
            examined+=1;model,proof=two_cnf([cnf[i] for i in ids],Counter())
            if proof is not None:
                negative+=1;details.append(dict(root_sha256=key,kind='binary-conflict',native_kind=node.get('proof',{}).get('kind')))
            else:
                variables={abs(l) for c in cnf for l in c}
                for fill in (False,True):
                    if holds(cnf,{v:model.get(v,fill) for v in variables}):
                        positive+=1;details.append(dict(root_sha256=key,kind='binary-model',fill=fill));break
        diagnosis.append(dict(case=case['case'],family=case['family'],nodes=row['new_nodes'],examined=examined,negative=negative,positive=positive,details=details))
    isolated=[]
    for case in cases:
        if case['case'] not in (35,44,47,52,56):continue
        arms={}
        for name,cls in (('native',ResidualSolver),('binary',BinarySubsetSolver)):
            s=cls()
            try:
                r=s.solve(case['source']);arms[name]=dict(answer=r['answer'],metrics=r['metrics'],nodes=r['archive_nodes'],payload=r['archive_payload_bytes'])
            finally:s.close()
        assert arms['native']['answer']==arms['binary']['answer']
        isolated.append(dict(case=case['case'],family=case['family'],arms=arms))
    base.write(out/'diagnosis.json',dict(source_catalog=study.binding(parent/'cases.json'),source_trial=study.binding(parent/'session-0/report.json'),
        census=diagnosis,totals={k:sum(r[k] for r in diagnosis) for k in ('examined','negative','positive')},isolated_checks=isolated,
        limitations=['Retrospective census of every newly inserted native node, not distinct fresh source coverage; ancestor closure can make descendants unnecessary.',
            'Positive binary models were tested against the whole residual, but this heuristic is not enabled by the negative-only policy.',
            'The five checks start from separate empty in-memory archives, with no shared preparation or discovery. These are untimed mechanism checks, not matched pipeline or exact-prefix timings.']))


if __name__=='__main__':diagnose(Path(sys.argv[1]))
