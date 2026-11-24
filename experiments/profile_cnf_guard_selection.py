#!/usr/bin/env python3
"""Adaptively profile the largest guided solve-time regression after comparison."""
from pathlib import Path
import cProfile,pstats,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_probes as study
base=study.base;old=study.old


def run(out):
    p=base.load(out/'protocol.json');comparisons=base.load(out/'comparisons.json');groups={}
    for sample in comparisons['samples']:
        if sample['mode'] in ('native','guided'):
            groups.setdefault((sample['target'],sample['mode']),[]).append(old.bound(sample)['solve_seconds'])
    relative={t:sum(groups[(t,'guided')])/sum(groups[(t,'native')])-1 for t in p['targets']}
    target=max(p['targets'],key=lambda t:(relative[t],-t))
    protocol=dict(comparisons=old.binding(out/'comparisons.json'),parent_protocol=old.binding(out/'protocol.json'),
        source=old.binding(Path(__file__)),target=target,relative_changes=relative,
        selection='Largest observed guided/native mean solve-time ratio; adaptive diagnostic, not a holdout.',
        limitations=['Only attempt(solver, source) is profiled. Profile timing is diagnostic and excluded from the four unprofiled comparisons.',
            'Sorted cumulative rows overlap along the call graph and must not be summed as exclusive attribution. Native self time and call counts are also retained.',
            'Both profiles repeat the same exact causal prefix. Native counters and authority digests must match their unprofiled arm.'])
    base.write(out/'profile-protocol.json',protocol);reports=[]
    for mode in ('native','guided'):
        dest=out/f'profile-{mode}';prof=cProfile.Profile();original=study.attempt
        def profiled(*args,**kwargs):return prof.runcall(original,*args,**kwargs)
        study.attempt=profiled
        try:study.trial(dest,out,target,mode)
        finally:study.attempt=original
        prof.dump_stats(str(dest/'query.pstats'));stats=pstats.Stats(prof)
        rows=[dict(file=f,line=line,function=name,primitive_calls=cc,total_calls=nc,self_seconds=tt,cumulative_seconds=ct)
              for (f,line,name),(cc,nc,tt,ct,callers) in stats.stats.items()]
        rows.sort(key=lambda r:(-r['cumulative_seconds'],r['file'],r['line']))
        base.write(dest/'query-profile.json',dict(total_seconds=stats.total_tt,rows=rows))
        reports.append(dict(mode=mode,report=old.binding(dest/'report.json'),profile=old.binding(dest/'query-profile.json'),
            raw=old.binding(dest/'query.pstats')))
    base.write(out/'profiles.json',dict(protocol=old.binding(out/'profile-protocol.json'),samples=reports))
    print(base.encode(dict(target=target,relative_changes=relative)),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
