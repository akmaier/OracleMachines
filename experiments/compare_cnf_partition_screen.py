#!/usr/bin/env python3
"""Fresh matched single-clause reuse versus bounded multi-clause screening."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_premise_guard as previous
from experiments import compare_cnf_clause_partition as partition_study
from experiments.cnf_partition_screen import PartitionScreen,publish_screened_branch
from experiments.cnf_clause_partition import branch_sources,publish_premise,make_record as partition_record,check_record as check_partition,PartitionBank,FORMAT as PARTITION_FORMAT
from experiments.cnf_guard_chain import make_record as chain_record,check_record as check_chain,GuardChainBank
from experiments.cnf_premise_guard import PremiseGuardSelector
from experiments.cnf_incremental_archive import ResidualAppendCursor
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.validate_cnf_unsat_support import bound
base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-clause-partition');FIELDS=previous.FIELDS;OLD_FIELDS=previous.OLD_FIELDS
MODES=('single','screened')
FILES=('experiments/cnf_partition_screen.py','solver/test_cnf_partition_screen.py','experiments/compare_cnf_partition_screen.py','experiments/validate_cnf_partition_screen.py')


def inherited(parent):
    return bound(parent['guard_chain_decisions'])+bound(parent['premise_guard_chain_decisions'])+bound(parent['clause_partition_decisions'])


def banks(s,records):
    return [GuardChainBank(s,[r for r in records if r['format']!=PARTITION_FORMAT]),PartitionBank(s,[r for r in records if r['format']==PARTITION_FORMAT])]


def lookup(retained,source):
    for bank in retained:
        result=bank.lookup(source)
        if result is not None:return result
    return None


def audit_records(path,records,prepared,catalogs,indices):
    tick=time.perf_counter();native=previous.ordinary.audit_portfolio(path,[],prepared,catalogs,indices);s=SnapshotResidualSolver(path)
    try:
        answers=[(check_partition if r['format']==PARTITION_FORMAT else check_chain)(s,r)['answer'] for r in records];retained=banks(s,records)
        assert [lookup(retained,r['source'])['answer'] for r in records]==answers
    finally:s.close()
    return dict(native=native,answers=answers,seconds=time.perf_counter()-tick)


def exclusions(parent):
    records=sum((bound(parent[f]) for f in FIELDS),[])+inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in records})]


def worker(out,p,catalog,mode):
    out.mkdir();start=time.perf_counter();parent=bound(p['parent']);old_records=inherited(parent);records=[];warm=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'proofs';base.restore_archive(parent['reference_union'],path);s=previous.ordinary.AccountedResidualSolver(path,node_limit=p['node_limit']);initial=rows(s);cursor=ResidualAppendCursor(s)
        try:
            tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Preparation search')):
                bank,extensions,indices,prepared,cofactors=previous.setup(s,p);cores=prepared['cores'];selector=previous.ordinary.AlternativeGuardSelector(p['alternative_budget'])
                retained=banks(s,old_records);near=PremiseGuardSelector(cores);screen=PartitionScreen(cores,p['plan_limit'],p['core_read_limit']) if mode=='screened' else None
            prepare_seconds=time.perf_counter()-tick;near_setup_counts=dict(near.counts);screen_setup_counts={} if screen is None else dict(screen.counts);assert not cursor.take();setup_seconds=time.perf_counter()-start
            for case in catalog['cases']:
                tick=time.perf_counter();s.counts=Counter();source=case['source'];assert lookup(retained,source) is None
                target,normal,normal_counts=previous.prepare(s,source,p,bank,extensions,cofactors,selector);early=cursor.take();guards=[] if normal['guard'] is None else [normal['guard']]
                choice=None;plan=None;screen_trace=None;near_counts=Counter();screen_counts=Counter();extra_start=time.perf_counter();before=Counter(s.counts)
                eligible=normal['guard'] is not None and not normal['target_known'] and normal['cofactor'] is None
                if eligible:
                    with patch.object(s,'_expand',side_effect=AssertionError('Near-premise search')):
                        old=Counter(near.counts);choice,guard,target=near.select(s,target);near_counts.update(near.counts-old)
                        if guard is not None:guards.append(guard)
                near_seconds=time.perf_counter()-extra_start;near_solver_counts=dict(s.counts-before);screen_seconds=0.;screen_solver_counts={}
                if eligible and choice is None and screen is not None:
                    extra_start=time.perf_counter();before=Counter(s.counts);old=Counter(screen.counts)
                    with patch.object(s,'_expand',side_effect=AssertionError('Screen search')),patch.object(s,'_store',side_effect=AssertionError('Screen publication')):plan,screen_trace=screen.select(s,target)
                    screen_seconds=time.perf_counter()-extra_start;screen_counts.update(screen.counts-old);screen_solver_counts=dict(s.counts-before)
                premise_counts=Counter();premise_solver_counts={};premise_inserted=False;premise_seconds=0.;children=[];construction_counts=Counter();construction_seconds=0.
                if plan is None:children=[s.solve(target)]
                else:
                    phase=time.perf_counter();before=Counter(s.counts)
                    with patch.object(s,'_expand',side_effect=AssertionError('Premise search')):premise_inserted,root=publish_premise(s,target,cores[plan['core']],plan['missing'],premise_counts)
                    premise_seconds=time.perf_counter()-phase;premise_solver_counts=dict(s.counts-before);phase=time.perf_counter();branches=branch_sources(target,plan['missing'],construction_counts)[1];construction_seconds=time.perf_counter()-phase
                    for (_,_,child_source),trace in zip(branches,plan['branches']):
                        child=publish_screened_branch(s,child_source,trace);children.append(child)
                        if child['answer']:break
                phase=time.perf_counter();record=chain_record(s,source,guards,children[0]) if plan is None else partition_record(s,source,guards,plan['missing'],root,children);composition_seconds=time.perf_counter()-phase;added=cursor.take()
                records.append(dict(case=case['case'],template_case=case['template_case'],record=record,ordinary=normal,eligible=eligible,choice=choice,screen=screen_trace,plan=plan,
                    early_ids=sorted(map(base.key_sha,early)),new_ids=sorted(map(base.key_sha,list(early)+list(added))),new_nodes=len(early)+len(added),children=children,
                    normal_counts=dict(normal_counts),near_counts=dict(near_counts),near_solver_counts=near_solver_counts,screen_counts=dict(screen_counts),screen_solver_counts=screen_solver_counts,
                    premise_counts=dict(premise_counts),premise_solver_counts=premise_solver_counts,premise_inserted=premise_inserted,construction_counts=dict(construction_counts),
                    near_seconds=near_seconds,screen_seconds=screen_seconds,premise_seconds=premise_seconds,construction_seconds=construction_seconds,composition_seconds=composition_seconds,seconds=time.perf_counter()-tick))
            tick=time.perf_counter();retained=banks(s,old_records+[r['record'] for r in records]);warm_setup_seconds=time.perf_counter()-tick
            with patch.object(s,'_expand',side_effect=AssertionError('Warm search')),patch.object(s,'_store',side_effect=AssertionError('Warm publication')):
                for case in catalog['cases']:
                    tick=time.perf_counter();answer=lookup(retained,case['source']);assert answer is not None;warm.append(dict(case=case['case'],result=answer,seconds=time.perf_counter()-tick))
            assert not cursor.take();final=rows(s);assert initial.items()<=final.items();census=s.archive_storage()
        except BaseException:
            s.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:s.close()
        used=[(n,bound(parent[n])) for n in OLD_FIELDS];cold=audit_records(path,[r['record'] for r in records]+old_records,prepared,used,indices)
        tick=time.perf_counter();base.write(out/'queries.json',records);base.write(out/'warm.json',warm);serialization_seconds=time.perf_counter()-tick;archive=base.archive(path,out)
    metrics=Counter()
    for r in records:
        for c in r['children']:metrics.update(c['metrics'])
    summary=dict(mode=mode,queries=len(records),positive=sum(r['record']['answer'] for r in records),new_nodes=len(final)-len(initial),nodes=len(final),new_payload_units=sum(len(k)+len(v) for k,v in final.items() if k not in initial),
        expanded_nodes=metrics['expanded_nodes'],trace_publications=metrics['screen_trace_publications'],traces_reused=metrics['screen_traces_reused'],eligible=sum(r['eligible'] for r in records),extra_guards=sum(r['choice'] is not None for r in records),
        screen_calls=sum(r['screen'] is not None for r in records),screen_plans=sum(len(r['screen']['attempts']) for r in records if r['screen'] is not None),partitions=sum(r['plan'] is not None for r in records),partition_premise_publications=sum(r['premise_inserted'] for r in records),
        setup_seconds=setup_seconds,prepare_seconds=prepare_seconds,query_seconds=sum(r['seconds'] for r in records),screen_seconds=sum(r['screen_seconds'] for r in records),warm_setup_seconds=warm_setup_seconds,warm_query_seconds=sum(r['seconds'] for r in warm),serialization_seconds=serialization_seconds,cold_seconds=cold['seconds'],compression_seconds=archive['seconds'],
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],sidecar_bytes=sum((out/f).stat().st_size for f in ('queries.json','warm.json')),row_digest=base.key_sha(base.encode(sorted(final.items()))),repeat_new_nodes=0,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
    result=dict(summary=summary,queries=binding(out/'queries.json'),warm=binding(out/'warm.json'),archive=archive,cold=cold,near_setup_counts=near_setup_counts,near_counts=dict(near.counts),screen_setup_counts=screen_setup_counts,screen_counts={} if screen is None else dict(screen.counts),child_metrics=dict(metrics),census=census,cursor_counts=dict(cursor.stats))
    base.write(out/'report.json',result);result['summary']['complete_worker_seconds']=time.perf_counter()-start;base.write(out/'report.json',result)


def run(out):
    out.mkdir(exist_ok=False);parent=base.load(PARENT/'checkpoint.json');old=base.load('experiments/results/cnf-premise-guard/protocol.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});base.write(out/'previous-decisions.json',exclusions(parent))
    p=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['extended_support_proposals'],causal_index=parent['causal_support_proposals'],template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        node_limit=100000,alternative_budget=1,per_template=64,plan_limit=4,core_read_limit=8,orders=[MODES,MODES[::-1]],
        limitations=['192 fresh neighbouring inputs exclude all inherited ordinary, chain and partition sidecars plus native roots. Two reversed-order pairs, separate processes, no concurrent tests/builds/profiles; no generalization beyond this generator.',
            'Both arms repeat ordinary preparation and premise-first one-clause selection. Screening runs only after both miss. Prepared overlapping cores missing two/three clauses are ranked by missing count and bank position, with at most eight checked core reads and four forward/reverse plans. Posting discovery and sorting are not bounded by the plan limit.',
            'Gate: all branches conflict by unit propagation, or at least two conflict and exactly one remaining residual has fewer literals than the propagated baseline. Rank by remaining count, residual literals, branch count, core position and order. Heuristic, no minimum-cost or universal gain guarantee.',
            'Retained forced prefixes/conflicts publish native checked proofs. Remaining residuals use the frozen solver. Trace publication avoids some expanded_nodes increments without removing materialized proofs: screening, trace checking, publications and total rows are charged separately.',
            'Warm banks and full cold native, sidecar and support-lineage audits are charged. Original bank acquisition remains an inherited cost. No native schema change, unrestricted-SAT or new formal resource claim. Compact previous-decisions file stores exclusion roots only; original catalogs remain bound by the parent checkpoint.'])
    base.write(out/'protocol.json',p);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(parent['reference_union'],path);s=ResidualSolver(path)
        try:catalog=previous.ordinary.eager.previous.inputs(s,p)
        finally:s.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']));samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True,stdout=subprocess.DEVNULL);samples.append(dict(repeat=repeat,mode=mode,**binding(dest/'report.json')));print(mode,repeat,flush=True)
    summary={}
    for mode in MODES:
        data=[bound(e)['summary'] for e in samples if e['mode']==mode];a=data[0];timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in data[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(x[k] for x in data)/len(data) for k in timed},'sidecar_bytes':[x['sidecar_bytes'] for x in data]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary));print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
