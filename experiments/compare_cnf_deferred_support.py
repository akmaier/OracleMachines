#!/usr/bin/env python3
"""Compare support construction policies on matched pre-acquisition clones."""
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cofactor_support as eager
from experiments.cnf_deferred_support import discover,DeferredCoreBank
base=eager.base;binding=eager.binding;rows=eager.rows;ResidualSolver=eager.ResidualSolver
PARENT=Path('experiments/results/cnf-cofactor-support');SEED=Path('experiments/results/cnf-snapshot-replay/checkpoint.json')
MODES=('current','eager','deferred');FIELDS=eager.FIELDS
AUTHORITY_FIELDS=FIELDS+('cofactor_support_decisions',)
FILES=['experiments/cnf_deferred_support.py','solver/test_cnf_deferred_support.py',
       'experiments/compare_cnf_deferred_support.py','experiments/validate_cnf_deferred_support.py']


def worker(out,protocol,catalog,mode):
    tick=time.perf_counter();original_bank=eager.CoreBank;state={}
    def proposals(solver,catalogs):
        result=discover(solver,catalogs);state['cores']=result['cores'];return result
    def bank(solver,cores):
        return DeferredCoreBank(solver,cores) if cores is state.get('cores') else original_bank(solver,cores)
    with ExitStack() as stack:
        if mode=='deferred':
            stack.enter_context(patch.object(eager,'prepare',proposals));stack.enter_context(patch.object(eager,'CoreBank',bank))
        eager.worker(out,protocol,catalog,'current' if mode=='current' else 'cofactor')
    elapsed=time.perf_counter()-tick;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    report=base.load(out/'report.json');report['summary']['mode']=mode
    report['summary']['complete_worker_seconds']=elapsed;report['summary']['complete_peak_rss_bytes']=peak
    report['summary']['deferred_materialization_nodes']=report['cofactor_counts'].get('materialization_nodes',0)
    report['construction_policy']=mode;base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});authority=base.load(PARENT/'checkpoint.json');seed=base.load(SEED);old=base.load(PARENT/'protocol.json')
    previous=[]
    for field in AUTHORITY_FIELDS:
        entry=authority[field];assert base.sha(entry['path'])==entry['sha256'];previous+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',previous)
    protocol=dict(parent=binding(SEED),authority_parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,template_catalog=old['template_catalog'],
        previous_decisions=binding(out/'previous-decisions.json'),prior_decision_catalogs=[seed[f] for f in FIELDS],
        authority_decision_catalogs=[authority[f] for f in AUTHORITY_FIELDS],cores=old['cores'],bank_catalog=old['bank_catalog'],
        node_limit=100000,per_template=64,visits=2,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='Exclude all 768 earlier answered queries including guarded ones, then all cached full roots in the latest 16320-key authority. Same salted order, next 64 per template, interleaved.',
        limitations=['Construction-policy ablation: every worker starts from the identical historical 14630-key pre-acquisition seed. The current 16320-key union and its complete 104-core bank remain preserved.',
            'Discovery uses the same 145 old negative cofactors. Eager builds all derived support proofs; deferred builds source-bound proposals and materializes a checked core only after a target match.',
            'Proposals never justify UNSAT. Materialization uses the frozen extractor and verifier; source and guard remain bound to each child result.',
            'Three balanced fresh-process triples, two visits per stream, no tests/builds/profilers overlap. This is not a comparison against simply loading the already-built current bank.',
            'complete_worker_seconds includes the frozen worker final row digest, report construction/write and stdout, as well as restoration, discovery, construction, querying, full cold audit and compression. Imports, CLI reads and the wrapper result rewrite are excluded.',
            'complete_peak_rss_bytes is sampled after the frozen worker returns, including its final digest. Frozen wall_seconds/peak_rss_bytes remain for continuity and have their earlier exclusions.',
            'Selection and historical acquisition are separately charged. Unseen constructed neighbouring queries are not an independent arbitrary-SAT benchmark. No uniform polynomial bound or minimal-proof claim.'])
    base.write(out/'protocol.json',protocol);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'authority';base.restore_archive(authority['reference_union'],path);solver=ResidualSolver(path)
        try:catalog=eager.previous.inputs(solver,protocol)
        finally:solver.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(x['path'])['summary'] for x in samples if x['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k.endswith('peak_rss_bytes')];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary));print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
