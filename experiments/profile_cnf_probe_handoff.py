#!/usr/bin/env python3
"""Inspect the largest unresolved fresh attempt after exact-prefix replay."""
from collections import Counter
from pathlib import Path
import cProfile,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_handoff as study
from experiments.cnf_fresh_mixtures import attempt
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']['holdout'])
    allrows=[base.load(out/f'holdout-large-{i}/queries.json') for i in range(4)]
    means={c['case']:sum(rows[c['case']]['solve_seconds'] for rows in allrows)/4 for c in cases}
    unresolved=[c for c,r in zip(cases,allrows[0]) if r['result'] is None]
    if not unresolved:
        base.write(out/'profiling.json',dict(records=[],reason='No unresolved fresh attempt remains.'));return
    chosen=max(unresolved,key=lambda c:means[c['case']]);index=chosen['case'];records=[]
    for mode,cls in study.CLASSES.items():
        rows=base.load(out/f'holdout-{mode}-0/queries.json')
        with tempfile.TemporaryDirectory() as td:
            solver=cls(Path(td)/'db',node_limit=p['node_limit'])
            try:
                for c,row in zip(cases[:index],rows[:index]):
                    r=attempt(solver,c['source']);assert (r['status'],r['metrics'])==(row['status'],row['metrics'])
                profiler=cProfile.Profile();r=profiler.runcall(attempt,solver,chosen['source'])
                assert (r['status'],r['metrics'])==(rows[index]['status'],rows[index]['metrics'])
                present={n for n, in solver.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                captured={t:dict(solver.db.execute(f'SELECT id,payload FROM {t}')) if t in present else {} for t in study.ALL_TABLES}
            finally:solver.close()
            # Exact prefix results already live in the matched archive. Verify
            # equality, rather than silently adding another alternative proof.
            db=Path(td)/'final';base.restore_archive(base.load(out/f'holdout-{mode}-0/report.json')['archive'],db)
            import sqlite3
            con=sqlite3.connect(db)
            try:
                present={n for n, in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                for t,entries in captured.items():
                    archived=dict(con.execute(f'SELECT id,payload FROM {t}')) if t in present else {}
                    assert entries.items()<=archived.items()
            finally:con.close()
        target=out/f'profile-holdout-{mode}-{index}.pstats';profiler.dump_stats(target)
        functions=[dict(file=f,line=l,function=n,calls=v[1],own_seconds=v[2],cumulative_seconds=v[3])
            for (f,l,n),v in pstats.Stats(profiler).stats.items()]
        records.append(dict(mode=mode,case=index,result=r,profile=study.binding(target),
            functions=sorted(functions,key=lambda x:-x['cumulative_seconds'])))
    structure=Counter(len(c) for c in chosen['source'])
    base.write(out/'profiling.json',dict(protocol=study.binding(out/'protocol.json'),case=chosen,
        mean_solve_seconds=means[index],widths=dict(structure),records=records,limitations=[
            'Posthoc selection chooses the largest mean unresolved large-handoff attempt among four fresh repetitions; this is not a new holdout or an algorithmic gate.',
            'Each exact chronological prefix starts empty and matches status/counters. Every retained payload equals one already archived in its matched worker.',
            'Profiler overhead is outside comparative means; cumulative function times overlap. Structure labels are diagnostic only.']))


if __name__=='__main__':profile(Path(sys.argv[1]))
