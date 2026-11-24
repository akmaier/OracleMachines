#!/usr/bin/env python3
"""Locate closure overhead on the largest fresh paired query regression."""
from pathlib import Path
import cProfile,pstats,sqlite3,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_binary_closure as study
from experiments.cnf_fresh_mixtures import attempt
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']['holdout'])
    rows={m:[base.load(out/f'holdout-{m}-{i}/queries.json') for i in range(4)] for m in study.MODES}
    changes={c['case']:sum(rows['closure'][i][c['case']]['solve_seconds']-rows['current'][i][c['case']]['solve_seconds'] for i in range(4))/4 for c in cases}
    index=max(changes,key=changes.get);chosen=cases[index];records=[]
    for mode,cls in study.CLASSES.items():
        expected=rows[mode][0]
        with tempfile.TemporaryDirectory() as td:
            s=cls(Path(td)/'db',node_limit=p['node_limit'])
            try:
                for c,old in zip(cases[:index],expected[:index]):
                    r=attempt(s,c['source']);assert (r['status'],r['metrics'])==(old['status'],old['metrics'])
                profiler=cProfile.Profile();r=profiler.runcall(attempt,s,chosen['source'])
                assert (r['status'],r['metrics'])==(expected[index]['status'],expected[index]['metrics'])
                present={n for n, in s.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                captured={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) if t in present else {} for t in study.ALL_TABLES}
            finally:s.close()
            path=Path(td)/'expected';base.restore_archive(base.load(out/f'holdout-{mode}-0/report.json')['archive'],path)
            con=sqlite3.connect(path)
            try:
                present={n for n, in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                for t,entries in captured.items():
                    old=dict(con.execute(f'SELECT id,payload FROM {t}')) if t in present else {}
                    assert entries.items()<=old.items()
            finally:con.close()
        target=out/f'profile-holdout-{mode}-{index}.pstats';profiler.dump_stats(target)
        stats=pstats.Stats(profiler)
        functions=[dict(file=f,line=l,function=n,calls=v[1],own_seconds=v[2],cumulative_seconds=v[3],
            callers=[dict(file=cf,line=cl,function=cn,stats=cv) for (cf,cl,cn),cv in v[4].items()])
            for (f,l,n),v in stats.stats.items()]
        records.append(dict(mode=mode,case=index,result=r,profile=study.binding(target),
            functions=sorted(functions,key=lambda f:-f['cumulative_seconds'])))
    base.write(out/'profiling.json',dict(protocol=study.binding(out/'protocol.json'),case=chosen,
        mean_solve_increase_seconds=changes[index],records=records,limitations=[
            'Posthoc selection chooses the largest fresh mean closure-minus-current solve change; this is not another holdout or a policy gate.',
            'Each arm replays its own exact empty-start prefix and matches every status, metric and retained payload to the timed worker.',
            'Profiling overhead and concurrent verification are outside matched means. Cumulative function costs overlap; call counts and ordinary matched timings remain separate evidence.']))


if __name__=='__main__':profile(Path(sys.argv[1]))
