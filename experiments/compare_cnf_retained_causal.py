#!/usr/bin/env python3
"""Matched retained causal frontiers without repeated historical discovery."""
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_causal_support as previous
from experiments.cnf_retained_causal import load_causal,retained_bank
from experiments.cnf_causal_support import discover_causal,CausalCoreBank
from experiments.cnf_active_support import ActiveCoreBank,extend_active,audit_with_lineage
eager=previous.eager;base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-causal-support');MODES=('legacy','rebuilt','retained')
OLD_FIELDS=previous.FIELDS;FIELDS=OLD_FIELDS+('causal_support_decisions',)
FILES=['experiments/cnf_retained_causal.py','solver/test_cnf_retained_causal.py','experiments/compare_cnf_retained_causal.py','experiments/validate_cnf_retained_causal.py']


def worker(out,protocol,catalog,mode):
    tick=time.perf_counter();original_bank=eager.CoreBank;state={}
    def prepare(solver,catalogs):
        state['before']=Counter(solver.counts);used=catalogs[:len(OLD_FIELDS)]
        if mode=='legacy':
            entry=protocol['support_index'];assert base.sha(entry['path'])==entry['sha256'];result=base.load(entry['path'])
        elif mode=='rebuilt':result=discover_causal(solver,used)
        else:
            entry=protocol['causal_index'];result=load_causal(entry['path'],entry['sha256'])
        state.update(prepared=result,catalogs=used,cores=result['cores']);return result
    def bank(solver,cores):
        if cores is not state.get('cores'):return original_bank(solver,cores)
        result=ActiveCoreBank(solver,cores) if mode=='legacy' else retained_bank(solver,state['prepared'])
        state['preparation_counts']=dict(solver.counts-state['before']);return result
    def cold(path,records):return audit_with_lineage(path,records,state['prepared'],state['catalogs'])
    with ExitStack() as stack:
        for name,value in [('FIELDS',FIELDS),('prepare',prepare),('CoreBank',bank),('audit',cold)]:stack.enter_context(patch.object(eager,name,value))
        eager.worker(out,protocol,catalog,'cofactor')
    elapsed=time.perf_counter()-tick;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    report=base.load(out/'report.json');summary=report['summary'];summary.update(mode=mode,complete_worker_seconds=elapsed,complete_peak_rss_bytes=peak)
    summary['materialization_nodes']=report['cofactor_counts'].get('materialization_nodes',0)
    summary['discovery_nodes']=state['prepared']['extraction_counts'].get('support_nodes',0) if mode=='rebuilt' else 0
    summary['lineage_seconds']=report['cold']['lineage_seconds'];summary['proof_query_seconds']=report['cold']['proof_query_seconds']
    report.update(construction_policy=mode,preparation_counts=state['preparation_counts']);base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);old=base.load(PARENT/'protocol.json');parent=base.load(PARENT/'checkpoint.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});prior=[]
    for field in FIELDS:
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['extended_support_proposals'],causal_index=parent['causal_support_proposals'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        prior_decision_catalogs=[parent[f] for f in FIELDS],node_limit=100000,per_template=64,visits=2,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='Same salted order excluding 1728 prior sidecar answers and all complete roots in the current 18672-key union; next 64 per template, interleaved.',
        limitations=['All workers preserve the current 18672-key union. Legacy loads the acquired 207-entry old-rule frontier. Rebuilt re-extracts the causal frontier from the same 389 historical origins. Retained loads the acquired 176-entry causal frontier instead. No mode adds the latest 51 negative origins.',
            'Both frontiers use the same eight ordered source catalogs. The ninth catalog is excluded from new query selection but is not used for discovery in this comparison. All historical acquisition and its stored proof rows remain charged separately.',
            'Loaded causal descriptions are fingerprinted hints bound to the causal materializer; every actual match still checks the core proof, materializes missing roots, and verifies current-query guards.',
            'Every mode retains the frozen complete proof/query audit and complete used-index lineage check on a pinned cold snapshot. Loading is not a persistent proof-validity flag.',
            'Three balanced fresh-process triples, two visits each, no overlapping tests/builds/profiles. Complete time includes final digest/report generation; imports, CLI reads and wrapper rewrite excluded. Selection is separately measured.',
            'Same acquired union and fresh neighbouring queries, not a historical cold-construction comparison or a repeated-query amortization claim. No arbitrary-SAT, minimum-core, cross-guard, or uniform-polynomial guarantee.'])
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
