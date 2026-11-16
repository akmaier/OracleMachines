#!/usr/bin/env python3
"""Compare a loaded ready bank, full rediscovery and checked delta discovery."""
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_deferred_support as previous
from experiments.cnf_deferred_support import discover,DeferredCoreBank
from experiments.cnf_incremental_support import extend,check_proposals
eager=previous.eager;base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-deferred-support');MODES=('ready','rebuild','incremental')
FIELDS=previous.AUTHORITY_FIELDS+('deferred_support_decisions',);OLD_FIELDS=eager.FIELDS
FILES=['experiments/cnf_incremental_support.py','solver/test_cnf_incremental_support.py',
    'experiments/compare_cnf_incremental_support.py','experiments/validate_cnf_incremental_support.py','experiments/profile_cnf_incremental_support.py']


def preparation(solver,prior,catalogs,mode):
    old=catalogs[:len(OLD_FIELDS)];new=catalogs[len(OLD_FIELDS):]
    if mode=='rebuild':return discover(solver,catalogs)
    if mode=='incremental':return extend(solver,prior,old,new)
    result=copy.deepcopy(prior);result.update(check_proposals(solver,result,old));return result


def worker(out,protocol,catalog,mode):
    tick=time.perf_counter();original_bank=eager.CoreBank;state={}
    def prepare(solver,catalogs):
        prior=base.load(protocol['ready_bank']['path']);assert base.sha(protocol['ready_bank']['path'])==protocol['ready_bank']['sha256']
        result=preparation(solver,prior,catalogs,mode);state['cores']=result['cores'];return result
    def bank(solver,cores):return DeferredCoreBank(solver,cores) if cores is state.get('cores') else original_bank(solver,cores)
    with ExitStack() as stack:
        stack.enter_context(patch.object(eager,'FIELDS',FIELDS));stack.enter_context(patch.object(eager,'prepare',prepare));stack.enter_context(patch.object(eager,'CoreBank',bank))
        eager.worker(out,protocol,catalog,'cofactor')
    elapsed=time.perf_counter()-tick;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    report=base.load(out/'report.json');summary=report['summary'];summary['mode']=mode;summary['complete_worker_seconds']=elapsed;summary['complete_peak_rss_bytes']=peak
    summary['materialization_nodes']=report['cofactor_counts'].get('materialization_nodes',0)
    summary['discovery_nodes']=base.load(report['cofactor_bank']['path'])['extraction_counts'].get('support_nodes',0) if mode!='ready' else 0
    report['construction_policy']=mode;base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);old=base.load(PARENT/'protocol.json');parent=base.load(PARENT/'checkpoint.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});prior=[]
    for field in FIELDS:
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,ready_bank=parent['cofactor_support_bank'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],
        previous_decisions=binding(out/'previous-decisions.json'),prior_decision_catalogs=[parent[f] for f in FIELDS],
        node_limit=100000,per_template=64,visits=2,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='Same salted order, excluding 960 prior sidecar answers including guarded records and all complete roots in the current 16760-key union. Next 64 per template, interleaved.',
        limitations=['Every mode starts from the current 16760-key union and loads the already-materialized 104-core bank; earlier acquisition stays charged in historical records.',
            'Ready checks and reuses the saved bank. Rebuild discovers supports from all 244 negative guarded sources. Incremental checks old provenance/cores and discovers only the 99 newly acquired negative sources.',
            'Unmaterialized proposals are never UNSAT certificates. Matching derives/checks the negative core before subset publication; full-query results retain source and checked guard.',
            'Three balanced fresh-process triples, two visits each, no tests/builds/profiles overlap. Complete clock includes final row digest/report generation, unlike earlier wall_seconds.',
            'Imports, CLI protocol reads and wrapper report rewrite are excluded. Selection, profiling and historical acquisition are separately charged.',
            'Constructed neighbouring development inputs; no blind arbitrary-SAT, cross-category, minimum-work or uniform-polynomial guarantee.'])
    base.write(out/'protocol.json',protocol);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(parent['reference_union'],path);solver=ResidualSolver(path)
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
