#!/usr/bin/env python3
"""Profile the largest remaining witness/ordinary solve-time ratio."""
from pathlib import Path
import cProfile,pstats,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_witness as study
base=study.base;old=study.old


def run(out):
    p=base.load(out/'protocol.json');comparison=base.load(out/'comparisons.json');groups={}
    for sample in comparison['samples']:
        if sample['mode'] in ('ordinary','witness'):
            groups.setdefault((sample['target'],sample['mode']),[]).append(old.bound(sample)['solve_seconds'])
    relative={t:sum(groups[(t,'witness')])/sum(groups[(t,'ordinary')])-1 for t in p['targets']}
    target=max(p['targets'],key=lambda t:(relative[t],-t))
    base.write(out/'profile-protocol.json',dict(comparisons=old.binding(out/'comparisons.json'),
        parent_protocol=old.binding(out/'protocol.json'),source=old.binding(Path(__file__)),
        target=target,relative_changes=relative,
        selection='Largest witness/ordinary solve-time ratio after comparison, including the least improvement if all ratios are below one. Adaptive exposed diagnostic.',
        limitations=['Only attempt is profiled. The two unprofiled alternating repetitions remain the timing comparison.',
            'Cumulative rows overlap; retain self time and calls rather than summing nested cumulative times.',
            'Each profile must reproduce its unprofiled native counters, gate summaries and database payloads.']))
    reports=[]
    for mode in ('ordinary','eager','witness'):
        dest=out/f'profile-{mode}';prof=cProfile.Profile();original=study.previous.attempt
        def profiled(*args,**kwargs):return prof.runcall(original,*args,**kwargs)
        study.previous.attempt=profiled
        try:study.trial(dest,out,target,mode)
        finally:study.previous.attempt=original
        prof.dump_stats(str(dest/'query.pstats'));stats=pstats.Stats(prof)
        rows=[dict(file=f,line=line,function=name,primitive_calls=cc,total_calls=nc,
                   self_seconds=tt,cumulative_seconds=ct)
              for (f,line,name),(cc,nc,tt,ct,callers) in stats.stats.items()]
        rows.sort(key=lambda r:(-r['cumulative_seconds'],r['file'],r['line']))
        base.write(dest/'query-profile.json',dict(total_seconds=stats.total_tt,rows=rows))
        reports.append(dict(mode=mode,report=old.binding(dest/'report.json'),
            profile=old.binding(dest/'query-profile.json'),raw=old.binding(dest/'query.pstats')))
    base.write(out/'profiles.json',dict(protocol=old.binding(out/'profile-protocol.json'),samples=reports))
    print(base.encode(dict(target=target,relative_changes=relative)),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
