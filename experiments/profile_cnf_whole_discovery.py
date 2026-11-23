#!/usr/bin/env python3
"""Profile costly whole inputs after reproducing their exact chronological prefix."""
from pathlib import Path
import cProfile, pstats, sys, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_discovery as study
from experiments.cnf_fresh_mixtures import attempt
base=study.base


def profile(out):
    p=base.load(out/'protocol.json'); records=[]
    for split, index in (('exposed',37), ('holdout',1), ('holdout',36)):
        cases=study.bound(p['cases'][split])
        for mode, cls in (('current',study.ConsequencePrioritySolver), ('lookahead',study.WholeLookaheadSolver)):
            expected=base.load(out/f'{split}-{mode}-0/queries.json')
            with tempfile.TemporaryDirectory() as td:
                s=cls(Path(td)/'db', node_limit=p['node_limit'])
                try:
                    for c, row in zip(cases[:index], expected[:index]):
                        r=attempt(s,c['source'])
                        assert (r['status'],r['metrics'])==(row['status'],row['metrics'])
                    profiler=cProfile.Profile()
                    r=profiler.runcall(attempt,s,cases[index]['source'])
                    assert (r['status'],r['metrics'])==(expected[index]['status'],expected[index]['metrics'])
                finally: s.close()
            path=out/f'profile-{split}-{mode}-{index}.pstats';profiler.dump_stats(path)
            functions=[dict(file=f,line=l,function=n,calls=v[1],own_seconds=v[2],cumulative_seconds=v[3])
                for (f,l,n),v in pstats.Stats(profiler).stats.items()]
            records.append(dict(split=split, mode=mode, case=index, result=r, profile=study.binding(path),
                functions=sorted(functions,key=lambda x:-x['cumulative_seconds'])))
    base.write(out/'profiling.json',dict(protocol=study.binding(out/'protocol.json'),records=records,
        limitations=['Exact chronological query prefix reproduced with an empty initial database; status and counters match timed workers.',
            'Profiling overhead is excluded from comparative means. Cumulative function times overlap.']))


if __name__=='__main__':profile(Path(sys.argv[1]))
