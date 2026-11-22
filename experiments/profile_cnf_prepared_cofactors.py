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
from experiments import compare_cnf_prepared_cofactors as study
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import normalize,token
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);streams={};scores=[]
    for mode in ('bipolar','prepared'):
        for index in (25,31,61):
            streams[index,mode]=[base.load(out/f'novel-{index}-{mode}-{r}/queries.json') for r in range(2)]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            costs={m:sum(r[j]['seconds'] for r in streams[index,m])/2 for m in ('bipolar','prepared')}
            scores.append(dict(case=index,position=j,variant=c['variant'],root=c['root'],query_seconds=costs,
                extra_seconds=costs['prepared']-costs['bipolar']))
    worst=max(scores,key=lambda r:r['query_seconds']['prepared']);index=worst['case'];position=worst['position']
    selected=[c for c in cases if (c['split'],c['case'])==('novel',index)]
    prefix=study.read_zip(p['prefixes'][str(index)]['archive']);records={}
    with tempfile.TemporaryDirectory() as td:
        for mode in ('bipolar','prepared'):
            trial_path=out/f'novel-{index}-{mode}-0/report.json';trial=base.load(trial_path)
            expected=study.bound(trial['queries']);path=Path(td)/mode;study.restore(prefix,path)
            s=(study.PreparedCofactorSolver if mode=='prepared' else InputSafeAffineProbeSolver)(path,node_limit=p['node_limit']);rows=[];prof=cProfile.Profile()
            try:
                with ExitStack() as stack:
                    stack.enter_context(patch.object(study.targeted.TargetedBackboneMixin,'_expand',study.bipolar_expand))
                    if mode=='prepared':stack.enter_context(patch.object(study.bipolar,'probe_child',study.prepared_probe_child))
                    for i,c in enumerate(selected):
                        before=study.tables(s)
                        if i==position:
                            prior=before
                            cnf,_,root=s._canonical(c['source']);assert root==c['root'] and s._read(root,cnf) is None
                            prof.enable()
                        if mode=='prepared':
                            with s.cofactor_session():r=study.probed(s,c['candidate'],'probe6',p['node_limit'])
                        else:r=study.probed(s,c['candidate'],'probe6',p['node_limit'])
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
    # Separate untimed admission audit. This graph walk is not in any timing
    # sample or the function profiles above. The memo confers no proof authority.
    memory=dict(checks=0,max_actual_bytes=0,max_charged_bytes=0);probe_census=[]
    def deep_size(obj,seen):
        if id(obj) in seen:return 0
        seen.add(id(obj));amount=sys.getsizeof(obj)
        if isinstance(obj,dict):amount+=sum(deep_size(k,seen)+deep_size(v,seen) for k,v in obj.items())
        elif isinstance(obj,(tuple,list)):amount+=sum(deep_size(v,seen) for v in obj)
        return amount
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'audit';study.restore(prefix,path);s=study.PreparedCofactorSolver(path,node_limit=p['node_limit'])
        original=s._note_cofactors;original_propagate=study.bipolar.propagate
        def inspect_probe(cnf,counts):
            fixed,trace,conflict=original_propagate(cnf,counts)
            units=sum(len(c)==1 for c in cnf);empty=any(not c for c in cnf)
            if not units and not empty:assert not fixed and not trace and conflict is None
            probe_census.append(dict(clauses=len(cnf),literals=sum(map(len,cnf)),initial_units=units,empty_clause=empty,fixed=len(fixed),conflict=conflict is not None,literal_visits=counts.get('propagation_literal_visits',0)))
            return fixed,trace,conflict
        def check_memory():
            original();actual=deep_size(s._cofactors,set());charged=sys.getsizeof(s._cofactors)+s._cofactor_payload
            assert actual<=charged<=s.cofactor_bytes
            memory['checks']+=1;memory['max_actual_bytes']=max(actual,memory['max_actual_bytes']);memory['max_charged_bytes']=max(charged,memory['max_charged_bytes'])
        try:
            with patch.object(study.bipolar,'propagate',inspect_probe),patch.object(s,'_note_cofactors',check_memory),patch.object(study.targeted.TargetedBackboneMixin,'_expand',study.bipolar_expand),patch.object(study.bipolar,'probe_child',study.prepared_probe_child):
                for c in selected:
                    with s.cofactor_session():study.probed(s,c['candidate'],'probe6',p['node_limit'])
            final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
            assert delta==study.read_zip(study.bound(records['prepared']['trial'])['delta'])
        finally:s.close()
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,records=records,memory_audit=memory,probe_census=probe_census,
        script_sha256=base.sha(__file__),limitations=[
        'Posthoc selection selects the largest prepared-cofactor query time among the six frozen novel edits; it is not held-out policy-selection evidence.',
        'Each stream restores its frozen prefix. Earlier queries run before the selected query is profiled. Every publication payload, partition and expansion count matches the original trial. No new proof authority is added.',
        'The bound prefix plus extra_ids from trial_report reconstructs the exact persistent pre-query state. The root is checked absent. Warm transient caches and candidate pools also exist after earlier queries; cold restoration alone does not reproduce them.',
        'A separate untimed object-graph walk checks each memo admission in the selected case stream against the conservative charge and cap; it reproduces the same proof bytes.',
        'cProfile adds substantial overhead. Cumulative function times overlap and must not be summed. These profiles identify work, not speedups; use the uninstrumented paired trials for performance comparisons.',
        'Use the preserved input to price narrower lookup, probe admission or propagation reuse. A checked deduction by itself does not imply a cheaper surviving search.']))
    print(base.encode(dict(selection=worst,profiles={m:r['total_profiled_seconds'] for m,r in records.items()})),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
