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
from experiments import compare_cnf_binary_interactions as study
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_residual_dag import normalize,token
base=study.base


def profile(out):
    p=base.load(out/'protocol.json');cases=study.bound(p['cases']);streams={};scores=[]
    for mode in ('binary1','binary2'):
        for index in (25,31,61):
            streams[index,mode]=[base.load(out/f'novel-{index}-{mode}-{r}/queries.json') for r in range(2)]
    for index in (25,31,61):
        for j,c in enumerate(c for c in cases if (c['split'],c['case'])==('novel',index)):
            costs={m:sum(r[j]['seconds'] for r in streams[index,m])/2 for m in ('binary1','binary2')}
            scores.append(dict(case=index,position=j,variant=c['variant'],root=c['root'],query_seconds=costs,
                extra_seconds=costs['binary2']-costs['binary1']))
    worst=max(scores,key=lambda r:r['query_seconds']['binary2']);index=worst['case'];position=worst['position']
    selected=[c for c in cases if (c['split'],c['case'])==('novel',index)]
    prefix=study.read_zip(p['prefixes'][str(index)]['archive']);records={}
    with tempfile.TemporaryDirectory() as td:
        for mode in ('binary1','binary2'):
            trial_path=out/f'novel-{index}-{mode}-0/report.json';trial=base.load(trial_path)
            expected=study.bound(trial['queries']);path=Path(td)/mode;study.restore(prefix,path)
            s=InputSafeAffineProbeSolver(path,node_limit=p['node_limit']);rows=[];prof=cProfile.Profile()
            try:
                with ExitStack() as stack:
                    fn=partial(study.first,policy='binary1') if mode=='binary1' else partial(study.second,policy='binary2')
                    stack.enter_context(patch.object(study.targeted,'inspect_targeted_backbone',fn))
                    for i,c in enumerate(selected):
                        before=study.tables(s)
                        if i==position:
                            prior=before
                            cnf,_,root=s._canonical(c['source']);assert root==c['root'] and s._read(root,cnf) is None
                            prof.enable()
                        r=study.prepared_run(s,c['candidate'],'probe6',p['node_limit'])
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
    # Separate diagnostic recognition audit; all evidence is checked against
    # its exact normalized source. These calls do not affect timed profiles.
    from experiments.cnf_binary_backbone import check_path
    evidence=[];position_now=None
    def inspect(cnf,counts):
        before=counts['binary_fallback_second_found'];got=study.second(cnf,counts,policy='binary2')
        if counts['binary_fallback_second_found']>before:
            assert study.first(cnf,Counter(),policy='binary1')==(None,None,None)
            checked=Counter();check_path(cnf,got[2][0],checked)
            evidence.append(dict(query_position=position_now,source=[list(c) for c in cnf],root=token(cnf,Counter()),
                evidence=got[2][0],checker_counts=dict(checked)))
        return got
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'audit';study.restore(prefix,path);s=InputSafeAffineProbeSolver(path,node_limit=p['node_limit'])
        try:
            with patch.object(study.targeted,'inspect_targeted_backbone',inspect):
                for position_now,c in enumerate(selected):study.prepared_run(s,c['candidate'],'probe6',p['node_limit'])
            final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(prefix[t]):]] for t in study.TABLES}
            assert delta==study.read_zip(study.bound(records['binary2']['trial'])['delta'])
        finally:s.close()
    # A posthoc counter ablation isolates crossing the eight-expansion probe
    # boundary. It replays the earlier query, then acquires the replacement
    # directly. Its proof bytes must already exist in the frozen trial delta.
    from experiments.cnf_probed_partition import acquire
    boundary={};boundary_cases=[c for c in cases if (c['split'],c['case'])==('novel',61)]
    boundary_prefix=study.read_zip(p['prefixes']['61']['archive'])
    for mode in ('binary1','binary2'):
        path_report=out/f'novel-61-{mode}-0/report.json';trial=base.load(path_report);expected=study.bound(trial['queries']);trial_delta=study.read_zip(trial['delta'])
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'direct';study.restore(boundary_prefix,path);s=InputSafeAffineProbeSolver(path,node_limit=p['node_limit'])
            try:
                fn=partial(study.first,policy='binary1') if mode=='binary1' else partial(study.second,policy='binary2')
                with patch.object(study.targeted,'inspect_targeted_backbone',fn):
                    initial=study.prepared_run(s,boundary_cases[0]['candidate'],'probe6',p['node_limit'])
                    direct=acquire(s,boundary_cases[1]['source'],p['node_limit'])
                assert initial['partition']==expected[0]['partition'] and initial['expanded_nodes']==expected[0]['expanded_nodes']
                assert direct['result']['root']==expected[1]['result']['root'] and direct['result']['answer']==expected[1]['result']['answer']
                final=study.tables(s);delta={t:[[k,v] for k,v in final[t][len(boundary_prefix[t]):]] for t in study.TABLES}
                for t in study.TABLES:assert all(dict(trial_delta[t]).get(k)==v for k,v in delta[t])
                boundary[mode]=dict(trial=study.binding(path_report),source=boundary_cases[1]['source'],root=direct['result']['root'],
                    direct_expansions=direct['metrics']['expanded_nodes'],wrapped_expansions=expected[1]['expanded_nodes'],
                    initial_probe_expansions=expected[1]['probe']['metrics'].get('expanded_nodes',0),
                    later_expansions=[b['metrics'].get('expanded_nodes',0) for b in expected[1]['branches']],
                    direct_query=direct,delta_ids={t:[k for k,v in rows] for t,rows in delta.items()},all_payloads_in_frozen_trial=True)
            finally:s.close()
    base.write(out/'probe-boundary.json',dict(cases=boundary,limitations=[
        'Posthoc fixed-case count ablation; it is not a fresh timing comparison. The earlier query is replayed to reconstruct transient pools.',
        'Direct acquisition removes the initial eight-expansion stop/restart and support preparation, with the same256 overall budget. All produced native bytes are already present in the independently audited frozen trial deltas.']))
    base.write(out/'next-target.json',dict(selection=worst,candidates=scores,records=records,second_target_evidence=evidence,probe_boundary=study.binding(out/'probe-boundary.json'),
        script_sha256=base.sha(__file__),limitations=[
        'Posthoc selection chooses the largest binary2 query among six frozen new edits, not a held-out policy-selection result.',
        'Each profile restores the bound prefix and replays earlier queries in order; every payload, partition and expansion matches its frozen trial. Extra_ids reconstruct persistent pre-query availability, but not transient warm pools.',
        'The separate recognition audit stores source-indexed paths missed by the first target; the original checker validates them and the audit preserves all trial payloads. A forced literal is not a full source-query decision.',
        'Instrumented times overlap and are not speedups; use paired uninstrumented trials. More recognized consequences may change routing and increase complete cost.',
        'The exposed exploration and signed variants are not broad coverage. Uniform efficient discovery, source composition and arbitrary SAT bounds remain open.']))
    print(base.encode(dict(selection={k:v for k,v in worst.items() if k!='root'},checked_second_targets=len(evidence))),flush=True)


if __name__=='__main__':profile(Path(sys.argv[1]))
