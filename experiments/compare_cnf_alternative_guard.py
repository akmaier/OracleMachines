#!/usr/bin/env python3
"""Matched bounded alternative guards after a first-target reuse miss."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_causal as previous
from experiments.cnf_accounted_residuals import AccountedResidualSolver,CENSUS
from experiments.cnf_incremental_archive import ResidualAppendCursor
from experiments.cnf_unsat_support import CoreBank
from experiments.cnf_clause_deletion_guard import ExtensionBank,propose,check_guard,lift
from experiments.cnf_clause_witness_reuse import reuse_witness
from experiments.cnf_retained_causal import load_causal
from experiments.cnf_proof_choice import ProofChoiceBank,compose,audit_portfolio
from experiments.cnf_alternative_guard import AlternativeGuardSelector
eager=previous.eager;base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-incremental-causal');MODES=('first','alternative')
OLD_FIELDS=previous.OLD_FIELDS;FIELDS=previous.FIELDS+('incremental_causal_decisions',)
FILES=['experiments/cnf_alternative_guard.py','solver/test_cnf_alternative_guard.py','experiments/compare_cnf_alternative_guard.py','experiments/validate_cnf_alternative_guard.py']


def worker(out,protocol,catalog,mode):
    out.mkdir();start=time.perf_counter();parent=base.load(protocol['parent']['path']);records=[];selector=AlternativeGuardSelector(protocol['alternative_budget'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path)
        solver=AccountedResidualSolver(path,node_limit=protocol['node_limit']);initial=rows(solver);cursor=ResidualAppendCursor(solver)
        try:
            tick=time.perf_counter();bank=CoreBank(solver,base.load(protocol['cores']['path']));extensions=ExtensionBank(base.load(protocol['bank_catalog']['path'])['bank'])
            bank_seconds=time.perf_counter()-tick;tick=time.perf_counter();before=Counter(solver.counts)
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh preparation search')):
                bindings=dict(legacy=protocol['support_index'],causal=protocol['causal_index'])
                entry=bindings['legacy'];assert base.sha(entry['path'])==entry['sha256'];legacy=base.load(entry['path'])
                entry=bindings['causal'];causal=load_causal(entry['path'],entry['sha256']);indices=dict(legacy=legacy,causal=causal)
                prepared=compose(indices,bindings);cofactors=ProofChoiceBank(solver,legacy,causal)
                used=[(name,base.load(entry['path'])) for name,entry in zip(OLD_FIELDS,protocol['prior_decision_catalogs'])]
            preparation_counts=dict(solver.counts-before)
            preparation_seconds=time.perf_counter()-tick;setup_added=cursor.take();setup_seconds=time.perf_counter()-start
            for visit in range(protocol['visits']):
                for case in catalog['cases']:
                    tick=time.perf_counter();solver.counts=Counter();counts=Counter()
                    normalized,_,key=solver._canonical(case['source']);known=solver._read(key,normalized,purpose='direct_query')
                    support=bank.reuse(case['source']) if known is None else None
                    witness=reuse_witness(solver,extensions,case['source'],counts) if known is None and support is None else None
                    guard=propose(solver,extensions,case['source'],counts) if known is None and support is None and witness is None else None
                    if guard is None:assignment={};target=case['source']
                    else:assignment,target=check_guard(solver,case['source'],guard,counts)
                    cofactor=None;target_known=False
                    if guard is not None:
                        normalized,_,target_key=solver._canonical(target);target_known=solver._read(target_key,normalized,purpose='guard_target') is not None
                        if cofactors is not None and not target_known:cofactor=cofactors.reuse(target)
                    guard_choice=None
                    if mode=='alternative' and guard is not None and not target_known and cofactor is None:
                        selected,guard_choice=selector.select(solver,extensions,case['source'],guard,cofactors)
                        if selected is not None:
                            guard=selected;assignment,target=check_guard(solver,case['source'],guard,counts)
                            normalized,_,target_key=solver._canonical(target);target_known=solver._read(target_key,normalized,purpose='guard_target') is not None
                            if not target_known:cofactor=cofactors.reuse(target)
                    premise_counts=dict(solver.counts);child=solver.solve(target)
                    model=lift(case['source'],assignment,child['model']) if child['answer'] else None;added=cursor.take()
                    records.append(dict(case=case['case'],visit=visit,source=case['source'],guard=guard,witness=witness,core=support,
                        guard_choice=guard_choice,cofactor=cofactor,target_known=target_known,target=[list(c) for c in target],assignment=assignment,child=child,answer=child['answer'],model=model,
                        new_nodes=len(added),new_ids=sorted(map(base.key_sha,added)),counts=dict(counts),premise_counts=premise_counts,seconds=time.perf_counter()-tick))
            final=rows(solver);assert initial.items()<=final.items();totals=solver.db.execute(CENSUS).fetchone();assert solver.archive_storage()==totals
            accounting=dict(censuses=solver.accounting_censuses,cursor=dict(cursor.stats),final_nodes=totals[0],final_payload_units=totals[1],full_row_snapshots=3,final_full_preservation=True)
        except BaseException:
            solver.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:solver.close()
        cold=audit_portfolio(path,records,prepared,used,indices);base.write(out/'queries.json',records);base.write(out/'cofactor-bank.json',prepared);archive=base.archive(path,out)
    summary=dict(mode=mode,queries=len(catalog['cases']),visits=protocol['visits'],positive=sum(r['answer'] for r in records if r['visit']==0),
        core_hits=sum(r['core'] is not None for r in records if r['visit']==0),cofactor_hits=sum(r['cofactor'] is not None for r in records if r['visit']==0),
        target_known=sum(r['target_known'] for r in records if r['visit']==0),guard_uses=sum(r['guard'] is not None for r in records if r['visit']==0),
        witness_publications=sum(r['witness'] is not None for r in records),nodes=len(final),new_nodes=len(final)-len(initial),preparation_nodes=len(setup_added),
        query_new_nodes=sum(r['new_nodes'] for r in records),expanded_nodes=sum(r['child']['metrics'].get('expanded_nodes',0) for r in records),
        split_nodes=sum(r['child']['metrics'].get('split_nodes',0) for r in records),repeat_new_nodes=sum(r['new_nodes'] for r in records if r['visit']),
        cofactor_sources=0 if prepared is None else len(prepared['origins']),cofactor_cores=0 if prepared is None else len(prepared['all_cores']),
        retained_cofactor_cores=0 if prepared is None else len(prepared['cores']),bank_seconds=bank_seconds,preparation_seconds=preparation_seconds,setup_seconds=setup_seconds,
        query_seconds=sum(r['seconds'] for r in records),first_query_seconds=sum(r['seconds'] for r in records if r['visit']==0),
        repeat_query_seconds=sum(r['seconds'] for r in records if r['visit']),cold_seconds=cold['seconds'],compression_seconds=archive['seconds'],wall_seconds=time.perf_counter()-start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],
        sidecar_bytes=sum((out/f).stat().st_size for f in ('queries.json','cofactor-bank.json')),row_digest=base.key_sha(base.encode(sorted(final.items()))))
    summary.update(materialization_nodes=cofactors.counts.get('materialization_nodes',0),discovery_nodes=0,distinct_source_origins=389,
        changed_guards=sum(bool(r['guard_choice'] and r['guard_choice']['selected']) for r in records if r['visit']==0),
        guard_selection_calls=selector.counts['selection_calls'],lineage_seconds=cold['lineage_seconds'],proof_query_seconds=cold['proof_query_seconds'])
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),cofactor_bank=binding(out/'cofactor-bank.json'),
        setup_ids=sorted(map(base.key_sha,setup_added)),archive=archive,cold=cold,accounting=accounting,bank_counts=dict(bank.counts),cofactor_counts=dict(cofactors.counts),guard_choice_counts=dict(selector.counts),preparation_counts=preparation_counts,construction_policy=mode))
    elapsed=time.perf_counter()-start;report=base.load(out/'report.json');report['summary'].update(complete_worker_seconds=elapsed,complete_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024));base.write(out/'report.json',report)
    print(base.encode(summary),flush=True)


def run(out):
    out.mkdir(exist_ok=False);old=base.load(PARENT/'protocol.json');parent=base.load(PARENT/'checkpoint.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});prior=[]
    for field in FIELDS:
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['extended_support_proposals'],causal_index=parent['causal_support_proposals'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        prior_decision_catalogs=[parent[f] for f in FIELDS],node_limit=100000,alternative_budget=1,per_template=64,visits=2,orders=[MODES,MODES[::-1],MODES,MODES[::-1]],
        selection='Same salted order excluding 2304 prior sidecar answers and all complete roots in the current 19907-key union; next 64 per template, interleaved.',
        limitations=['Both modes start from the current 19907-key union and the same acquired 207-entry legacy / 176-entry causal portfolio. The larger optional causal bank remains preserved but is not loaded; neither mode acquires new supports.',
            'Both banks retain eight catalogs / 389 distinct origins. Selection excludes all 2304 prior sidecar answers and cached full roots, then takes 192 new neighbours. The 20-expansion historical opportunity is not reused as a fresh case.',
            'Alternative selection runs only when the first guarded residual misses both archive and support bank. At most one other matching extension proposal is checked, including unavailable or positive hints; enumerating the extension index and scanning supports are still charged.',
            'Selection reads checked known target proofs or checked ready contained negative supports; it never solves or materializes a pending proposal. The ordinary guard, subset-publication, child-check and model-lifting path remains required.',
            'Four alternating fresh-process pairs, two visits, no overlapping tests/builds/profiles. Full time includes preparation, recognition, checking, publication, queries, persistence, complete cold audit of every proof/query and both index lineages, compression and final digest/report generation. Imports, initial CLI reads and final wrapper rewrite excluded.',
            'Selection and original acquisition are separately charged. Changed guards can change later sharing and repeated-query overhead. This bounded heuristic is not optimal guard selection or a uniform arbitrary-SAT bound.'])
    base.write(out/'protocol.json',protocol);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path);solver=ResidualSolver(path)
        try:catalog=eager.previous.inputs(solver,protocol)
        finally:solver.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True,stdout=subprocess.DEVNULL)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')));print(mode,repeat,flush=True)
    summary={}
    for mode in MODES:
        trials=[base.load(x['path'])['summary'] for x in samples if x['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k.endswith('peak_rss_bytes')];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary));print(base.encode({m:{k:v for k,v in s.items() if k in ('expanded_nodes','cofactor_hits','new_nodes','mean_complete_worker_seconds')} for m,s in summary.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
