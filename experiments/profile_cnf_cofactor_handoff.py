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
from experiments import compare_cnf_cofactor_handoff as study
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import normalize,token
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);streams={};scores=[]
    for mode in ('binary1','bipolar','handoff'):
        for index in (25,31,61):
            streams[index,mode]=[base.load(out/f'novel-{index}-{mode}-{r}/queries.json') for r in range(2)]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            costs={m:sum(r[j]['seconds'] for r in streams[index,m])/2 for m in ('binary1','bipolar','handoff')}
            scores.append(dict(case=index,position=j,variant=c['variant'],root=c['root'],query_seconds=costs,
                extra_seconds=costs['handoff']-costs['bipolar']))
    worst=max(scores,key=lambda r:r['query_seconds']['handoff']);index=worst['case'];position=worst['position']
    selected=[c for c in cases if (c['split'],c['case'])==('novel',index)]
    prefix=study.read_zip(p['prefixes'][str(index)]['archive']);records={}
    with tempfile.TemporaryDirectory() as td:
        for mode in ('binary1','bipolar','handoff'):
            trial_path=out/f'novel-{index}-{mode}-0/report.json';trial=base.load(trial_path)
            expected=study.bound(trial['queries']);path=Path(td)/mode;study.restore(prefix,path)
            s=(study.CofactorHandoffSolver if mode=='handoff' else InputSafeAffineProbeSolver)(path,node_limit=p['node_limit']);rows=[];prof=cProfile.Profile()
            try:
                with ExitStack() as stack:
                    if mode=='binary1':
                        stack.enter_context(patch.object(study.targeted,'inspect_targeted_backbone',partial(study.discover,policy='binary1')))
                    else:
                        stack.enter_context(patch.object(study.targeted.TargetedBackboneMixin,'_expand',study.handoff_expand if mode=='handoff' else study.bipolar_expand))
                    if mode=='handoff':stack.enter_context(patch.object(study.native,'propagate',study.handoff_propagate))
                    for i,c in enumerate(selected):
                        before=study.tables(s)
                        if i==position:
                            prior=before
                            cnf,_,root=s._canonical(c['source']);assert root==c['root'] and s._read(root,cnf) is None
                            prof.enable()
                        if mode=='handoff':
                            with s.handoff_session():r=study.probed(s,c['candidate'],'probe6',p['node_limit'])
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
    # Separate object-graph audit; none of these walks enter the timing samples
    # or function profiles. Active ancestor offers remain charged until return.
    from dataclasses import fields,is_dataclass
    memory=dict(checks=0,max_actual_bytes=0,max_charged_bytes=0,max_live_offers=0)
    from experiments import cnf_clause_partition as partition,cnf_probed_partition as probed_module
    partition_calls=[];query_position=None;original_branches=partition.branch_sources
    def audited_branches(target,missing,counts=None):
        result=original_branches(target,missing,counts)
        partition_calls.append(dict(query_position=query_position,input_sha256=base.key_sha(base.encode([target,missing])),
            result_sha256=base.key_sha(base.encode(result)),source_literals=sum(map(len,target)),branches=len(result[1])))
        return result
    def deep_size(obj,seen):
        if id(obj) in seen:return 0
        seen.add(id(obj));amount=sys.getsizeof(obj)
        if is_dataclass(obj):amount+=sum(deep_size(getattr(obj,f.name),seen) for f in fields(obj))
        elif isinstance(obj,dict):amount+=sum(deep_size(k,seen)+deep_size(v,seen) for k,v in obj.items())
        elif isinstance(obj,(tuple,list)):amount+=sum(deep_size(v,seen) for v in obj)
        return amount
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'audit';study.restore(prefix,path);s=study.CofactorHandoffSolver(path,node_limit=p['node_limit'])
        retain=s._retain_offer;visit=s._visit_offer;clear=s._clear_offer;active=[]
        def inspect_memory():
            live=active+([s._offer] if s._offer is not None else [])
            # The just-selected offer may be present in both audit locations.
            unique=list({id(offer):offer for offer in live}.values());seen=set()
            actual=sum(deep_size(offer,seen) for offer in unique);charged=s._handoff_held
            assert sum(o.charge for o in unique)==charged
            assert actual<=charged<=s.handoff_bytes
            memory['checks']+=1
            memory['max_actual_bytes']=max(actual,memory['max_actual_bytes'])
            memory['max_charged_bytes']=max(charged,memory['max_charged_bytes'])
            memory['max_live_offers']=max(len(unique),memory['max_live_offers'])
        def retain_audited(*args,**kwargs):
            result=retain(*args,**kwargs);inspect_memory();return result
        def visit_audited(offer):
            active.append(offer);inspect_memory()
            try:return visit(offer)
            finally:active.pop();inspect_memory()
        def clear_audited():
            clear();inspect_memory()
        try:
            with patch.object(partition,'branch_sources',audited_branches),patch.object(probed_module,'branch_sources',audited_branches),patch.object(s,'_retain_offer',retain_audited),patch.object(s,'_visit_offer',visit_audited),patch.object(s,'_clear_offer',clear_audited),patch.object(study.targeted.TargetedBackboneMixin,'_expand',study.handoff_expand),patch.object(study.native,'propagate',study.handoff_propagate):
                for query_position,c in enumerate(selected):
                    with s.handoff_session():study.probed(s,c['candidate'],'probe6',p['node_limit'])
                    assert not active and not s._handoff_held
            final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
            assert delta==study.read_zip(study.bound(records['handoff']['trial'])['delta'])
        finally:s.close()
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,records=records,memory_audit=memory,partition_preparation_audit=partition_calls,
        script_sha256=base.sha(__file__),limitations=[
        'Posthoc selection selects the largest handoff query time among the six frozen novel edits; it is not held-out policy-selection evidence.',
        'Each stream restores its frozen prefix. Earlier queries run before the selected query is profiled. Every publication payload, partition and expansion count matches the original trial. No new proof authority is added.',
        'The bound prefix plus extra_ids from trial_report reconstructs the exact persistent pre-query state. The root is checked absent. Warm transient caches and candidate pools also exist after earlier queries; cold restoration alone does not reproduce them.',
        'A separate untimed object-graph walk checks all live offers at admission, selection and cleanup in the selected case stream against their aggregate conservative charge and cap; it reproduces the same proof bytes.',
        'cProfile adds substantial overhead. Cumulative function times overlap and must not be summed. These profiles identify work, not speedups; use the uninstrumented paired trials for performance comparisons.',
        'The separate partition audit hashes complete inputs and produced structures, recording exact duplicate preparation. Hashes are diagnostic only and grant no solver authority.',
        'Use the preserved input to price partition preparation, probe admission and the surviving continuation. A checked deduction by itself does not imply a cheaper surviving search.']))
    print(base.encode(dict(selection=worst,profiles={m:r['total_profiled_seconds'] for m,r in records.items()})),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
