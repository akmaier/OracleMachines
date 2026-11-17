#!/usr/bin/env python3
"""Matched incremental causal discovery versus a fixed acquired portfolio."""
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_proof_choice as previous
from experiments.cnf_retained_causal import load_causal,retained_bank
from experiments.cnf_proof_choice import ProofChoiceBank,compose
from experiments.cnf_incremental_causal import extend_causal,audit_extended_portfolio
from experiments.cnf_active_support import ActiveCoreBank,extend_active,audit_with_lineage
eager=previous.eager;base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-proof-choice');MODES=('fixed','extended')
OLD_FIELDS=previous.OLD_FIELDS;FIELDS=previous.FIELDS+('proof_choice_decisions',)
FILES=['experiments/cnf_incremental_causal.py','solver/test_cnf_incremental_causal.py','experiments/compare_cnf_incremental_causal.py','experiments/validate_cnf_incremental_causal.py']


def worker(out,protocol,catalog,mode):
    tick=time.perf_counter();original_bank=eager.CoreBank;state={}
    def prepare(solver,catalogs):
        state['before']=Counter(solver.counts);used=catalogs[:len(OLD_FIELDS)]
        bindings=dict(legacy=protocol['support_index'],causal=protocol['causal_index'])
        entry=bindings['legacy'];assert base.sha(entry['path'])==entry['sha256'];legacy=base.load(entry['path'])
        entry=bindings['causal'];causal=load_causal(entry['path'],entry['sha256'])
        if mode=='extended':
            causal=extend_causal(solver,causal,used,catalogs[len(OLD_FIELDS):])
            base.write(out/'causal-frontier.json',causal);bindings['causal']=binding(out/'causal-frontier.json')
        indices=dict(legacy=legacy,causal=causal);prepared=compose(indices,bindings)
        state.update(indices=indices,prepared=prepared,cores=prepared['cores'],bindings=bindings,
            catalogs_by_bank=dict(legacy=used,causal=catalogs if mode=='extended' else used))
        return prepared
    def bank(solver,cores):
        if cores is not state.get('cores'):return original_bank(solver,cores)
        result=ProofChoiceBank(solver,state['indices']['legacy'],state['indices']['causal'])
        state['preparation_counts']=dict(solver.counts-state['before']);return result
    def cold(path,records):
        return audit_extended_portfolio(path,records,state['prepared'],state['catalogs_by_bank'],state['indices'])
    with ExitStack() as stack:
        for name,value in [('FIELDS',FIELDS),('prepare',prepare),('CoreBank',bank),('audit',cold)]:stack.enter_context(patch.object(eager,name,value))
        eager.worker(out,protocol,catalog,'cofactor')
    elapsed=time.perf_counter()-tick;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    report=base.load(out/'report.json');summary=report['summary'];summary.update(mode=mode,complete_worker_seconds=elapsed,complete_peak_rss_bytes=peak)
    summary['materialization_nodes']=report['cofactor_counts'].get('materialization_nodes',0)
    summary['discovery_nodes']=state['indices']['causal']['extraction_counts'].get('support_nodes',0) if mode=='extended' else 0
    summary['new_origin_records']=state['indices']['causal']['delta_origin_count'] if mode=='extended' else 0
    summary['acquired_index_bytes']=(out/'causal-frontier.json').stat().st_size if mode=='extended' else 0
    summary['sidecar_bytes']+=summary['acquired_index_bytes']
    summary['distinct_source_origins']=len({(o['catalog'],o['case']) for index in state['indices'].values() for o in index['origins']})
    summary['lineage_seconds']=report['cold']['lineage_seconds'];summary['proof_query_seconds']=report['cold']['proof_query_seconds']
    report.update(construction_policy=mode,preparation_counts=state['preparation_counts'],causal_index=state['bindings']['causal']);base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);old=base.load(PARENT/'protocol.json');parent=base.load(PARENT/'checkpoint.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});prior=[]
    for field in FIELDS:
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['extended_support_proposals'],causal_index=parent['causal_support_proposals'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        prior_decision_catalogs=[parent[f] for f in FIELDS],node_limit=100000,per_template=64,visits=2,orders=[MODES,MODES[::-1],MODES,MODES[::-1]],
        selection='Same salted order excluding 2112 prior sidecar answers and all complete roots in the current 19543-key union; next 64 per template, interleaved.',
        limitations=['Both modes preserve the acquired 19543-key union and use the ready-first portfolio. Fixed loads the old legacy and causal frontiers. Extended acquires causal supports from only the three newer catalogs, then maintains exact containment coverage and first-origin history.',
            'The old indices have eight catalogs / 389 distinct guarded negative origins. The three new catalogs add 137 guarded negative records, for 526 total. These are provenance records, not 526 distinct residual structures.',
            'Incremental acquisition checks new sources and may traverse old proof dependencies. It publishes no proof nodes. Pending supports still require matching causal materialization and ordinary negative proof checks.',
            'Legacy keeps its eight-catalog lineage; the extended causal bank uses all eleven catalogs. Both full lineages and the unchanged complete proof/query audit run on the same pinned cold snapshot. No persistent unchecked validity flag.',
            'Four alternating fresh-process pairs, two visits, no overlapping tests/builds/profiles. Full time includes loading, acquisition, merge, index serialization, matching, checking, derivation, queries, persistence, full cold audit, compression and final digest/report generation. Imports, initial CLI reads and final wrapper rewrite excluded.',
            'Selection and historical acquisition are separately charged. Newly serialized causal indices are charged in sidecar bytes. Old histories and every trial remain retained.',
            'A smaller containment frontier can retire a cheaper ready alternative; all raw supports and provenance remain stored. The portfolio heuristic does not minimize total proof cost.',
            'Novel acquired-source neighbours, not blind arbitrary SAT. No cross-guard, historical cold-construction, compact-closure or uniform-polynomial guarantee.'])
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
