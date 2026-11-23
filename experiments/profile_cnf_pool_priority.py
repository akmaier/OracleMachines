#!/usr/bin/env python3
"""Diagnostic query-only profile; excluded from paired timing means."""
from pathlib import Path
import cProfile,pstats,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_pool_priority as study


def run(out):
    p=study.base.load(out/'protocol.json');original=study.query;prof=cProfile.Profile()
    def measured(*args,**kwargs):return prof.runcall(original,*args,**kwargs)
    study.query=measured;dest=out/'profile-pools-native';study.worker(dest,p,'pools-native')
    prof.dump_stats(str(out/'queries.pstats'));stats=pstats.Stats(prof)
    rows=[dict(file=f,line=line,function=name,primitive_calls=cc,calls=nc,self_seconds=tt,cumulative_seconds=ct) for (f,line,name),(cc,nc,tt,ct,callers) in stats.stats.items()]
    reference=study.base.load(out/'pools-native-0/report.json');actual=study.base.load(dest/'report.json')
    assert study.read_zip(actual['delta'])==study.read_zip(reference['delta'])
    for a,b in zip(study.bound(actual['queries']),study.bound(reference['queries'])):
        for field in ('root','status','route','expanded_nodes','new_ids'):assert a[field]==b[field],field
    study.base.write(out/'profile.json',dict(script_sha256=study.base.sha(__file__),trial=study.binding(dest/'report.json'),reference=study.binding(out/'pools-native-0/report.json'),proofs_and_routes_unchanged=True,
        total_query_seconds=stats.total_tt,total_calls=stats.total_calls,by_self=sorted(rows,key=lambda r:r['self_seconds'],reverse=True),by_cumulative=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True),
        limitations=['One query-only cProfile run of the matched stream. Instrumentation distorts timing; cumulative rows overlap. Profile timings are excluded from comparative means.']))
    print(study.base.encode(sorted(rows,key=lambda r:r['self_seconds'],reverse=True)[:12]),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
