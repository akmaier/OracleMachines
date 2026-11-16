#!/usr/bin/env python3
"""Post-hoc profile of one checked warm visit; not a benchmark-speed result."""
from pathlib import Path
from collections import Counter
import cProfile,pstats,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_unsat_support as s
from experiments.cnf_clause_deletion_guard import ExtensionBank,propose,check_guard,lift
from experiments.cnf_clause_witness_reuse import reuse_witness
from experiments.cnf_unsat_support import CoreBank


def profile(out):
    data=s.base.load(out/'all-0/report.json');catalog=s.base.load(out/'cases.json');records=s.base.load(data['queries']['path']);cores=s.base.load(data['cores']['path'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';s.base.restore_archive(data['archive'],path);warmup=s.old.previous.audit(path,records)
        solver=s.ResidualSolver(path);solver.db.execute('PRAGMA query_only=ON');initial=s.rows(solver)
        with patch.object(solver,'_expand',side_effect=AssertionError('Fresh profile search')):
            for key in initial:solver._read(key)
            extensions=ExtensionBank(catalog['bank']);bank=CoreBank(solver,cores);profiler=cProfile.Profile();start=time.perf_counter();profiler.enable()
            for case in catalog['cases']:
                before=s.rows(solver);solver.counts=Counter();counts=Counter();cnf,_,key=solver._canonical(case['source']);known=solver._read(key,cnf)
                support=bank.reuse(case['source']) if known is None else None
                witness=reuse_witness(solver,extensions,case['source'],counts) if known is None and support is None else None
                guard=propose(solver,extensions,case['source'],counts) if known is None and support is None and witness is None else None
                if guard is None:fixed={};target=case['source']
                else:fixed,target=check_guard(solver,case['source'],guard,counts)
                child=solver.solve(target)
                if child['answer']:lift(case['source'],fixed,child['model'])
                assert child['answer']==records[case['case']]['answer']
                after=s.rows(solver);assert before==after;assert not set(after)-set(before)
            profiler.disable();elapsed=time.perf_counter()-start
        solver.close();assert s.base.sha(path)==data['archive']['database_sha256']
    profiler.dump_stats(str(out/'warm-profile.pstats'));stats=pstats.Stats(profiler);selected=[]
    for (file,line,name),(primitive,calls,selftime,cumulative,_) in stats.stats.items():
        if name in ('rows','archive_storage','_canonical','reuse','reuse_witness','propose','_read','solve'):
            selected.append(dict(file=file,line=line,function=name,calls=calls,self_seconds=selftime,cumulative_seconds=cumulative))
    s.base.write(out/'warm-profile.json',dict(source=s.binding(__file__),trial=s.binding(out/'all-0/report.json'),queries=len(catalog['cases']),
        seconds=elapsed,warmup=warmup,selected=selected,profile=s.binding(out/'warm-profile.pstats'),no_fresh_search=True,archive_unchanged=True,
        limitation='Instrumented post-hoc warm pass, separately charged. Cumulative times overlap across nested calls and are not summed indiscriminately; this is diagnostic evidence, not an optimization speedup.'))
    print(s.base.encode(dict(seconds=elapsed,selected=selected)))


if __name__=='__main__':profile(Path(sys.argv[1]))
