#!/usr/bin/env python3
"""Posthoc single-selected ablation and source-bound joint cost profiles."""
from collections import Counter
from functools import partial
from pathlib import Path
from unittest.mock import patch
import cProfile,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_backbone as study,cnf_joint_backbone as joint
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
base=study.base


def run_query(s,c,p):
    if study.native_split(c['split']):return study.harness.query(s,c,'native',p['branch_limit'])
    return study.previous.previous.prepared_run(s,c['candidate'],'probe6',p['node_limit'])


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);exploration=study.bound(p['exploration']);spec=exploration['spec']
    prefix=study.seed(spec)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'ablation';study.restore(prefix,path);s=joint.SingleFromJointSolver(path)
        try:
            assert s._read(spec['root']) is None
            r=acquire(s,spec['source'],p['branch_limit']);final=study.tables(s)
            delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
        finally:s.close()
        rd=SnapshotResidualSolver(path)
        try:
            for key,v in delta[study.TABLES[0]]:assert rd._read(key) is not None
            assert rd._read(spec['root'])['answer']==r['result']['answer']
        finally:rd.close()
    base.write(out/'ablation-query.json',r);archive=study.write_zip(out/'ablation-delta.json.gz',delta)
    base.write(out/'ablation.json',dict(spec=spec,query=study.binding(out/'ablation-query.json'),delta=archive,script_sha256=base.sha(__file__),limitations=[
        'Posthoc exposed count ablation uses the same discovery but only the first selected path at each node. Subsequent residuals/discovery may differ. This is not a fresh paired timing comparison.',
        'All emitted native evidence is independently checked and merged by the cumulative audit; the final union is never seeded.']))
    scores=[]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            times={m:sum(base.load(out/f'novel-{index}-{m}-{i}/queries.json')[j]['seconds'] for i in range(2))/2 for m in study.MODES}
            scores.append(dict(case=index,position=j,root=c['root'],variant=c['variant'],query_seconds=times))
    worst=max(scores,key=lambda r:r['query_seconds']['joint']);profiles=[];observations=[]
    for split,index,position in (('branch-original',31,0),('novel',worst['case'],worst['position'])):
        cs=[c for c in cases if (c['split'],c['case'])==(split,index)]
        prefix=study.read_zip(p['prefixes'][split if study.native_split(split) else str(index)]['archive'])
        for mode in study.MODES:
            trial_path=out/f'{split}-{index}-{mode}-0/report.json';trial=base.load(trial_path);expected=study.bound(trial['queries'])
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';study.restore(prefix,path);s=(joint.JointBackboneSolver if mode=='joint' else InputSafeAffineProbeSolver)(path);prof=cProfile.Profile()
                kernel=study.previous.previous;fn=partial(kernel.second,policy='binary2') if mode=='binary2' else partial(kernel.first,policy='binary1')
                try:
                    with patch.object(kernel.targeted,'inspect_targeted_backbone',fn):
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
                prefix=p['prefixes'][split if study.native_split(split) else str(index)]['archive'],extra_ids={t:[k for k,v in prior[t][len(prefix[t]):]] for t in study.TABLES},
                functions=functions,output_matches_trial=True))
        # A separate proof-evidence census avoids including observer allocations
        # in either comparative timing or the function profiles.
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';study.restore(prefix,path);s=joint.JointBackboneSolver(path);original=joint.force_all;events=[];j=None
            def observed(solver,cnf,evidence):
                entry=None
                if j==position:
                    entry=dict(source=[list(c) for c in cnf],root=study.token(cnf,Counter()),evidence=evidence,
                        variables=len({abs(l) for c in cnf for l in c}),widths=dict(Counter(map(len,cnf))),
                        path_steps=sum(len(e['path']) for e in evidence));events.append(entry)
                result=original(solver,cnf,evidence)
                if entry is not None:entry['answer']=result[0] is not None
                return result
            try:
                with patch.object(joint,'force_all',observed):
                    for j,c in enumerate(cs):run_query(s,c,p)
                final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
                trial_path=out/f'{split}-{index}-joint-0/report.json';trial=base.load(trial_path);assert delta==study.read_zip(trial['delta'])
                observations.append(dict(split=split,case=index,position=position,trial=study.binding(trial_path),events=events,output_matches_trial=True))
            finally:s.close()
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,profiles=profiles,observations=observations,ablation=study.binding(out/'ablation.json'),script_sha256=base.sha(__file__),limitations=[
        'Posthoc exposed branch and largest new joint query, chosen after the frozen comparison. Profile outputs and separate evidence-census native bytes match the exact frozen streams.',
        'Instrumented times overlap and are not comparative speedups. Recorded source-indexed paths are checked independently and are not complete source-query decisions by themselves.',
        'The profile prefix plus earlier trial IDs reconstruct persistent availability, not warm pools. The exact source and prior stream are retained for further work.',
        'The current filter is directional; later consequences may imply earlier ones. Recognition, proof amplification and adaptive context costs remain explicit. No general independent-basis or arbitrary-SAT efficiency result is claimed.']))
    print(base.encode(dict(ablation_expansions=base.load(out/'ablation-query.json')['metrics']['expanded_nodes'],selection={k:v for k,v in worst.items() if k!='root'},events=[dict(split=o['split'],sizes=[len(e['evidence']) for e in o['events']]) for o in observations])),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
