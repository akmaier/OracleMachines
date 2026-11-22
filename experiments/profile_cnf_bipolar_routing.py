#!/usr/bin/env python3
"""Posthoc cost attribution; never use instrumented time as comparative time."""
from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from functools import partial
from pathlib import Path
from unittest.mock import patch
import cProfile,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bipolar_routing as study
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import normalize,token
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);streams={};scores=[]
    for mode in ('binary1','bipolar'):
        for index in (25,31,61):
            streams[index,mode]=[base.load(out/f'novel-{index}-{mode}-{r}/queries.json') for r in range(2)]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            costs={m:sum(r[j]['seconds'] for r in streams[index,m])/2 for m in ('binary1','bipolar')}
            scores.append(dict(case=index,position=j,variant=c['variant'],root=c['root'],query_seconds=costs,
                extra_seconds=costs['bipolar']-costs['binary1']))
    worst=max(scores,key=lambda r:r['extra_seconds']);index=worst['case'];position=worst['position']
    selected=[c for c in cases if (c['split'],c['case'])==('novel',index)]
    prefix=study.read_zip(p['prefixes'][str(index)]['archive']);records={}
    with tempfile.TemporaryDirectory() as td:
        for mode in ('binary1','bipolar'):
            trial_path=out/f'novel-{index}-{mode}-0/report.json';trial=base.load(trial_path)
            expected=study.bound(trial['queries']);path=Path(td)/mode;study.restore(prefix,path)
            s=InputSafeAffineProbeSolver(path,node_limit=p['node_limit']);rows=[];prof=cProfile.Profile()
            try:
                with ExitStack() as stack:
                    if mode=='binary1':stack.enter_context(patch.object(study.targeted,'inspect_targeted_backbone',partial(study.discover,policy='binary1')))
                    else:stack.enter_context(patch.object(study.targeted.TargetedBackboneMixin,'_expand',study.bipolar_expand))
                    for i,c in enumerate(selected):
                        before=study.tables(s)
                        if i==position:
                            prior=before
                            cnf,_,root=s._canonical(c['source']);assert root==c['root'] and s._read(root,cnf) is None
                            prof.enable()
                        r=study.probed(s,c['candidate'],'probe6',p['node_limit'])
                        if i==position:prof.disable()
                        final=study.tables(s);ids={t:[k for k,v in final[t][len(before[t]):]] for t in study.TABLES}
                        for field in ('expanded_nodes','status','partition'):assert r[field]==expected[i][field]
                        assert ids==expected[i]['new_ids'];rows.append(r)
            finally:s.close()
            delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
            assert delta==study.read_zip(trial['delta'])
            extra={t:[[k,v] for k,v in prior[t][len(prefix[t]):]] for t in study.TABLES}
            assert all(not extra[t] for t in study.TABLES[1:])
            stats=pstats.Stats(prof);ordered=sorted(stats.stats.items(),key=lambda pair:pair[1][3],reverse=True)
            functions=[]
            for (file,line,name),(cc,nc,own,total,callers) in ordered[:40]:
                functions.append(dict(file=file,line=line,name=name,primitive_calls=cc,calls=nc,self_seconds=own,cumulative_seconds=total))
            records[mode]=dict(trial=study.binding(trial_path),source=selected[position]['source'],root=selected[position]['root'],
                prefix=p['prefixes'][str(index)]['archive'],trial_report=study.binding(trial_path),
                extra_ids=[k for k,v in extra[study.TABLES[0]]],extra_count=len(extra[study.TABLES[0]]),
                profiled_query_position=position,functions=functions,total_profiled_seconds=stats.total_tt,
                output_matches_frozen_trial=True)
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,records=records,
        script_sha256=base.sha(__file__),limitations=[
        'Posthoc selection maximizes the two-polarity query-time regression against binary1 among the six frozen novel edits; it is not held-out policy-selection evidence.',
        'Each stream restores its frozen prefix. Earlier queries run before the selected query is profiled. Every publication payload, partition and expansion count matches the original trial. No new proof authority is added.',
        'The bound prefix plus extra_ids from trial_report reconstructs the exact persistent pre-query state. The root is checked absent. Warm transient caches and candidate pools also exist after earlier queries; cold restoration alone does not reproduce them.',
        'cProfile adds substantial overhead. Cumulative function times overlap and must not be summed. These profiles identify work, not speedups; use the uninstrumented paired trials for performance comparisons.',
        'Use the preserved input to test cheaper admission or propagation reuse. A checked deduction by itself does not imply a cheaper surviving search.']))
    print(base.encode(dict(selection=worst,profiles={m:r['total_profiled_seconds'] for m,r in records.items()})),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
