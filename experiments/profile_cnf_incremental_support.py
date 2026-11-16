#!/usr/bin/env python3
"""Profile support preparation separately from the uninstrumented comparison."""
from pathlib import Path
from unittest.mock import patch
import cProfile,pstats,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_support as study
base=study.base


def profile(out):
    out.mkdir(exist_ok=False);parent=base.load(study.PARENT/'checkpoint.json');prior=base.load(parent['cofactor_support_bank']['path'])
    catalogs=[(f,base.load(parent[f]['path'])) for f in study.FIELDS];reports={}
    for mode in study.MODES:
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path);solver=study.ResidualSolver(path);solver.db.execute('PRAGMA query_only=ON')
            profiler=cProfile.Profile();tick=time.perf_counter()
            try:
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh profile search')),patch.object(solver,'_store',side_effect=AssertionError('Discovery publication')):
                    profiler.enable();prepared=study.preparation(solver,prior,catalogs,mode);profiler.disable()
                elapsed=time.perf_counter()-tick
            finally:solver.close()
            assert base.sha(path)==parent['reference_union']['database_sha256']
        profiler.dump_stats(str(out/f'{mode}.pstats'));stats=pstats.Stats(profiler);functions=[]
        for (file,line,name),(_,calls,selftime,cumulative,_) in stats.stats.items():
            if name in ('extract','_canonical','_read','check_guard','check_proposals','merge','_preimage','prepare','source_core','restrict'):
                functions.append(dict(file=file,line=line,function=name,calls=calls,self_seconds=selftime,cumulative_seconds=cumulative))
        base.write(out/f'{mode}-proposals.json',prepared)
        reports[mode]=dict(seconds=elapsed,origins=len(prepared['origins']),raw_supports=len(prepared['all_cores']),retained=len(prepared['cores']),
            extraction_counts=prepared['extraction_counts'] if mode!='ready' else {},functions=functions,profile=study.binding(out/f'{mode}.pstats'))
    a=base.load(out/'rebuild-proposals.json');b=base.load(out/'incremental-proposals.json')
    for f in ('cores','all_cores','origins','retained_indices','dominance'):assert a[f]==b[f],f
    base.write(out/'report.json',dict(parent=study.binding(study.PARENT/'checkpoint.json'),source=study.binding(__file__),reports=reports,
        identical_frontiers=True,no_fresh_search=True,archive_unchanged=True,
        limitation='Separately instrumented preparation diagnosis, not a benchmark speedup. Nested cumulative times overlap; no concurrent timed workers.'))
    print(base.encode({m:{k:v for k,v in r.items() if k not in ('functions','profile','extraction_counts')} for m,r in reports.items()}))


if __name__=='__main__':profile(Path(sys.argv[1]))
