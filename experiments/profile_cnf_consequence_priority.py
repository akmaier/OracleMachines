#!/usr/bin/env python3
"""Posthoc profiles and checked-source arbitration observations on frozen streams."""
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import cProfile,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_consequence_priority as study,cnf_consequence_priority as priority
from experiments import cnf_partition_preparation as prepared
from experiments.cnf_joint_backbone import JointBackboneSolver
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
base=study.base


def run_query(s,c,p):
    if study.native_split(c['split']):return study.harness.query(s,c,'native',p['branch_limit'])
    return study.previous.previous.previous.prepared_run(s,c['candidate'],'probe6',p['node_limit'])


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);scores=[]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            times={m:sum(base.load(out/f'novel-{index}-{m}-{i}/queries.json')[j]['seconds'] for i in range(2))/2 for m in study.MODES}
            scores.append(dict(case=index,position=j,root=c['root'],variant=c['variant'],query_seconds=times))
    worst=max(scores,key=lambda r:r['query_seconds']['priority']);profiles=[];observations=[]
    for split,index,position in (('branch-original',31,0),('controls',61,0),('novel',worst['case'],worst['position'])):
        cs=[c for c in cases if (c['split'],c['case'])==(split,index)]
        prefix_binding=p['prefixes'][split if study.native_split(split) else str(index)]['archive'];prefix=study.read_zip(prefix_binding)
        for mode in study.MODES:
            trial_path=out/f'{split}-{index}-{mode}-0/report.json';trial=base.load(trial_path);expected=study.bound(trial['queries'])
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';study.restore(prefix,path)
                cls={'binary1':InputSafeAffineProbeSolver,'joint':JointBackboneSolver,'priority':priority.ConsequencePrioritySolver}[mode]
                s=cls(path);prof=cProfile.Profile();kernel=study.previous.previous.previous
                try:
                    with patch.object(kernel.targeted,'inspect_targeted_backbone',partial(kernel.first,policy='binary1')):
                        for j,c in enumerate(cs):
                            before=study.tables(s)
                            if j==position:prior=before;prof.enable()
                            r=run_query(s,c,p)
                            if j==position:prof.disable()
                            for f in ('expanded_nodes','status','partition'):assert r[f]==expected[j][f]
                    final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES};assert delta==study.read_zip(trial['delta'])
                finally:s.close()
            stats=pstats.Stats(prof)
            functions=[dict(file=f,line=line,name=name,primitive_calls=cc,calls=nc,self_seconds=own,cumulative_seconds=total)
                for (f,line,name),(cc,nc,own,total,callers) in sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:45]]
            profiles.append(dict(split=split,case=index,position=position,mode=mode,trial=study.binding(trial_path),source=cs[position]['source'],root=cs[position]['root'],
                prefix=prefix_binding,extra_ids={t:[k for k,v in prior[t][len(prefix[t]):]] for t in study.TABLES},functions=functions,output_matches_trial=True))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';study.restore(prefix,path);s=priority.ConsequencePrioritySolver(path);original=priority.prefer_ordinary;events=[];acquisitions=[];j=None;depth=0;original_acquire=prepared.acquire
            def observed(solver,cnf,parts):
                nonlocal depth
                entry=None
                if j==position:
                    entry=dict(source=[list(c) for c in cnf],root=study.token(cnf,Counter()),evidence=parts,
                        variables=len({abs(l) for c in cnf for l in c}),widths=dict(Counter(map(len,cnf))),depth=depth);events.append(entry)
                depth+=1
                try:result=original(solver,cnf,parts)
                except BaseException as error:
                    if entry is not None:entry.update(completed=False,error_type=type(error).__name__)
                    raise
                finally:depth-=1
                if entry is not None:
                    entry.update(completed=True,accepted=result is not None)
                    if result is not None:entry.update(answer=result[0] is not None,proof_kind=None if result[1] is None else result[1]['kind'],split_variable=None if result[1] is None else result[1].get('variable'))
                return result
            def acquired(solver,source,budget,**kwargs):
                before=study.tables(solver) if j==position else None
                result=original_acquire(solver,source,budget,**kwargs)
                if before is not None:
                    cnf,_=study.normalize(source);root=study.token(cnf,Counter())
                    acquisitions.append(dict(source=[list(c) for c in source],root=root,prefix=prefix_binding,budget=budget,
                        extra_ids={t:[k for k,value in before[t][len(prefix[t]):]] for t in study.TABLES},
                        target_absent=all(root not in dict(before[t]) for t in study.TABLES),expanded_nodes=result['metrics'].get('expanded_nodes',0),status=result['status']))
                return result
            try:
                with patch.object(priority,'prefer_ordinary',observed),patch.object(prepared,'acquire',acquired):
                    for j,c in enumerate(cs):run_query(s,c,p)
                final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
                trial_path=out/f'{split}-{index}-priority-0/report.json';trial=base.load(trial_path);assert delta==study.read_zip(trial['delta'])
                observations.append(dict(split=split,case=index,position=position,trial=study.binding(trial_path),events=events,acquisitions=acquisitions,output_matches_trial=True))
            finally:s.close()
    matches=[]
    for split in ('controls','novel'):
        for index in (25,31,61):
            arms={m:base.load(out/f'{split}-{index}-{m}-0/report.json') for m in study.MODES}
            for baseline in ('binary1','joint'):
                if study.read_zip(arms[baseline]['delta'])==study.read_zip(arms['priority']['delta']):matches.append(dict(split=split,case=index,baseline=baseline))
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,profiles=profiles,observations=observations,identical_delta_streams=matches,script_sha256=base.sha(__file__),limitations=[
        'Posthoc exposed branch, preceding case61 regression and largest fresh priority query. Instrumented times overlap and do not measure comparative speedups. Every profile and separate observation reproduces frozen native bytes.',
        'Recorded paths bind exact sources and remain independently checked; diagnostic selection events alone are not proof authority. A budget-stopped continuation records completed=false, not a rejected candidate.',
        'Profile prefixes plus listed earlier trial IDs reconstruct persistent availability; replay the exact prior stream for warm pools. The final union is never a benchmark seed.',
        'Only a late-single trigger has been tested, not a generally optimal consequence policy. Full-CNF cofactor recognition may add work or miss a better split. Source recomposition, independent external coverage and general resource bounds remain open.']))
    print(base.encode(dict(selection={k:v for k,v in worst.items() if k!='root'},identical_delta_streams=matches,observations=[dict(split=o['split'],accepted=sum(bool(e.get('accepted')) for e in o['events']),events=len(o['events'])) for o in observations])),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
