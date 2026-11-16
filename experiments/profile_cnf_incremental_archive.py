#!/usr/bin/env python3
"""Locate the remaining cold replay cost after all matched workers finish."""
from pathlib import Path
import cProfile,pstats,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_archive as study


def profile(out):
    report=study.base.load(out/'report.json');trial=study.base.load(out/'delta-0/report.json')
    assert len(report['samples'])==9
    records=study.base.load(trial['queries']['path']);profiler=cProfile.Profile()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'cold';study.base.restore_archive(trial['archive'],path)
        start=time.perf_counter();profiler.enable();result=study.prior.old.previous.audit(path,records);profiler.disable()
        elapsed=time.perf_counter()-start
        assert study.base.sha(path)==trial['archive']['database_sha256']
    profiler.dump_stats(str(out/'cold-profile.pstats'));stats=pstats.Stats(profiler);selected=[]
    for (file,line,name),(primitive,calls,selftime,cumulative,_) in stats.stats.items():
        if name in ('audit','rows','archive_storage','_canonical','_read','_verify','solve','check_guard','check_witness','replay'):
            selected.append(dict(file=file,line=line,function=name,calls=calls,self_seconds=selftime,cumulative_seconds=cumulative))
    study.base.write(out/'cold-profile.json',dict(source=study.binding(__file__),trial=study.binding(out/'delta-0/report.json'),
        profile=study.binding(out/'cold-profile.pstats'),seconds=elapsed,check=result,selected=selected,archive_unchanged=True,
        limitations=['Post-hoc instrumented cold audit, separate from timed trials and validation. Cumulative times overlap; do not add nested categories.',
            'The audit retains the unchanged ordinary solver, including its per-query full archive-size census. These are diagnostics, not a measured replacement audit.']))
    print(study.base.encode(dict(seconds=elapsed,selected=selected)))


if __name__=='__main__':profile(Path(sys.argv[1]))
