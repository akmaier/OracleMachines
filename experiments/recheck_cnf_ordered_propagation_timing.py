#!/usr/bin/env python3
"""Balanced repeated subset for trace-preserving affected-clause propagation."""
from collections import Counter
import gc
import hashlib
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_ordered_propagation import MODES, root_lift
from experiments.cnf_residual_dag import ResidualSolver, holds


def main(directory):
    target=directory/'timing-control.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    indices=[858,875,907,970,1042,1061,1194,977,1044,1185,1289,1368]
    order=['baseline','ordered','ordered','baseline','ordered','baseline','baseline','ordered']
    trials=[];expected={};database_hashes={}
    for mode in order:
        gc.collect();cls,options=MODES[mode]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';start=time.perf_counter()
            solver=ResidualSolver(path);h=cls(path,**options)
            initialization=time.perf_counter()-start;rows=[]
            for i in indices:
                source=report['cases'][i]['source'];start=time.perf_counter()
                discovery=h.inspect(source);solved=solver.solve(source)
                if solved['answer']:root_lift(h,discovery,solved['model'])
                elapsed=time.perf_counter()-start
                if solved['answer']:assert holds(source,solved['model'])
                reference=next(r for r in report['records'] if r['mode']==mode and r['case']==i)
                assert solved['answer']==reference['answer']
                assert discovery['summary']==reference['discovery']['summary']
                signature=(solved['answer'],discovery['summary'],discovery['metrics'])
                key=(mode,i)
                if key in expected:assert expected[key]==signature
                else:expected[key]=signature
                rows.append(dict(case=i,total_seconds=elapsed,discovery_seconds=discovery['seconds'],
                    solver_seconds=solved['seconds'],summary=discovery['summary'],metrics=discovery['metrics']))
            storage=h.storage();h.close();solver.close()
            database_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
            if mode in database_hashes:assert database_hashes[mode]==database_sha256
            else:database_hashes[mode]=database_sha256
            trials.append(dict(mode=mode,initialization_seconds=initialization,rows=rows,storage=storage,
                database_sha256=database_sha256,total_seconds=sum(r['total_seconds'] for r in rows),
                discovery_seconds=sum(r['discovery_seconds'] for r in rows),
                solver_seconds=sum(r['solver_seconds'] for r in rows)))
        print(mode,trials[-1]['total_seconds'],flush=True)
    summaries={}
    for mode in ('baseline','ordered'):
        rs=[r for r in trials if r['mode']==mode]
        summaries[mode]={k:dict(mean=statistics.mean(r[k] for r in rs),
            minimum=min(r[k] for r in rs),maximum=max(r[k] for r in rs))
            for k in ('total_seconds','discovery_seconds','solver_seconds')}
    result=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),indices=indices,
        order=order,trials=trials,summary=summaries,
        limitations=['Twelve fixed source queries; identical structural coverage and proofs, not a repeated full-corpus or industrial benchmark',
          'ABBA BAAB fresh-database runs balance order; four observations per mode do not establish significance',
          'Same operation inclusions as the full run; initialization, comparisons, hashing and cleanup excluded',
          'Every trial agrees with full-run answers/summaries; within-mode counters, storage and database hashes repeat',
          'Full experiment supplies persistent proof archives and cold replay; timing trial databases are ephemeral'])
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(summaries),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
