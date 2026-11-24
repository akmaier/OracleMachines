#!/usr/bin/env python3
"""Controlled compiler costs, persistent native witnesses and miss controls."""
from collections import Counter
from pathlib import Path
import random
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_covers as study
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_clause_cover import discover,compile_cover
from experiments.cnf_guard_cover_cases import family
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_fresh_mixtures import attempt
base=study.base;old=study.old


def run(out):
    p=base.load(out/'protocol.json');rng=random.Random(202611241621);rows=[]
    protocol=dict(parent=old.binding(out/'protocol.json'),source=old.binding(Path(__file__)),
        widths=[3,4,6,8],variants=['identity','signed_permutation'],repetitions=2,
        limitations=[
            'Controlled synthetic gadget family with deliberately supplied conditional-unit templates. Generation includes template acquisition, transport and graph/model preparation; it is timed separately and added to compiler cost for the charged total.',
            'Empty stores for both arms, alternating order, no native dispatch cap reached. Each archive and every contained native node is checked by both the base and canonical snapshot readers, with fresh reader instances.',
            'Warm compilation repeats evidence validation then reuses the root; warm fresh solve uses its native result. No zero-cost lookup or universal speedup is inferred.',
            'Serialized record bytes include keys and payloads, database/compressed bytes are separately reported. No allocator-level peak-memory measurement is made for these short in-process microtrials.'])
    base.write(out/'controlled-protocol.json',protocol)
    started=time.perf_counter()
    for width in protocol['widths']:
        for variant in protocol['variants']:
            rename=None
            if variant=='signed_permutation':
                names=list(range(1,4*width+1));rng.shuffle(names)
                rename={i:v*rng.choice((-1,1)) for i,v in enumerate(names,1)}
            for repeat in range(2):
                tick=time.perf_counter();source,templates,hints,graph,model=family(width,rename)
                preparation=time.perf_counter()-tick
                case=dict(width=width,variant=variant,repeat=repeat,source=[list(cl) for cl in source],
                          templates=templates,hints=hints,graph=graph,model=sorted([v,b] for v,b in model.items()),
                          preparation_seconds=preparation,arms={})
                for mode in ('fresh','cover') if repeat==0 else ('cover','fresh'):
                    dest=out/f'controlled-{width}-{variant}-{repeat}-{mode}';dest.mkdir()
                    with tempfile.TemporaryDirectory() as td:
                        path=Path(td)/'db';tick=time.perf_counter()
                        s=native.ResidualSolver(path) if mode=='cover' else LazyBinaryClosureSolver(path,node_limit=256)
                        setup=time.perf_counter()-tick;counts=Counter()
                        try:
                            tick=time.perf_counter()
                            if mode=='cover':
                                cover=discover(source,graph,model,counts,**p['discovery']);assert cover is not None
                                root=compile_cover(s,source,hints,graph,cover,counts);status='unsat'
                            else:
                                result=attempt(s,source);status=result['status'];root=result['result']['root']
                            solve=time.perf_counter()-tick;assert status=='unsat' and not s._read(root)['answer']
                            records=list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
                            native_counts=dict(s.counts);tick=time.perf_counter();warm_counts=Counter()
                            if mode=='cover': assert compile_cover(s,source,hints,graph,cover,warm_counts)==root
                            else: assert attempt(s,source)['result']['root']==root
                            warm=time.perf_counter()-tick
                            assert list(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))==records
                        finally:s.close()
                        readers={}
                        for cls in (native.ResidualSolver,CanonicalVerifySnapshot):
                            tick=time.perf_counter();reader=cls(path)
                            try:
                                for key,_ in records: assert not reader._read(key)['answer']
                            finally: reader.close()
                            readers[cls.__name__]=time.perf_counter()-tick
                        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
                        arm=dict(root=root,status=status,setup_seconds=setup,solve_seconds=solve,warm_seconds=warm,
                            counts=dict(counts),warm_counts=dict(warm_counts),native_counts=native_counts,
                            nodes=len(records),record_bytes=sum(len(k.encode())+len(v.encode()) for k,v in records),
                            cold_readers_seconds=readers,persistence_seconds=persistence,archive=archive,
                            charged_acquisition_and_solve_seconds=solve+(preparation if mode=='cover' else 0))
                    base.write(dest/'report.json',arm);case['arms'][mode]=old.binding(dest/'report.json')
                rows.append(case)
    misses=[]
    for edit in ('delete_support','delete_wide','flip_wide'):
        source,templates,hints,graph,model=family(edit=edit);c=Counter()
        assert discover(source,graph,model,c,**p['discovery']) is None
        s=native.ResidualSolver()
        try:
            verdict=s.solve(source);assert verdict['answer']
            assert native.holds(source,dict(verdict['assignment'])) if isinstance(verdict.get('assignment'),list) else True
        finally:s.close()
        misses.append(dict(edit=edit,source=source,templates=templates,hints=hints,graph=graph,
                           model=sorted([v,b] for v,b in model.items()),counts=dict(c),native_result=verdict))
    base.write(out/'controlled.json',dict(protocol=old.binding(out/'controlled-protocol.json'),rows=rows,misses=misses,
        complete_seconds=time.perf_counter()-started))
    print(base.encode(dict(rows=len(rows),misses=len(misses),seconds=time.perf_counter()-started)),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
