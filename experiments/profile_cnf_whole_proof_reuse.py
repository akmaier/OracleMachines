#!/usr/bin/env python3
"""Profile costly whole inputs after reproducing their exact chronological prefix."""
from pathlib import Path
import cProfile, pstats, sys, tempfile, time
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_proof_reuse as study
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_pool_priority import try_pools
base=study.base


def profile(out):
    p=base.load(out/'protocol.json'); records=[];pool_checks=[]
    for split, index in (('exposed',70), ('holdout',31), ('holdout',34)):
        cases=study.bound(p['cases'][split])
        for mode, cls in (('completion',study.WholeAffineSolver), ('reuse',study.WholeProofReuseSolver)):
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
        # Posthoc causal check: are complete pool results already available in
        # the new policy's exact prefix, before it chooses a partial plan?
        expected=base.load(out/f'{split}-reuse-0/queries.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';s=study.WholeProofReuseSolver(path,node_limit=p['node_limit'])
            try:
                for c,row in zip(cases[:index],expected[:index]):
                    r=attempt(s,c['source'])
                    assert (r['status'],r['metrics'])==(row['status'],row['metrics'])
                tick=time.perf_counter();s.counts=Counter()
                cnf,names,root=s._canonical(cases[index]['source'])
                route=try_pools(s,cnf,root);elapsed=time.perf_counter()-tick
                node=s._read(root,cnf) if route is not None else None
                if node is not None:
                    assert ('sat' if node['answer'] else 'unsat')==expected[index]['status']
                dest=out/f'pool-check-{split}-{index}';dest.mkdir()
                pool_checks.append(dict(split=split,case=index,route=route,answer=None if node is None else node['answer'],
                    root=root,seconds=elapsed,counts=dict(s.counts),archive=base.archive(path,dest)))
            finally:s.close()
    base.write(out/'profiling.json',dict(protocol=study.binding(out/'protocol.json'),records=records,
        pool_checks=pool_checks,
        limitations=['Exact chronological query prefix reproduced with an empty initial database; status and counters match timed workers.',
            'Profiling overhead is excluded from comparative means. Cumulative function times overlap.',
            'Pool-priority probes are posthoc diagnostics on an independently reconstructed reuse-policy prefix. They do not change the frozen policy or establish a matched improved-policy speedup.']))


if __name__=='__main__':profile(Path(sys.argv[1]))
