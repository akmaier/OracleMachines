#!/usr/bin/env python3
"""Posthoc profiles and separate graph/construction audits, after timing."""
from collections import Counter
from contextlib import ExitStack
from dataclasses import fields,is_dataclass
from functools import partial
from pathlib import Path
from unittest.mock import patch
import cProfile,pstats,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_preparation as study
from experiments import cnf_partition_preparation as preparation,cnf_clause_partition as partition,cnf_probed_partition as old
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
base=study.base


def contexts(stack,s,mode):
    if mode.startswith('binary'):
        stack.enter_context(patch.object(study.targeted,'inspect_targeted_backbone',partial(study.discover,policy='binary1')))
    else:
        stack.enter_context(patch.object(study.targeted.TargetedBackboneMixin,'_expand',study.handoff_expand))
        stack.enter_context(patch.object(study.native,'propagate',study.handoff_propagate))


def query(s,c,mode,budget):
    fn=preparation.run if mode.endswith('-prepared') else old.run
    if mode.startswith('handoff'):
        with s.handoff_session():return fn(s,c['candidate'],'probe6',budget)
    return fn(s,c['candidate'],'probe6',budget)


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);scores=[]
    for index in (25,31,61):
        streams={m:[base.load(out/f'novel-{index}-{m}-{r}/queries.json') for r in range(2)] for m in study.MODES}
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            costs={m:sum(r[j]['seconds'] for r in streams[m])/2 for m in study.MODES}
            scores.append(dict(case=index,position=j,variant=c['variant'],root=c['root'],query_seconds=costs,
                partitioned=streams['binary-prepared'][0][j]['partition'] is not None))
    largest=max(scores,key=lambda r:r['query_seconds']['binary-prepared'])
    selected=max((r for r in scores if r['partitioned']),key=lambda r:r['query_seconds']['binary-prepared']);index=selected['case'];position=selected['position']
    stream=[c for c in cases if (c['split'],c['case'])==('novel',index)]
    prefix=study.read_zip(p['prefixes'][str(index)]['archive']);records={}
    with tempfile.TemporaryDirectory() as td:
        for mode in study.MODES:
            path=Path(td)/mode;study.restore(prefix,path)
            trial_path=out/f'novel-{index}-{mode}-0/report.json';trial=base.load(trial_path);expected=study.bound(trial['queries'])
            cls=study.CofactorHandoffSolver if mode.startswith('handoff') else InputSafeAffineProbeSolver
            s=cls(path,node_limit=p['node_limit']);prof=cProfile.Profile()
            try:
                with ExitStack() as stack:
                    contexts(stack,s,mode)
                    for j,c in enumerate(stream):
                        before=study.tables(s)
                        if j==position:
                            prior=before;cnf,_,root=s._canonical(c['source']);assert root==c['root'] and s._read(root,cnf) is None
                            prof.enable()
                        r=query(s,c,mode,p['node_limit'])
                        if j==position:prof.disable()
                        final=study.tables(s);ids={t:[k for k,v in final[t][len(before[t]):]] for t in study.TABLES}
                        for field in ('expanded_nodes','status','partition'):assert r[field]==expected[j][field]
                        assert ids==expected[j]['new_ids']
            finally:s.close()
            delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
            assert delta==study.read_zip(trial['delta'])
            extra={t:[[k,v] for k,v in prior[t][len(prefix[t]):]] for t in study.TABLES};assert not any(extra[t] for t in study.TABLES[1:])
            stats=pstats.Stats(prof);functions=[]
            for (file,line,name),(cc,nc,own,total,callers) in sorted(stats.stats.items(),key=lambda kv:kv[1][3],reverse=True)[:45]:
                functions.append(dict(file=file,line=line,name=name,primitive_calls=cc,calls=nc,self_seconds=own,cumulative_seconds=total))
            records[mode]=dict(trial=study.binding(trial_path),trial_report=study.binding(trial_path),source=stream[position]['source'],root=stream[position]['root'],
                prefix=p['prefixes'][str(index)]['archive'],extra_ids=[k for k,v in extra[study.TABLES[0]]],extra_count=len(extra[study.TABLES[0]]),
                profiled_query_position=position,query_summary=dict(expanded_nodes=expected[position]['expanded_nodes'],route=expected[position]['route'],
                    probe_expansions=0 if expected[position]['probe'] is None else expected[position]['probe']['metrics'].get('expanded_nodes',0),
                    branch_expansions=[b['metrics'].get('expanded_nodes',0) for b in expected[position]['branches']],
                    branch_seconds=[b['seconds'] for b in expected[position]['branches']]),functions=functions,total_profiled_seconds=stats.total_tt,output_matches_frozen_trial=True)
    # Untimed diagnostic graph walks, separate from all function profiles.
    audits={};original_build=partition.branch_sources;original_prepare=preparation.prepare
    def deep_size(obj,seen):
        if id(obj) in seen:return 0
        seen.add(id(obj));n=sys.getsizeof(obj)
        if is_dataclass(obj):n+=sum(deep_size(getattr(obj,f.name),seen) for f in fields(obj))
        elif isinstance(obj,dict):n+=sum(deep_size(k,seen)+deep_size(v,seen) for k,v in obj.items())
        elif isinstance(obj,(list,tuple,set,frozenset)):n+=sum(deep_size(x,seen) for x in obj)
        return n
    for mode in ('binary1','binary-prepared'):
        observations=[];j=None
        def old_build(source,missing,counts=None):
            ordered,branches=original_build(source,missing,counts)
            observations.append(dict(query_position=j,kind='reconstructed',input_sha256=base.key_sha(base.encode([source,missing])),
                result_sha256=base.key_sha(base.encode((ordered,branches))),branches=len(branches),
                retained_graph_bytes=deep_size((source,missing,ordered,branches),set())))
            return ordered,branches
        def new_build(source,missing,counts):
            prepared=original_prepare(source,missing,counts)
            comparable=(prepared.ordered,[(a,dict(b),c) for a,b,c in prepared.branches]);actual=deep_size(prepared,set())
            assert actual<=counts['partition_prepared_charge']
            observations.append(dict(query_position=j,kind='prepared',input_sha256=base.key_sha(base.encode([source,missing])),
                result_sha256=base.key_sha(base.encode(comparable)),branches=len(prepared.branches),retained_graph_bytes=actual,
                conservative_charge=counts['partition_prepared_charge']))
            return prepared
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'audit';study.restore(prefix,path);s=InputSafeAffineProbeSolver(path,node_limit=p['node_limit'])
            try:
                with ExitStack() as stack:
                    contexts(stack,s,mode)
                    stack.enter_context(patch.object(partition,'branch_sources',old_build));stack.enter_context(patch.object(old,'branch_sources',old_build))
                    stack.enter_context(patch.object(preparation,'prepare',new_build))
                    for j,c in enumerate(stream):query(s,c,mode,p['node_limit'])
                final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
                assert delta==study.read_zip(study.bound(records[mode]['trial'])['delta'])
            finally:s.close()
        audits[mode]=observations
    for j in range(len(stream)):
        left=[r for r in audits['binary1'] if r['query_position']==j];right=[r for r in audits['binary-prepared'] if r['query_position']==j]
        if not left:
            assert not right;continue
        assert len(left)==4 and len(right)==2
        assert [r['kind'] for r in right]==['prepared','reconstructed']
        assert len({r['input_sha256'] for r in left+right})==len({r['result_sha256'] for r in left+right})==1
    # Save the exact persistent state before the dominant branch is acquired,
    # not the final trial state containing its answer.
    from experiments.cnf_snapshot_replay import SnapshotResidualSolver
    mode='binary-prepared';trial=study.bound(records[mode]['trial']);expected=study.bound(trial['queries'])
    branch_index=max(range(len(expected[position]['branches'])),key=lambda i:expected[position]['branches'][i]['seconds'])
    wanted_call=(1 if expected[position]['probe'] is not None else 0)+branch_index
    original_acquire=preparation.acquire;calls=0;captured=None;before_branch=None
    class StopBeforeBranch(Exception):pass
    def capture(s,source,budget,**kwargs):
        nonlocal calls,captured,before_branch
        ordinal=calls;calls+=1
        if ordinal!=wanted_call:return original_acquire(s,source,budget,**kwargs)
        cnf,names,root=s._canonical(source)
        assert s._read(root,cnf) is None and not s.db.pending and not s.db.in_transaction
        assert root==expected[position]['partition']['children'][branch_index]['root']
        before_branch=study.tables(s)
        captured=dict(source=[list(c) for c in source],root=root,parent_query_root=selected['root'],case=index,query_position=position,
            branch_index=branch_index,budget_remaining=budget,
            variables=len(names),clause_lengths=dict(Counter(map(len,cnf))),literals=sum(map(len,cnf)),
            selection='Largest branch acquisition time in the first binary-prepared trial of the selected query',
            measured_seconds=expected[position]['branches'][branch_index]['seconds'],
            expanded_nodes=expected[position]['branches'][branch_index]['metrics'].get('expanded_nodes',0))
        raise StopBeforeBranch
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'branch';study.restore(prefix,path);s=InputSafeAffineProbeSolver(path,node_limit=p['node_limit'])
        try:
            with ExitStack() as stack:
                contexts(stack,s,mode)
                for j,c in enumerate(stream):
                    if j<position:query(s,c,mode,p['node_limit']);continue
                    with patch.object(preparation,'acquire',capture):
                        try:query(s,c,mode,p['node_limit'])
                        except StopBeforeBranch:pass
                        else:raise AssertionError('Branch capture was not reached')
                    break
            assert captured is not None
            extra={t:[[k,v] for k,v in before_branch[t][len(prefix[t]):]] for t in study.TABLES}
            final_delta=study.read_zip(trial['delta'])
            assert not any(extra[t] for t in study.TABLES[1:])
            for t in study.TABLES:assert all(dict(final_delta[t]).get(k)==v for k,v in extra[t])
        finally:s.close()
        fresh=SnapshotResidualSolver(path)
        try:
            for k,v in extra[study.TABLES[0]]:assert fresh._read(k) is not None
            assert fresh._read(captured['root']) is None
            captured.update(prefix=p['prefixes'][str(index)]['archive'],trial_report=records[mode]['trial'],
                extra_ids=[k for k,v in extra[study.TABLES[0]]],extra_count=len(extra[study.TABLES[0]]),
                fresh_reader_counts=dict(fresh.counts),target_absent=True)
        finally:fresh.close()
    base.write(out/'next-target.json',dict(selection=selected,largest_new_query=largest,candidates=scores,records=records,preparation_audit=audits,branch_candidate=captured,
        script_sha256=base.sha(__file__),limitations=[
        'Posthoc selection chooses the largest partitioned binary-prepared query time among six frozen new edits; the largest overall query is also recorded. It is not held-out policy-selection evidence.',
        'Profiles restore exact prefixes and earlier stream queries. Every native delta, partition and expansion matches its frozen trial. Bound extra_ids reconstruct persistent pre-query state, but not warm transient caches.',
        'Independent object-graph audits run after the profiles and are not part of comparative timings. Graph sizes compare one returned preparation at a time, not simultaneous peak process memory; accounting/control objects and construction transients are excluded.',
        'Complete input and output hashes confirm duplicate structures diagnostically and grant no authority. The independent checker always reconstructs and validates sidecars.',
        'cProfile overhead and overlapping cumulative times prevent interpreting instrumented times as speedups. Use the uninstrumented paired trials.',
        'The branch candidate is captured before acquisition; its extra rows are matched to the trial delta and checked by a fresh reader. Exact persistent availability is reproducible, while warm transient caches are not serialized.',
        'Sharing construction cannot improve the complexity of arbitrary unresolved branches. Probe admission, source-level discovery, compact sidecars and cold replay remain open.']))
    print(base.encode(dict(selection={k:v for k,v in selected.items() if k!='root'},audits={m:len(v) for m,v in audits.items()})),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
