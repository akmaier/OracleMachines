#!/usr/bin/env python3
"""Matched terminal-conflict admission on fresh excluded neighbours."""
from pathlib import Path
from unittest.mock import patch
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_alternative_guard as previous
from experiments.cnf_terminal_guard import TerminalGuardSelector
base=previous.base;eager=previous.eager;binding=previous.binding;rows=previous.rows
ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-pending-guards');MODES=('ready','terminal')
OLD_FIELDS=previous.OLD_FIELDS;FIELDS=previous.FIELDS+('alternative_guard_decisions',)
FILES=['experiments/cnf_terminal_guard.py','solver/test_cnf_terminal_guard.py','experiments/compare_cnf_terminal_guard.py','experiments/validate_cnf_terminal_guard.py']


def worker(out,protocol,catalog,mode):
    start=time.perf_counter()
    cls=previous.AlternativeGuardSelector if mode=='ready' else TerminalGuardSelector
    # Preserve the frozen pipeline in both arms; only the selector is substituted.
    with patch.object(previous,'AlternativeGuardSelector',cls):previous.worker(out,protocol,catalog,'alternative')
    report=base.load(out/'report.json');summary=report['summary'];counts=report['guard_choice_counts']
    summary['mode']=mode;report['construction_policy']=mode
    summary['terminal_choices']=counts.get('terminal_choices',0)
    summary['terminal_materialization_nodes']=counts.get('terminal_materialization_nodes',0)
    summary['materialization_nodes']+=summary['terminal_materialization_nodes']
    base.write(out/'report.json',report)
    summary['complete_worker_seconds']=time.perf_counter()-start
    summary['complete_peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    base.write(out/'report.json',report)


def run(out):
    out.mkdir(exist_ok=False);old=base.load('experiments/results/cnf-alternative-guard/protocol.json');parent=base.load(PARENT/'checkpoint.json');sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});prior=[]
    for field in FIELDS:
        entry=parent[field];assert base.sha(entry['path'])==entry['sha256'];prior+=base.load(entry['path'])
    base.write(out/'previous-decisions.json',prior)
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,support_index=parent['extended_support_proposals'],causal_index=parent['causal_support_proposals'],
        template_catalog=old['template_catalog'],cores=old['cores'],bank_catalog=old['bank_catalog'],previous_decisions=binding(out/'previous-decisions.json'),
        prior_decision_catalogs=[parent[f] for f in FIELDS],node_limit=100000,alternative_budget=1,per_template=64,visits=2,orders=[MODES,MODES[::-1],MODES,MODES[::-1]],
        selection='Same salted order excluding 2496 prior sidecar answers and all complete roots in the current 20340-key union; next 64 per template, interleaved.',
        limitations=['Both modes start from the current 20340-key union and the same acquired 207-entry legacy / 176-entry causal portfolio. The larger optional causal bank remains preserved but is not loaded; neither mode acquires new supports.',
            'Both banks retain eight catalogs / 389 distinct origins. Selection excludes all 2496 prior sidecar answers and cached full roots, then takes 192 new neighbours. The 20-expansion historical opportunity is not reused as a fresh case.',
            'Alternative selection runs only when the first guarded residual misses both archive and support bank. At most one other matching extension proposal is checked, including unavailable or positive hints; enumerating the extension index and scanning supports are still charged.',
            'Both arms first prefer known targets and ready supports. Terminal mode may then derive the first matching pending support whose checked origin is a terminal unit conflict, under the same one-alternative budget. At most one core row is published; ordinary subset publication and query checking remain required.',
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
