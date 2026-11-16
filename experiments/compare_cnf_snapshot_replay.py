#!/usr/bin/env python3
"""Matched ordinary and single-census cold audits after identical expansion."""
from pathlib import Path
from contextlib import nullcontext
from unittest.mock import patch
import subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_archive as previous
from experiments.cnf_snapshot_replay import audit as snapshot_audit
base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-incremental-archive')
MODES=('ordinary_audit','snapshot_audit')
FILES=['experiments/cnf_snapshot_replay.py','solver/test_cnf_snapshot_replay.py',
       'experiments/compare_cnf_snapshot_replay.py','experiments/validate_cnf_snapshot_replay.py']


def worker(out,protocol,catalog,mode):
    context=patch.object(previous.prior.old.previous,'audit',snapshot_audit) if mode=='snapshot_audit' else nullcontext()
    # Reuse the frozen expansion worker and clock; only the final audit changes.
    with context:previous.worker(out,protocol,catalog,'delta')
    report=base.load(out/'report.json');report['summary']['mode']=mode;report['expansion_mode']='delta'
    base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json')
    prior_decisions=[]
    for field in ('unsat_support_decisions','incremental_archive_decisions'):
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior_decisions+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior_decisions)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,
        template_catalog=old['template_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        prior_decision_catalogs=[parent[f] for f in ('unsat_support_decisions','incremental_archive_decisions')],
        cores=old['cores'],bank_catalog=old['bank_catalog'],node_limit=100000,per_template=64,visits=2,
        orders=[MODES,MODES[::-1],MODES,MODES[::-1]],
        selection='Same salted double-deletion order, excluding all 384 previously answered queries including guarded ones, then any cached complete root. Next 64 per template, interleaved.',
        limitations=['Both modes use the latest 14208-key union, identical persisted banks and the frozen delta expansion worker. Only its complete cold audit changes.',
            'Ordinary audit uses the frozen solver. Snapshot audit runs the same frozen audit and proof checker with read-only snapshot size totals computed once.',
            'The snapshot pins a SQLite read transaction and rejects DML, schema changes and transaction-ending statements. Hostile private-connection changes are outside the contract.',
            'The scoped solver substitution owns its process; it is not a concurrent multithreaded audit API. Archives are private closed clones during measured audits.',
            'Four balanced fresh-process pairs, two visits per stream, no tests/builds/profilers overlap. Historical extraction/acquisition remain separately charged.',
            'Frozen worker timer includes restoration, checking, solving, bookkeeping, full final preservation, complete cold replay, sidecar writes and compression. Process launch, imports, CLI protocol/catalog reads and final report writes are excluded.',
            'Constructed neighbouring inputs. No new recognition, proof compression or unrestricted-SAT guarantee.'])
    base.write(out/'protocol.json',protocol);tick=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'parent';base.restore_archive(parent['reference_union'],path);solver=ResidualSolver(path)
        try:catalog=previous.inputs(solver,protocol)
        finally:solver.close()
    base.write(out/'cases.json',catalog);base.write(out/'preflight.json',dict(seconds=time.perf_counter()-tick,selection=catalog['selection']))
    samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),str(out/'cases.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(x['path'])['summary'] for x in samples if x['mode']==mode];a=trials[0]
        timed=[k for k in a if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in a if k not in timed and k not in ('mode','sidecar_bytes')]
        for b in trials[1:]:
            for k in fixed:assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed},'sidecar_bytes':[t['sidecar_bytes'] for t in trials]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),cases=binding(out/'cases.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),base.load(sys.argv[4]),sys.argv[5])
    else:run(Path(sys.argv[1]))
