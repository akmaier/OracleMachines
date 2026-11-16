#!/usr/bin/env python3
"""Matched active proof checks with complete, charged cold lineage verification."""
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_support as previous
from experiments.cnf_incremental_support import extend,check_proposals
from experiments.cnf_deferred_support import DeferredCoreBank
from experiments.cnf_active_support import ActiveCoreBank,extend_active,audit_with_lineage
eager=previous.eager;base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-incremental-support');MODES=('loaded','eager','active')
OLD_FIELDS=previous.FIELDS;FIELDS=OLD_FIELDS+('incremental_support_decisions',)
FILES=['experiments/cnf_active_support.py','solver/test_cnf_active_support.py','experiments/compare_cnf_active_support.py','experiments/validate_cnf_active_support.py']


def worker(out,protocol,catalog,mode):
    tick=time.perf_counter();original_bank=eager.CoreBank;state={}
    def prepare(solver,catalogs):
        prior=base.load(protocol['support_index']['path']);assert base.sha(protocol['support_index']['path'])==protocol['support_index']['sha256']
        state['before']=Counter(solver.counts);old=catalogs[:len(OLD_FIELDS)];new=catalogs[len(OLD_FIELDS):]
        if mode=='loaded':
            result=copy.deepcopy(prior);result.update(check_proposals(solver,result,old));used=old
        else:
            result=(extend_active if mode=='active' else extend)(solver,prior,old,new);used=catalogs
        state.update(prepared=result,catalogs=used,cores=result['cores']);return result
    def bank(solver,cores):
        if cores is not state.get('cores'):return original_bank(solver,cores)
        result=(ActiveCoreBank if mode=='active' else DeferredCoreBank)(solver,cores)
        state['preparation_counts']=dict(solver.counts-state['before']);return result
    def cold(path,records):return audit_with_lineage(path,records,state['prepared'],state['catalogs'])
    with ExitStack() as stack:
        for name,value in [('FIELDS',FIELDS),('prepare',prepare),('CoreBank',bank),('audit',cold)]:stack.enter_context(patch.object(eager,name,value))
        eager.worker(out,protocol,catalog,'cofactor')
    elapsed=time.perf_counter()-tick;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    report=base.load(out/'report.json');summary=report['summary'];summary.update(mode=mode,complete_worker_seconds=elapsed,complete_peak_rss_bytes=peak)
    summary['materialization_nodes']=report['cofactor_counts'].get('materialization_nodes',0)
    summary['discovery_nodes']=0 if mode=='loaded' else state['prepared']['extraction_counts'].get('support_nodes',0)
    summary['lineage_seconds']=report['cold']['lineage_seconds'];summary['proof_query_seconds']=report['cold']['proof_query_seconds']
    report.update(construction_policy=mode,preparation_counts=state['preparation_counts']);base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);old=base.load(PARENT/'protocol.json');parent=base.load(PARENT/'checkpoint.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});prior=[]
    for field in FIELDS:
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['incremental_support_proposals'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        prior_decision_catalogs=[parent[f] for f in FIELDS],node_limit=100000,per_template=64,visits=2,orders=[MODES,MODES[1:]+MODES[:1],MODES[2:]+MODES[:2]],
        selection='Same salted order, excluding 1152 prior sidecar answers and all complete roots in the latest 17161-key union. Next 64 per template, interleaved.',
        limitations=['All workers preserve the current 17161-key union and load the saved 151-entry support index including pending proposals. Prior acquisition stays charged in history.',
            'Loaded checks and reuses the existing index. Eager extends it from 42 new negative sources and checks old lineage upfront. Active extends with the same new sources and checks matched core proofs on demand.',
            'Every mode additionally runs the same frozen complete proof/query audit and full used-index provenance check on one pinned cold snapshot, both included in complete time. This audit boundary is broader than the previous benchmark.',
            'Active proposals are hints, never negative certificates: every matched root must have an ordinary checked negative proof before publication. Pending roots materialize from checked origins. Complete query guards remain checked online.',
            'Three balanced fresh-process triples, two visits each, no tests/builds/profiles overlap. Complete time includes final digest/report generation; imports, CLI reads and wrapper rewrite are excluded.',
            'Private append-only solver ownership and read-only pinned cold audits; no shared mutating service or hostile private-connection contract.',
            'Constructed neighbouring inputs; no broad cross-category, arbitrary-SAT, minimum-work or uniform-polynomial guarantee.'])
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
